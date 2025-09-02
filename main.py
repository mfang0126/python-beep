import io
import os
import librosa
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Tuple
from scipy.signal import butter, filtfilt, fftconvolve, find_peaks, correlate
from dotenv import load_dotenv

# 1. 初始化 FastAPI 应用
app = FastAPI(
    title="Audio Beep Detection API",
    description="一个可以检测音频文件中'嘟'声时间点的API"
)

# CORS (development friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _format_mm_ss(time_seconds: float) -> str:
    """格式化为 MM:SS.mmm 字符串。"""
    if time_seconds is None or (isinstance(time_seconds, float) and np.isnan(time_seconds)):
        return "00:00.000"
    minutes = int(time_seconds // 60)
    seconds = time_seconds - minutes * 60
    return f"{minutes:02d}:{seconds:06.3f}"

# 从 .env 载入环境变量
load_dotenv()

def _get_env_optional_float(name: str) -> Optional[float]:
    val = os.getenv(name)
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None

def _get_env_float(name: str, default_value: float) -> float:
    try:
        return float(os.getenv(name, default_value))
    except Exception:
        return default_value

def _get_env_int(name: str, default_value: int) -> int:
    try:
        return int(os.getenv(name, default_value))
    except Exception:
        return default_value

def _get_env_bool(name: str, default_value: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default_value
    return str(val).lower() in {"1", "true", "yes", "on"}


class FindBeepsResponse(BaseModel):
    filename: str
    detected_beep_timestamps: List[float] = Field(..., description="检测到的时间(秒)")
    detected_beep_timestamps_mm_ss: List[str] = Field(..., description="检测到的时间(MM:SS.mmm)")


class TemplateMatchResponse(BaseModel):
    filename: str
    template: str
    sr: int
    threshold: float
    min_separation_s: float
    raw: bool
    matches: List[float]
    matches_mm_ss: List[str]
    num_matches: int


# 2. 定义我们的API端点 (Endpoint)
@app.post("/detect-frequency-beeps/", response_model=FindBeepsResponse)
async def detect_frequency_beeps(file: UploadFile = File(...)):
    """
    接收一个音频文件，分析并返回所有检测到的'嘟'声的时间戳 (秒)。
    """
    # 检查上传的是否是音频文件
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="错误：请上传一个音频文件。")

    try:
        # --- 核心音频处理逻辑 ---

        # a. 将上传的文件内容读入内存
        contents = await file.read()
        
        # b. 使用 librosa 加载音频。我们用 io.BytesIO 来让 librosa 直接从内存中读取
        y, sr = librosa.load(io.BytesIO(contents), sr=None)

        # c. 设置参数 (这些值你需要根据你的'嘟'声样本进行微调)
        target_freq_low = 1100  # '嘟'声的最低频率
        target_freq_high = 1300 # '嘟'声的最高频率
        n_fft = 4096            # FFT窗口大小，决定频率分辨率
        hop_length = n_fft // 4 # 与 STFT 保持一致的步长
        
        # d. 进行短时傅里叶变换 (STFT)
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

        # e. 找到目标频率范围对应的索引
        target_freq_indices = np.where((freqs >= target_freq_low) & (freqs <= target_freq_high))[0]

        # f. 计算目标频率范围的能量
        energy_at_target_freq = np.sum(np.abs(D[target_freq_indices, :]), axis=0)

        # g. 设置动态阈值来检测'嘟'声 (平均能量的5倍，可以调整)
        threshold = np.mean(energy_at_target_freq) * 5

        # h. 找到所有能量超过阈值的帧
        beep_frames = np.where(energy_at_target_freq > threshold)[0]
        
        # i. 为了避免将一个'嘟'声识别成连续的多个点，我们做一个简单的处理：
        #    只保留连续'嘟'声块的起始点
        if len(beep_frames) > 0:
            beep_groups = np.split(beep_frames, np.where(np.diff(beep_frames) != 1)[0] + 1)
            first_beep_frames = [group[0] for group in beep_groups]
        else:
            first_beep_frames = []

        # j. 将帧索引转换为秒
        beep_timestamps = librosa.frames_to_time(first_beep_frames, sr=sr, hop_length=hop_length)

        # 3. 返回结果
        ts = beep_timestamps.tolist()  # 转换为Python列表
        return FindBeepsResponse(
            filename=file.filename or "unknown",
            detected_beep_timestamps=ts,
            detected_beep_timestamps_mm_ss=[_format_mm_ss(t) for t in ts],
        )

    except Exception as e:
        # 如果处理过程中发生任何错误，返回一个服务器错误信息
        raise HTTPException(status_code=500, detail=f"处理音频时发生错误: {str(e)}")

# 添加一个根路径，方便测试服务是否启动
@app.get("/")
def read_root():
    return {"status": "Audio Processing API is running!"}

# 3. 模板匹配端点：使用参考片段在目标音频中检测相似的'嘟'声
@app.post("/detect-template-matches/", response_model=TemplateMatchResponse)
async def detect_template_matches(
    file: UploadFile = File(...),
    threshold: Optional[float] = None,
    min_separation_s: Optional[float] = None,
    sr_target: Optional[int] = None,
    band_low: Optional[float] = None,
    band_high: Optional[float] = None,
    smooth_ms: Optional[float] = None,
    raw: Optional[bool] = None,
    start_s: Optional[float] = None,
    end_s: Optional[float] = None,
):
    """
    基于提供的参考片段(模板)在目标音频中进行相似'嘟'声检测。
    - 使用带通滤波聚焦在目标频段，然后对包络做归一化互相关(NCC)。
    - 通过峰值检测返回匹配到的时间点(秒)。
    可调参数:
      - threshold: NCC阈值(0~1)，越高越严格
      - min_separation_s: 相邻两次检测最小间隔(秒)
      - sr_target: 处理采样率(Hz)
      - band_low/band_high: 目标频段(Hz)
      - smooth_ms: 包络平滑窗口大小(毫秒)
    """
    # 检查上传类型
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="错误：请上传音频文件作为目标。")

    try:
        # 参数优先采用查询参数；未提供时从环境变量读取
        threshold = threshold if threshold is not None else _get_env_float("BEEP_THRESHOLD", 0.6)
        min_separation_s = min_separation_s if min_separation_s is not None else _get_env_float("BEEP_MIN_SEP", 0.5)
        sr_target = sr_target if sr_target is not None else _get_env_int("BEEP_SR", 11025)
        band_low = band_low if band_low is not None else _get_env_float("BEEP_BAND_LOW", 1100.0)
        band_high = band_high if band_high is not None else _get_env_float("BEEP_BAND_HIGH", 1300.0)
        smooth_ms = smooth_ms if smooth_ms is not None else _get_env_float("BEEP_SMOOTH_MS", 10.0)
        raw = raw if raw is not None else _get_env_bool("BEEP_RAW", False)
        if start_s is None:
            start_s = _get_env_optional_float("BEEP_START_S")
        if end_s is None:
            end_s = _get_env_optional_float("BEEP_END_S")

        # 读取音频
        target_bytes = await file.read()
        default_template_path = os.getenv("DEFAULT_TEMPLATE_PATH", "/Users/freedom/CCL/python-beep/beep_template.wav")
        try:
            with open(default_template_path, "rb") as f:
                template_bytes = f.read()
            template_name = default_template_path.split("/")[-1]
        except Exception:
            raise HTTPException(status_code=400, detail="默认模板文件不存在。请创建 beep_template.wav。")

        y_target, sr = librosa.load(io.BytesIO(target_bytes), sr=sr_target)
        y_tmpl, _ = librosa.load(io.BytesIO(template_bytes), sr=sr_target)

        if y_tmpl.size == 0 or y_target.size == 0:
            raise HTTPException(status_code=400, detail="无法读取音频或音频为空。")

        # 原始波形互相关（raw=True）或 带通+包络+NCC（raw=False）
        min_dist = max(1, int(min_separation_s * sr_target))

        if raw:
            x = y_target.astype(np.float32)
            h = y_tmpl.astype(np.float32)
            x /= (np.max(np.abs(x)) + 1e-8)
            h /= (np.max(np.abs(h)) + 1e-8)
            corr = correlate(x, h, mode='valid')
            height = float(threshold) * float(np.max(corr) if corr.size > 0 else 1.0)
            peaks, _ = find_peaks(corr, height=height, distance=min_dist)
            times = (peaks / float(sr_target)).tolist()
            # 可选的时间范围过滤
            if start_s is not None:
                times = [t for t in times if t >= start_s]
            if end_s is not None:
                times = [t for t in times if t <= end_s]
            return TemplateMatchResponse(
                filename=file.filename or "unknown",
                template=template_name,
                sr=sr_target,
                threshold=threshold,
                min_separation_s=min_separation_s,
                raw=True,
                matches=times,
                matches_mm_ss=[_format_mm_ss(t) for t in times],
                num_matches=len(times),
            )
        else:
            # 设计带通滤波器
            nyq = 0.5 * sr_target
            low = max(1.0, band_low) / nyq
            high = min(sr_target/2 - 100.0, band_high) / nyq
            if not (0 < low < high < 1):
                raise HTTPException(status_code=400, detail="带通频段设置不合理，请调整 band_low/band_high。")
            b, a = butter(N=4, Wn=[low, high], btype='band')  # type: ignore

            # 带通 + 取包络 + 平滑
            def envelope(sig: np.ndarray) -> np.ndarray:
                if sig.ndim > 1:
                    sig = np.mean(sig, axis=1)
                fil = filtfilt(b, a, sig)
                env = np.abs(fil)
                win = max(1, int(sr_target * (smooth_ms / 1000.0)))
                kernel = np.ones(win, dtype=np.float32) / float(win)
                # 使用FFT卷积加速
                sm = fftconvolve(env, kernel, mode='same')
                return sm.astype(np.float32)

            env_target = envelope(y_target)
            env_tmpl = envelope(y_tmpl)

            L = env_tmpl.size
            if L < 10:
                raise HTTPException(status_code=400, detail="模板片段太短，至少需要>10个样本。")
            if env_target.size <= L:
                raise HTTPException(status_code=400, detail="目标音频太短，长度应大于模板。")

            # 归一化互相关
            tmpl_energy = float(np.sum(env_tmpl ** 2))
            if tmpl_energy == 0.0:
                raise HTTPException(status_code=400, detail="模板能量为0，无法进行匹配。")

            numerator = fftconvolve(env_target, env_tmpl[::-1], mode='valid')
            ones = np.ones(L, dtype=np.float32)
            target_energy = fftconvolve(env_target.astype(np.float32) ** 2, ones, mode='valid')
            denom = np.sqrt(target_energy * tmpl_energy) + 1e-8
            ncc = numerator / denom

            peaks, _ = find_peaks(ncc, height=threshold, distance=min_dist)
            times = (peaks / float(sr_target)).tolist()

            # 可选的时间范围过滤
            if start_s is not None:
                times = [t for t in times if t >= start_s]
            if end_s is not None:
                times = [t for t in times if t <= end_s]
            return TemplateMatchResponse(
                filename=file.filename or "unknown",
                template=template_name,
                sr=sr_target,
                threshold=threshold,
                min_separation_s=min_separation_s,
                raw=False,
                matches=times,
                matches_mm_ss=[_format_mm_ss(t) for t in times],
                num_matches=len(times),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板匹配时发生错误: {str(e)}")