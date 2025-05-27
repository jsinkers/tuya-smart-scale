# Tuya Smart Scale Home Assistant Integration

A Home Assistant custom integration for Tuya smart scales that fetches user measurement data from the Tuya Cloud API. This integration supports multiple users per scale and exposes all body composition metrics as Home Assistant sensors. The official Tuya integration does not support body fat scales, so this custom integration fills that gap.

## Features

- **Multi-User Support**: Automatically discovers and creates sensors for all users associated with your smart scale
- **Body Composition Analysis**: Exposes 20 different metrics including weight, BMI, body fat, muscle mass, water percentage, bone mass, and more
- **Tuya Cloud API Integration**: Uses official Tuya v2.0 Cloud API with proper authentication and signature handling
- **Easy Configuration**: Simple setup through Home Assistant's config flow UI
- **Real-time Updates**: Automatically fetches latest measurements and analysis reports
- **Smart Data Handling**: Handles Tuya API quirks (like "wegith" typo) transparently

## Installation

### Installation via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jsinkers&repository=tuya-smart-scale&category=integration)

1. Install [HACS](https://hacs.xyz/) if you haven't already
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Add `https://github.com/jsinkers/tuya_smart_scale` as Integration
3. Install "Tuya Smart Scale" from HACS
4. Restart Home Assistant
5. Add integration via Settings → Devices & Services → Add Integration

### Manual Installation

1. Copy the `tuya_scale` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/tuya_scale/
   ```

2. Restart Home Assistant

3. The integration will be available in **Settings** → **Devices & Services** → **Add Integration**

## Configuration

### Prerequisites

You need Tuya Cloud API credentials:

1. Create a Tuya Developer Account at [Tuya IoT Platform](https://iot.tuya.com/)
2. Create a new project and obtain:
   - **Access ID** (Client ID)
   - **Access Key** (Client Secret)
   - **Device ID** of your smart scale
3. Select your region (Americas, Europe, China, or India)

### Setup in Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** and search for "Tuya Smart Scale"
3. Enter your Tuya Cloud API credentials:
   - Access ID
   - Access Key  
   - Device ID
   - Region
4. Click **Submit**

The integration will automatically:
- Validate your credentials
- Discover all users associated with the scale
- Create sensors for each user's measurements
- Start fetching data every 60 seconds

## Usage

Once configured, you'll see sensors for each user in the format:
- `sensor.tuya_scale_[nickname]_weight`
- `sensor.tuya_scale_[nickname]_body_fat`
- `sensor.tuya_scale_[nickname]_bmi`
- etc.

Use these sensors in:
- **Dashboards**: Display current measurements and trends
- **Automations**: Trigger actions based on weight changes or health metrics
- **Scripts**: Create custom health tracking workflows
- **History**: View long-term trends and progress

## Supported Sensors

The integration creates the following sensors for each user:

### Basic Measurements

A weight record from the scale includes:
- **Weight** (kg) 
- **Height** (cm)
- **Body Resistance** (Ω)
- **Measurement Time** (timestamp)

### Body Composition Analysis

Analysis reports for a given weight record include:
- **BMI** - Body Mass Index
- **Body Fat** (%) - Body fat percentage  
- **Muscle Mass** (kg)
- **Body Water** (%) - Body water percentage
- **Bone Mass** (kg)
- **Visceral Fat** - Visceral fat rating
- **Protein** (kg)
- **Fat-Free Mass (FFM)** (kg)
- **Metabolism** - Basal metabolic rate
- **Body Age** (years)
- **Body Score** - Overall body score
- **Body Type** - Body type classification

### User Information

- **User ID** - Tuya user identifier
- **Device ID** - Scale device identifier
- **Nickname** - User's display name

## Troubleshooting

### Common Issues

**"Invalid credentials" error:**
- Verify your Access ID and Access Key are correct
- Ensure you've selected the correct region
- Check that your Tuya project has the necessary permissions

**"Device not found" error:**
- Confirm the Device ID is correct (found in Tuya Smart app)
- Ensure the device is online and accessible via Tuya Cloud

**No recent data:**
- The integration only fetches data when measurements exist
- Use your scale to generate new measurements
- Check that the scale is connected to Wi-Fi and syncing to Tuya Cloud

## Technical Details

- **API Version**: Tuya Cloud API v2.0
- **Update Interval**: 60 seconds
- **Data Source**: Tuya Cloud (not local device communication)
- **Authentication**: OAuth 2.0 with signature-based requests
- **Version**: 0.1 (Initial Release)

## Contributing

This integration is open source. Contributions, bug reports, and feature requests are welcome on GitHub.

## License

This project is licensed under the MIT License.