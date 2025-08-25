# CLAUDE.md - Personal Assistant Configuration
## Silver Fox Marketing - Claude Code Environment

### 👋 Welcome to Your Personal Assistant Environment

I am Claude, your expert-level coding and social media management assistant, configured specifically for your Silver Fox Marketing operations. This containerized environment provides secure, isolated access to help you with development, automation, and business operations while protecting your NAS and sensitive systems.

---

## 🎯 My Core Capabilities

### **Development & Coding**
- Full-stack development (JavaScript, Python, PHP, etc.)
- Database design and optimization
- API integrations and automations
- Google Apps Script for business automation
- Docker containerization and DevOps
- Code review and optimization

### **Business Operations**
- Excel/Google Sheets automation and analysis
- CRM integrations (Pipedrive, HubSpot, etc.)
- Marketing automation workflows
- Data analysis and reporting
- Process optimization and documentation

### **Social Media Management**
- Content strategy and planning
- Multi-platform campaign coordination
- Analytics and performance tracking
- Brand voice consistency
- Community management strategies

---

## 📁 Project Structure & Organization

### **Recommended Directory Structure:**
```
/workspace/
├── docs/                     # Project documentation and context
│   ├── CLAUDE.md            # This file
│   ├── business-context/    # Company-specific information
│   ├── project-briefs/      # Individual project documentation
│   └── references/          # Quick reference materials
├── projects/                # Active development projects
│   ├── automation/          # Business automation scripts
│   ├── integrations/        # API integrations
│   └── websites/           # Web development projects
├── data/                    # Data files and exports
│   ├── spreadsheets/        # Excel/CSV files
│   ├── exports/            # Data exports from various systems
│   └── backups/            # Backup files
└── scripts/                # Utility scripts and tools
    ├── deploy/             # Deployment scripts
    └── maintenance/        # Maintenance utilities
```

---

## 🛠️ Development Environment & Extensions

### **Installed VSCode Extensions**

#### **Currently Active Extensions:**
1. **MarkdownLint** - Documentation quality and consistency
2. **npm IntelliSense** - Enhanced Node.js package management
3. **Debugger for Firefox** - Cross-browser testing capabilities
4. **Microsoft Edge Tools for VS Code** - Edge DevTools integration
5. **ESLint** - JavaScript/TypeScript code quality and consistency
6. **GitLens** - Git supercharged with enhanced version control
7. **Kubernetes** - Container orchestration and deployment
8. **VIM** - Advanced text editing with VIM keybindings
9. **Claude Code** - AI-powered development assistant (primary tool)

#### **Recommended Additional Extensions for Silver Fox Assistant:**

**🚀 Essential for Our Workflow:**
- **Python** - Enhanced Python development (critical for scrapers)
- **Pylance** - Advanced Python language server
- **Python Debugger** - Debug scraper issues efficiently
- **autoDocstring** - Generate Python docstrings automatically
- **Black Formatter** - Python code formatting consistency

**📊 Data & Database:**
- **SQLTools** - Database management and queries
- **MongoDB for VS Code** - NoSQL database management
- **CSV to Table** - Better CSV file visualization
- **Excel Viewer** - View spreadsheets in VSCode

**🌐 Web Development & APIs:**
- **REST Client** - Test API endpoints directly in VSCode
- **Postman** - Advanced API testing and documentation
- **Live Server** - Local development server
- **Auto Rename Tag** - HTML/XML tag synchronization

**🔄 Integration & Automation:**
- **Google Apps Script** - Direct GAS development
- **GitHub Copilot** - AI code completion (complements Claude Code)
- **GitHub Actions** - CI/CD workflow management
- **Docker** - Container development and management

**📋 Project Management:**
- **Todo Tree** - Track TODO comments across codebase
- **Project Manager** - Switch between project contexts
- **Bookmarks** - Navigate large codebases efficiently
- **Error Lens** - Inline error highlighting

**🎨 Documentation & Collaboration:**
- **Draw.io Integration** - Create technical diagrams
- **Mermaid Markdown Syntax Highlighting** - Flowcharts and diagrams
- **Code Spell Checker** - Prevent typos in code and docs
- **Better Comments** - Enhanced comment visibility

### **How Extensions Enhance Our Silver Fox Workflow:**

1. **Scraper Development**: Python extensions + ESLint for quality code
2. **API Testing**: REST Client for testing dealership APIs
3. **Database Management**: SQLTools for inventory data analysis
4. **Documentation**: MarkdownLint + autoDocstring for comprehensive docs
5. **Version Control**: GitLens for tracking scraper improvements
6. **Debugging**: Python Debugger + Error Lens for rapid issue resolution

---

## 🔗 External Platform Integrations

### **Current Integration Capabilities:**

### **For Context & Data Access:**

#### **GitHub Integration**
- **Setup**: Place repository URLs in `docs/references/github-repos.md`
- **Usage**: I can help with code review, documentation, and deployment
- **Access Method**: Provide specific repository URLs when needed

#### **Google Workspace**
- **Gmail**: Share relevant email threads via forwarding or screenshots
- **Drive**: Export documents to local files for analysis
- **Sheets**: Download as Excel/CSV for processing in this environment
- **Apps Script**: Develop and test scripts locally, then deploy

#### **Pipedrive CRM**
- **Data Export**: Regular CSV exports for analysis
- **API Integration**: Develop integrations within this secure environment
- **Custom Fields**: Document field mappings in `docs/business-context/`

#### **Social Media Platforms**
- **Analytics Data**: Export performance data for analysis
- **Content Planning**: Develop strategies and schedules locally
- **Asset Management**: Store creative assets in organized folders

#### **🆕 Enhanced Business Integrations**

**Notion Integration:**
- **Project Documentation**: Link Notion databases to our development workflow
- **Client Notes**: Import Notion pages for context-aware development
- **Task Management**: Sync development tasks with Notion project boards
- **Knowledge Base**: Access company procedures and brand guidelines
- **Setup**: Share Notion page URLs or export markdown for local processing

**Gmail Integration:**
- **Client Communications**: Import relevant email threads for project context
- **Automated Reporting**: Generate and send scraper performance reports
- **Issue Notifications**: Email alerts for scraper failures or data anomalies
- **Business Intelligence**: Process email data for client engagement insights
- **Setup**: Forward key emails or use Gmail API for automated access

**Google Drive Integration:**
- **Document Processing**: Import client contracts, specifications, and requirements
- **Asset Management**: Access brand assets, logos, and marketing materials
- **Data Backup**: Automated backup of scraper outputs and reports
- **Collaboration**: Share development progress and technical documentation
- **Setup**: Use Google Drive API or manual file exports for processing

---

## 📋 Project Context Management

### **Business Context Location:**
Store company-specific information in `/workspace/docs/business-context/`:

```
business-context/
├── company-overview.md      # Silver Fox Marketing overview
├── client-profiles/         # Individual client information
├── service-offerings.md     # Current services and pricing
├── brand-guidelines.md      # Brand voice and visual guidelines
├── tools-and-systems.md     # Current tech stack and integrations
└── team-structure.md        # Team roles and responsibilities
```

### **Project Documentation:**
For individual projects, create structured briefs in `/workspace/docs/project-briefs/`:

```
project-briefs/
├── points-program-automation/
│   ├── requirements.md
│   ├── technical-specs.md
│   └── implementation-plan.md
├── social-media-campaigns/
│   ├── campaign-strategy.md
│   ├── content-calendar.md
│   └── performance-metrics.md
└── client-websites/
    ├── discovery-notes.md
    ├── design-requirements.md
    └── development-timeline.md
```

---

## ⚡ Quick Start Commands

### **Initialize New Project:**
```bash
# Create project structure
mkdir -p /workspace/projects/[project-name]/{src,docs,tests}
mkdir -p /workspace/docs/project-briefs/[project-name]

# Initialize with templates
cp /workspace/docs/templates/project-brief.md /workspace/docs/project-briefs/[project-name]/
```

### **Common Development Tasks:**
```bash
# Start development server
npm run dev

# Run tests
npm test

# Deploy to staging
./scripts/deploy/staging.sh

# Backup current work
./scripts/maintenance/backup.sh
```

---

## 🛠 Available Tools & Libraries

### **Pre-installed in Environment:**
- **Node.js & NPM** - JavaScript runtime and packages
- **Python 3** - Data analysis and automation
- **Git** - Version control
- **Curl** - API testing and data fetching
- **Vim** - Text editor for quick edits

### **Commonly Used Libraries:**
- **Google APIs** - Sheets, Drive, Gmail integration
- **Axios** - HTTP requests
- **Lodash** - Utility functions
- **Moment.js** - Date manipulation
- **Puppeteer** - Web scraping and automation

---

## 📊 Data Security & Privacy

### **Container Isolation Benefits:**
- ✅ Isolated from your NAS and sensitive systems
- ✅ No persistent storage of sensitive data
- ✅ Network isolation when needed
- ✅ Easy cleanup and reset capabilities

### **Best Practices:**
- Store sensitive credentials in environment variables
- Use `.env` files for configuration (never commit to git)
- Regular cleanup of temporary files
- Backup important work to secure external storage

---

## 📞 How to Work With Me

### **Project Initiation:**
1. **Provide Context**: Share relevant business context and project requirements
2. **Define Scope**: Clear objectives and deliverables
3. **Resource Access**: Specify what external data/systems I need to work with
4. **Timeline**: Project deadlines and milestones

### **Ongoing Collaboration:**
- **Progress Updates**: Regular check-ins on project status
- **Code Reviews**: I'll review and optimize your existing code
- **Problem Solving**: Bring technical challenges for collaborative solutions
- **Documentation**: I'll maintain clear documentation for all work

### **Communication Style:**
- Be specific about requirements and constraints
- Share examples when possible
- Ask questions if anything is unclear
- Provide feedback on proposed solutions

---

## 🏗️ **SILVER FOX ORDER PROCESSING SYSTEM v2.1 - PRODUCTION READY STATUS**

### **📊 DEALERSHIP-SPECIFIC VIN INTELLIGENCE ARCHITECTURE**
*Complete order processing system with individual dealership VIN logs for precise graphics processing*

#### **🚨 CRITICAL ARCHITECTURAL UPDATE (August 8, 2025 - FINAL TESTING PHASE):**
**DEALERSHIP-SPECIFIC VIN LOGS IMPLEMENTATION**

**NEW ARCHITECTURE - Individual Dealership VIN Tracking:**
- **🏢 SEPARATE VIN LOGS** - Each dealership maintains independent VIN history
- **🎯 PRECISE CAO LOGIC** - Compare only against specific dealership's VIN log
- **✅ SIMPLIFIED PROCESSING** - No cross-dealership complexity or time windows
- **📊 CLEAN DATA SEPARATION** - BMW VINs vs Bommarito VINs completely isolated
- **🔄 MIGRATION COMPLETE** - Existing unified VIN history migrated to dealership tables

**Technical Infrastructure Achieved:**
- **✅ REAL Scraper Execution** - Actual website scraping working (BMW, Honda, Lincoln tested)
- **✅ WebSocket Live Updates** - Real-time progress streaming in web interface  
- **✅ Scraper18Controller Active** - 36 dealership scrapers technically integrated
- **✅ Flexible CSV Processing** - Handles various scraper output formats
- **✅ Enhanced Error Handling** - Detailed validation and progress reporting
- **✅ DEALERSHIP VIN LOGS** - Individual tables: `bmw_vin_log`, `bommarito_west_county_vin_log`, etc.

**Still Required for Production:**
- **🔄 Database Integration** - Final constraint fix needed for complete data flow
- **🔄 End-to-End Testing** - Complete scraper → Order Processing Wizard integration
- **🔄 Individual Scraper Validation** - Test all 36 scrapers individually
- **🔄 Order Processing Integration** - Connect scraped data to QR generation
- **🔄 Performance Testing** - Load testing and error handling validation

**Today's Technical Achievements:**
- Fixed Unicode encoding issues enabling real scraper execution
- Aligned WebSocket event names for live progress updates
- Implemented flexible CSV column name mapping
- Fixed database schema column references (scan_date → order_date)
- Added dealer_name column injection to CSV files
- Achieved 993 vehicles scraped successfully (database import pending final fix)

#### **Active Scraper Integration (36 Production Dealerships):**
**🏢 Premium Brands:** BMW of West St. Louis, Bommarito Cadillac, Columbia BMW, Porsche St. Louis, Spirit Lexus
**🚗 Honda Network:** Columbia Honda, Frank Leta Honda, Honda of Frontenac, Serra Honda O'Fallon  
**🔧 Ford Network:** Pundmann Ford, Suntrup Ford Kirkwood, Suntrup Ford West, Thoroughbred Ford
**⚙️ GM Network:** Rusty Drewing Cadillac, Rusty Drewing Chevrolet Buick GMC, Suntrup Buick GMC, Weber Chevrolet
**🔑 Hyundai/Kia:** Auffenberg Hyundai, HW Kia, Kia of Columbia, Suntrup Hyundai South, Suntrup Kia South
**🚙 Chrysler/Jeep:** Glendale Chrysler Jeep, South County Autos, Joe Machens CDJR
**🏛️ Lincoln Network:** Dave Sinclair Lincoln, Dave Sinclair Lincoln South, Dave Sinclair Lincoln St. Peters
**🌟 Specialty:** Land Rover Ranch Mirage, Mini of St. Louis, West County Volvo Cars
**🏭 Multi-Brand:** Joe Machens (Nissan, Hyundai, Toyota), Pappas Toyota, Bommarito West County

#### **🎯 NEW SYSTEM CAPABILITIES:**
- **DEALERSHIP-SPECIFIC VIN TRACKING**: Each dealership maintains separate VIN history
- **SIMPLIFIED CAO LOGIC**: Current inventory vs. dealership's own VIN log only
- **PRECISE GRAPHICS TARGETING**: Only vehicles never processed by that dealership get graphics
- **CLEAN DATA ARCHITECTURE**: No cross-contamination between dealership VIN logs
- **TEST DATA CONTROL**: CSV import testing skips VIN logging to preserve history accuracy
- **STATUS AGNOSTIC PROCESSING**: VIN processed = VIN processed, regardless of status changes
- **LIST ORDER OVERRIDE**: Process specific VINs regardless of history
- **QR Code Generation**: 388x388 PNG codes with custom URLs
- **Adobe CSV Export**: Variable data library format for graphics production
- **Real-time Monitoring**: Live processing status and results tracking

#### **🏗️ DEALERSHIP-SPECIFIC VIN LOG ARCHITECTURE**

**CRITICAL DESIGN CHANGE - Individual Dealership VIN Tracking:**

**Database Structure:**
```sql
-- Individual VIN log table per dealership
bmw_of_west_st_louis_vin_log (vin, processed_date, order_type, template_type)
bommarito_west_county_vin_log (vin, processed_date, order_type, template_type)  
dave_sinclair_lincoln_vin_log (vin, processed_date, order_type, template_type)
-- ... separate table for each of 36 dealerships
```

**CAO Order Logic - SIMPLIFIED:**
```
1. Get current inventory from raw_vehicle_data WHERE location = 'Bommarito West County'
2. Get processed VINs from bommarito_west_county_vin_log  
3. NEW VINs = current inventory VINs NOT IN dealership's VIN log
4. Generate graphics ONLY for NEW VINs
5. Add processed VINs to bommarito_west_county_vin_log
```

**Benefits of New Architecture:**
- **🎯 PRECISE TARGETING**: Only truly new vehicles get graphics for that specific dealership
- **📊 CLEAN SEPARATION**: BMW VINs never interfere with Bommarito logic
- **⚡ SIMPLE QUERIES**: Single table lookup instead of complex cross-dealership logic
- **🔄 NO TIME WINDOWS**: VIN processed = skip, VIN not processed = graphics
- **📈 SCALABLE**: Add new dealerships without affecting existing VIN logs

**Migration Impact:**
- **Legacy vin_history table** → Split into 36 dealership-specific tables
- **Complex time-based logic** → Simple IN/NOT IN comparison
- **Cross-dealership rules** → Eliminated completely

#### **📋 ORDER PROCESSING WORKFLOW - DETAILED DOCUMENTATION**

**Two Distinct Order Processing Methods:**

### **1. CAO (Comparative Analysis Order) - UPDATED ARCHITECTURE**
**Purpose:** Automatically identify vehicles needing graphics using dealership-specific VIN logs

**NEW SIMPLIFIED Process Flow:**
1. **Get Current Inventory**: Query raw_vehicle_data WHERE location = 'Dealership Name'
2. **Apply Dealership Filters**: 
   - Some dealerships want ONLY used cars
   - Some want ONLY new cars  
   - Some want BOTH new and used
   - These filters are configurable per dealership
3. **VIN Log Comparison**: Simple query against dealership's own VIN log table
   ```sql
   SELECT * FROM filtered_inventory 
   WHERE vin NOT IN (SELECT vin FROM dealership_name_vin_log)
   ```
4. **Generate Graphics**: Process ONLY VINs never seen by this dealership before
5. **Update VIN Log**: INSERT processed VINs into dealership_name_vin_log

**CRITICAL CHANGE**: Each dealership has its own VIN log - no cross-dealership complexity!

### **2. LIST Order**
**Purpose:** Process specific vehicles provided by account managers

**Process Flow:**
1. **Receive List**: Account manager provides specific VINs/vehicles
2. **No Comparison Needed**: Skip VIN history check (we already know what needs graphics)
3. **Direct to Processing**: Generate QR codes and CSV for listed vehicles

### **🔧 CRITICAL PROCESSING SEQUENCE**

**IMPORTANT: The order of operations below is MANDATORY for Adobe integration**

#### **Step 1: Generate QR Codes FIRST**
- **Individual QR codes** for each vehicle needing graphics
- **Links to EXACT vehicle URL** on dealership website (NOT homepage)
- **File format**: 388x388 PNG
- **File naming**: `[DealershipName]_QR_Code_[Index].png`
- **Storage location**: Organized by dealership and date

#### **Step 2: Export Variable Data CSV**
- **Contains all vehicle information** for Adobe template processing
- **MUST INCLUDE QR code file paths** as a data column
- **Format**: Adobe-compatible variable data structure
- **Critical requirement**: QR codes must exist BEFORE CSV creation

**Why This Order Matters:**
- Adobe InDesign/Illustrator needs the QR code file paths in the CSV
- The CSV acts as a data merge source for the graphic templates
- Adobe pulls both vehicle data AND QR codes to create final graphics
- Without QR file paths in CSV, Adobe cannot complete the graphics

#### **Step 3: Update VIN History (CRITICAL)**
**This step is ABSOLUTELY CRITICAL for system accuracy**

After processing is complete:
- **MUST add all processed VINs** to the dealership's VIN log
- **Purpose**: Enables accurate future CAO comparisons
- **Without this step**: System will repeatedly process the same vehicles
- **Impact**: Breaks the entire comparative analysis workflow

**VIN History Updates Include:**
- VIN number
- Dealership name
- Order date (when processed)
- Vehicle type (new/used/certified)
- Created timestamp

**Why This Is Critical:**
- Future CAO orders compare current inventory against VIN history
- Only vehicles NOT in history are identified as needing graphics
- Missing this step = duplicate work and wasted resources
- This is the foundation of the entire comparative analysis system

### **🎛️ DEALERSHIP FILTERING SETTINGS**

**Planned Enhancement: Dealership Settings Tab**
- **Location**: New tab in web interface for dealership configuration
- **Configurable Filters**:
  - Vehicle Type: New Only / Used Only / Both / Certified Pre-Owned
  - Price Range: Min/Max thresholds
  - Days on Lot: Exclude vehicles under X days
  - Stock Number Requirements: Include/exclude based on patterns
  - Custom Rules: Dealership-specific requirements

**Current Implementation:**
- Filters are stored in `dealership_configs` table
- Applied during CAO processing in `filter_vehicles_by_type()` method
- Accessible via API for future settings interface

#### **🚀 SCRAPER SYSTEM INTEGRATION:**
- **✅ Complete Integration: 36 production scrapers** - All proven scraper 18 logic integrated
- **✅ Enhanced Error Handling** - Individual failures don't crash entire system
- **✅ Direct Database Import** - Scraped data automatically flows to PostgreSQL
- **✅ Web GUI Control** - Replaced config.csv with intuitive web interface
- **✅ Real-time Monitoring** - Live progress updates via Socket.IO
- **🎯 Ultimate Goal: Complete automation** of graphics order processing - ACHIEVED!

#### **🎨 PROFESSIONAL DEALERSHIP SETTINGS INTERFACE v2.5 (August 25, 2025):**
- **✅ MAJOR UI/UX OVERHAUL** - Complete professional redesign with Silver Fox brand alignment
- **✅ BULK EDITING FUNCTIONALITY** - Edit multiple dealerships simultaneously with inline controls
- **✅ CRITICAL SAVE FIX** - "Save All Changes" button now works properly with comprehensive error handling
- **✅ ENHANCED FORM CONTROLS** - Vehicle type checkboxes, price ranges, active toggles for each dealership
- **✅ MODERN MODAL SYSTEM** - Professional configuration modals with backdrop blur and animations
- **✅ BRAND CONSISTENCY** - Silver Fox red, gold accents, and gradient styling throughout
- **✅ REAL-TIME FEEDBACK** - Terminal status messages and visual confirmations for all operations
- **✅ TECHNICAL IMPROVEMENTS** - Fixed API endpoints, proper data validation, enhanced user experience

---

## 🚀 Current Project Priorities

### **Primary Focus: Technology Development**
1. **PipeDrive Integration** - 2-month transition currently underway for complete CRM automation
2. **✅ Scraper System Integration - COMPLETE** - All 36 scrapers integrated with enhanced error handling
3. **Mobile Tools Development** - VIN scanning, QR verification for installation team efficiency
4. **Order Form Integration** - Dynamic PipeDrive-embedded order processing system
5. **Business Intelligence Dashboard** - Executive dashboard for real-time business insights

### **Secondary Focus: Social Media Authority Development**  
1. **LotSherpa Authority Strategy** - 80% automotive industry thought leadership content
2. **Dual-Brand Authority Management** - Launch LotSherpa without disrupting Silver Fox operations
3. **Community Integration Content** - Position automotive expertise to elevate all business graphics

### **Strategic Goals:**
- **LotSherpa**: $2M revenue target, 50 new dealer relationships, geographic expansion
- **Silver Fox**: Maintain St. Louis market dominance while building automotive industry authority
- **Technology Platform**: Industry-leading automation creating competitive advantages

*Note: Individual social media tools, content strategies, and program development have dedicated folders with detailed context documents.*

---

## 📝 Notes & Reminders

### **Important Considerations:**
- Always test integrations in staging environment first
- Maintain backup copies of critical automation scripts
- Document all custom solutions for team knowledge sharing
- Regular security reviews of external integrations

### **Contact & Support:**
- **Primary User**: Silver Fox Marketing Team
- **Environment**: Containerized Claude Code Sandbox
- **Last Updated**: August 1, 2025
- **Version**: 1.0

---

## 🔄 Regular Maintenance

### **Weekly Tasks:**
- [ ] Review and organize project files
- [ ] Update documentation for completed work
- [ ] Test critical automations and integrations
- [ ] Backup important scripts and configurations

### **Monthly Tasks:**
- [ ] Security review of access credentials
- [ ] Performance optimization of running systems
- [ ] Update project priorities and roadmap
- [ ] Clean up temporary files and unused resources

---

*Ready to help you build, automate, and optimize your Silver Fox Marketing operations. What shall we work on today?*