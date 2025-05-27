# Tuya Smart Scales Utilities

## Data download

- run `python download_scale_data.py` to fetch the latest measurements and analysis reports from your Tuya Body Fat Scale
- Python script to download data from Tuya Body Fat Scale. It first downloads the history measurements and then gets the detailed analysis report for each measurement. Only new records that have not been downloaded before are fetched. Records are saved in a JSON file `scale_data.json`.
- Tuya API keys need to be provided in the `.env` file.
- API Documentation at https://developer.tuya.com/en/docs/cloud/body-fat-scale?id=K9jgsgbn2mxcl

## Data Dictionary for `scale_data.json`

This document provides a description of each field in the `scale_data.json` file along with their units.

| Field Name         | Description                                      | Units          |
|--------------------|--------------------------------------------------|----------------|
| `body_r`           | Resistance measurement from scale                | Ohms (?)       |
| `create_time`      | Timestamp when the record was created            | milliseconds since Unix epoch |
| `device_id`        | Unique identifier for the device                 | string         |
| `height`           | Height measurement                               | centimeters    |
| `id`               | Unique identifier for the record                 | string         |
| `nickname`         | Tuya Nickname of the user                        | string         |
| `user_id`          | Tuya Unique identifier for the user              | string         |
| `wegith`           | Weight measurement (typo from Tuya API)          | kilograms      |
| `analysis_report`  | Detailed analysis report for the record          | JSON object    |
| `bmi`              | Body Mass Index                                  | unitless       |
| `body_age`         | Physical age                                         | years          |
| `body_score`       | Body score                                       | unitless       |
| `body_type`        | Body type                                        | unitless       |
| `bones`            | Bone mass                                        | kilograms      |
| `fat`              | Body fat percentage                              | percentage     |
| `ffm`              | Fat-free mass (Lean body mass)                                    | kilograms      |
| `metabolism`       | Basal metabolic rate                                       | unitless       |
| `muscle`           | Muscle mass                                      | kilograms      |
| `protein`          | Protein                                          | kilograms      |
| `visceral_fat`     | Visceral fat rating                               | unitless       |
| `water`            | Body water percentage                            | percentage     |