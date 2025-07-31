# MinisForum Database Web GUI
## Silver Fox Marketing - Local Dealership Control Interface

### 🎨 **Brand Identity Implementation**
- **Colors**: Official Silver Fox hex codes (`#fd410d`, `#ff8f71`, `#a52b0f`, `#ffffff`, `#220901`, `#8d8d92`, `#ffc817`)
- **Typography**: Calmetta Xbold (headers), Calmetta Regular (accents), Montserrat (body)
- **Design**: Professional interface matching Silver Fox brand guidelines

---

### 🚀 **Quick Start**

1. **Add Custom Fonts** (Required for brand consistency):
   ```
   web_gui/static/fonts/
   ├── Calmetta-Xbold.woff2
   ├── Calmetta-Xbold.woff
   ├── Calmetta-Regular.woff2
   └── Calmetta-Regular.woff
   ```

2. **Start the Server**:
   ```bash
   # Windows
   start_server.bat
   
   # Or manually
   pip install -r requirements.txt
   python app.py
   ```

3. **Access the Interface**:
   - Open browser to: `http://localhost:5000`
   - Local interface only (secure, no external access)

---

### 📋 **Interface Features**

#### **Scraper Control Tab**
- ✅ Visual dealership selection grid (40 dealerships)
- ⚙️ Individual dealership filtering (gear icons)
- 🚀 One-click scraper start
- 📅 Scheduling interface
- 📊 Real-time progress tracking

#### **Data Pipeline Tabs**
- **Raw Data**: Import statistics and validation
- **Normalized Data**: Processed vehicle data overview  
- **Order Processing**: Job status and progress
- **QR Generation**: QR code creation status
- **Adobe Export**: Ready-to-import files

#### **Real-time Terminal**
- 📟 Live system output and error reporting
- 📝 Persistent logging for archival purposes
- 🗑️ Clear terminal functionality
- ⏰ Timestamped entries

---

### 🔧 **Configuration & Settings**

#### **Dealership Filtering Options**
Each dealership can be individually configured:
- ☑️ **Vehicle Types**: New, Pre-Owned, Certified Pre-Owned
- 💰 **Price Ranges**: Min/Max price filters
- 📅 **Year Filters**: Minimum year requirements
- 🏗️ **Stock Requirements**: Require stock numbers

#### **Scheduling System**
- 🕐 **Daily Scheduling**: Set automatic scrape times
- 🔄 **Manual Override**: Run scrapes on-demand
- 📊 **Status Tracking**: Monitor scheduled vs manual runs

---

### 📊 **Reports & Exports**

#### **Adobe-Ready Export Files**
- 📄 **CSV Format**: Compatible with Adobe Illustrator workflow
- 🎯 **QR Code Paths**: Embedded file paths for batch processing
- 🗂️ **Dealership-Specific**: Individual files per dealership
- ⬇️ **Download Interface**: Direct file access

#### **Summary Reports**
- 📈 **Daily Statistics**: Vehicle counts, processing time, errors
- 🚗 **Dealership Breakdown**: Individual performance metrics
- ⚠️ **Error Reporting**: Missing VINs, failed processes
- 📋 **Historical Data**: Archive of all scraper runs

---

### 🔗 **Database Integration**

The web interface connects directly to your existing MinisForum PostgreSQL database:
- 🗄️ **Real-time Data**: Live database queries
- 🔒 **Secure Connection**: Local database access only
- 🔄 **Automatic Sync**: Reflects all database changes
- 📊 **Performance Optimized**: Efficient queries and caching

---

### 🎯 **Daily Workflow**

1. **Morning Review**:
   - Check overnight scraper results
   - Review terminal logs for any issues
   - Verify QR code generation completed

2. **Order Processing**:
   - Select required dealerships
   - Generate Adobe export files
   - Download CSV files for printing

3. **Quality Control**:
   - Review summary report for missing VINs
   - Check dealership-specific metrics
   - Verify QR code file integrity

4. **Next Day Setup**:
   - Adjust dealership filtering if needed
   - Confirm scheduling settings
   - Prepare for next automated run

---

### 🛠️ **Technical Architecture**

- **Backend**: Flask web framework with PostgreSQL integration
- **Frontend**: Vanilla JavaScript with Silver Fox brand styling
- **Database**: Direct integration with existing MinisForum database
- **Security**: Local-only access, no external network exposure
- **Performance**: Optimized for 40 dealerships, thousands of vehicles

---

### 📞 **Support & Troubleshooting**

#### **Common Issues**
- **Database Connection**: Verify PostgreSQL service is running
- **Font Loading**: Ensure custom fonts are in `/static/fonts/`
- **Port Conflicts**: Default port 5000, change in `app.py` if needed
- **Permission Errors**: Run as administrator if file access issues

#### **Log Files**
- **Web GUI Logs**: `web_gui.log` (application events)
- **Scraper Logs**: Terminal output + database logs
- **Database Logs**: PostgreSQL standard logging

---

### 🎉 **Ready for Production**

This web interface provides complete control over your MinisForum database system with:
- ✅ Silver Fox brand consistency
- ✅ Intuitive dealership management
- ✅ Real-time progress monitoring  
- ✅ Adobe-ready export generation
- ✅ Comprehensive error reporting
- ✅ Local security and performance

**Perfect for daily dealership operations and order processing workflows!**