/**
 * MinisForum Database Web GUI - JavaScript Application
 * Silver Fox Marketing - Dealership Management Interface
 * 
 * Handles all frontend interactions, API calls, and real-time updates
 * for the dealership database control system.
 */

class MinisFornumApp {
    constructor() {
        this.dealerships = [];
        this.selectedDealerships = new Set();
        this.scraperRunning = false;
        this.currentTab = 'scraper';
        this.currentDealership = null;
        
        // New queue management properties
        this.processingQueue = new Map(); // Store queue items with their settings
        this.dealershipDefaults = new Map(); // Store default CAO/List settings for dealerships
        this.weeklySchedule = {
            monday: ['Columbia Honda', 'BMW of West St. Louis'],
            tuesday: ['Dave Sinclair Lincoln South', 'Suntrup Ford West'],
            wednesday: ['Joe Machens Toyota', 'Thoroughbred Ford'],
            thursday: ['Suntrup Ford Kirkwood', 'Joe Machens Hyundai'],
            friday: ['Columbia Honda', 'BMW of West St. Louis', 'Dave Sinclair Lincoln South']
        };
        
        // Progress tracking
        this.progressData = {
            totalScrapers: 0,
            completedScrapers: 0,
            currentScraper: null,
            progressPercent: 0
        };
        
        // Data search properties
        this.dataSearch = {
            currentResults: [],
            totalCount: 0,
            currentPage: 0,
            pageSize: 50,
            availableDealers: [],
            searchCache: new Map(),
            activeFilters: {
                location: '',
                year: '',
                make: '',
                model: '',
                vehicle_type: '',
                import_date: ''
            },
            filterOptions: {}
        };
        
        // Modal scraper properties
        this.modalProgress = {
            dealershipsProcessed: 0,
            vehiclesProcessed: 0,
            errors: 0,
            totalDealerships: 0,
            progressPercent: 0
        };
        this.modalConsolePaused = false;
        
        // Initialize Socket.IO
        this.initSocketIO();
        
        // Initialize the application
        this.init();
    }
    
    initSocketIO() {
        console.log('Initializing Socket.IO connection...');
        
        // Initialize Socket.IO
        this.socket = io();
        
        // Set up event listeners for real-time progress updates
        this.socket.on('connect', () => {
            console.log('Socket.IO connected');
            this.addTerminalMessage('Real-time connection established', 'success');
            
            // Check if we're on the scraper tab and restore visibility if needed
            if (this.currentTab === 'scraper') {
                this.restoreScraperStatusVisibility();
            }
        });
        
        this.socket.on('disconnect', () => {
            console.log('Socket.IO disconnected');
            this.addTerminalMessage('Real-time connection lost', 'warning');
        });
        
        // Scraping session events
        this.socket.on('scraper_session_start', (data) => {
            this.onScrapingSessionStart(data);
        });
        
        this.socket.on('scraper_start', (data) => {
            this.onScraperStart(data);
        });
        
        this.socket.on('scraper_progress', (data) => {
            this.onScraperProgress(data);
        });
        
        this.socket.on('scraper_complete', (data) => {
            this.onScraperComplete(data);
        });
        
        this.socket.on('scraper_session_complete', (data) => {
            this.onScrapingSessionComplete(data);
        });
        
        this.socket.on('scraper_output', (data) => {
            this.handleScraperOutput(data);
        });
    }
    
    async init() {
        console.log('Initializing MinisForum Database GUI...');
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Load initial data
        try {
            await this.loadDealerships();
            console.log(`✅ Loaded ${this.dealerships.length} dealerships`);
            console.log('Dealership names:', this.dealerships.map(d => d.name));
            
            // Load dealership defaults after dealerships are loaded
            await this.loadDealershipDefaults();
            
            // Re-render dealership list with correct types
            this.renderDealershipList(this.dealerships);
            
            // Set up search functionality after dealerships are loaded
            this.setupDealershipSearchListeners();
        } catch (error) {
            console.error('❌ Failed to load dealerships:', error);
            this.addTerminalMessage(`Failed to load dealerships: ${error.message}`, 'error');
        }
        
        // Select all dealerships by default to ensure Start Scrape button works
        if (this.dealerships && this.dealerships.length > 0) {
            this.dealerships.forEach(dealership => {
                this.selectedDealerships.add(dealership.name);
            });
            console.log(`✅ Selected all ${this.selectedDealerships.size} dealerships by default`);
        }
        
        // Update button states
        this.updateScraperButtonStates();
        
        this.checkScraperStatus();
        
        // Set up periodic status checks
        this.startStatusPolling();
        
        console.log('Application initialized successfully');
    }
    
    bindEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Main action buttons
        document.getElementById('startScrapeBtn').addEventListener('click', () => {
            this.startScraper();
        });
        
        document.getElementById('scheduleBtn').addEventListener('click', () => {
            this.showScheduleModal();
        });
        
        document.getElementById('testWebSocketBtn').addEventListener('click', () => {
            this.testWebSocketConnection();
        });
        
        // New scraper selection functionality
        document.getElementById('selectDealershipsBtn').addEventListener('click', () => {
            this.showDealershipSelectionModal();
        });
        
        // Modal controls
        document.getElementById('closeDealershipSelectionModal').addEventListener('click', () => {
            this.closeModal('dealershipSelectionModal');
        });
        
        document.getElementById('cancelDealershipSelection').addEventListener('click', () => {
            this.closeModal('dealershipSelectionModal');
        });
        
        document.getElementById('selectAllBtnModal').addEventListener('click', () => {
            this.selectAllDealerships();
        });
        
        document.getElementById('selectNoneBtnModal').addEventListener('click', () => {
            this.selectNoneDealerships();
        });
        
        document.getElementById('saveDealershipSelection').addEventListener('click', () => {
            this.startSelectedScraper();
        });
        
        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal('dealershipModal');
        });
        
        document.getElementById('closeScheduleModal').addEventListener('click', () => {
            this.closeModal('scheduleModal');
        });
        
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveDealershipSettings();
        });
        
        document.getElementById('saveSchedule').addEventListener('click', () => {
            this.saveScheduleSettings();
        });
        
        // Terminal controls - check if element exists first
        const clearTerminalBtn = document.getElementById('clearTerminal');
        if (clearTerminalBtn) {
            clearTerminalBtn.addEventListener('click', () => {
                this.clearTerminal();
            });
        }
        
        const clearTerminalStatusBtn = document.getElementById('clearTerminalStatus');
        if (clearTerminalStatusBtn) {
            clearTerminalStatusBtn.addEventListener('click', () => {
                this.clearTerminalStatus();
            });
        }
        
        // Scraper console controls - check if element exists first
        const clearScraperConsoleBtn = document.getElementById('clearScraperConsole');
        if (clearScraperConsoleBtn) {
            clearScraperConsoleBtn.addEventListener('click', () => {
                this.clearScraperConsole();
            });
        }
        
        // Report generation buttons - check if elements exist first
        const generateAdobeBtn = document.getElementById('generateAdobeBtn');
        if (generateAdobeBtn) {
            generateAdobeBtn.addEventListener('click', () => {
                this.generateAdobeReport();
            });
        }
        
        const generateSummaryBtn = document.getElementById('generateSummaryBtn');
        if (generateSummaryBtn) {
            generateSummaryBtn.addEventListener('click', () => {
                this.generateSummaryReport();
            });
        }
        
        // Refresh buttons for data tabs - check if elements exist first
        const refreshRawDataBtn = document.getElementById('refreshRawData');
        if (refreshRawDataBtn) {
            refreshRawDataBtn.addEventListener('click', () => {
                this.loadRawDataOverview();
            });
        }
        
        const refreshNormalizedDataBtn = document.getElementById('refreshNormalizedData');
        if (refreshNormalizedDataBtn) {
            refreshNormalizedDataBtn.addEventListener('click', () => {
                this.loadNormalizedDataOverview();
            });
        }
        
        const refreshOrderDataBtn = document.getElementById('refreshOrderData');
        if (refreshOrderDataBtn) {
            refreshOrderDataBtn.addEventListener('click', () => {
                this.loadOrderProcessingOverview();
            });
        }
        
        const refreshQRDataBtn = document.getElementById('refreshQRData');
        if (refreshQRDataBtn) {
            refreshQRDataBtn.addEventListener('click', () => {
                this.loadQROverview();
            });
        }
        
        // System Status event listeners - check if elements exist first
        const refreshSystemStatusBtn = document.getElementById('refreshSystemStatus');
        if (refreshSystemStatusBtn) {
            refreshSystemStatusBtn.addEventListener('click', () => {
                this.refreshSystemStatus();
            });
        }
        
        const exportSystemReportBtn = document.getElementById('exportSystemReport');
        if (exportSystemReportBtn) {
            exportSystemReportBtn.addEventListener('click', () => {
                this.exportSystemReport();
            });
        }
        
        // Data Search event listeners
        this.bindDataSearchEventListeners();
        
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }
    
    bindDataSearchEventListeners() {
        // Search button and enter key
        const searchBtn = document.getElementById('searchVehiclesBtn');
        const searchInput = document.getElementById('vehicleSearchInput');
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.performVehicleSearch();
            });
        }
        
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performVehicleSearch();
                }
            });
            
            // Auto-search with debounce
            let searchTimeout;
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (searchInput.value.trim().length >= 2 || searchInput.value.trim().length === 0) {
                        this.performVehicleSearch();
                    }
                }, 500);
            });
        }
        
        // Filter change handlers
        const filterBy = document.getElementById('filterBy');
        if (filterBy) {
            filterBy.addEventListener('change', () => {
                this.updateFilterVisibility();
                this.performVehicleSearch();
            });
        }
        
        // Data type radio buttons
        document.querySelectorAll('input[name="dataType"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.performVehicleSearch();
            });
        });
        
        // Date inputs
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        if (startDate) {
            startDate.addEventListener('change', () => {
                this.performVehicleSearch();
            });
        }
        if (endDate) {
            endDate.addEventListener('change', () => {
                this.performVehicleSearch();
            });
        }
        
        // Dealer select
        const dealerSelect = document.getElementById('dealerSelect');
        if (dealerSelect) {
            dealerSelect.addEventListener('change', () => {
                this.performVehicleSearch();
            });
        }
        
        // Sort controls
        const sortBy = document.getElementById('sortBy');
        const sortOrder = document.getElementById('sortOrder');
        if (sortBy) {
            sortBy.addEventListener('change', () => {
                this.performVehicleSearch();
            });
        }
        if (sortOrder) {
            sortOrder.addEventListener('change', () => {
                this.performVehicleSearch();
            });
        }
        
        // Pagination
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => {
                this.goToPreviousPage();
            });
        }
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => {
                this.goToNextPage();
            });
        }
        
        // Export and refresh buttons
        const exportBtn = document.getElementById('exportSearchResults');
        const refreshBtn = document.getElementById('refreshDataSearch');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportSearchResults();
            });
        }
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshDataSearch();
            });
        }
        
        // Terminal clear for status tab
        const clearTerminalStatus = document.getElementById('clearTerminalStatus');
        if (clearTerminalStatus) {
            clearTerminalStatus.addEventListener('click', () => {
                this.clearTerminalStatus();
            });
        }
    }
    
    async loadDealerships() {
        try {
            this.addTerminalMessage('Loading dealership configurations...', 'info');
            
            const response = await fetch('/api/dealerships');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const dealerships = await response.json();
            this.dealerships = dealerships;
            
            // Commented out - using dropdown instead of grid display
            // this.renderDealershipGrid();
            
            // Select all active dealerships by default
            this.dealerships.forEach(dealership => {
                if (dealership.is_active) {
                    this.selectedDealerships.add(dealership.name);
                }
            });
            
            this.updateDealershipSelection();
            this.addTerminalMessage(`Loaded ${dealerships.length} dealership configurations`, 'success');
            
        } catch (error) {
            console.error('Error loading dealerships:', error);
            this.addTerminalMessage(`Error loading dealerships: ${error.message}`, 'error');
        }
    }
    
    renderDealershipGrid() {
        const grid = document.getElementById('dealershipGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        this.dealerships.forEach(dealership => {
            const card = this.createDealershipCard(dealership);
            grid.appendChild(card);
        });
    }
    
    createDealershipCard(dealership) {
        const card = document.createElement('div');
        card.className = `dealership-card ${dealership.is_active ? 'active' : 'inactive'}`;
        card.dataset.dealership = dealership.name;
        
        // Get filtering rules for display
        const filteringRules = dealership.filtering_rules || {};
        const vehicleTypes = this.getEnabledVehicleTypes(filteringRules);
        const priceRange = this.getPriceRange(filteringRules);
        
        card.innerHTML = `
            <div class="card-header">
                <input type="checkbox" class="dealership-checkbox" 
                       ${this.selectedDealerships.has(dealership.name) ? 'checked' : ''}
                       onchange="app.toggleDealershipSelection('${dealership.name}', this.checked)">
                <h3 class="dealership-name">${dealership.name}</h3>
                <button class="settings-btn" onclick="app.showDealershipSettings('${dealership.name}')">
                    <i class="fas fa-cog"></i>
                </button>
            </div>
            <div class="dealership-info">
                <div class="info-row">
                    <span class="info-label">Vehicle Types:</span>
                    <span class="info-value">${vehicleTypes}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Price Range:</span>
                    <span class="info-value">${priceRange}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value ${dealership.is_active ? 'success' : 'error'}">
                        ${dealership.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    getEnabledVehicleTypes(filteringRules) {
        const excludeConditions = filteringRules.exclude_conditions || [];
        const types = [];
        
        if (!excludeConditions.includes('new')) types.push('New');
        if (!excludeConditions.includes('po')) types.push('Pre-Owned');
        if (!excludeConditions.includes('cpo')) types.push('CPO');
        
        return types.length > 0 ? types.join(', ') : 'None';
    }
    
    getPriceRange(filteringRules) {
        const minPrice = filteringRules.min_price;
        const maxPrice = filteringRules.max_price;
        
        if (minPrice && maxPrice) {
            return `$${minPrice.toLocaleString()} - $${maxPrice.toLocaleString()}`;
        } else if (minPrice) {
            return `$${minPrice.toLocaleString()}+`;
        } else if (maxPrice) {
            return `Up to $${maxPrice.toLocaleString()}`;
        } else {
            return 'Any Price';
        }
    }
    
    toggleDealershipSelection(dealershipName, selected) {
        if (selected) {
            this.selectedDealerships.add(dealershipName);
        } else {
            this.selectedDealerships.delete(dealershipName);
        }
        
        this.updateDealershipSelection();
        this.addTerminalMessage(`${dealershipName} ${selected ? 'selected' : 'deselected'} for scraping`, 'info');
    }
    
    updateDealershipSelection() {
        // Update visual selection state
        document.querySelectorAll('.dealership-card').forEach(card => {
            const dealershipName = card.dataset.dealership;
            const isSelected = this.selectedDealerships.has(dealershipName);
            
            card.classList.toggle('selected', isSelected);
            
            const checkbox = card.querySelector('.dealership-checkbox');
            if (checkbox) {
                checkbox.checked = isSelected;
            }
        });
        
        // Update start button state
        const startButton = document.getElementById('startScrapeBtn');
        if (startButton) {
            startButton.disabled = this.selectedDealerships.size === 0 || this.scraperRunning;
            
            const buttonText = startButton.querySelector('span') || startButton;
            if (this.scraperRunning) {
                buttonText.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            } else {
                buttonText.innerHTML = '<i class="fas fa-play"></i> Start Scrape';
            }
        }
    }
    
    showDealershipSettings(dealershipName) {
        this.currentDealership = dealershipName;
        const dealership = this.dealerships.find(d => d.name === dealershipName);
        
        if (!dealership) return;
        
        // Populate modal with current settings
        document.getElementById('modalTitle').textContent = `${dealershipName} Settings`;
        
        const filteringRules = dealership.filtering_rules || {};
        const excludeConditions = filteringRules.exclude_conditions || [];
        
        // Set vehicle type checkboxes
        document.querySelector('input[value="new"]').checked = !excludeConditions.includes('new');
        document.querySelector('input[value="po"]').checked = !excludeConditions.includes('po');
        document.querySelector('input[value="cpo"]').checked = !excludeConditions.includes('cpo');
        
        // Set price and year filters
        document.getElementById('minPrice').value = filteringRules.min_price || '';
        document.getElementById('maxPrice').value = filteringRules.max_price || '';
        document.getElementById('minYear').value = filteringRules.min_year || '';
        
        this.showModal('dealershipModal');
    }
    
    async saveDealershipSettings() {
        if (!this.currentDealership) return;
        
        try {
            // Collect form data
            const vehicleTypes = Array.from(document.querySelectorAll('input[name="vehicle_types"]:checked'))
                .map(input => input.value);
            
            const excludeConditions = ['new', 'po', 'cpo'].filter(type => !vehicleTypes.includes(type));
            
            const filteringRules = {
                exclude_conditions: excludeConditions,
                require_stock: true
            };
            
            // Add price filters if specified
            const minPrice = parseInt(document.getElementById('minPrice').value);
            const maxPrice = parseInt(document.getElementById('maxPrice').value);
            const minYear = parseInt(document.getElementById('minYear').value);
            
            if (minPrice) filteringRules.min_price = minPrice;
            if (maxPrice) filteringRules.max_price = maxPrice;
            if (minYear) filteringRules.min_year = minYear;
            
            // Send update to server
            const response = await fetch(`/api/dealerships/${this.currentDealership}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filtering_rules: filteringRules,
                    is_active: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Updated settings for ${this.currentDealership}`, 'success');
                this.closeModal('dealershipModal');
                this.loadDealerships(); // Refresh the grid
            } else {
                this.addTerminalMessage(`Failed to update ${this.currentDealership}: ${result.message}`, 'error');
            }
            
        } catch (error) {
            console.error('Error saving dealership settings:', error);
            this.addTerminalMessage(`Error saving settings: ${error.message}`, 'error');
        }
    }
    
    async startScraper() {
        if (this.scraperRunning) return;
        
        if (this.selectedDealerships.size === 0) {
            this.addTerminalMessage('Please select at least one dealership before starting the scraper.', 'warning');
            this.addScraperConsoleMessage('⚠️ Please select at least one dealership before starting the scraper.', 'warning');
            return;
        }
        
        try {
            this.scraperRunning = true;
            this.updateScraperButtonStates();
            
            this.addTerminalMessage('Starting scraper pipeline...', 'info');
            this.addScraperConsoleMessage('🚀 Starting scraper pipeline...', 'info');
            
            const response = await fetch('/api/scrapers/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership_names: Array.from(this.selectedDealerships) // Send all selected dealerships
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result && result.success) {
                this.addTerminalMessage('Scraper started successfully', 'success');
                this.addScraperConsoleMessage('✅ Scraper started successfully - Waiting for data...', 'success');
            } else {
                const errorMessage = result?.message || result?.error || 'Unknown error occurred';
                this.addTerminalMessage(`Failed to start scraper: ${errorMessage}`, 'error');
                this.addScraperConsoleMessage(`❌ Failed to start scraper: ${errorMessage}`, 'error');
                this.scraperRunning = false;
                this.updateScraperButtonStates();
            }
            
        } catch (error) {
            console.error('Error starting scraper:', error);
            this.addTerminalMessage(`Error starting scraper: ${error.message}`, 'error');
            this.addScraperConsoleMessage(`❌ Error starting scraper: ${error.message}`, 'error');
            this.scraperRunning = false;
            this.updateScraperButtonStates();
        }
    }
    
    updateScraperButtonStates() {
        const startBtn = document.getElementById('startScrapeBtn');
        const selectBtn = document.getElementById('selectDealershipsBtn');
        
        if (startBtn) {
            if (this.scraperRunning) {
                startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
                startBtn.disabled = true;
            } else {
                startBtn.innerHTML = '<i class="fas fa-play"></i> Start Scrape (All)';
                startBtn.disabled = this.selectedDealerships.size === 0;
            }
        }
        
        if (selectBtn) {
            selectBtn.disabled = this.scraperRunning;
        }
    }
    
    async checkScraperStatus() {
        try {
            const response = await fetch('/api/scraper/status');
            const status = await response.json();
            
            this.scraperRunning = status.running;
            
            if (status.last_scrape) {
                const lastScrape = new Date(status.last_scrape);
                document.getElementById('lastScrape').textContent = 
                    `Last Scrape: ${lastScrape.toLocaleDateString()} ${lastScrape.toLocaleTimeString()}`;
            }
            
            if (status.results && Object.keys(status.results).length > 0) {
                this.updateScraperProgress(status.results);
            }
            
            this.updateDealershipSelection();
            
            // Update system status
            const statusIndicator = document.getElementById('systemStatus');
            const statusIcon = statusIndicator.querySelector('.status-icon');
            const statusText = statusIndicator.querySelector('.status-text');
            
            if (this.scraperRunning) {
                statusIcon.className = 'fas fa-circle status-icon warning';
                statusText.textContent = 'Scraper Running';
            } else {
                statusIcon.className = 'fas fa-circle status-icon';
                statusText.textContent = 'System Ready';
            }
            
        } catch (error) {
            console.error('Error checking scraper status:', error);
        }
    }
    
    updateScraperProgress(results) {
        const statusElement = document.getElementById('scraperStatus');
        const progressFill = document.getElementById('progressFill');
        const statusDetails = document.getElementById('statusDetails');
        
        if (!results.dealerships) return;
        
        const totalDealerships = Object.keys(results.dealerships).length;
        const completedDealerships = Object.values(results.dealerships)
            .filter(d => d.status === 'completed' || d.status === 'failed').length;
        
        const progress = totalDealerships > 0 ? (completedDealerships / totalDealerships) * 100 : 0;
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
        if (statusDetails) {
            const totalVehicles = Object.values(results.dealerships)
                .reduce((sum, d) => sum + (d.vehicle_count || 0), 0);
            
            statusDetails.innerHTML = `
                <div class="status-item">
                    <span class="status-number">${completedDealerships}</span>
                    <span class="status-label">Dealerships Processed</span>
                </div>
                <div class="status-item">
                    <span class="status-number">${totalVehicles}</span>
                    <span class="status-label">Vehicles Processed</span>
                </div>
                <div class="status-item">
                    <span class="status-number">${results.errors ? results.errors.length : 0}</span>
                    <span class="status-label">Errors</span>
                </div>
                <div class="status-item">
                    <span class="status-number">${Math.round(progress)}%</span>
                    <span class="status-label">Complete</span>
                </div>
            `;
        }
        
        // Hide status when complete
        if (progress >= 100 && !this.scraperRunning) {
            setTimeout(() => {
                this.hideScraperStatus();
            }, 3000);
        }
    }
    
    showScraperStatus() {
        const statusElement = document.getElementById('scraperStatus');
        if (statusElement) {
            statusElement.style.display = 'block';
            console.log('✅ Scraper status panel shown');
            
            // Also ensure scraper console has initial message
            this.addScraperConsoleMessage('🔧 Scraper status panel activated', 'info');
        } else {
            console.error('❌ scraperStatus element not found!');
        }
    }
    
    hideScraperStatus() {
        const statusElement = document.getElementById('scraperStatus');
        if (statusElement) {
            statusElement.style.display = 'none';
        }
    }
    
    restoreScraperStatusVisibility() {
        // Check if scraper is currently running by looking at our progress data
        const scraperStatus = document.getElementById('scraperStatus');
        if (scraperStatus && this.scraperRunning) {
            // Ensure scraper status is visible when switching back to scraper tab
            scraperStatus.style.display = 'block';
            console.log('Restored scraper status visibility');
        }
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-panel`).classList.add('active');
        
        this.currentTab = tabName;
        
        // If switching to scraper tab, ensure scraper status visibility is preserved
        if (tabName === 'scraper') {
            this.restoreScraperStatusVisibility();
        }
        
        // Load tab-specific data
        this.loadTabData(tabName);
    }
    
    loadTabData(tabName) {
        switch (tabName) {
            case 'raw-data':
                this.loadRawDataOverview();
                break;
            case 'normalized-data':
                this.loadNormalizedDataOverview();
                break;
            case 'data-search':
                this.initDataSearch();
                break;
            case 'system-status':
                this.loadSystemStatus();
                break;
            case 'queue-management':
                this.loadQueueManagement();
                break;
            case 'dealership-settings':
                this.loadDealershipSettings();
                break;
        }
    }
    
    async loadRawDataOverview() {
        const overview = document.getElementById('rawDataOverview');
        if (overview) {
            overview.innerHTML = '<div class="loading">Loading raw data statistics...</div>';
            
            try {
                const response = await fetch('/api/raw-data');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                overview.innerHTML = `
                    <div class="overview-card">
                        <h3>Raw Data Overview</h3>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <strong>Total Records:</strong> ${data.total_count}
                            </div>
                        </div>
                        
                        <h4>By Location:</h4>
                        <div class="data-table">
                            ${data.by_location.map(loc => `
                                <div class="data-row">
                                    <span class="location">${loc.location || 'Unknown'}</span>
                                    <span class="count">${loc.count} vehicles</span>
                                    <span class="date">Last: ${new Date(loc.last_import).toLocaleDateString()}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <h4>Recent Imports:</h4>
                        <div class="data-table">
                            ${data.recent_imports.slice(0, 5).map(vehicle => `
                                <div class="data-row">
                                    <span>${vehicle.year} ${vehicle.make} ${vehicle.model}</span>
                                    <span class="location">${vehicle.location || 'Unknown'}</span>
                                    <span class="date">${new Date(vehicle.import_timestamp).toLocaleDateString()}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading raw data:', error);
                overview.innerHTML = `
                    <div class="overview-card error">
                        <h3>Raw Data Overview</h3>
                        <p>Error loading data: ${error.message}</p>
                    </div>
                `;
            }
        }
    }
    
    async loadNormalizedDataOverview() {
        const overview = document.getElementById('normalizedDataOverview');
        if (overview) {
            overview.innerHTML = '<div class="loading">Loading normalized data statistics...</div>';
            
            try {
                const response = await fetch('/api/normalized-data');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                overview.innerHTML = `
                    <div class="overview-card">
                        <h3>Normalized Data Overview</h3>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <strong>Total Records:</strong> ${data.total_count}
                            </div>
                        </div>
                        
                        <h4>By Make:</h4>
                        <div class="data-table">
                            ${data.by_make.map(make => `
                                <div class="data-row">
                                    <span class="make">${make.make}</span>
                                    <span class="count">${make.count} vehicles</span>
                                    <span class="price">Avg: $${Math.round(make.avg_price || 0).toLocaleString()}</span>
                                    <span class="years">${make.min_year}-${make.max_year}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <h4>Recent Updates:</h4>
                        <div class="data-table">
                            ${data.recent_updates.slice(0, 5).map(vehicle => `
                                <div class="data-row">
                                    <span>${vehicle.year} ${vehicle.make} ${vehicle.model}</span>
                                    <span class="price">$${(vehicle.price || 0).toLocaleString()}</span>
                                    <span class="date">${new Date(vehicle.updated_at).toLocaleDateString()}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading normalized data:', error);
                overview.innerHTML = `
                    <div class="overview-card error">
                        <h3>Normalized Data Overview</h3>
                        <p>Error loading data: ${error.message}</p>
                    </div>
                `;
            }
        }
    }
    
    async loadOrderProcessingOverview() {
        const overview = document.getElementById('orderStatusOverview');
        if (overview) {
            overview.innerHTML = '<div class="loading">Loading order processing statistics...</div>';
            
            try {
                const response = await fetch('/api/order-processing');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                overview.innerHTML = `
                    <div class="overview-card">
                        <h3>Order Processing Overview</h3>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <strong>Total Jobs:</strong> ${data.total_jobs}
                            </div>
                            <div class="stat-item">
                                <strong>Completed:</strong> ${data.statistics.completed_jobs || 0}
                            </div>
                            <div class="stat-item">
                                <strong>Failed:</strong> ${data.statistics.failed_jobs || 0}
                            </div>
                            <div class="stat-item">
                                <strong>Total Vehicles:</strong> ${Math.round(data.statistics.total_vehicles_processed || 0)}
                            </div>
                        </div>
                        
                        <h4>Jobs by Status:</h4>
                        <div class="data-table">
                            ${data.by_status.map(status => `
                                <div class="data-row">
                                    <span class="status">${status.status}</span>
                                    <span class="count">${status.count} jobs</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <h4>Recent Jobs:</h4>
                        <div class="data-table">
                            ${data.recent_jobs.slice(0, 5).map(job => `
                                <div class="data-row">
                                    <span class="dealer">${job.dealership_name}</span>
                                    <span class="type">${job.job_type}</span>
                                    <span class="count">${job.vehicle_count} vehicles</span>
                                    <span class="status">${job.status}</span>
                                    <span class="date">${new Date(job.created_at).toLocaleDateString()}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading order processing data:', error);
                overview.innerHTML = `
                    <div class="overview-card error">
                        <h3>Order Processing Overview</h3>
                        <p>Error loading data: ${error.message}</p>
                    </div>
                `;
            }
        }
    }
    
    async loadQROverview() {
        // This would load QR generation statistics
        const overview = document.getElementById('qrOverview');
        if (overview) {
            overview.innerHTML = `
                <div class="overview-card">
                    <h3>QR Generation</h3>
                    <div class="metric">
                        <span class="metric-label">QR Codes Generated</span>
                        <span class="metric-value">Loading...</span>
                    </div>
                </div>
            `;
        }
    }
    
    async loadExportFiles() {
        // This would load available export files
        const exportFiles = document.getElementById('exportFiles');
        if (exportFiles) {
            exportFiles.innerHTML = `
                <div class="export-file">
                    <div class="file-info">
                        <div class="file-name">No export files available</div>
                        <div class="file-details">Run a scrape to generate export files</div>
                    </div>
                </div>
            `;
        }
    }
    
    async generateAdobeReport() {
        try {
            this.addTerminalMessage('Generating Adobe export files...', 'info');
            
            const selectedDealerships = Array.from(this.selectedDealerships);
            const queryParams = selectedDealerships.map(d => `dealerships=${encodeURIComponent(d)}`).join('&');
            
            const response = await fetch(`/api/reports/adobe?${queryParams}`);
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Generated ${result.count} Adobe export files`, 'success');
                this.loadExportFiles(); // Refresh the export files list
            } else {
                this.addTerminalMessage('Failed to generate Adobe export files', 'error');
            }
            
        } catch (error) {
            console.error('Error generating Adobe report:', error);
            this.addTerminalMessage(`Error generating Adobe report: ${error.message}`, 'error');
        }
    }
    
    async generateSummaryReport() {
        try {
            this.addTerminalMessage('Generating summary report...', 'info');
            
            const response = await fetch('/api/reports/summary');
            const report = await response.json();
            
            if (report.error) {
                this.addTerminalMessage('No scrape data available for summary report', 'warning');
                return;
            }
            
            // Display summary report in terminal
            this.addTerminalMessage('=== SCRAPER SUMMARY REPORT ===', 'success');
            this.addTerminalMessage(`Scrape Date: ${report.scrape_date} at ${report.scrape_time}`, 'info');
            this.addTerminalMessage(`Duration: ${report.duration_formatted}`, 'info');
            this.addTerminalMessage(`Total Vehicles: ${report.total_vehicles}`, 'info');
            this.addTerminalMessage(`Missing VINs: ${report.missing_vins}`, report.missing_vins > 0 ? 'warning' : 'info');
            this.addTerminalMessage(`Dealerships: ${report.dealerships_successful}/${report.dealerships_processed} successful`, 'info');
            
            if (report.total_errors > 0) {
                this.addTerminalMessage(`Errors: ${report.total_errors}`, 'error');
                report.errors.forEach(error => {
                    this.addTerminalMessage(`  - ${error}`, 'error');
                });
            }
            
            this.addTerminalMessage('=== END SUMMARY REPORT ===', 'success');
            
        } catch (error) {
            console.error('Error generating summary report:', error);
            this.addTerminalMessage(`Error generating summary report: ${error.message}`, 'error');
        }
    }
    
    showScheduleModal() {
        this.showModal('scheduleModal');
    }
    
    showDealershipSelectionModal() {
        this.renderDealershipCheckboxes('dealershipCheckboxGridModal');
        this.showModal('dealershipSelectionModal');
    }
    
    saveScheduleSettings() {
        // This would save schedule settings
        this.addTerminalMessage('Schedule settings saved', 'success');
        this.closeModal('scheduleModal');
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
        }
    }
    
    addTerminalMessage(message, type = 'info') {
        const terminal = document.getElementById('terminalOutput');
        if (!terminal) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = 'terminal-line';
        
        line.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message ${type}">${message}</span>
        `;
        
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
        
        // Keep only last 100 messages
        const lines = terminal.querySelectorAll('.terminal-line');
        if (lines.length > 100) {
            lines[0].remove();
        }
    }
    
    clearTerminal() {
        const terminal = document.getElementById('terminalOutput');
        if (terminal) {
            terminal.innerHTML = '';
            this.addTerminalMessage('Terminal cleared', 'info');
        }
    }
    
    addScraperConsoleMessage(message, type = 'info') {
        const console = document.getElementById('scraperConsoleOutput');
        if (!console) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = 'terminal-line';
        
        line.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message ${type}">${message}</span>
        `;
        
        console.appendChild(line);
        
        // Auto-scroll to bottom
        console.scrollTop = console.scrollHeight;
        
        // Limit console lines to prevent memory issues
        const lines = console.querySelectorAll('.terminal-line');
        if (lines.length > 500) {
            lines[0].remove();
        }
    }
    
    clearScraperConsole() {
        const console = document.getElementById('scraperConsoleOutput');
        if (console) {
            console.innerHTML = '';
            this.addScraperConsoleMessage('Scraper console cleared', 'info');
        }
    }
    
    startStatusPolling() {
        // Check status every 5 seconds
        setInterval(() => {
            this.checkScraperStatus();
        }, 5000);
        
        // Load logs every 10 seconds
        setInterval(() => {
            this.loadRecentLogs();
        }, 10000);
    }
    
    async loadRecentLogs() {
        try {
            const response = await fetch('/api/logs');
            const result = await response.json();
            
            if (result.logs && result.logs.length > 0) {
                // Add new log entries to terminal (simplified version)
                // In a full implementation, you'd track which logs have been shown
            }
            
        } catch (error) {
            // Silently handle log loading errors
        }
    }
    
    // Real-time progress event handlers
    onScrapingSessionStart(data) {
        console.log('Scraping session started:', data);
        
        this.progressData.totalScrapers = data.total_scrapers;
        this.progressData.completedScrapers = 0;
        this.progressData.progressPercent = 0;
        
        // Initialize modal progress
        this.modalProgress = {
            dealershipsProcessed: 0,
            vehiclesProcessed: 0,
            errors: 0,
            totalDealerships: data.total_scrapers,
            progressPercent: 0
        };
        
        // Show progress bar
        const scraperStatus = document.getElementById('scraperStatus');
        if (scraperStatus) {
            scraperStatus.style.display = 'block';
        }
        
        // Update UI
        this.updateProgressBar(0);
        this.addTerminalMessage(`🚀 Starting scraper session: ${data.total_scrapers} scrapers`, 'info');
        this.addTerminalMessage(`📋 Target dealerships: ${data.scraper_names.join(', ')}`, 'info');
        
        // Add to scraper console
        this.addScraperConsoleMessage(`🚀 SCRAPER SESSION STARTED`, 'success');
        this.addScraperConsoleMessage(`📊 Total scrapers: ${data.total_scrapers}`, 'info');
        
        // Add to modal console
        this.addModalConsoleMessage(`🚀 SCRAPER SESSION STARTED`, 'success');
        this.addModalConsoleMessage(`📊 Total scrapers: ${data.total_scrapers}`, 'info');
        this.addScraperConsoleMessage(`📋 Dealerships: ${data.scraper_names.join(', ')}`, 'info');
        this.addScraperConsoleMessage('', 'info'); // Empty line
        
        // Update button state
        const startBtn = document.getElementById('startScrapeBtn');
        if (startBtn) {
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
            startBtn.disabled = true;
        }
        
        this.scraperRunning = true;
    }
    
    onScraperStart(data) {
        console.log('Scraper started:', data);
        
        this.progressData.currentScraper = data.scraper_name;
        
        this.addTerminalMessage(`🔄 Starting scraper: ${data.scraper_name}`, 'info');
        if (data.expected_vehicles) {
            this.addTerminalMessage(`   Expected vehicles: ~${data.expected_vehicles}`, 'info');
        }
        this.addTerminalMessage(`   Progress: ${data.progress}/${data.total}`, 'info');
        
        // Add to scraper console
        this.addScraperConsoleMessage(`🔄 STARTING: ${data.scraper_name}`, 'info');
        if (data.expected_vehicles) {
            this.addScraperConsoleMessage(`   Expected vehicles: ~${data.expected_vehicles}`, 'info');
        }
        this.addScraperConsoleMessage(`   Progress: ${data.progress}/${data.total}`, 'info');
        
        // Update status details
        this.updateStatusDetails(`Running: ${data.scraper_name}`);
    }
    
    onScraperProgress(data) {
        console.log('Scraper progress:', data);
        
        // Add terminal message (scraper 18 style)
        this.addTerminalMessage(`   [${data.timestamp}] ${data.status}`, 'info');
        if (data.details) {
            this.addTerminalMessage(`   └── ${data.details}`, 'info');
        }
        
        // Add to scraper console with enhanced detail
        this.addScraperConsoleMessage(`${data.status}`, 'info');
        if (data.details) {
            this.addScraperConsoleMessage(`└── ${data.details}`, 'info');
        }
        
        // Update Live Scraper Console progress indicators
        this.updateScraperConsoleIndicators(data);
        
        // Update real-time progress indicators
        if (data.overall_progress !== undefined) {
            this.updateProgressBar(data.overall_progress);
            this.progressData.progressPercent = data.overall_progress;
        }
        
        // Update dealership progress indicators
        if (data.completed_scrapers !== undefined) {
            this.progressData.completedScrapers = data.completed_scrapers;
        }
        
        // Update vehicles processed indicator
        if (data.vehicles_processed !== undefined) {
            this.updateVehiclesProcessed(data.vehicles_processed);
        }
        
        
        // Update errors indicator
        if (data.errors !== undefined) {
            this.updateErrorsCount(data.errors);
        }
        
        // Update page progress for current scraper
        if (data.current_page && data.total_pages) {
            this.updateCurrentScraperProgress(data.scraper_name, data.current_page, data.total_pages);
        }
        
        // Update status details with enhanced info
        let statusMessage = `${data.scraper_name}: ${data.status}`;
        if (data.vehicles_processed > 0) {
            statusMessage += ` (${data.vehicles_processed} vehicles)`;
        }
        if (data.current_page && data.total_pages) {
            statusMessage += ` [Page ${data.current_page}/${data.total_pages}]`;
        }
        this.updateStatusDetails(statusMessage);
    }
    
    updateScraperConsoleIndicators(data) {
        // Update the progress indicators in the Live Scraper Console header
        const dealershipsProcessed = data.completed_scrapers || this.progressData.completedScrapers || 0;
        const vehiclesProcessed = this.progressData.totalVehiclesProcessed || 0;
        const errors = this.progressData.totalErrors || 0;
        
        // Update indicator values
        const dealershipsElement = document.getElementById('dealershipsProcessed');
        const vehiclesElement = document.getElementById('vehiclesProcessed');
        const errorsElement = document.getElementById('errorsCount');
        
        if (dealershipsElement) dealershipsElement.textContent = dealershipsProcessed;
        if (vehiclesElement) vehiclesElement.textContent = vehiclesProcessed;
        if (errorsElement) errorsElement.textContent = errors;
    }
    
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
    
    async testWebSocketConnection() {
        this.addScraperConsoleMessage('🧪 Testing WebSocket connection...', 'info');
        
        try {
            const response = await fetch('/api/test-websocket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addScraperConsoleMessage('📡 WebSocket test message sent from server', 'success');
            } else {
                this.addScraperConsoleMessage('❌ Failed to send WebSocket test message', 'error');
            }
        } catch (error) {
            console.error('Error testing WebSocket:', error);
            this.addScraperConsoleMessage(`❌ WebSocket test error: ${error.message}`, 'error');
        }
    }
    
    onScraperComplete(data) {
        console.log('Scraper completed:', data);
        
        this.progressData.completedScrapers = data.completed;
        this.progressData.progressPercent = data.progress_percent;
        
        // Update progress bar
        this.updateProgressBar(data.progress_percent);
        
        // Terminal output
        if (data.success) {
            const statusIcon = data.is_real_data ? "🎉" : "⚠️";
            const dataType = data.is_real_data ? "REAL DATA" : "FALLBACK";
            this.addTerminalMessage(`${statusIcon} COMPLETED: ${data.scraper_name}`, 'success');
            this.addTerminalMessage(`   ✅ Vehicles found: ${data.vehicle_count}`, 'success');
            this.addTerminalMessage(`   📊 Data source: ${data.data_source}`, 'info');
            this.addTerminalMessage(`   🎯 Data type: ${dataType}`, data.is_real_data ? 'success' : 'warning');
            if (data.duration) {
                this.addTerminalMessage(`   ⏱️  Duration: ${data.duration.toFixed(1)}s`, 'info');
            }
            
            // Add to scraper console
            this.addScraperConsoleMessage(`${statusIcon} COMPLETED: ${data.scraper_name}`, 'success');
            this.addScraperConsoleMessage(`✅ Vehicles found: ${data.vehicle_count}`, 'success');
            this.addScraperConsoleMessage(`📊 Data source: ${data.data_source}`, 'info');
            this.addScraperConsoleMessage(`🎯 Data type: ${dataType}`, data.is_real_data ? 'success' : 'warning');
        } else {
            this.addTerminalMessage(`❌ FAILED: ${data.scraper_name}`, 'error');
            this.addTerminalMessage(`   🚫 Error: ${data.error}`, 'error');
            
            // Add to scraper console
            this.addScraperConsoleMessage(`❌ FAILED: ${data.scraper_name}`, 'error');
            this.addScraperConsoleMessage(`🚫 Error: ${data.error}`, 'error');
        }
        
        this.addTerminalMessage(`   📈 Overall progress: ${data.progress_percent.toFixed(1)}% (${data.completed + data.failed}/${data.total})`, 'info');
        this.addTerminalMessage('', 'info'); // Empty line for spacing
        
        this.addScraperConsoleMessage(`📈 Progress: ${data.progress_percent.toFixed(1)}% (${data.completed + data.failed}/${data.total})`, 'info');
        this.addScraperConsoleMessage('', 'info'); // Empty line
        
        // Update status details
        this.updateStatusDetails(`Completed: ${data.scraper_name} (${data.progress_percent.toFixed(1)}%)`);
    }
    
    onScrapingSessionComplete(data) {
        console.log('Scraping session completed:', data);
        
        // Update progress bar to 100%
        this.updateProgressBar(100);
        
        // Terminal output
        this.addTerminalMessage('=' * 80, 'info');
        this.addTerminalMessage('🏆 SCRAPING SESSION COMPLETED', 'success');
        this.addTerminalMessage('=' * 80, 'info');
        this.addTerminalMessage(`⏰ Completed at: ${new Date(data.end_time).toLocaleString()}`, 'info');
        this.addTerminalMessage(`⏱️  Total duration: ${data.total_duration.toFixed(1)} seconds`, 'info');
        this.addTerminalMessage(`📊 Scrapers run: ${data.total_scrapers}`, 'info');
        this.addTerminalMessage(`✅ Successful: ${data.completed}`, 'success');
        this.addTerminalMessage(`❌ Failed: ${data.failed}`, data.failed > 0 ? 'error' : 'info');
        this.addTerminalMessage(`📈 Success rate: ${data.success_rate.toFixed(1)}%`, 'info');
        this.addTerminalMessage('', 'info');
        this.addTerminalMessage(`🚗 Total vehicles: ${data.total_vehicles}`, 'info');
        this.addTerminalMessage(`🎯 Real data: ${data.total_real_data}`, 'success');
        this.addTerminalMessage(`🔄 Fallback data: ${data.total_fallback_data}`, 'warning');
        
        if (data.total_real_data > 0) {
            const realDataPercent = (data.total_real_data / data.total_vehicles * 100);
            this.addTerminalMessage(`🎉 Real data rate: ${realDataPercent.toFixed(1)}%`, 'success');
        }
        
        if (data.errors && data.errors.length > 0) {
            this.addTerminalMessage(`⚠️  Errors encountered: ${data.errors.length}`, 'warning');
            data.errors.slice(0, 3).forEach(error => {
                this.addTerminalMessage(`   - ${error}`, 'error');
            });
            if (data.errors.length > 3) {
                this.addTerminalMessage(`   ... and ${data.errors.length - 3} more`, 'error');
            }
        }
        
        this.addTerminalMessage('=' * 80, 'info');
        
        if (data.total_real_data > 0) {
            this.addTerminalMessage('🎉 SUCCESS: Real data extracted from live APIs!', 'success');
        } else {
            this.addTerminalMessage('⚠️ WARNING: No real data extracted - check API connectivity', 'warning');
        }
        
        this.addTerminalMessage('=' * 80, 'info');
        
        // Reset UI state
        this.scraperRunning = false;
        this.updateScraperButtonStates();
        
        // Update status details
        this.updateStatusDetails(`Session complete: ${data.success_rate.toFixed(1)}% success rate`);
        
        // Refresh data tabs
        this.loadRawDataOverview();
        this.loadNormalizedDataOverview();
        this.loadOrderProcessingOverview();
    }
    
    updateProgressBar(percent) {
        const progressFill = document.getElementById('progressFill');
        if (progressFill) {
            progressFill.style.width = `${percent}%`;
        }
        
        // Update progress text
        const statusHeader = document.querySelector('.scraper-status .status-header h3');
        if (statusHeader) {
            statusHeader.textContent = `Scraper Progress (${percent.toFixed(1)}%)`;
        }
    }
    
    updateVehiclesProcessed(count) {
        // Update vehicles processed indicator in the GUI
        const vehiclesEl = document.getElementById('vehiclesProcessed');
        if (vehiclesEl) {
            vehiclesEl.textContent = count.toLocaleString();
        }
        
        // Update any other vehicle counter elements
        const vehicleCounters = document.querySelectorAll('.vehicle-count');
        vehicleCounters.forEach(el => {
            el.textContent = count.toLocaleString();
        });
    }
    
    updateErrorsCount(count) {
        // Update errors indicator in the GUI
        const errorsEl = document.getElementById('errorsCount');
        if (errorsEl) {
            errorsEl.textContent = count;
            // Change color based on error count
            if (count > 0) {
                errorsEl.className = 'metric-value status-error';
            } else {
                errorsEl.className = 'metric-value status-online';
            }
        }
    }
    
    updateCurrentScraperProgress(scraperName, currentPage, totalPages) {
        // Update current scraper progress indicator
        const currentScraperEl = document.getElementById('currentScraper');
        if (currentScraperEl) {
            currentScraperEl.textContent = `${scraperName} (Page ${currentPage}/${totalPages})`;
        }
        
        // Update scraper-specific progress bar if it exists
        const scraperProgressEl = document.getElementById('scraperSpecificProgress');
        if (scraperProgressEl && totalPages > 0) {
            const scraperPercent = (currentPage / totalPages) * 100;
            scraperProgressEl.style.width = `${scraperPercent}%`;
        }
    }
    
    updateStatusDetails(message) {
        const statusDetails = document.getElementById('statusDetails');
        if (statusDetails) {
            const timestamp = new Date().toLocaleTimeString();
            statusDetails.innerHTML = `
                <div class="status-detail">
                    <span class="status-time">[${timestamp}]</span>
                    <span class="status-message">${message}</span>
                </div>
            `;
        }
    }
    
    // System Status Dashboard Functions
    async loadSystemStatus() {
        try {
            console.log('Loading system status...');
            
            // Load active scrapers count
            const scrapersResponse = await fetch('/api/dealerships');
            const dealerships = await scrapersResponse.json();
            const activeScrapers = dealerships.filter(d => d.is_active).length;
            
            // Load database health
            const dbResponse = await fetch('/api/test-database');
            const dbHealth = await dbResponse.json();
            
            // Load vehicle count
            const rawDataResponse = await fetch('/api/raw-data');
            const rawData = await rawDataResponse.json();
            
            // Load order processing status
            const orderResponse = await fetch('/api/orders/today-schedule');
            const todaySchedule = await orderResponse.json();
            
            // Update system metrics
            this.updateSystemMetrics({
                activeScrapers: activeScrapers,
                databaseHealth: dbHealth.status === 'success' ? 'Excellent' : 'Warning',
                orderProcessingStatus: 'Ready',
                vehicleCount: rawData.total_count || 0,
                todayScheduleCount: todaySchedule.length || 0
            });
            
        } catch (error) {
            console.error('Error loading system status:', error);
            this.updateSystemMetrics({
                activeScrapers: 'Error',
                databaseHealth: 'Error',
                orderProcessingStatus: 'Error',
                vehicleCount: 'Error'
            });
        }
    }
    
    updateSystemMetrics(metrics) {
        // Update active scrapers
        const activeScrapersEl = document.getElementById('activeScrapers');
        if (activeScrapersEl) {
            activeScrapersEl.textContent = metrics.activeScrapers;
            activeScrapersEl.className = 'metric-value ' + (metrics.activeScrapers > 0 ? 'status-online' : 'status-warning');
        }
        
        // Update database health
        const databaseHealthEl = document.getElementById('databaseHealth');
        if (databaseHealthEl) {
            databaseHealthEl.textContent = metrics.databaseHealth;
            const healthClass = metrics.databaseHealth === 'Excellent' ? 'status-online' : 
                               metrics.databaseHealth === 'Warning' ? 'status-warning' : 'status-error';
            databaseHealthEl.className = 'metric-value ' + healthClass;
        }
        
        // Update order processing status
        const orderStatusEl = document.getElementById('orderProcessingStatus');
        if (orderStatusEl) {
            orderStatusEl.textContent = metrics.orderProcessingStatus;
            orderStatusEl.className = 'metric-value status-online';
        }
        
        // Update vehicle count
        const vehicleCountEl = document.getElementById('vehicleCount');
        if (vehicleCountEl) {
            vehicleCountEl.textContent = typeof metrics.vehicleCount === 'number' ? 
                metrics.vehicleCount.toLocaleString() : metrics.vehicleCount;
            vehicleCountEl.className = 'metric-value status-online';
        }
    }
    
    // System status refresh handler
    async refreshSystemStatus() {
        const refreshBtn = document.getElementById('refreshSystemStatus');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        }
        
        await this.loadSystemStatus();
        
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync"></i> Refresh';
        }
        
        this.addTerminalMessage('System status refreshed', 'success');
    }
    
    // Export system report
    async exportSystemReport() {
        try {
            const response = await fetch('/api/reports/summary');
            const report = await response.json();
            
            // Create and download JSON report
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `silver_fox_system_report_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.addTerminalMessage('System report exported successfully', 'success');
            
        } catch (error) {
            console.error('Export error:', error);
            this.addTerminalMessage('Failed to export system report', 'error');
        }
    }
    
    // =============================================================================
    // NEW QUEUE MANAGEMENT FUNCTIONALITY
    // =============================================================================
    
    async loadQueueManagement() {
        console.log('Loading new queue management interface...');
        
        // Set up event listeners for new queue system
        this.setupNewQueueEventListeners();
        
        // Load dealership list and defaults
        await this.loadDealershipList();
        await this.loadDealershipDefaults();
        
        // Re-render dealership list with correct types
        this.renderDealershipList(this.dealerships);
        
        // Set up search functionality when queue management tab is loaded
        this.setupDealershipSearchListeners();
        
        // Initialize empty queue
        this.renderQueue();
        
        this.addTerminalMessage('Queue management interface loaded', 'success');
    }
    
    async loadDealershipSettings() {
        console.log('Loading dealership settings...');
        
        try {
            const response = await fetch('/api/dealerships');
            const dealerships = await response.json();
            
            this.renderDealershipSettings(dealerships);
        } catch (error) {
            console.error('Error loading dealership settings:', error);
            this.showDealershipSettingsError('Error loading dealership settings');
        }
    }
    
    renderDealershipSettings(dealerships) {
        const container = document.getElementById('dealershipSettingsGrid');
        
        if (!dealerships || dealerships.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-cog"></i>
                    <h3>No Dealership Configurations Found</h3>
                    <p>No dealership settings are available.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = dealerships.map(dealer => {
            const vehicleTypes = dealer.filtering_rules?.vehicle_types || [];
            const vehicleTypesDisplay = vehicleTypes.length > 0 
                ? vehicleTypes.map(type => {
                    const typeDisplay = type.charAt(0).toUpperCase() + type.slice(1);
                    return `<span class="vehicle-type-tag ${type}">${typeDisplay}</span>`;
                }).join('')
                : '<span class="no-types">No vehicle types configured</span>';
            
            return `
            <div class="dealership-settings-card" data-dealer-name="${dealer.name}">
                <div class="settings-card-header">
                    <h3>${dealer.name}</h3>
                    <div class="active-status">
                        <input type="checkbox" 
                               id="active-${dealer.name.replace(/\s+/g, '-')}" 
                               ${dealer.is_active ? 'checked' : ''} 
                               onchange="app.toggleDealershipActive('${dealer.name}', this.checked)">
                        <label for="active-${dealer.name.replace(/\s+/g, '-')}">Active</label>
                    </div>
                </div>
                <div class="settings-card-body">
                    <div class="setting-group">
                        <label>Vehicle Types to Process:</label>
                        <div class="vehicle-types-display">
                            ${vehicleTypesDisplay}
                        </div>
                    </div>
                    
                    <div class="setting-group">
                        <label>Configuration:</label>
                        <div class="config-details">
                            <span class="config-item">
                                <i class="fas fa-car"></i>
                                ${vehicleTypes.length} vehicle type(s) configured
                            </span>
                            <span class="config-item">
                                <i class="fas fa-calendar"></i>
                                Updated: ${dealer.updated_at ? new Date(dealer.updated_at).toLocaleDateString() : 'Never'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="setting-actions">
                        <button class="btn btn-secondary btn-sm" onclick="app.editDealershipSettings('${dealer.name}')">
                            <i class="fas fa-edit"></i>
                            Edit Settings
                        </button>
                    </div>
                </div>
            </div>
            `;
        }).join('');
        
        // Setup save button
        const saveBtn = document.getElementById('saveDealershipSettings');
        if (saveBtn && !saveBtn.hasEventListener) {
            saveBtn.addEventListener('click', () => this.saveDealershipSettings());
            saveBtn.hasEventListener = true;
        }
        
        // Setup refresh button
        const refreshBtn = document.getElementById('refreshDealershipSettings');
        if (refreshBtn && !refreshBtn.hasEventListener) {
            refreshBtn.addEventListener('click', () => this.loadDealershipSettings());
            refreshBtn.hasEventListener = true;
        }
    }
    
    showDealershipSettingsError(message) {
        const container = document.getElementById('dealershipSettingsGrid');
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error Loading Settings</h3>
                <p>${message}</p>
                <button class="btn btn-secondary" onclick="app.loadDealershipSettings()">
                    <i class="fas fa-sync"></i>
                    Try Again
                </button>
            </div>
        `;
    }
    
    async toggleDealershipActive(dealershipName, isActive) {
        try {
            const response = await fetch(`/api/dealerships/${encodeURIComponent(dealershipName)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    is_active: isActive
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`${dealershipName} ${isActive ? 'activated' : 'deactivated'}`, 'success');
            } else {
                this.addTerminalMessage(`Failed to update ${dealershipName}: ${result.error}`, 'error');
                // Reload settings to reset checkbox state
                this.loadDealershipSettings();
            }
        } catch (error) {
            console.error('Error toggling dealership active state:', error);
            this.addTerminalMessage(`Error updating ${dealershipName}`, 'error');
            // Reload settings to reset checkbox state
            this.loadDealershipSettings();
        }
    }
    
    async editDealershipSettings(dealershipName) {
        console.log(`Editing settings for: ${dealershipName}`);
        this.addTerminalMessage('Dealership settings editor - Coming soon!', 'info');
    }
    
    async saveDealershipSettings() {
        console.log('Saving dealership settings...');
        // Implementation for saving settings
        this.addTerminalMessage('Dealership settings saved', 'success');
    }
    
    setupNewQueueEventListeners() {
        // Day buttons
        document.querySelectorAll('.day-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const day = e.currentTarget.dataset.day;
                this.addDayToQueue(day);
            });
        });
        
        // Clear queue button
        const clearBtn = document.getElementById('clearQueueBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearQueue());
        }
        
        // Process queue button
        const processBtn = document.getElementById('processQueueBtn');
        if (processBtn) {
            processBtn.addEventListener('click', (e) => {
                try {
                    console.log('Process Queue button clicked, queue size:', this.processingQueue.size);
                    this.addTerminalMessage('Process Queue button clicked...', 'info');
                    this.launchOrderWizard();
                } catch (error) {
                    console.error('Error in process queue button:', error);
                    this.addTerminalMessage(`Error processing queue: ${error.message}`, 'error');
                }
            });
        }
        
        // Refresh button (reuses existing functionality)
        const refreshBtn = document.getElementById('refreshQueueBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDealershipList());
        }
    }
    
    async loadDealershipList() {
        try {
            const response = await fetch('/api/dealerships');
            const dealerships = await response.json();
            
            this.dealerships = dealerships;
            this.renderDealershipList(dealerships);
            
            this.addTerminalMessage(`Loaded ${dealerships.length} dealerships`, 'success');
            
        } catch (error) {
            console.error('Error loading dealerships:', error);
            this.addTerminalMessage(`Error loading dealerships: ${error.message}`, 'error');
        }
    }
    
    renderDealershipList(dealerships) {
        console.log('🏢 Rendering dealership list...', {
            dealerships: dealerships ? dealerships.length : 0,
            hasDefaults: this.dealershipDefaults ? this.dealershipDefaults.size : 0
        });
        
        const dealershipList = document.getElementById('dealershipList');
        if (!dealershipList) {
            console.error('❌ dealershipList element not found');
            return;
        }
        
        if (!dealerships || dealerships.length === 0) {
            console.log('⚠️ No dealerships to render');
            dealershipList.innerHTML = '<div class="loading">No dealerships available</div>';
            return;
        }
        
        try {
            const html = dealerships.map(dealership => {
                const dealershipType = this.getDealershipDefault(dealership.name);
                const typeClass = dealershipType.toLowerCase(); // 'cao' or 'list'
                console.log(`🏢 Dealership: ${dealership.name} -> Type: ${dealershipType} -> Class: ${typeClass}`);
                return `
                    <div class="dealership-item" data-dealership="${dealership.name}">
                        <div class="dealership-name">${dealership.name}</div>
                        <div class="dealership-type ${typeClass}">${dealershipType}</div>
                    </div>
                `;
            }).join('');
            
            dealershipList.innerHTML = html;
            console.log('✅ Dealership list rendered successfully');
        } catch (error) {
            console.error('❌ Error rendering dealership list:', error);
            dealershipList.innerHTML = '<div class="loading error">Error loading dealerships</div>';
        }
        
        // Set up event delegation for dealership items
        this.setupDealershipEventListeners();
    }
    
    setupDealershipEventListeners() {
        const dealershipList = document.getElementById('dealershipList');
        if (!dealershipList) return;
        
        // Remove existing listeners to prevent duplicates
        dealershipList.removeEventListener('click', this.dealershipClickHandler);
        
        // Create bound handler function
        this.dealershipClickHandler = (e) => {
            const dealershipItem = e.target.closest('.dealership-item');
            if (dealershipItem) {
                const dealershipName = dealershipItem.getAttribute('data-dealership');
                if (dealershipName) {
                    this.addDealershipToQueue(dealershipName);
                }
            }
        };
        
        // Add event listener using delegation
        dealershipList.addEventListener('click', this.dealershipClickHandler);
    }
    
    setupDealershipSearchListeners() {
        console.log('🔍 Setting up dealership search listeners...');
        
        // Wait a bit for DOM to be ready
        setTimeout(() => {
            const searchInput = document.getElementById('dealershipSearchInput');
            const searchBtn = document.getElementById('dealershipSearchBtn');
            const clearBtn = document.getElementById('clearDealershipSearchBtn');
            
            console.log('Search elements found:', {
                searchInput: !!searchInput,
                searchBtn: !!searchBtn,
                clearBtn: !!clearBtn
            });
            
            if (searchInput) {
                console.log('✅ Search input found, adding listeners');
                
                // Add fresh listeners (don't try to remove since we don't have references)
                searchInput.addEventListener('input', () => {
                    console.log('🔍 Search input changed:', searchInput.value);
                    this.filterDealershipList();
                });
                searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        console.log('🔍 Enter key pressed in search');
                        this.filterDealershipList();
                    }
                });
                console.log('✅ Search input listeners added');
                
                // Clear any existing value and ensure all items are visible
                console.log('🧪 Clearing search input...');
                searchInput.value = '';
                this.filterDealershipList(); // Show all dealerships
            } else {
                console.error('❌ Search input not found!');
            }
            
            if (searchBtn) {
                searchBtn.addEventListener('click', () => {
                    console.log('🔍 Search button clicked');
                    this.filterDealershipList();
                });
                console.log('✅ Search button listener added');
            }
            
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    console.log('🔍 Clear button clicked');
                    this.clearDealershipSearch();
                });
                console.log('✅ Clear button listener added');
            }
        }, 100);
    }
    
    filterDealershipList() {
        console.log('🔍 Filtering dealership list...');
        const searchInput = document.getElementById('dealershipSearchInput');
        const clearBtn = document.getElementById('clearDealershipSearchBtn');
        const dealershipList = document.getElementById('dealershipList');
        
        if (!searchInput || !dealershipList) {
            console.log('❌ Missing search elements:', {
                searchInput: !!searchInput,
                dealershipList: !!dealershipList
            });
            return;
        }
        
        const searchTerm = searchInput.value.toLowerCase().trim();
        const dealershipItems = dealershipList.querySelectorAll('.dealership-item');
        
        console.log('🔍 Search details:', {
            searchTerm,
            itemCount: dealershipItems.length
        });
        
        // Show/hide clear button
        if (clearBtn) {
            clearBtn.style.display = searchTerm ? 'inline-block' : 'none';
        }
        
        let visibleCount = 0;
        dealershipItems.forEach((item, index) => {
            const dealershipName = item.querySelector('.dealership-name');
            if (dealershipName) {
                const name = dealershipName.textContent.toLowerCase();
                const matches = !searchTerm || name.includes(searchTerm);
                item.style.display = matches ? 'flex' : 'none';
                if (matches) visibleCount++;
                
                if (index < 3) { // Log first 3 items for debugging
                    console.log(`Item ${index}: "${name}" matches "${searchTerm}": ${matches}`);
                }
            }
        });
        
        console.log(`🔍 Filter results: ${visibleCount}/${dealershipItems.length} visible`);
        
        // Show "no results" message if needed
        this.updateDealershipSearchResults(visibleCount, searchTerm);
    }
    
    clearDealershipSearch() {
        const searchInput = document.getElementById('dealershipSearchInput');
        const clearBtn = document.getElementById('clearDealershipSearchBtn');
        
        if (searchInput) {
            searchInput.value = '';
        }
        if (clearBtn) {
            clearBtn.style.display = 'none';
        }
        
        this.filterDealershipList();
    }
    
    updateDealershipSearchResults(visibleCount, searchTerm) {
        const dealershipList = document.getElementById('dealershipList');
        if (!dealershipList) return;
        
        // Remove any existing "no results" message
        const existingNoResults = dealershipList.querySelector('.no-search-results');
        if (existingNoResults) {
            existingNoResults.remove();
        }
        
        // Add "no results" message if search term exists but no matches
        if (searchTerm && visibleCount === 0) {
            const noResultsDiv = document.createElement('div');
            noResultsDiv.className = 'no-search-results';
            noResultsDiv.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    <i class="fas fa-search"></i>
                    <p>No dealerships found matching "${searchTerm}"</p>
                    <button class="btn btn-secondary btn-small" onclick="window.appController.clearDealershipSearch()">
                        Clear Search
                    </button>
                </div>
            `;
            dealershipList.appendChild(noResultsDiv);
        }
    }
    
    // Test function that can be called from browser console
    testDealershipSearch() {
        console.log('🧪 Testing dealership search functionality...');
        
        const searchInput = document.getElementById('dealershipSearchInput');
        const dealershipList = document.getElementById('dealershipList');
        const items = dealershipList ? dealershipList.querySelectorAll('.dealership-item') : [];
        
        console.log('Test results:', {
            searchInput: !!searchInput,
            dealershipList: !!dealershipList,
            itemCount: items.length
        });
        
        if (searchInput && items.length > 0) {
            console.log('Manual search test with "bmw":');
            searchInput.value = 'bmw';
            this.filterDealershipList();
        } else {
            console.error('Missing elements for search test');
        }
        
        return {
            searchInput: !!searchInput,
            dealershipList: !!dealershipList,
            itemCount: items.length
        };
    }
    
    async loadDealershipDefaults() {
        // Set default order types for dealerships - Mix of CAO and LIST
        this.dealershipDefaults.set('Columbia Honda', 'LIST');
        this.dealershipDefaults.set('BMW of West St. Louis', 'CAO');
        this.dealershipDefaults.set('Dave Sinclair Lincoln South', 'LIST');
        this.dealershipDefaults.set('Suntrup Ford West', 'CAO');
        this.dealershipDefaults.set('Joe Machens Toyota', 'LIST');
        this.dealershipDefaults.set('Thoroughbred Ford', 'CAO');
        this.dealershipDefaults.set('Suntrup Ford Kirkwood', 'LIST');
        this.dealershipDefaults.set('Joe Machens Hyundai', 'CAO');
        this.dealershipDefaults.set('Test Integration Dealer', 'LIST');
        
        // Set defaults for any other dealerships with a mix of both types
        if (this.dealerships) {
            this.dealerships.forEach((dealership, index) => {
                if (!this.dealershipDefaults.has(dealership.name)) {
                    // Alternate between CAO and LIST for variety
                    this.dealershipDefaults.set(dealership.name, index % 2 === 0 ? 'CAO' : 'LIST');
                }
            });
        }
        
        console.log('Dealership defaults loaded:', Array.from(this.dealershipDefaults.entries()));
    }
    
    getDealershipDefault(dealershipName) {
        if (!this.dealershipDefaults) {
            console.warn('⚠️ dealershipDefaults not initialized, using CAO default');
            return 'CAO';
        }
        const defaultType = this.dealershipDefaults.get(dealershipName) || 'CAO';
        return defaultType;
    }
    
    addDayToQueue(day) {
        const dayDealerships = this.weeklySchedule[day.toLowerCase()] || [];
        
        if (dayDealerships.length === 0) {
            this.addTerminalMessage(`No dealerships scheduled for ${day}`, 'warning');
            return;
        }
        
        let addedCount = 0;
        dayDealerships.forEach(dealershipName => {
            if (!this.processingQueue.has(dealershipName)) {
                const defaultType = this.getDealershipDefault(dealershipName);
                this.processingQueue.set(dealershipName, {
                    name: dealershipName,
                    orderType: defaultType,
                    addedBy: `${day} schedule`
                });
                addedCount++;
            }
        });
        
        this.renderQueue();
        this.addTerminalMessage(`Added ${addedCount} dealerships from ${day} schedule`, 'success');
        
        // Highlight the day button temporarily
        const dayBtn = document.querySelector(`[data-day="${day.toLowerCase()}"]`);
        if (dayBtn) {
            dayBtn.classList.add('active');
            setTimeout(() => dayBtn.classList.remove('active'), 1000);
        }
    }
    
    addDealershipToQueue(dealershipName) {
        if (this.processingQueue.has(dealershipName)) {
            this.addTerminalMessage(`${dealershipName} already in queue`, 'warning');
            return;
        }
        
        const defaultType = this.getDealershipDefault(dealershipName);
        this.processingQueue.set(dealershipName, {
            name: dealershipName,
            orderType: defaultType,
            addedBy: 'manual selection'
        });
        
        this.renderQueue();
        this.addTerminalMessage(`Added ${dealershipName} to queue`, 'success');
        
        // Highlight the dealership item temporarily
        const dealershipItems = document.querySelectorAll('.dealership-item');
        dealershipItems.forEach(item => {
            if (item.querySelector('.dealership-name').textContent === dealershipName) {
                item.classList.add('selected');
                setTimeout(() => item.classList.remove('selected'), 1000);
            }
        });
    }
    
    removeDealershipFromQueue(dealershipName) {
        if (this.processingQueue.has(dealershipName)) {
            this.processingQueue.delete(dealershipName);
            this.renderQueue();
            this.addTerminalMessage(`Removed ${dealershipName} from queue`, 'success');
        }
    }
    
    updateQueueItemOrderType(dealershipName, orderType) {
        if (this.processingQueue.has(dealershipName)) {
            const item = this.processingQueue.get(dealershipName);
            item.orderType = orderType;
            this.processingQueue.set(dealershipName, item);
            this.addTerminalMessage(`Changed ${dealershipName} to ${orderType} order`, 'info');
        }
    }
    
    renderQueue() {
        const queueItems = document.getElementById('queueItems');
        const processBtn = document.getElementById('processQueueBtn');
        
        if (!queueItems) return;
        
        if (this.processingQueue.size === 0) {
            queueItems.innerHTML = `
                <div class="empty-queue">
                    <i class="fas fa-clipboard-list"></i>
                    <p>No dealerships in queue</p>
                    <p class="help-text">Select dealerships or day buttons to add to queue</p>
                </div>
            `;
            if (processBtn) processBtn.disabled = true;
            return;
        }
        
        // Enable the process button since we have items in queue
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.style.cursor = 'pointer';
            processBtn.style.opacity = '1';
        }
        
        const queueArray = Array.from(this.processingQueue.values());
        queueItems.innerHTML = queueArray.map(item => `
            <div class="queue-item">
                <div class="queue-item-header">
                    <div class="queue-dealership-name">${item.name}</div>
                    <div class="queue-item-actions">
                        <button class="delete-btn" onclick="app.removeDealershipFromQueue('${item.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="order-type-selection">
                    <div class="order-type-option cao">
                        <input type="radio" name="orderType_${item.name.replace(/\s+/g, '_')}" 
                               value="CAO" ${item.orderType === 'CAO' ? 'checked' : ''}
                               onchange="app.updateQueueItemOrderType('${item.name}', 'CAO')">
                        <label>CAO (Automatic)</label>
                    </div>
                    <div class="order-type-option list">
                        <input type="radio" name="orderType_${item.name.replace(/\s+/g, '_')}" 
                               value="LIST" ${item.orderType === 'LIST' ? 'checked' : ''}
                               onchange="app.updateQueueItemOrderType('${item.name}', 'LIST')">
                        <label>List (VIN Entry)</label>
                    </div>
                </div>
            </div>
        `).join('');
        
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.innerHTML = `
                <i class="fas fa-play"></i>
                Process Queue (${this.processingQueue.size})
            `;
        }
    }
    
    clearQueue() {
        this.processingQueue.clear();
        this.renderQueue();
        this.addTerminalMessage('Queue cleared', 'success');
    }
    
    launchOrderWizard() {
        if (this.processingQueue.size === 0) {
            this.addTerminalMessage('No dealerships in queue to process', 'warning');
            return;
        }
        
        // Ask user which method they prefer
        const useWizard = confirm(
            'How would you like to process the queue?\n\n' +
            'OK = Open Order Processing Wizard (recommended)\n' +
            'Cancel = Process directly in this window'
        );
        
        if (useWizard) {
            this.openOrderWizard();
        } else {
            this.processQueueDirectly();
        }
    }
    
    openOrderWizard() {
        try {
            // Store queue data for wizard
            const queueData = Array.from(this.processingQueue.values());
            localStorage.setItem('orderWizardQueue', JSON.stringify(queueData));
            
            // Store testing mode setting
            const testingMode = document.getElementById('queueTestingMode')?.checked || false;
            localStorage.setItem('orderWizardTestingMode', testingMode.toString());
            
            this.addTerminalMessage('Opening Order Processing Wizard...', 'info');
            
            // Open wizard in new tab with cache-busting parameter
            const timestamp = new Date().getTime();
            const wizardWindow = window.open(`/order-wizard?v=${timestamp}`, '_blank');
            
            if (!wizardWindow) {
                this.addTerminalMessage('Popup blocked! Processing directly instead...', 'warning');
                setTimeout(() => this.processQueueDirectly(), 1000);
                return;
            }
            
            this.addTerminalMessage(`Launched order wizard for ${this.processingQueue.size} dealerships`, 'success');
            
            // Clear queue after launching wizard
            setTimeout(() => {
                this.clearQueue();
            }, 1000);
            
        } catch (error) {
            console.error('Error opening wizard:', error);
            this.addTerminalMessage('Error opening wizard, processing directly...', 'warning');
            this.processQueueDirectly();
        }
    }
    
    async processQueueDirectly() {
        try {
            const queueArray = Array.from(this.processingQueue.values());
            const testingMode = document.getElementById('queueTestingMode')?.checked || false;
            
            this.addTerminalMessage(`Processing ${queueArray.length} dealerships directly...`, 'info');
            if (testingMode) {
                this.addTerminalMessage('Testing Mode: VIN logging disabled', 'warning');
            }
            
            // Process each dealership
            for (const dealership of queueArray) {
                this.addTerminalMessage(`Processing ${dealership.name}...`, 'info');
                
                const response = await fetch('/api/orders/process-cao', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        dealerships: [dealership.name],
                        template_type: 'shortcut_pack',
                        skip_vin_logging: testingMode
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    const dealerResult = result[0];
                    
                    if (dealerResult.success) {
                        this.addTerminalMessage(`${dealership.name}: ${dealerResult.new_vehicles} new vehicles processed`, 'success');
                        if (dealerResult.download_csv) {
                            this.addTerminalMessage(`Download: <a href="/download_csv/${dealerResult.download_csv}" target="_blank" style="color: #ffc817; text-decoration: underline;">${dealerResult.download_csv}</a>`, 'success');
                        }
                    } else {
                        this.addTerminalMessage(`${dealership.name}: ${dealerResult.error}`, 'error');
                    }
                } else {
                    this.addTerminalMessage(`${dealership.name}: Failed to process (HTTP ${response.status})`, 'error');
                }
            }
            
            this.addTerminalMessage('Queue processing complete!', 'success');
            this.clearQueue();
            
        } catch (error) {
            console.error('Error processing queue:', error);
            this.addTerminalMessage(`Error processing queue: ${error.message}`, 'error');
        }
    }
    
    // =============================================================================
    // ENHANCED SCRAPER CONTROL FUNCTIONALITY
    // =============================================================================
    
    toggleDealershipSelection() {
        const panel = document.getElementById('dealershipSelectionPanel');
        const btn = document.getElementById('selectDealershipsBtn');
        
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-times"></i> Hide Selection';
            this.renderDealershipCheckboxes();
        } else {
            panel.style.display = 'none';
            btn.innerHTML = '<i class="fas fa-list-check"></i> Select Dealerships';
        }
    }
    
    renderDealershipCheckboxes(containerId = 'dealershipCheckboxGrid') {
        console.log('🔧 DEBUG: renderDealershipCheckboxes called with containerId:', containerId);
        
        const grid = document.getElementById(containerId);
        console.log('🔧 DEBUG: grid element:', grid);
        console.log('🔧 DEBUG: this.dealerships:', this.dealerships);
        console.log('🔧 DEBUG: dealerships length:', this.dealerships ? this.dealerships.length : 'null/undefined');
        
        if (!grid) {
            console.error(`❌ ${containerId} element not found!`);
            this.addScraperConsoleMessage(`ERROR: ${containerId} element not found`, 'error');
            return;
        }
        
        if (!this.dealerships) {
            console.error('❌ this.dealerships is null/undefined!');
            this.addScraperConsoleMessage('ERROR: No dealerships data available', 'error');
            return;
        }
        
        if (this.dealerships.length === 0) {
            console.warn('⚠️ this.dealerships is empty array');
            this.addScraperConsoleMessage('WARNING: No dealerships found', 'warning');
            grid.innerHTML = '<div class="no-dealerships">No dealerships available</div>';
            return;
        }
        
        console.log('✅ Rendering checkboxes for dealerships:', this.dealerships.map(d => d.name));
        this.addScraperConsoleMessage(`Rendering ${this.dealerships.length} dealership checkboxes...`, 'info');
        
        grid.innerHTML = this.dealerships.map(dealership => `
            <div class="dealership-checkbox-item">
                <label class="checkbox-label">
                    <input type="checkbox" name="scraperDealerships" value="${dealership.name}" 
                           ${this.selectedDealerships.has(dealership.name) ? 'checked' : ''}>
                    <span class="checkmark"></span>
                    <span class="dealership-label">${dealership.name}</span>
                </label>
            </div>
        `).join('');
        
        // Add event listeners to checkboxes
        grid.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedDealerships.add(e.target.value);
                } else {
                    this.selectedDealerships.delete(e.target.value);
                }
                this.updateScraperButtonState();
            });
        });
        
        console.log('✅ Dealership checkboxes rendered successfully');
        this.addScraperConsoleMessage(`✅ ${this.dealerships.length} dealership checkboxes rendered`, 'success');
    }
    
    selectAllDealerships() {
        this.dealerships.forEach(dealership => {
            this.selectedDealerships.add(dealership.name);
        });
        this.renderDealershipCheckboxes();
        this.updateScraperButtonState();
        this.addTerminalMessage('Selected all dealerships for scraping', 'info');
    }
    
    selectNoneDealerships() {
        this.selectedDealerships.clear();
        this.renderDealershipCheckboxes();
        this.updateScraperButtonState();
        this.addTerminalMessage('Cleared dealership selection', 'info');
    }
    
    updateScraperButtonState() {
        const scrapeSelectedBtn = document.getElementById('scrapeSelectedBtn');
        const selectedCount = this.selectedDealerships.size;
        
        if (scrapeSelectedBtn) {
            scrapeSelectedBtn.disabled = selectedCount === 0 || this.scraperRunning;
            scrapeSelectedBtn.innerHTML = `
                <i class="fas fa-play"></i>
                Scrape Selected (${selectedCount})
            `;
        }
    }
    
    startSelectedScraper() {
        if (this.selectedDealerships.size === 0) {
            this.addTerminalMessage('No dealerships selected for scraping', 'warning');
            return;
        }
        
        // Close the modal
        this.closeModal('dealershipSelectionModal');
        
        this.addTerminalMessage(`Starting scraper for ${this.selectedDealerships.size} selected dealerships`, 'info');
        this.startScraper(); // Use existing scraper method
    }
    
    setupQueueEventListeners() {
        // Populate queue button
        const populateBtn = document.getElementById('populateQueueBtn');
        if (populateBtn) {
            populateBtn.addEventListener('click', () => this.populateTodaysQueue());
        }
        
        // Refresh queue button
        const refreshBtn = document.getElementById('refreshQueueBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadTodaysQueue());
        }
        
        // Add custom order button
        const addOrderBtn = document.getElementById('addCustomOrderBtn');
        if (addOrderBtn) {
            addOrderBtn.addEventListener('click', () => this.addCustomOrder());
        }
    }
    
    async populateTodaysQueue() {
        try {
            const populateBtn = document.getElementById('populateQueueBtn');
            if (populateBtn) {
                populateBtn.disabled = true;
                populateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Populating...';
            }
            
            this.addTerminalMessage('Populating today\'s queue...', 'info');
            
            const response = await fetch('/api/queue/populate-today', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Added ${result.orders_added} orders to today's queue`, 'success');
                await this.loadTodaysQueue();
                await this.loadQueueSummary();
            } else {
                this.addTerminalMessage(`Failed to populate queue: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error populating queue:', error);
            this.addTerminalMessage(`Error populating queue: ${error.message}`, 'error');
        } finally {
            const populateBtn = document.getElementById('populateQueueBtn');
            if (populateBtn) {
                populateBtn.disabled = false;
                populateBtn.innerHTML = '<i class="fas fa-calendar-plus"></i> Populate Today\'s Queue';
            }
        }
    }
    
    async loadTodaysQueue() {
        try {
            const response = await fetch('/api/queue/today');
            const orders = await response.json();
            
            this.renderOrdersList(orders);
            
        } catch (error) {
            console.error('Error loading queue:', error);
            this.addTerminalMessage(`Error loading queue: ${error.message}`, 'error');
        }
    }
    
    async loadQueueSummary() {
        try {
            const response = await fetch('/api/queue/summary-today');
            const summary = await response.json();
            
            this.renderQueueSummary(summary);
            
        } catch (error) {
            console.error('Error loading queue summary:', error);
        }
    }
    
    renderQueueSummary(summary) {
        document.getElementById('totalOrders').textContent = summary.total_orders || 0;
        document.getElementById('completedOrders').textContent = summary.completed_orders || 0;
        document.getElementById('pendingOrders').textContent = summary.pending_orders || 0;
        document.getElementById('completionRate').textContent = `${summary.completion_percentage || 0}%`;
    }
    
    renderOrdersList(orders) {
        const ordersList = document.getElementById('ordersList');
        if (!ordersList) return;
        
        if (!orders || orders.length === 0) {
            ordersList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list"></i>
                    <p>No orders in queue. Click "Populate Today's Queue" to load scheduled orders.</p>
                </div>
            `;
            return;
        }
        
        ordersList.innerHTML = orders.map(order => this.renderOrderItem(order)).join('');
    }
    
    renderOrderItem(order) {
        const statusClass = order.status.toLowerCase().replace('_', '-');
        const vehicleTypesText = Array.isArray(order.vehicle_types) ? order.vehicle_types.join(', ') : 'All';
        
        return `
            <div class="order-item ${statusClass}" data-queue-id="${order.queue_id}">
                <div class="order-info">
                    <div class="order-title">${order.dealership_name}</div>
                    <div class="order-details">
                        <span>Template: ${order.template_type}</span>
                        <span>Types: ${vehicleTypesText}</span>
                        <span>Priority: ${order.priority}</span>
                    </div>
                </div>
                <div class="order-meta">
                    <span class="order-status ${statusClass}">${order.status.replace('_', ' ')}</span>
                    <div class="order-actions">
                        ${this.renderOrderActions(order)}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderOrderActions(order) {
        switch (order.status) {
            case 'pending':
                return `
                    <button class="order-btn process" onclick="app.processQueueOrder(${order.queue_id})">
                        <i class="fas fa-play"></i> Process
                    </button>
                    <button class="order-btn view" onclick="app.markAsInProgress(${order.queue_id})">
                        <i class="fas fa-clock"></i> Start
                    </button>
                `;
            case 'in_progress':
                return `
                    <button class="order-btn complete" onclick="app.markAsCompleted(${order.queue_id})">
                        <i class="fas fa-check"></i> Complete
                    </button>
                    <button class="order-btn view" onclick="window.open('/order-form', '_blank')">
                        <i class="fas fa-external-link-alt"></i> Open Tab
                    </button>
                `;
            case 'completed':
                return `
                    <button class="order-btn view" onclick="app.viewOrderResults(${order.queue_id})">
                        <i class="fas fa-eye"></i> View Results
                    </button>
                `;
            case 'failed':
                return `
                    <button class="order-btn process" onclick="app.processQueueOrder(${order.queue_id})">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                `;
            default:
                return '';
        }
    }
    
    async processQueueOrder(queueId) {
        try {
            this.addTerminalMessage(`Processing queue order ${queueId}...`, 'info');
            
            const response = await fetch(`/api/queue/process/${queueId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Order processed: ${result.vehicles_processed} vehicles, ${result.qr_codes_generated} QR codes`, 'success');
                
                // Show download link if CSV was generated
                if (result.download_csv) {
                    this.addTerminalMessage(`Download ready: <a href="/download_csv/${result.download_csv}" target="_blank" style="color: #ffc817; text-decoration: underline;">${result.download_csv}</a>`, 'success');
                }
                
                await this.loadTodaysQueue();
                await this.loadQueueSummary();
            } else {
                this.addTerminalMessage(`Failed to process order: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error processing order:', error);
            this.addTerminalMessage(`Error processing order: ${error.message}`, 'error');
        }
    }
    
    async markAsInProgress(queueId) {
        await this.updateOrderStatus(queueId, 'in_progress');
    }
    
    async markAsCompleted(queueId) {
        await this.updateOrderStatus(queueId, 'completed');
    }
    
    async updateOrderStatus(queueId, status) {
        try {
            const response = await fetch(`/api/queue/update-status/${queueId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Order ${queueId} marked as ${status}`, 'success');
                await this.loadTodaysQueue();
                await this.loadQueueSummary();
            } else {
                this.addTerminalMessage(`Failed to update order status: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error updating order status:', error);
            this.addTerminalMessage(`Error updating order status: ${error.message}`, 'error');
        }
    }
    
    async viewOrderResults(queueId) {
        // This would show detailed results of the processed order
        this.addTerminalMessage(`Viewing results for order ${queueId}`, 'info');
        // Could open a modal or redirect to results page
    }
    
    async loadDealershipOptions() {
        try {
            const response = await fetch('/api/dealerships');
            const dealerships = await response.json();
            
            const select = document.getElementById('customDealership');
            if (select) {
                select.innerHTML = '<option value="">Select Dealership</option>' +
                    dealerships.map(d => `<option value="${d.name}">${d.name}</option>`).join('');
            }
            
        } catch (error) {
            console.error('Error loading dealerships:', error);
        }
    }
    
    async addCustomOrder() {
        try {
            const dealership = document.getElementById('customDealership').value;
            const template = document.getElementById('customTemplate').value;
            const date = document.getElementById('customDate').value;
            const notes = document.getElementById('customNotes').value;
            
            // Get selected vehicle types
            const vehicleTypeCheckboxes = document.querySelectorAll('input[name="customVehicleTypes"]:checked');
            const vehicleTypes = Array.from(vehicleTypeCheckboxes).map(cb => cb.value);
            
            if (!dealership || !date) {
                this.addTerminalMessage('Please select dealership and date', 'error');
                return;
            }
            
            const response = await fetch('/api/queue/add-custom-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership_name: dealership,
                    template_type: template,
                    vehicle_types: vehicleTypes,
                    scheduled_date: date,
                    notes: notes
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage('Custom order added to queue', 'success');
                
                // Clear form
                document.getElementById('customDealership').value = '';
                document.getElementById('customNotes').value = '';
                vehicleTypeCheckboxes.forEach(cb => cb.checked = cb.value === 'new' || cb.value === 'used');
                
                // Refresh queue if it's for today
                const today = new Date().toISOString().split('T')[0];
                if (date === today) {
                    await this.loadTodaysQueue();
                    await this.loadQueueSummary();
                }
            } else {
                this.addTerminalMessage(`Failed to add custom order: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error adding custom order:', error);
            this.addTerminalMessage(`Error adding custom order: ${error.message}`, 'error');
        }
    }
    
    // =============================================================================
    // DATA SEARCH FUNCTIONALITY
    // =============================================================================
    
    async initDataSearch() {
        console.log('Initializing data search interface...');
        
        // Initialize sub-tab functionality
        this.initSubTabs();
        
        // Setup vehicle history modal
        this.setupVehicleHistoryModal();
        
        // Re-bind event listeners since elements are now available
        this.bindDataSearchEventListeners();
        
        // Load initial data
        await this.loadAvailableDealers();
        await this.loadDateRange();
        this.updateFilterVisibility();
        
        // Set default dates if needed
        this.setDefaultDateRange();
        
        // Load initial search results (recent vehicles)
        await this.executeVehicleSearch('');
        
        // Initialize VIN history viewer
        this.initVinHistory();
        
        // Load scraper history for the default scraper-view tab
        const activeSubTab = document.querySelector('.sub-tab-button.active');
        if (activeSubTab && activeSubTab.dataset.subtab === 'scraper-view') {
            this.loadScraperHistory();
            this.setupCsvImport();
        }
        
        console.log('Data search interface initialized');
    }
    
    initSubTabs() {
        // Handle sub-tab switching
        document.querySelectorAll('.sub-tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const subtab = e.currentTarget.dataset.subtab;
                this.switchSubTab(subtab);
            });
        });
    }
    
    switchSubTab(subtabName) {
        // Update sub-tab buttons
        document.querySelectorAll('.sub-tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`[data-subtab="${subtabName}"]`).classList.add('active');
        
        // Update sub-tab panels
        document.querySelectorAll('.sub-tab-panel').forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none';
        });
        const activePanel = document.getElementById(`${subtabName}-panel`);
        if (activePanel) {
            activePanel.classList.add('active');
            activePanel.style.display = 'block';
        }
        
        // Update control buttons visibility
        const exportSearchBtn = document.getElementById('exportSearchResults');
        if (subtabName === 'scraper-view') {
            exportSearchBtn.style.display = 'none';
        } else {
            exportSearchBtn.style.display = 'none';
        }
        
        // Load content for specific sub-tabs
        if (subtabName === 'vin-history') {
            this.loadDealershipVinLogs();
        } else if (subtabName === 'scraper-view') {
            this.loadScraperHistory();
            this.setupCsvImport();
        }
    }
    
    // =============================================================================
    // VEHICLE HISTORY MODAL FUNCTIONALITY
    // =============================================================================
    
    showVehicleHistory(vin, rowElement) {
        if (!vin) return;
        
        try {
            // Get vehicle info from row data
            const vehicleInfo = JSON.parse(rowElement.getAttribute('data-vehicle-info'));
            
            // Populate modal with vehicle summary
            this.populateVehicleSummary(vehicleInfo);
            
            // Show the modal
            const modal = document.getElementById('vehicleHistoryModal');
            if (modal) {
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
            
            // Load vehicle history
            this.loadVehicleHistory(vin);
            
        } catch (error) {
            console.error('Error showing vehicle history:', error);
            this.addTerminalMessage(`Error loading vehicle history: ${error.message}`, 'error');
        }
    }
    
    populateVehicleSummary(vehicleInfo) {
        // Update modal title and vehicle summary
        const title = document.getElementById('vehicleHistoryTitle');
        const modalVin = document.getElementById('modalVin');
        const modalVehicle = document.getElementById('modalVehicle');
        const modalTotalScrapes = document.getElementById('modalTotalScrapes');
        const modalCurrentLocation = document.getElementById('modalCurrentLocation');
        
        if (title) {
            title.textContent = `Vehicle History - ${vehicleInfo.vin}`;
        }
        
        if (modalVin) {
            modalVin.textContent = vehicleInfo.vin || 'N/A';
        }
        
        if (modalVehicle) {
            const vehicleDisplay = `${vehicleInfo.year || ''} ${vehicleInfo.make || ''} ${vehicleInfo.model || ''}${vehicleInfo.trim ? ' ' + vehicleInfo.trim : ''}`.trim();
            modalVehicle.textContent = vehicleDisplay || 'N/A';
        }
        
        if (modalTotalScrapes) {
            modalTotalScrapes.textContent = vehicleInfo.scrape_count || '1';
        }
        
        if (modalCurrentLocation) {
            modalCurrentLocation.textContent = vehicleInfo.location || 'N/A';
        }
    }
    
    async loadVehicleHistory(vin) {
        const scraperContainer = document.getElementById('historyTimeline');
        if (!scraperContainer) return;
        
        // Show loading state
        scraperContainer.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                Loading scrape history...
            </div>
        `;
        
        try {
            const response = await fetch(`/api/data/vehicle-history/${encodeURIComponent(vin)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderScrapesList(data.scrapes, data.first_scraped, data.total_scrapes);
            } else {
                throw new Error(data.error || 'Failed to load vehicle history');
            }
            
        } catch (error) {
            console.error('Error loading vehicle history:', error);
            scraperContainer.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading scrape history</p>
                    <p class="error-details">${error.message}</p>
                </div>
            `;
        }
    }
    
    renderScrapesList(scrapes, firstScraped, totalScrapes) {
        const scraperContainer = document.getElementById('historyTimeline');
        if (!scraperContainer) return;
        
        if (!scrapes || scrapes.length === 0) {
            scraperContainer.innerHTML = `
                <div class="no-history">
                    <i class="fas fa-spider"></i>
                    <p>No scrape history available for this vehicle</p>
                </div>
            `;
            return;
        }
        
        // Create header with first scraped info
        const firstScrapedDate = firstScraped ? new Date(firstScraped).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : 'Unknown';
        
        // Group scrapes by dealership for color coding
        const dealershipColors = {};
        const dealerships = [...new Set(scrapes.map(s => s.dealership))];
        const colors = ['#e3f2fd', '#f3e5f5', '#e8f5e8', '#fff3e0', '#fce4ec'];
        dealerships.forEach((dealer, index) => {
            dealershipColors[dealer] = colors[index % colors.length];
        });
        
        const scrapesHTML = scrapes.map((scrape, index) => {
            const scrapeDate = scrape.date ? new Date(scrape.date).toLocaleDateString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric'
            }) : 'Unknown';
            
            const scrapeTime = scrape.date ? new Date(scrape.date).toLocaleTimeString('en-US', {
                hour: '2-digit', minute: '2-digit'
            }) : '';
            
            const backgroundColor = dealershipColors[scrape.dealership] || '#f5f5f5';
            
            return `
                <div class="scrape-item" style="background-color: ${backgroundColor}">
                    <div class="scrape-header">
                        <span class="scrape-number">#${index + 1}</span>
                        <span class="scrape-date">${scrapeDate} ${scrapeTime}</span>
                        <span class="scrape-dealership">${scrape.dealership || 'Unknown'}</span>
                        <span class="scrape-price">${scrape.price_formatted || 'N/A'}</span>
                    </div>
                    <div class="scrape-details">
                        <span class="detail-item">Stock: ${scrape.stock || 'N/A'}</span>
                        <span class="detail-item">Type: ${scrape.vehicle_type || 'N/A'}</span>
                        <span class="detail-item">Mileage: ${scrape.mileage_formatted || 'N/A'}</span>
                        <span class="detail-item">Color: ${scrape.exterior_color || 'N/A'}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        scraperContainer.innerHTML = `
            <div class="scrapes-summary">
                <div class="summary-stats">
                    <span class="stat-item"><strong>Total Scrapes:</strong> ${totalScrapes}</span>
                    <span class="stat-item"><strong>First Scraped:</strong> ${firstScrapedDate}</span>
                    <span class="stat-item"><strong>Dealerships:</strong> ${dealerships.length}</span>
                </div>
            </div>
            <div class="scrapes-list">
                ${scrapesHTML}
            </div>
        `;
    }
    
    getTimelineIcon(eventType) {
        const iconMap = {
            'scrape': 'fa-spider',
            'order': 'fa-shopping-cart',
            'vin_log': 'fa-clipboard-list',
            'price_change': 'fa-dollar-sign',
            'dealer_change': 'fa-exchange-alt',
            'default': 'fa-circle'
        };
        return iconMap[eventType] || iconMap.default;
    }
    
    setupVehicleHistoryModal() {
        // Close modal handlers
        const closeBtn = document.getElementById('closeVehicleHistoryModal');
        const modal = document.getElementById('vehicleHistoryModal');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeVehicleHistoryModal());
        }
        
        if (modal) {
            // Close on backdrop click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeVehicleHistoryModal();
                }
            });
        }
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && modal.style.display === 'block') {
                this.closeVehicleHistoryModal();
            }
        });
    }
    
    closeVehicleHistoryModal() {
        const modal = document.getElementById('vehicleHistoryModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    // =============================================================================
    // INDIVIDUAL VEHICLE DATA TYPE TOGGLE FUNCTIONALITY
    // =============================================================================
    
    async toggleVehicleDataType(vin, toggleElement) {
        if (!vin) return;
        
        const isNormalized = toggleElement.checked;
        const rowElement = toggleElement.closest('tr');
        
        if (!rowElement) return;
        
        try {
            // Show loading state
            toggleElement.disabled = true;
            const originalRow = rowElement.innerHTML;
            
            // Fetch the appropriate data type for this VIN
            const dataType = isNormalized ? 'normalized' : 'raw';
            const response = await fetch(`/api/data/vehicle-single/${encodeURIComponent(vin)}?data_type=${dataType}`);
            const data = await response.json();
            
            if (data.success && data.vehicle) {
                // Update the row with new data while preserving the toggle state
                this.updateVehicleRow(rowElement, data.vehicle, isNormalized);
            } else {
                // If no normalized data exists, show message and revert toggle
                if (isNormalized && data.error && data.error.includes('No normalized data')) {
                    this.showToast('No normalized data available for this vehicle', 'warning');
                    toggleElement.checked = false;
                } else {
                    throw new Error(data.error || 'Failed to load vehicle data');
                }
            }
            
        } catch (error) {
            console.error('Error toggling vehicle data type:', error);
            this.showToast(`Error loading ${isNormalized ? 'normalized' : 'raw'} data: ${error.message}`, 'error');
            // Revert toggle state on error
            toggleElement.checked = !isNormalized;
        } finally {
            toggleElement.disabled = false;
        }
    }
    
    updateVehicleRow(rowElement, vehicleData, isNormalized) {
        // Get the current toggle element before updating
        const currentToggle = rowElement.querySelector('.toggle-input');
        const currentVin = currentToggle ? currentToggle.getAttribute('data-vin') : '';
        
        // Format the new vehicle data
        const dataSourceBadge = `<span class="data-type-badge data-type-${isNormalized ? 'normalized' : 'raw'}">${isNormalized ? 'NORMALIZED' : 'RAW'}</span>`;
        
        const scrapedTime = vehicleData.import_timestamp ? 
            new Date(vehicleData.import_timestamp).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : 'N/A';
        
        // Update vehicle info data attribute
        const vehicleInfo = JSON.stringify({
            vin: vehicleData.vin,
            year: vehicleData.year,
            make: vehicleData.make,
            model: vehicleData.model,
            trim: vehicleData.trim,
            location: vehicleData.location,
            scrape_count: vehicleData.scrape_count
        }).replace(/'/g, '&apos;');
        
        // Update row attributes
        rowElement.setAttribute('data-vehicle-info', vehicleInfo);
        
        // Update row content
        rowElement.innerHTML = `
            <td class="vin-cell">${vehicleData.vin || 'N/A'}</td>
            <td>${vehicleData.stock || 'N/A'}</td>
            <td class="dealer-cell">${vehicleData.location || 'N/A'}</td>
            <td>${vehicleData.year || 'N/A'}</td>
            <td>${vehicleData.make || 'N/A'}</td>
            <td>${vehicleData.model || 'N/A'}</td>
            <td>${vehicleData.trim || 'N/A'}</td>
            <td class="price-cell">${vehicleData.price_formatted || 'N/A'}</td>
            <td>${vehicleData.mileage_formatted || 'N/A'}</td>
            <td>${vehicleData.vehicle_type || 'N/A'}</td>
            <td class="date-cell">${scrapedTime}</td>
            <td class="scrape-count-cell">${vehicleData.scrape_count || 1}</td>
            <td class="toggle-cell" onclick="event.stopPropagation();">
                <label class="data-toggle-switch">
                    <input type="checkbox" class="toggle-input" data-vin="${currentVin}" ${isNormalized ? 'checked' : ''} onchange="app.toggleVehicleDataType('${currentVin}', this)">
                    <span class="toggle-slider">
                        <span class="toggle-label-raw">R</span>
                        <span class="toggle-label-norm">N</span>
                    </span>
                </label>
            </td>
            <td>${dataSourceBadge}</td>
        `;
    }
    
    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        // Set background color based on type
        const colors = {
            info: '#2196F3',
            success: '#4CAF50',
            warning: '#FF9800',
            error: '#F44336'
        };
        toast.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // =============================================================================
    // VIN HISTORY VIEWER FUNCTIONALITY
    // =============================================================================
    
    async initVinHistory() {
        console.log('Initializing VIN history viewer...');
        
        // VIN history properties
        this.vinHistory = {
            currentPage: 1,
            perPage: 100,
            totalCount: 0,
            results: [],
            dealerships: []
        };
        
        // Bind VIN history event listeners
        this.bindVinHistoryEventListeners();
        
        // Load initial statistics
        await this.loadVinHistoryStats();
        
        console.log('VIN history viewer initialized');
    }
    
    bindVinHistoryEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('vinHistorySearchInput');
        const searchBtn = document.getElementById('searchVinHistoryBtn');
        
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchVinHistory();
                }
            });
        }
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.searchVinHistory();
            });
        }
        
        // Filter controls
        const dealerFilter = document.getElementById('vinHistoryDealerFilter');
        const dateFromFilter = document.getElementById('vinHistoryDateFrom');
        const dateToFilter = document.getElementById('vinHistoryDateTo');
        const clearFiltersBtn = document.getElementById('clearVinHistoryFilters');
        
        if (dealerFilter) {
            dealerFilter.addEventListener('change', () => {
                this.searchVinHistory();
            });
        }
        
        if (dateFromFilter) {
            dateFromFilter.addEventListener('change', () => {
                this.searchVinHistory();
            });
        }
        
        if (dateToFilter) {
            dateToFilter.addEventListener('change', () => {
                this.searchVinHistory();
            });
        }
        
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearVinHistoryFilters();
            });
        }
        
        // Export functionality
        const exportBtn = document.getElementById('exportVinHistory');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportVinHistory();
            });
        }
        
        // Pagination
        const prevBtn = document.getElementById('vinHistoryPrevBtn');
        const nextBtn = document.getElementById('vinHistoryNextBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.vinHistory.currentPage > 1) {
                    this.vinHistory.currentPage--;
                    this.searchVinHistory();
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const totalPages = Math.ceil(this.vinHistory.totalCount / this.vinHistory.perPage);
                if (this.vinHistory.currentPage < totalPages) {
                    this.vinHistory.currentPage++;
                    this.searchVinHistory();
                }
            });
        }
    }
    
    async loadVinHistoryStats() {
        // This loads initial stats when switching to VIN history tab
        await this.searchVinHistory();
    }
    
    async searchVinHistory() {
        const container = document.getElementById('vinHistoryTableContainer');
        if (!container) return;
        
        // Show loading state
        container.innerHTML = `
            <div class="loading-search">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Searching VIN history database...</p>
            </div>
        `;
        
        // Build query parameters
        const params = new URLSearchParams();
        params.append('page', this.vinHistory.currentPage);
        params.append('per_page', this.vinHistory.perPage);
        
        // Add search query
        const searchQuery = document.getElementById('vinHistorySearchInput')?.value.trim();
        if (searchQuery) {
            params.append('query', searchQuery);
        }
        
        // Add filters
        const dealership = document.getElementById('vinHistoryDealerFilter')?.value;
        if (dealership) {
            params.append('dealership', dealership);
        }
        
        const dateFrom = document.getElementById('vinHistoryDateFrom')?.value;
        if (dateFrom) {
            params.append('date_from', dateFrom);
        }
        
        const dateTo = document.getElementById('vinHistoryDateTo')?.value;
        if (dateTo) {
            params.append('date_to', dateTo);
        }
        
        try {
            const response = await fetch(`/api/data/vin-history?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.vinHistory.results = data.data;
                this.vinHistory.totalCount = data.pagination.total;
                
                // Update statistics
                this.updateVinHistoryStats(data.statistics);
                
                // Update dealership filter if needed
                if (data.dealerships && !dealership) {
                    this.updateDealershipFilter(data.dealerships);
                }
                
                // Display results
                this.displayVinHistoryResults();
                
                // Update pagination
                this.updateVinHistoryPagination(data.pagination);
            } else {
                throw new Error(data.error || 'Failed to load VIN history');
            }
            
        } catch (error) {
            console.error('Error searching VIN history:', error);
            container.innerHTML = `
                <div class="search-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading VIN History</h3>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
    
    updateVinHistoryStats(stats) {
        if (!stats) return;
        
        document.getElementById('totalVins').textContent = stats.total_records?.toLocaleString() || '0';
        document.getElementById('uniqueVins').textContent = stats.unique_vins?.toLocaleString() || '0';
        document.getElementById('totalDealerships').textContent = stats.unique_dealerships?.toLocaleString() || '0';
        
        // Format date range
        if (stats.earliest_date && stats.latest_date) {
            const earliest = new Date(stats.earliest_date).toLocaleDateString();
            const latest = new Date(stats.latest_date).toLocaleDateString();
            document.getElementById('dateRange').textContent = `${earliest} - ${latest}`;
        } else {
            document.getElementById('dateRange').textContent = '--';
        }
    }
    
    updateDealershipFilter(dealerships) {
        const select = document.getElementById('vinHistoryDealerFilter');
        if (!select) return;
        
        // Preserve current selection
        const currentValue = select.value;
        
        // Clear and rebuild options
        select.innerHTML = '<option value="">All Dealerships</option>';
        
        dealerships.forEach(dealer => {
            const option = document.createElement('option');
            option.value = dealer.dealership_name;
            option.textContent = `${dealer.dealership_name} (${dealer.count.toLocaleString()})`;
            select.appendChild(option);
        });
        
        // Restore selection
        select.value = currentValue;
    }
    
    displayVinHistoryResults() {
        const container = document.getElementById('vinHistoryTableContainer');
        if (!container) return;
        
        if (this.vinHistory.results.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <h3>No VIN History Found</h3>
                    <p>Try adjusting your search criteria or filters</p>
                </div>
            `;
            return;
        }
        
        // Build table HTML
        let tableHTML = `
            <table class="vin-history-table">
                <thead>
                    <tr>
                        <th>VIN</th>
                        <th>Dealership</th>
                        <th>Order Date</th>
                        <th>Vehicle Info</th>
                        <th>Stock #</th>
                        <th>Status</th>
                        <th>Price</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        this.vinHistory.results.forEach(record => {
            const vehicleInfo = record.year && record.make && record.model 
                ? `${record.year} ${record.make} ${record.model} ${record.trim || ''}`.trim()
                : 'N/A';
            
            const price = record.price 
                ? `$${parseFloat(record.price).toLocaleString()}`
                : 'N/A';
            
            tableHTML += `
                <tr>
                    <td class="vin-cell">${record.vin || 'N/A'}</td>
                    <td class="dealership-cell">${record.dealership_name || 'N/A'}</td>
                    <td class="date-cell">${new Date(record.order_date).toLocaleDateString()}</td>
                    <td class="vehicle-info-cell" title="${vehicleInfo}">${vehicleInfo}</td>
                    <td>${record.stock || 'N/A'}</td>
                    <td>${record.status || record.vehicle_type || 'N/A'}</td>
                    <td class="price-cell">${price}</td>
                </tr>
            `;
        });
        
        tableHTML += `
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
        
        // Update results count
        document.getElementById('vinHistoryResultsCount').textContent = this.vinHistory.totalCount.toLocaleString();
    }
    
    updateVinHistoryPagination(pagination) {
        const pageInfo = document.getElementById('vinHistoryPageInfo');
        const prevBtn = document.getElementById('vinHistoryPrevBtn');
        const nextBtn = document.getElementById('vinHistoryNextBtn');
        const paginationContainer = document.getElementById('vinHistoryPagination');
        
        if (pagination.pages > 1) {
            paginationContainer.style.display = 'flex';
            pageInfo.textContent = `Page ${pagination.page} of ${pagination.pages}`;
            
            prevBtn.disabled = pagination.page <= 1;
            nextBtn.disabled = pagination.page >= pagination.pages;
        } else {
            paginationContainer.style.display = 'none';
        }
    }
    
    clearVinHistoryFilters() {
        document.getElementById('vinHistorySearchInput').value = '';
        document.getElementById('vinHistoryDealerFilter').value = '';
        document.getElementById('vinHistoryDateFrom').value = '';
        document.getElementById('vinHistoryDateTo').value = '';
        
        this.vinHistory.currentPage = 1;
        this.searchVinHistory();
    }
    
    async exportVinHistory() {
        // TODO: Implement VIN history export functionality
        alert('VIN history export functionality coming soon!');
    }
    
    async loadAvailableDealers() {
        try {
            const response = await fetch('/api/data/dealers');
            const data = await response.json();
            
            if (data.success) {
                this.dataSearch.availableDealers = data.dealers;
                this.populateDealerSelect();
            }
            
        } catch (error) {
            console.error('Error loading dealers:', error);
            this.addTerminalMessage('Failed to load dealer list', 'error');
        }
    }
    
    async loadDateRange() {
        try {
            const response = await fetch('/api/data/date-range');
            const data = await response.json();
            
            if (data.success && data.min_date && data.max_date) {
                // Set date input limits
                const startDate = document.getElementById('startDate');
                const endDate = document.getElementById('endDate');
                
                if (startDate) {
                    startDate.min = data.min_date;
                    startDate.max = data.max_date;
                }
                if (endDate) {
                    endDate.min = data.min_date;
                    endDate.max = data.max_date;
                }
            }
            
        } catch (error) {
            console.error('Error loading date range:', error);
        }
    }
    
    populateDealerSelect() {
        const dealerSelect = document.getElementById('dealerSelect');
        if (dealerSelect && this.dataSearch.availableDealers.length > 0) {
            dealerSelect.innerHTML = '<option value="">Select Dealer...</option>' +
                this.dataSearch.availableDealers.map(dealer => 
                    `<option value="${dealer}">${dealer}</option>`
                ).join('');
        }
    }
    
    updateFilterVisibility() {
        const filterBy = document.getElementById('filterBy');
        const dateFilter = document.getElementById('dateFilter');
        const dealerFilter = document.getElementById('dealerFilter');
        
        if (filterBy && dateFilter && dealerFilter) {
            const filterValue = filterBy.value;
            
            // Hide all filters first
            dateFilter.style.display = 'none';
            dealerFilter.style.display = 'none';
            
            // Show relevant filter
            if (filterValue === 'date') {
                dateFilter.style.display = 'flex';
            } else if (filterValue === 'dealer') {
                dealerFilter.style.display = 'flex';
            }
        }
    }
    
    setDefaultDateRange() {
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        
        if (startDate && endDate && !startDate.value && !endDate.value) {
            // Set to last 30 days by default
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);
            
            endDate.value = today.toISOString().split('T')[0];
            startDate.value = thirtyDaysAgo.toISOString().split('T')[0];
        }
    }
    
    async performVehicleSearch() {
        const searchInput = document.getElementById('vehicleSearchInput');
        const query = searchInput ? searchInput.value.trim() : '';
        
        // Reset to first page for new search
        this.dataSearch.currentPage = 0;
        
        await this.executeVehicleSearch(query);
    }
    
    async executeVehicleSearch(query = '') {
        try {
            // Show loading state
            this.showSearchLoading();
            
            // Build search parameters
            const params = this.buildSearchParams(query);
            
            // Check cache first
            const cacheKey = JSON.stringify(params);
            if (this.dataSearch.searchCache.has(cacheKey)) {
                const cachedResult = this.dataSearch.searchCache.get(cacheKey);
                this.displaySearchResults(cachedResult);
                return;
            }
            
            // Make API call
            const response = await fetch(`/api/data/search?${new URLSearchParams(params)}`);
            const data = await response.json();
            
            if (data.success) {
                // Cache the result
                this.dataSearch.searchCache.set(cacheKey, data);
                
                // Display results
                this.displaySearchResults(data);
                
                // Update terminal
                if (query) {
                    this.addTerminalMessage(`Search completed: ${data.total_count} vehicles found for "${query}"`, 'success');
                } else {
                    this.addTerminalMessage(`Data loaded: ${data.total_count} vehicles`, 'info');
                }
            } else {
                throw new Error(data.error || 'Search failed');
            }
            
        } catch (error) {
            console.error('Error performing search:', error);
            this.showSearchError(error.message);
            this.addTerminalMessage(`Search error: ${error.message}`, 'error');
        }
    }
    
    buildSearchParams(query) {
        const filterBy = document.getElementById('filterBy');
        const dataTypeRadios = document.querySelectorAll('input[name="dataType"]:checked');
        const sortBy = document.getElementById('sortBy');
        const sortOrder = document.getElementById('sortOrder');
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        const dealerSelect = document.getElementById('dealerSelect');
        
        const params = {
            query: query,
            limit: this.dataSearch.pageSize,
            offset: this.dataSearch.currentPage * this.dataSearch.pageSize
        };
        
        // Filter type
        if (filterBy) {
            params.filter_by = filterBy.value;
        }
        
        // Always use raw data type (data type filter removed)
        params.data_type = 'raw';
        
        // Sorting
        if (sortBy) {
            params.sort_by = sortBy.value;
        }
        if (sortOrder) {
            params.sort_order = sortOrder.value;
        }
        
        // Date filtering
        if (params.filter_by === 'date') {
            if (startDate && startDate.value) {
                params.start_date = startDate.value;
            }
            if (endDate && endDate.value) {
                params.end_date = endDate.value;
            }
        }
        
        // Dealer filtering
        if (params.filter_by === 'dealer' && dealerSelect && dealerSelect.value) {
            params.dealer_names = [dealerSelect.value];
        }
        
        return params;
    }
    
    showSearchLoading() {
        const container = document.getElementById('resultsTableContainer');
        if (container) {
            container.innerHTML = `
                <div class="loading-search">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Searching vehicles...</p>
                </div>
            `;
        }
        
        // Hide pagination and header
        const header = document.getElementById('resultsHeader');
        const pagination = document.getElementById('paginationControls');
        if (header) header.style.display = 'none';
        if (pagination) pagination.style.display = 'none';
    }
    
    showSearchError(message) {
        const container = document.getElementById('resultsTableContainer');
        if (container) {
            container.innerHTML = `
                <div class="search-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Search Error</h3>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="app.refreshDataSearch()">
                        <i class="fas fa-retry"></i>
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    displaySearchResults(data) {
        this.dataSearch.currentResults = data.data;
        this.dataSearch.totalCount = data.total_count;
        
        const header = document.getElementById('resultsHeader');
        const container = document.getElementById('resultsTableContainer');
        const pagination = document.getElementById('paginationControls');
        const resultsCount = document.getElementById('resultsCount');
        
        // Update results count
        if (resultsCount) {
            resultsCount.textContent = data.total_count.toLocaleString();
        }
        
        // Show header
        if (header) {
            header.style.display = 'flex';
        }
        
        // Display results table
        if (container) {
            if (data.data.length === 0) {
                container.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <h3>No Results Found</h3>
                        <p>Try adjusting your search criteria or filters</p>
                    </div>
                `;
            } else {
                container.innerHTML = this.buildResultsTable(data.data);
                // Bind filter event listeners after table is created
                this.bindHeaderFilterListeners();
                // Load dynamic filter options
                this.loadDynamicFilterOptions();
            }
        }
        
        // Update pagination
        this.updatePagination(data.page_info);
        
        // Show pagination if needed
        if (pagination && data.total_count > this.dataSearch.pageSize) {
            pagination.style.display = 'flex';
        }
    }
    
    // =============================================================================
    // DYNAMIC FILTERING SYSTEM
    // =============================================================================
    
    bindHeaderFilterListeners() {
        const headerFilters = document.querySelectorAll('.header-filter');
        
        headerFilters.forEach(select => {
            select.addEventListener('change', async (e) => {
                const field = e.target.getAttribute('data-field');
                const value = e.target.value;
                
                // Update active filters
                this.dataSearch.activeFilters[field] = value;
                
                // Update filter visual state
                this.updateFilterActiveState(field, value);
                
                // Reset to first page
                this.dataSearch.currentPage = 0;
                
                // Trigger new search with filters
                await this.executeVehicleSearchWithFilters();
            });
        });
    }
    
    updateFilterActiveState(field, value) {
        const headerElement = document.querySelector(`[data-field="${field}"]`);
        if (headerElement) {
            if (value) {
                headerElement.classList.add('has-active-filter');
            } else {
                headerElement.classList.remove('has-active-filter');
            }
        }
    }
    
    async loadDynamicFilterOptions() {
        try {
            // Build parameters for filter options API
            const searchInput = document.getElementById('vehicleSearchInput');
            const query = searchInput ? searchInput.value.trim() : '';
            
            const params = {
                query: query,
                filter_location: this.dataSearch.activeFilters.location,
                filter_year: this.dataSearch.activeFilters.year,
                filter_make: this.dataSearch.activeFilters.make,
                filter_model: this.dataSearch.activeFilters.model,
                filter_vehicle_type: this.dataSearch.activeFilters.vehicle_type,
                filter_import_date: this.dataSearch.activeFilters.import_date
            };
            
            const response = await fetch(`/api/data/filter-options?${new URLSearchParams(params)}`);
            const data = await response.json();
            
            if (data.success) {
                this.dataSearch.filterOptions = data.filters;
                this.populateFilterDropdowns();
            }
            
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }
    
    populateFilterDropdowns() {
        const filterMappings = {
            'location': 'locations',
            'year': 'years', 
            'make': 'makes',
            'model': 'models',
            'vehicle_type': 'vehicle_types',
            'import_timestamp': 'import_dates'
        };
        
        for (const [fieldName, optionsKey] of Object.entries(filterMappings)) {
            const select = document.querySelector(`.header-filter[data-field="${fieldName}"]`);
            if (select && this.dataSearch.filterOptions[optionsKey]) {
                // Store current value
                const currentValue = select.value;
                
                // Clear existing options except the "All" option
                select.innerHTML = `<option value="">${select.options[0].text}</option>`;
                
                // Add new options
                this.dataSearch.filterOptions[optionsKey].forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                    select.appendChild(optionElement);
                });
                
                // Restore value if it still exists
                if (currentValue) {
                    select.value = currentValue;
                }
            }
        }
    }
    
    async executeVehicleSearchWithFilters() {
        try {
            // Show loading state
            this.showSearchLoading();
            
            // Build search parameters including filters
            const searchInput = document.getElementById('vehicleSearchInput');
            const query = searchInput ? searchInput.value.trim() : '';
            const params = this.buildSearchParamsWithFilters(query);
            
            // Check cache first
            const cacheKey = JSON.stringify(params);
            if (this.dataSearch.searchCache.has(cacheKey)) {
                const cachedResult = this.dataSearch.searchCache.get(cacheKey);
                this.displaySearchResults(cachedResult);
                return;
            }
            
            // Make API call
            const response = await fetch(`/api/data/search?${new URLSearchParams(params)}`);
            const data = await response.json();
            
            if (data.success) {
                // Cache the result
                this.dataSearch.searchCache.set(cacheKey, data);
                
                // Display results
                this.displaySearchResults(data);
                
                // Update terminal
                const filterCount = Object.values(this.dataSearch.activeFilters).filter(v => v).length;
                const filterText = filterCount > 0 ? ` (${filterCount} filters active)` : '';
                
                if (query) {
                    this.addTerminalMessage(`Search completed: ${data.total_count} vehicles found for "${query}"${filterText}`, 'success');
                } else {
                    this.addTerminalMessage(`Data loaded: ${data.total_count} vehicles${filterText}`, 'info');
                }
            } else {
                throw new Error(data.error || 'Search failed');
            }
            
        } catch (error) {
            console.error('Error performing filtered search:', error);
            this.showSearchError(error.message);
            this.addTerminalMessage(`Search error: ${error.message}`, 'error');
        }
    }
    
    buildSearchParamsWithFilters(query) {
        const filterBy = document.getElementById('filterBy');
        const dataTypeRadios = document.querySelectorAll('input[name="dataType"]:checked');
        const sortBy = document.getElementById('sortBy');
        const sortOrder = document.getElementById('sortOrder');
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        const dealerSelect = document.getElementById('dealerSelect');
        
        const params = {
            query: query,
            limit: this.dataSearch.pageSize,
            offset: this.dataSearch.currentPage * this.dataSearch.pageSize
        };
        
        // Add standard search parameters
        if (filterBy) {
            params.filter_by = filterBy.value;
        }
        
        // Always use raw data type (data type filter removed)
        params.data_type = 'raw';
        
        if (sortBy) {
            params.sort_by = sortBy.value;
        }
        if (sortOrder) {
            params.sort_order = sortOrder.value;
        }
        
        // Date filtering from the old system
        if (params.filter_by === 'date') {
            if (startDate && startDate.value) {
                params.start_date = startDate.value;
            }
            if (endDate && endDate.value) {
                params.end_date = endDate.value;
            }
        }
        
        // Dealer filtering from the old system
        if (params.filter_by === 'dealer' && dealerSelect && dealerSelect.value) {
            params.dealer_names = [dealerSelect.value];
        }
        
        // Add header filters
        for (const [field, value] of Object.entries(this.dataSearch.activeFilters)) {
            if (value) {
                params[`header_filter_${field}`] = value;
            }
        }
        
        return params;
    }
    
    buildResultsTable(results) {
        return `
            <table class="results-table">
                <thead>
                    <tr>
                        <th class="sortable" onclick="app.sortBy('vin')">VIN</th>
                        <th class="sortable" onclick="app.sortBy('stock')">Stock #</th>
                        <th class="filterable-header" data-field="location">
                            <div class="header-content">
                                <span>Dealer</span>
                                <div class="filter-dropdown" id="dealershipFilter">
                                    <select class="header-filter" data-field="location">
                                        <option value="">All Dealers</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="filterable-header" data-field="year">
                            <div class="header-content">
                                <span>Year</span>
                                <div class="filter-dropdown" id="yearFilter">
                                    <select class="header-filter" data-field="year">
                                        <option value="">All Years</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="filterable-header" data-field="make">
                            <div class="header-content">
                                <span>Make</span>
                                <div class="filter-dropdown" id="makeFilter">
                                    <select class="header-filter" data-field="make">
                                        <option value="">All Makes</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="filterable-header" data-field="model">
                            <div class="header-content">
                                <span>Model</span>
                                <div class="filter-dropdown" id="modelFilter">
                                    <select class="header-filter" data-field="model">
                                        <option value="">All Models</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="sortable" onclick="app.sortBy('trim')">Trim</th>
                        <th class="sortable" onclick="app.sortBy('price')">Price</th>
                        <th class="sortable" onclick="app.sortBy('mileage')">Mileage</th>
                        <th class="filterable-header" data-field="vehicle_type">
                            <div class="header-content">
                                <span>Type</span>
                                <div class="filter-dropdown" id="typeFilter">
                                    <select class="header-filter" data-field="vehicle_type">
                                        <option value="">All Types</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="filterable-header" data-field="time_scraped">
                            <div class="header-content">
                                <span>Last Scraped</span>
                                <div class="filter-dropdown" id="timeScrapedFilter">
                                    <select class="header-filter" data-field="time_scraped">
                                        <option value="">All Times</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="sortable" onclick="app.sortBy('first_scraped')">First Scraped</th>
                        <th class="sortable" onclick="app.sortBy('scrape_count')">Scrapes</th>
                        <th class="toggle-header">Raw/Norm</th>
                        <th>Data Source</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map(vehicle => this.buildVehicleRow(vehicle)).join('')}
                </tbody>
            </table>
        `;
    }
    
    buildVehicleRow(vehicle) {
        const dataSourceBadge = vehicle.data_source ? 
            `<span class="data-type-badge data-type-${vehicle.data_source}">${vehicle.data_source.toUpperCase()}</span>` : '';
        
        // Format the scraped time (use time_scraped if available, fallback to import_timestamp)
        const timeField = vehicle.time_scraped || vehicle.import_timestamp;
        const scrapedTime = timeField ? 
            new Date(timeField).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : 'N/A';
        
        // Format the first scraped time
        const firstScrapedTime = vehicle.first_scraped ? 
            new Date(vehicle.first_scraped).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : 'N/A';
        
        return `
            <tr class="vehicle-row" data-vin="${vehicle.vin}" data-vehicle-info='${JSON.stringify({
                vin: vehicle.vin,
                year: vehicle.year,
                make: vehicle.make,
                model: vehicle.model,
                trim: vehicle.trim,
                location: vehicle.location,
                scrape_count: vehicle.scrape_count
            }).replace(/'/g, '&apos;')}' onclick="app.showVehicleHistory('${vehicle.vin}', this)">
                <td class="vin-cell">${vehicle.vin || 'N/A'}</td>
                <td>${vehicle.stock || 'N/A'}</td>
                <td class="dealer-cell">${vehicle.location || 'N/A'}</td>
                <td>${vehicle.year || 'N/A'}</td>
                <td>${vehicle.make || 'N/A'}</td>
                <td>${vehicle.model || 'N/A'}</td>
                <td>${vehicle.trim || 'N/A'}</td>
                <td class="price-cell">${vehicle.price_formatted || 'N/A'}</td>
                <td>${vehicle.mileage_formatted || 'N/A'}</td>
                <td>${vehicle.vehicle_type || 'N/A'}</td>
                <td class="date-cell">${scrapedTime}</td>
                <td class="date-cell">${firstScrapedTime}</td>
                <td class="scrape-count-cell">${vehicle.scrape_count || 1}</td>
                <td class="toggle-cell" onclick="event.stopPropagation();">
                    <label class="data-toggle-switch">
                        <input type="checkbox" class="toggle-input" data-vin="${vehicle.vin}" onchange="app.toggleVehicleDataType('${vehicle.vin}', this)">
                        <span class="toggle-slider">
                            <span class="toggle-label-raw">R</span>
                            <span class="toggle-label-norm">N</span>
                        </span>
                    </label>
                </td>
                <td>${dataSourceBadge}</td>
            </tr>
        `;
    }
    
    updatePagination(pageInfo) {
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const pageInfoEl = document.getElementById('pageInfo');
        
        if (prevBtn) {
            prevBtn.disabled = this.dataSearch.currentPage === 0;
        }
        
        if (nextBtn) {
            nextBtn.disabled = !pageInfo.has_more;
        }
        
        if (pageInfoEl) {
            const currentPageNum = this.dataSearch.currentPage + 1;
            const totalPages = pageInfo.total_pages || 1;
            pageInfoEl.textContent = `Page ${currentPageNum} of ${totalPages}`;
        }
    }
    
    async goToPreviousPage() {
        if (this.dataSearch.currentPage > 0) {
            this.dataSearch.currentPage--;
            await this.executeVehicleSearch(document.getElementById('vehicleSearchInput').value.trim());
        }
    }
    
    async goToNextPage() {
        // Check if there are more pages available
        const nextBtn = document.getElementById('nextPageBtn');
        if (nextBtn && nextBtn.disabled) {
            return; // Don't go to next page if button is disabled
        }
        
        this.dataSearch.currentPage++;
        await this.executeVehicleSearch(document.getElementById('vehicleSearchInput').value.trim());
    }
    
    async sortBy(field) {
        const sortBySelect = document.getElementById('sortBy');
        const sortOrderSelect = document.getElementById('sortOrder');
        
        if (sortBySelect) {
            // If already sorting by this field, toggle order
            if (sortBySelect.value === field) {
                const currentOrder = sortOrderSelect.value;
                sortOrderSelect.value = currentOrder === 'asc' ? 'desc' : 'asc';
            } else {
                sortBySelect.value = field;
                sortOrderSelect.value = 'asc';
            }
            
            // Reset to first page and search
            this.dataSearch.currentPage = 0;
            await this.executeVehicleSearch(document.getElementById('vehicleSearchInput').value.trim());
        }
    }
    
    async exportSearchResults() {
        try {
            const searchInput = document.getElementById('vehicleSearchInput');
            const query = searchInput ? searchInput.value.trim() : '';
            
            // Build export parameters (same as search but without pagination)
            const params = this.buildSearchParams(query);
            delete params.limit;
            delete params.offset;
            
            this.addTerminalMessage('Preparing export...', 'info');
            
            const response = await fetch('/api/data/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addTerminalMessage(`Export ready: ${data.row_count} vehicles exported to ${data.filename}`, 'success');
                
                // Download the file
                const link = document.createElement('a');
                link.href = data.download_url;
                link.download = data.filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                throw new Error(data.error || 'Export failed');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.addTerminalMessage(`Export error: ${error.message}`, 'error');
        }
    }
    
    async refreshDataSearch() {
        // Clear cache
        this.dataSearch.searchCache.clear();
        
        // Reload dealers and date range
        await this.loadAvailableDealers();
        await this.loadDateRange();
        
        // Re-run current search
        const searchInput = document.getElementById('vehicleSearchInput');
        const query = searchInput ? searchInput.value.trim() : '';
        await this.executeVehicleSearch(query);
        
        this.addTerminalMessage('Data search refreshed', 'success');
    }
    
    clearTerminalStatus() {
        const terminalContent = document.getElementById('terminalOutputStatus');
        if (terminalContent) {
            terminalContent.innerHTML = `
                <div class="terminal-line">
                    <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                    <span class="message">Console cleared</span>
                </div>
            `;
        }
    }
    
    // Update the addTerminalMessage method to also update the status console
    addTerminalMessage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const terminalLine = `
            <div class="terminal-line">
                <span class="timestamp">[${timestamp}]</span>
                <span class="message ${type}">${message}</span>
            </div>
        `;
        
        // Add to main terminal (if it exists)
        const terminalOutput = document.getElementById('terminalOutput');
        if (terminalOutput) {
            terminalOutput.insertAdjacentHTML('beforeend', terminalLine);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
        
        // Also add to status console
        const terminalOutputStatus = document.getElementById('terminalOutputStatus');
        if (terminalOutputStatus) {
            terminalOutputStatus.insertAdjacentHTML('beforeend', terminalLine);
            terminalOutputStatus.scrollTop = terminalOutputStatus.scrollHeight;
        }
        
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    // =============================================================================
    // DEALERSHIP VIN LOG FUNCTIONALITY
    // =============================================================================
    
    async loadDealershipVinLogs() {
        try {
            const response = await fetch('/api/dealership-vin-logs');
            const data = await response.json();
            
            if (data.success) {
                this.renderDealershipCards(data.vin_logs);
            } else {
                console.error('Failed to load dealership VIN logs:', data.error);
                this.showError('Failed to load dealership VIN logs');
            }
        } catch (error) {
            console.error('Error loading dealership VIN logs:', error);
            this.showError('Error loading dealership VIN logs');
        }
    }
    
    renderDealershipCards(dealerships) {
        const container = document.getElementById('dealershipCardsGrid');
        
        if (!dealerships || dealerships.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <h3>No VIN Log Data Found</h3>
                    <p>No dealership VIN logs are available.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = dealerships.map(dealer => `
            <div class="dealership-card" data-dealer="${dealer.dealership_name}">
                <div class="dealership-card-header">
                    <h3 class="dealership-name">${this.formatDealershipName(dealer.dealership_name)}</h3>
                    <i class="fas fa-building dealership-icon"></i>
                </div>
                
                <div class="dealership-stats">
                    <div class="stat-item">
                        <div class="stat-value">${dealer.vin_count || 0}</div>
                        <div class="stat-label">Total VINs</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Baseline Data</div>
                    </div>
                </div>
                
                <div class="table-info">
                    <div class="table-name">
                        <i class="fas fa-database"></i>
                        <span>${dealer.table_name}</span>
                    </div>
                </div>
                
                <div class="dealership-actions">
                    <button class="btn-view-vin-log" onclick="app.openVinLogModal('${dealer.dealership_name}')">
                        <i class="fas fa-eye"></i>
                        View VIN Log
                    </button>
                </div>
            </div>
        `).join('');

        // Setup search functionality
        this.setupDealershipSearch(dealerships);
    }
    
    setupDealershipSearch(dealerships) {
        const searchInput = document.getElementById('dealershipSearchInput');
        const searchBtn = document.getElementById('searchDealershipsBtn');
        
        if (!searchInput) return;
        
        const performSearch = () => {
            const query = searchInput.value.toLowerCase().trim();
            
            if (!query) {
                this.renderDealershipCards(dealerships);
                return;
            }
            
            const filtered = dealerships.filter(dealer => 
                dealer.dealership_name.toLowerCase().includes(query)
            );
            
            this.renderDealershipCards(filtered);
        };
        
        searchInput.addEventListener('input', performSearch);
        if (searchBtn) {
            searchBtn.addEventListener('click', performSearch);
        }
    }
    
    async openVinLogModal(dealershipName) {
        const modal = document.getElementById('vinLogModal');
        const modalTitle = document.getElementById('vinLogModalTitle');
        
        if (!modal || !modalTitle) return;
        
        modalTitle.textContent = `${this.formatDealershipName(dealershipName)} - VIN History`;
        modal.style.display = 'flex';
        
        // Initialize modal state
        this.currentVinLogData = null;
        this.currentFilteredData = null;
        this.currentOrderFilter = null;
        this.currentDealership = dealershipName;
        
        // Setup modal event listeners
        this.setupVinLogModalEvents();
        this.setupExportHandlers();
        
        // Load VIN data for this dealership
        await this.loadVinLogData(dealershipName);
    }
    
    setupVinLogModalEvents() {
        const closeBtn = document.getElementById('closeVinLogModal');
        const closeBtn2 = document.getElementById('closeVinLogModalBtn');
        const modal = document.getElementById('vinLogModal');
        const searchInput = document.getElementById('vinLogSearch');
        const searchBtn = document.getElementById('vinLogSearchBtn');
        
        if (closeBtn && !closeBtn.hasEventListener) {
            closeBtn.addEventListener('click', () => this.closeVinLogModal());
            closeBtn.hasEventListener = true;
        }
        
        if (closeBtn2 && !closeBtn2.hasEventListener) {
            closeBtn2.addEventListener('click', () => this.closeVinLogModal());
            closeBtn2.hasEventListener = true;
        }
        
        if (modal && !modal.hasEventListener) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeVinLogModal();
                }
            });
            modal.hasEventListener = true;
        }
        
        // Setup search functionality
        if (searchInput && !searchInput.hasEventListener) {
            searchInput.addEventListener('input', () => this.filterVinLogData());
            searchInput.hasEventListener = true;
        }
        
        if (searchBtn && !searchBtn.hasEventListener) {
            searchBtn.addEventListener('click', () => this.filterVinLogData());
            searchBtn.hasEventListener = true;
        }
        
        // Update VIN Log button
        const updateVinLogBtn = document.getElementById('updateVinLogBtn');
        if (updateVinLogBtn && !updateVinLogBtn.hasEventListener) {
            updateVinLogBtn.addEventListener('click', () => this.openVinLogUpdateModal());
            updateVinLogBtn.hasEventListener = true;
        }
    }
    
    closeVinLogModal() {
        const modal = document.getElementById('vinLogModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    async loadVinLogData(dealershipName) {
        try {
            console.log('Loading VIN data for:', dealershipName);
            const response = await fetch(`/api/dealership-vin-logs/${encodeURIComponent(dealershipName)}?limit=10000`);
            const data = await response.json();
            console.log('API Response:', { 
                success: data.success, 
                historyCount: data.history?.length || 0,
                statsTotal: data.stats?.total_vins || 0,
                firstFewDates: data.history?.slice(0, 5).map(h => h.processed_date) || []
            });
            
            if (data.success) {
                // Store the full data for filtering
                this.currentVinLogData = data;
                this.currentFilteredData = data.history || [];
                this.currentOrderFilter = null;
                
                // Clear search input
                const searchInput = document.getElementById('vinLogSearch');
                if (searchInput) searchInput.value = '';
                
                this.renderVinLogModal(data);
            } else {
                console.error('Failed to load VIN log data:', data.error);
                this.showVinLogError('Failed to load VIN log data');
            }
        } catch (error) {
            console.error('Error loading VIN log data:', error);
            this.showVinLogError('Error loading VIN log data');
        }
    }
    
    renderVinLogModal(data = null) {
        // Use stored filtered data if no data provided
        const displayData = data || this.currentVinLogData;
        const historyData = this.currentFilteredData || displayData?.history || [];
        
        // Update stats based on filtered data
        const totalVins = document.getElementById('modalTotalVins');
        const orderNumbers = document.getElementById('modalOrderNumbers');
        const dateRange = document.getElementById('modalDateRange');
        
        if (totalVins) totalVins.textContent = historyData.length;
        
        // Calculate unique orders from filtered data
        const uniqueOrders = [...new Set(historyData.map(record => record.order_number).filter(Boolean))];
        if (orderNumbers) orderNumbers.textContent = uniqueOrders.length;
        
        if (dateRange && historyData.length > 0) {
            const dates = historyData.map(record => record.processed_date).filter(Boolean);
            if (dates.length > 0) {
                const sortedDates = dates.sort();
                dateRange.textContent = `${this.formatDate(sortedDates[0])} - ${this.formatDate(sortedDates[sortedDates.length - 1])}`;
            } else {
                dateRange.textContent = 'No date range';
            }
        }
        
        // Update modal title to show filter status
        const modalTitle = document.getElementById('vinLogModalTitle');
        if (modalTitle && this.currentDealership) {
            let title = `${this.formatDealershipName(this.currentDealership)} - VIN History`;
            if (this.currentOrderFilter) {
                title += ` - Order: ${this.currentOrderFilter}`;
            }
            modalTitle.textContent = title;
        }
        
        // Render table
        const tableContainer = document.getElementById('vinLogTableContainer');
        if (!tableContainer) return;
        
        if (!historyData || historyData.length === 0) {
            tableContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No VIN History Found</h3>
                    <p>No VIN records match your current filter criteria.</p>
                    ${this.currentOrderFilter ? `
                        <button class="btn btn-secondary" onclick="app.clearOrderFilter()">
                            <i class="fas fa-times"></i>
                            Clear Filter
                        </button>
                    ` : ''}
                </div>
            `;
            return;
        }
        
        tableContainer.innerHTML = `
            <table class="vin-log-table">
                <thead>
                    <tr>
                        <th>VIN</th>
                        <th>Order Number</th>
                        <th>Processed Date</th>
                        <th>Order Type</th>
                    </tr>
                </thead>
                <tbody>
                    ${historyData.map(record => `
                        <tr>
                            <td><span class="vin-number">${record.vin}</span></td>
                            <td>
                                <span class="order-number clickable ${record.order_type?.toLowerCase() === 'baseline' ? 'baseline' : ''}" 
                                      onclick="app.filterByOrder('${record.order_number || ''}')">
                                    ${record.order_number || 'N/A'}
                                </span>
                            </td>
                            <td>${record.processed_date ? this.formatDate(record.processed_date) : 'N/A'}</td>
                            <td>${record.order_type || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    showVinLogError(message) {
        const tableContainer = document.getElementById('vinLogTableContainer');
        if (tableContainer) {
            tableContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Data</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    getDateClass(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const daysDiff = (now - date) / (1000 * 60 * 60 * 24);
        
        if (daysDiff < 7) return 'recent';
        if (daysDiff > 30) return 'old';
        return '';
    }
    
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }
    
    formatDealershipName(name) {
        if (!name) return 'Unknown Dealership';
        
        // Convert from lowercase with spaces to title case
        return name.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }
    
    // VIN Log Filtering Functions
    filterVinLogData() {
        if (!this.currentVinLogData || !this.currentVinLogData.history) return;
        
        const searchInput = document.getElementById('vinLogSearch');
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        
        let filteredData = this.currentVinLogData.history;
        
        // Apply order filter if active
        if (this.currentOrderFilter) {
            filteredData = filteredData.filter(record => 
                record.order_number === this.currentOrderFilter
            );
        }
        
        // Apply search filter
        if (searchTerm) {
            filteredData = filteredData.filter(record => {
                const vin = (record.vin || '').toLowerCase();
                const orderNumber = (record.order_number || '').toLowerCase();
                const orderType = (record.order_type || '').toLowerCase();
                
                return vin.includes(searchTerm) || 
                       orderNumber.includes(searchTerm) || 
                       orderType.includes(searchTerm);
            });
        }
        
        this.currentFilteredData = filteredData;
        this.renderVinLogModal();
    }
    
    filterByOrder(orderNumber) {
        if (!orderNumber || orderNumber === 'N/A') return;
        
        this.currentOrderFilter = orderNumber;
        
        // Clear search input when filtering by order
        const searchInput = document.getElementById('vinLogSearch');
        if (searchInput) searchInput.value = '';
        
        this.filterVinLogData();
    }
    
    clearOrderFilter() {
        this.currentOrderFilter = null;
        this.filterVinLogData();
    }

    // =============================================================================
    // SCRAPER VIEW FUNCTIONALITY
    // =============================================================================
    
    async loadScraperHistory() {
        try {
            const response = await fetch('/api/scraper-imports');
            const data = await response.json();
            
            if (data.success) {
                this.renderScraperHistoryTable(data.imports);
            } else {
                console.error('Failed to load scraper history:', data.error);
                this.showScraperHistoryError('Failed to load scraper history');
            }
        } catch (error) {
            console.error('Error loading scraper history:', error);
            this.showScraperHistoryError('Error loading scraper history');
        }
    }
    
    renderScraperHistoryTable(imports) {
        const container = document.getElementById('scraperTableContainer');
        
        if (!imports || imports.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <h3>No Import History Found</h3>
                    <p>No scraper imports are available.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <table class="scraper-history-table">
                <thead>
                    <tr>
                        <th>Import ID</th>
                        <th>Date</th>
                        <th>Source</th>
                        <th>Vehicles</th>
                        <th>Dealerships</th>
                        <th>Status</th>
                        <th>File</th>
                    </tr>
                </thead>
                <tbody>
                    ${imports.map(import_ => `
                        <tr onclick="app.openScraperDataModal(${import_.import_id})" data-import-id="${import_.import_id}">
                            <td><strong>#${import_.import_id}</strong></td>
                            <td>${this.formatDate(import_.import_date)}</td>
                            <td>${import_.import_source || 'Unknown'}</td>
                            <td>${import_.total_vehicles || import_.actual_vehicles || 0}</td>
                            <td>
                                <span class="dealership-count clickable" 
                                      onclick="event.stopPropagation(); app.showImportDealerships(${import_.import_id})"
                                      style="cursor: pointer; color: var(--primary-blue); text-decoration: underline;"
                                      title="Click to view dealerships">
                                    ${import_.dealerships_count || import_.actual_dealerships || 0}
                                </span>
                            </td>
                            <td>
                                <span class="import-status-badge ${import_.status || 'unknown'}" 
                                      onclick="event.stopPropagation(); app.toggleScraperStatus(${import_.import_id}, '${import_.status || 'archived'}')"
                                      style="cursor: pointer;" 
                                      title="Click to toggle status">
                                    ${import_.status || 'Unknown'}
                                </span>
                            </td>
                            <td>${import_.file_name || '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // Setup refresh button
        const refreshBtn = document.getElementById('refreshScraperHistory');
        if (refreshBtn && !refreshBtn.hasEventListener) {
            refreshBtn.addEventListener('click', () => this.loadScraperHistory());
            refreshBtn.hasEventListener = true;
        }
    }
    
    showScraperHistoryError(message) {
        const container = document.getElementById('scraperTableContainer');
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error Loading Data</h3>
                <p>${message}</p>
                <button class="btn btn-secondary" onclick="app.loadScraperHistory()">
                    <i class="fas fa-sync"></i>
                    Try Again
                </button>
            </div>
        `;
    }
    
    async toggleScraperStatus(importId, currentStatus) {
        const newStatus = currentStatus === 'active' ? 'archived' : 'active';
        
        // Show confirmation dialog
        const message = newStatus === 'active' 
            ? 'This will set this import as the active dataset for order processing. The currently active dataset will be archived. Continue?'
            : 'This will archive this import. Continue?';
            
        if (!confirm(message)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/scraper-imports/${importId}/toggle-status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    new_status: newStatus
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Import #${importId} status changed to ${newStatus}`, 'success');
                // Reload the scraper history to show updated status
                this.loadScraperHistory();
            } else {
                this.addTerminalMessage(`Failed to change status: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error toggling scraper status:', error);
            this.addTerminalMessage(`Error changing status: ${error.message}`, 'error');
        }
    }
    
    async showImportDealerships(importId) {
        const modal = document.getElementById('importDealershipsModal');
        const modalTitle = document.getElementById('importDealershipsTitle');
        const listContainer = document.getElementById('importDealershipsList');
        
        if (!modal || !modalTitle) return;
        
        // Show modal
        modal.style.display = 'flex';
        modalTitle.textContent = `Dealerships in Import #${importId}`;
        
        // Show loading
        listContainer.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                Loading dealerships...
            </div>
        `;
        
        try {
            // Fetch dealerships for this import
            const response = await fetch(`/api/scraper-imports/${importId}/dealerships`);
            const data = await response.json();
            
            if (data.success && data.dealerships) {
                this.renderImportDealerships(data.dealerships, importId);
            } else {
                listContainer.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load dealerships</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading dealerships:', error);
            listContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading dealerships</p>
                </div>
            `;
        }
        
        // Setup close handlers
        this.setupImportDealershipsModalEvents();
    }
    
    renderImportDealerships(dealerships, importId) {
        const container = document.getElementById('importDealershipsList');
        
        if (!dealerships || dealerships.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-building"></i>
                    <p>No dealerships found in this import</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="dealerships-grid">
                ${dealerships.map(dealer => `
                    <div class="dealership-card" 
                         onclick="app.showDealershipVehicles(${importId}, '${dealer.name}')"
                         title="Click to view vehicles">
                        <div class="dealership-card-header">
                            <i class="fas fa-building"></i>
                            <h4>${dealer.name}</h4>
                        </div>
                        <div class="dealership-card-stats">
                            <div class="stat">
                                <span class="stat-value">${dealer.vehicle_count || 0}</span>
                                <span class="stat-label">Vehicles</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">${dealer.new_count || 0}</span>
                                <span class="stat-label">New</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">${dealer.used_count || 0}</span>
                                <span class="stat-label">Used</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    setupImportDealershipsModalEvents() {
        const modal = document.getElementById('importDealershipsModal');
        const closeBtn = document.getElementById('closeImportDealershipsModal');
        
        if (closeBtn && !closeBtn.hasEventListener) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
            closeBtn.hasEventListener = true;
        }
        
        if (modal && !modal.hasModalEventListener) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
            modal.hasModalEventListener = true;
        }
    }
    
    async showDealershipVehicles(importId, dealershipName) {
        // Close the dealerships modal
        document.getElementById('importDealershipsModal').style.display = 'none';
        
        // Open the scraper data modal with dealership filter
        await this.openScraperDataModal(importId);
        
        // Apply dealership filter
        setTimeout(() => {
            this.setDealershipFilter(dealershipName);
        }, 500);
    }
    
    setDealershipFilter(dealershipName) {
        // Show filter tag
        const filterTags = document.getElementById('scraperDataFilterTags');
        const filterNameSpan = document.getElementById('dealershipFilterName');
        const searchInput = document.getElementById('scraperDataSearch');
        
        if (filterTags && filterNameSpan) {
            filterTags.style.display = 'block';
            filterNameSpan.textContent = dealershipName;
        }
        
        // Apply search filter
        if (searchInput) {
            searchInput.value = dealershipName;
            this.filterScraperData();
        }
    }
    
    clearDealershipFilter() {
        // Hide filter tag
        const filterTags = document.getElementById('scraperDataFilterTags');
        const searchInput = document.getElementById('scraperDataSearch');
        
        if (filterTags) {
            filterTags.style.display = 'none';
        }
        
        // Clear search
        if (searchInput) {
            searchInput.value = '';
            this.filterScraperData();
        }
    }
    
    async openScraperDataModal(importId) {
        const modal = document.getElementById('scraperDataModal');
        const modalTitle = document.getElementById('scraperDataModalTitle');
        
        if (!modal || !modalTitle) return;
        
        modalTitle.textContent = `Scraper Data - Import #${importId}`;
        modal.style.display = 'flex';
        
        // Initialize modal state
        this.currentScraperData = null;
        this.currentFilteredScraperData = null;
        this.currentImportId = importId;
        
        // Setup modal event listeners
        this.setupScraperDataModalEvents();
        
        // Load vehicle data for this import
        await this.loadScraperData(importId);
    }
    
    setupScraperDataModalEvents() {
        const closeBtn = document.getElementById('closeScraperDataModal');
        const closeBtn2 = document.getElementById('closeScraperDataModalBtn');
        const modal = document.getElementById('scraperDataModal');
        const searchInput = document.getElementById('scraperDataSearch');
        const searchBtn = document.getElementById('scraperDataSearchBtn');
        
        if (closeBtn && !closeBtn.hasEventListener) {
            closeBtn.addEventListener('click', () => this.closeScraperDataModal());
            closeBtn.hasEventListener = true;
        }
        
        if (closeBtn2 && !closeBtn2.hasEventListener) {
            closeBtn2.addEventListener('click', () => this.closeScraperDataModal());
            closeBtn2.hasEventListener = true;
        }
        
        if (modal && !modal.hasEventListener) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeScraperDataModal();
                }
            });
            modal.hasEventListener = true;
        }
        
        // Setup search functionality
        if (searchInput && !searchInput.hasEventListener) {
            searchInput.addEventListener('input', () => this.filterScraperData());
            searchInput.hasEventListener = true;
        }
        
        if (searchBtn && !searchBtn.hasEventListener) {
            searchBtn.addEventListener('click', () => this.filterScraperData());
            searchBtn.hasEventListener = true;
        }
    }
    
    closeScraperDataModal() {
        const modal = document.getElementById('scraperDataModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    async loadScraperData(importId) {
        try {
            const response = await fetch(`/api/scraper-imports/${importId}/vehicles`);
            const data = await response.json();
            
            if (data.success) {
                // Store the full data for filtering
                this.currentScraperData = data;
                this.currentFilteredScraperData = data.vehicles || [];
                
                // Clear search input
                const searchInput = document.getElementById('scraperDataSearch');
                if (searchInput) searchInput.value = '';
                
                this.renderScraperDataModal(data);
            } else {
                console.error('Failed to load scraper data:', data.error);
                this.showScraperDataError('Failed to load scraper data');
            }
        } catch (error) {
            console.error('Error loading scraper data:', error);
            this.showScraperDataError('Error loading scraper data');
        }
    }
    
    renderScraperDataModal(data = null) {
        const displayData = data || this.currentScraperData;
        const vehicleData = this.currentFilteredScraperData || displayData?.vehicles || [];
        
        // Update import info
        const importId = document.getElementById('modalImportId');
        const importDate = document.getElementById('modalImportDate');
        const importSource = document.getElementById('modalImportSource');
        const totalVehicles = document.getElementById('modalTotalVehicles');
        
        if (importId) importId.textContent = `#${this.currentImportId}`;
        if (importDate) importDate.textContent = displayData?.import_info?.import_date ? 
            this.formatDate(displayData.import_info.import_date) : 'Unknown';
        if (importSource) importSource.textContent = displayData?.import_info?.import_source || 'Unknown';
        if (totalVehicles) totalVehicles.textContent = vehicleData.length;
        
        // Render vehicle table
        const tableContainer = document.getElementById('scraperDataTableContainer');
        if (!tableContainer) return;
        
        if (!vehicleData || vehicleData.length === 0) {
            tableContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No Vehicle Data Found</h3>
                    <p>No vehicles found in this import.</p>
                </div>
            `;
            return;
        }
        
        // Get column headers from first vehicle
        const firstVehicle = vehicleData[0];
        const headers = Object.keys(firstVehicle);
        
        tableContainer.innerHTML = `
            <table class="scraper-data-table">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${this.formatColumnHeader(header)}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${vehicleData.map(vehicle => `
                        <tr>
                            ${headers.map(header => `
                                <td>${this.formatCellValue(vehicle[header], header)}</td>
                            `).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    showScraperDataError(message) {
        const tableContainer = document.getElementById('scraperDataTableContainer');
        if (tableContainer) {
            tableContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Data</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    filterScraperData() {
        if (!this.currentScraperData || !this.currentScraperData.vehicles) return;
        
        const searchInput = document.getElementById('scraperDataSearch');
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        
        let filteredData = this.currentScraperData.vehicles;
        
        // Apply search filter
        if (searchTerm) {
            filteredData = filteredData.filter(vehicle => {
                return Object.values(vehicle).some(value => {
                    if (value === null || value === undefined) return false;
                    return String(value).toLowerCase().includes(searchTerm);
                });
            });
        }
        
        this.currentFilteredScraperData = filteredData;
        this.renderScraperDataModal();
    }
    
    formatColumnHeader(header) {
        return header.replace(/_/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatCellValue(value, header) {
        if (value === null || value === undefined) return '-';
        
        // Format specific columns
        if (header === 'price' && typeof value === 'number') {
            return `$${value.toLocaleString()}`;
        }
        
        if (header === 'year' && value) {
            return value;
        }
        
        if (header === 'vin' && value) {
            return `<span class="vin-number">${value}</span>`;
        }
        
        // Truncate long text
        const text = String(value);
        if (text.length > 50) {
            return `<span title="${text}">${text.substring(0, 47)}...</span>`;
        }
        
        return text;
    }

    // CSV Import Functionality
    setupCsvImport() {
        const selectBtn = document.getElementById('selectCsvBtn');
        const importBtn = document.getElementById('importCsvBtn');
        const fileInput = document.getElementById('csvFileInput');
        
        if (selectBtn && !selectBtn.hasEventListener) {
            selectBtn.addEventListener('click', () => {
                fileInput.click();
            });
            selectBtn.hasEventListener = true;
        }
        
        if (fileInput && !fileInput.hasEventListener) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    importBtn.disabled = false;
                    importBtn.innerHTML = `<i class="fas fa-download"></i> Import ${file.name}`;
                } else {
                    importBtn.disabled = true;
                    importBtn.innerHTML = `<i class="fas fa-download"></i> Import Data`;
                }
            });
            fileInput.hasEventListener = true;
        }
        
        if (importBtn && !importBtn.hasEventListener) {
            importBtn.addEventListener('click', () => {
                const file = fileInput.files[0];
                if (file) {
                    this.importCsvFile(file);
                }
            });
            importBtn.hasEventListener = true;
        }
    }
    
    async importCsvFile(file) {
        const statusDiv = document.getElementById('importStatus');
        const statusMessage = document.getElementById('importStatusMessage');
        const progressBar = document.getElementById('importProgressBar');
        const progressFill = document.getElementById('importProgressFill');
        const importBtn = document.getElementById('importCsvBtn');
        
        // Show status
        statusDiv.style.display = 'block';
        progressBar.style.display = 'block';
        statusMessage.textContent = 'Uploading file...';
        progressFill.style.width = '10%';
        importBtn.disabled = true;
        
        try {
            const formData = new FormData();
            formData.append('csv_file', file);
            
            statusMessage.textContent = 'Processing CSV data...';
            progressFill.style.width = '50%';
            
            const response = await fetch('/api/csv-import', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                statusMessage.textContent = `Successfully imported ${result.vehicle_count} vehicles!`;
                statusMessage.style.color = '#155724';
                progressFill.style.width = '100%';
                
                // Refresh the scraper history
                setTimeout(() => {
                    this.loadScraperHistory();
                    statusDiv.style.display = 'none';
                    progressBar.style.display = 'none';
                    
                    // Reset file input
                    const fileInput = document.getElementById('csvFileInput');
                    fileInput.value = '';
                    importBtn.innerHTML = `<i class="fas fa-download"></i> Import Data`;
                    importBtn.disabled = true;
                }, 2000);
                
            } else {
                statusMessage.textContent = `Import failed: ${result.error}`;
                statusMessage.style.color = '#721c24';
                progressFill.style.width = '100%';
                progressFill.style.background = '#dc3545';
            }
            
        } catch (error) {
            statusMessage.textContent = `Import error: ${error.message}`;
            statusMessage.style.color = '#721c24';
            progressFill.style.width = '100%';
            progressFill.style.background = '#dc3545';
        }
        
        importBtn.disabled = false;
    }
    
    // =============================================================================
    // VIN LOG UPDATE FUNCTIONALITY
    // =============================================================================
    
    openVinLogUpdateModal() {
        if (!this.currentDealership) {
            this.addTerminalMessage('No dealership selected for VIN log update', 'error');
            return;
        }
        
        // Update modal title and dealership name
        const updateTitle = document.getElementById('vinLogUpdateTitle');
        const dealershipName = document.getElementById('updateDealershipName');
        
        if (updateTitle) {
            updateTitle.textContent = `Update VIN Log - ${this.formatDealershipName(this.currentDealership)}`;
        }
        
        if (dealershipName) {
            dealershipName.textContent = this.formatDealershipName(this.currentDealership);
        }
        
        // Reset modal state
        this.resetVinLogUpdateModal();
        
        // Setup event listeners for this modal
        this.setupVinLogUpdateEvents();
        
        // Show the modal
        const modal = document.getElementById('vinLogUpdateModal');
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }
    
    setupVinLogUpdateEvents() {
        // File upload events
        const fileUploadArea = document.getElementById('vinLogFileUpload');
        const fileInput = document.getElementById('vinLogFileInput');
        const removeFileBtn = document.getElementById('removeVinLogFile');
        
        if (fileUploadArea && !fileUploadArea.hasVinLogEvents) {
            fileUploadArea.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileUploadArea.classList.add('dragover');
            });
            
            fileUploadArea.addEventListener('dragleave', () => {
                fileUploadArea.classList.remove('dragover');
            });
            
            fileUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                fileUploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].name.endsWith('.csv')) {
                    this.handleVinLogFileSelect(files[0]);
                }
            });
            
            fileUploadArea.hasVinLogEvents = true;
        }
        
        if (fileInput && !fileInput.hasVinLogEvents) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleVinLogFileSelect(e.target.files[0]);
                }
            });
            fileInput.hasVinLogEvents = true;
        }
        
        if (removeFileBtn && !removeFileBtn.hasVinLogEvents) {
            removeFileBtn.addEventListener('click', () => {
                this.clearVinLogFile();
            });
            removeFileBtn.hasVinLogEvents = true;
        }
        
        // Modal close events
        const closeBtn = document.getElementById('closeVinLogUpdateModal');
        const cancelBtn = document.getElementById('cancelVinLogUpdate');
        const modal = document.getElementById('vinLogUpdateModal');
        
        if (closeBtn && !closeBtn.hasVinLogEvents) {
            closeBtn.addEventListener('click', () => this.closeVinLogUpdateModal());
            closeBtn.hasVinLogEvents = true;
        }
        
        if (cancelBtn && !cancelBtn.hasVinLogEvents) {
            cancelBtn.addEventListener('click', () => this.closeVinLogUpdateModal());
            cancelBtn.hasVinLogEvents = true;
        }
        
        if (modal && !modal.hasVinLogEvents) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeVinLogUpdateModal();
                }
            });
            modal.hasVinLogEvents = true;
        }
        
        // Import button
        const importBtn = document.getElementById('startVinLogImport');
        if (importBtn && !importBtn.hasVinLogEvents) {
            importBtn.addEventListener('click', () => this.startVinLogImport());
            importBtn.hasVinLogEvents = true;
        }
    }
    
    resetVinLogUpdateModal() {
        // Clear file selection
        this.clearVinLogFile();
        
        // Reset checkboxes
        const skipDuplicates = document.getElementById('skipDuplicates');
        const updateExisting = document.getElementById('updateExisting');
        
        if (skipDuplicates) skipDuplicates.checked = true;
        if (updateExisting) updateExisting.checked = false;
        
        // Hide progress and results
        const progress = document.getElementById('vinLogImportProgress');
        const results = document.getElementById('vinLogImportResults');
        
        if (progress) progress.style.display = 'none';
        if (results) results.style.display = 'none';
        
        // Reset import button
        const importBtn = document.getElementById('startVinLogImport');
        if (importBtn) {
            importBtn.disabled = true;
            importBtn.innerHTML = '<i class="fas fa-upload"></i> Import CSV';
        }
        
        this.selectedVinLogFile = null;
    }
    
    handleVinLogFileSelect(file) {
        if (!file.name.endsWith('.csv')) {
            this.addTerminalMessage('Please select a CSV file', 'error');
            return;
        }
        
        this.selectedVinLogFile = file;
        
        // Update UI
        const uploadArea = document.getElementById('vinLogFileUpload');
        const fileInfo = document.getElementById('vinLogFileInfo');
        const fileName = document.getElementById('vinLogFileName');
        const importBtn = document.getElementById('startVinLogImport');
        
        if (uploadArea) uploadArea.style.display = 'none';
        if (fileInfo) fileInfo.style.display = 'flex';
        if (fileName) fileName.textContent = file.name;
        if (importBtn) importBtn.disabled = false;
        
        this.addTerminalMessage(`CSV file selected: ${file.name}`, 'success');
    }
    
    clearVinLogFile() {
        this.selectedVinLogFile = null;
        
        // Reset UI
        const uploadArea = document.getElementById('vinLogFileUpload');
        const fileInfo = document.getElementById('vinLogFileInfo');
        const fileInput = document.getElementById('vinLogFileInput');
        const importBtn = document.getElementById('startVinLogImport');
        
        if (uploadArea) uploadArea.style.display = 'block';
        if (fileInfo) fileInfo.style.display = 'none';
        if (fileInput) fileInput.value = '';
        if (importBtn) importBtn.disabled = true;
    }
    
    async startVinLogImport() {
        if (!this.selectedVinLogFile || !this.currentDealership) {
            this.addTerminalMessage('Missing file or dealership selection', 'error');
            return;
        }
        
        const skipDuplicates = document.getElementById('skipDuplicates')?.checked || false;
        const updateExisting = document.getElementById('updateExisting')?.checked || false;
        
        // Show progress section
        const progress = document.getElementById('vinLogImportProgress');
        const results = document.getElementById('vinLogImportResults');
        
        if (progress) progress.style.display = 'block';
        if (results) results.style.display = 'none';
        
        this.updateVinLogProgress('Uploading CSV file...', 0);
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('csv_file', this.selectedVinLogFile);
            formData.append('dealership_name', this.currentDealership);
            formData.append('skip_duplicates', skipDuplicates);
            formData.append('update_existing', updateExisting);
            
            // Upload and process
            const response = await fetch('/api/vin-log/import', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateVinLogProgress('Import completed successfully!', 100);
                this.showVinLogImportResults(result);
                this.addTerminalMessage(`VIN log updated: ${result.processed} records processed`, 'success');
                
                // Refresh VIN log data in background
                setTimeout(() => {
                    if (this.currentDealership) {
                        this.loadVinLogData(this.currentDealership);
                    }
                }, 1000);
            } else {
                this.updateVinLogProgress(`Import failed: ${result.error}`, 100);
                this.addTerminalMessage(`VIN log import failed: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('VIN log import error:', error);
            this.updateVinLogProgress(`Import error: ${error.message}`, 100);
            this.addTerminalMessage(`VIN log import error: ${error.message}`, 'error');
        }
    }
    
    updateVinLogProgress(text, percent) {
        const progressText = document.getElementById('vinLogProgressText');
        const progressFill = document.getElementById('vinLogProgressFill');
        
        if (progressText) progressText.textContent = text;
        if (progressFill) progressFill.style.width = `${percent}%`;
    }
    
    showVinLogImportResults(result) {
        const resultsSection = document.getElementById('vinLogImportResults');
        if (!resultsSection) return;
        
        // Update result statistics
        const processedCount = document.getElementById('processedCount');
        const addedCount = document.getElementById('addedCount');
        const updatedCount = document.getElementById('updatedCount');
        const skippedCount = document.getElementById('skippedCount');
        const errorCount = document.getElementById('errorCount');
        
        if (processedCount) processedCount.textContent = result.processed || 0;
        if (addedCount) addedCount.textContent = result.added || 0;
        if (updatedCount) updatedCount.textContent = result.updated || 0;
        if (skippedCount) skippedCount.textContent = result.skipped || 0;
        if (errorCount) errorCount.textContent = result.errors ? result.errors.length : 0;
        
        // Update log container
        const logContainer = document.getElementById('importLogContainer');
        if (logContainer && result.log) {
            logContainer.innerHTML = result.log.map(entry => 
                `<div class="log-entry ${entry.type}">${entry.message}</div>`
            ).join('');
        }
        
        // Show results section
        resultsSection.style.display = 'block';
    }
    
    closeVinLogUpdateModal() {
        const modal = document.getElementById('vinLogUpdateModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }
    
    setupExportHandlers() {
        // VIN Log Export Handler
        const vinLogExportBtn = document.getElementById('exportVinLogData');
        if (vinLogExportBtn) {
            vinLogExportBtn.addEventListener('click', () => this.exportVinLogData());
        }
        
        // Scraper Data Export Handler
        const scraperDataExportBtn = document.getElementById('exportScraperData');
        if (scraperDataExportBtn) {
            scraperDataExportBtn.addEventListener('click', () => this.exportScraperData());
        }
    }
    
    async exportVinLogData() {
        try {
            const dealershipName = document.getElementById('vinLogModalTitle').textContent.replace('VIN History - ', '');
            
            // Show loading state
            const exportBtn = document.getElementById('exportVinLogData');
            const originalText = exportBtn.innerHTML;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            exportBtn.disabled = true;
            
            const response = await fetch('/api/vin-log/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dealership_name: dealershipName
                })
            });
            
            if (!response.ok) {
                throw new Error(`Export failed: ${response.statusText}`);
            }
            
            // Get the blob and create download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vin_log_${dealershipName.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showNotification('VIN log data exported successfully!', 'success');
            
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification(`Export failed: ${error.message}`, 'error');
        } finally {
            // Restore button state
            const exportBtn = document.getElementById('exportVinLogData');
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
        }
    }
    
    async exportScraperData() {
        try {
            const importId = document.getElementById('modalImportId').textContent;
            
            if (!importId || importId === '-') {
                this.showNotification('No import data to export', 'warning');
                return;
            }
            
            // Show loading state
            const exportBtn = document.getElementById('exportScraperData');
            const originalText = exportBtn.innerHTML;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            exportBtn.disabled = true;
            
            const response = await fetch('/api/scraper-data/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    import_id: importId
                })
            });
            
            if (!response.ok) {
                throw new Error(`Export failed: ${response.statusText}`);
            }
            
            // Get the blob and create download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scraper_data_${importId}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showNotification('Scraper data exported successfully!', 'success');
            
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification(`Export failed: ${error.message}`, 'error');
        } finally {
            // Restore button state
            const exportBtn = document.getElementById('exportScraperData');
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
        }
    }
}

// Initialize the application when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new MinisFornumApp();
});

// Global function for inline event handlers
window.app = app;