#!/usr/bin/env python3
"""
CLI tool for testing the Beep Detection API

LOCAL TESTING SCRIPT - Not for deployment
Used to test API endpoints locally and compare detection results
"""
import argparse
import requests
import json
import time
import os
from pathlib import Path


class BeepAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def health_check(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def detect_frequency_beeps(self, audio_file, **params):
        """Test frequency detection endpoint"""
        try:
            files = {"file": open(audio_file, "rb")}
            data = {}
            for key, value in params.items():
                data[key] = str(value)
            
            response = requests.post(
                f"{self.base_url}/detect-frequency-beeps/",
                files=files,
                data=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def detect_template_matches(self, audio_file, **params):
        """Test template matching endpoint"""
        try:
            files = {"file": open(audio_file, "rb")}
            data = {}
            for key, value in params.items():
                data[key] = str(value)
            
            response = requests.post(
                f"{self.base_url}/detect-template-matches/",
                files=files,
                data=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def detect_cross_correlation(self, audio_file, **params):
        """Test cross-correlation endpoint"""
        try:
            files = {"file": open(audio_file, "rb")}
            data = {}
            for key, value in params.items():
                data[key] = str(value)
            
            response = requests.post(
                f"{self.base_url}/detect-cross-correlation/",
                files=files,
                data=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def print_results(title, result):
    """Print results in a formatted way"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    print("Raw response:")
    print(result)
    print("")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Print basic info
    if "filename" in result:
        print(f"📁 File: {result['filename']}")
    if "num_matches" in result:
        print(f"🔢 Matches: {result['num_matches']}")
    if "method" in result:
        print(f"🔬 Method: {result['method']}")
    
    # Print matches
    if "matches" in result and result["matches"]:
        print(f"\n📍 Detected timestamps:")
        for i, timestamp in enumerate(result["matches"][:10]):  # Show first 10
            mm_ss = result["matches_mm_ss"][i] if "matches_mm_ss" in result else f"{timestamp:.3f}"
            print(f"   {i+1:2d}. {mm_ss}")
        
        if len(result["matches"]) > 10:
            print(f"   ... and {len(result['matches']) - 10} more")
    
    # Print parameters
    if any(key in result for key in ["threshold", "sr", "min_separation_s"]):
        print(f"\n⚙️  Parameters:")
        for key in ["threshold", "sr", "min_separation_s", "raw"]:
            if key in result:
                print(f"   {key}: {result[key]}")


def main():
    parser = argparse.ArgumentParser(description="CLI tool for testing Beep Detection API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--file", help="Audio file to test (required for most endpoints)")
    parser.add_argument("--endpoint", choices=["health", "frequency", "template", "cross-correlation", "all"], 
                       default="all", help="Which endpoint to test")
    parser.add_argument("--threshold", type=float, default=0.5, help="Detection threshold")
    parser.add_argument("--min-separation", type=float, default=0.5, help="Minimum separation between beeps")
    parser.add_argument("--sr", type=int, default=22050, help="Sample rate")
    parser.add_argument("--raw", action="store_true", help="Use raw template matching")
    parser.add_argument("--compare", action="store_true", help="Compare results between methods")
    
    args = parser.parse_args()
    
    # Check if file is required
    if args.endpoint not in ["health"] and not args.file:
        print(f"❌ Error: --file is required for endpoint '{args.endpoint}'")
        return
    
    # Check if file exists
    if args.file and not Path(args.file).exists():
        print(f"❌ Error: File '{args.file}' not found")
        return
    
    client = BeepAPIClient(args.url)
    
    print(f"🚀 Testing Beep Detection API at {args.url}")
    print(f"📁 Using audio file: {args.file}")
    
    # Health check first
    if args.endpoint in ["health", "all"]:
        health = client.health_check()
        print_results("Health Check", health)
        
        if "error" in health:
            print("❌ Server is not running. Please start it with: make run")
            return
    
    # Test endpoints
    results = {}
    
    if args.endpoint in ["frequency", "all"]:
        print("\n⏳ Testing frequency detection...")
        result = client.detect_frequency_beeps(args.file)
        results["frequency"] = result
        print_results("Frequency Detection", result)
    
    if args.endpoint in ["template", "all"]:
        print("\n⏳ Testing template matching...")
        result = client.detect_template_matches(
            args.file,
            threshold=args.threshold,
            min_separation_s=args.min_separation,
            sr_target=args.sr,
            raw=args.raw
        )
        results["template"] = result
        print_results("Template Matching", result)
    
    if args.endpoint in ["cross-correlation", "all"]:
        print("\n⏳ Testing cross-correlation...")
        result = client.detect_cross_correlation(
            args.file,
            threshold=args.threshold,
            min_separation_s=args.min_separation,
            sr_target=args.sr
        )
        results["cross-correlation"] = result
        print_results("Cross-Correlation", result)
    
    # Compare results
    if args.compare and len(results) > 1:
        print(f"\n{'='*60}")
        print("📊 COMPARISON")
        print(f"{'='*60}")
        
        for method, result in results.items():
            if "error" not in result and "num_matches" in result:
                print(f"{method:15}: {result['num_matches']:3d} matches")
    
    print(f"\n✅ Testing complete!")


if __name__ == "__main__":
    main()