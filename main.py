import io
import os
import numpy as np
import soundfile as sf
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Tuple
from scipy.signal import correlate
from dotenv import load_dotenv

# Import configuration system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "api"))
from utils.config import get_settings

# Import cross-correlation function
from routes.cross_correlation import cross_correlation_detection

# 1. 初始化 FastAPI 应用
app = FastAPI(
    title="Audio Beep Detection API",
    description="Lightweight beep detection using cross-correlation",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载环境变量
load_dotenv()

# 获取配置
settings = get_settings()

# Static files for Swagger UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom Swagger UI endpoint for Vercel (port 80/443)
@app.get("/swagger", response_class=HTMLResponse)
async def custom_swagger_ui():
    """Custom Swagger UI endpoint optimized for Vercel deployment"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Audio Beep Detection API - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

# Static Swagger UI page (for better Vercel compatibility)
@app.get("/swagger-static", response_class=HTMLResponse)
async def static_swagger_ui():
    """Static Swagger UI page for Vercel deployment"""
    with open("static/swagger.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# OpenAPI JSON endpoint
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    """Return OpenAPI specification"""
    return app.openapi()

# 2. 定义响应模型
class HealthResponse(BaseModel):
    status: str

class CrossCorrelationResponse(BaseModel):
    filename: str
    template: str
    sr: int
    threshold: float
    min_separation_s: float
    method: str
    matches: List[float]
    matches_mm_ss: List[str]
    num_matches: int

# 3. 定义API端点
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return {"status": "Audio Processing API is running!"}

@app.post("/detect-cross-correlation/", response_model=CrossCorrelationResponse)
async def detect_cross_correlation_beeps(
    file: UploadFile = File(...),
    threshold: Optional[float] = None,
    min_separation_s: Optional[float] = None,
    sr_target: Optional[int] = None
):
    """使用轻量级互相关检测嘟声（仅使用SciPy，不依赖librosa）"""
    if not file.content_type or not file.content_type.startswith("audio/"):
        # 如果content_type不是audio/，检查文件扩展名
        filename = file.filename or ""
        if not (filename.lower().endswith('.wav') or filename.lower().endswith('.mp3') or 
                filename.lower().endswith('.flac') or filename.lower().endswith('.aac') or
                filename.lower().endswith('.ogg') or filename.lower().endswith('.m4a')):
            raise HTTPException(status_code=400, detail="错误：请上传一个音频文件。")

    try:
        # 使用配置参数
        threshold = threshold if threshold is not None else settings.beep_threshold
        min_separation_s = min_separation_s if min_separation_s is not None else settings.beep_min_sep
        sr_target = sr_target if sr_target is not None else settings.beep_sr

        # 读取音频文件（使用soundfile）
        contents = await file.read()
        y_target, sr = sf.read(io.BytesIO(contents))
        
        # 重采样如果需要
        if sr != sr_target:
            # 简单的重采样（对于生产环境，建议使用更专业的重采样）
            from scipy import signal
            old_samples = len(y_target)
            new_samples = int(old_samples * sr_target / sr)
            y_target = signal.resample(y_target, new_samples)
            sr = sr_target
        
        # 确保音频是单声道
        if len(y_target.shape) > 1:
            y_target = np.mean(y_target, axis=1)
        
        # 读取模板文件
        template_path = settings.default_template_path
        if not os.path.exists(template_path):
            raise HTTPException(status_code=500, detail=f"模板文件未找到: {template_path}")
        
        y_template, sr_template = sf.read(template_path)
        
        # 重采样模板到目标采样率
        if sr_template != sr_target:
            from scipy import signal
            old_samples = len(y_template)
            new_samples = int(old_samples * sr_target / sr_template)
            y_template = signal.resample(y_template, new_samples)
        
        # 确保模板是单声道
        if len(y_template.shape) > 1:
            y_template = np.mean(y_template, axis=1)
        
        # 调用互相关检测函数
        matches = cross_correlation_detection(
            y_target=y_target,
            y_template=y_template,
            sr=sr_target,
            threshold=threshold,
            min_separation_s=min_separation_s
        )
        
        # 转换为分:秒格式
        matches_mm_ss = [f"{int(m//60):02d}:{int(m%60):03d}" for m in matches]
        
        return {
            "filename": file.filename or "unknown",
            "template": os.path.basename(template_path),
            "sr": sr_target,
            "threshold": threshold,
            "min_separation_s": min_separation_s,
            "method": "cross_correlation",
            "matches": matches,
            "matches_mm_ss": matches_mm_ss,
            "num_matches": len(matches)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理音频时出错: {str(e)}")

# 4. 根路径重定向到健康检查
@app.get("/")
async def root():
    """根路径重定向到健康检查"""
    return {
        "status": "Audio Processing API is running!", 
        "endpoints": [
            "/health", 
            "/detect-cross-correlation/",
            "/docs", 
            "/swagger", 
            "/swagger-static",
            "/redoc",
            "/openapi.json"
        ],
        "documentation": {
            "swagger_ui": "/docs or /swagger or /swagger-static",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)