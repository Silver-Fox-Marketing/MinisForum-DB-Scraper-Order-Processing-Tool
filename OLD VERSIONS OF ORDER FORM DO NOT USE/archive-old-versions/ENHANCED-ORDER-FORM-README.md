# Silver Fox Marketing - Enhanced Order Processing Tool

## Overview
Enhanced order processing form with variable data printing support for VersaWorks. Features multiple conditional workflows, bulk entry capabilities, and automated CSV generation with Google Drive integration.

## Features

### ✅ Current Features
- **Complete Conditional Logic**: All original form workflows preserved
- **Multi-Field Entry**: Spreadsheet-style bulk entry for Windshields, Body Sides, and Complements
- **CSV Export for VersaWorks**: Quantity expansion (5 qty = 5 individual rows)
- **Google Drive Integration**: Automatic upload to organized folders
- **Auto-Save & Crash Protection**: Prevents data loss if browser closes accidentally
- **Silver Fox Branding**: Professional styling with brand colors
- **Order Summary**: Formatted for Pipedrive CRM integration

### 🏗️ Order Types Supported
1. **Vehicle Merchandising** - Windshield banners, side graphics, complements, specially sized
2. **Dealership Merchandising** - Interior/exterior showroom graphics with advanced options
3. **Custom Special Products** - Flexible specifications and requirements
4. **New Template Requests** - Template creation with detailed requirements
5. **Business Cards** - Single/double sided with quantity options
6. **Custom Banners** - Standard and pole banners with finishing options

## Quick Start

### Basic Usage
1. Open `index.html` in a web browser
2. Select order type from dropdown
3. Fill in conditional fields (appear based on selections)
4. For bulk orders: Click "Enter Multiple Items" (Windshields/Body Sides/Complements)
5. Export CSV for VersaWorks or copy summary for Pipedrive

### Google Drive Setup
1. Follow instructions in `GOOGLE_DRIVE_SETUP.md`
2. Get Google Cloud API credentials
3. Update CLIENT_ID and API_KEY in `index-with-drive.html`
4. Test connection and automatic uploads

## File Structure
```
silver-fox-order-form-enhanced/
├── index.html                  # Standard version
├── index-with-drive.html      # Version with Google Drive integration
├── README.md                  # This file
├── GOOGLE_DRIVE_SETUP.md     # Google Drive configuration guide
└── PIPEDRIVE_INTEGRATION.md  # Future implementation guide
```

## Variable Data Printing Workflow

### VersaWorks CSV Format
The CSV export creates individual rows for each item to be printed:

**Input:** Quantity: 5, Message: "Sale Price $29,999"  
**Output:** 5 separate CSV rows, each with quantity: 1

This ensures VersaWorks processes each graphic individually for variable data printing.

### Variable Data Products with Size (Static Size Requirement)

#### **Critical VersaWorks Constraint:**
VersaWorks cannot process variable data CSVs with mixed sizes. All items in one CSV must use the **same size**.

#### **Universal Rule:**
**Any product with both SIZE fields AND "Multiple Items" capability must implement static size logic.**

#### **Standard Size-First Workflow (Applied to ALL products with Size + Multiple Items):**
1. **Select Product Type:** (e.g., Vehicle Merchandising → Windshields)
2. **Choose Size FIRST:** Must select size before bulk entry (Small, Medium (STD), Large)
3. **Size Gets Locked:** Size dropdown becomes disabled with green "Size Locked" indicator
4. **Multiple Items Button Appears:** Only available after size selection
5. **Bulk Entry:** Size is static, other fields (Material, etc.) can vary per vehicle
6. **CSV Export:** All rows use the locked size, other fields can differ

#### **Products Using This Logic:**
- **Windshields** - Size: Small, Medium (STD), Large
- **Future Products** - Any product with size options and bulk entry capability

#### **Example Static Size CSV:**
```csv
Quantity,Vehicle Type,Message Line 1,Message Line 2,Price,Material,Size
"1","SUV","Sale Price $29,999","","","Summer Vinyl","Medium (STD)"
"1","Truck","Sale Price $34,999","","","Winter Vinyl","Medium (STD)"
"1","Sedan","Sale Price $22,999","","","Perforated Vinyl","Medium (STD)"
```

**Notice:** Size column is identical (Medium (STD)) but Material varies per vehicle.

### Standard Product Example:
```csv
Quantity,Vehicle Type,Message Line 1,Message Line 2,Price,Color,Size
"1","SUV","Sale Price $29,999","","","Red","Large"
"1","SUV","Sale Price $29,999","","","Red","Large"
"1","SUV","Sale Price $29,999","","","Red","Large"
```

## Google Drive Integration

### Features
- **Automatic Upload**: CSV files automatically saved to Google Drive
- **Folder Organization**: Customizable folder structure
- **Local + Cloud**: Downloads locally AND uploads to Drive
- **Settings Persistence**: Remembers your preferences
- **Visual Status**: Connection indicator in header

### Setup Instructions

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" (or select existing project)
3. Name it "Silver Fox Order Form"
4. Note your project ID for later

#### Step 2: Enable Google Drive API
1. In your project, navigate to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"
4. Wait for the API to be enabled (few seconds)

#### Step 3: Create API Key
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key immediately (looks like: AIzaSyB-1234567890abcdefg)
4. Optional: Click "Restrict Key" for security:
   - Under "API restrictions", select "Restrict key"
   - Choose "Google Drive API" from the list
   - Save changes

#### Step 4: Create OAuth 2.0 Client ID
1. Click "Create Credentials" > "OAuth client ID"
2. If prompted, configure OAuth consent screen first:
   - Choose "External" for user type
   - App name: "Silver Fox Order Form"
   - User support email: Your email
   - Developer contact: Your email
   - Save and continue through remaining screens
3. Back at OAuth client ID creation:
   - Application type: "Web application"
   - Name: "Silver Fox Order Form Client"
4. Add Authorized JavaScript origins:
   - Click "Add URI" under Authorized JavaScript origins
   - Add: `http://localhost` (for testing)
   - Add: `http://localhost:8000` (if using Python server)
   - Add: Your production domain (e.g., `https://yourdomain.com`)
5. Copy the Client ID (looks like: 123456789-abcdefg.apps.googleusercontent.com)

#### Step 5: Update Credentials in Code
1. Open `index-with-drive.html`
2. Find these lines (around line 578-579):
```javascript
const CLIENT_ID = 'YOUR_CLIENT_ID.apps.googleusercontent.com';
const API_KEY = 'YOUR_API_KEY';
```
3. Replace with your actual credentials:
```javascript
const CLIENT_ID = '123456789-abcdefg.apps.googleusercontent.com';
const API_KEY = 'AIzaSyB-1234567890abcdefg';
```
4. Save the file

#### Step 6: Test the Integration
1. Serve the file via HTTP (not file://):
   - Python 3: `python -m http.server 8000`
   - Node.js: `npx http-server`
   - Or upload to web server
2. Open in browser: `http://localhost:8000/index-with-drive.html`
3. Click "Connect" button in header
4. Sign in with Google account
5. Grant permissions when prompted
6. Status should show "Connected" (green indicator)

#### Step 7: Test CSV Upload
1. Select order type and fill form
2. For bulk orders, use "Enter Multiple Items" button
3. Click "Export to CSV"
4. Verify:
   - File downloads locally
   - "Upload successful" notification appears
   - Check Google Drive for the file in Silver Fox Orders/CSV Exports/

### Default Structure
```
Google Drive/
└── Silver Fox Orders/
    └── CSV Exports/
        ├── silver-fox-order-2024-01-15T10-30-45.csv
        └── silver-fox-order-2024-01-15T14-22-10.csv
```

### Troubleshooting

#### "Failed to initialize Google API"
- Verify API key is correct
- Ensure Google Drive API is enabled in Cloud Console
- Check browser console for specific error

#### "Not authorized" or CORS errors
- Ensure you're serving via HTTP, not opening file directly
- Verify OAuth client origins include your domain
- Check that Client ID is correct

#### Files not uploading
- Confirm you're signed in (green "Connected" status)
- Check browser console for errors
- Verify internet connection
- Ensure popup blockers aren't blocking Google sign-in

#### "Popup blocked" during sign-in
- Allow popups for your domain
- Try clicking Connect button again
- Use Chrome or Firefox for best compatibility

## Auto-Save & Crash Protection

### How It Works
- **Automatic Saving**: Form data auto-saves every 5 seconds while you work
- **Clean Start**: Form opens empty by default for new orders
- **Crash Recovery**: If browser closes accidentally, cached data is preserved
- **Smart Notifications**: Restore prompt appears when cached data is available

### User Experience
1. **Fill out form** - Data auto-saves in background
2. **Browser crashes/closes** - Data is preserved locally
3. **Reopen form** - Yellow notification appears with restore option
4. **Choose to restore** - Previous form state is fully recovered
5. **Or start fresh** - Discard cached data and begin new order

### Features
- ✅ **24-hour cache expiry** - Old data automatically cleaned up
- ✅ **Smart restore** - Preserves order type, product selections, all fields
- ✅ **Multiple items data** - Bulk entry spreadsheet data included
- ✅ **Visual indicators** - Auto-save timestamp shown briefly
- ✅ **No interference** - Cache doesn't affect normal form operation

### Cache Management
- **Manual clear**: "Clear Form" button removes cached data
- **Auto-expire**: Cache expires after 24 hours
- **Privacy**: All data stored locally in browser only
- **No server storage**: Uses localStorage for maximum privacy

## 🚀 Future Implementations

### Pipedrive API Integration
**Status**: Planned for next release  
**Complexity**: Moderate  
**Timeline**: 2-3 weeks

#### Planned Features:
1. **Automatic Deal Creation**: Submit form → Create Pipedrive deal
2. **CSV Attachment**: Attach exported CSV to the deal
3. **Contact Sync**: Update/create contact information
4. **Pipeline Management**: Move deals through stages automatically
5. **Activity Logging**: Track order processing activities

#### Technical Requirements:
- **Backend Server**: Node.js/Python API endpoint (CORS restrictions)
- **Authentication**: Pipedrive API token
- **Data Mapping**: Form fields → Pipedrive custom fields
- **Error Handling**: Retry logic and user notifications

#### Implementation Options:
1. **Server-Side Integration** (Recommended)
   - Secure API token storage
   - Advanced error handling
   - Bulk operations support
   - Background processing

2. **Serverless Functions** (Netlify/Vercel)
   - No server maintenance
   - Automatic scaling
   - Cost-effective
   - Easy deployment

3. **Zapier/Make Integration** (No-Code)
   - Quick setup
   - Visual workflow builder
   - Multiple app connections
   - No development needed

#### API Endpoints Planned:
```javascript
// Create deal with order details
POST /api/pipedrive/deals
{
    "title": "Order - Vehicle Merchandising",
    "value": estimatedValue,
    "person_id": contactId,
    "org_id": organizationId,
    "custom_fields": {
        "order_type": "Vehicle Merchandising",
        "product_type": "Windshields",
        "quantity": totalQuantity,
        "csv_file_url": driveFileUrl
    }
}

// Update deal status
PUT /api/pipedrive/deals/{id}
{
    "stage_id": completedStageId,
    "status": "won"
}

// Add activity/note
POST /api/pipedrive/activities
{
    "subject": "CSV exported to Google Drive",
    "deal_id": dealId,
    "note": csvSummary
}
```

#### Benefits:
- **Automated Workflow**: Form → Pipedrive → Google Drive
- **Better Tracking**: All orders in CRM pipeline
- **Team Collaboration**: Shared visibility on order status
- **Reporting**: Built-in Pipedrive analytics
- **Integration**: Works with existing Pipedrive setup

### Other Future Enhancements
1. **Email Notifications**: Order confirmations and status updates
2. **Inventory Integration**: Check material availability
3. **Pricing Calculator**: Dynamic pricing based on specifications
4. **QR Code Generation**: Direct QR codes for tracking
5. **Multi-Language Support**: Spanish language option
6. **Mobile Optimization**: Tablet-friendly interface
7. **Advanced Templates**: More conditional logic options

## Development Setup

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Google Cloud Platform account (for Drive integration)
- Text editor for configuration

### Configuration
1. **Google Drive Setup**: Follow `GOOGLE_DRIVE_SETUP.md`
2. **Local Testing**: Serve files via local HTTP server
3. **Production Deploy**: Upload to web server or CDN

### Browser Compatibility
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## Support & Maintenance

### Troubleshooting
- Check browser console for errors
- Verify Google API credentials
- Test internet connection for Drive uploads
- Clear browser cache if issues persist

### Updates
- Monitor Google API changes
- Test form functionality monthly
- Update dependencies as needed
- Backup configurations before changes

## License
Proprietary - Silver Fox Marketing Internal Use

## Contact
For technical support or feature requests, contact the Silver Fox Marketing development team.

---

**Version**: 2.0  
**Last Updated**: January 2025  
**Maintained by**: Silver Fox Marketing Team