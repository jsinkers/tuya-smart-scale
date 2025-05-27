# Tuya Smart Scale Integration & Utilities

This repository provides tools for working with Tuya smart scales, including a Home Assistant integration and standalone utilities.

## 🏠 Home Assistant Integration

**Location:** `custom_components/tuya_scale/`

A complete Home Assistant custom integration that automatically discovers users and creates 20+ body composition sensors per user.

**Quick Setup:**

1. Copy `custom_components/tuya_scale/` to your Home Assistant config directory
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services → Add Integration
4. Enter your Tuya Cloud API credentials

See [integration README](custom_components/tuya_scale/README.md) for detailed setup instructions.

## 🔧 Utilities

**Location:** `utilities/`

Standalone Python scripts for downloading and working with Tuya scale data outside of Home Assistant.

- `tuya_scale_downloader.py` - Downloads measurement history and analysis reports to JSON files
- Requires `.env` file with Tuya API credentials
- Incremental updates (only fetches new records)

See [utilities README](utilities/README.md) for usage instructions.

## Requirements

- Tuya Cloud API credentials (Access ID, Access Key, Device ID)
- For Home Assistant: HA 2024.1.0+
- For utilities: Python 3.7+, custom tuya-connector-python

## API Reference

Based on [Tuya Body Fat Scale API Documentation](https://developer.tuya.com/en/docs/cloud/body-fat-scale?id=K9jgsgbn2mxcl)
