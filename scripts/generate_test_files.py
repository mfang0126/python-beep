#!/usr/bin/env python3
"""
Generate test audio files using the actual beep template as reference

LOCAL TESTING SCRIPT - Not for deployment
Used to create test audio files with known ground truth for accuracy validation
"""
import numpy as np
import soundfile as sf
import json
import os
from pathlib import Path

class TestAudioGenerator:
    def __init__(self):
        # Load the template
        template_path = 'static/beep_template.wav'
        self.template_audio, self.template_sr = sf.read(template_path)
        self.template_duration = len(self.template_audio) / self.template_sr
        print(f"Template loaded: {self.template_duration:.2f}s at {self.template_sr}Hz")
        
    def create_test_with_template(self, output_name, beep_times, total_duration=10.0, noise_level=0.01):
        """Create test file using the actual template beep"""
        
        # Create empty audio array
        total_samples = int(self.template_sr * total_duration)
        audio = np.zeros(total_samples)
        
        # Add background noise
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, total_samples)
            audio += noise
        
        # Insert template beeps at specified times
        for beep_time in beep_times:
            start_sample = int(beep_time * self.template_sr)
            end_sample = start_sample + len(self.template_audio)
            
            if end_sample <= total_samples:
                # Add the template beep
                audio[start_sample:end_sample] += self.template_audio
        
        # Save to testing-files directory
        output_path = f"testing-files/{output_name}.wav"
        sf.write(output_path, audio, self.template_sr)
        
        # Create test info
        test_info = {
            "filename": output_path,
            "ground_truth": beep_times,
            "template_used": "static/beep_template.wav",
            "template_duration": self.template_duration,
            "total_duration": total_duration,
            "noise_level": noise_level,
            "description": f"Template beeps at {[f'{t:.2f}s' for t in beep_times]}"
        }
        
        return output_path, test_info
    
    def create_comprehensive_test_suite(self):
        """Create test suite covering various scenarios"""
        print("🔬 Creating comprehensive test suite...")
        
        test_suite = []
        
        # Test 1: Simple periodic beeps
        _, info1 = self.create_test_with_template(
            "periodic_beeps",
            [1.0, 3.0, 5.0, 7.0, 9.0],
            total_duration=12.0,
            noise_level=0.005
        )
        test_suite.append(info1)
        
        # Test 2: Close beeps (test minimum separation)
        _, info2 = self.create_test_with_template(
            "close_beeps",
            [1.0, 1.8, 3.0, 4.5, 6.0],
            total_duration=8.0,
            noise_level=0.005
        )
        test_suite.append(info2)
        
        # Test 3: Noisy environment
        _, info3 = self.create_test_with_template(
            "noisy_beeps",
            [1.5, 3.5, 5.5, 7.5],
            total_duration=10.0,
            noise_level=0.02
        )
        test_suite.append(info3)
        
        # Test 4: Sparse beeps
        _, info4 = self.create_test_with_template(
            "sparse_beeps",
            [2.0, 6.0],
            total_duration=8.0,
            noise_level=0.005
        )
        test_suite.append(info4)
        
        # Test 5: Dense beeps
        _, info5 = self.create_test_with_template(
            "dense_beeps",
            [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5],
            total_duration=9.0,
            noise_level=0.005
        )
        test_suite.append(info5)
        
        # Test 6: Variable spacing
        _, info6 = self.create_test_with_template(
            "variable_spacing",
            [1.0, 2.2, 4.0, 7.0],
            total_duration=10.0,
            noise_level=0.005
        )
        test_suite.append(info6)
        
        # Test 7: Single beep
        _, info7 = self.create_test_with_template(
            "single_beep",
            [3.0],
            total_duration=6.0,
            noise_level=0.005
        )
        test_suite.append(info7)
        
        # Save test suite manifest
        manifest_path = "testing-files/test_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(test_suite, f, indent=2)
        
        print(f"✅ Created {len(test_suite)} test files in testing-files/")
        
        # Print summary
        print("\n📊 Test Suite Summary:")
        for i, test in enumerate(test_suite, 1):
            print(f"{i:2d}. {test['filename']}")
            print(f"     {test['description']}")
            print(f"     Ground truth: {[f'{t:.2f}s' for t in test['ground_truth']]}")
            print()
        
        return test_suite

if __name__ == "__main__":
    generator = TestAudioGenerator()
    test_suite = generator.create_comprehensive_test_suite()
    
    print("🎯 Test files ready for accuracy validation!")
    print("📁 Location: testing-files/")
    print("📋 Manifest: testing-files/test_manifest.json")