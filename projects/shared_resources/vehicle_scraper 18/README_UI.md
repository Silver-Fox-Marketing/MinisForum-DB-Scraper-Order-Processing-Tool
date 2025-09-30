# Vehicle Scraper Web UI

A user-friendly web interface for selecting and running vehicle scrapers from 41 automotive dealerships.

## Features

🚗 **Easy Scraper Selection**
- Visual grid of all 41 available scrapers
- Search functionality to find specific dealerships
- Quick selection presets (Joe Machens, Suntrup, etc.)
- Select all/none options

📊 **Real-time Monitoring**
- Live status updates for running scrapers
- Real-time log streaming
- Progress tracking with visual indicators
- Auto-refreshing status every 5 seconds

🔧 **Management Controls**
- Start/stop individual scrapers
- Download log files
- View detailed execution logs
- Error handling and reporting

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_ui.txt
```

### 2. Start the Web Interface
```bash
python scraper_ui.py
```

### 3. Access the Interface
Open your web browser and go to:
```
http://localhost:5000
```

## Usage

### Main Interface
1. **Browse Available Scrapers**: View all 41 dealership scrapers in an organized grid
2. **Search**: Use the search box to find specific dealerships
3. **Select Scrapers**: Check the boxes for the scrapers you want to run
4. **Quick Presets**: Use preset buttons for common selections
5. **Run**: Click "Run Selected Scrapers" to start execution

### Monitoring Execution
- **Results Page**: See immediate status of all started scrapers
- **Live Logs**: Click "View Live Logs" to see real-time output
- **Auto-refresh**: Status updates automatically every 5 seconds
- **Controls**: Stop running scrapers or download logs

### Available Scrapers

**Joe Machens Dealerships (4)**
- Joe Machens Nissan ✅ (Recently Updated - Dealer Inspire Support)
- Joe Machens Toyota
- Joe Machens Hyundai
- Joe Machens CDJR

**Suntrup Dealerships (5)**
- Suntrup Ford Kirkwood
- Suntrup Ford West
- Suntrup Buick GMC
- Suntrup Hyundai South
- Suntrup Kia South

**Other Major Dealerships (32)**
- BMW of West St. Louis
- Columbia BMW/Honda
- Audi/Jaguar/Land Rover Ranch Mirage
- And 29+ more dealerships

## File Structure

```
vehicle_scraper 18/
├── scraper_ui.py          # Main Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with styling
│   ├── index.html        # Main selection page
│   ├── results.html      # Execution results page
│   └── logs.html         # Live logs viewer
├── scrapers/             # Individual scraper modules
├── output_data/          # Generated scraper output
└── requirements_ui.txt   # Python dependencies
```

## Features in Detail

### Smart Selection
- **Search Filter**: Type to filter dealerships by name
- **Preset Groups**: Quick selection for dealership groups
- **Visual Feedback**: Selected items are highlighted
- **Status Indicators**: See which scrapers are ready/running/completed

### Real-time Monitoring
- **Live Status**: See running scrapers update in real-time
- **Log Streaming**: Watch scraper output as it happens
- **Progress Indicators**: Visual status with color coding
- **Auto-refresh**: Updates every 5 seconds automatically

### Management
- **Stop Control**: Stop running scrapers if needed
- **Log Download**: Save log files for later analysis
- **Error Handling**: Clear error messages and status
- **Output Organization**: Each run creates timestamped folders

## Output

Each scraper run creates:
```
output_data/
└── [scraper_name]_[timestamp]/
    ├── [scraper_name]_vehicles.csv    # Main vehicle data
    └── log/
        ├── vehicles_processed.json     # Processing log
        └── [various log files]         # Debug/error logs
```

## Status Indicators

- 🔵 **Ready**: Scraper is available to run
- 🟡 **Running**: Scraper is currently executing (animated)
- 🟢 **Completed**: Scraper finished successfully
- 🔴 **Failed**: Scraper encountered an error

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# If port 5000 is busy, edit scraper_ui.py line 284:
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

**Missing Dependencies**
```bash
pip install flask werkzeug
```

**Scrapers Not Found**
- Ensure you're running from the correct directory
- Check that `scrapers/` folder exists with `.py` files

**Permission Errors**
- Run as administrator if needed
- Check write permissions for `output_data/` folder

## Development

The UI is built with:
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Real-time Updates**: AJAX polling
- **Responsive Design**: Works on desktop and mobile

To add new scrapers, simply place `.py` files in the `scrapers/` directory following the existing naming convention.

## Security Notes

- UI runs on localhost only by default
- No authentication (local use only)
- Scrapers run with current user permissions
- Log files may contain URLs and data from scraped sites