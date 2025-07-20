# Alpen-Paesse Home Assistant Integration

A Home Assistant custom integration that monitors Swiss Alpine pass conditions from alpen-paesse.ch with configurable pass selection and regular updates.

## Features

- **Swiss Alpine Passes Supported**: Monitor conditions for major Alpine passes including Gotthardpass, Furkapass, Grimselpass, and many more
- **Three Sensors Per Pass**: 
  - Status
  - Temperature (°C)
  - Last Update
- **Configurable Pass Selection**: Choose which passes to monitor through the Home Assistant UI
- **Device Grouping**: Each pass appears as a separate device with its three sensors
- **Hourly Updates**: Automatically fetches fresh data every 60 minutes
- **Proper Error Handling**: Graceful handling of network issues and parsing errors

## Installation
1. Copy the `custom_components/alpen_paesse` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration → Integrations
4. Click "Add Integration" and search for "Alpen-Paesse"
5. Select the Alpine passes you want to monitor

## Configuration
The integration uses a config flow for easy setup through the Home Assistant UI. You can:

- Select multiple passes to monitor
- Reconfigure pass selection at any time
- Each pass creates a device with three sensors

## Technical Details
- **Data Source**: Scrapes alpen-paesse.ch using proper HTTP headers
- **Update Interval**: 3600 seconds (1 hour)
- **Parsing**: CSS selectors extract status, temperature, and timestamps
- **Error Handling**: Continues operating if some passes are temporarily unavailable
- **Concurrent Requests**: Limited to 3 simultaneous requests to respect the website


## Development
The integration follows Home Assistant development standards:
- Modern config flow pattern
- DataUpdateCoordinator for efficient data management
- Proper device and entity structure
- Comprehensive error handling and logging

## Contributing
This integration follows Home Assistant custom component best practices. Feel free to submit issues or improvements.

## License
This integration is provided as-is for monitoring Swiss Alpine pass conditions. Data is sourced from alpen-paesse.ch under their terms of service.
