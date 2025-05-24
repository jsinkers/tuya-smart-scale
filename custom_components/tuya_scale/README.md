# Tuya Smart Scale Integration

This project provides an integration for Home Assistant to download and manage data from Tuya smart scales. The integration allows users to monitor their weight and other related metrics directly within Home Assistant.

## Features

- Fetch and display weight data from Tuya smart scales.
- Easy configuration through the Home Assistant UI.
- Supports multiple smart scale devices.

## Installation

1. Clone this repository to your Home Assistant `custom_components` directory:
   ```
   git clone https://github.com/yourusername/tuya_smart_scale.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Restart Home Assistant.

## Configuration

To set up the Tuya Smart Scale integration, follow these steps:

1. Go to the Home Assistant UI.
2. Navigate to `Configuration` > `Integrations`.
3. Click on `Add Integration` and search for `Tuya Smart Scale`.
4. Follow the prompts to enter your Tuya account credentials and configure your devices.

## Usage

Once configured, the Tuya Smart Scale integration will automatically fetch data from your smart scales. You can view the data in the Home Assistant dashboard and create automations based on the scale readings.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.