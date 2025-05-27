# Tuya Smart Scale Utilities

Standalone Python utilities for downloading and analyzing data from Tuya smart scales without Home Assistant.

## Overview

The **Tuya Scale Data Downloader** is a standalone Python script that downloads measurement data from your Tuya smart scale using the official Tuya Cloud API. It fetches both raw measurement data and detailed body composition analysis reports, storing everything in a local JSON file for further analysis.

## Features

- **Direct API Integration**: Uses Tuya Cloud API v2.0 with proper authentication (no external dependencies like `tuya_connector`)
- **Incremental Updates**: Only downloads new records since the last run
- **Body Composition Analysis**: Automatically generates detailed analysis reports for measurements with valid resistance data
- **Multi-User Support**: Handles multiple users per scale device
- **Robust Error Handling**: Comprehensive logging and error recovery
- **JSON Output**: Saves data in structured JSON format for easy analysis

## Requirements

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Tuya Cloud API Credentials

You'll need to set up a Tuya Cloud project and get API credentials:

1. **Create Tuya Cloud Account**: Sign up at [Tuya IoT Platform](https://iot.tuya.com/)
2. **Create Cloud Project**: 
   - Go to Cloud → Development → Create Cloud Project
   - Select your region and project type
3. **Get API Credentials**: Note down your `Access ID` and `Access Key`
4. **Link Your Device**: Add your smart scale to the project
5. **Get Device ID**: Find your scale's device ID in the device list

## Setup

### 1. Environment Configuration

Create a `.env` file in the utilities directory:

```bash
# Tuya Cloud API Credentials
ACCESS_ID=your_tuya_access_id_here
ACCESS_KEY=your_tuya_access_key_here
DEVICE_ID=your_scale_device_id_here
REGION=eu  # Options: us, eu, cn, in

# Personal Information (for body composition analysis)
BIRTHDATE=1900-01-30  # Format: YYYY-MM-DD

# Optional Configuration
DATA_FILE=scale_data.json  # Output file name
DEBUG_LOGS=false  # Set to 'true' for detailed debugging
```

### 2. First Run

Run the downloader to fetch all historical data:

```bash
python tuya_scale_downloader.py
```

### 3. Regular Updates

Run the same command regularly to fetch new measurements:

```bash
# The script automatically detects the last downloaded record
# and only fetches new data since then
python tuya_scale_downloader.py
```

## How It Works

### 1. **Authentication**
- Generates secure HMAC-SHA256 signatures for Tuya API requests
- Automatically handles access token management and renewal

### 2. **Data Retrieval**
- Fetches measurement records from the Tuya Cloud API with pagination
- Downloads data incrementally (only new records since last run)
- Handles API rate limits and error recovery

### 3. **Body Composition Analysis**
- For each measurement with valid resistance data, requests detailed analysis
- Calculates age at time of measurement for accurate body composition
- Enriches raw scale data with BMI, body fat, muscle mass, etc.

### 4. **Data Storage**
- Saves all data in structured JSON format
- Maintains chronological order of measurements
- Preserves both raw scale data and analysis reports

### 5. **Incremental Updates**
- Tracks the timestamp of the most recent record
- On subsequent runs, only downloads newer data
- Prevents duplicate records and reduces API usage

## Output Format

The script creates a `scale_data.json` file with an array of measurement records. Each record contains:

### Raw Scale Data
- **Weight, Height**: Physical measurements
- **Body Resistance**: Used for body composition analysis  
- **Timestamps**: When the measurement was taken
- **User Information**: Tuya user ID and nickname

### Analysis Reports (when available)
- **Body Composition**: Fat percentage, muscle mass, bone mass
- **Health Metrics**: BMI, visceral fat, body age, body score
- **Metabolic Data**: Basal metabolic rate, body water percentage

## Data Dictionary for `scale_data.json`

| Field Name         | Description                                      | Units          |
|--------------------|--------------------------------------------------|----------------|
| `body_r`           | Body resistance measurement from scale           | Ohms           |
| `create_time`      | Timestamp when the record was created            | milliseconds since Unix epoch |
| `device_id`        | Unique identifier for the scale device           | string         |
| `height`           | Height measurement                               | centimeters    |
| `id`               | Unique identifier for the record                 | string         |
| `nick_name`        | User's nickname in Tuya platform                | string         |
| `user_id`          | Unique identifier for the user                   | string         |
| `wegith`           | Weight measurement (Tuya API typo)               | kilograms      |
| **Analysis Report Fields** _(when resistance data available)_ |                |
| `bmi`              | Body Mass Index                                  | unitless       |
| `body_age`         | Estimated physical age                           | years          |
| `body_score`       | Overall body composition score                   | unitless       |
| `body_type`        | Body type classification                         | numeric code   |
| `bones`            | Bone mass                                        | kilograms      |
| `fat`              | Body fat percentage                              | percentage     |
| `ffm`              | Fat-free mass (lean body mass)                   | kilograms      |
| `metabolism`       | Basal metabolic rate                             | kcal/day       |
| `muscle`           | Muscle mass                                      | kilograms      |
| `protein`          | Protein percentage                               | percentage     |
| `visceral_fat`     | Visceral fat level                               | rating scale   |
| `water`            | Body water percentage                            | percentage     |

## Usage Examples

### Basic Data Download
```bash
# Download all new measurements
python tuya_scale_downloader.py
```

### With Debug Logging
```bash
# Enable detailed logging for troubleshooting
DEBUG_LOGS=true python tuya_scale_downloader.py
```

### Custom Output File
```bash
# Save to a specific file
DATA_FILE=my_scale_data.json python tuya_scale_downloader.py
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure your `.env` file has all required fields
   - Check that ACCESS_ID, ACCESS_KEY, DEVICE_ID, and BIRTHDATE are set

2. **"Authentication failed"**
   - Verify your Tuya Cloud API credentials
   - Ensure your device is linked to your Tuya Cloud project
   - Check that you're using the correct region (us/eu/cn/in)

3. **"No analysis reports generated"**
   - Analysis reports require valid body resistance data (`body_r > 0`). Some measurements may not have resistance data e.g. if wearing shoes/socks.

### Debug Mode

Enable detailed logging to diagnose issues:

```bash
DEBUG_LOGS=true python tuya_scale_downloader.py
```

This will show:
- API request URLs and headers
- Response status codes and data
- Detailed error messages
- Processing steps for each record

## API Reference

- **Tuya Cloud API Documentation**: https://developer.tuya.com/en/docs/cloud/body-fat-scale?id=K9jgsgbn2mxcl
- **Scale Data API**: https://developer.tuya.com/en/docs/cloud/scale-data-service?id=Kb3owhrnwjlxo
- **Analysis Reports API**: https://developer.tuya.com/en/docs/cloud/body-analysis-service?id=Kb3owhrnwj2k8