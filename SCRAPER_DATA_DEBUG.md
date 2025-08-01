# Scraper Data Flow Debug Guide

## Issue: "Scraper started successfully - Waiting for data" but no progress shown

## Fixes Applied

### 1. Added Missing WebSocket Event Listener
The frontend was missing the `scraper_output` event listener that the backend emits.

**Added to `app.js`:**
```javascript
this.socket.on('scraper_output', (data) => {
    this.handleScraperOutput(data);
});
```

### 2. Created `handleScraperOutput` Method
Handles raw scraper output messages from the backend.

```javascript
handleScraperOutput(data) {
    // Handle raw scraper output messages
    console.log('Scraper output received:', data);
    
    if (data.message) {
        this.addScraperConsoleMessage(data.message, data.type || 'info');
    }
    
    if (data.status) {
        this.addScraperConsoleMessage(`Status: ${data.status}`, 'info');
    }
    
    // Update progress if available
    if (data.progress !== undefined) {
        this.updateProgressBar(data.progress);
    }
    
    // Update indicators if available
    this.updateScraperConsoleIndicators(data);
}
```

### 3. Enhanced Demo Mode with Progress Simulation
Added realistic demo scraper output to test the data flow.

**Demo sequence:**
1. Starting message (immediate)
2. Processing message with progress (after 2s)
3. Completion message (after 5s total)

## Testing Steps

1. **Select Dealerships**: Choose one or more dealerships
2. **Start Scraper**: Click "Start Scrape" button
3. **Watch Console**: Should see:
   - ✅ "Scraper started successfully - Waiting for data..."
   - 🔄 "DEMO: Starting scraper for [dealership]"
   - 📊 "DEMO: Processing pages for [dealership]"
   - 🏁 "DEMO: Completed scraper for [dealership]"

## Debugging Commands

### Check Browser Console
Open browser DevTools (F12) and look for:
- `Scraper output received:` logs
- Any WebSocket connection errors
- Socket.IO connection status

### Check Network Tab
Look for:
- POST to `/api/scrapers/start` (should return 200)
- WebSocket connection to `/socket.io/`

### Check Server Logs
Server should show:
- Scraper start messages
- Socket.IO emissions
- Background thread execution

## Expected Results

**Before Fix:**
- ✅ "Scraper started successfully - Waiting for data..."
- (No further updates)

**After Fix:**
- ✅ "Scraper started successfully - Waiting for data..."
- 🔄 Demo scraper progress messages
- 📊 Progress bar updates
- 🏁 Completion notifications

## Files Modified

- `web_gui/app.py` - Added demo scraper simulation
- `web_gui/static/js/app.js` - Added WebSocket event handling

If you still see no data after these fixes, check:
1. Browser console for JavaScript errors
2. WebSocket connection in Network tab
3. Server logs for Socket.IO emissions