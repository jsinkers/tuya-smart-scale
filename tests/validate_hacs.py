#!/usr/bin/env python3
"""
HACS Validation Test Script
Validates that the repository structure meets HACS requirements.

Usage:
    cd tests/
    python3 validate_hacs.py

Or from repository root:
    python3 tests/validate_hacs.py
"""

import os
import json
import sys
from pathlib import Path

# Detect if we're running from tests/ directory or repository root
current_dir = os.getcwd()
if current_dir.endswith('/tests'):
    # Running from tests directory
    root_prefix = "../"
else:
    # Running from repository root
    root_prefix = ""

def check_repository_structure():
    """Check if repository structure meets HACS requirements."""
    print("🔍 Checking HACS Repository Structure")
    print("=" * 50)
    
    required_files = [
        f"{root_prefix}README.md",
        f"{root_prefix}hacs.json", 
        f"{root_prefix}custom_components/tuya_smart_scale/__init__.py",
        f"{root_prefix}custom_components/tuya_smart_scale/manifest.json",
        f"{root_prefix}custom_components/tuya_smart_scale/sensor.py",
        f"{root_prefix}LICENSE"
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def validate_manifest_json():
    """Validate manifest.json has required HACS fields."""
    print("\n📄 Validating manifest.json")
    print("=" * 50)
    
    required_fields = ["domain", "name", "version", "documentation", "issue_tracker", "codeowners"]
    
    try:
        with open(f"{root_prefix}custom_components/tuya_smart_scale/manifest.json", "r") as f:
            manifest = json.load(f)
        
        all_good = True
        for field in required_fields:
            if field in manifest:
                print(f"✅ {field}: {manifest[field]}")
            else:
                print(f"❌ {field} - MISSING")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading manifest.json: {e}")
        return False

def validate_hacs_json():
    """Validate hacs.json structure."""
    print("\n🏪 Validating hacs.json")
    print("=" * 50)
    
    try:
        with open(f"{root_prefix}hacs.json", "r") as f:
            hacs_config = json.load(f)
        
        print(f"✅ name: {hacs_config.get('name', 'NOT SET')}")
        
        if "homeassistant" in hacs_config:
            print(f"✅ homeassistant: {hacs_config['homeassistant']}")
        else:
            print("ℹ️  homeassistant: not specified (optional)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading hacs.json: {e}")
        return False

def check_integration_files():
    """Check all integration files exist and have no obvious issues."""
    print("\n🔧 Checking Integration Files")
    print("=" * 50)
    
    integration_files = [
        f"{root_prefix}custom_components/tuya_smart_scale/__init__.py",
        f"{root_prefix}custom_components/tuya_smart_scale/api.py", 
        f"{root_prefix}custom_components/tuya_smart_scale/config_flow.py",
        f"{root_prefix}custom_components/tuya_smart_scale/const.py",
        f"{root_prefix}custom_components/tuya_smart_scale/coordinator.py",
        f"{root_prefix}custom_components/tuya_smart_scale/sensor.py"
    ]
    
    all_good = True
    for file_path in integration_files:
        if os.path.exists(file_path):
            # Check file size
            size = os.path.getsize(file_path)
            if size > 0:
                print(f"✅ {file_path} ({size} bytes)")
            else:
                print(f"⚠️  {file_path} (empty file)")
                all_good = False
        else:
            print(f"❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def main():
    """Run all HACS validation checks."""
    print("🏪 HACS Integration Validation")
    print("=" * 60)
    
    checks = [
        check_repository_structure(),
        validate_manifest_json(),
        validate_hacs_json(),
        check_integration_files()
    ]
    
    print("\n📋 Summary")
    print("=" * 50)
    
    if all(checks):
        print("🎉 All HACS requirements are met!")
        print("✅ Repository is ready for HACS compatibility")
        print("\n📝 Next steps:")
        print("   1. Push to GitHub")
        print("   2. Create a release (optional but recommended)")
        print("   3. Users can add via HACS custom repositories")
        return 0
    else:
        print("❌ Some requirements are not met")
        print("🔧 Please fix the issues above before submitting to HACS")
        return 1

if __name__ == "__main__":
    sys.exit(main())
