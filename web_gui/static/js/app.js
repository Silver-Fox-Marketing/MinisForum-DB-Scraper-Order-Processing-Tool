/**
 * MinisForum Database Web GUI - JavaScript Application
 * Silver Fox Marketing - Dealership Management Interface
 * 
 * Handles all frontend interactions, API calls, and real-time updates
 * for the dealership database control system.
 */

// TEMPLATE CACHING BYPASS - DOM INJECTION FOR SEARCH BAR
document.addEventListener('DOMContentLoaded', function() {
    // Inject dealership settings search bar using DOM manipulation
    setTimeout(() => {
        const dealershipPanel = document.getElementById('dealership-settings-panel');
        if (dealershipPanel) {
            const panelHeader = dealershipPanel.querySelector('.panel-header');
            if (panelHeader && !document.getElementById('injected-search-bar')) {
                console.log('Injecting search bar via DOM manipulation...');
                
                const searchContainer = document.createElement('div');
                searchContainer.id = 'injected-search-bar';
                searchContainer.className = 'dealership-settings-search-container';
                searchContainer.innerHTML = `
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" 
                           id="dealershipSettingsSearchInput" 
                           class="search-input" 
                           placeholder="Search dealerships by name...">
                    <button id="clearDealershipSearch" class="btn btn-sm btn-secondary" style="display: none;">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                
                // Insert after panel header
                panelHeader.insertAdjacentElement('afterend', searchContainer);
                
                // Attach search functionality
                const searchInput = searchContainer.querySelector('#dealershipSettingsSearchInput');
                const clearButton = searchContainer.querySelector('#clearDealershipSearch');
                
                searchInput.addEventListener('input', function() {
                    const query = this.value.toLowerCase().trim();
                    clearButton.style.display = query ? 'block' : 'none';
                    filterDealershipSettings(query);
                });
                
                clearButton.addEventListener('click', function() {
                    searchInput.value = '';
                    this.style.display = 'none';
                    filterDealershipSettings('');
                });
                
                console.log('✅ Search bar successfully injected via DOM!');
            }
        }
    }, 1000); // Allow time for page to fully load
});

function filterDealershipSettings(query) {
    const dealershipItems = document.querySelectorAll('.modern-dealer-panel');
    let visibleCount = 0;
    
    dealershipItems.forEach(item => {
        const dealershipName = item.querySelector('.dealer-title');
        if (dealershipName) {
            const name = dealershipName.textContent.toLowerCase();
            const isVisible = !query || name.includes(query);
            
            item.style.display = isVisible ? 'flex' : 'none';
            if (isVisible) visibleCount++;
        }
    });
    
    // Update results info if container exists
    const resultsInfo = document.getElementById('dealershipSettingsSearchInfo');
    if (resultsInfo) {
        if (query) {
            resultsInfo.textContent = `Found ${visibleCount} dealerships matching "${query}"`;
            resultsInfo.style.display = 'block';
        } else {
            resultsInfo.style.display = 'none';
        }
    }
}

// Global variables for vehicle data editing
let reviewVehicleData = [];
let currentEditingIndex = -1;

// Global function for inline row editing
function toggleRowEdit(index) {
    const row = document.getElementById(`vehicle-row-${index}`);
    const editBtn = document.getElementById(`edit-btn-${index}`);
    const isEditing = row.getAttribute('data-editing') === 'true';
    
    if (isEditing) {
        // Save changes and switch to display mode
        saveRowChanges(index);
        setRowEditMode(index, false);
        editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
    } else {
        // Switch to edit mode
        setRowEditMode(index, true);
        editBtn.innerHTML = '<i class="fas fa-save"></i> Save';
    }
}

function setRowEditMode(index, isEditing) {
    const row = document.getElementById(`vehicle-row-${index}`);
    const editableCells = row.querySelectorAll('.editable-cell');
    
    row.setAttribute('data-editing', isEditing.toString());
    
    editableCells.forEach(cell => {
        const displayValue = cell.querySelector('.display-value');
        const editInput = cell.querySelector('.edit-input');
        
        if (isEditing) {
            displayValue.style.display = 'none';
            editInput.style.display = 'block';
            editInput.focus();
        } else {
            displayValue.style.display = 'block';
            editInput.style.display = 'none';
        }
    });
}

function saveRowChanges(index) {
    const row = document.getElementById(`vehicle-row-${index}`);
    const editableCells = row.querySelectorAll('.editable-cell');
    
    editableCells.forEach(cell => {
        const displayValue = cell.querySelector('.display-value');
        const editInput = cell.querySelector('.edit-input');
        const field = cell.getAttribute('data-field');
        
        // Update display value with edited value
        const newValue = editInput.value;
        displayValue.textContent = newValue;
        
        // Update the vehicle data
        if (reviewVehicleData[index]) {
            if (field === 'year-make') {
                const parts = newValue.split(' ');
                reviewVehicleData[index].year = parts[0] || '';
                reviewVehicleData[index].make = parts.slice(1).join(' ') || '';
            } else if (field === 'model') {
                reviewVehicleData[index].model = newValue;
            } else if (field === 'trim') {
                reviewVehicleData[index].trim = newValue;
            } else if (field === 'stock') {
                reviewVehicleData[index].stock = newValue;
            } else if (field === 'vin') {
                reviewVehicleData[index].vin = newValue;
                // Update title attribute for full VIN display
                displayValue.setAttribute('title', newValue);
            }
        }
    });
    
    console.log('Updated vehicle data:', reviewVehicleData[index]);
}

class MinisFornumApp {
    constructor() {
        this.dealerships = [];
        this.selectedDealerships = new Set();
        this.scraperRunning = false;
        this.currentTab = 'queue-management';
        this.currentDealership = null;
        this.currentImportMethod = 'csv'; // Default to CSV import method
        
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
        
        // Listen for modal wizard completion events
        window.addEventListener('modalWizardComplete', (event) => {
            if (event.detail.action === 'clearQueue') {
                console.log('🧹 IMMEDIATE: Clearing queue on modal completion');
                this.clearQueue();
            }
        });
        this.progressData = {
            totalScrapers: 0,
            completedScrapers: 0,
            currentScraper: null,
            progressPercent: 0
        };

        // Active scrapers tracking
        this.activeScrapers = new Map(); // Track running scrapers by name

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

        // Load saved dealership schedule on startup
        this.loadSavedScheduleOnStartup();
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
        
        // Initialize theme system
        this.initTheme();
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Initialize manual VIN entry functionality
        // Commented out - function was moved to modal-specific initialization
        // this.initializeManualVinEntry();
        
        // Load initial data
        try {
            await this.loadDealerships();
            console.log(`✅ Loaded ${this.dealerships.length} dealerships`);
            console.log('Dealership names:', this.dealerships.map(d => d.name));
            
            // Load dealership defaults after dealerships are loaded
            await this.loadDealershipDefaults();
            
            // Re-render dealership list with correct types
            await this.renderDealershipList(this.dealerships);
            
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
        
        // Initialize with the correct tab display
        this.switchTab(this.currentTab);
        
        console.log('Application initialized successfully');
    }
    
    bindEventListeners() {
        // Sidebar tab navigation (updated for new sidebar structure)
        document.querySelectorAll('.sidebar-tab').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = e.currentTarget.dataset.tab;
                if (tabName) {
                    this.switchTab(tabName);
                }
            });
        });
        
        // Also handle legacy tab-button class for compatibility
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = e.currentTarget.dataset.tab;
                if (tabName) {
                    this.switchTab(tabName);
                }
            });
        });
        
        // Sidebar toggle functionality
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarExpand = document.getElementById('sidebarExpand');
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const sidebar = document.querySelector('.sidebar-navigation');
        const mainContent = document.querySelector('.main-content');
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
            });
        }
        
        if (sidebarExpand) {
            sidebarExpand.addEventListener('click', () => {
                sidebar.classList.remove('collapsed');
            });
        }
        
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
                mainContent.classList.toggle('sidebar-open');
            });
        }
        
        // Close mobile sidebar when clicking overlay
        if (mainContent) {
            mainContent.addEventListener('click', (e) => {
                if (e.target === mainContent && sidebar.classList.contains('mobile-open')) {
                    sidebar.classList.remove('mobile-open');
                    mainContent.classList.remove('sidebar-open');
                }
            });
        }
        
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

        // Dealership Schedule Configuration Modal
        document.getElementById('schedule-settings-btn').addEventListener('click', () => {
            this.showDealershipScheduleModal();
        });

        document.getElementById('closeDealershipScheduleModal').addEventListener('click', () => {
            this.closeModal('dealershipScheduleModal');
        });

        document.getElementById('cancelScheduleConfig').addEventListener('click', () => {
            this.closeModal('dealershipScheduleModal');
        });

        document.getElementById('saveScheduleConfig').addEventListener('click', () => {
            this.saveDealershipScheduleConfig();
        });

        document.getElementById('selectAllDays').addEventListener('click', () => {
            this.assignAllDealershipsToAllDays();
        });

        document.getElementById('clearAllDays').addEventListener('click', () => {
            this.clearAllDealershipAssignments();
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
        document.getElementById('modalTitle').textContent = dealershipName;
        
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
        document.getElementById('seasoningDays').value = filteringRules.seasoning_days || '';
        
        // Set required brands field (convert array to comma-separated string)
        const requiredBrands = filteringRules.required_brands || [];
        document.getElementById('requiredBrands').value = requiredBrands.join(', ');
        
        // Set order type (default to CAO if not specified)
        const orderType = filteringRules.order_type || 'cao';
        if (orderType === 'list') {
            document.getElementById('orderTypeList').checked = true;
        } else {
            document.getElementById('orderTypeCao').checked = true;
        }
        
        this.showModal('dealershipModal');
    }
    
    async saveDealershipSettings() {
        console.log('saveDealershipSettings (first version) called');
        console.log('currentDealership:', this.currentDealership);
        
        if (!this.currentDealership) {
            console.log('No currentDealership set, returning');
            return;
        }
        
        try {
            // Collect form data
            const vehicleTypes = Array.from(document.querySelectorAll('input[name="vehicle_types"]:checked'))
                .map(input => input.value);
            
            console.log('Vehicle types selected:', vehicleTypes);
            
            // Build exclude conditions based on what's NOT selected
            const excludeConditions = [];
            
            // Check if NEW is excluded
            if (!vehicleTypes.includes('new')) {
                excludeConditions.push('new');
            }
            
            // Check if USED is excluded (used encompasses po and cpo)
            if (!vehicleTypes.includes('used')) {
                excludeConditions.push('used');
                excludeConditions.push('po');
                excludeConditions.push('cpo');
            } else {
                // If used IS selected, we still exclude po and cpo as separate categories
                excludeConditions.push('po');
                excludeConditions.push('cpo');
            }
            
            console.log('Exclude conditions:', excludeConditions);
            
            const filteringRules = {
                exclude_conditions: excludeConditions,  // Keep for backward compatibility
                vehicle_types: vehicleTypes,  // Add this for backend CAO processing
                allowed_vehicle_types: vehicleTypes,  // Also add this variant that backend checks
                require_stock: true,
                exclude_missing_stock: true  // Backend checks this flag
            };
            
            // Add price filters if specified
            const minPrice = parseInt(document.getElementById('minPrice').value);
            const maxPrice = parseInt(document.getElementById('maxPrice').value);
            const minYear = parseInt(document.getElementById('minYear').value);
            const seasoningDays = parseInt(document.getElementById('seasoningDays').value);
            
            if (minPrice) filteringRules.min_price = minPrice;
            if (maxPrice) filteringRules.max_price = maxPrice;
            if (seasoningDays) filteringRules.seasoning_days = seasoningDays;
            if (minYear) filteringRules.min_year = minYear;
            
            // Add required brands filter (for dealerships like Pappas Toyota that only want specific brands)
            const requiredBrandsInput = document.getElementById('requiredBrands').value.trim();
            if (requiredBrandsInput) {
                // Convert comma-separated string to array
                const brandsArray = requiredBrandsInput.split(',').map(brand => brand.trim()).filter(brand => brand);
                if (brandsArray.length > 0) {
                    filteringRules.required_brands = brandsArray;
                }
            }
            
            // Add exclude missing price filter (critical for graphics printing)
            const excludeMissingPrice = document.getElementById('excludeMissingPrice').checked;
            filteringRules.exclude_missing_price = excludeMissingPrice;
            
            // Add order type from radio buttons
            const orderTypeRadios = document.getElementsByName('order_type');
            let selectedOrderType = 'cao'; // default
            for (const radio of orderTypeRadios) {
                if (radio.checked) {
                    selectedOrderType = radio.value;
                    break;
                }
            }
            filteringRules.order_type = selectedOrderType;

            // Get template type settings and new output configurations
            const templateVariant = document.getElementById('templateVariant')?.value || 'standard';
            const priceMarkup = parseInt(document.getElementById('priceMarkup')?.value) || 0;

            // Get custom template selections for new and used vehicles
            const newCustomTemplate = document.getElementById('newVehicleCustomTemplate')?.value || '';
            const usedCustomTemplate = document.getElementById('usedVehicleCustomTemplate')?.value || '';

            console.log('[DEBUG] Custom template values:', {
                newCustomTemplate,
                usedCustomTemplate,
                newElement: document.getElementById('newVehicleCustomTemplate'),
                usedElement: document.getElementById('usedVehicleCustomTemplate')
            });

            const outputRules = {
                custom_templates: {
                    new: newCustomTemplate,
                    used: usedCustomTemplate
                },
                template_variant: templateVariant,
                price_markup: priceMarkup
            };

            console.log('Custom template settings:', outputRules.custom_templates);
            console.log('Full output rules:', outputRules);

            // Send update to server
            const requestBody = {
                filtering_rules: filteringRules,
                output_rules: outputRules,
                is_active: true
            };
            
            console.log('Sending update to server:', {
                endpoint: `/api/dealerships/${this.currentDealership}`,
                body: requestBody
            });
            
            const response = await fetch(`/api/dealerships/${this.currentDealership}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            const result = await response.json();
            console.log('Server response:', result);
            
            if (result.success) {
                this.addTerminalMessage(`Updated settings for ${this.currentDealership}`, 'success');
                this.closeModal('dealershipModal');
                
                // Update just this dealership's data
                await this.loadDealerships(); // Refresh the dealership settings grid
                
                // Also refresh the order queue management dealership list
                await this.loadDealershipDefaults(); // Reload defaults from updated data
                await this.renderDealershipList(this.dealerships); // Re-render order queue list
                
                // Update just this dealership's default in memory and queue
                const dealership = this.dealerships.find(d => d.name === this.currentDealership);
                if (dealership) {
                    const orderType = dealership.filtering_rules?.order_type || 'cao';
                    this.dealershipDefaults.set(dealership.name, orderType.toUpperCase());
                    
                    // Update only this dealership's queue item if it exists
                    if (this.processingQueue.has(dealership.name)) {
                        const item = this.processingQueue.get(dealership.name);
                        item.orderType = orderType.toUpperCase();
                        this.processingQueue.set(dealership.name, item);
                        this.renderQueue(); // Re-render to show updated selection
                    }
                }
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

        // If no dealerships selected, ask if they want to run all
        if (this.selectedDealerships.size === 0) {
            const runAll = confirm('No dealerships selected. Would you like to run scrapers for ALL dealerships?');
            if (runAll) {
                // Select all dealerships
                this.selectAllDealerships();
                this.addTerminalMessage('Selected all dealerships for scraping', 'info');
                this.addScraperConsoleMessage('[INFO] Selected all dealerships for scraping', 'info');
            } else {
                this.addTerminalMessage('Please select at least one dealership before starting the scraper.', 'warning');
                this.addScraperConsoleMessage('[WARNING] Please select at least one dealership before starting the scraper.', 'warning');
                return;
            }
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
        // Update sidebar tab buttons (updated for new sidebar structure)
        document.querySelectorAll('.sidebar-tab').forEach(button => {
            button.classList.remove('active');
        });
        
        // Also handle legacy tab-button class
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        
        const activeTab = document.querySelector(`.sidebar-tab[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }
        
        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        const targetPanel = document.getElementById(`${tabName}-panel`);
        console.log(`[DEBUG] Switching to tab: ${tabName}`);
        console.log(`[DEBUG] Target panel ID: ${tabName}-panel`);
        console.log(`[DEBUG] Panel found:`, !!targetPanel);

        if (targetPanel) {
            targetPanel.classList.add('active');
            console.log(`[DEBUG] Added active class to panel:`, targetPanel.id);

            // Template builder activation
            if (tabName === 'template-builder') {
                console.log(`[SUCCESS] Template builder activated`);

                // Make a global function to inspect this panel
                window.debugTemplateBuilder = function() {
                    const panel = document.getElementById('template-builder-panel');
                    console.log('=== TEMPLATE BUILDER DEBUG INFO ===');
                    console.log('Panel exists:', !!panel);
                    if (panel) {
                        console.log('Panel position:', panel.getBoundingClientRect());
                        console.log('Panel computed styles:', getComputedStyle(panel));
                        console.log('Panel parent:', panel.parentElement);
                        console.log('Panel innerHTML length:', panel.innerHTML.length);
                        console.log('Panel classes:', panel.className);
                        panel.style.border = '20px solid lime';
                        panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                };

                console.log(`[DEBUG] Global debug function created: debugTemplateBuilder()`);

                // Auto-fix: Move template builder if it's in wrong container
                if (tabName === 'template-builder') {
                    const parentContainer = targetPanel.parentElement;

                    // Check if it's in the wrong container and fix it
                    if (parentContainer && parentContainer.classList.contains('sub-tab-panels')) {
                        // Move it to the correct container
                        const mainTabContainer = document.querySelector('.main-content .tab-panels') ||
                                               document.querySelector('.main-content') ||
                                               parentContainer.parentElement.parentElement;

                        if (mainTabContainer && mainTabContainer !== parentContainer) {
                            mainTabContainer.appendChild(targetPanel);
                            console.log(`[AUTO-FIX] Template builder moved to correct container`);
                        }
                    }
                }
            }
        } else {
            console.error(`[ERROR] Panel not found for tab: ${tabName}`);
        }
        
        this.currentTab = tabName;
        
        // Show/hide floating queue actions panel based on tab
        const floatingPanel = document.getElementById('floatingQueueActions');
        if (floatingPanel) {
            if (tabName === 'queue') {
                floatingPanel.style.display = 'block';
            } else {
                floatingPanel.style.display = 'none';
            }
        }
        
        // If switching to scraper tab, ensure scraper status visibility is preserved
        if (tabName === 'scraper') {
            this.restoreScraperStatusVisibility();
        }
        
        // Close mobile sidebar after tab switch
        const sidebar = document.querySelector('.sidebar-navigation');
        const mainContent = document.querySelector('.main-content');
        if (sidebar && mainContent && window.innerWidth <= 768) {
            sidebar.classList.remove('mobile-open');
            mainContent.classList.remove('sidebar-open');
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
            case 'template-builder':
                // Template builder doesn't need data loading
                console.log('Template Builder tab activated');
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
            modal.style.display = 'none';
        }

        // Special cleanup for dealership settings modal
        if (modalId === 'dealershipModal') {
            this.currentEditingDealership = null;
        }

        // Special cleanup for dealership schedule modal
        if (modalId === 'dealershipScheduleModal') {
            // Reset any modal-specific state if needed
            console.log('Dealership schedule modal closed');
        }
    }

    showDealershipScheduleModal() {
        this.loadDealershipScheduleData();
        this.showModal('dealershipScheduleModal');
    }

    async loadDealershipScheduleData() {
        try {
            // Get all dealerships
            const response = await fetch('/api/dealerships');
            const dealerships = await response.json();

            if (Array.isArray(dealerships) && dealerships.length > 0) {
                this.dealerships = dealerships;
                this.renderDealershipScheduleInterface();
                this.loadCurrentScheduleSettings();
            } else {
                console.error('No dealerships found or invalid response structure');
                this.addTerminalMessage('No dealerships found', 'error');
            }
        } catch (error) {
            console.error('Error loading dealership data:', error);
            this.addTerminalMessage('Error loading dealership data', 'error');
        }
    }

    renderDealershipScheduleInterface() {
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];

        days.forEach(day => {
            // Target specifically the modal's day containers
            const gridContainer = document.querySelector(`#dealershipScheduleModal [data-day="${day}"]`);
            if (gridContainer) {
                gridContainer.innerHTML = '';

                // Create dealership items for this day
                this.dealerships.forEach(dealership => {
                    const dealershipItem = document.createElement('div');
                    dealershipItem.className = 'dealership-item';
                    dealershipItem.dataset.dealership = dealership.name;
                    dealershipItem.textContent = dealership.name;

                    // Add click handler to toggle assignment
                    dealershipItem.addEventListener('click', () => {
                        this.toggleDealershipAssignment(day, dealership.name, dealershipItem);
                    });

                    gridContainer.appendChild(dealershipItem);
                });
            }
        });
    }

    async loadCurrentScheduleSettings() {
        try {
            const response = await fetch('/api/dealership-schedule');
            const data = await response.json();

            if (data.success && data.schedule) {
                this.currentScheduleSettings = data.schedule;
                this.applyCurrentScheduleToInterface();
            } else {
                // Initialize empty schedule if none exists
                this.currentScheduleSettings = {
                    monday: [],
                    tuesday: [],
                    wednesday: [],
                    thursday: [],
                    friday: []
                };
            }
        } catch (error) {
            console.error('Error loading schedule settings:', error);
            // Initialize empty schedule on error
            this.currentScheduleSettings = {
                monday: [],
                tuesday: [],
                wednesday: [],
                thursday: [],
                friday: []
            };
        }
    }

    applyCurrentScheduleToInterface() {
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];

        days.forEach(day => {
            const assignedDealerships = this.currentScheduleSettings[day] || [];
            assignedDealerships.forEach(dealershipName => {
                const dealershipItem = document.querySelector(`#dealershipScheduleModal [data-day="${day}"] [data-dealership="${dealershipName}"]`);
                if (dealershipItem) {
                    dealershipItem.classList.add('selected');
                }
            });
        });
    }

    toggleDealershipAssignment(day, dealershipName, element) {
        if (!this.currentScheduleSettings[day]) {
            this.currentScheduleSettings[day] = [];
        }

        const isCurrentlyAssigned = this.currentScheduleSettings[day].includes(dealershipName);

        if (isCurrentlyAssigned) {
            // Remove from assignment
            this.currentScheduleSettings[day] = this.currentScheduleSettings[day].filter(name => name !== dealershipName);
            element.classList.remove('selected');
        } else {
            // Add to assignment
            this.currentScheduleSettings[day].push(dealershipName);
            element.classList.add('selected');
        }
    }

    assignAllDealershipsToAllDays() {
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
        const allDealershipNames = this.dealerships.map(d => d.name);

        days.forEach(day => {
            this.currentScheduleSettings[day] = [...allDealershipNames];

            // Update UI in modal
            const gridContainer = document.querySelector(`#dealershipScheduleModal [data-day="${day}"]`);
            if (gridContainer) {
                const dealershipItems = gridContainer.querySelectorAll('.dealership-item');
                dealershipItems.forEach(item => item.classList.add('selected'));
            }
        });
    }

    clearAllDealershipAssignments() {
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];

        days.forEach(day => {
            this.currentScheduleSettings[day] = [];

            // Update UI in modal
            const gridContainer = document.querySelector(`#dealershipScheduleModal [data-day="${day}"]`);
            if (gridContainer) {
                const dealershipItems = gridContainer.querySelectorAll('.dealership-item');
                dealershipItems.forEach(item => item.classList.remove('selected'));
            }
        });
    }

    async saveDealershipScheduleConfig() {
        try {
            const response = await fetch('/api/dealership-schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    schedule: this.currentScheduleSettings
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addTerminalMessage('Dealership schedule saved successfully', 'success');

                // Apply the saved schedule to the main day buttons
                this.applyScheduleToMainInterface();

                this.closeModal('dealershipScheduleModal');
            } else {
                this.addTerminalMessage(`Failed to save schedule: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error saving dealership schedule:', error);
            this.addTerminalMessage('Error saving dealership schedule', 'error');
        }
    }

    applyScheduleToMainInterface() {
        // Apply the saved schedule to the main day buttons and dealership list
        const dayButtons = document.querySelectorAll('.day-btn');

        dayButtons.forEach(button => {
            const day = button.dataset.day;
            const assignedDealerships = this.currentScheduleSettings[day] || [];

            // Update button state based on whether it has assigned dealerships
            if (assignedDealerships.length > 0) {
                button.classList.add('has-assignments');
                button.title = `${assignedDealerships.length} dealerships assigned`;
            } else {
                button.classList.remove('has-assignments');
                button.title = 'No dealerships assigned';
            }
        });

        // Store the schedule globally so other parts of the app can access it
        window.dealershipSchedule = this.currentScheduleSettings;

        console.log('Applied schedule to main interface:', this.currentScheduleSettings);
    }

    async loadSavedScheduleOnStartup() {
        try {
            const response = await fetch('/api/dealership-schedule');
            const data = await response.json();

            if (data.success && data.schedule) {
                this.currentScheduleSettings = data.schedule;
                this.applyScheduleToMainInterface();
                console.log('Loaded saved schedule on startup:', data.schedule);
            }
        } catch (error) {
            console.log('No saved schedule found or error loading:', error);
            // Initialize empty schedule
            this.currentScheduleSettings = {
                monday: [],
                tuesday: [],
                wednesday: [],
                thursday: [],
                friday: []
            };
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

        // Add to active scrapers tracking
        this.activeScrapers.set(data.scraper_name, {
            name: data.scraper_name,
            startTime: new Date(),
            status: 'starting',
            progress: data.progress || 0,
            total: data.total || 0,
            expected_vehicles: data.expected_vehicles || 0
        });
        this.updateActiveScrapersList();

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

        // Remove from active scrapers
        this.activeScrapers.delete(data.scraper_name);
        this.updateActiveScrapersList();

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

    updateActiveScrapersList() {
        const activeScrapersList = document.getElementById('activeScrapersList');
        if (!activeScrapersList) return;

        if (this.activeScrapers.size === 0) {
            activeScrapersList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-robot"></i>
                    <p>No active scrapers</p>
                    <p class="help-text">Start a scraper from the controls above to see real-time progress</p>
                </div>
            `;
            return;
        }

        activeScrapersList.innerHTML = Array.from(this.activeScrapers.values()).map(scraper => {
            const elapsed = Math.floor((new Date() - scraper.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const timeStr = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

            return `
                <div class="active-scraper-card">
                    <div class="scraper-header">
                        <div class="scraper-name">${scraper.name}</div>
                        <div class="scraper-time">${timeStr}</div>
                    </div>
                    <div class="scraper-status">${scraper.status}</div>
                    ${scraper.expected_vehicles > 0 ? `<div class="scraper-vehicles">~${scraper.expected_vehicles} vehicles expected</div>` : ''}
                </div>
            `;
        }).join('');
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
        
        // Initialize sub-tabs for queue management
        this.initSubTabs();
        
        // Ensure the default sub-tab (order-queue) is active
        const defaultSubTab = document.querySelector('[data-subtab="order-queue"]');
        if (defaultSubTab) {
            defaultSubTab.classList.add('active');
        }
        const defaultPanel = document.getElementById('order-queue-panel');
        if (defaultPanel) {
            defaultPanel.classList.add('active');
            defaultPanel.style.display = 'block';
        }
        
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
        
        // Don't setup anything here - let the sub-tab switching handle it
        
        this.addTerminalMessage('Queue management interface loaded', 'success');
    }
    
    async loadDealershipSettings() {
        console.log('Loading dealership settings...');
        
        try {
            const response = await fetch('/api/dealership-settings');
            const result = await response.json();
            
            if (result.success) {
                this.renderDealershipSettings(result.dealerships);
            } else {
                throw new Error(result.error || 'Failed to load settings');
            }
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
            // Escape dealership name for safe use in onclick handlers
            const escapedName = dealer.name.replace(/'/g, "\\'");
            const vehicleTypes = dealer.filtering_rules?.vehicle_types || [];
            const vehicleTypesDisplay = vehicleTypes.length > 0 
                ? vehicleTypes.map(type => {
                    const typeDisplay = type.charAt(0).toUpperCase() + type.slice(1);
                    return `<span class="vehicle-type-tag ${type}">${typeDisplay}</span>`;
                }).join('')
                : '<span class="no-types">No vehicle types configured</span>';
            
            // Generate active filters display
            const activeFilters = [];
            if (dealer.filtering_rules?.exclude_missing_stock) {
                activeFilters.push('<span class="filter-tag stock-filter"><i class="fas fa-hashtag"></i> Exclude Missing Stock</span>');
            }
            if (dealer.filtering_rules?.exclude_missing_price) {
                activeFilters.push('<span class="filter-tag price-filter"><i class="fas fa-dollar-sign"></i> Exclude Missing Price</span>');
            }
            if (dealer.filtering_rules?.exclude_status?.length > 0) {
                const statusList = dealer.filtering_rules.exclude_status.join(', ');
                activeFilters.push(`<span class="filter-tag status-filter"><i class="fas fa-ban"></i> Exclude: ${statusList}</span>`);
            }
            
            const filtersDisplay = activeFilters.length > 0 
                ? activeFilters.join('')
                : '<span class="no-filters">No special filters active</span>';
            
            const dealerInitials = dealer.name.split(' ')
                .map(word => word.charAt(0))
                .slice(0, 2)
                .join('')
                .toUpperCase();
            
            const isActive = dealer.active;
            const vehicleCount = dealer.vehicle_count || 0;
            
            return `
            <div class="dealership-settings-card ${!isActive ? 'disabled' : ''}" data-dealer-name="${dealer.name}" data-dealership-id="${dealer.id}" data-is-active="${isActive}">
                <div class="settings-card-header">
                    <h3>
                        <div class="dealer-icon">${dealerInitials}</div>
                        ${dealer.name}
                    </h3>
                    <div class="dealer-status">
                        <div class="status-indicator ${isActive ? '' : 'offline'}"></div>
                        <span class="order-type-badge-header">
                            <i class="fas fa-${dealer.filtering_rules?.order_type === 'list' ? 'list' : 'search'}"></i>
                            ${(dealer.filtering_rules?.order_type || 'cao').toUpperCase()}
                        </span>
                    </div>
                </div>
                <div class="settings-card-body">
                    <div class="status-section">
                        <div class="status-toggle">
                            <input type="checkbox" class="modern-toggle" id="toggle-${dealer.id}" ${isActive ? 'checked' : ''}>
                            <label for="toggle-${dealer.id}" class="toggle-label">
                                <span class="toggle-slider"></span>
                                <span class="toggle-text">
                                    <i class="fas fa-${isActive ? 'check-circle' : 'times-circle'}"></i>
                                    ${isActive ? 'Active' : 'Inactive'}
                                </span>
                            </label>
                        </div>
                    </div>
                    
                    <div class="metrics-section">
                        <div class="metric-item">
                            <i class="fas fa-car"></i>
                            <span class="metric-number">${vehicleCount}</span>
                            <span class="metric-label">vehicles</span>
                        </div>
                        <div class="metric-item">
                            <i class="fas fa-clock"></i>
                            <span class="metric-date">${dealer.updated_at ? new Date(dealer.updated_at).toLocaleDateString() : 'Never'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="card-actions">
                    <button class="modern-btn test-btn" onclick="app.testDealerConnection('${escapedName}')" title="Test Connection">
                        <i class="fas fa-play-circle"></i>
                    </button>
                    <button class="modern-btn settings-btn" onclick="app.editDealershipSettings('${escapedName}')" title="Settings">
                        <i class="fas fa-cogs"></i>
                    </button>
                    <button class="modern-btn history-btn" onclick="app.showDealershipVinLog('${escapedName}')" title="View VIN History">
                        <i class="fas fa-history"></i>
                    </button>
                </div>
            </div>
            `;
        }).join('');
        
        // Setup save button
        const saveBtn = document.getElementById('saveDealershipSettings');
        if (saveBtn && !saveBtn.hasEventListener) {
            saveBtn.addEventListener('click', () => this.saveAllDealershipSettings());
            saveBtn.hasEventListener = true;
        }
        
        // Setup refresh button
        const refreshBtn = document.getElementById('refreshDealershipSettings');
        if (refreshBtn && !refreshBtn.hasEventListener) {
            refreshBtn.addEventListener('click', () => this.loadDealershipSettings());
            refreshBtn.hasEventListener = true;
        }
        
        // Setup search functionality for dealership settings
        this.setupDealershipSettingsSearch(dealerships);
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
    
    setupDealershipSettingsSearch(dealerships) {
        const searchInput = document.getElementById('dealershipSettingsSearchInput');
        const searchBtn = document.getElementById('dealershipSettingsSearchBtn');
        const clearBtn = document.getElementById('clearDealershipSettingsSearchBtn');
        const searchInfo = document.getElementById('dealershipSettingsSearchInfo');
        
        if (!searchInput) return;
        
        // Store the original dealership data
        this.originalDealershipSettings = dealerships;
        
        const performSearch = () => {
            const query = searchInput.value.toLowerCase().trim();
            
            if (query === '') {
                // Show all dealerships
                this.filterDealershipSettings('');
                clearBtn.style.display = 'none';
                searchInfo.style.display = 'none';
            } else {
                // Filter dealerships
                this.filterDealershipSettings(query);
                clearBtn.style.display = 'inline-block';
                
                // Show results count
                const filteredCount = this.getFilteredDealershipCount(query);
                searchInfo.style.display = 'block';
                searchInfo.querySelector('.results-count').textContent = 
                    `${filteredCount} dealership${filteredCount !== 1 ? 's' : ''} found`;
            }
        };
        
        // Event listeners
        if (searchInput && !searchInput.hasDealershipSettingsListener) {
            searchInput.addEventListener('input', performSearch);
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            searchInput.hasDealershipSettingsListener = true;
        }
        
        if (searchBtn && !searchBtn.hasDealershipSettingsListener) {
            searchBtn.addEventListener('click', performSearch);
            searchBtn.hasDealershipSettingsListener = true;
        }
        
        if (clearBtn && !clearBtn.hasDealershipSettingsListener) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                performSearch();
            });
            clearBtn.hasDealershipSettingsListener = true;
        }
    }
    
    filterDealershipSettings(query) {
        const cards = document.querySelectorAll('.dealership-settings-card');
        
        cards.forEach(card => {
            const dealerName = card.getAttribute('data-dealer-name') || '';
            const isVisible = query === '' || dealerName.toLowerCase().includes(query);
            
            card.style.display = isVisible ? 'block' : 'none';
        });
    }
    
    getFilteredDealershipCount(query) {
        if (!this.originalDealershipSettings) return 0;
        
        if (query === '') return this.originalDealershipSettings.length;
        
        return this.originalDealershipSettings.filter(dealer => 
            dealer.name.toLowerCase().includes(query)
        ).length;
    }
    
    async toggleDealershipActive(dealershipName, isActive) {
        // Find the dealership card to update UI immediately
        const card = document.querySelector(`[data-dealer-name="${dealershipName}"]`);
        const statusBtn = card?.querySelector('.btn-status');
        
        // Show loading state
        if (statusBtn) {
            const originalContent = statusBtn.innerHTML;
            statusBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            statusBtn.disabled = true;
        }
        
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
                // Update the card's visual state immediately
                this.updateDealershipCardState(dealershipName, isActive);
                
                this.addTerminalMessage(`${dealershipName} ${isActive ? 'activated' : 'deactivated'}`, 'success');
                
                // Refresh the order queue dealerships list to filter disabled ones
                await this.loadOrderQueueDealerships();
            } else {
                this.addTerminalMessage(`Failed to update ${dealershipName}: ${result.error}`, 'error');
                // Reset button state
                if (statusBtn) {
                    statusBtn.innerHTML = `<i class="fas fa-${isActive ? 'unlock' : 'power-off'}"></i> ${isActive ? 'Enable' : 'Disable'}`;
                    statusBtn.disabled = false;
                }
            }
        } catch (error) {
            console.error('Error toggling dealership active state:', error);
            this.addTerminalMessage(`Error updating ${dealershipName}`, 'error');
            // Reset button state
            if (statusBtn) {
                statusBtn.innerHTML = `<i class="fas fa-${isActive ? 'unlock' : 'power-off'}"></i> ${isActive ? 'Enable' : 'Disable'}`;
                statusBtn.disabled = false;
            }
        }
    }
    
    updateDealershipCardState(dealershipName, isActive) {
        const card = document.querySelector(`[data-dealer-name="${dealershipName}"]`);
        if (!card) return;
        
        // Update card classes
        if (isActive) {
            card.classList.remove('disabled');
        } else {
            card.classList.add('disabled');
        }
        
        // Update data attribute
        card.setAttribute('data-is-active', isActive);
        
        // Update status indicator
        const statusIndicator = card.querySelector('.status-indicator');
        if (statusIndicator) {
            if (isActive) {
                statusIndicator.classList.remove('offline');
            } else {
                statusIndicator.classList.add('offline');
            }
        }
        
        // Update status text
        const statusText = card.querySelector('.config-item:first-child');
        if (statusText) {
            statusText.innerHTML = `
                <i class="fas fa-${isActive ? 'check-circle' : 'times-circle'}"></i>
                ${isActive ? 'Active' : 'Disabled'}
            `;
        }
        
        // Update button
        const statusBtn = card.querySelector('.btn-status');
        if (statusBtn) {
            statusBtn.innerHTML = `<i class="fas fa-${isActive ? 'power-off' : 'unlock'}"></i> ${isActive ? 'Disable' : 'Enable'}`;
            statusBtn.onclick = () => this.toggleDealershipActive(dealershipName, !isActive);
            statusBtn.disabled = false;
        }
        
        console.log(`Updated dealership card state: ${dealershipName} is now ${isActive ? 'active' : 'disabled'}`);
    }
    
    async loadOrderQueueDealerships() {
        // Reload the dealership list to apply active/disabled filtering
        try {
            const response = await fetch('/api/dealerships');
            const dealerships = await response.json();
            
            this.dealerships = dealerships;
            await this.renderDealershipList(dealerships);
            
            console.log(`♻️ Refreshed order queue dealerships list - ${dealerships.length} total dealerships loaded`);
            
        } catch (error) {
            console.error('Error refreshing order queue dealerships:', error);
            this.addTerminalMessage(`Error refreshing dealerships list: ${error.message}`, 'error');
        }
    }
    
    async testDealerConnection(dealershipName) {
        console.log(`Testing connection for: ${dealershipName}`);
        
        // Find the button that was clicked to show loading state
        const card = document.querySelector(`[data-dealer-name="${dealershipName}"]`);
        const testBtn = card?.querySelector('.btn-test');
        
        if (testBtn) {
            const originalContent = testBtn.innerHTML;
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
            testBtn.disabled = true;
        }
        
        try {
            const response = await fetch(`/api/test-scraper/${encodeURIComponent(dealershipName)}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`✅ ${dealershipName} connection test successful!`, 'success');
            } else {
                this.showNotification(`❌ ${dealershipName} connection failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Test connection error:', error);
            this.showNotification(`❌ Failed to test ${dealershipName}: ${error.message}`, 'error');
        } finally {
            if (testBtn) {
                testBtn.innerHTML = '<i class="fas fa-play"></i> Test';
                testBtn.disabled = false;
            }
        }
    }

    async editDealershipSettings(dealershipName) {
        console.log(`Editing settings for: ${dealershipName}`);

        try {
            // Get current dealership settings
            const response = await fetch('/api/dealership-settings');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load dealership settings');
            }

            // Find the specific dealership
            const dealership = data.dealerships.find(d => d.name === dealershipName);
            if (!dealership) {
                throw new Error(`Dealership ${dealershipName} not found`);
            }
            
            // Store current dealership for saving later - set BOTH variables
            this.currentEditingDealership = dealership;
            this.currentDealership = dealership.name;  // Set this for saveDealershipSettings function
            
            // Populate and show the modal
            await this.showDealershipModal(dealership);
            
        } catch (error) {
            console.error('Error loading dealership settings:', error);
            this.addTerminalMessage(`Error loading settings: ${error.message}`, 'error');
        }
    }
    
    async showDealershipModal(dealership) {
        // Set modal title
        const modalTitle = document.getElementById('modalTitle');
        if (modalTitle) {
            modalTitle.textContent = dealership.name;
        }
        
        // Get filtering rules
        const filteringRules = dealership.filtering_rules || {};
        
        // Handle exclude_conditions (what's saved) to determine what's checked
        let vehicleTypes;
        if (filteringRules.exclude_conditions) {
            // Convert exclude_conditions to vehicle_types
            // Note: 'po' and 'cpo' are subsets of 'used', so we check for used differently
            vehicleTypes = [];
            
            // If 'new' is NOT in exclude_conditions, then NEW checkbox should be checked
            if (!filteringRules.exclude_conditions.includes('new')) {
                vehicleTypes.push('new');
            }
            
            // For used: it's checked if we're NOT excluding all used types
            // We exclude used if 'used' is in the list OR if both 'po' and 'cpo' are excluded
            // but there's no explicit 'used' (which shouldn't happen with current logic)
            const excludesUsed = filteringRules.exclude_conditions.includes('used');
            const excludesPO = filteringRules.exclude_conditions.includes('po');
            const excludesCPO = filteringRules.exclude_conditions.includes('cpo');
            
            // Used checkbox is checked if we're not excluding used vehicles
            // When only po and cpo are excluded (but not 'used'), it means we want used vehicles
            if (!excludesUsed) {
                vehicleTypes.push('used');
            }
        } else if (filteringRules.vehicle_types) {
            // Fallback to vehicle_types if it exists
            vehicleTypes = filteringRules.vehicle_types;
        } else {
            // Default to both checked
            vehicleTypes = ['new', 'used'];
        }
        
        console.log('Populating modal with vehicle types:', vehicleTypes, 'from rules:', filteringRules);
        
        // Update vehicle type checkboxes
        const newCheckbox = document.getElementById('vehicleNew');
        const usedCheckbox = document.getElementById('vehicleUsed');
        
        if (newCheckbox) newCheckbox.checked = vehicleTypes.includes('new');
        if (usedCheckbox) usedCheckbox.checked = vehicleTypes.includes('used');
        
        // Update order type radio buttons
        const orderType = filteringRules.order_type || 'cao';
        const caoRadio = document.getElementById('orderTypeCao');
        const listRadio = document.getElementById('orderTypeList');
        
        if (caoRadio) caoRadio.checked = (orderType === 'cao');
        if (listRadio) listRadio.checked = (orderType === 'list');
        
        // Update price filters - clear them first, then set if exists
        const minPriceInput = document.getElementById('minPrice');
        const maxPriceInput = document.getElementById('maxPrice');
        const minYearInput = document.getElementById('minYear');
        const seasoningDaysInput = document.getElementById('seasoningDays');
        
        if (minPriceInput) {
            minPriceInput.value = filteringRules.min_price || '';
        }
        if (maxPriceInput) {
            maxPriceInput.value = filteringRules.max_price || '';
        }
        if (minYearInput) {
            minYearInput.value = filteringRules.min_year || '';
        }
        if (seasoningDaysInput) {
            seasoningDaysInput.value = filteringRules.seasoning_days || '';
        }
        
        // Update exclude missing price checkbox
        const excludeMissingPriceCheckbox = document.getElementById('excludeMissingPrice');
        if (excludeMissingPriceCheckbox) {
            excludeMissingPriceCheckbox.checked = filteringRules.exclude_missing_price || false;
        }

        // Set template settings based on output_rules
        const outputRules = dealership.output_rules || {};

        // Set template variant and price markup from output_rules
        const templateVariantSelect = document.getElementById('templateVariant');
        const priceMarkupInput = document.getElementById('priceMarkup');

        if (templateVariantSelect) {
            // Load custom templates from template builder
            await this.loadCustomTemplates(templateVariantSelect, outputRules.template_variant || 'standard');
        }
        if (priceMarkupInput) {
            priceMarkupInput.value = outputRules.price_markup || '';
        }


        // Set custom template selections if they exist
        const customTemplates = outputRules.custom_templates || {};
        const newCustomTemplateSelect = document.getElementById('newVehicleCustomTemplate');
        const usedCustomTemplateSelect = document.getElementById('usedVehicleCustomTemplate');

        if (newCustomTemplateSelect) {
            newCustomTemplateSelect.value = customTemplates.new || '';
        }
        if (usedCustomTemplateSelect) {
            usedCustomTemplateSelect.value = customTemplates.used || '';
        }

        // Show the modal
        const modal = document.getElementById('dealershipModal');
        if (modal) {
            modal.style.display = 'flex'; // Use flex to maintain centering
            modal.classList.add('show');
        }
        
        console.log('Dealership modal opened for:', dealership.name);
    }

    async loadCustomTemplates(templateSelect, currentSelection) {
        try {
            // Fetch custom templates from template builder
            const response = await fetch('/api/templates/list');
            const data = await response.json();

            if (data.success && data.templates) {
                // Get the custom templates optgroup for main dropdown
                const customGroup = document.getElementById('customTemplatesGroup');
                if (customGroup) {
                    // Clear existing custom templates
                    customGroup.innerHTML = '';

                    // Add each custom template as an option
                    data.templates.forEach(template => {
                        const option = document.createElement('option');
                        option.value = `custom_${template.id}`;
                        option.textContent = template.template_name;
                        customGroup.appendChild(option);
                    });

                    console.log(`[TEMPLATE LOADER] Loaded ${data.templates.length} custom templates to main dropdown`);
                }

                // Also populate the vehicle-specific dropdowns
                const newVehicleGroup = document.getElementById('newCustomTemplatesGroup');
                const usedVehicleGroup = document.getElementById('usedCustomTemplatesGroup');

                [newVehicleGroup, usedVehicleGroup].forEach(group => {
                    if (group) {
                        // Clear existing custom templates
                        group.innerHTML = '';

                        // Add each custom template as an option
                        data.templates.forEach(template => {
                            const option = document.createElement('option');
                            option.value = `custom_${template.id}`;
                            option.textContent = template.template_name;
                            group.appendChild(option);
                        });
                    }
                });

                console.log(`[TEMPLATE LOADER] Loaded ${data.templates.length} custom templates to vehicle-specific dropdowns`);
            }

            // Set the current selection after loading templates
            if (templateSelect) {
                templateSelect.value = currentSelection;
            }

        } catch (error) {
            console.error('[TEMPLATE LOADER] Failed to load custom templates:', error);
        }
    }

    async saveDealershipSettingsOLD_DUPLICATE() {
        console.log('saveDealershipSettings (DUPLICATE - should not be called)');
        
        if (!this.currentEditingDealership) {
            this.addTerminalMessage('No dealership selected for editing', 'error');
            return;
        }
        
        try {
            // Get form values
            const newChecked = document.getElementById('vehicleNew')?.checked || false;
            const usedChecked = document.getElementById('vehicleUsed')?.checked || false;
            const minPrice = document.getElementById('minPrice')?.value || '';
            const maxPrice = document.getElementById('maxPrice')?.value || '';
            
            console.log('Form values:', {
                newChecked, usedChecked, minPrice, maxPrice, 
                dealershipId: this.currentEditingDealership.id,
                dealershipName: this.currentEditingDealership.name
            });
            
            // Build vehicle types array
            const vehicleTypes = [];
            if (newChecked) vehicleTypes.push('new');
            if (usedChecked) vehicleTypes.push('used');
            
            // Build filtering rules object
            const filteringRules = {
                vehicle_types: vehicleTypes
            };
            
            console.log('Filtering rules to save:', filteringRules);
            
            if (minPrice) filteringRules.min_price = parseFloat(minPrice);
            if (maxPrice) filteringRules.max_price = parseFloat(maxPrice);
            
            // Send update to backend
            const response = await fetch(`/api/dealership-settings/${this.currentEditingDealership.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filtering_rules: filteringRules
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to save settings');
            }
            
            // Close modal and refresh settings
            this.closeDealershipModal();
            this.loadDealershipSettings();
            this.addTerminalMessage(`Settings saved for ${this.currentEditingDealership.name}`, 'success');
            
        } catch (error) {
            console.error('Error saving dealership settings:', error);
            this.addTerminalMessage(`Error saving settings: ${error.message}`, 'error');
        }
    }
    
    async saveAllDealershipSettings() {
        console.log('Saving all dealership settings...');
        
        try {
            // Collect all dealership setting data from the form
            const dealershipCards = document.querySelectorAll('.dealership-settings-card:not(.disabled)');
            const updates = [];
            
            dealershipCards.forEach(card => {
                const dealershipId = parseInt(card.dataset.dealershipId);
                if (!dealershipId) return;
                
                // Get active toggle setting
                const activeToggle = card.querySelector('.modern-toggle');
                
                // Keep existing filtering rules (will be managed via settings modal)
                const existingDealer = this.dealerships.find(d => d.id === dealershipId);
                const filteringRules = existingDealer?.filtering_rules || {};
                
                updates.push({
                    id: dealershipId,
                    filtering_rules: filteringRules,
                    is_active: activeToggle ? activeToggle.checked : true
                });
            });
            
            if (updates.length === 0) {
                this.addTerminalMessage('No dealership settings to save', 'warning');
                return;
            }
            
            // Send bulk update to backend
            this.addTerminalMessage(`Saving settings for ${updates.length} dealerships...`, 'info');
            
            // Process updates individually since we don't have a true bulk endpoint
            let successCount = 0;
            let errorCount = 0;
            
            for (const update of updates) {
                try {
                    const response = await fetch(`/api/dealership-settings/${update.id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            filtering_rules: update.filtering_rules,
                            is_active: update.is_active
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        successCount++;
                    } else {
                        console.error(`Failed to update dealership ${update.id}:`, data.error);
                        errorCount++;
                    }
                } catch (error) {
                    console.error(`Error updating dealership ${update.id}:`, error);
                    errorCount++;
                }
            }
            
            // Show results
            if (successCount > 0) {
                this.addTerminalMessage(`Successfully saved settings for ${successCount} dealership${successCount !== 1 ? 's' : ''}`, 'success');
            }
            if (errorCount > 0) {
                this.addTerminalMessage(`Failed to save settings for ${errorCount} dealership${errorCount !== 1 ? 's' : ''} - check console for details`, 'error');
            }
            
            // Refresh the settings display
            this.loadDealershipSettings();
            // Refresh order type defaults for queue
            this.loadDealershipDefaults();
            
        } catch (error) {
            console.error('Error saving all dealership settings:', error);
            this.addTerminalMessage(`Error saving dealership settings: ${error.message}`, 'error');
        }
    }
    
    // Quick access to VIN log from dealership panel  
    showDealershipVinLog(dealershipName) {
        console.log('Opening VIN log for dealership:', dealershipName);
        // Use the existing VIN log modal functionality from data tab
        this.openVinLogModal(dealershipName);
    }
    
    closeDealershipModal() {
        const modal = document.getElementById('dealershipModal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('show');
        }
        this.currentEditingDealership = null;
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
            await this.renderDealershipList(dealerships);
            
            this.addTerminalMessage(`Loaded ${dealerships.length} dealerships`, 'success');
            
        } catch (error) {
            console.error('Error loading dealerships:', error);
            this.addTerminalMessage(`Error loading dealerships: ${error.message}`, 'error');
        }
    }
    
    async renderDealershipList(dealerships) {
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
        
        // Load last order dates if not already loaded
        if (!this.lastOrderDates) {
            try {
                const response = await fetch('/api/dealerships/last-orders');
                this.lastOrderDates = await response.json();
                console.log('✅ Loaded last order dates:', this.lastOrderDates);
            } catch (error) {
                console.error('❌ Failed to load last order dates:', error);
                this.lastOrderDates = {}; // Fallback to empty object
            }
        }
        
        try {
            // Filter out disabled dealerships from the queue list
            const activeDealerships = dealerships.filter(dealership => {
                const isActive = dealership.is_active !== false; // Default to active if not specified
                if (!isActive) {
                    console.log(`🚫 Filtered out disabled dealership: ${dealership.name}`);
                }
                return isActive;
            });
            
            console.log(`📊 Dealership filtering results: ${dealerships.length} total, ${activeDealerships.length} active, ${dealerships.length - activeDealerships.length} disabled`);
            
            if (activeDealerships.length === 0) {
                dealershipList.innerHTML = '<div class="loading">No active dealerships available</div>';
                return;
            }
            
            const html = activeDealerships.map(dealership => {
                const dealershipType = this.getDealershipDefault(dealership.name);
                const typeClass = dealershipType.toLowerCase(); // 'cao' or 'list'
                
                // Generate dealer initials for icon
                const initials = dealership.name.split(' ')
                    .map(word => word.charAt(0))
                    .slice(0, 2)
                    .join('')
                    .toUpperCase();
                
                // Get last order date from API data
                const lastOrderDate = this.lastOrderDates[dealership.name] || 'No orders yet';
                
                return `
                    <div class="modern-dealer-panel ${typeClass}" data-dealership="${dealership.name}" draggable="true" tabindex="0" title="Click to add to queue or press Alt+L when focused">
                        <div class="panel-content">
                            <h3 class="dealer-title">${dealership.name}</h3>
                            <div class="panel-details">
                                <div class="detail-row">
                                    <span class="detail-label">Last Order:</span>
                                    <span class="detail-value">${lastOrderDate}</span>
                                </div>
                                <div class="order-type-badge ${typeClass}">
                                    ${dealershipType}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            dealershipList.innerHTML = html;
            console.log('✅ Dealership list rendered successfully');

            // Hide dealerships that are already in the queue
            if (this.processingQueue && this.processingQueue.size > 0) {
                const dealershipItems = dealershipList.querySelectorAll('.modern-dealer-panel');
                dealershipItems.forEach(item => {
                    const dealershipName = item.getAttribute('data-dealership');
                    if (this.processingQueue.has(dealershipName)) {
                        item.style.display = 'none';
                    }
                });
            }
        } catch (error) {
            console.error('❌ Error rendering dealership list:', error);
            dealershipList.innerHTML = '<div class="loading error">Error loading dealerships</div>';
        }

        // Set up event delegation for dealership items
        this.setupDealershipEventListeners();

        // Update filter counts
        this.updateFilterCounts();
    }

    updateFilterCounts() {
        const dealershipList = document.getElementById('dealershipList');
        if (!dealershipList) return;

        const allPanels = dealershipList.querySelectorAll('.modern-dealer-panel');
        const visiblePanels = Array.from(allPanels).filter(panel => panel.style.display !== 'none');

        // Count by type
        const caoPanels = visiblePanels.filter(panel => panel.classList.contains('cao'));
        const listPanels = visiblePanels.filter(panel => panel.classList.contains('list'));

        // Update count displays
        const filterCountAll = document.getElementById('filterCountAll');
        const filterCountCAO = document.getElementById('filterCountCAO');
        const filterCountLIST = document.getElementById('filterCountLIST');

        if (filterCountAll) filterCountAll.textContent = visiblePanels.length;
        if (filterCountCAO) filterCountCAO.textContent = caoPanels.length;
        if (filterCountLIST) filterCountLIST.textContent = listPanels.length;
    }

    filterDealershipsByType(filterType) {
        const dealershipList = document.getElementById('dealershipList');
        if (!dealershipList) return;

        const allPanels = dealershipList.querySelectorAll('.modern-dealer-panel');
        const filterButtons = document.querySelectorAll('.filter-btn');

        // Update active button
        filterButtons.forEach(btn => {
            if (btn.dataset.filter === filterType) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Apply filter
        allPanels.forEach(panel => {
            // Skip panels already hidden because they're in queue
            const isInQueue = this.processingQueue && this.processingQueue.has(panel.getAttribute('data-dealership'));
            if (isInQueue) {
                panel.style.display = 'none';
                return;
            }

            if (filterType === 'all') {
                panel.style.display = '';
            } else if (filterType === 'cao') {
                panel.style.display = panel.classList.contains('cao') ? '' : 'none';
            } else if (filterType === 'list') {
                panel.style.display = panel.classList.contains('list') ? '' : 'none';
            }
        });

        // Update counts after filtering
        this.updateFilterCounts();

        this.addTerminalMessage(`Filtered dealerships: ${filterType.toUpperCase()}`, 'info');
    }

    setupDealershipEventListeners() {
        const dealershipList = document.getElementById('dealershipList');
        if (!dealershipList) return;
        
        // Remove existing listeners to prevent duplicates
        dealershipList.removeEventListener('click', this.dealershipClickHandler);
        
        // Create bound handler function
        this.dealershipClickHandler = (e) => {
            const dealershipItem = e.target.closest('.modern-dealer-panel');
            if (dealershipItem) {
                const dealershipName = dealershipItem.getAttribute('data-dealership');
                if (dealershipName) {
                    this.addDealershipToQueue(dealershipName);
                }
            }
        };
        
        // Add event listener using delegation
        dealershipList.addEventListener('click', this.dealershipClickHandler);

        // Add keyboard navigation for dealership panels
        dealershipList.addEventListener('keydown', (e) => {
            const dealershipItem = e.target.closest('.modern-dealer-panel');
            if (dealershipItem && e.key === 'Enter') {
                e.preventDefault();
                dealershipItem.click();
            }
        });

        // Set up drag and drop event handlers
        this.setupDragAndDrop();
    }
    
    setupDragAndDrop() {
        const dealershipList = document.getElementById('dealershipList');
        const queuePanel = document.getElementById('queueItems');
        
        if (!dealershipList || !queuePanel) return;
        
        // Add dragstart event to all dealership items
        dealershipList.addEventListener('dragstart', (e) => {
            const dealershipItem = e.target.closest('.modern-dealer-panel');
            if (dealershipItem) {
                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('text/plain', dealershipItem.getAttribute('data-dealership'));
                dealershipItem.classList.add('dragging');
                
                // Store the dragged element
                this.draggedDealership = dealershipItem.getAttribute('data-dealership');
            }
        });
        
        // Add dragend event to clean up
        dealershipList.addEventListener('dragend', (e) => {
            const dealershipItem = e.target.closest('.modern-dealer-panel');
            if (dealershipItem) {
                dealershipItem.classList.remove('dragging');
            }
        });
        
        // Set up the queue panel as a drop zone
        queuePanel.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            queuePanel.classList.add('drag-over');
        });
        
        queuePanel.addEventListener('dragleave', (e) => {
            if (e.target === queuePanel || !queuePanel.contains(e.relatedTarget)) {
                queuePanel.classList.remove('drag-over');
            }
        });
        
        queuePanel.addEventListener('drop', (e) => {
            e.preventDefault();
            queuePanel.classList.remove('drag-over');
            
            const dealershipName = e.dataTransfer.getData('text/plain');
            if (dealershipName) {
                this.addDealershipToQueue(dealershipName);
                console.log('✅ Dropped dealership:', dealershipName);
            }
        });
    }
    
    setupDealershipSearchListeners() {
        console.log('🔍 Setting up dealership search listeners...');

        // Wait a bit for DOM to be ready
        setTimeout(() => {
            const searchInput = document.getElementById('dealershipSearchInput');
            const searchBtn = document.getElementById('dealershipSearchBtn');
            const clearBtn = document.getElementById('clearDealershipSearchBtn');
            const dealershipList = document.getElementById('dealershipList');

            console.log('Search elements found:', {
                searchInput: !!searchInput,
                searchBtn: !!searchBtn,
                clearBtn: !!clearBtn,
                dealershipList: !!dealershipList
            });

            if (searchInput) {
                console.log('✅ Search input found, adding listeners');

                // Show dealership list when search input is clicked or focused
                searchInput.addEventListener('focus', () => {
                    if (dealershipList) {
                        dealershipList.style.display = 'block';
                        // Load dealerships if not already loaded
                        if (dealershipList.innerHTML.includes('Loading')) {
                            this.loadDealershipList();
                        }
                    }
                });

                // Hide dealership list when clicking outside
                document.addEventListener('click', (e) => {
                    if (dealershipList &&
                        !searchInput.contains(e.target) &&
                        !dealershipList.contains(e.target) &&
                        !e.target.closest('.dealership-search')) {
                        // Only hide if search is empty
                        if (!searchInput.value.trim()) {
                            dealershipList.style.display = 'none';
                        }
                    }
                });

                // Add fresh listeners (don't try to remove since we don't have references)
                searchInput.addEventListener('input', () => {
                    console.log('🔍 Search input changed:', searchInput.value);
                    // Show list when typing
                    if (dealershipList && searchInput.value.trim()) {
                        dealershipList.style.display = 'block';
                    }
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
        const dealershipItems = dealershipList.querySelectorAll('.modern-dealer-panel');
        
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
            const dealershipName = item.querySelector('.dealer-title');
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
        const dealershipList = document.getElementById('dealershipList');

        if (searchInput) {
            searchInput.value = '';
        }
        if (clearBtn) {
            clearBtn.style.display = 'none';
        }

        // Hide the dealership list when clearing the search
        if (dealershipList) {
            dealershipList.style.display = 'none';
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
        const items = dealershipList ? dealershipList.querySelectorAll('.modern-dealer-panel') : [];
        
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
        // Load order types from dealership settings
        if (this.dealerships) {
            this.dealerships.forEach(dealership => {
                // Get order type from dealership filtering rules, default to 'CAO' if not set
                const orderType = dealership.filtering_rules?.order_type || 'cao';
                // Convert to uppercase for consistency with queue system
                this.dealershipDefaults.set(dealership.name, orderType.toUpperCase());
            });
        }
        
        console.log('Dealership defaults loaded from settings:', Array.from(this.dealershipDefaults.entries()));
        
        // Update any existing queue items to reflect new defaults
        this.updateQueueItemsToDefaults();
    }
    
    updateQueueItemsToDefaults() {
        // Update existing queue items to match their dealership defaults
        let updatedCount = 0;
        this.processingQueue.forEach((item, dealershipName) => {
            const newDefault = this.getDealershipDefault(dealershipName);
            if (item.orderType !== newDefault) {
                item.orderType = newDefault;
                this.processingQueue.set(dealershipName, item);
                updatedCount++;
            }
        });
        
        if (updatedCount > 0) {
            console.log(`Updated ${updatedCount} queue items to match new defaults`);
            this.renderQueue(); // Re-render to show updated selections
        }
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
        // Use the new schedule system instead of hardcoded weeklySchedule
        const dayDealerships = this.currentScheduleSettings?.[day.toLowerCase()] ||
                              window.dealershipSchedule?.[day.toLowerCase()] || [];

        console.log(`🔍 Day ${day} - Found ${dayDealerships.length} dealerships:`, dayDealerships);

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
                console.log(`✅ Added ${dealershipName} to queue with type ${defaultType}`);

                // Hide the dealership from the individual dealerships panel
                const dealershipItems = document.querySelectorAll('.modern-dealer-panel');
                dealershipItems.forEach(item => {
                    if (item.getAttribute('data-dealership') === dealershipName) {
                        item.style.display = 'none';
                    }
                });
            } else {
                console.log(`⚠️ ${dealershipName} already in queue, skipping`);
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
        // Debug logging to identify trigger source
        console.log('🔍 DEBUG: addDealershipToQueue called for:', dealershipName);
        console.trace('Call stack trace:');

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

        // Remove the dealership item from the list when added to queue
        const dealershipItems = document.querySelectorAll('.modern-dealer-panel');
        dealershipItems.forEach(item => {
            if (item.getAttribute('data-dealership') === dealershipName) {
                item.style.display = 'none';
            }
        });
    }
    
    removeDealershipFromQueue(dealershipName) {
        if (this.processingQueue.has(dealershipName)) {
            this.processingQueue.delete(dealershipName);
            this.renderQueue();
            this.addTerminalMessage(`Removed ${dealershipName} from queue`, 'success');

            // Show the dealership item back in the list
            const dealershipItems = document.querySelectorAll('.modern-dealer-panel');
            dealershipItems.forEach(item => {
                if (item.getAttribute('data-dealership') === dealershipName) {
                    item.style.display = '';
                }
            });
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
        const queueToolbar = document.getElementById('queueToolbar');
        const queueCountDisplay = document.getElementById('queueCountDisplay');

        if (!queueItems) return;

        // Update toolbar visibility and count
        if (queueToolbar) {
            if (this.processingQueue.size > 0) {
                queueToolbar.style.display = 'flex';
                if (queueCountDisplay) {
                    queueCountDisplay.textContent = this.processingQueue.size;
                }
            } else {
                queueToolbar.style.display = 'none';
            }
        }

        if (this.processingQueue.size === 0) {
            // Get today's day name for smart suggestion
            const today = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][new Date().getDay()];
            const todaySchedule = this.currentScheduleSettings?.[today] || [];

            queueItems.innerHTML = `
                <div class="empty-queue">
                    <div class="empty-icon">
                        <i class="fas fa-clipboard-list"></i>
                    </div>
                    <h4>Queue is Empty</h4>
                    <p class="empty-subtitle">Add dealerships to begin processing</p>

                    <div class="quick-actions">
                        ${todaySchedule.length > 0 ? `
                            <button class="quick-action-btn primary" onclick="app.addDayToQueue('${today}')">
                                <i class="fas fa-calendar-day"></i>
                                Add Today's Schedule (${todaySchedule.length})
                            </button>
                        ` : ''}
                        <button class="quick-action-btn secondary" onclick="document.getElementById('dealershipSearchInput').focus()">
                            <i class="fas fa-search"></i>
                            Search Dealerships
                        </button>
                    </div>

                    <div class="empty-help">
                        <p><strong>How to add dealerships:</strong></p>
                        <ul>
                            <li>Click a day button (MON-FRI) to add scheduled dealerships</li>
                            <li>Click individual dealership cards below</li>
                            <li>Drag and drop dealerships to the queue</li>
                        </ul>
                    </div>
                </div>
            `;
            if (processBtn) {
                processBtn.disabled = true;
                processBtn.innerHTML = `
                    <i class="fas fa-play"></i>
                    Process Queue (0)
                `;
            }
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
                        <button class="delete-btn" onclick="app.removeDealershipFromQueue(\`${item.name}\`)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="order-type-selection">
                    <div class="order-type-option cao">
                        <input type="radio" name="orderType_${item.name.replace(/\s+/g, '_')}"
                               value="CAO" ${item.orderType === 'CAO' ? 'checked' : ''}
                               onchange="app.updateQueueItemOrderType(\`${item.name}\`, 'CAO')">
                        <label>CAO (Automatic)</label>
                    </div>
                    <div class="order-type-option list">
                        <input type="radio" name="orderType_${item.name.replace(/\s+/g, '_')}"
                               value="LIST" ${item.orderType === 'LIST' ? 'checked' : ''}
                               onchange="app.updateQueueItemOrderType(\`${item.name}\`, 'LIST')">
                        <label>List (VIN Entry)</label>
                    </div>
                    <div class="order-type-option maintenance">
                        <input type="radio" name="orderType_${item.name.replace(/\s+/g, '_')}"
                               value="MAINTENANCE" ${item.orderType === 'MAINTENANCE' ? 'checked' : ''}
                               onchange="app.updateQueueItemOrderType(\`${item.name}\`, 'MAINTENANCE')">
                        <label>Maintenance</label>
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
        console.log('🧹 DEBUG: clearQueue called - clearing', this.processingQueue.size, 'items');
        console.trace('Clear queue call stack:');
        this.processingQueue.clear();
        this.renderQueue();
        this.addTerminalMessage('Queue cleared', 'success');

        // Show all dealership items back in the list
        const dealershipItems = document.querySelectorAll('.modern-dealer-panel');
        dealershipItems.forEach(item => {
            item.style.display = '';
        });

        // Update filter counts after clearing queue
        if (this.updateFilterCounts) {
            this.updateFilterCounts();
        }
    }

    setAllQueueItems(orderType) {
        if (this.processingQueue.size === 0) {
            this.addTerminalMessage('Queue is empty', 'warning');
            return;
        }

        let updateCount = 0;
        this.processingQueue.forEach((item, dealershipName) => {
            if (item.orderType !== orderType) {
                item.orderType = orderType;
                this.processingQueue.set(dealershipName, item);
                updateCount++;
            }
        });

        this.renderQueue();
        this.addTerminalMessage(`Set ${updateCount} items to ${orderType}`, 'success');
    }

    launchOrderWizard() {
        if (this.processingQueue.size === 0) {
            this.addTerminalMessage('No dealerships in queue to process', 'warning');
            return;
        }

        // Launch order wizard directly (production mode)
        this.openOrderWizard();
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
            
            // Check wizard mode toggle (default to modal wizard when checked)
            const toggleElement = document.getElementById('useModalWizard');
            const useModalWizard = toggleElement ? toggleElement.checked : true;
            
            if (useModalWizard) {
                // Open wizard modal
                this.showModal('orderWizardModal');
                
                // Always create a fresh modal wizard instance to prevent state persistence issues
                window.modalWizard = new ModalOrderWizard();
                
                window.modalWizard.initializeFromQueue(queueData);
                this.addTerminalMessage(`Launched modal wizard for ${this.processingQueue.size} dealerships`, 'success');
                
            } else {
                // Open wizard in new tab (original behavior)
                const timestamp = new Date().getTime();
                const wizardWindow = window.open(`/order-wizard?v=${timestamp}`, '_blank');
                
                if (!wizardWindow) {
                    this.addTerminalMessage('Popup blocked! Using modal wizard instead...', 'warning');
                    // Fallback to modal
                    this.showModal('orderWizardModal');
                    if (typeof window.modalWizard === 'undefined') {
                        window.modalWizard = new ModalOrderWizard();
                    }
                    window.modalWizard.initializeFromQueue(queueData);
                    return;
                }
                
                this.addTerminalMessage(`Launched standalone wizard for ${this.processingQueue.size} dealerships`, 'success');
            }
            
            // Queue will be cleared when modal wizard completes successfully
            // No longer clearing automatically to prevent premature clearing
            
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
        // Handle sub-tab switching - remove existing listeners first
        document.querySelectorAll('.sub-tab-button').forEach(button => {
            // Clone the button to remove all event listeners
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
        });
        
        // Add fresh event listeners
        document.querySelectorAll('.sub-tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const subtab = e.currentTarget.dataset.subtab;
                console.log('Sub-tab clicked:', subtab);
                this.switchSubTab(subtab);
            });
        });
    }
    
    switchSubTab(subtabName) {
        console.log('Switching to sub-tab:', subtabName);
        
        // Update sub-tab buttons
        document.querySelectorAll('.sub-tab-button').forEach(button => {
            button.classList.remove('active');
        });
        const activeButton = document.querySelector(`[data-subtab="${subtabName}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
        
        // Update sub-tab panels
        document.querySelectorAll('.sub-tab-panel').forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none';
        });
        const activePanel = document.getElementById(`${subtabName}-panel`);
        console.log('Active panel ID:', `${subtabName}-panel`, 'Found:', !!activePanel);
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
        console.log('Loading content for sub-tab:', subtabName);
        if (subtabName === 'vin-history') {
            this.loadDealershipVinLogs();
        } else if (subtabName === 'scraper-view') {
            this.loadScraperHistory();
            this.setupCsvImport();
        } else if (subtabName === 'scraper-data') {
            console.log('Loading scraper data for Order Queue tab');
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                this.loadScraperHistory();
                this.setupCsvImport();
            }, 100);
        } else if (subtabName === 'order-queue') {
            console.log('Setting up order queue dealership search...');
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                this.setupDealershipSearchListeners();
            }, 100);
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

    // Alias for showToast to maintain compatibility
    showNotification(message, type = 'info') {
        return this.showToast(message, type);
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
                        <th class="filterable-header" data-field="normalized_type">
                            <div class="header-content">
                                <span>Norm Type</span>
                                <div class="filter-dropdown" id="normalizedTypeFilter">
                                    <select class="header-filter" data-field="normalized_type">
                                        <option value="">All</option>
                                        <option value="new">New</option>
                                        <option value="po">Pre-Owned</option>
                                        <option value="cpo">CPO</option>
                                    </select>
                                </div>
                            </div>
                        </th>
                        <th class="filterable-header" data-field="on_lot_status">
                            <div class="header-content">
                                <span>On Lot Status</span>
                                <div class="filter-dropdown" id="onLotStatusFilter">
                                    <select class="header-filter" data-field="on_lot_status">
                                        <option value="">All</option>
                                        <option value="onlot">On Lot</option>
                                        <option value="offlot">Off Lot</option>
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
            // Add cache-busting timestamp to force fresh data
            const timestamp = new Date().getTime();
            const response = await fetch(`/api/dealership-vin-logs?_cb=${timestamp}`, {
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
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

        container.innerHTML = dealerships.map(dealer => {
            // Escape dealership name for safe use in onclick handlers
            const escapedDealerName = dealer.dealership_name.replace(/'/g, "\\'");
            
            return `
            <div class="dealership-card" data-dealer="${dealer.dealership_name}">
                <div class="dealership-card-header">
                    <h3 class="dealership-name">${this.formatDealershipName(dealer.dealership_name)}</h3>
                    <i class="fas fa-building dealership-icon"></i>
                </div>
                
                <div class="dealership-stats">
                    <div class="stat-item">
                        <div class="stat-value">${dealer.total_vins || dealer.vin_count || 0}</div>
                        <div class="stat-label">Total VINs</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${this.formatLastUpdated(dealer.last_updated)}</div>
                        <div class="stat-label">Last Updated</div>
                    </div>
                </div>
                
                <div class="table-info">
                    <div class="table-name">
                        <i class="fas fa-database"></i>
                        <span>${dealer.table_name}</span>
                    </div>
                </div>
                
                <div class="dealership-actions">
                    <button class="btn-view-vin-log" onclick="app.openVinLogModal('${escapedDealerName}')">
                        <i class="fas fa-eye"></i>
                        View VIN Log
                    </button>
                </div>
            </div>
            `;
        }).join('');

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
        console.log('setupVinLogModalEvents called');
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
        console.log('Setup updateVinLogBtn:', !!updateVinLogBtn, 'hasListener:', updateVinLogBtn?.hasEventListener);
        if (updateVinLogBtn && !updateVinLogBtn.hasEventListener) {
            updateVinLogBtn.addEventListener('click', () => {
                console.log('Update VIN Log button clicked');
                this.openVinLogUpdateModal();
            });
            updateVinLogBtn.hasEventListener = true;
            console.log('Update VIN Log button event listener attached');
        }

        // Remove Order Group button
        const removeOrderGroupBtn = document.getElementById('removeOrderGroupBtn');
        console.log('Setup removeOrderGroupBtn:', !!removeOrderGroupBtn, 'hasListener:', removeOrderGroupBtn?.hasEventListener);
        if (removeOrderGroupBtn && !removeOrderGroupBtn.hasEventListener) {
            removeOrderGroupBtn.addEventListener('click', () => {
                console.log('Remove Order Group button clicked');
                this.showOrderGroupSelectionModal();
            });
            removeOrderGroupBtn.hasEventListener = true;
            console.log('Remove Order Group button event listener attached');
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
    
    formatLastUpdated(dateString) {
        if (!dateString) return 'Never';
        
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0 || diffDays === 1) {
                return 'Today';
            } else if (diffDays === 2) {
                return 'Yesterday';
            } else if (diffDays <= 7) {
                return `${diffDays-1} days ago`;
            } else if (diffDays <= 30) {
                return `${Math.floor(diffDays/7)} weeks ago`;
            } else {
                // Format as short date for older dates
                return date.toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric',
                    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
                });
            }
        } catch (error) {
            return 'Invalid Date';
        }
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
        console.log('Loading scraper history...');
        
        // Check which container to use based on current tab
        let container = document.getElementById('queueScraperTableContainer');
        if (!container || !container.offsetParent) {
            // If queue container doesn't exist or isn't visible, try the analytics one
            container = document.getElementById('scraperTableContainer');
        }
        
        if (!container) {
            console.error('Scraper table container not found');
            return;
        }
        
        console.log('Using container:', container.id);
        
        // Show loading state
        container.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                Loading scraper history...
            </div>
        `;
        
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
        // Check which container to use based on current tab
        let container = document.getElementById('queueScraperTableContainer');
        if (!container || !container.offsetParent) {
            // If queue container doesn't exist or isn't visible, try the analytics one
            container = document.getElementById('scraperTableContainer');
        }
        
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
                        <th>Actions</th>
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
                            <td>
                                <button class="btn-delete-import" 
                                        onclick="event.stopPropagation(); app.deleteScraperImport(${import_.import_id}, '${import_.status}')"
                                        title="${import_.status === 'active' ? 'Cannot delete active import' : 'Delete this import'}"
                                        ${import_.status === 'active' ? 'disabled' : ''}
                                        style="background: transparent; border: none; color: ${import_.status === 'active' ? 'var(--theme-text-secondary, #999)' : 'var(--danger-red, #ff4444)'}; cursor: ${import_.status === 'active' ? 'not-allowed' : 'pointer'}; padding: 5px; opacity: ${import_.status === 'active' ? '0.5' : '1'};">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
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
        // Check which container to use based on current tab
        let container = document.getElementById('queueScraperTableContainer');
        if (!container || !container.offsetParent) {
            // If queue container doesn't exist or isn't visible, try the analytics one
            container = document.getElementById('scraperTableContainer');
        }
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
    
    async deleteScraperImport(importId, status) {
        // Prevent deletion of active imports
        if (status === 'active') {
            this.addTerminalMessage('Cannot delete the active import. Please run a new scraper import to archive this one first.', 'error');
            return;
        }
        
        // Show confirmation dialog with warning
        const confirmed = confirm(
            `WARNING: This will permanently delete Import #${importId} and all associated vehicle data.\n\n` +
            `This action cannot be undone.\n\n` +
            `Are you sure you want to delete this import?`
        );
        
        if (!confirmed) {
            return;
        }
        
        // Double confirmation for safety
        const doubleConfirmed = confirm(
            `FINAL CONFIRMATION\n\n` +
            `Delete Import #${importId}?\n\n` +
            `Click OK to permanently delete this import.`
        );
        
        if (!doubleConfirmed) {
            return;
        }
        
        try {
            // Show loading state
            this.addTerminalMessage(`Deleting Import #${importId}...`, 'info');
            
            const response = await fetch(`/api/scraper-imports/${importId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`SUCCESS: Import #${importId} and all associated data deleted successfully`, 'success');
                
                // Reload the scraper history to reflect the deletion
                this.loadScraperHistory();
                
                // Also refresh the data management counts if they exist
                this.refreshDataManagementCounts();
                
            } else {
                this.addTerminalMessage(`FAILED to delete import: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting scraper import:', error);
            this.addTerminalMessage(`ERROR deleting import: ${error.message}`, 'error');
        }
    }
    
    refreshDataManagementCounts() {
        // Refresh any count displays after deletion
        try {
            // Update scraper import count if it exists
            const importCountElement = document.querySelector('.import-count, #scraperImportCount');
            if (importCountElement) {
                // Re-fetch the actual count from the current table
                const tableRows = document.querySelectorAll('#scraperTableContainer tbody tr');
                if (tableRows) {
                    importCountElement.textContent = tableRows.length;
                }
            }
        } catch (error) {
            console.log('Note: Could not refresh data management counts:', error.message);
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
        
        // Initialize toggle state (default to normalized/checked)
        const toggle = document.getElementById('dataTypeToggle');
        const labels = document.querySelectorAll('.data-type-toggle-container .toggle-label');
        
        if (toggle) {
            toggle.checked = true; // Default to normalized
        }
        
        // Update label states
        labels.forEach((label, index) => {
            if (index === 0) {
                // Raw label
                label.classList.remove('active');
            } else {
                // Normalized label
                label.classList.add('active');
            }
        });
        
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
        
        // Setup data type toggle functionality
        const dataTypeToggle = document.getElementById('dataTypeToggle');
        if (dataTypeToggle && !dataTypeToggle.hasEventListener) {
            dataTypeToggle.addEventListener('change', () => this.toggleDataType());
            dataTypeToggle.hasEventListener = true;
        }
    }
    
    closeScraperDataModal() {
        const modal = document.getElementById('scraperDataModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    toggleDataType() {
        const toggle = document.getElementById('dataTypeToggle');
        const labels = document.querySelectorAll('.data-type-toggle-container .toggle-label');
        
        if (!toggle) return;
        
        const isNormalized = toggle.checked;
        
        // Update label active states
        labels.forEach((label, index) => {
            if (index === 0) {
                // Raw label
                label.classList.toggle('active', !isNormalized);
            } else {
                // Normalized label  
                label.classList.toggle('active', isNormalized);
            }
        });
        
        // Re-render the modal with the selected data type
        this.renderScraperDataModal();
    }
    
    async loadScraperData(importId) {
        try {
            // Show loading state
            const tableContainer = document.getElementById('scraperDataTableContainer');
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="loading-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        <h3>Loading Vehicle Data...</h3>
                        <p>Loading all vehicles from import #${importId}</p>
                    </div>
                `;
            }
            
            // Load normalized data - request ALL vehicles (not just 50)
            const response = await fetch(`/api/scraper-imports/${importId}/vehicles?per_page=10000`);
            const data = await response.json();
            
            if (data.success) {
                // Store the data
                this.currentScraperData = data;
                this.currentFilteredScraperData = data.vehicles || [];
                
                console.log(`Loaded ${data.vehicles?.length || 0} vehicles out of ${data.total || 0} total`);
                
                // If we didn't get all vehicles, try to get more
                if (data.total && data.vehicles && data.vehicles.length < data.total) {
                    console.warn(`Only loaded ${data.vehicles.length}/${data.total} vehicles. Consider increasing per_page limit.`);
                }
                
                // For now, simulate raw data by using the same data with different structure
                // In production, this would come from a separate raw data endpoint
                this.currentScraperData.raw_vehicles = this.simulateRawData(data.vehicles || []);
                
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
    
    // Simulate raw data for demonstration (in production this would come from actual raw data)
    simulateRawData(normalizedVehicles) {
        return normalizedVehicles.map(vehicle => {
            // Create a "raw" version matching the actual raw_vehicle_data schema
            const rawVehicle = {};
            
            // CRITICAL FIELDS FIRST - Stock Number and Status (matching database names)
            if (vehicle.stock_number || vehicle.stock) rawVehicle.stock = vehicle.stock_number || vehicle.stock;
            if (vehicle.status) rawVehicle.status = vehicle.status;
            
            // Core vehicle identification (matching database field names)
            if (vehicle.vin) rawVehicle.vin = vehicle.vin;
            if (vehicle.year) rawVehicle.year = vehicle.year;
            if (vehicle.make) rawVehicle.make = vehicle.make;
            if (vehicle.model) rawVehicle.model = vehicle.model;
            if (vehicle.trim) rawVehicle.trim = vehicle.trim;
            
            // Vehicle details (matching database schema)
            if (vehicle.ext_color || vehicle.color) rawVehicle.ext_color = vehicle.ext_color || vehicle.color;
            if (vehicle.body_style) rawVehicle.body_style = vehicle.body_style;
            if (vehicle.fuel_type) rawVehicle.fuel_type = vehicle.fuel_type;
            
            // Pricing information
            if (vehicle.price) rawVehicle.price = vehicle.price;
            if (vehicle.msrp) rawVehicle.msrp = vehicle.msrp;
            
            // Inventory classification
            if (vehicle.type) rawVehicle.type = vehicle.type;
            if (vehicle.normalized_type) rawVehicle.normalized_type = vehicle.normalized_type;
            if (vehicle.on_lot_status) rawVehicle.on_lot_status = vehicle.on_lot_status;
            
            // Location information
            if (vehicle.location) rawVehicle.location = vehicle.location;
            if (vehicle.street_address) rawVehicle.street_address = vehicle.street_address;
            if (vehicle.locality) rawVehicle.locality = vehicle.locality;
            if (vehicle.region) rawVehicle.region = vehicle.region;
            if (vehicle.postal_code) rawVehicle.postal_code = vehicle.postal_code;
            if (vehicle.country) rawVehicle.country = vehicle.country;
            
            // Scraping metadata (crucial for raw view)
            if (vehicle.vehicle_url) rawVehicle.vehicle_url = vehicle.vehicle_url;
            if (vehicle.import_date) rawVehicle.import_date = vehicle.import_date;
            if (vehicle.import_timestamp) rawVehicle.import_timestamp = vehicle.import_timestamp;
            if (vehicle.time_scraped) rawVehicle.time_scraped = vehicle.time_scraped;
            if (vehicle.date_in_stock) rawVehicle.date_in_stock = vehicle.date_in_stock;
            if (vehicle.import_id) rawVehicle.import_id = vehicle.import_id;
            if (vehicle.is_archived !== undefined) rawVehicle.is_archived = vehicle.is_archived;
            
            // Add ID field
            if (vehicle.id) rawVehicle.id = vehicle.id;
            
            return rawVehicle;
        });
    }
    
    renderScraperDataModal(data = null) {
        const displayData = data || this.currentScraperData;
        const toggle = document.getElementById('dataTypeToggle');
        const isNormalized = toggle ? toggle.checked : true;
        
        // Choose data source based on toggle state
        let vehicleData;
        if (isNormalized) {
            // Use normalized data (current filtered data)
            vehicleData = this.currentFilteredScraperData || displayData?.vehicles || [];
        } else {
            // Use raw data (original scraped data without normalization)
            vehicleData = this.currentScraperData?.raw_vehicles || this.currentFilteredScraperData || displayData?.vehicles || [];
        }
        
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
            const dataTypeText = isNormalized ? 'normalized' : 'raw';
            tableContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No ${dataTypeText.charAt(0).toUpperCase() + dataTypeText.slice(1)} Data Found</h3>
                    <p>No ${dataTypeText} vehicle data found in this import.</p>
                </div>
            `;
            return;
        }
        
        // Get column headers from first vehicle and prioritize VIN first
        const firstVehicle = vehicleData[0];
        const allHeaders = Object.keys(firstVehicle);
        
        // Prioritize columns: VIN first, then stock, status, then others
        const priorityHeaders = ['vin', 'vehicle_vin', 'stock', 'stock_number', 'status', 'inventory_status'];
        const headers = [];
        
        // Add priority headers first (if they exist)
        priorityHeaders.forEach(priority => {
            const found = allHeaders.find(header => 
                header.toLowerCase() === priority || 
                header.toLowerCase().includes(priority.replace('_', ''))
            );
            if (found && !headers.includes(found)) {
                headers.push(found);
            }
        });
        
        // Add remaining headers
        allHeaders.forEach(header => {
            if (!headers.includes(header)) {
                headers.push(header);
            }
        });
        
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
        if (!this.currentScraperData) return;
        
        const searchInput = document.getElementById('scraperDataSearch');
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const toggle = document.getElementById('dataTypeToggle');
        const isNormalized = toggle ? toggle.checked : true;
        
        // Choose base dataset based on toggle state
        let baseData;
        if (isNormalized) {
            baseData = this.currentScraperData.vehicles || [];
        } else {
            baseData = this.currentScraperData.raw_vehicles || [];
        }
        
        let filteredData = baseData;
        
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
        
        if ((header === 'vin' || header === 'vehicle_vin') && value) {
            return `<span class="vin-number">${value}</span>`;
        }
        
        if ((header === 'stock' || header === 'stock_number' || header === 'dealer_stock_num') && value) {
            return `<strong>${value}</strong>`;
        }
        
        if ((header === 'status' || header === 'inventory_status') && value) {
            return `<span class="status-badge status-${value.toLowerCase().replace(' ', '-')}">${value}</span>`;
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
        console.log('Setting up CSV import...');
        const selectBtn = document.getElementById('selectCsvBtn');
        const importBtn = document.getElementById('importCsvBtn');
        const fileInput = document.getElementById('csvFileInput');
        
        // Setup refresh button for scraper history
        const refreshBtn = document.getElementById('refreshScraperHistory');
        if (refreshBtn && !refreshBtn.hasEventListener) {
            console.log('Adding refresh button listener');
            refreshBtn.addEventListener('click', () => {
                console.log('Refresh button clicked');
                this.loadScraperHistory();
            });
            refreshBtn.hasEventListener = true;
        }
        
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
        try {
            console.log('openVinLogUpdateModal called');
            console.log('currentDealership:', this.currentDealership);
            
            if (!this.currentDealership) {
                console.log('Error: No dealership selected');
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
            
        } catch (error) {
            console.error('Error in openVinLogUpdateModal:', error);
            this.addTerminalMessage(`Error opening VIN log update modal: ${error.message}`, 'error');
            return;
        }
        
        // CLEAR TEXTAREA FOR NEW DEALERSHIP (fix persistence issue)
        const textarea = document.getElementById('manualOrderEntry');
        if (textarea) {
            textarea.value = '';
            console.log('Cleared textarea for new dealership:', this.currentDealership);
        }
        
        // Show the modal
        const modal = document.getElementById('vinLogUpdateModal');
        console.log('vinLogUpdateModal element found:', !!modal);
        
        if (modal) {
            console.log('Showing VIN log update modal');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            
            // AUTOMATICALLY FIX IMPORT MANUAL VINS BUTTON VISIBILITY
            setTimeout(() => {
                console.log('🔧 AUTO-FIXING: Import Manual VINs button visibility...');
                if (window.forceManualButtonVisible) {
                    const success = window.forceManualButtonVisible();
                    console.log('✅ Auto-fix result:', success ? 'SUCCESS' : 'FAILED');
                } else {
                    console.error('❌ forceManualButtonVisible function not found');
                }
            }, 100);
            
            // AUTO-SWITCH TO MANUAL ENTRY TAB for better UX
            setTimeout(() => {
                this.switchToManualMode();
            }, 100);
        } else {
            console.error('vinLogUpdateModal element not found in DOM');
            this.addTerminalMessage('VIN log update modal not found in DOM', 'error');
        }
    }
    
    setupVinLogModalEventHandlers() {
        // DEDICATED MODAL EVENT BINDING - Called every time modal opens
        console.log('=== SETTING UP VIN LOG MODAL EVENT HANDLERS ===');
        
        // 1. Tab switching events
        const csvImportTab = document.getElementById('csvImportTab');
        const manualEntryTab = document.getElementById('manualEntryTab');
        
        if (csvImportTab) {
            // Remove existing listeners and add fresh ones
            csvImportTab.replaceWith(csvImportTab.cloneNode(true));
            const newCsvTab = document.getElementById('csvImportTab');
            newCsvTab.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('=== CSV TAB CLICKED ===');
                this.switchToCSVMode();
            });
        }
        
        if (manualEntryTab) {
            // Remove existing listeners and add fresh ones  
            manualEntryTab.replaceWith(manualEntryTab.cloneNode(true));
            const newManualTab = document.getElementById('manualEntryTab');
            newManualTab.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('=== MANUAL TAB CLICKED ===');
                this.switchToManualMode();
            });
        }
        
        // 2. Manual entry textarea monitoring
        const textarea = document.getElementById('manualOrderEntry');
        if (textarea) {
            textarea.replaceWith(textarea.cloneNode(true));
            const newTextarea = document.getElementById('manualOrderEntry');
            newTextarea.addEventListener('input', () => {
                console.log('=== TEXTAREA INPUT DETECTED ===');
                this.updateManualEntryStats();
                this.updateImportButtonState();
            });
        }
        
        // 3. Import button events
        const importBtn = document.getElementById('startVinLogImport');
        if (importBtn) {
            importBtn.replaceWith(importBtn.cloneNode(true));
            const newImportBtn = document.getElementById('startVinLogImport');
            newImportBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('=== IMPORT BUTTON CLICKED ===');
                this.handleImportButtonClick();
            });
        }
        
        // 4. Validate button event
        const validateBtn = document.getElementById('validateManualEntry');
        if (validateBtn) {
            validateBtn.replaceWith(validateBtn.cloneNode(true));
            const newValidateBtn = document.getElementById('validateManualEntry');
            newValidateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('=== VALIDATE BUTTON CLICKED ===');
                this.validateManualEntryFormat();
            });
        }
        
        console.log('=== MODAL EVENT HANDLERS SETUP COMPLETE ===');
    }
    
    switchToCSVMode() {
        console.log('Switching to CSV mode');
        const csvTab = document.getElementById('csvImportTab');
        const manualTab = document.getElementById('manualEntryTab');
        const csvSection = document.getElementById('csvImportSection');
        const manualSection = document.getElementById('manualEntrySection');
        
        if (csvTab) csvTab.classList.add('active');
        if (manualTab) manualTab.classList.remove('active');
        if (csvSection) csvSection.style.display = 'block';
        if (manualSection) manualSection.style.display = 'none';
        
        this.currentImportMethod = 'csv';
        this.updateImportButtonState();
    }
    
    switchToManualMode() {
        console.log('Switching to Manual Entry mode');
        const csvTab = document.getElementById('csvImportTab');
        const manualTab = document.getElementById('manualEntryTab');
        const csvSection = document.getElementById('csvImportSection');
        const manualSection = document.getElementById('manualEntrySection');
        
        if (csvTab) csvTab.classList.remove('active');
        if (manualTab) manualTab.classList.add('active');
        if (csvSection) csvSection.style.display = 'none';
        if (manualSection) manualSection.style.display = 'block';
        
        this.currentImportMethod = 'manual';
        this.updateImportButtonState();
        this.updateManualEntryStats();
    }
    
    updateImportButtonState() {
        const importBtn = document.getElementById('startVinLogImport');
        const importButtonText = document.getElementById('importButtonText');
        const importButtonIcon = document.getElementById('importButtonIcon');
        
        if (!importBtn) return;
        
        if (this.currentImportMethod === 'manual') {
            const textarea = document.getElementById('manualOrderEntry');
            const hasContent = textarea && textarea.value.trim().length > 0;
            
            importBtn.disabled = !hasContent;
            if (importButtonText) importButtonText.textContent = 'Import Manual VINs';
            if (importButtonIcon) importButtonIcon.className = 'fas fa-keyboard';
            
            console.log('Manual mode button state:', { hasContent, disabled: !hasContent });
        } else {
            importBtn.disabled = !this.selectedVinLogFile;
            if (importButtonText) importButtonText.textContent = 'Import CSV';
            if (importButtonIcon) importButtonIcon.className = 'fas fa-upload';
            
            console.log('CSV mode button state:', { hasFile: !!this.selectedVinLogFile, disabled: !this.selectedVinLogFile });
        }
    }
    
    handleImportButtonClick() {
        if (this.currentImportMethod === 'manual') {
            console.log('Processing manual VIN import');
            this.processManualVinEntry();
        } else {
            console.log('Processing CSV import');
            this.startVinLogImport();
        }
    }
    
    validateManualEntryFormat() {
        console.log('=== VALIDATE BUTTON CLICKED ===');
        const textarea = document.getElementById('manualOrderEntry');
        if (!textarea) {
            console.error('Manual entry textarea not found');
            alert('Error: Cannot find textarea element');
            return;
        }
        
        const text = textarea.value.trim();
        console.log('Textarea content:', text);
        
        if (!text) {
            alert('Please enter some VIN data to validate');
            return;
        }
        
        // Simple validation - count orders and VINs
        const lines = text.split('\n').map(line => line.trim()).filter(line => line);
        let orders = 0;
        let vins = 0;
        let errors = [];
        
        console.log('Processing lines:', lines);
        
        for (let line of lines) {
            if (line.length === 17 && /^[A-HJ-NPR-Z0-9]+$/i.test(line)) {
                vins++;
                console.log('Found VIN:', line);
            } else if (line.length > 0 && line.length < 17) {
                orders++;
                console.log('Found Order:', line);
            } else if (line.length > 17) {
                errors.push(`Line too long: ${line.substring(0, 20)}...`);
            }
        }
        
        const message = `Validation Results:\n• Orders: ${orders}\n• VINs: ${vins}\n• Errors: ${errors.length}`;
        console.log('Validation results:', { orders, vins, errors: errors.length });
        
        if (errors.length > 0) {
            alert(message + '\n\nErrors:\n' + errors.slice(0, 5).join('\n'));
        } else {
            alert(message + '\n\n✅ Format looks good!');
        }
    }
    
    clearManualEntry() {
        console.log('=== CLEAR BUTTON CLICKED ===');
        const textarea = document.getElementById('manualOrderEntry');
        if (textarea) {
            textarea.value = '';
            console.log('Textarea cleared');
            this.updateManualEntryStats();
            this.updateImportButtonState();
        } else {
            console.error('Cannot find textarea to clear');
        }
    }
    
    setupVinLogUpdateEvents() {
        // Initialize manual entry functionality for this modal instance - inline approach
        console.log('Setting up VIN log update events including manual entry tabs');
        
        // Set up tab switching directly
        const csvImportTab = document.getElementById('csvImportTab');
        const manualEntryTab = document.getElementById('manualEntryTab');
        
        console.log('Manual entry tabs found:', {
            csvImportTab: !!csvImportTab,
            manualEntryTab: !!manualEntryTab
        });
        
        if (csvImportTab) {
            csvImportTab.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('CSV Import tab clicked - switching to CSV mode');
                
                // Switch tabs
                csvImportTab.classList.add('active');
                manualEntryTab?.classList.remove('active');
                
                // Show/hide sections
                const csvSection = document.getElementById('csvImportSection');
                const manualSection = document.getElementById('manualEntrySection');
                if (csvSection) csvSection.style.display = 'block';
                if (manualSection) manualSection.style.display = 'none';
                
                console.log('Switched to CSV mode');
            });
        }
        
        if (manualEntryTab) {
            manualEntryTab.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Manual Entry tab clicked - switching to manual mode');
                
                // Switch tabs
                manualEntryTab.classList.add('active');
                csvImportTab?.classList.remove('active');
                
                // Show/hide sections
                const csvSection = document.getElementById('csvImportSection');
                const manualSection = document.getElementById('manualEntrySection');
                if (csvSection) csvSection.style.display = 'none';
                if (manualSection) manualSection.style.display = 'block';
                
                console.log('Switched to Manual Entry mode - textarea should be visible now');
            });
        }
        
        // Set up manual entry functionality
        const textarea = document.getElementById('manualOrderEntry');
        if (textarea) {
            textarea.addEventListener('input', () => {
                this.updateManualEntryStats();
            });
        }
        
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
        
        // Import Manual VINs button - Force show existing button (template cache bypass)
        let importManualBtn = document.getElementById('importManualVins');
        if (importManualBtn) {
            console.log('TEMPLATE CACHE BYPASS: Found existing Import Manual VINs button, forcing visibility');
            // Force show the button that exists but is hidden due to template caching
            importManualBtn.style.display = 'none'; // Will be controlled by tab switching
            importManualBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            importManualBtn.style.border = 'none';
            importManualBtn.style.color = 'white';
            importManualBtn.style.padding = '10px 20px';
            importManualBtn.style.borderRadius = '6px';
            importManualBtn.style.marginRight = '10px';
            importManualBtn.style.cursor = 'pointer';
            importManualBtn.style.transition = 'all 0.3s ease';
        } else {
            console.log('TEMPLATE CACHE BYPASS: Import Manual VINs button not found in DOM - template cache issue confirmed');
        }
        
        if (importManualBtn && !importManualBtn.hasVinLogEvents) {
            importManualBtn.addEventListener('click', () => this.processManualVinEntry());
            importManualBtn.hasVinLogEvents = true;
        }
        
        // TEMPLATE CACHE BYPASS - Add click handler for CSS pseudo-button
        const modalFooter = document.querySelector('#vinLogUpdateModal .modal-footer');
        if (modalFooter && !modalFooter.hasPseudoClickHandler) {
            modalFooter.addEventListener('click', (e) => {
                // Check if click is on the pseudo-button area
                const rect = modalFooter.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const clickY = e.clientY - rect.top;
                
                // If we're in manual mode and click is in the pseudo-button area
                if (document.body.hasAttribute('data-manual-mode') && clickX < 200 && clickY < 50) {
                    console.log('TEMPLATE CACHE BYPASS: CSS pseudo-button clicked');
                    this.processManualVinEntry();
                }
            });
            modalFooter.hasPseudoClickHandler = true;
        }
    }
    
    resetVinLogUpdateModal() {
        // Clear file selection
        this.clearVinLogFile();
        
        // Reset checkboxes
        const skipDuplicates = document.getElementById('skipDuplicates');
        const updateExisting = document.getElementById('updateExisting');

        if (skipDuplicates) skipDuplicates.checked = false;
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
        if (!this.currentDealership) {
            this.addTerminalMessage('No dealership selected', 'error');
            return;
        }
        
        // SMART IMPORT - Check which import method is active and route accordingly
        const currentMethod = this.currentImportMethod || 'csv';
        
        console.log(`SMART IMPORT: Processing ${currentMethod} import for ${this.currentDealership}`);
        
        if (currentMethod === 'manual') {
            // Process manual VIN entry
            console.log('SMART IMPORT: Routing to manual VIN processing');
            await this.processManualVinEntry();
            return;
        }
        
        // CSV import logic
        console.log('SMART IMPORT: Routing to CSV file processing');
        if (!this.selectedVinLogFile) {
            this.addTerminalMessage('No CSV file selected', 'error');
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
    
    async processManualVinEntry() {
        console.log('=== PROCESSING MANUAL VIN ENTRY ===');
        
        if (!this.currentDealership) {
            alert('Error: No dealership selected');
            return;
        }
        
        const textarea = document.getElementById('manualOrderEntry');
        if (!textarea || !textarea.value.trim()) {
            alert('Please enter VIN data before importing.');
            return;
        }
        
        // Get VIN data from textarea
        const textContent = textarea.value.trim();
        console.log('Manual VIN content:', textContent);
        
        // Parse the manual entry to extract VINs and order number
        const vins = this.parseManualVinEntry(textContent);
        if (!vins || vins.length === 0) {
            alert('No valid VINs found in the entered data. Please check your format.');
            return;
        }
        
        console.log('Parsed VINs:', vins);
        
        try {
            // Show progress
            this.updateVinLogProgress('Processing manual VIN import...', 10);
            
            // Call API to import VINs to dealership-specific VIN log
            const response = await fetch('/api/manual-vin-import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dealership_name: this.currentDealership,
                    vins: vins,
                    import_date: new Date().toISOString(),
                    source: 'manual_entry'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateVinLogProgress(`Successfully imported ${result.imported_count} VINs`, 100);
                this.addTerminalMessage(`Manual VIN import completed: ${result.imported_count} VINs added to ${this.currentDealership} log`, 'success');
                
                // Clear the textarea
                textarea.value = '';
                
                // Update stats
                if (window.updateManualEntryStatsInline) {
                    window.updateManualEntryStatsInline();
                }
                
                // Refresh VIN log data
                setTimeout(() => {
                    if (this.currentDealership) {
                        this.loadVinLogData(this.currentDealership);
                    }
                }, 1000);
                
                alert(`Successfully imported ${result.imported_count} VINs to ${this.currentDealership} VIN log`);
                
            } else {
                this.updateVinLogProgress(`Import failed: ${result.error}`, 100);
                this.addTerminalMessage(`Manual VIN import failed: ${result.error}`, 'error');
                alert(`Import failed: ${result.error}`);
            }
            
        } catch (error) {
            console.error('Manual VIN import error:', error);
            this.updateVinLogProgress(`Import error: ${error.message}`, 100);
            this.addTerminalMessage(`Manual VIN import error: ${error.message}`, 'error');
            alert(`Error importing VINs: ${error.message}`);
        }
    }
    
    parseManualVinEntry(textContent) {
        console.log('=== PARSING MANUAL VIN ENTRY ===');
        
        // Extract VINs (17-character alphanumeric strings)
        const vinRegex = /\b[A-HJ-NPR-Z0-9]{17}\b/g;
        const vins = textContent.match(vinRegex) || [];
        
        // Extract order number (look for patterns like "Order #12345" or just "12345" if it looks like an order number)
        let orderNumber = null;
        const orderPatterns = [
            /order\s*#?\s*(\d+)/i,
            /job\s*#?\s*(\d+)/i,
            /\b(\d{4,8})\b/g  // 4-8 digit numbers that could be order numbers
        ];
        
        for (const pattern of orderPatterns) {
            const match = textContent.match(pattern);
            if (match) {
                orderNumber = match[1] || match[0];
                break;
            }
        }
        
        console.log('Parsed results:', { vins, orderNumber });
        
        // Return VINs with associated order number
        return vins.map(vin => ({
            vin: vin.toUpperCase(),
            order_number: orderNumber,
            processed_date: new Date().toISOString()
        }));
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

    showOrderGroupSelectionModal() {
        if (!this.currentVinLogData || !this.currentVinLogData.history || this.currentVinLogData.history.length === 0) {
            this.showNotification('No VIN log data available for selection', 'warning');
            return;
        }

        // Get unique order numbers from current VIN log data
        const orderNumbers = [...new Set(this.currentVinLogData.history
            .filter(record => record.order_number)
            .map(record => record.order_number)
        )].sort();

        if (orderNumbers.length === 0) {
            this.showNotification('No order groups found in VIN log', 'warning');
            return;
        }

        // Create modal HTML for order selection
        const modalHTML = `
            <div class="modal" id="orderGroupSelectionModal" style="display: flex;">
                <div class="modal-content" style="max-width: 500px; margin: auto;">
                    <div class="modal-header">
                        <h3>Select Order Group to Remove</h3>
                        <button class="modal-close" onclick="this.closest('.modal').style.display = 'none'">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p style="margin-bottom: 15px; color: #e74c3c; font-weight: bold;">
                            ⚠️ Warning: This will permanently delete all VINs in the selected order group.
                        </p>
                        <div class="form-group">
                            <label for="orderGroupSelect">Order Group:</label>
                            <select id="orderGroupSelect" class="form-control">
                                <option value="">Select an order group...</option>
                                ${orderNumbers.map(order => `<option value="${order}">${order}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="this.closest('.modal').style.display = 'none'">
                            Cancel
                        </button>
                        <button class="btn btn-danger" id="confirmRemoveOrderGroup">
                            Remove Order Group
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if it exists
        const existingModal = document.getElementById('orderGroupSelectionModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add event listener for confirm button
        const confirmBtn = document.getElementById('confirmRemoveOrderGroup');
        const orderSelect = document.getElementById('orderGroupSelect');

        confirmBtn.addEventListener('click', () => {
            const selectedOrder = orderSelect.value;
            if (!selectedOrder) {
                this.showNotification('Please select an order group', 'warning');
                return;
            }

            // Get count of VINs to be removed
            const vinsToRemove = this.currentVinLogData.history.filter(record => record.order_number === selectedOrder).length;

            // Confirm deletion
            const confirmMessage = `Are you sure you want to remove order group "${selectedOrder}"?\n\nThis will delete ${vinsToRemove} VIN(s) permanently.`;
            if (confirm(confirmMessage)) {
                this.removeOrderGroup(selectedOrder);
                document.getElementById('orderGroupSelectionModal').style.display = 'none';
            }
        });
    }

    async removeOrderGroup(orderNumber) {
        try {
            if (!this.currentDealership || !orderNumber) {
                this.showNotification('Missing dealership or order number', 'error');
                return;
            }

            // Show loading state
            this.showNotification('Removing order group...', 'info');

            const response = await fetch('/api/vin-log/remove-order-group', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dealership_name: this.currentDealership,
                    order_number: orderNumber
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to remove order group');
            }

            this.showNotification(`Successfully removed order group ${orderNumber} (${data.vins_removed} VINs)`, 'success');

            // Reload VIN log data to reflect changes
            await this.loadVinLogData(this.currentDealership);

        } catch (error) {
            console.error('Remove order group error:', error);
            this.showNotification(`Failed to remove order group: ${error.message}`, 'error');
        }
    }

    // Dark Mode Theme System
    initTheme() {
        console.log('Initializing theme system...');
        
        // Load saved theme preference or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        
        // Add event listener to dark mode toggle button
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            // Set initial toggle state
            darkModeToggle.checked = savedTheme === 'dark';
            
            darkModeToggle.addEventListener('change', () => {
                this.toggleTheme();
            });
        }
    }
    
    setTheme(theme) {
        console.log(`Setting theme to: ${theme}`);
        
        // Apply theme to document root
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update dark mode toggle state
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            darkModeToggle.checked = theme === 'dark';
        }
        
        // Save theme preference
        localStorage.setItem('theme', theme);
        
        // Store current theme for reference
        this.currentTheme = theme;
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Show notification for theme change
        this.showNotification(`Switched to ${newTheme} mode`, 'info');
    }
}

/**
 * Modal Order Wizard - Simplified version for modal display
 */
class ModalOrderWizard {
    constructor() {
        this.currentStep = 0;
        this.steps = ['initialize', 'cao', 'list', 'review', 'orderNumber', 'complete'];
        this.queueData = [];
        this.caoOrders = [];
        this.listOrders = [];
        this.maintenanceOrders = [];
        this.currentListIndex = 0;
        this.processedOrders = [];
        this.processingResults = {
            totalDealerships: 0,
            caoProcessed: 0,
            listProcessed: 0,
            totalVehicles: 0,
            filesGenerated: 0,
            errors: []
        };

        // Add dealership-specific edited data storage
        this.dealershipEditedData = new Map(); // Store edited data for each dealership
        this.dealershipReviewStatus = new Map(); // Track which dealerships have been reviewed

        this.initializeEvents();
    }
    
    initializeEvents() {
        // Close modal event
        const closeBtn = document.getElementById('closeOrderWizardModal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        // Modal backdrop click disabled - users must use X button to close
        // This prevents accidental closure during order processing
        const modal = document.getElementById('orderWizardModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                // Prevent backdrop click from closing modal
                // Only the close button (X) can close the modal
                e.stopPropagation();
            });
        }
    }
    
    initializeFromQueue(queueData) {
        console.log('Initializing modal wizard with queue data:', queueData);
        
        this.queueData = queueData;
        this.caoOrders = queueData.filter(item => item.orderType === 'CAO');
        this.listOrders = queueData.filter(item => item.orderType === 'LIST');
        this.maintenanceOrders = queueData.filter(item => item.orderType === 'MAINTENANCE');
        this.processingResults.totalDealerships = queueData.length;
        
        // Set testing mode checkbox based on queue setting
        const testingMode = localStorage.getItem('orderWizardTestingMode') === 'true';
        const modalTestingCheckbox = document.getElementById('modalSkipVinLogging');
        if (modalTestingCheckbox) {
            modalTestingCheckbox.checked = testingMode;
        }
        
        // Reset to first step
        this.currentStep = 0;
        this.showStep('initialize');
        
        // Update the modal content
        this.renderModalQueueSummary();
        this.updateModalProgress('initialize');
    }
    
    renderModalQueueSummary() {
        const summaryContainer = document.getElementById('modalQueueSummary');
        if (!summaryContainer) return;
        
        const totalElement = document.getElementById('modalTotalDealerships');
        if (totalElement) {
            totalElement.textContent = this.queueData.length;
        }
        
        const caoCount = this.caoOrders.length;
        const listCount = this.listOrders.length;
        const maintenanceCount = this.maintenanceOrders.length;
        
        summaryContainer.innerHTML = `
            <div class="queue-summary-grid">
                <div class="summary-card cao-card">
                    <div class="card-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="card-content">
                        <h4>CAO Orders (Automatic)</h4>
                        <div class="card-value">${caoCount}</div>
                        <div class="card-details">
                            ${this.caoOrders.map(order => order.name).join(', ') || 'None'}
                        </div>
                    </div>
                </div>
                
                <div class="summary-card list-card">
                    <div class="card-icon">
                        <i class="fas fa-list"></i>
                    </div>
                    <div class="card-content">
                        <h4>List Orders (VIN Entry)</h4>
                        <div class="card-value">${listCount}</div>
                        <div class="card-details">
                            ${this.listOrders.map(order => order.name).join(', ') || 'None'}
                        </div>
                    </div>
                </div>
                
                <div class="summary-card maintenance-card">
                    <div class="card-icon">
                        <img src="/static/images/maintenance_icon.svg" alt="Maintenance" style="width: 20px; height: 20px; color: currentColor;">
                    </div>
                    <div class="card-content">
                        <h4>Maintenance Orders (CAO + Manual)</h4>
                        <div class="card-value">${maintenanceCount}</div>
                        <div class="card-details">
                            ${this.maintenanceOrders.map(order => order.name).join(', ') || 'None'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    showStep(stepName) {
        // Hide all modal wizard steps
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show target step
        const targetStep = document.getElementById(`modal${stepName.charAt(0).toUpperCase() + stepName.slice(1)}Step`);
        if (targetStep) {
            targetStep.classList.add('active');
        }
    }
    
    updateModalProgress(stepName) {
        // Update modal progress indicators
        document.querySelectorAll('#modalWizardProgress .progress-step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        const stepIndex = this.steps.indexOf(stepName);
        for (let i = 0; i <= stepIndex; i++) {
            const stepEl = document.getElementById(`modal-step-${this.steps[i]}`);
            if (stepEl) {
                if (i === stepIndex) {
                    stepEl.classList.add('active');
                } else {
                    stepEl.classList.add('completed');
                }
            }
        }
    }
    
    startProcessing() {
        console.log('Starting modal wizard processing...');
        this.updateModalProgress('cao');
        this.showStep('cao');
        
        // Process CAO orders only (maintenance has its own workflow)
        if (this.caoOrders.length > 0) {
            this.processCaoOrders();
        } else {
            // Skip to list processing (or maintenance if needed)
            setTimeout(() => {
                this.proceedToListProcessing();
            }, 1000);
        }
    }
    
    async processCaoOrders() {
        const statusContainer = document.getElementById('modalCaoProgress');
        if (!statusContainer) return;
        
        statusContainer.innerHTML = `
            <div class="cao-processing-status">
                <h3>Processing ${this.caoOrders.length} CAO Orders...</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="modalCaoProgressFill" style="width: 0%"></div>
                </div>
                <div class="processing-list" id="modalCaoProcessingList"></div>
            </div>
        `;
        
        const processingList = document.getElementById('modalCaoProcessingList');
        const progressFill = document.getElementById('modalCaoProgressFill');
        
        // Process each CAO order
        for (let i = 0; i < this.caoOrders.length; i++) {
            const order = this.caoOrders[i];
            
            // Add processing item
            const processingItem = document.createElement('div');
            processingItem.className = 'cao-processing-item';
            processingItem.innerHTML = `
                <div class="processing-dealership">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>${order.name}</span>
                </div>
                <div class="processing-status">Processing...</div>
            `;
            processingList.appendChild(processingItem);
            
            try {
                // Make real API call to process CAO order
                console.log(`Making API call for ${order.name}...`);
                const result = await this.processCaoOrder(order.name);
                console.log(`API result for ${order.name}:`, result);
                
                // Store result for later use
                this.processedOrders.push({
                    dealership: order.name,
                    type: 'cao',
                    result: result
                });
                
                processingItem.innerHTML = `
                    <div class="processing-dealership">
                        <i class="fas fa-check" style="color: #16a34a;"></i>
                        <span>${order.name}</span>
                    </div>
                    <div class="processing-status" style="color: #16a34a;">
                        ${result.vehicles_processed || 0} vehicles processed
                    </div>
                `;
                
                this.processingResults.caoProcessed++;
                this.processingResults.totalVehicles += result.vehicles_processed || 0;
                this.processingResults.filesGenerated += result.files_generated || 0;
                
            } catch (error) {
                processingItem.innerHTML = `
                    <div class="processing-dealership">
                        <i class="fas fa-times" style="color: #dc2626;"></i>
                        <span>${order.name}</span>
                    </div>
                    <div class="processing-status" style="color: #dc2626;">
                        Error: ${error.message}
                    </div>
                `;
                this.processingResults.errors.push(`${order.name}: ${error.message}`);
            }
            
            // Update progress
            const progress = ((i + 1) / this.caoOrders.length) * 100;
            progressFill.style.width = `${progress}%`;
        }
        
        // Proceed to next step
        setTimeout(() => {
            this.nextStep();
        }, 1500);
    }
    
    async processCaoOrder(dealershipName) {
        // Get testing mode checkbox state from modal checkbox
        const modalTestingCheckbox = document.getElementById('modalSkipVinLogging');
        const testingMode = modalTestingCheckbox ? modalTestingCheckbox.checked :
                           (localStorage.getItem('orderWizardTestingMode') === 'true');

        // ORIGINAL CAO PROCESSING (maintain backward compatibility)
        console.log(`Processing CAO order for ${dealershipName} (original workflow)`);
        const originalResponse = await fetch('/api/orders/process-cao', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dealerships: [dealershipName],
                vehicle_types: null,  // Use dealership-specific filtering rules from database
                skip_vin_logging: true  // Always skip VIN logging in old workflow when using two-phase workflow
            })
        });

        if (!originalResponse.ok) {
            throw new Error(`Failed to process CAO order: ${originalResponse.statusText}`);
        }

        const originalResults = await originalResponse.json();
        console.log('Original CAO API response:', originalResults);
        const originalResult = originalResults[0] || originalResults; // Handle both array and single object responses
        console.log('Original CAO processed result:', originalResult);
        console.log('[DEBUG] Vehicle count properties in result:', {
            'new_vehicles': originalResult.new_vehicles,
            'vehicle_count': originalResult.vehicle_count,
            'vehicles_processed': originalResult.vehicles_processed,
            'success': originalResult.success
        });

        // PHASE 1: ALSO prepare CAO data for the new two-phase workflow
        console.log(`[PHASE 1] ALSO preparing CAO data for ${dealershipName} for new workflow`);
        let phase1Result = null;
        try {
            const phase1Response = await fetch('/api/orders/prepare-cao', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealerships: [dealershipName],
                    skip_vin_logging: testingMode
                })
            });

            if (phase1Response.ok) {
                const phase1Results = await phase1Response.json();
                console.log('[PHASE 1] Prepare CAO API response:', phase1Results);
                phase1Result = phase1Results[0] || phase1Results;
                console.log('[PHASE 1] Prepared data result:', phase1Result);
            } else {
                console.warn('[PHASE 1] Failed to prepare CAO data for new workflow, continuing with original only');
            }
        } catch (error) {
            console.warn('[PHASE 1] Error preparing CAO data for new workflow:', error.message);
        }

        // Return original result with Phase 1 data attached for new workflow
        const vehicleCount = originalResult.new_vehicles || originalResult.vehicle_count ||
                           originalResult.vehicles_processed || 0;

        return {
            ...originalResult,
            vehicles_processed: vehicleCount,
            // Store Phase 1 data for the new workflow (if available)
            phase1_data: phase1Result
        };
    }

    async generateFinalFiles(dealershipName, vehiclesData, orderNumber, templateType = null, forceVinLogging = false) {
        // PHASE 2: Generate final files from prepared data + order number
        const modalTestingCheckbox = document.getElementById('modalSkipVinLogging');
        const testingMode = modalTestingCheckbox ? modalTestingCheckbox.checked :
                           (localStorage.getItem('orderWizardTestingMode') === 'true');

        // If forceVinLogging is true, always enable VIN logging regardless of testing mode
        const skipVinLogging = forceVinLogging ? false : testingMode;

        console.log(`[PHASE 2] Generating final files for ${dealershipName} with order number: ${orderNumber}`);
        console.log(`[PHASE 2] Processing ${vehiclesData.length} vehicles`);
        console.log(`[JS QR TRACE 1] generateFinalFiles() called with:`);
        console.log(`[JS QR TRACE 1]   - Dealership: ${dealershipName}`);
        console.log(`[JS QR TRACE 1]   - Order Number: ${orderNumber}`);
        console.log(`[JS QR TRACE 1]   - Template Type: ${templateType}`);
        console.log(`[JS QR TRACE 1]   - Vehicle Count: ${vehiclesData.length}`);
        console.log(`[JS QR TRACE 1]   - Testing Mode: ${testingMode}`);
        console.log(`[JS QR TRACE 1]   - Sample Vehicle Data:`, vehiclesData.slice(0, 2));

        // Get custom template configuration for this dealership
        const dealershipData = window.app?.dealerships?.find(d => d.name === dealershipName);
        const customTemplateConfig = dealershipData?.output_rules?.custom_templates || null;
        console.log(`[JS QR TRACE 1]   - Custom Template Config:`, customTemplateConfig);

        const response = await fetch('/api/orders/generate-final-files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dealership_name: dealershipName,
                vehicles_data: vehiclesData,
                order_number: orderNumber,
                template_type: templateType,
                custom_templates: customTemplateConfig,
                skip_vin_logging: skipVinLogging
            })
        });

        console.log(`[JS QR TRACE 2] API request sent to /api/orders/generate-final-files`);
        console.log(`[JS QR TRACE 2] Request payload:`, {
            dealership_name: dealershipName,
            vehicles_data: vehiclesData.slice(0, 2), // Show first 2 for brevity
            order_number: orderNumber,
            template_type: templateType,
            skip_vin_logging: skipVinLogging
        });

        if (!response.ok) {
            throw new Error(`Failed to generate final files: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('[PHASE 2] Final file generation result:', result);
        console.log(`[JS QR TRACE 3] generateFinalFiles() API response received`);
        console.log(`[JS QR TRACE 3] Response status: ${response.status}`);
        console.log(`[JS QR TRACE 3] Response result:`, result);

        // Map backend fields to frontend expected fields for PHASE 2 (file generation)
        const mappedResult = {
            vehicles_processed: result.vehicle_count || 0,
            files_generated: result.qr_codes_generated || 0,
            success: result.success,
            dealership: result.dealership,
            order_number: result.order_number,
            phase: 'files_generated',
            download_csv: result.download_csv,
            qr_folder: result.qr_folder,
            csv_file: result.csv_file,
            billing_csv_file: result.billing_csv_file,
            download_billing_csv: result.download_billing_csv,
            timestamp: result.timestamp,
            vins_logged_to_history: result.vins_logged_to_history,
            vin_logging_success: result.vin_logging_success
        };

        console.log('[PHASE 2] Mapped result for frontend:', mappedResult);
        return mappedResult;
    }

    async generateAllFinalFiles() {
        // PHASE 2: Generate final files for all dealerships with prepared data + order numbers
        console.log('[PHASE 2] Generating final files for all dealerships...');

        // Find all CAO orders that have Phase 1 prepared data
        const caoOrdersWithData = this.processedOrders.filter(order =>
            order.result &&
            order.result.phase1_data &&
            order.result.phase1_data.vehicles_data &&
            order.result.phase1_data.vehicles_data.length > 0
        );

        // Find all LIST orders that are prepared but not yet processed
        const listOrdersToProcess = this.processedOrders.filter(order =>
            order.type === 'list' &&
            order.result &&
            order.result.phase === 'prepared_for_review' &&
            order.result.vehicles_for_review &&
            order.result.vehicles_for_review.length > 0
        );

        console.log(`[PHASE 2] Found ${caoOrdersWithData.length} CAO orders with prepared data`);
        console.log(`[PHASE 2] Found ${listOrdersToProcess.length} LIST orders to process`);

        // Process LIST orders that need final processing
        for (const listOrder of listOrdersToProcess) {
            console.log(`[PHASE 2] Processing LIST order for ${listOrder.dealership}`);
            try {
                const skipVinLogging = document.getElementById('skipVinLogging')?.checked || false;
                const response = await fetch('/api/orders/process-list', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        dealership: listOrder.dealership,
                        vins: listOrder.vins, // Use the filtered VINs
                        skip_vin_logging: skipVinLogging
                    })
                });

                if (!response.ok) {
                    throw new Error(`Failed to process list order: ${response.statusText}`);
                }

                const result = await response.json();
                console.log(`LIST processing result for ${listOrder.dealership}:`, result);

                // Update the order result with the final processing result
                listOrder.result = result;
                this.processingResults.filesGenerated += result.files_generated || 0;

            } catch (error) {
                console.error(`Error processing LIST order for ${listOrder.dealership}:`, error);
                this.processingResults.errors.push(`${listOrder.dealership}: ${error.message}`);
            }
        }

        const dealershipsWithData = caoOrdersWithData;

        console.log(`[PHASE 2] Processing ${dealershipsWithData.length} CAO orders...`);

        if (dealershipsWithData.length === 0 && listOrdersToProcess.length === 0) {
            console.log('[PHASE 2] No orders with prepared data to process');
            return;
        }

        if (dealershipsWithData.length === 0) {
            console.log('[PHASE 2] No CAO orders to process, LIST orders were already processed');
            return;
        }

        // Collect order numbers for each dealership
        // TODO: This needs to be implemented to collect order numbers from the UI
        // For now, use a placeholder method
        const orderNumbers = this.collectOrderNumbers(dealershipsWithData);

        // Process each dealership with final file generation
        for (let i = 0; i < dealershipsWithData.length; i++) {
            const order = dealershipsWithData[i];
            const dealershipName = order.dealership;
            const vehiclesData = order.result.phase1_data.vehicles_data;
            const templateType = order.result.phase1_data.template_type;
            const orderNumber = orderNumbers[dealershipName];

            if (!orderNumber) {
                console.warn(`[PHASE 2] No order number provided for ${dealershipName}, skipping...`);
                continue;
            }

            console.log(`[PHASE 2] Generating final files for ${dealershipName} with order ${orderNumber}`);

            try {
                // Call Phase 2 file generation
                const finalResult = await this.generateFinalFiles(
                    dealershipName,
                    vehiclesData,
                    orderNumber,
                    templateType,
                    true  // forceVinLogging=true for Process Presently
                );

                // Update the processed order with final file information
                order.result = {
                    ...order.result,
                    ...finalResult,
                    phase: 'files_generated'
                };

                console.log(`[PHASE 2] Successfully generated final files for ${dealershipName}`);

            } catch (error) {
                console.error(`[PHASE 2] Error generating final files for ${dealershipName}:`, error);
                throw new Error(`Failed to generate final files for ${dealershipName}: ${error.message}`);
            }
        }

        console.log('[PHASE 2] All final files generated successfully');
    }

    collectOrderNumbers(dealershipsWithData) {
        // Collect order numbers entered by the user in the order number step
        // This method should extract order numbers from the UI
        console.log('[PHASE 2] Collecting order numbers from UI...');

        const orderNumbers = {};

        // Try to collect from multi-dealership order inputs if they exist
        dealershipsWithData.forEach(order => {
            const dealershipName = order.dealership;

            // Look for dealership-specific order number input
            const orderInput = document.getElementById(`orderNumber_${dealershipName.replace(/\s+/g, '_')}`);

            if (orderInput && orderInput.value.trim()) {
                orderNumbers[dealershipName] = orderInput.value.trim();
                console.log(`[PHASE 2] Collected order number for ${dealershipName}: ${orderInput.value.trim()}`);
            } else {
                // Fallback to single order number if available
                if (this.singleOrderNumber) {
                    orderNumbers[dealershipName] = this.singleOrderNumber;
                    console.log(`[PHASE 2] Using single order number for ${dealershipName}: ${this.singleOrderNumber}`);
                } else {
                    console.warn(`[PHASE 2] No order number found for ${dealershipName}`);
                }
            }
        });

        return orderNumbers;
    }

    proceedToListProcessing() {
        // Check if we have maintenance orders to process first
        if (this.maintenanceOrders.length > 0) {
            this.processMaintenanceOrders();
            return;
        }
        
        if (this.listOrders.length === 0) {
            // No list orders, proceed to review
            this.proceedToReview();
            return;
        }
        
        this.updateModalProgress('list');
        this.showStep('list');
        this.showCurrentListOrder();
    }
    
    async processMaintenanceOrders() {
        console.log('Processing maintenance orders...');
        this.currentMaintenanceIndex = 0;
        this.maintenanceResults = []; // Store CAO results for each maintenance order
        
        // Process each maintenance order (CAO + Manual VINs)
        await this.processCurrentMaintenanceOrder();
    }
    
    async processCurrentMaintenanceOrder() {
        if (this.currentMaintenanceIndex >= this.maintenanceOrders.length) {
            // All maintenance orders processed, move to regular list processing
            if (this.listOrders.length > 0) {
                this.updateModalProgress('list');
                this.showStep('list');
                this.showCurrentListOrder();
            } else {
                this.proceedToReview();
            }
            return;
        }
        
        const currentOrder = this.maintenanceOrders[this.currentMaintenanceIndex];
        console.log('Processing maintenance order for:', currentOrder.name);
        
        // Step 1: Run CAO for this dealership
        try {
            const caoResult = await this.processSingleCaoOrder(currentOrder);
            
            // Store CAO results for this maintenance order
            this.maintenanceResults[this.currentMaintenanceIndex] = {
                order: currentOrder,
                caoResults: caoResult,
                manualVins: []
            };
            
            // Step 2: Show manual VIN entry form for this dealership
            this.showMaintenanceVinEntry(currentOrder, caoResult);
            
        } catch (error) {
            console.error('Error processing maintenance CAO for', currentOrder.name, error);
            console.log('CAO failed, but showing manual VIN entry form anyway for maintenance order');
            this.maintenanceResults[this.currentMaintenanceIndex] = {
                order: currentOrder,
                caoResults: null,
                manualVins: [],
                error: error.message
            };
            
            // Even if CAO fails, still show manual VIN entry for maintenance orders
            this.showMaintenanceVinEntry(currentOrder, null);
        }
    }
    
    async processSingleCaoOrder(order) {
        console.log('Processing single CAO order for:', order.name);

        try {
            // Check if this is a maintenance order and use appropriate endpoint
            const isMaintenance = this.maintenanceOrders && this.maintenanceOrders.some(m => m.name === order.name);
            const endpoint = isMaintenance ? '/api/orders/process-maintenance' : '/api/orders/process-cao';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(isMaintenance ? {
                    dealership: order.name,  // Maintenance endpoint expects single dealership
                    vins: [],  // Empty VIN list for CAO-only processing
                    skip_vin_logging: document.getElementById('orderWizardTestingMode')?.checked || false
                } : {
                    dealerships: [order.name],  // Backend expects array, just like regular CAO
                    vehicle_types: null,  // Use dealership-specific filtering rules from database
                    skip_vin_logging: document.getElementById('orderWizardTestingMode')?.checked || false
                })
            });
            
            const result = await response.json();

            // Handle different response formats
            if (isMaintenance) {
                // Maintenance endpoint returns single result
                if (result.success) {
                    return await this.mapCaoResultForFrontend(result);
                } else {
                    throw new Error(result.message || 'Maintenance processing failed');
                }
            } else {
                // CAO endpoint returns array of results, get the first one
                if (Array.isArray(result) && result.length > 0) {
                    const firstResult = result[0];
                    if (firstResult.success) {
                        return await this.mapCaoResultForFrontend(firstResult);
                    } else {
                        throw new Error(firstResult.message || 'CAO processing failed');
                    }
                } else if (result.success) {
                    return await this.mapCaoResultForFrontend(result);
                } else {
                    throw new Error(result.message || 'CAO processing failed');
                }
            }
        } catch (error) {
            console.error('Error in processSingleCaoOrder:', error);
            throw error;
        }
    }
    
    async mapCaoResultForFrontend(result) {
        // Map backend fields to frontend expected fields for maintenance orders
        console.log('🔍 DEBUGGING Backend result keys:', Object.keys(result));
        console.log('🔍 DEBUGGING Backend result:', result);
        
        // Try different possible field names for vehicles array
        let vehiclesArray = result.vehicles || result.processed_vehicles || result.vehicle_data || result.vehicle_list || [];
        console.log('🔍 DEBUGGING Found vehicles array:', vehiclesArray, 'Length:', vehiclesArray.length);
        
        // If no vehicles in response but we have a CSV file, fetch and parse it
        if (vehiclesArray.length === 0 && (result.download_csv || result.csv_file)) {
            // Use the web-accessible download_csv path instead of local csv_file path
            const csvUrl = result.download_csv || result.csv_file;
            console.log('🔍 DEBUGGING: No vehicles in response, attempting to fetch CSV data from:', csvUrl);
            try {
                vehiclesArray = await this.fetchVehiclesFromCsv(csvUrl, result.dealership);
                console.log('🔍 DEBUGGING: Successfully parsed', vehiclesArray.length, 'vehicles from CSV');
            } catch (error) {
                console.error('❌ ERROR: Failed to fetch vehicles from CSV:', error);
            }
        }
        
        return {
            vehicle_count: result.new_vehicles || result.vehicle_count || 0,
            vehicles: vehiclesArray,
            dealership: result.dealership,
            success: result.success,
            download_csv: result.download_csv,
            qr_folder: result.qr_folder,
            csv_file: result.csv_file,
            timestamp: result.timestamp
        };
    }
    
    async fetchVehiclesFromCsv(csvPath, dealershipName) {
        // Fetch CSV file and parse vehicle data for maintenance order display
        console.log('📄 FETCHING CSV data from:', csvPath);
        
        try {
            const response = await fetch(csvPath);
            if (!response.ok) {
                throw new Error(`Failed to fetch CSV: ${response.status} ${response.statusText}`);
            }
            
            const csvText = await response.text();
            const vehicles = this.parseCsvToVehicles(csvText);
            
            // Fetch raw_status data for review stage display
            console.log(`🔍 ATTEMPTING to fetch raw_status for: ${dealershipName}`);
            try {
                const rawStatusUrl = `/api/vehicles/raw-status/${encodeURIComponent(dealershipName)}`;
                console.log(`📡 Making API call to: ${rawStatusUrl}`);
                
                const rawStatusResponse = await fetch(rawStatusUrl, {
                    cache: 'no-cache'
                });
                
                console.log(`📊 API response status: ${rawStatusResponse.status}`);
                
                if (rawStatusResponse.ok) {
                    const rawStatusData = await rawStatusResponse.json();
                    console.log(`✅ Retrieved raw_status for ${Object.keys(rawStatusData).length} vehicles from ${dealershipName}`);
                    console.log(`🎯 Raw status sample data:`, Object.keys(rawStatusData).slice(0, 3).map(vin => `${vin}: ${rawStatusData[vin]}`));
                    
                    // Merge raw_status data into vehicles for UI display (not for CSV export)
                    vehicles.forEach(vehicle => {
                        const vin = vehicle.VIN || vehicle.vin || '';
                        if (vin && rawStatusData[vin]) {
                            vehicle.raw_status = rawStatusData[vin] || 'Empty';
                            console.log(`🔗 Mapped ${vin} -> ${vehicle.raw_status}`);
                        } else {
                            vehicle.raw_status = 'N/A';
                            console.log(`❌ No mapping for VIN: ${vin}`);
                        }
                    });
                } else {
                    console.warn(`❌ Failed to fetch raw_status for ${dealership}:`, rawStatusResponse.statusText);
                    // Set all vehicles to N/A if API call fails
                    vehicles.forEach(vehicle => {
                        vehicle.raw_status = 'API_FAILED';
                    });
                }
            } catch (error) {
                console.error(`💥 Error fetching raw_status for ${dealership}:`, error);
                // Set all vehicles to N/A if API call fails
                vehicles.forEach(vehicle => {
                    vehicle.raw_status = 'FETCH_ERROR';
                });
            }
            
            console.log('✅ SUCCESS: Parsed', vehicles.length, 'vehicles from CSV with raw_status data');
            return vehicles;
            
        } catch (error) {
            console.error('❌ ERROR: Failed to fetch/parse CSV:', error);
            return [];
        }
    }
    
    parseCsvToVehicles(csvText) {
        // Parse CSV text into vehicle objects for display
        const lines = csvText.trim().split('\n');
        if (lines.length <= 1) return []; // No data rows
        
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        const vehicles = [];
        
        console.log('📋 CSV Headers found:', headers);
        
        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
            const vehicle = {};
            
            // Map CSV columns to vehicle object
            headers.forEach((header, index) => {
                vehicle[header.toLowerCase()] = values[index] || '';
            });
            
            // Standardize common field names for display
            if (!vehicle.vin && vehicle.stock_number) vehicle.vin = vehicle.stock_number;
            if (!vehicle.year && vehicle.model_year) vehicle.year = vehicle.model_year;
            if (!vehicle.make && vehicle.vehicle_make) vehicle.make = vehicle.vehicle_make;
            if (!vehicle.model && vehicle.vehicle_model) vehicle.model = vehicle.vehicle_model;
            
            vehicles.push(vehicle);
        }
        
        console.log('🚗 Sample vehicle parsed:', vehicles[0]);
        return vehicles;
    }
    
    showMaintenanceVinEntry(order, caoResults) {
        console.log('Showing maintenance VIN entry for:', order.name, 'CAO results:', caoResults);
        
        this.updateModalProgress('list');
        this.showStep('list');
        
        const dealershipContainer = document.getElementById('modalListDealerships');
        
        if (dealershipContainer) {
            dealershipContainer.innerHTML = `
                <div class="maintenance-dealership-container">
                    <div class="dealership-header">
                        <div class="dealership-info">
                            <h3>${order.name}</h3>
                            <span class="order-type-badge maintenance-badge">
                                <img src="/static/images/maintenance_icon.svg" alt="Maintenance" style="width: 14px; height: 14px; margin-right: 5px;">
                                MAINTENANCE
                            </span>
                        </div>
                        <div class="maintenance-summary">
                            <div class="cao-results-summary">
                                <strong>CAO Results:</strong> ${caoResults ? caoResults.vehicle_count || 0 : 0} vehicles
                            </div>
                        </div>
                    </div>
                    
                    <div class="maintenance-sections">
                        <div class="cao-results-section">
                            <h4><i class="fas fa-robot"></i> CAO Results (${caoResults ? caoResults.vehicle_count || 0 : 0} vehicles)</h4>
                            <div class="cao-results-preview">
                                ${caoResults && caoResults.vehicles ? 
                                    caoResults.vehicles.slice(0, 3).map(v => 
                                        `<div class="vin-preview">${v.vin} - ${v.year} ${v.make} ${v.model}</div>`
                                    ).join('') + 
                                    (caoResults.vehicles.length > 3 ? `<div class="vin-preview">... and ${caoResults.vehicles.length - 3} more</div>` : '')
                                : '<div class="no-results">No CAO results</div>'}
                            </div>
                        </div>
                        
                        <div class="manual-vin-section">
                            <h4><i class="fas fa-plus"></i> Add Manual VINs</h4>
                            <p>Enter additional VINs from your installer (one per line):</p>
                            <textarea 
                                id="maintenanceVinInput" 
                                class="vin-textarea" 
                                placeholder="Enter VINs here (one per line)&#10;Example:&#10;1HGBH41JXMN109186&#10;2HGFC2F59JH542637&#10;WAUBF98E07A012345"
                                rows="8"
                            ></textarea>
                        </div>
                    </div>
                    
                    <div class="wizard-actions">
                        <button class="btn-wizard secondary" onclick="window.modalWizard.skipMaintenanceVinEntry()">
                            Skip Manual Entry
                        </button>
                        <button class="btn-wizard primary" onclick="window.modalWizard.processMaintenanceVins()">
                            <i class="fas fa-arrow-right"></i>
                            Combine & Continue
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    async processMaintenanceVins() {
        console.log('[MAINTENANCE DEBUG] processMaintenanceVins() called');

        const vinInput = document.getElementById('maintenanceVinInput');
        console.log('[MAINTENANCE DEBUG] vinInput element:', vinInput);
        console.log('[MAINTENANCE DEBUG] vinInput.value:', vinInput ? vinInput.value : 'NULL');

        const manualVins = vinInput ? vinInput.value.trim().split('\n').filter(vin => vin.trim()) : [];
        console.log('[MAINTENANCE DEBUG] manualVins array:', manualVins);
        console.log('[MAINTENANCE DEBUG] manualVins count:', manualVins.length);

        if (this.maintenanceResults[this.currentMaintenanceIndex]) {
            const currentOrder = this.maintenanceOrders[this.currentMaintenanceIndex];
            const dealershipName = currentOrder.name;

            console.log('[MAINTENANCE DEBUG] Dealership:', dealershipName);
            console.log('[MAINTENANCE DEBUG] Sending to API - VINs:', manualVins);

            try {
                // Call the maintenance API with manual VINs - it will handle CAO + LIST deduplication
                const response = await fetch('/api/orders/process-maintenance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        dealership: dealershipName,
                        vins: manualVins.map(vin => vin.trim()),
                        skip_vin_logging: document.getElementById('orderWizardTestingMode')?.checked || false
                    })
                });

                if (response.ok) {
                    const result = await response.json();

                    if (result.success) {
                        // Backend returns deduplicated combined vehicles in 'vehicles' field
                        const vehicles = result.vehicles || result.vehicles_data || [];

                        const combinedResults = {
                            dealership: dealershipName,
                            orderType: 'MAINTENANCE',
                            type: 'maintenance',  // For compatibility with review stage
                            success: true,
                            vehicle_count: result.total_count || result.vehicle_count,
                            vehicles: vehicles,
                            caoCount: result.cao_count || 0,
                            manualCount: result.list_count || 0,
                            // Add result object for compatibility with "Process Presently" function
                            result: {
                                phase: 'prepared_for_review',
                                vehicles_for_review: vehicles,  // Make vehicles available for review
                                dealership: dealershipName
                            }
                        };

                        console.log(`Maintenance order processed: ${combinedResults.vehicle_count} vehicles (${combinedResults.caoCount} CAO + ${combinedResults.manualCount} LIST, deduplicated)`);

                        this.processedOrders.push(combinedResults);
                        this.processingResults.totalVehicles += combinedResults.vehicle_count;
                    } else {
                        console.error('Maintenance processing failed:', result.error);
                    }
                } else {
                    console.error('Failed to process maintenance order');
                }
            } catch (error) {
                console.error('Error processing maintenance vins:', error);
            }
        }

        // Move to next maintenance order
        this.currentMaintenanceIndex++;
        this.processCurrentMaintenanceOrder();
    }
    
    skipMaintenanceVinEntry() {
        // Just use CAO results without manual VINs
        const caoResults = this.maintenanceResults[this.currentMaintenanceIndex].caoResults;
        const caoVehicles = caoResults ? caoResults.vehicles || [] : [];
        
        const combinedResults = {
            dealership: this.maintenanceResults[this.currentMaintenanceIndex].order.name,
            orderType: 'MAINTENANCE',
            success: true,
            vehicle_count: caoVehicles.length,
            vehicles: caoVehicles,
            caoCount: caoVehicles.length,
            manualCount: 0
        };
        
        this.processedOrders.push(combinedResults);
        this.processingResults.totalVehicles += combinedResults.vehicle_count;
        
        // Move to next maintenance order
        this.currentMaintenanceIndex++;
        this.processCurrentMaintenanceOrder();
    }
    
    showCurrentListOrder() {
        if (this.currentListIndex >= this.listOrders.length) {
            this.proceedToReview();
            return;
        }
        
        const currentOrder = this.listOrders[this.currentListIndex];
        const dealershipContainer = document.getElementById('modalListDealerships');
        
        if (dealershipContainer && currentOrder) {
            dealershipContainer.innerHTML = `
                <div class="current-dealership-card">
                    <h4>${currentOrder.name}</h4>
                    <p>Please enter VINs for this LIST order dealership:</p>
                    <textarea 
                        id="modalVinInput" 
                        class="vin-textarea" 
                        placeholder="Enter VINs, one per line...
Example:
1HGBH41JXMN109186
2FMDK3GC4DBA54321
1FTFW1ET5CFC12345"
                        rows="8"></textarea>
                    <div class="vin-help">
                        <p><strong>Instructions:</strong></p>
                        <ul>
                            <li>Enter one VIN or Stock Number per line</li>
                            <li>VINs: Exactly 17 characters</li>
                            <li>Stock Numbers: Up to 17 characters</li>
                            <li>Entries will be automatically validated</li>
                        </ul>
                    </div>
                </div>
            `;
        }
    }
    
    async processListVins() {
        const vinInput = document.getElementById('modalVinInput');
        if (!vinInput || !vinInput.value.trim()) {
            alert('Please enter VINs for this dealership');
            return;
        }
        
        const vins = vinInput.value.trim().split('\n')
            .map(vin => vin.trim())
            .filter(vin => vin.length > 0);

        if (vins.length === 0) {
            alert('Please enter valid VINs or Stock Numbers');
            return;
        }

        // Validate entries: Accept VINs (17 chars) and Stock Numbers (<17 chars, max 17)
        const invalidEntries = vins.filter(entry => entry.length > 17);
        if (invalidEntries.length > 0) {
            alert(`Invalid entries detected (maximum 17 characters): ${invalidEntries.join(', ')}`);
            return;
        }
        
        // Get current dealership - check if we're in maintenance processing first
        let currentOrder;
        if (this.currentMaintenanceIndex < this.maintenanceOrders.length) {
            // We're in maintenance processing, use maintenance order
            currentOrder = this.maintenanceOrders[this.currentMaintenanceIndex];
            console.log('Using maintenance order context for LIST processing:', currentOrder?.name);
        } else {
            // Regular LIST processing
            currentOrder = this.listOrders[this.currentListIndex];
            console.log('Using regular LIST order context:', currentOrder?.name);
        }

        if (!currentOrder) {
            alert('No current dealership found');
            return;
        }
        
        try {
            // PHASE 1: Prepare and validate VINs first
            console.log(`Preparing LIST order for ${currentOrder.name} with ${vins.length} VINs`);

            const prepareResponse = await fetch('/api/orders/prepare-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership: currentOrder.name,
                    vins: vins
                })
            });

            if (!prepareResponse.ok) {
                throw new Error(`Failed to prepare list order: ${prepareResponse.statusText}`);
            }

            const prepareResult = await prepareResponse.json();
            console.log(`LIST preparation result:`, prepareResult);

            if (!prepareResult.success) {
                alert(`Error preparing LIST order: ${prepareResult.error}`);
                return;
            }

            // Show excluded VINs notification if any
            if (prepareResult.invalid_vin_list && prepareResult.invalid_vin_list.length > 0) {
                const excludedMessage = `${prepareResult.invalid_vin_list.length} VIN(s) were excluded because they are not found in scraper data:\n${prepareResult.invalid_vin_list.join('\n')}\n\nOnly ${prepareResult.valid_vins} valid VINs will be processed. Continue?`;
                if (!confirm(excludedMessage)) {
                    return;
                }
            }

            // Store the preparation result for review stage
            this.currentListPrepareData = prepareResult;

            // Add additional fields for review stage
            prepareResult.dealership = currentOrder.name;
            prepareResult.vehicles_for_review = prepareResult.vehicles_data || [];
            prepareResult.filtered_vin_list = (prepareResult.vehicles_data || []).map(v => v.vin);
            prepareResult.original_vin_list = vins;
            prepareResult.template_type = currentOrder.template || 'shortcut_pack';

            // Move to review stage with only valid vehicles
            this.showListReviewStage(prepareResult);

        } catch (error) {
            console.error('Error preparing LIST order:', error);
            alert(`Error preparing VINs: ${error.message}`);
            this.processingResults.errors.push(`${currentOrder.name}: ${error.message}`);

            // Move to next dealership on error
            this.currentListIndex++;
            if (this.currentListIndex < this.listOrders.length) {
                this.showCurrentListOrder();
            } else {
                this.proceedToReview();
            }
        }
    }

    showListReviewStage(prepareResult) {
        // Store the filtered LIST data for the review stage
        console.log('Storing LIST data for review stage with valid vehicles:', prepareResult.vehicles_for_review);

        // Store the LIST order result with ONLY valid vehicles for the review stage
        // This will make the review stage show only valid vehicles
        this.processedOrders.push({
            dealership: prepareResult.dealership,
            type: 'list',
            vins: prepareResult.filtered_vin_list, // Only valid VINs for review display
            original_vin_list: prepareResult.original_vin_list, // Keep original for billing
            result: {
                success: true,
                vehicles_for_review: prepareResult.vehicles_for_review,
                vehicle_count: prepareResult.vehicles_for_review.length,
                template_type: prepareResult.template_type,
                phase: 'prepared_for_review'
            }
        });

        this.processingResults.listProcessed++;
        this.processingResults.totalVehicles += prepareResult.vehicles_for_review.length;

        // Continue with next dealership or proceed to review
        this.currentListIndex++;
        if (this.currentListIndex < this.listOrders.length) {
            this.showCurrentListOrder();
        } else {
            this.proceedToReview();
        }
    }

    async processListReviewComplete() {
        // PHASE 2: Process the reviewed data (equivalent to old direct processing)
        // Get current dealership - check if we're in maintenance processing first
        let currentOrder;
        if (this.currentMaintenanceIndex < this.maintenanceOrders.length) {
            // We're in maintenance processing, use maintenance order
            currentOrder = this.maintenanceOrders[this.currentMaintenanceIndex];
        } else {
            // Regular LIST processing
            currentOrder = this.listOrders[this.currentListIndex];
        }

        const skipVinLogging = document.getElementById('skipVinLogging')?.checked || false;

        try {
            console.log(`Processing reviewed LIST order for ${currentOrder.name}`);

            const response = await fetch('/api/orders/process-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership: currentOrder.name,
                    vins: this.currentReviewData.filtered_vin_list, // Use only valid VINs
                    skip_vin_logging: skipVinLogging
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to process list order: ${response.statusText}`);
            }

            const result = await response.json();
            console.log(`LIST processing result:`, result);

            // Store the actual result data
            this.processedOrders.push({
                dealership: currentOrder.name,
                type: 'list',
                vins: this.currentReviewData.original_vin_list, // Keep original for billing
                result: result
            });

            this.processingResults.listProcessed++;
            this.processingResults.totalVehicles += result.vehicle_count || result.vehicles_processed || this.currentReviewData.filtered_vin_list.length;
            this.processingResults.filesGenerated += result.files_generated || 0;

        } catch (error) {
            console.error('Error processing reviewed LIST order:', error);
            alert(`Error processing VINs: ${error.message}`);
            this.processingResults.errors.push(`${currentOrder.name}: ${error.message}`);
        }

        // Move to next dealership or complete
        this.currentListIndex++;

        if (this.currentListIndex < this.listOrders.length) {
            this.showCurrentListOrder();
        } else {
            this.proceedToReview();
        }
    }
    
    proceedToReview() {
        // Initialize completed dealerships tracking for this session
        this.completedDealerships = new Set();
        console.log('Initialized completed dealerships tracking for review stage');

        this.updateModalProgress('review');
        this.showStep('review');
        this.renderReviewSummary();
    }
    
    renderReviewSummary() {
        // Set up dealership selector if multiple dealerships
        this.setupDealershipSelector();

        // Update table headers based on current dealership template variant
        this.updateTableHeaders();

        // Don't overwrite the vehicle data table - just populate it
        this.populateModalVehicleDataTable();
        this.updateModalDownloadButton();
    }

    updateTableHeaders() {
        // Get current dealership's template variant
        const currentDealership = this.selectedReviewDealership ||
                                (this.processedOrders && this.processedOrders[0] && this.processedOrders[0].dealership);

        console.log('🔍 DEBUG updateTableHeaders: currentDealership =', currentDealership);
        console.log('🔍 DEBUG updateTableHeaders: this =', this);
        console.log('🔍 DEBUG updateTableHeaders: this.constructor.name =', this.constructor.name);
        console.log('🔍 DEBUG updateTableHeaders: this.dealerships =', this.dealerships ? 'AVAILABLE' : 'NULL');

        // Compare this to window.app
        console.log('🔍 DEBUG: this === window.app =', this === window.app);
        console.log('🔍 DEBUG: window.app.dealerships =', window.app?.dealerships ? 'AVAILABLE' : 'NULL');

        if (!currentDealership) return;

        if (this.dealerships) {
            console.log('🔍 DEBUG: Total dealerships loaded =', this.dealerships.length);
            const glendaleDealer = this.dealerships.find(d => d.name === 'Glendale CDJR');
            console.log('🔍 DEBUG: Glendale CDJR found =', glendaleDealer ? 'YES' : 'NO');
            if (glendaleDealer) {
                console.log('🔍 DEBUG: Glendale data keys =', Object.keys(glendaleDealer));
                console.log('🔍 DEBUG: Glendale output_rules =', glendaleDealer.output_rules);
            }
        }

        // Check if dealership uses SCP + $ format (Glendale format)
        // Use fallback to window.app.dealerships if this.dealerships is not available (modal context)
        const dealerships = this.dealerships || window.app?.dealerships;
        const dealershipData = dealerships?.find(d => d.name === currentDealership);
        console.log('🔍 DEBUG: dealershipData found =', dealershipData ? 'YES' : 'NO');

        const outputRules = dealershipData?.output_rules || {};
        const templateVariant = outputRules.template_variant || 'standard';
        console.log('🔍 DEBUG: outputRules =', outputRules);
        console.log('🔍 DEBUG: templateVariant =', templateVariant);

        const isGlendaleFormat = templateVariant === 'glendale_format';
        console.log('🔍 DEBUG: isGlendaleFormat =', isGlendaleFormat);

        // Update table headers
        const headerRow = document.querySelector('#modalVehicleDataTable thead tr');
        if (!headerRow) return;

        if (isGlendaleFormat) {
            // Glendale format: Empty, Year/Model, Trim, Price, Stock, VIN, Raw Status, Data Type, Actions
            headerRow.innerHTML = `
                <th></th>
                <th>Year/Model</th>
                <th>Trim</th>
                <th>Price</th>
                <th>Stock</th>
                <th>VIN</th>
                <th class="raw-status-header">Raw Status</th>
                <th class="data-toggle-header">Data Type</th>
                <th></th>
            `;
        } else {
            // Standard format: Empty, Year/Make, Model, Trim, Stock, VIN, Raw Status, Data Type, Actions
            headerRow.innerHTML = `
                <th></th>
                <th>Year/Make</th>
                <th>Model</th>
                <th>Trim</th>
                <th>Stock</th>
                <th>VIN</th>
                <th class="raw-status-header">Raw Status</th>
                <th class="data-toggle-header">Data Type</th>
                <th></th>
            `;
        }

        console.log(`Updated table headers for ${isGlendaleFormat ? 'Glendale' : 'standard'} format`);
    }

    setupDealershipSelector() {
        console.log('🏢 SETUP DEALERSHIP SELECTOR: Starting...');
        const selectorSection = document.getElementById('modalDealershipSelector');
        const tabsContainer = document.getElementById('modalDealershipTabs');

        console.log('🏢 SETUP: Elements found:', {
            selectorSection: !!selectorSection,
            tabsContainer: !!tabsContainer
        });

        if (!selectorSection || !tabsContainer) {
            console.warn('🚨 SETUP: Dealership selector elements not found!');
            console.log('🔍 SETUP: Available modal elements:', {
                allElements: document.querySelectorAll('[id*="modal"]').length,
                reviewSummary: !!document.getElementById('modalReviewSummary')
            });
            return;
        }

        // Get all processed dealerships
        const dealerships = new Map();

        console.log('🏢 SETUP: Processing orders:', this.processedOrders?.length || 0);

        // Add processed orders
        this.processedOrders.forEach(order => {
            console.log('🏢 SETUP: Checking order:', {
                dealership: order.dealership,
                hasResult: !!order.result,
                vehiclesGenerated: order.result?.vehicles_generated,
                success: order.result?.success
            });

            // Check for vehicles_processed (current API) or vehicles_generated (legacy)
            const vehicleCount = order.result?.vehicles_processed || order.result?.vehicles_generated || 0;

            // Check if this dealership has already been completed
            const isCompleted = this.completedDealerships && this.completedDealerships.has(order.dealership);
            console.log(`🏢 SETUP: ${order.dealership} - isCompleted: ${isCompleted}`);

            if (order.result && order.result.success && vehicleCount > 0 && !isCompleted) {
                dealerships.set(order.dealership, {
                    name: order.dealership,
                    count: vehicleCount,
                    type: 'cao',
                    data: order
                });
                console.log('🏢 SETUP: Added dealership:', order.dealership, 'with', vehicleCount, 'vehicles');
            } else if (isCompleted) {
                console.log(`🏢 SETUP: Skipped ${order.dealership} - already completed via individual processing`);
            }
        });

        // Add maintenance results
        if (this.maintenanceResults && this.maintenanceResults.length > 0) {
            this.maintenanceResults.forEach(result => {
                // Include both CAO and manual VINs in the count
                const vehicleCount = (result.caoResults?.vehicles?.length || 0) + (result.manualVins?.length || 0);
                dealerships.set(result.order.name, {
                    name: result.order.name,
                    count: vehicleCount,
                    type: 'maintenance',
                    data: result
                });
            });
        }

        console.log('🏢 SETUP: Final dealership count:', dealerships.size);
        console.log('🏢 SETUP: Dealerships found:', Array.from(dealerships.keys()));

        // Show selector only if multiple dealerships
        if (dealerships.size <= 1) {
            console.log('🏢 SETUP: Not showing selector - only', dealerships.size, 'dealerships');
            selectorSection.style.display = 'none';
            // Set to the single dealership name if available
            if (dealerships.size === 1) {
                this.selectedReviewDealership = Array.from(dealerships.keys())[0];
                console.log('🏢 SETUP: Single dealership mode, set selectedReviewDealership to:', this.selectedReviewDealership);
            } else {
                this.selectedReviewDealership = null;
            }
            return;
        }

        console.log('🏢 SETUP: Showing dealership selector for', dealerships.size, 'dealerships');
        selectorSection.style.display = 'block';

        // Initialize selected dealership to first available dealership instead of 'all'
        if (!this.selectedReviewDealership || this.selectedReviewDealership === 'all') {
            // Set to first dealership if available, otherwise 'all'
            const firstDealership = Array.from(dealerships.keys())[0];
            this.selectedReviewDealership = firstDealership || 'all';
        }

        // Render dealership tabs
        let tabsHTML = '';

        // Add "All Dealerships" tab
        const totalVehicles = Array.from(dealerships.values()).reduce((sum, d) => sum + d.count, 0);
        tabsHTML += `
            <div class="dealership-tab all-dealerships ${this.selectedReviewDealership === 'all' ? 'active' : ''}"
                 data-dealership="all">
                <i class="fas fa-list tab-icon"></i>
                <span class="tab-name">All Dealerships</span>
                <span class="vehicle-count">${totalVehicles}</span>
            </div>
        `;

        // Add individual dealership tabs
        Array.from(dealerships.values()).forEach(dealership => {
            tabsHTML += `
                <div class="dealership-tab ${this.selectedReviewDealership === dealership.name ? 'active' : ''}"
                     data-dealership="${dealership.name}">
                    <i class="fas fa-building tab-icon"></i>
                    <span class="tab-name">${dealership.name}</span>
                    <span class="vehicle-count">${dealership.count}</span>
                </div>
            `;
        });

        tabsContainer.innerHTML = tabsHTML;

        // Add click event listeners
        tabsContainer.addEventListener('click', (e) => {
            const tab = e.target.closest('.dealership-tab');
            if (tab) {
                const dealership = tab.dataset.dealership;
                this.switchReviewDealership(dealership);
            }
        });

        // Update current dealership badge
        this.updateCurrentDealershipBadge();
    }

    switchReviewDealership(dealershipName) {
        console.log('Switching review to dealership:', dealershipName);

        // Save current dealership's edited data before switching
        if (this.selectedReviewDealership && this.selectedReviewDealership !== 'all' && this.reviewVehicleData) {
            console.log(`[REVIEW] Saving edited data for ${this.selectedReviewDealership}: ${this.reviewVehicleData.length} vehicles`);
            this.dealershipEditedData.set(this.selectedReviewDealership, [...this.reviewVehicleData]);
            this.dealershipReviewStatus.set(this.selectedReviewDealership, true);
        }

        this.selectedReviewDealership = dealershipName;

        // Update active tab
        document.querySelectorAll('.dealership-tab').forEach(tab => {
            tab.classList.remove('active');
        });

        const activeTab = document.querySelector(`[data-dealership="${dealershipName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Update current dealership badge
        this.updateCurrentDealershipBadge();

        // Update table headers for new dealership
        this.updateTableHeaders();

        // Load saved data for new dealership if it exists
        if (dealershipName !== 'all' && this.dealershipEditedData.has(dealershipName)) {
            console.log(`[REVIEW] Loading saved data for ${dealershipName}`);
            this.reviewVehicleData = [...this.dealershipEditedData.get(dealershipName)];
        }

        // Refresh vehicle data table for selected dealership
        this.populateModalVehicleDataTable();
        this.updateModalDownloadButton();
    }

    updateCurrentDealershipBadge() {
        const badge = document.getElementById('modalCurrentDealership');
        const nameSpan = document.getElementById('modalCurrentDealershipName');

        if (!badge || !nameSpan) return;

        if (this.selectedReviewDealership && this.selectedReviewDealership !== 'all') {
            badge.style.display = 'flex';
            nameSpan.textContent = this.selectedReviewDealership;
        } else {
            badge.style.display = 'none';
        }
    }

    setupRawDataToggle() {
        console.log('🔄 SETUP RAW DATA TOGGLE: Starting...');
        const toggle = document.getElementById('modalRawDataToggle');

        if (!toggle) {
            console.warn('Raw data toggle not found');
            return;
        }

        // Store raw data toggle state
        this.showRawData = false;

        // Add event listener for toggle changes
        toggle.addEventListener('change', (e) => {
            console.log('🔄 RAW DATA TOGGLE: Changed to', e.target.checked);
            this.showRawData = e.target.checked;

            // Re-populate table with current mode
            this.populateModalVehicleDataTable();
        });

        console.log('✅ RAW DATA TOGGLE: Setup complete');
    }

    async fetchRawDataForVins(vins, dealership) {
        console.log('🔍 FETCH RAW DATA: Fetching raw data for VINs:', vins, 'from dealership:', dealership);

        try {
            const response = await fetch('/api/get_raw_scraper_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    vins: vins,
                    dealership: dealership
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const rawData = await response.json();
            console.log('✅ FETCH RAW DATA: Retrieved raw data:', rawData);
            return rawData;

        } catch (error) {
            console.error('❌ FETCH RAW DATA: Error fetching raw data:', error);
            return {};
        }
    }

    populateModalVehicleDataTable() {
        const tableBody = document.getElementById('modalVehicleDataBody');
        const vehicleCountEl = document.getElementById('modalVehicleCount');
        const noDataPlaceholder = document.getElementById('modalNoDataPlaceholder');
        
        if (!tableBody) {
            console.warn('modalVehicleDataBody element not found');
            return;
        }
        
        console.log('Populating modal vehicle data table...');
        console.log('Processed orders:', this.processedOrders);
        console.log('Selected dealership filter:', this.selectedReviewDealership);

        // Get all vehicles from processed orders, filtered by selected dealership
        let allVehicles = [];
        
        // Generate sample vehicle data for all processed orders (regular CAO/LIST orders)
        this.processedOrders.forEach(order => {
            // Filter by selected dealership
            if (this.selectedReviewDealership && this.selectedReviewDealership !== 'all') {
                if (order.dealership !== this.selectedReviewDealership) {
                    return; // Skip this dealership
                }
            }

            if (order.result) {
                // CRITICAL FIX: Use REAL vehicle data from API instead of sample data
                console.log('DEBUG: Full order result structure for', order.dealership, ':', order.result);
                console.log('DEBUG: Available keys in result:', Object.keys(order.result));

                // Check if this is prepared LIST data (no CSV yet) or processed data (with CSV)
                if (order.result.vehicles_for_review && order.result.phase === 'prepared_for_review') {
                    // This is prepared LIST data - use vehicles directly
                    console.log(`Using prepared vehicle data for ${order.dealership}: ${order.result.vehicles_for_review.length} vehicles`);
                    const vehicles = order.result.vehicles_for_review;

                    // DEBUG: Log the actual vehicle data structure to verify formatted fields
                    console.log('[LIST PREVIEW DEBUG] First vehicle data:', vehicles[0]);
                    console.log('[LIST PREVIEW DEBUG] Has YEARMAKE?', vehicles[0]?.YEARMAKE);
                    console.log('[LIST PREVIEW DEBUG] Has STOCK?', vehicles[0]?.STOCK);
                    console.log('[LIST PREVIEW DEBUG] Has VIN?', vehicles[0]?.VIN);

                    // Display the vehicles immediately
                    const tableBody = document.getElementById('modalVehicleDataBody') ||
                                    document.getElementById('modalVehicleTableBody') ||
                                    document.getElementById('vehicleTableBody');
                    const noDataPlaceholder = document.getElementById('modalNoDataPlaceholder');
                    const vehicleCountEl = document.getElementById('modalVehicleCount');

                    if (tableBody && vehicles.length > 0) {
                        this.renderVehicleTable(vehicles, tableBody);
                        console.log(`Populated table with ${vehicles.length} prepared vehicles for ${order.dealership}`);
                    }

                    if (noDataPlaceholder) noDataPlaceholder.style.display = 'none';
                    if (vehicleCountEl) vehicleCountEl.textContent = vehicles.length.toString();

                    // Add to allVehicles for display
                    allVehicles.push(...vehicles);

                } else if (order.result.phase1_data?.vehicles_data || order.result.download_csv) {
                    // CRITICAL FIX: Use vehicles_data from NEW method's phase1_data (which contains actual vehicle records)
                    // This ensures we show detailed vehicle data while keeping the count consistent with tab badges
                    if (order.result.phase1_data?.vehicles_data && Array.isArray(order.result.phase1_data.vehicles_data)) {
                        console.log(`Using NEW method vehicle data for ${order.dealership}: ${order.result.phase1_data.vehicles_data.length} vehicles`);
                        console.log(`Tab badge count from OLD method: ${order.result.vehicles_processed} vehicles`);
                        const vehicles = order.result.phase1_data.vehicles_data;

                        // Generate table-ready vehicle data from database records
                        // FORMAT FIXED: Use VDP Shortcut Pack structure instead of wrong PRICE/DATA_TYPE format
                        const formattedVehicles = vehicles.map((vehicle, index) => {
                            const year = vehicle.year || '';
                            const make = vehicle.make || '';
                            const model = vehicle.model || '';
                            const trim = vehicle.trim || '';
                            const stock = vehicle.stock || '';
                            const vin = vehicle.vin || '';
                            const vehicleCondition = vehicle.vehicle_condition || '';

                            // Determine vehicle type prefix (NEW or USED)
                            const isNewVehicle = vehicleCondition?.toLowerCase() === 'new' ||
                                                vehicle.vehicle_type?.toLowerCase() === 'new' ||
                                                vehicle.type?.toLowerCase() === 'new';
                            const typePrefix = isNewVehicle ? 'NEW' : 'USED';

                            // Generate QR filepath for Adobe processing
                            const dealershipName = order.dealership.replace(/\s+/g, '_');
                            const qrIndex = index + 1;
                            const qrFilepath = `C:\\Users\\Nick_Workstation\\Documents\\QRS\\${dealershipName}_QR_Code_${qrIndex}.png`;

                            // VDP Shortcut Pack format structure
                            return {
                                YEARMAKE: isNewVehicle ? `NEW ${year} ${make}` : `${year} ${make}`,
                                MODEL: model,
                                TRIM: trim,
                                STOCK: `${year} ${model} - ${stock}`,
                                VIN: `${typePrefix} - ${vin}`,
                                '@QR': qrFilepath,
                                QRYEARMODEL: `${year} ${model} - ${stock}`,
                                QRSTOCK: `${typePrefix} - ${vin}`,
                                '@QR2': qrFilepath,
                                MISC: `${year} ${model} - ${vin} - ${stock}`,
                                RAW_STATUS: vehicle.raw_status || vehicle.status || 'N/A'
                            };
                        });

                        // Display the vehicles immediately using NEW method data
                        const tableBody = document.getElementById('modalVehicleDataBody') ||
                                        document.getElementById('modalVehicleTableBody') ||
                                        document.getElementById('vehicleTableBody');
                        const noDataPlaceholder = document.getElementById('modalNoDataPlaceholder');
                        const vehicleCountEl = document.getElementById('modalVehicleCount');

                        if (tableBody && formattedVehicles.length > 0) {
                            this.renderVehicleTable(formattedVehicles, tableBody);
                            console.log(`Populated table with ${formattedVehicles.length} vehicles from NEW method data for ${order.dealership}`);
                        }

                        if (noDataPlaceholder) noDataPlaceholder.style.display = 'none';
                        if (vehicleCountEl) vehicleCountEl.textContent = formattedVehicles.length.toString();

                        // Add to allVehicles for display
                        allVehicles.push(...formattedVehicles);

                    } else if (order.result.download_csv) {
                        // Fallback: Fetch from CSV only if direct vehicle data is not available
                        console.log(`Falling back to CSV fetch for ${order.dealership}: ${order.result.download_csv}`);
                        this.fetchVehicleDataFromCSV(order.result.download_csv, order.dealership).then(vehicles => {
                            if (vehicles && vehicles.length > 0) {
                                const tableBody = document.getElementById('modalVehicleDataBody') ||
                                              document.getElementById('modalVehicleTableBody') ||
                                              document.getElementById('vehicleTableBody');
                                const noDataPlaceholder = document.getElementById('modalNoDataPlaceholder');
                                const vehicleCountEl = document.getElementById('modalVehicleCount');

                                if (tableBody) {
                                    if (this.showRawData) {
                                        const vins = vehicles.map(v => v.VIN || v.vin).filter(vin => vin);
                                        this.fetchRawDataForVins(vins, order.dealership).then(rawData => {
                                            this.renderVehicleTableWithRawData(vehicles, tableBody, rawData);
                                        });
                                    } else {
                                        this.renderVehicleTable(vehicles, tableBody);
                                    }
                                    console.log(`Populated table with ${vehicles.length} vehicles from CSV fallback for ${order.dealership}`);
                                }

                                if (noDataPlaceholder) noDataPlaceholder.style.display = 'none';
                                if (vehicleCountEl) vehicleCountEl.textContent = vehicles.length.toString();
                            }
                        }).catch(error => {
                            console.error(`Failed to fetch CSV data for ${order.dealership}:`, error);
                        });
                    }
                } else {
                    console.error(`No CSV file available for ${order.dealership}`);
                }
            }
        });
        
        console.log('Total vehicles to display:', allVehicles.length);
        
        // If we have vehicles, render them immediately
        if (allVehicles.length > 0) {
            console.log('✅ DISPLAYING VEHICLES: Found', allVehicles.length, 'vehicles to display');
            console.log('Sample vehicle data:', allVehicles[0]);
            
            // Hide placeholder and show table
            if (noDataPlaceholder) noDataPlaceholder.style.display = 'none';
            if (vehicleCountEl) vehicleCountEl.textContent = allVehicles.length.toString();
            
            // Store vehicle data globally for modal editing
            window.reviewVehicleData = allVehicles;
            
            // Generate and render table rows
            if (this.showRawData && allVehicles.length > 0) {
                // Extract VINs and dealerships for raw data fetching
                const vinsByDealership = {};
                allVehicles.forEach(vehicle => {
                    const dealership = vehicle.dealership;
                    const vin = vehicle.VIN || vehicle.vin;
                    if (dealership && vin) {
                        if (!vinsByDealership[dealership]) {
                            vinsByDealership[dealership] = [];
                        }
                        vinsByDealership[dealership].push(vin);
                    }
                });

                // Fetch raw data for all dealerships
                const rawDataPromises = Object.entries(vinsByDealership).map(([dealership, vins]) =>
                    this.fetchRawDataForVins(vins, dealership).then(rawData => ({ dealership, rawData }))
                );

                Promise.all(rawDataPromises).then(results => {
                    const combinedRawData = {};
                    results.forEach(({ dealership, rawData }) => {
                        Object.assign(combinedRawData, rawData);
                    });
                    this.renderVehicleTableWithRawData(allVehicles, tableBody, combinedRawData);
                });
            } else {
                this.renderVehicleTable(allVehicles, tableBody);
            }
            return;
        }
        
        // If still no vehicles, show placeholder
        if (allVehicles.length === 0) {
            tableBody.innerHTML = '';
            if (noDataPlaceholder) noDataPlaceholder.style.display = 'block';
            if (vehicleCountEl) vehicleCountEl.textContent = '0';
            console.log('No vehicles to display, showing placeholder');
            return;
        }
        
        // Hide placeholder
        if (noDataPlaceholder) noDataPlaceholder.style.display = 'none';
        
        // Store vehicle data for modal editing
        this.reviewVehicleData = allVehicles;

        // Also save to dealership-specific storage for batch processing
        if (this.selectedReviewDealership && this.selectedReviewDealership !== 'all') {
            console.log(`[REVIEW] Auto-saving data for ${this.selectedReviewDealership}: ${allVehicles.length} vehicles`);
            this.dealershipEditedData.set(this.selectedReviewDealership, [...allVehicles]);
        }
        
        // Generate table rows
        const tableRows = allVehicles.map((vehicle, index) => {
            return `
                <tr id="vehicle-row-${index}" data-editing="false">
                    <td>
                        <button class="btn-edit btn-icon-only" onclick="window.modalWizard.toggleRowEdit(${index})" id="edit-btn-${index}" title="Edit row">
                            <i class="fas fa-edit"></i>
                        </button>
                    </td>
                    <td class="editable-cell" data-field="year-make" data-index="${index}">
                        <span class="display-value">${vehicle.year || ''} ${vehicle.make || ''}</span>
                        <input type="text" class="edit-input" value="${vehicle.year || ''} ${vehicle.make || ''}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="model" data-index="${index}">
                        <span class="display-value">${vehicle.model || ''}</span>
                        <input type="text" class="edit-input" value="${vehicle.model || ''}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="trim" data-index="${index}">
                        <span class="display-value">${vehicle.trim || ''}</span>
                        <input type="text" class="edit-input" value="${vehicle.trim || ''}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="stock" data-index="${index}">
                        <span class="display-value stock-badge">${vehicle.stock || ''}</span>
                        <input type="text" class="edit-input" value="${vehicle.stock || ''}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="vin" data-index="${index}">
                        <span class="display-value vin-display" title="${vehicle.vin || ''}">${vehicle.vin || ''}</span>
                        <input type="text" class="edit-input" value="${vehicle.vin || ''}" style="display: none;" maxlength="17">
                    </td>
                    <td>
                        <span class="qr-status">
                            <i class="fas fa-qrcode"></i>
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
        
        console.log('Generated table rows:', tableRows.length, 'characters');
        tableBody.innerHTML = tableRows;
        if (vehicleCountEl) vehicleCountEl.textContent = allVehicles.length.toString();
        console.log('Table populated successfully');
    }
    
    generateSampleVehicleData(order) {
        // Generate sample vehicle data based on order results
        const vehicleCount = order.result.new_vehicles || order.result.vehicle_count || 27;
        const sampleVehicles = [];
        
        const makes = ['Lexus', 'Toyota', 'Honda', 'BMW', 'Mercedes'];
        const models = ['ES 350', 'RX 350', 'GX 460', 'IS 300', 'NX 300'];
        const types = ['Pre-Owned', 'Certified Pre-Owned', 'New'];
        
        console.log(`Generating ${vehicleCount} sample vehicles for ${order.dealership}`);
        
        for (let i = 0; i < vehicleCount; i++) {
            sampleVehicles.push({
                year: 2020 + Math.floor(Math.random() * 5),
                make: makes[Math.floor(Math.random() * makes.length)],
                model: models[Math.floor(Math.random() * models.length)],
                trim: '350L',
                stock: `${order.dealership.substring(0, 3).toUpperCase()}${(1000 + i).toString()}`,
                vin: this.generateSampleVin(),
                type: types[Math.floor(Math.random() * types.length)],
                price: 25000 + Math.floor(Math.random() * 30000),
                ext_color: 'Black',
                vehicle_url: `https://dealer.com/inventory/${i}`
            });
        }
        
        return sampleVehicles;
    }
    
    generateSampleVin() {
        const chars = 'ABCDEFGHJKLMNPRSTUVWXYZ123456789';
        let vin = '';
        for (let i = 0; i < 17; i++) {
            vin += chars[Math.floor(Math.random() * chars.length)];
        }
        return vin;
    }
    
    truncateVin(vin) {
        if (!vin || vin.length <= 10) return vin;
        return vin.substring(0, 8) + '...';
    }

    toggleRowEdit(index) {
        const row = document.getElementById(`vehicle-row-${index}`);
        const editBtn = document.getElementById(`edit-btn-${index}`);
        const saveBtn = document.getElementById(`save-btn-${index}`);
        const isEditing = row.getAttribute('data-editing') === 'true';
        
        if (isEditing) {
            // Cancel edit mode without saving
            this.setRowEditMode(index, false);
            editBtn.innerHTML = '<i class="fas fa-edit"></i>';
            editBtn.title = 'Edit row';
            saveBtn.style.display = 'none';
        } else {
            // Switch to edit mode
            this.setRowEditMode(index, true);
            editBtn.innerHTML = '<i class="fas fa-times"></i>';
            editBtn.title = 'Cancel edit';
            saveBtn.style.display = 'inline-flex';
        }
    }
    
    saveRowEdit(index) {
        // Save the changes and exit edit mode
        this.saveRowChanges(index);
        this.setRowEditMode(index, false);
        
        // Reset buttons
        const editBtn = document.getElementById(`edit-btn-${index}`);
        const saveBtn = document.getElementById(`save-btn-${index}`);
        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
        editBtn.title = 'Edit row';
        saveBtn.style.display = 'none';
        
        console.log(`Saved changes for row ${index}`);
    }

    setRowEditMode(index, editing) {
        const row = document.getElementById(`vehicle-row-${index}`);
        row.setAttribute('data-editing', editing);
        
        const cells = row.querySelectorAll('.editable-cell');
        cells.forEach(cell => {
            const displayValue = cell.querySelector('.display-value');
            const editInput = cell.querySelector('.edit-input');
            
            if (editing) {
                displayValue.style.display = 'none';
                editInput.style.display = 'block';
                editInput.focus();
            } else {
                displayValue.style.display = 'block';
                editInput.style.display = 'none';
            }
        });
    }

    async saveRowChanges(index) {
        const row = document.getElementById(`vehicle-row-${index}`);
        const cells = row.querySelectorAll('.editable-cell');
        
        cells.forEach(cell => {
            const field = cell.getAttribute('data-field');
            const displayValue = cell.querySelector('.display-value');
            const editInput = cell.querySelector('.edit-input');
            
            // Update display value with edited value
            if (field === 'year-make') {
                displayValue.textContent = editInput.value;
                // Parse year and make if needed
                const parts = editInput.value.split(' ');
                if (this.reviewVehicleData && this.reviewVehicleData[index]) {
                    this.reviewVehicleData[index].year = parts[0];
                    this.reviewVehicleData[index].make = parts.slice(1).join(' ');
                    // Update YEARMAKE field for CSV
                    this.reviewVehicleData[index].YEARMAKE = editInput.value;
                }
            } else {
                displayValue.textContent = editInput.value;
                // Update the vehicle data
                if (this.reviewVehicleData && this.reviewVehicleData[index]) {
                    // Map display field names to CSV field names
                    const fieldMapping = {
                        'model': 'MODEL',
                        'trim': 'TRIM', 
                        'stock': 'STOCK',
                        'vin': 'VIN'
                    };
                    const csvField = fieldMapping[field] || field;
                    this.reviewVehicleData[index][csvField] = editInput.value;
                }
            }
        });
        
        console.log('Row changes saved for index:', index);
        
        // Save changes to CSV file
        await this.saveToCSVFile();
    }
    
    async saveToCSVFile() {
        if (!this.reviewVehicleData || this.reviewVehicleData.length === 0) {
            console.log('No review vehicle data to save');
            return;
        }
        
        // Get the CSV filename from processed orders
        const csvFilename = this.processedOrders.length > 0 && 
                           this.processedOrders[0].result && 
                           this.processedOrders[0].result.download_csv ? 
                           this.processedOrders[0].result.download_csv.split('/').pop() : null;
                           
        if (!csvFilename) {
            console.error('Could not determine CSV filename for saving');
            return;
        }
        
        try {
            // Convert vehicle data back to CSV format
            const csvData = this.convertVehicleDataToCSV(this.reviewVehicleData);
            
            // Save to server
            const response = await fetch('/api/csv/save-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: csvFilename,
                    data: csvData
                })
            });
            
            if (response.ok) {
                console.log('✅ Changes saved to CSV file successfully');
            } else {
                console.error('❌ Failed to save changes to CSV file:', response.statusText);
            }
        } catch (error) {
            console.error('❌ Error saving changes to CSV file:', error);
        }
    }
    
    deleteVehicleRow(index) {
        if (!this.reviewVehicleData || index >= this.reviewVehicleData.length) {
            console.error('Invalid vehicle index for deletion:', index);
            return;
        }
        
        // Get the vehicle info for confirmation
        const vehicle = this.reviewVehicleData[index];
        const vehicleInfo = `${vehicle.YEARMAKE || vehicle.year || 'Unknown'} ${vehicle.MODEL || vehicle.model || ''} - ${vehicle.VIN || vehicle.vin || 'No VIN'}`;
        
        // Confirm deletion
        if (confirm(`Are you sure you want to delete this vehicle?\n\n${vehicleInfo}`)) {
            // Remove from data array
            this.reviewVehicleData.splice(index, 1);
            
            // Update vehicle count
            const vehicleCountElement = document.getElementById('modalVehicleCount');
            if (vehicleCountElement) {
                vehicleCountElement.textContent = this.reviewVehicleData.length;
            }
            
            // Re-render the table with updated indexes
            const tableBody = document.getElementById('modalVehicleDataBody');
            if (tableBody) {
                this.renderVehicleTable(this.reviewVehicleData, tableBody);
            }
            
            // Save changes to CSV
            this.saveToCSVFile();
            
            console.log(`Deleted vehicle at index ${index}: ${vehicleInfo}`);
        }
    }
    
    convertVehicleDataToCSV(vehicleData, format = 'raw', dealership = '') {
        if (!vehicleData || vehicleData.length === 0) {
            return '';
        }

        // NEW: Support both raw (CAO) and VDP (LIST) formats
        // CRITICAL FIX: Default to VDP format for NEW method consistency with OLD method
        // Always use VDP Shortcut Pack format unless explicitly requesting raw format
        if (format !== 'raw') {
            return this.convertVehicleDataToVDPFormat(vehicleData, dealership);
        }

        // FALLBACK: Raw database format for CAO orders (preserve all existing functionality)
        // Get headers from first vehicle object, exclude raw_status from CSV output
        const allHeaders = Object.keys(vehicleData[0]);
        const headers = allHeaders.filter(header =>
            !['raw_status', 'RAW_STATUS'].includes(header)
        );

        console.log('CSV export headers (raw_status excluded):', headers);

        // Create CSV content
        const csvRows = [headers.join(',')];

        vehicleData.forEach(vehicle => {
            const row = headers.map(header => {
                const value = vehicle[header] || '';
                // Escape commas and quotes in values
                return typeof value === 'string' && (value.includes(',') || value.includes('"'))
                    ? `"${value.replace(/"/g, '""')}"`
                    : value;
            });
            csvRows.push(row.join(','));
        });

        return csvRows.join('\n');
    }

    convertVehicleDataToVDPFormat(vehicleData, dealership = '') {
        // VDP CSV format specifically for LIST orders and Adobe processing
        console.log('Converting vehicle data to VDP CSV format for Adobe...');
        console.log(`[JS QR TRACE 4] convertVehicleDataToVDPFormat() called with:`);
        console.log(`[JS QR TRACE 4]   - Dealership: ${dealership}`);
        console.log(`[JS QR TRACE 4]   - Vehicle Count: ${vehicleData.length}`);
        console.log(`[JS QR TRACE 4]   - Sample Vehicle Structure:`, vehicleData.slice(0, 1));

        // VDP CSV Header - Standard Shortcut Pack format
        const csvRows = ['YEARMAKE,MODEL,TRIM,STOCK,VIN,@QR,QRYEARMODEL,QRSTOCK,@QR2,MISC'];

        vehicleData.forEach((vehicle, index) => {
            // Extract normalized vehicle data fields
            const year = vehicle.year || '';
            const make = vehicle.make || '';
            const model = vehicle.model || '';
            const trim = vehicle.trim || '';
            const stock = vehicle.stock || '';
            const vin = vehicle.vin || '';
            const vehicleCondition = vehicle.vehicle_condition || '';

            // Determine vehicle type prefix (NEW or USED) - check multiple possible fields
            const isNewVehicle = vehicleCondition?.toLowerCase() === 'new' ||
                                vehicle.vehicle_type?.toLowerCase() === 'new' ||
                                vehicle.type?.toLowerCase() === 'new';
            const typePrefix = isNewVehicle ? 'NEW' : 'USED';

            // Generate Nick's specific QR code filepaths for Adobe processing
            const dealershipName = dealership.replace(/\s+/g, '_'); // Replace spaces with underscores
            const qrIndex = index + 1; // 1-based index for QR codes
            const qrFilepath = `C:\\Users\\Nick_Workstation\\Documents\\QRS\\${dealershipName}_QR_Code_${qrIndex}.png`;

            // Build VDP CSV fields following exact Adobe format
            const yearmake = isNewVehicle ? `NEW ${year} ${make}` : `${year} ${make}`;
            const modelField = model;
            const trimField = trim;
            const stockField = `${year} ${model} - ${stock}`;
            const vinField = `${typePrefix} - ${vin}`;
            const qrField = qrFilepath; // Nick's specific QR filepath for Adobe
            const qryearmodel = `${year} ${model} - ${stock}`;
            const qrstock = `${typePrefix} - ${vin}`;
            const qr2Field = qrFilepath; // Duplicate QR filepath for @QR2 field
            // Fix MISC field casing to match reference format
            const miscField = `${year} ${model} - ${vin} - ${stock}`;

            // Escape CSV values that contain commas or quotes
            const escapeCSVValue = (value) => {
                const strValue = String(value || '');
                return strValue.includes(',') || strValue.includes('"')
                    ? `"${strValue.replace(/"/g, '""')}"`
                    : strValue;
            };

            // Create CSV row with proper VDP format
            const row = [
                escapeCSVValue(yearmake),
                escapeCSVValue(modelField),
                escapeCSVValue(trimField),
                escapeCSVValue(stockField),
                escapeCSVValue(vinField),
                escapeCSVValue(qrField),
                escapeCSVValue(qryearmodel),
                escapeCSVValue(qrstock),
                escapeCSVValue(qr2Field),
                escapeCSVValue(miscField)
            ];

            csvRows.push(row.join(','));

            console.log(`[VDP CSV] Row ${index + 1}: ${yearmake} | ${modelField} | ${trimField} | ${stockField} | ${vinField} | QR: ${qrFilepath}`);
        });

        console.log(`Generated VDP CSV with ${vehicleData.length} vehicles in Adobe format for ${dealership}`);
        return csvRows.join('\n');
    }
    
    async fetchVehicleDataFromCSV(csvUrl, dealership) {
        try {
            console.log(`Fetching CSV data for ${dealership} from ${csvUrl}`);
            
            // Add cache-busting to ensure fresh data
            const cacheBusterUrl = csvUrl + (csvUrl.includes('?') ? '&' : '?') + 't=' + Date.now();
            const response = await fetch(cacheBusterUrl, { cache: 'no-cache' });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const csvText = await response.text();
            console.log(`CSV content length: ${csvText.length} characters`);
            
            // Parse CSV into vehicle objects
            const lines = csvText.split('\n').filter(line => line.trim());
            if (lines.length < 2) {
                throw new Error('CSV file appears to be empty or invalid');
            }
            
            // Parse header row
            const headers = this.parseCSVLine(lines[0]);
            console.log('CSV headers:', headers);
            
            // Parse data rows into vehicle objects
            const vehicles = [];
            for (let i = 1; i < lines.length; i++) {
                const values = this.parseCSVLine(lines[i]);
                if (values.length > 0) {
                    const vehicle = {};
                    headers.forEach((header, index) => {
                        vehicle[header] = values[index] || '';
                    });
                    vehicles.push(vehicle);
                }
            }
            
            console.log(`Parsed ${vehicles.length} vehicles from CSV`);
            return vehicles;
            
        } catch (error) {
            console.error(`Error fetching CSV data for ${dealership}:`, error);
            throw error;
        }
    }
    
    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current);
        
        return result.map(field => field.trim());
    }
    
    renderVehicleTable(vehicles, tableBody) {
        if (!vehicles || vehicles.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9">No vehicles to display</td></tr>';
            return;
        }

        // Store vehicles for editing
        this.reviewVehicleData = vehicles;

        // Determine if we're using Glendale format
        const currentDealership = this.selectedReviewDealership ||
                                (this.processedOrders && this.processedOrders[0] && this.processedOrders[0].dealership);
        // Use fallback to window.app.dealerships if this.dealerships is not available (modal context)
        const dealerships = this.dealerships || window.app?.dealerships;
        const dealershipData = dealerships?.find(d => d.name === currentDealership);
        const outputRules = dealershipData?.output_rules || {};
        const templateVariant = outputRules.template_variant || 'standard';
        const isGlendaleFormat = templateVariant === 'glendale_format';

        // Generate table rows with actual vehicle data - map CSV columns to display format
        const rows = vehicles.map((vehicle, index) => {
            if (isGlendaleFormat) {
                // Glendale format: YEARMODEL, TRIM, PRICE, STOCK, VIN
                return `
                    <tr id="vehicle-row-${index}" data-editing="false">
                        <td>
                            <button class="btn-edit btn-icon-only" onclick="window.modalWizard.toggleRowEdit(${index})" id="edit-btn-${index}" title="Edit row">
                                <i class="fas fa-edit"></i>
                            </button>
                        </td>
                        <td class="editable-cell" data-field="yearmodel" data-index="${index}">
                            <span class="display-value">${vehicle.YEARMODEL || vehicle.yearmodel || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.YEARMODEL || vehicle.yearmodel || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="trim" data-index="${index}">
                            <span class="display-value">${vehicle.TRIM || vehicle.trim || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.TRIM || vehicle.trim || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="price" data-index="${index}">
                            <span class="display-value price-badge">${vehicle.PRICE || vehicle.price || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.PRICE || vehicle.price || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="stock" data-index="${index}">
                            <span class="display-value stock-badge">${vehicle.STOCK || vehicle.stock || vehicle.stock_number || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.STOCK || vehicle.stock || vehicle.stock_number || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="vin" data-index="${index}">
                            <span class="display-value vin-display" title="${vehicle.VIN || vehicle.vin || ''}">${vehicle.VIN || vehicle.vin || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.VIN || vehicle.vin || ''}" style="display: none;" maxlength="17">
                        </td>
                        <td class="raw-status-cell" data-field="raw_status" data-index="${index}">
                            <span class="display-value">${vehicle.raw_status || vehicle.RAW_STATUS || 'N/A'}</span>
                        </td>
                        <td class="toggle-cell" onclick="event.stopPropagation();">
                            <label class="data-toggle-switch">
                                <input type="checkbox" class="toggle-input" data-vin="${vehicle.VIN || vehicle.vin || ''}" onchange="window.modalWizard.toggleVehicleDataType('${vehicle.VIN || vehicle.vin || ''}', this)">
                                <span class="toggle-slider">
                                    <span class="toggle-label-raw">R</span>
                                    <span class="toggle-label-norm">N</span>
                                </span>
                            </label>
                        </td>
                        <td>
                            <button class="btn-save btn-icon-only" onclick="window.modalWizard.saveRowEdit(${index})" id="save-btn-${index}" title="Save changes" style="display: none;">
                                <i class="fas fa-save"></i>
                            </button>
                            <button class="btn-delete-row btn-icon-only" onclick="window.modalWizard.deleteVehicleRow(${index})" id="delete-btn-${index}" title="Delete row">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            } else {
                // Standard format: YEARMAKE, MODEL, TRIM, STOCK, VIN
                return `
                    <tr id="vehicle-row-${index}" data-editing="false">
                        <td>
                            <button class="btn-edit btn-icon-only" onclick="window.modalWizard.toggleRowEdit(${index})" id="edit-btn-${index}" title="Edit row">
                                <i class="fas fa-edit"></i>
                            </button>
                        </td>
                        <td class="editable-cell" data-field="year-make" data-index="${index}">
                            <span class="display-value">${vehicle.YEARMAKE || vehicle.year || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.YEARMAKE || vehicle.year || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="model" data-index="${index}">
                            <span class="display-value">${vehicle.MODEL || vehicle.model || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.MODEL || vehicle.model || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="trim" data-index="${index}">
                            <span class="display-value">${vehicle.TRIM || vehicle.trim || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.TRIM || vehicle.trim || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="stock" data-index="${index}">
                            <span class="display-value stock-badge">${vehicle.STOCK || vehicle.stock || vehicle.stock_number || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.STOCK || vehicle.stock || vehicle.stock_number || ''}" style="display: none;">
                        </td>
                        <td class="editable-cell" data-field="vin" data-index="${index}">
                            <span class="display-value vin-display" title="${vehicle.VIN || vehicle.vin || ''}">${vehicle.VIN || vehicle.vin || ''}</span>
                            <input type="text" class="edit-input" value="${vehicle.VIN || vehicle.vin || ''}" style="display: none;" maxlength="17">
                        </td>
                        <td class="raw-status-cell" data-field="raw_status" data-index="${index}">
                            <span class="display-value">${vehicle.raw_status || vehicle.RAW_STATUS || 'N/A'}</span>
                        </td>
                        <td class="toggle-cell" onclick="event.stopPropagation();">
                            <label class="data-toggle-switch">
                                <input type="checkbox" class="toggle-input" data-vin="${vehicle.VIN || vehicle.vin || ''}" onchange="window.modalWizard.toggleVehicleDataType('${vehicle.VIN || vehicle.vin || ''}', this)">
                                <span class="toggle-slider">
                                    <span class="toggle-label-raw">R</span>
                                    <span class="toggle-label-norm">N</span>
                                </span>
                            </label>
                        </td>
                        <td>
                            <button class="btn-save btn-icon-only" onclick="window.modalWizard.saveRowEdit(${index})" id="save-btn-${index}" title="Save changes" style="display: none;">
                                <i class="fas fa-save"></i>
                            </button>
                            <button class="btn-delete-row btn-icon-only" onclick="window.modalWizard.deleteVehicleRow(${index})" id="delete-btn-${index}" title="Delete row">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }
        }).join('');

        tableBody.innerHTML = rows;
        console.log(`Rendered ${vehicles.length} vehicle rows in table (${isGlendaleFormat ? 'Glendale' : 'standard'} format)`);

        // EMERGENCY: Force raw_status data via DOM injection (bypasses all caching)
        this.injectRawStatusData(vehicles, tableBody);
    }
    
    async injectRawStatusData(vehicles, tableBody) {
        console.log('🚨 EMERGENCY DOM INJECTION: Forcing raw_status data into table cells');

        // Determine current dealership from active tab, NOT from first order
        let dealership = null;

        // First try: Get from active dealership tab
        const activeDealershipTab = document.querySelector('.dealership-tab.active');
        if (activeDealershipTab) {
            dealership = activeDealershipTab.getAttribute('data-dealership');
            if (dealership === 'all') {
                dealership = null; // Can't inject for "all" view
            }
        }

        // Second try: Use selectedReviewDealership property
        if (!dealership && this.selectedReviewDealership && this.selectedReviewDealership !== 'all') {
            dealership = this.selectedReviewDealership;
        }

        // Third try: Fall back to first order (single dealership scenario)
        if (!dealership && this.processedOrders && this.processedOrders.length === 1) {
            dealership = this.processedOrders[0].dealership;
        }

        if (!dealership) {
            console.error('❌ Cannot inject raw_status: No dealership found');
            return;
        }

        console.log(`🎯 Injecting raw_status for dealership: ${dealership}`);
        
        try {
            // Fetch raw_status data directly 
            const response = await fetch(`/api/vehicles/raw-status/${encodeURIComponent(dealership)}`, {
                cache: 'no-cache'
            });
            
            if (!response.ok) {
                console.error('❌ Raw status API failed:', response.status);
                return;
            }
            
            const rawStatusData = await response.json();
            console.log(`✅ Retrieved raw_status for ${Object.keys(rawStatusData).length} vehicles`);
            
            // Force inject raw_status into existing table cells
            const rows = tableBody.querySelectorAll('tr');
            rows.forEach((row, index) => {
                if (index < vehicles.length) {
                    const vehicle = vehicles[index];
                    let vin = vehicle.VIN || vehicle.vin || '';
                    
                    // Extract actual VIN from formatted string (e.g., "USED - 1FA6P8CF3R5408633" -> "1FA6P8CF3R5408633")
                    if (vin.includes(' - ')) {
                        vin = vin.split(' - ').pop();
                    }
                    
                    const rawStatus = rawStatusData[vin] || 'N/A';
                    
                    // Find the raw_status cell and force update it
                    const rawStatusCell = row.querySelector('.raw-status-cell .display-value');
                    if (rawStatusCell) {
                        rawStatusCell.textContent = rawStatus;
                        console.log(`🔗 INJECTED: ${vin} -> ${rawStatus}`);
                    } else {
                        console.warn(`❌ No raw_status cell found for row ${index}`);
                    }
                }
            });
            
        } catch (error) {
            console.error('💥 Raw status injection failed:', error);
        }
    }
    
    updateModalDownloadButton() {
        const downloadBtn = document.getElementById('modalDownloadCsv');
        if (!downloadBtn) return;

        // Show download button if there are processed orders
        if (this.processedOrders.length > 0) {
            downloadBtn.style.display = 'inline-flex';
            downloadBtn.onclick = () => {
                this.downloadCurrentDealershipCsv();
            };
        } else {
            downloadBtn.style.display = 'none';
        }
    }

    async downloadCurrentDealershipCsv() {
        console.log('[ENHANCED DOWNLOAD] Starting enhanced download with edited data...');

        // Check if we have edited review data
        if (!this.reviewVehicleData || this.reviewVehicleData.length === 0) {
            console.error('[ENHANCED DOWNLOAD] No review vehicle data available');
            alert('No vehicle data available for download. Please load vehicle data first.');
            return;
        }

        // Determine dealership name
        let dealershipName = null;

        // Check if we have a dealership selector (multi-dealership mode)
        const dealershipSelector = document.getElementById('modalDealershipSelector');
        const isMultiMode = dealershipSelector && dealershipSelector.style.display !== 'none';

        if (isMultiMode && this.selectedReviewDealership) {
            dealershipName = this.selectedReviewDealership;
            console.log('[ENHANCED DOWNLOAD] Multi-dealership mode, using selected:', dealershipName);
        } else {
            // Single dealership mode: get dealership from processed orders
            if (this.processedOrders.length > 0) {
                dealershipName = this.processedOrders[0].dealership;
                console.log('[ENHANCED DOWNLOAD] Single dealership mode, using:', dealershipName);
            }
        }

        if (!dealershipName) {
            console.error('[ENHANCED DOWNLOAD] Could not determine dealership name');
            alert('Could not determine dealership name for download');
            return;
        }

        // Prompt for order number
        const orderNumber = prompt('Enter order number for this download:', '');
        if (!orderNumber || orderNumber.trim() === '') {
            console.log('[ENHANCED DOWNLOAD] User cancelled or entered empty order number');
            return;
        }

        try {
            // Convert current edited vehicle data to CSV
            console.log('[ENHANCED DOWNLOAD] Converting edited vehicle data to CSV...');
            const csvData = this.convertVehicleDataToCSV(this.reviewVehicleData);

            if (!csvData) {
                console.error('[ENHANCED DOWNLOAD] Failed to convert vehicle data to CSV');
                alert('Failed to convert vehicle data to CSV format');
                return;
            }

            console.log('[ENHANCED DOWNLOAD] CSV data ready, calling enhanced download endpoint...');

            // Call the enhanced download endpoint
            const response = await fetch('/api/csv/enhanced-download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership_name: dealershipName,
                    order_number: orderNumber.trim(),
                    csv_data: csvData
                })
            });

            if (!response.ok) {
                throw new Error(`Enhanced download failed: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();
            console.log('[ENHANCED DOWNLOAD] Enhanced download successful:', result);

            if (result.success) {
                // Show success message with file counts
                const message = `Enhanced download completed successfully!

Files created:
• CSV File: ${result.vehicles_processed} vehicles
• QR Codes: ${result.qr_codes_generated} generated
• Billing CSV: ${result.billing_csv_generated ? 'Created' : 'Failed'}
• VIN Log: ${result.vin_log_updated ? 'Updated' : 'Failed'}

Output folder: ${result.output_folder}`;

                alert(message);

                // Open download links for each file type
                if (result.csv_download_url) {
                    console.log('[ENHANCED DOWNLOAD] Opening CSV download:', result.csv_download_url);
                    window.open(result.csv_download_url, '_blank');
                }

                if (result.billing_download_url) {
                    console.log('[ENHANCED DOWNLOAD] Opening billing CSV download:', result.billing_download_url);
                    setTimeout(() => window.open(result.billing_download_url, '_blank'), 500);
                }

                // Note: QR codes are saved to the output folder, no download URL needed
                console.log('[ENHANCED DOWNLOAD] QR codes saved to:', result.qr_folder);

            } else {
                console.error('[ENHANCED DOWNLOAD] Server reported failure:', result.error);
                alert(`Enhanced download failed: ${result.error}`);
            }

        } catch (error) {
            console.error('[ENHANCED DOWNLOAD] Error during enhanced download:', error);
            alert(`Enhanced download failed: ${error.message}`);
        }
    }
    
    async proceedToQRGeneration() {
        // BATCH PROCESS ALL DEALERSHIPS: New functionality for Generate QR button
        console.log('[BATCH QR] Starting batch processing of all dealerships with prepared data...');

        // Prevent multiple simultaneous calls
        if (this.batchProcessingInProgress) {
            console.log('[BATCH QR] Batch processing already in progress, ignoring duplicate call');
            return;
        }

        this.batchProcessingInProgress = true;

        // Save current dealership's edited data before batch processing
        if (this.selectedReviewDealership && this.selectedReviewDealership !== 'all' && this.reviewVehicleData) {
            console.log(`[BATCH QR] Saving current dealership data for ${this.selectedReviewDealership}: ${this.reviewVehicleData.length} vehicles`);
            this.dealershipEditedData.set(this.selectedReviewDealership, [...this.reviewVehicleData]);
            this.dealershipReviewStatus.set(this.selectedReviewDealership, true);
        }

        try {
            // Step 1: Identify all dealerships with prepared data
            const dealershipsWithData = this.getDealershipsWithPreparedData();

            if (dealershipsWithData.length === 0) {
                alert('No dealerships have prepared data ready for processing.');
                return;
            }

            console.log(`[BATCH QR] Found ${dealershipsWithData.length} dealerships with prepared data:`,
                       dealershipsWithData.map(d => d.name));

            // Step 2: Collect order numbers for each dealership
            const orderNumbers = await this.collectBatchOrderNumbers(dealershipsWithData);

            if (!orderNumbers) {
                console.log('[BATCH QR] Batch processing cancelled by user');
                return;
            }

            // Step 3: Process all dealerships in batch
            console.log('[BATCH QR] Processing all dealerships in batch...');
            const results = await this.processBatchDealerships(dealershipsWithData, orderNumbers);

            // Step 4: Show completion summary
            this.showBatchProcessingResults(results);

        } catch (error) {
            console.error('[BATCH QR] Error during batch processing:', error);
            alert('Error during batch processing: ' + error.message);
        } finally {
            this.batchProcessingInProgress = false;
        }
    }

    async processThisDealershipNow() {
        // Process the current dealership immediately with order number
        console.log('Processing current dealership immediately...');

        // Get current dealership and result from current processing state
        let currentDealership = null;
        let currentResult = null;

        // Get the currently selected dealership from the tabs
        const activeDealershipTab = document.querySelector('.dealership-tab.active');
        if (activeDealershipTab) {
            currentDealership = activeDealershipTab.getAttribute('data-dealership');

            // Skip "all" dealerships view - we need a specific dealership
            if (currentDealership === 'all') {
                alert('Please select a specific dealership to process (not "All Dealerships" view)');
                return;
            }

            // Check if this dealership was already processed
            if (this.completedDealerships && this.completedDealerships.has(currentDealership)) {
                alert(`${currentDealership} has already been processed. Please select a different dealership.`);
                return;
            }
        }

        // Alternative: get from selectedReviewDealership property
        if (!currentDealership && this.selectedReviewDealership && this.selectedReviewDealership !== 'all') {
            currentDealership = this.selectedReviewDealership;
        }

        // Final fallback: if we have only one processed order, use that dealership
        if (!currentDealership && this.processedOrders && this.processedOrders.length === 1) {
            currentDealership = this.processedOrders[0].dealership;
            console.log(`[SINGLE DEALERSHIP] Using dealership from processedOrders: ${currentDealership}`);
        }

        // Find the result for this dealership from processedOrders
        let dealershipOrder = null;
        if (currentDealership && this.processedOrders) {
            dealershipOrder = this.processedOrders.find(order =>
                order.dealership === currentDealership
            );
            if (dealershipOrder) {
                currentResult = dealershipOrder.result;
            }
        }

        if (!currentDealership) {
            alert('Could not determine which dealership to process');
            return;
        }

        // Check if we have either CSV data OR prepared LIST data OR maintenance data
        const isPreparedList = currentResult &&
                              dealershipOrder &&
                              dealershipOrder.type === 'list' &&
                              currentResult.phase === 'prepared_for_review' &&
                              currentResult.vehicles_for_review;

        const isMaintenance = currentResult &&
                             dealershipOrder &&
                             dealershipOrder.type === 'maintenance' &&
                             currentResult.phase === 'prepared_for_review' &&
                             currentResult.vehicles_for_review;

        if (!currentResult || (!currentResult.download_csv && !isPreparedList && !isMaintenance)) {
            alert('No CSV data or prepared LIST data available for this dealership');
            return;
        }

        // Prompt for order number
        const orderNumber = prompt(`Enter order number for ${currentDealership}:`, '');
        if (!orderNumber || !orderNumber.trim()) {
            alert('Order number is required to process');
            return;
        }

        // Show processing message
        console.log(`Processing ${currentDealership} with order number: ${orderNumber}`);

        try {
            console.log(`Processing ${currentDealership} with enhanced download functionality...`);

            // ENHANCED DOWNLOAD: Generate final files with order number using EDITED CSV data
            let enhancedResult = null;
            console.log(`[ENHANCED DOWNLOAD] Generating final files for ${currentDealership} with order number ${orderNumber} using edited CSV data`);

            try {
                // Check if we have edited review data OR prepared LIST data
                let vehicleDataToProcess = null;
                let csvData = null;

                // PRIORITY 1: Always use edited review data if available (user deletions/edits)
                if (this.reviewVehicleData && this.reviewVehicleData.length > 0) {
                    vehicleDataToProcess = this.reviewVehicleData;
                    if (isPreparedList || isMaintenance) {
                        // LIST/MAINTENANCE order: Use VDP format with user-edited data
                        csvData = this.convertVehicleDataToCSV(this.reviewVehicleData, 'vdp', currentDealership);
                        console.log('[ENHANCED DOWNLOAD] Using edited LIST/MAINTENANCE data with VDP format for', this.reviewVehicleData.length, 'vehicles');
                    } else {
                        // CAO order: Use raw format with user-edited data (preserve existing functionality)
                        csvData = this.convertVehicleDataToCSV(this.reviewVehicleData);
                        console.log('[ENHANCED DOWNLOAD] Using edited CSV data with', this.reviewVehicleData.length, 'vehicles');
                    }
                }
                // PRIORITY 2: Fallback to prepared LIST/MAINTENANCE data if no user edits
                else if ((isPreparedList || isMaintenance) && currentResult.vehicles_for_review && currentResult.vehicles_for_review.length > 0) {
                    vehicleDataToProcess = currentResult.vehicles_for_review;
                    csvData = this.convertVehicleDataToCSV(vehicleDataToProcess, 'vdp', currentDealership);
                    console.log('[ENHANCED DOWNLOAD] Using prepared LIST/MAINTENANCE data with VDP format for', vehicleDataToProcess.length, 'vehicles');
                }
                // No data available (preserve existing error handling)
                else {
                    console.error('[ENHANCED DOWNLOAD] No review vehicle data available');
                    throw new Error('No edited vehicle data available for processing');
                }

                // Get custom template configuration for this dealership
                const dealershipData = window.app?.dealerships?.find(d => d.name === currentDealership);
                const customTemplateConfig = dealershipData?.output_rules?.custom_templates || null;
                console.log(`[ENHANCED DOWNLOAD] Custom Template Config for ${currentDealership}:`, customTemplateConfig);

                // Get original VIN list for LIST orders (for billing ordered vs produced)
                const originalVinList = (isPreparedList && dealershipOrder && dealershipOrder.original_vin_list) ? dealershipOrder.original_vin_list : null;
                if (originalVinList) {
                    console.log(`[ENHANCED DOWNLOAD] LIST order detected - passing original VIN count: ${originalVinList.length}`);
                }

                // Call the enhanced download endpoint that preserves edits
                const enhancedResponse = await fetch('/api/csv/enhanced-download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        dealership_name: currentDealership,
                        order_number: orderNumber.trim(),
                        csv_data: csvData,
                        custom_templates: customTemplateConfig,
                        original_vin_list: originalVinList  // For LIST orders billing (ordered vs produced)
                    })
                });

                if (enhancedResponse.ok) {
                    enhancedResult = await enhancedResponse.json();
                    console.log(`[ENHANCED DOWNLOAD] Successfully generated final files for ${currentDealership}:`, enhancedResult);
                } else {
                    const errorData = await enhancedResponse.json();
                    throw new Error(errorData.error || 'Failed to generate final files with enhanced download');
                }
            } catch (error) {
                console.error(`[ENHANCED DOWNLOAD] Failed to generate final files for ${currentDealership}:`, error.message);
                throw error; // Fail the process if enhanced download fails since this is the main functionality
            }

            // Show success message using enhanced result
            const successMessage = `Successfully processed ${currentDealership}!\n\n` +
                `Order Number: ${orderNumber}\n` +
                `QR Codes Generated: ${enhancedResult.qr_codes_generated || 0}\n` +
                `VINs Updated: ${enhancedResult.vin_log_updated ? enhancedResult.vehicles_processed || 0 : 0}\n` +
                `${enhancedResult.billing_csv_generated ? 'Billing CSV Generated\n' : ''}` +
                `${enhancedResult ? `[ENHANCED DOWNLOAD] Final files generated with edited data and order number\n` : ''}` +
                `${enhancedResult.output_folder ? `Files saved to: ${enhancedResult.output_folder_name || 'orders folder'}` : ''}`;

            alert(successMessage);

            // Remove this dealership from the tabs if it was successfully processed
            // Find the tab either from activeDealershipTab or by searching for it
            let tabToRemove = activeDealershipTab;
            if (!tabToRemove && currentDealership) {
                tabToRemove = document.querySelector(`[data-dealership="${currentDealership}"]`);
            }

            if (tabToRemove) {
                // Track processed dealerships separately - DO NOT remove from processedOrders
                // as other dealerships still need their data
                if (!this.completedDealerships) {
                    this.completedDealerships = new Set();
                }
                this.completedDealerships.add(currentDealership);
                console.log(`Marked ${currentDealership} as completed. Total completed: ${this.completedDealerships.size}`);

                // Remove the tab from UI only
                tabToRemove.remove();
                console.log(`Removed ${currentDealership} tab from UI`);

                // Find remaining dealership tabs (excluding "All Dealerships" tab) using document instead of tabContainer
                // to ensure we search the entire DOM after the removal
                const remainingTabs = document.querySelectorAll('.dealership-tab:not(.all-dealerships)');
                console.log(`DEBUG: Total dealership tabs found: ${document.querySelectorAll('.dealership-tab').length}`);
                console.log(`DEBUG: All dealerships tabs found: ${document.querySelectorAll('.dealership-tab.all-dealerships').length}`);
                console.log(`DEBUG: Non-all dealership tabs found: ${remainingTabs.length}`);

                // Filter out completed dealerships from remaining tabs
                const availableTabs = Array.from(remainingTabs).filter(tab => {
                    const tabDealership = tab.dataset.dealership;
                    const isCompleted = this.completedDealerships && this.completedDealerships.has(tabDealership);
                    console.log(`DEBUG: Tab ${tabDealership} - completed: ${isCompleted}`);
                    return !isCompleted;
                });

                console.log(`Remaining available dealership tabs after removal: ${availableTabs.length}`);
                if (availableTabs.length > 0) {
                    availableTabs.forEach((tab, index) => {
                        console.log(`DEBUG: Available tab ${index}: ${tab.dataset.dealership}`);
                    });
                }

                if (availableTabs.length > 0) {
                    // Select the first remaining dealership
                    const nextDealership = availableTabs[0].dataset.dealership;
                    console.log(`Auto-selecting next dealership: ${nextDealership}`);

                    // Switch to the next dealership properly
                    this.switchReviewDealership(nextDealership);

                    // Update the review data for the new dealership
                    this.selectedReviewDealership = nextDealership;
                    console.log(`Switched to dealership: ${nextDealership}`);
                } else {
                    // All dealerships processed, complete the wizard
                    console.log('All dealerships processed - no more tabs remaining');
                    setTimeout(() => {
                        if (confirm('All dealerships have been processed. Complete the wizard?')) {
                            this.completeProcessing();
                        }
                    }, 500);
                }

                // Update the "All Dealerships" tab count if it exists
                const allDealershipsTab = document.querySelector('.all-dealerships .vehicle-count');
                if (allDealershipsTab) {
                    const currentTotal = parseInt(allDealershipsTab.textContent) || 0;
                    const processedCount = enhancedResult.vehicles_processed || 0;
                    allDealershipsTab.textContent = Math.max(0, currentTotal - processedCount);
                }
            }

        } catch (error) {
            console.error('Error processing dealership:', error);
            alert(`Failed to process ${currentDealership}: ${error.message}`);
        }
    }

    renderVehicleTableWithRawData(vehicles, tableBody, rawData) {
        console.log('🗂️ RENDER RAW DATA TABLE: Starting with', vehicles.length, 'vehicles and raw data:', Object.keys(rawData).length, 'entries');

        if (!vehicles || vehicles.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8">No vehicles to display</td></tr>';
            return;
        }

        // Store vehicles for editing
        this.reviewVehicleData = vehicles;

        // Generate table rows with raw data - show all available fields
        const rows = vehicles.map((vehicle, index) => {
            const vin = vehicle.VIN || vehicle.vin || '';
            const rawVehicle = rawData[vin] || {};

            // Display raw data fields or normalized data as fallback
            const yearMake = rawVehicle.year_make || rawVehicle.YEARMAKE || vehicle.YEARMAKE || vehicle.year || '';
            const model = rawVehicle.model || rawVehicle.MODEL || vehicle.MODEL || vehicle.model || '';
            const trim = rawVehicle.trim || rawVehicle.TRIM || vehicle.TRIM || vehicle.trim || '';
            const stock = rawVehicle.stock_number || rawVehicle.STOCK || vehicle.STOCK || vehicle.stock || vehicle.stock_number || '';
            const rawStatus = rawVehicle.vehicle_condition || rawVehicle.raw_status || rawVehicle.RAW_STATUS || vehicle.raw_status || vehicle.RAW_STATUS || 'N/A';

            return `
                <tr id="vehicle-row-${index}" data-editing="false" class="raw-data-row">
                    <td>
                        <button class="btn-edit btn-icon-only" onclick="window.modalWizard.toggleRowEdit(${index})" id="edit-btn-${index}" title="Edit row">
                            <i class="fas fa-edit"></i>
                        </button>
                    </td>
                    <td class="editable-cell" data-field="year-make" data-index="${index}">
                        <span class="display-value">${yearMake}</span>
                        <input type="text" class="edit-input" value="${yearMake}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="model" data-index="${index}">
                        <span class="display-value">${model}</span>
                        <input type="text" class="edit-input" value="${model}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="trim" data-index="${index}">
                        <span class="display-value">${trim}</span>
                        <input type="text" class="edit-input" value="${trim}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="stock" data-index="${index}">
                        <span class="display-value stock-badge">${stock}</span>
                        <input type="text" class="edit-input" value="${stock}" style="display: none;">
                    </td>
                    <td class="editable-cell" data-field="vin" data-index="${index}">
                        <span class="display-value vin-display" title="${vin}">${vin}</span>
                        <input type="text" class="edit-input" value="${vin}" style="display: none;" maxlength="17">
                    </td>
                    <td class="raw-status-cell raw-data-status" data-field="raw_status" data-index="${index}">
                        <span class="display-value raw-status-badge">${rawStatus}</span>
                        <div class="raw-data-tooltip">
                            <i class="fas fa-info-circle"></i>
                            <div class="tooltip-content">
                                <strong>Raw Scraper Data:</strong><br>
                                ${Object.entries(rawVehicle).map(([key, value]) => `${key}: ${value || 'N/A'}`).join('<br>')}
                            </div>
                        </div>
                    </td>
                    <td>
                        <button class="btn-save btn-icon-only" onclick="window.modalWizard.saveRowEdit(${index})" id="save-btn-${index}" title="Save changes" style="display: none;">
                            <i class="fas fa-save"></i>
                        </button>
                        <button class="btn-delete-row btn-icon-only" onclick="window.modalWizard.deleteVehicleRow(${index})" id="delete-btn-${index}" title="Delete row">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = rows;
        console.log(`✅ RENDER RAW DATA TABLE: Rendered ${vehicles.length} vehicle rows with raw data`);
    }

    setupMultiDealershipOrderInput() {
        console.log('🏢 SETUP MULTI-DEALERSHIP ORDER INPUT: Starting...');

        const singleOrderInput = document.getElementById('singleOrderInput');
        const multiOrderInput = document.getElementById('multiOrderInput');
        const dealershipOrderList = document.getElementById('dealershipOrderList');

        // Get successful dealerships with vehicles (same logic as dealership selector)
        const dealerships = new Map();

        this.processedOrders.forEach(order => {
            const vehicleCount = order.result?.vehicles_processed || order.result?.vehicles_generated || 0;
            if (order.result && order.result.success && vehicleCount > 0) {
                dealerships.set(order.dealership, {
                    name: order.dealership,
                    count: vehicleCount,
                    type: 'cao',
                    data: order
                });
            }
        });

        // Add maintenance results if any
        if (this.maintenanceResults && this.maintenanceResults.length > 0) {
            this.maintenanceResults.forEach(result => {
                // Include both CAO and manual VINs in the count
                const vehicleCount = (result.caoResults?.vehicles?.length || 0) + (result.manualVins?.length || 0);
                if (vehicleCount > 0) {
                    dealerships.set(result.order.name, {
                        name: result.order.name,
                        count: vehicleCount,
                        type: 'maintenance',
                        data: result
                    });
                }
            });
        }

        console.log('🏢 ORDER INPUT: Found', dealerships.size, 'dealerships with vehicles');

        // Show multi-input for 2+ dealerships, single input for 1 dealership
        if (dealerships.size <= 1) {
            singleOrderInput.style.display = 'block';
            multiOrderInput.style.display = 'none';
            return;
        }

        // Set up multi-dealership interface
        singleOrderInput.style.display = 'none';
        multiOrderInput.style.display = 'block';

        // Clear existing content
        dealershipOrderList.innerHTML = '';

        // Create input for each dealership
        dealerships.forEach((dealershipData, dealershipName) => {
            const dealershipItem = document.createElement('div');
            dealershipItem.className = 'dealership-order-item';
            dealershipItem.innerHTML = `
                <div class="dealership-order-header">
                    <div class="dealership-order-name">
                        <i class="fas fa-building"></i>
                        ${dealershipName}
                    </div>
                    <div class="dealership-vehicle-count">${dealershipData.count} vehicles</div>
                </div>
                <div class="dealership-order-input">
                    <label for="orderNumber_${dealershipName.replace(/\s+/g, '_')}">Order Number for ${dealershipName}:</label>
                    <input type="text"
                           id="orderNumber_${dealershipName.replace(/\s+/g, '_')}"
                           class="form-control dealership-order-field"
                           data-dealership="${dealershipName}"
                           placeholder="e.g., SF24001-${dealershipName.split(' ').map(w => w[0]).join('')}"
                           maxlength="20" required>
                </div>
            `;
            dealershipOrderList.appendChild(dealershipItem);
        });

        console.log('🏢 ORDER INPUT: Created inputs for', dealerships.size, 'dealerships');
    }

    // NEW BATCH PROCESSING HELPER FUNCTIONS FOR GENERATE QR FUNCTIONALITY

    getDealershipsWithPreparedData() {
        // Identify dealerships that have prepared data ready for batch processing
        const dealerships = [];

        console.log('[BATCH QR] Checking for dealerships with prepared data...');
        console.log('[BATCH QR] processedOrders available:', !!this.processedOrders);
        console.log('[BATCH QR] processedOrders length:', this.processedOrders?.length || 0);

        // Check processedOrders for dealerships with prepared data
        if (this.processedOrders) {
            this.processedOrders.forEach((order, index) => {
                console.log(`[BATCH QR] Checking order ${index}: ${order.dealership}`);

                const hasPhase1Data = order.result && order.result.phase1_data &&
                                    order.result.phase1_data.ready_for_review;

                // Check for prepared LIST data (new functionality)
                const isPreparedList = order.type === 'list' &&
                                     order.result?.phase === 'prepared_for_review' &&
                                     order.result?.vehicles_for_review;

                // Get vehicle count from different sources based on order type
                const vehicleCount = order.result?.vehicle_count || // prepared LIST data
                                   order.result?.new_vehicles ||
                                   order.result?.vehicles_processed ||
                                   0;

                const hasSuccess = order.result && order.result.success;

                console.log(`[BATCH QR] ${order.dealership} - success: ${hasSuccess}, vehicleCount: ${vehicleCount}, hasPhase1Data: ${hasPhase1Data}, isPreparedList: ${isPreparedList}`);

                // For batch processing, include dealerships that have successful results with vehicles > 0
                // Include both CSV orders with phase1_data AND prepared LIST orders
                // BUT exclude dealerships that have already been completed via individual processing
                const isAlreadyCompleted = this.completedDealerships && this.completedDealerships.has(order.dealership);

                console.log(`[BATCH QR] ${order.dealership} - isAlreadyCompleted: ${isAlreadyCompleted}`);

                if (hasSuccess && vehicleCount > 0 && !isAlreadyCompleted) {
                    dealerships.push({
                        name: order.dealership,
                        count: vehicleCount,
                        type: isPreparedList ? 'list' : 'cao', // Set correct type for LIST orders
                        data: order,
                        phase1Data: order.result.phase1_data
                    });
                    console.log(`[BATCH QR] Added dealership: ${order.dealership} (${vehicleCount} vehicles, type: ${isPreparedList ? 'list' : 'cao'})`);
                } else if (isAlreadyCompleted) {
                    console.log(`[BATCH QR] Skipped ${order.dealership} - already completed via individual processing`);
                }
            });
        }

        // Add maintenance results if any
        if (this.maintenanceResults && this.maintenanceResults.length > 0) {
            this.maintenanceResults.forEach(result => {
                // Include both CAO and manual VINs in the count
                const vehicleCount = (result.caoResults?.vehicles?.length || 0) + (result.manualVins?.length || 0);
                if (vehicleCount > 0) {
                    dealerships.push({
                        name: result.order.name,
                        count: vehicleCount,
                        type: 'maintenance',
                        data: result
                    });
                    console.log(`[BATCH QR] Added maintenance result: ${result.order.name} (${vehicleCount} vehicles)`);
                }
            });
        }

        console.log(`[BATCH QR] getDealershipsWithPreparedData found ${dealerships.length} dealerships:`,
                   dealerships.map(d => `${d.name} (${d.count} vehicles)`));
        return dealerships;
    }

    async collectBatchOrderNumbers(dealerships) {
        // Collect order numbers for each dealership that will be batch processed
        const orderNumbers = new Map();

        console.log('[BATCH QR] Collecting order numbers for batch processing...');

        // Create a simple dialog to collect order numbers with improved styling
        const dialogHTML = `
            <div id="batchOrderDialog" class="modal-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 99999;
            ">
                <div class="modal-content" style="
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    max-width: 600px;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    position: relative;
                ">
                    <div class="modal-header" style="margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">Batch Processing - Enter Order Numbers</h3>
                        <p style="margin: 0; color: #666;">Enter order numbers for each dealership to be processed:</p>
                    </div>
                    <div class="modal-body" style="margin-bottom: 20px;">
                        <div id="batchOrderList">
                            ${dealerships.map(dealership => `
                                <div class="dealership-batch-item" style="
                                    margin-bottom: 15px;
                                    padding: 15px;
                                    border: 1px solid #ddd;
                                    border-radius: 5px;
                                    background: #f9f9f9;
                                ">
                                    <div style="
                                        font-weight: bold;
                                        margin-bottom: 8px;
                                        color: #333;
                                        font-size: 14px;
                                    ">
                                        ${dealership.name} (${dealership.count} vehicles)
                                    </div>
                                    <input type="text"
                                           id="batchOrder_${dealership.name.replace(/\s+/g, '_')}"
                                           class="form-control batch-order-field"
                                           data-dealership="${dealership.name}"
                                           placeholder="Enter order number..."
                                           style="
                                               width: 100%;
                                               padding: 10px;
                                               border: 1px solid #ccc;
                                               border-radius: 4px;
                                               font-size: 14px;
                                               box-sizing: border-box;
                                           "
                                           maxlength="20" required>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="modal-footer" style="
                        display: flex;
                        gap: 10px;
                        justify-content: flex-end;
                        border-top: 1px solid #eee;
                        padding-top: 15px;
                    ">
                        <button id="batchOrderCancel" class="btn-wizard secondary" style="
                            padding: 10px 20px;
                            border: 1px solid #ccc;
                            background: #f5f5f5;
                            color: #333;
                            border-radius: 4px;
                            cursor: pointer;
                        ">Cancel</button>
                        <button id="batchOrderProcess" class="btn-wizard primary" style="
                            padding: 10px 20px;
                            border: none;
                            background: #007bff;
                            color: white;
                            border-radius: 4px;
                            cursor: pointer;
                        ">Process All Dealerships</button>
                    </div>
                </div>
            </div>
        `;

        // Add dialog to DOM
        document.body.insertAdjacentHTML('beforeend', dialogHTML);
        console.log('[BATCH QR] Dialog HTML added to DOM');

        return new Promise((resolve) => {
            const dialog = document.getElementById('batchOrderDialog');
            const cancelBtn = document.getElementById('batchOrderCancel');
            const processBtn = document.getElementById('batchOrderProcess');

            console.log('[BATCH QR] Dialog elements found:', {
                dialog: !!dialog,
                cancelBtn: !!cancelBtn,
                processBtn: !!processBtn
            });

            if (!dialog || !cancelBtn || !processBtn) {
                console.error('[BATCH QR] Failed to find dialog elements');
                resolve(null);
                return;
            }

            // Focus on the first input field
            setTimeout(() => {
                const firstInput = dialog.querySelector('.batch-order-field');
                if (firstInput) {
                    firstInput.focus();
                }
            }, 100);

            cancelBtn.onclick = () => {
                console.log('[BATCH QR] User cancelled batch processing');
                dialog.remove();
                resolve(null);
            };

            processBtn.onclick = () => {
                console.log('[BATCH QR] User clicked Process All Dealerships');
                const orderFields = document.querySelectorAll('.batch-order-field');
                let hasErrors = false;

                orderFields.forEach(field => {
                    const orderNumber = field.value.trim();
                    if (!orderNumber) {
                        field.style.borderColor = '#ff4444';
                        field.style.backgroundColor = '#fff5f5';
                        hasErrors = true;
                    } else {
                        field.style.borderColor = '#ccc';
                        field.style.backgroundColor = 'white';
                        orderNumbers.set(field.dataset.dealership, orderNumber);
                    }
                });

                if (hasErrors) {
                    alert('Please enter order numbers for all dealerships.');
                    return;
                }

                console.log('[BATCH QR] All order numbers collected:', Object.fromEntries(orderNumbers));
                dialog.remove();
                resolve(orderNumbers);
            };

            // Add ESC key support
            document.addEventListener('keydown', function escHandler(event) {
                if (event.key === 'Escape') {
                    document.removeEventListener('keydown', escHandler);
                    dialog.remove();
                    resolve(null);
                }
            });
        });
    }

    async processBatchDealerships(dealerships, orderNumbers) {
        // Process all dealerships in batch with their order numbers
        const results = [];

        console.log('[BATCH QR] Starting batch processing of dealerships...');

        for (const dealership of dealerships) {
            const orderNumber = orderNumbers.get(dealership.name);

            try {
                console.log(`[BATCH QR] Processing ${dealership.name} with order number: ${orderNumber}`);

                // Get the current vehicle data for this dealership (including any edits)
                let vehicleData = null;

                // First check if we have saved edited data for this dealership
                if (this.dealershipEditedData.has(dealership.name)) {
                    vehicleData = this.dealershipEditedData.get(dealership.name);
                    console.log(`[BATCH QR] Using saved edited vehicle data for ${dealership.name}: ${vehicleData.length} vehicles`);
                } else if (this.selectedReviewDealership === dealership.name && this.reviewVehicleData) {
                    // If it's the current dealership, save the edited data first
                    vehicleData = this.reviewVehicleData;
                    this.dealershipEditedData.set(dealership.name, [...vehicleData]);
                    console.log(`[BATCH QR] Using current edited vehicle data for ${dealership.name}: ${vehicleData.length} vehicles`);
                } else {
                    // Check if this is prepared LIST data (new functionality)
                    if (dealership.data.type === 'list' &&
                        dealership.data.result.phase === 'prepared_for_review' &&
                        dealership.data.result.vehicles_for_review) {
                        vehicleData = dealership.data.result.vehicles_for_review;
                        console.log(`[BATCH QR] Using prepared LIST data for ${dealership.name}: ${vehicleData.length} vehicles`);
                    }
                    // Fall back to original CSV data (preserve existing functionality)
                    else {
                        const csvUrl = dealership.data.result.download_csv;
                        if (csvUrl) {
                            const csvResponse = await fetch(csvUrl);
                            const csvText = await csvResponse.text();
                            vehicleData = this.parseCSVData(csvText);
                            console.log(`[BATCH QR] Using original CSV data for ${dealership.name}: ${vehicleData.length} vehicles`);
                        }
                    }
                }

                if (!vehicleData || vehicleData.length === 0) {
                    throw new Error(`No vehicle data available for ${dealership.name}`);
                }

                // Use the generate-final-files endpoint for proper template processing
                const response = await fetch('/api/orders/generate-final-files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        dealership_name: dealership.name,
                        vehicles_data: vehicleData,
                        order_number: orderNumber,
                        template_type: null, // Let system determine from dealership config
                        skip_vin_logging: false // We want proper VIN logging for batch processing
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    console.log(`[BATCH QR] Successfully processed ${dealership.name}`);
                    results.push({
                        dealership: dealership.name,
                        success: true,
                        result: result,
                        vehicleCount: vehicleData.length
                    });
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Processing failed');
                }

            } catch (error) {
                console.error(`[BATCH QR] Error processing ${dealership.name}:`, error);
                results.push({
                    dealership: dealership.name,
                    success: false,
                    error: error.message,
                    vehicleCount: 0
                });
            }
        }

        return results;
    }

    showBatchProcessingResults(results) {
        // Show summary of batch processing results
        const successCount = results.filter(r => r.success).length;
        const errorCount = results.filter(r => !r.success).length;
        const totalVehicles = results.reduce((sum, r) => sum + (r.vehicleCount || 0), 0);

        console.log('[BATCH QR] Batch processing completed');
        console.log('[BATCH QR] Results:', results);

        const summaryHTML = `
            <div id="batchResultsDialog" class="modal-overlay" style="display: block; z-index: 10000;">
                <div class="modal-content" style="max-width: 700px;">
                    <div class="modal-header">
                        <h3>Batch Processing Complete</h3>
                    </div>
                    <div class="modal-body">
                        <div class="batch-summary" style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px;">
                            <h4>Summary</h4>
                            <p><strong>Dealerships Processed:</strong> ${successCount} successful, ${errorCount} failed</p>
                            <p><strong>Total Vehicles:</strong> ${totalVehicles}</p>
                        </div>

                        <div class="batch-details">
                            <h4>Details</h4>
                            ${results.map(result => `
                                <div class="result-item" style="margin-bottom: 10px; padding: 10px; border-left: 4px solid ${result.success ? '#28a745' : '#dc3545'}; background: ${result.success ? '#d4edda' : '#f8d7da'};">
                                    <div style="font-weight: bold;">${result.dealership}</div>
                                    ${result.success ?
                                        `<div style="color: #155724;">✅ Successfully processed ${result.vehicleCount} vehicles</div>` :
                                        `<div style="color: #721c24;">❌ Error: ${result.error}</div>`
                                    }
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button id="batchResultsClose" class="btn-wizard primary">Close</button>
                    </div>
                </div>
            </div>
        `;

        // Add dialog to DOM
        document.body.insertAdjacentHTML('beforeend', summaryHTML);

        // Handle close button
        document.getElementById('batchResultsClose').onclick = () => {
            document.getElementById('batchResultsDialog').remove();
        };

        // Mark all processed dealerships as completed
        if (!this.completedDealerships) {
            this.completedDealerships = new Set();
        }

        results.forEach(result => {
            if (result.success) {
                this.completedDealerships.add(result.dealership);
            }
        });
    }

    parseCSVData(csvText) {
        // Parse CSV text into vehicle data objects (helper function for batch processing)
        try {
            const lines = csvText.split('\n').filter(line => line.trim());
            if (lines.length < 2) {
                console.warn('CSV file appears to be empty or invalid');
                return [];
            }

            // Parse header row
            const headers = this.parseCSVLine(lines[0]);

            // Parse data rows into vehicle objects
            const vehicles = [];
            for (let i = 1; i < lines.length; i++) {
                const values = this.parseCSVLine(lines[i]);
                if (values.length > 0) {
                    const vehicle = {};
                    headers.forEach((header, index) => {
                        vehicle[header] = values[index] || '';
                    });
                    vehicles.push(vehicle);
                }
            }

            console.log(`[BATCH QR] parseCSVData: Parsed ${vehicles.length} vehicles from CSV`);
            return vehicles;

        } catch (error) {
            console.error('[BATCH QR] Error parsing CSV data:', error);
            return [];
        }
    }

    generateFinalOutput() {
        const singleOrderInput = document.getElementById('singleOrderInput');
        const multiOrderInput = document.getElementById('multiOrderInput');

        // Check if we're in single or multi mode
        const isMultiMode = multiOrderInput.style.display !== 'none';

        if (isMultiMode) {
            // Validate all dealership order numbers
            const dealershipOrderFields = document.querySelectorAll('.dealership-order-field');
            const orderNumbers = new Map();
            let hasErrors = false;

            dealershipOrderFields.forEach(field => {
                const dealership = field.dataset.dealership;
                const orderNumber = field.value.trim();

                if (!orderNumber) {
                    field.style.borderColor = '#ff4444';
                    hasErrors = true;
                } else {
                    field.style.borderColor = '';
                    orderNumbers.set(dealership, orderNumber);
                }
            });

            if (hasErrors) {
                alert('Please enter order numbers for all dealerships');
                return;
            }

            // Store order numbers for each dealership
            this.dealershipOrderNumbers = orderNumbers;
            console.log('🏢 ORDER NUMBERS: Collected for', orderNumbers.size, 'dealerships:', Object.fromEntries(orderNumbers));

        } else {
            // Single dealership mode
            const orderNumberInput = document.getElementById('modalOrderNumber');
            const orderNumber = orderNumberInput?.value.trim();

            if (!orderNumber) {
                alert('Please enter an order number');
                return;
            }

            // Store single order number
            this.singleOrderNumber = orderNumber;
        }

        // Complete the process
        this.completeProcessing();
    }
    
    async completeProcessing() {
        console.log('[PHASE 2] Starting final file generation before completion...');

        try {
            // PHASE 2: Generate final files for all dealerships with prepared data + order numbers
            await this.generateAllFinalFiles();
        } catch (error) {
            console.error('[PHASE 2] Error during final file generation:', error);
            alert(`Error generating final files: ${error.message}`);
            return;
        }

        this.updateModalProgress('complete');
        this.showStep('complete');

        const completionContainer = document.getElementById('modalCompletionDetails');
        if (completionContainer) {
            completionContainer.innerHTML = `
                <div class="completion-stats">
                    <div class="stat-card">
                        <div class="stat-value">${this.processingResults.totalDealerships}</div>
                        <div class="stat-label">Total Dealerships</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${this.processingResults.caoProcessed}</div>
                        <div class="stat-label">CAO Processed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${this.processingResults.listProcessed}</div>
                        <div class="stat-label">List Processed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${this.processingResults.totalVehicles}</div>
                        <div class="stat-label">Total Vehicles</div>
                    </div>
                </div>
            `;
            
            // FORCE DARK MODE FIXES - Bypass CSS caching
            setTimeout(() => {
                this.forceDarkModeStyles();
            }, 100);
        }
    }
    
    forceDarkModeStyles() {
        // CRITICAL: Force dark mode styles when CSS caching interferes
        const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
        if (!isDarkMode) return;
        
        console.log('FORCING DARK MODE STYLES - CSS CACHE BYPASS');
        
        // Force all summary cards dark styling
        const summaryCards = document.querySelectorAll('#orderWizardModal .summary-card');
        summaryCards.forEach(card => {
            card.style.background = 'rgba(15, 23, 42, 0.95)';
            card.style.border = '1px solid rgba(51, 65, 85, 0.5)';
            
            const cardTitle = card.querySelector('h4');
            if (cardTitle) {
                cardTitle.style.color = '#f8fafc';
                cardTitle.style.fontWeight = '600';
            }
            
            const cardCount = card.querySelector('.card-count');
            if (cardCount) {
                cardCount.style.color = '#ffffff';
                cardCount.style.fontWeight = '700';
            }
            
            const cardText = card.querySelectorAll('p');
            cardText.forEach(p => {
                p.style.color = '#cbd5e1';
            });
            
            const cardValues = card.querySelectorAll('.card-value, .card-details');
            cardValues.forEach(val => {
                val.style.color = '#ffffff';
                val.style.fontWeight = '600';
            });
        });
        
        // Force statistics cards (stat-card class)
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach(card => {
            card.style.background = 'rgba(15, 23, 42, 0.95)';
            card.style.border = '1px solid rgba(51, 65, 85, 0.5)';
            
            const statValue = card.querySelector('.stat-value');
            if (statValue) {
                statValue.style.color = '#ffffff';
                statValue.style.fontWeight = '700';
            }
            
            const statLabel = card.querySelector('.stat-label');
            if (statLabel) {
                statLabel.style.color = '#cbd5e1';
            }
        });
    }

    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            const nextStepName = this.steps[this.currentStep];
            
            if (nextStepName === 'list') {
                this.proceedToListProcessing();
            } else if (nextStepName === 'review') {
                this.proceedToReview();
            } else if (nextStepName === 'orderNumber') {
                this.proceedToQRGeneration();
            } else if (nextStepName === 'complete') {
                this.completeProcessing();
            }
        }
    }
    
    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            const previousStepName = this.steps[this.currentStep];
            this.updateModalProgress(previousStepName);
            this.showStep(previousStepName);
        }
    }
    
    viewOrderFolder() {
        alert('Order files have been generated and are available in the output directories.');
    }
    
    startNewOrder() {
        if (confirm('Start a new order? This will close the wizard.')) {
            this.closeModal();
        }
    }
    
    closeModal() {
        const modal = document.getElementById('orderWizardModal');
        if (modal) {
            modal.classList.remove('show');
            // Also remove any inline style that might interfere
            modal.style.display = '';
        }
        
        // Dispatch custom event to clear the main app's processing queue
        window.dispatchEvent(new CustomEvent('modalWizardComplete', {
            detail: { action: 'clearQueue' }
        }));
        
        // Reset wizard state
        this.currentStep = 0;
        this.currentListIndex = 0;
        this.processedOrders = [];
        this.processingResults = {
            totalDealerships: 0,
            caoProcessed: 0,
            listProcessed: 0,
            totalVehicles: 0,
            filesGenerated: 0,
            errors: []
        };
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Manual VIN Entry Functions
    initializeManualVinEntry() {
        // Set up tab switching (this is called during app init when elements may not exist)
        const csvImportTab = document.getElementById('csvImportTab');
        const manualEntryTab = document.getElementById('manualEntryTab');
        const csvSection = document.getElementById('csvImportSection');
        const manualSection = document.getElementById('manualEntrySection');
        
        if (csvImportTab && manualEntryTab) {
            csvImportTab.addEventListener('click', () => {
                this.switchImportMethod('csv');
            });
            
            manualEntryTab.addEventListener('click', () => {
                this.switchImportMethod('manual');
            });
        }
    }
    
    initializeManualVinEntryForModal() {
        // Set up tab switching for modal elements (called when modal opens)
        const csvImportTab = document.getElementById('csvImportTab');
        const manualEntryTab = document.getElementById('manualEntryTab');
        
        if (csvImportTab && !csvImportTab.hasManualEntryEvents) {
            csvImportTab.addEventListener('click', () => {
                console.log('CSV Import tab clicked');
                this.switchImportMethod('csv');
            });
            csvImportTab.hasManualEntryEvents = true;
        }
        
        if (manualEntryTab && !manualEntryTab.hasManualEntryEvents) {
            manualEntryTab.addEventListener('click', () => {
                console.log('Manual Entry tab clicked');
                this.switchImportMethod('manual');
            });
            manualEntryTab.hasManualEntryEvents = true;
        }
        
        // Set up manual entry textarea monitoring
        const textarea = document.getElementById('manualOrderEntry');
        if (textarea) {
            textarea.addEventListener('input', () => {
                this.updateManualEntryStats();
            });
        }
        
        // Set up manual entry action buttons
        const validateBtn = document.getElementById('validateManualEntry');
        const clearBtn = document.getElementById('clearManualEntry');
        
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                this.validateManualEntry();
            });
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearManualEntry();
            });
        }
    }
    
    switchImportMethod(method) {
        console.log('switchImportMethod called with:', method);
        const csvImportTab = document.getElementById('csvImportTab');
        const manualEntryTab = document.getElementById('manualEntryTab');
        const csvSection = document.getElementById('csvImportSection');
        const manualSection = document.getElementById('manualEntrySection');
        const importButtonText = document.getElementById('importButtonText');
        const importButtonIcon = document.getElementById('importButtonIcon');
        const importBtn = document.getElementById('startVinLogImport');
        const importManualBtn = document.getElementById('importManualVins');
        
        console.log('Elements found:', {
            csvImportTab: !!csvImportTab,
            manualEntryTab: !!manualEntryTab,
            csvSection: !!csvSection,
            manualSection: !!manualSection
        });
        
        if (method === 'csv') {
            csvImportTab?.classList.add('active');
            manualEntryTab?.classList.remove('active');
            if (csvSection) csvSection.style.display = 'block';
            if (manualSection) manualSection.style.display = 'none';
            
            // TEMPLATE CACHE BYPASS - Use body attribute to control CSS pseudo-button
            document.body.removeAttribute('data-manual-mode');
            
            // Show CSV import button, hide manual import button
            if (importBtn) {
                importBtn.style.display = '';
                importBtn.disabled = !this.selectedVinLogFile;
                importBtn.style.cursor = this.selectedVinLogFile ? 'pointer' : 'not-allowed';
            }
            if (importManualBtn) {
                importManualBtn.style.display = 'none';
            }
            
            // Update button text and icon for CSV import
            if (importButtonText) importButtonText.textContent = 'Import CSV';
            if (importButtonIcon) {
                importButtonIcon.className = 'fas fa-upload';
            }
        } else if (method === 'manual') {
            csvImportTab?.classList.remove('active');
            manualEntryTab?.classList.add('active');
            if (csvSection) csvSection.style.display = 'none';
            if (manualSection) manualSection.style.display = 'block';
            
            // TEMPLATE CACHE BYPASS - Transform existing Import CSV button for manual mode
            console.log('TEMPLATE CACHE BYPASS: Converting Import CSV button to manual mode');
            
            if (importBtn) {
                // Keep the existing button visible but transform it for manual use
                importBtn.style.display = '';
                
                // Change button text and appearance
                if (importButtonText) importButtonText.textContent = 'Import Manual VINs';
                if (importButtonIcon) importButtonIcon.className = 'fas fa-keyboard';
                
                // Transform button to green for manual mode (template cache bypass)
                importBtn.style.background = 'linear-gradient(135deg, #10b981, #059669) !important';
                importBtn.style.borderColor = '#10b981 !important';
                importBtn.style.color = 'white !important';
                
                console.log('TEMPLATE CACHE BYPASS: Import CSV button transformed to manual import button');
                
                // Update button state based on manual entry content
                const textarea = document.getElementById('manualOrderEntry');
                if (textarea) {
                    importBtn.disabled = !textarea.value.trim();
                } else {
                    importBtn.disabled = true;
                }
            }
            
            // Initialize manual entry functionality if not already done
            this.updateManualEntryStats();
        }
        
        // Store current method for import processing
        this.currentImportMethod = method;
    }
    
    updateManualEntryStats() {
        console.log('=== UPDATE MANUAL ENTRY STATS CALLED ===');
        const textarea = document.getElementById('manualOrderEntry');
        const orderCountEl = document.getElementById('manualOrderCount');
        const vinCountEl = document.getElementById('manualVinCount');
        const importBtn = document.getElementById('startVinLogImport');
        
        console.log('Elements found:', {
            textarea: !!textarea,
            orderCountEl: !!orderCountEl,
            vinCountEl: !!vinCountEl,
            importBtn: !!importBtn
        });
        
        if (!textarea || !orderCountEl || !vinCountEl) {
            console.error('Missing required elements for stats update');
            return;
        }
        
        const text = textarea.value.trim();
        console.log('Textarea value:', text);
        
        if (!text) {
            orderCountEl.textContent = '0';
            vinCountEl.textContent = '0';
            console.log('No text found, setting counts to 0');
            
            if (importBtn && this.currentImportMethod === 'manual') {
                importBtn.disabled = true;
            }
            return;
        }
        
        // SIMPLE COUNTING LOGIC - Same as validation
        const lines = text.split('\n').map(line => line.trim()).filter(line => line);
        let orders = 0;
        let vins = 0;
        
        for (let line of lines) {
            if (line.length === 17 && /^[A-HJ-NPR-Z0-9]+$/i.test(line)) {
                vins++;
                console.log('Found VIN:', line);
            } else if (line.length > 0 && line.length < 17) {
                orders++;
                console.log('Found Order:', line);
            }
        }
        
        // UPDATE THE DISPLAY
        orderCountEl.textContent = orders.toString();
        vinCountEl.textContent = vins.toString();
        
        console.log('Updated stats:', { orders, vins });
        
        // Enable button if we have content
        const hasContent = orders > 0 || vins > 0;
        if (importBtn && this.currentImportMethod === 'manual') {
            importBtn.disabled = !hasContent;
            console.log('Import button state:', { disabled: !hasContent });
        }
    }
    
    parseManualEntry(text) {
        const lines = text.split('\n');
        const orders = [];
        let currentOrder = null;
        let totalVins = 0;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Empty line indicates end of current order group
            if (!line) {
                if (currentOrder) {
                    orders.push(currentOrder);
                    currentOrder = null;
                }
                continue;
            }
            
            // Check if this looks like a VIN (17 characters, alphanumeric)
            const isVin = /^[A-HJ-NPR-Z0-9]{17}$/i.test(line);
            
            if (isVin) {
                // This is a VIN
                if (currentOrder) {
                    currentOrder.vins.push(line.toUpperCase());
                    totalVins++;
                } else {
                    // VIN without order number - this is an error
                    console.warn(`VIN found without order number at line ${i + 1}: ${line}`);
                }
            } else {
                // This should be an order number
                if (currentOrder) {
                    // Previous order wasn't closed with empty line
                    orders.push(currentOrder);
                }
                currentOrder = {
                    orderNumber: line,
                    vins: [],
                    lineNumber: i + 1
                };
            }
        }
        
        // Don't forget the last order if text doesn't end with empty line
        if (currentOrder) {
            orders.push(currentOrder);
        }
        
        return {
            orders,
            totalVins,
            errors: []
        };
    }
    
    validateManualEntry() {
        const textarea = document.getElementById('manualOrderEntry');
        const resultsDiv = document.getElementById('manualValidationResults');
        const contentDiv = document.getElementById('manualValidationContent');
        
        if (!textarea || !resultsDiv || !contentDiv) return;
        
        const text = textarea.value.trim();
        if (!text) {
            this.showManualValidationResults('Please enter order data to validate.', 'warning');
            return;
        }
        
        const parsed = this.parseManualEntry(text);
        const errors = [];
        const warnings = [];
        
        // Validate each order
        parsed.orders.forEach((order, index) => {
            // Check order number format
            if (!order.orderNumber || order.orderNumber.length < 3) {
                errors.push(`Order ${index + 1} (line ${order.lineNumber}): Order number too short or missing`);
            }
            
            // Check for VINs
            if (order.vins.length === 0) {
                errors.push(`Order ${index + 1} (${order.orderNumber}): No VINs found`);
            }
            
            // Validate VIN format
            order.vins.forEach((vin, vinIndex) => {
                if (!/^[A-HJ-NPR-Z0-9]{17}$/i.test(vin)) {
                    errors.push(`Order ${index + 1} (${order.orderNumber}), VIN ${vinIndex + 1}: Invalid VIN format - ${vin}`);
                }
            });
            
            // Check for excessive VINs in one order
            if (order.vins.length > 50) {
                warnings.push(`Order ${index + 1} (${order.orderNumber}): Large number of VINs (${order.vins.length})`);
            }
        });
        
        // Check for duplicate order numbers
        const orderNumbers = parsed.orders.map(o => o.orderNumber);
        const duplicates = orderNumbers.filter((item, index) => orderNumbers.indexOf(item) !== index);
        if (duplicates.length > 0) {
            errors.push(`Duplicate order numbers found: ${[...new Set(duplicates)].join(', ')}`);
        }
        
        // Check for duplicate VINs
        const allVins = parsed.orders.flatMap(o => o.vins);
        const duplicateVins = allVins.filter((item, index) => allVins.indexOf(item) !== index);
        if (duplicateVins.length > 0) {
            warnings.push(`Duplicate VINs found: ${[...new Set(duplicateVins)].join(', ')}`);
        }
        
        // Generate results
        let resultHtml = '';
        
        if (errors.length === 0 && warnings.length === 0) {
            resultHtml = `
                <div class="validation-success">
                    <i class="fas fa-check-circle"></i>
                    <strong>Validation Successful!</strong>
                </div>
                <div style="margin-top: 1rem;">
                    <div><strong>Summary:</strong></div>
                    <ul>
                        <li>${parsed.orders.length} orders ready for import</li>
                        <li>${parsed.totalVins} VINs total</li>
                        <li>Average ${Math.round(parsed.totalVins / parsed.orders.length)} VINs per order</li>
                    </ul>
                </div>
            `;
        } else {
            if (errors.length > 0) {
                resultHtml += `
                    <div class="validation-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Validation Errors (${errors.length}):</strong>
                    </div>
                    <ul style="margin: 0.5rem 0;">
                        ${errors.map(error => `<li class="validation-error">${error}</li>`).join('')}
                    </ul>
                `;
            }
            
            if (warnings.length > 0) {
                resultHtml += `
                    <div class="validation-warning" style="margin-top: 1rem;">
                        <i class="fas fa-exclamation-circle"></i>
                        <strong>Warnings (${warnings.length}):</strong>
                    </div>
                    <ul style="margin: 0.5rem 0;">
                        ${warnings.map(warning => `<li class="validation-warning">${warning}</li>`).join('')}
                    </ul>
                `;
            }
        }
        
        contentDiv.innerHTML = resultHtml;
        resultsDiv.style.display = 'block';
        
        // Scroll to results
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    showManualValidationResults(message, type = 'info') {
        const resultsDiv = document.getElementById('manualValidationResults');
        const contentDiv = document.getElementById('manualValidationContent');
        
        if (resultsDiv && contentDiv) {
            contentDiv.innerHTML = `<div class="validation-${type}">${message}</div>`;
            resultsDiv.style.display = 'block';
        }
    }
    
    clearManualEntry() {
        const textarea = document.getElementById('manualOrderEntry');
        const resultsDiv = document.getElementById('manualValidationResults');
        
        if (textarea) {
            textarea.value = '';
            this.updateManualEntryStats();
        }
        
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    }
    
    async processManualVinEntry() {
        const textarea = document.getElementById('manualOrderEntry');
        if (!textarea || !this.currentDealership) return;
        
        const text = textarea.value.trim();
        if (!text) {
            this.addTerminalMessage('No manual entry data to process', 'error');
            return;
        }
        
        const parsed = this.parseManualEntry(text);
        
        // Convert to CSV format for existing import function
        let csvData = 'ORDER_NUMBER,VIN\n';
        parsed.orders.forEach(order => {
            // First line with order number and first VIN
            if (order.vins.length > 0) {
                csvData += `${order.orderNumber},${order.vins[0]}\n`;
                
                // Additional VINs with empty order number column
                for (let i = 1; i < order.vins.length; i++) {
                    csvData += `,${order.vins[i]}\n`;
                }
                
                // Empty line to separate order groups
                csvData += '\n';
            }
        });
        
        // Create blob and process through existing CSV import
        const blob = new Blob([csvData], { type: 'text/csv' });
        const formData = new FormData();
        formData.append('file', blob, 'manual_entry.csv');
        formData.append('dealership_name', this.currentDealership);
        formData.append('skip_duplicates', document.getElementById('skipDuplicates')?.checked ? 'true' : 'false');
        formData.append('update_existing', document.getElementById('updateExisting')?.checked ? 'true' : 'false');
        
        await this.processVinLogImport(formData);
        
        // Clear manual entry after successful import
        this.clearManualEntry();
    }

    async toggleVehicleDataType(vin, toggleElement) {
        if (!vin) return;

        // Clean the VIN for API call (remove prefixes like "NEW - ", "USED - ", etc.)
        // but keep the original for display purposes
        let cleanVin = vin;
        if (vin.includes(' - ')) {
            cleanVin = vin.split(' - ').pop();
        }

        const isNormalized = !toggleElement.checked;
        const rowElement = toggleElement.closest('tr');

        if (!rowElement) return;

        try {
            // Show loading state
            toggleElement.disabled = true;
            const originalRow = rowElement.innerHTML;

            // Fetch the appropriate data type for this VIN (use cleaned VIN for API)
            // When checked (true) = show raw view, when unchecked (false) = show normalized view
            const dataType = toggleElement.checked ? 'raw' : 'normalized';
            console.log(`Fetching ${dataType} data for VIN: ${cleanVin} (toggle checked: ${toggleElement.checked})`);

            const response = await fetch(`/api/data/vehicle-single/${encodeURIComponent(cleanVin)}?data_type=${dataType}`);
            const data = await response.json();

            console.log('API Response:', data);

            if (data.success && data.vehicle) {
                // Update the row with new data while preserving the toggle state
                // Pass both original VIN (for display) and clean VIN (for data attributes)
                this.updateModalVehicleRow(rowElement, data.vehicle, isNormalized, vin, cleanVin);
            } else {
                // If no normalized data exists, show message and revert toggle
                if (isNormalized && data.error && data.error.includes('No normalized data')) {
                    this.showModalToast('No normalized data available for this vehicle', 'warning');
                    toggleElement.checked = false;
                } else if (!isNormalized && data.error) {
                    // For raw data, show error but still try to display something
                    console.error('Raw data fetch error:', data.error);
                    this.showModalToast(`No raw data found for this VIN`, 'info');
                    toggleElement.checked = true; // Revert to normalized
                } else {
                    throw new Error(data.error || 'Failed to load vehicle data');
                }
            }

        } catch (error) {
            console.error('Error toggling vehicle data type:', error);
            this.showModalToast(`Error loading ${isNormalized ? 'normalized' : 'raw'} data: ${error.message}`, 'error');
            // Revert toggle state on error
            toggleElement.checked = !isNormalized;
        } finally {
            toggleElement.disabled = false;
        }
    }

    updateModalVehicleRow(rowElement, vehicleData, isNormalized, originalVin, cleanVin) {
        // Use original VIN for display (keeps "NEW - " prefix for graphics)
        // Use clean VIN for data attributes and API calls
        if (!originalVin) {
            originalVin = vehicleData.vin || vehicleData.VIN || '';
        }
        if (!cleanVin) {
            cleanVin = originalVin;
            if (originalVin.includes(' - ')) {
                cleanVin = originalVin.split(' - ').pop();
            }
        }

        // Format the new vehicle data for modal context
        const dataSourceBadge = `<span class="data-type-badge data-type-${isNormalized ? 'normalized' : 'raw'}">${isNormalized ? 'NORMALIZED' : 'RAW'}</span>`;

        const scrapedTime = vehicleData.import_timestamp ?
            new Date(vehicleData.import_timestamp).toLocaleDateString() : 'Unknown';

        // Get row index for button IDs
        const allRows = Array.from(rowElement.parentNode.children);
        const index = allRows.indexOf(rowElement);

        // Update the row content while preserving structure
        // Use original VIN for display (keeps "NEW - " prefix) but clean VIN for data attribute
        const displayVin = originalVin;

        // When in raw view, disable editing and show raw data for reference
        const isRawView = !isNormalized;
        const rawDataInfo = isRawView ? ` | Price: $${vehicleData.price || 'N/A'} | Mileage: ${vehicleData.mileage || 'N/A'}` : '';

        // Store original row data before modifying for data preservation
        if (!rowElement.dataset.originalRowData) {
            rowElement.dataset.originalRowData = rowElement.innerHTML;
        }

        // For raw view, create a scrollable container that spans the data columns
        if (isRawView) {
            rowElement.innerHTML = `
                <td>
                    <button class="btn-edit btn-icon-only" onclick="window.modalWizard.toggleRowEdit(${index})" id="edit-btn-${index}" title="Editing disabled in raw view" disabled style="opacity: 0.3; cursor: not-allowed;">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
                <td colspan="6" style="padding: 0; position: relative; background: rgba(255, 152, 0, 0.1);">
                    <div class="raw-data-scroll" style="overflow-x: auto; overflow-y: hidden; width: 100%; max-width: 600px; padding: 8px; scrollbar-width: thin; -webkit-overflow-scrolling: touch; height: 45px; border: 1px solid rgba(255, 152, 0, 0.3);">
                        <div style="display: flex; align-items: center; min-width: 1200px; gap: 20px; white-space: nowrap; font-size: 0.9em;">
                            <span><strong>Year:</strong> ${vehicleData.year || 'N/A'}</span>
                            <span><strong>Make:</strong> ${vehicleData.make || 'N/A'}</span>
                            <span><strong>Model:</strong> ${vehicleData.model || 'N/A'}</span>
                            <span><strong>Trim:</strong> ${vehicleData.trim || 'N/A'}</span>
                            <span><strong>Stock:</strong> ${vehicleData.stock || vehicleData.stock_number || 'N/A'}</span>
                            <span><strong>VIN:</strong> ${cleanVin}</span>
                            <span style="color: var(--accent-primary); font-weight: 600;"><strong>Price:</strong> $${vehicleData.price || 'N/A'}</span>
                            <span><strong>Mileage:</strong> ${vehicleData.mileage || 'N/A'}</span>
                            <span><strong>Type:</strong> ${vehicleData.vehicle_type || 'N/A'}</span>
                            <span><strong>Exterior:</strong> ${vehicleData.exterior_color || 'N/A'}</span>
                            <span><strong>Interior:</strong> ${vehicleData.interior_color || 'N/A'}</span>
                            <span><strong>Engine:</strong> ${vehicleData.engine || 'N/A'}</span>
                            <span><strong>Transmission:</strong> ${vehicleData.transmission || 'N/A'}</span>
                            <span><strong>Fuel:</strong> ${vehicleData.fuel_type || 'N/A'}</span>
                        </div>
                    </div>
                </td>
                <td class="toggle-cell" onclick="event.stopPropagation();">
                    <label class="data-toggle-switch">
                        <input type="checkbox" class="toggle-input" data-vin="${originalVin}" checked onchange="window.modalWizard.toggleVehicleDataType('${originalVin}', this)">
                        <span class="toggle-slider">
                            <span class="toggle-label-raw">R</span>
                            <span class="toggle-label-norm">N</span>
                        </span>
                    </label>
                </td>
                <td>
                    <button class="btn-save btn-icon-only" onclick="window.modalWizard.saveRowEdit(${index})" id="save-btn-${index}" title="Save changes" style="display: none;">
                        <i class="fas fa-save"></i>
                    </button>
                    <button class="btn-delete-row btn-icon-only" onclick="window.modalWizard.deleteVehicleRow(${index})" id="delete-btn-${index}" title="Deletion disabled in raw view" disabled style="opacity: 0.3; cursor: not-allowed;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
        } else {
            // Normal view - restore original data if available, otherwise reconstruct
            if (rowElement.dataset.originalRowData) {
                // Restore the original row data
                rowElement.innerHTML = rowElement.dataset.originalRowData;
                // Update the toggle state to unchecked
                const toggleInput = rowElement.querySelector('.toggle-input');
                if (toggleInput) {
                    toggleInput.checked = false;
                }
                // Clear the stored data
                delete rowElement.dataset.originalRowData;
                return;
            }

            // Fallback: reconstruct the normalized view
            rowElement.innerHTML = `
                <td>
                    <button class="btn-edit btn-icon-only" onclick="window.modalWizard.toggleRowEdit(${index})" id="edit-btn-${index}" title="Edit row">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
                <td class="editable-cell" data-field="year-make" data-index="${index}">
                    <span class="display-value">${vehicleData.YEARMAKE || ''}</span>
                    <input type="text" class="edit-input" value="${vehicleData.YEARMAKE || ''}" style="display: none;">
                </td>
                <td class="editable-cell" data-field="model" data-index="${index}">
                    <span class="display-value">${vehicleData.MODEL || ''}</span>
                    <input type="text" class="edit-input" value="${vehicleData.MODEL || ''}" style="display: none;">
                </td>
                <td class="editable-cell" data-field="trim" data-index="${index}">
                    <span class="display-value">${vehicleData.TRIM || ''}</span>
                    <input type="text" class="edit-input" value="${vehicleData.TRIM || ''}" style="display: none;">
                </td>
                <td class="editable-cell" data-field="stock" data-index="${index}">
                    <span class="display-value stock-badge">${vehicleData.STOCK || ''}</span>
                    <input type="text" class="edit-input" value="${vehicleData.STOCK || ''}" style="display: none;">
                </td>
                <td class="editable-cell" data-field="vin" data-index="${index}">
                    <span class="display-value vin-display" title="${displayVin}">${displayVin}</span>
                    <input type="text" class="edit-input" value="${displayVin}" style="display: none;" maxlength="17">
                </td>
                <td class="raw-status-cell" data-field="raw_status" data-index="${index}">
                    <span class="display-value">${vehicleData.raw_status || 'N/A'}</span>
                </td>
                <td class="toggle-cell" onclick="event.stopPropagation();">
                    <label class="data-toggle-switch">
                        <input type="checkbox" class="toggle-input" data-vin="${originalVin}" onchange="window.modalWizard.toggleVehicleDataType('${originalVin}', this)">
                        <span class="toggle-slider">
                            <span class="toggle-label-raw">R</span>
                            <span class="toggle-label-norm">N</span>
                        </span>
                    </label>
                </td>
                <td>
                    <button class="btn-save btn-icon-only" onclick="window.modalWizard.saveRowEdit(${index})" id="save-btn-${index}" title="Save changes" style="display: none;">
                        <i class="fas fa-save"></i>
                    </button>
                    <button class="btn-delete-row btn-icon-only" onclick="window.modalWizard.deleteVehicleRow(${index})" id="delete-btn-${index}" title="Delete row">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
        }
    }

    showModalToast(message, type = 'info') {
        // Simple toast notification for modal context
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            background: ${type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#28a745'};
        `;

        document.body.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

}

// EMERGENCY INLINE FUNCTIONS - DIRECT IMPLEMENTATION
function updateManualEntryStatsInline() {
    console.log('=== EMERGENCY INLINE UPDATE STATS ===');
    const textarea = document.getElementById('manualOrderEntry');
    const orderCountEl = document.getElementById('manualOrderCount');
    const vinCountEl = document.getElementById('manualVinCount');
    
    if (!textarea || !orderCountEl || !vinCountEl) {
        console.error('Missing elements');
        return;
    }
    
    const text = textarea.value.trim();
    if (!text) {
        orderCountEl.textContent = '0';
        vinCountEl.textContent = '0';
        return;
    }
    
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);
    let orders = 0;
    let vins = 0;
    
    for (let line of lines) {
        if (line.length === 17 && /^[A-HJ-NPR-Z0-9]+$/i.test(line)) {
            vins++;
        } else if (line.length > 0 && line.length < 17) {
            orders++;
        }
    }
    
    orderCountEl.textContent = orders.toString();
    vinCountEl.textContent = vins.toString();
    console.log('EMERGENCY: Updated stats:', { orders, vins });
}

function validateManualEntryInline() {
    console.log('=== EMERGENCY VALIDATE CLICKED ===');
    const textarea = document.getElementById('manualOrderEntry');
    if (!textarea) return;
    
    const text = textarea.value.trim();
    if (!text) {
        alert('Please enter VIN data');
        return;
    }
    
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);
    let orders = 0;
    let vins = 0;
    
    for (let line of lines) {
        if (line.length === 17 && /^[A-HJ-NPR-Z0-9]+$/i.test(line)) {
            vins++;
        } else if (line.length > 0 && line.length < 17) {
            orders++;
        }
    }
    
    alert(`Validation Results:\n• Orders: ${orders}\n• VINs: ${vins}\n\n✅ Format looks good!`);
}

function clearManualEntryInline() {
    console.log('=== EMERGENCY CLEAR CLICKED ===');
    const textarea = document.getElementById('manualOrderEntry');
    if (textarea) {
        textarea.value = '';
        updateManualEntryStatsInline();
    }
}

function switchToManualModeInline() {
    console.log('=== EMERGENCY SWITCH TO MANUAL ===');
    const csvTab = document.getElementById('csvImportTab');
    const manualTab = document.getElementById('manualEntryTab');
    const csvSection = document.getElementById('csvImportSection');
    const manualSection = document.getElementById('manualEntrySection');
    
    if (csvTab) csvTab.classList.remove('active');
    if (manualTab) manualTab.classList.add('active');
    if (csvSection) csvSection.style.display = 'none';
    if (manualSection) manualSection.style.display = 'block';
    
    updateManualEntryStatsInline();
}

function switchToCSVModeInline() {
    console.log('=== EMERGENCY SWITCH TO CSV ===');
    const csvTab = document.getElementById('csvImportTab');
    const manualTab = document.getElementById('manualEntryTab');
    const csvSection = document.getElementById('csvImportSection');
    const manualSection = document.getElementById('manualEntrySection');
    
    if (csvTab) csvTab.classList.add('active');
    if (manualTab) manualTab.classList.remove('active');
    if (csvSection) csvSection.style.display = 'block';
    if (manualSection) manualSection.style.display = 'none';
}

// Initialize the application when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new MinisFornumApp();
    // Global function for inline event handlers - must be set after app is created
    window.app = app;
});

// ===== EMERGENCY MANUAL VIN ENTRY FUNCTIONS - DIRECT INJECTION =====
// These functions MUST work regardless of caching issues

function updateManualEntryStatsInline() {
    console.log('=== EMERGENCY INLINE UPDATE STATS - DIRECT ===');
    const textarea = document.getElementById('manualOrderEntry');
    const orderCountEl = document.getElementById('manualOrderCount');
    const vinCountEl = document.getElementById('manualVinCount');
    
    if (!textarea || !orderCountEl || !vinCountEl) {
        console.error('EMERGENCY: Required elements not found');
        return;
    }
    
    const lines = textarea.value.split('\n').filter(line => line.trim());
    let orders = 0;
    let vins = 0;
    
    for (let line of lines) {
        const trimmed = line.trim().toUpperCase();
        // More flexible order detection
        if (trimmed.match(/^ORDER[\s\d]/i) || trimmed.match(/^\d+$/) || trimmed.match(/^#\d+/)) {
            orders++;
            console.log(`FOUND ORDER: "${line}"`);
        } else if (trimmed.match(/^[A-Z0-9]{17}$/)) {
            vins++;
        }
    }
    
    orderCountEl.textContent = orders;
    vinCountEl.textContent = vins;
    console.log(`EMERGENCY: Updated counts - Orders: ${orders}, VINs: ${vins}`);
}

function validateManualEntryInline() {
    console.log('=== EMERGENCY VALIDATE CLICKED - DIRECT ===');
    const textarea = document.getElementById('manualOrderEntry');
    
    if (!textarea) {
        alert('ERROR: Manual order entry textarea not found');
        return;
    }
    
    const lines = textarea.value.split('\n').filter(line => line.trim());
    const vinPattern = /^[A-Z0-9]{17}$/;
    const orderPattern = /^\s*ORDER\s*\d+/i;
    
    let validVins = 0;
    let invalidVins = 0;
    let orders = 0;
    let results = ['VALIDATION RESULTS:', ''];
    
    for (let line of lines) {
        const trimmed = line.trim().toUpperCase();
        if (orderPattern.test(line)) {
            orders++;
            results.push(`✓ ORDER: ${line}`);
        } else if (vinPattern.test(trimmed)) {
            validVins++;
            results.push(`✓ VALID VIN: ${trimmed}`);
        } else if (trimmed.length > 0) {
            invalidVins++;
            results.push(`✗ INVALID: ${trimmed}`);
        }
    }
    
    results.push('', `SUMMARY: ${orders} orders, ${validVins} valid VINs, ${invalidVins} invalid entries`);
    alert(results.join('\n'));
    
    console.log('EMERGENCY: Validation complete');
}

function clearManualEntryInline() {
    console.log('=== EMERGENCY CLEAR CLICKED - CONSOLE SAFE ===');
    try {
        const textarea = document.getElementById('manualOrderEntry');
        const orderCountEl = document.getElementById('manualOrderCount');
        const vinCountEl = document.getElementById('manualVinCount');
        
        if (!textarea) {
            console.error('ERROR: Manual order entry textarea not found');
            return false;
        }
        
        textarea.value = '';
        if (orderCountEl) orderCountEl.textContent = '0';
        if (vinCountEl) vinCountEl.textContent = '0';
        console.log('SUCCESS: Manual entries cleared');
        return true;
    } catch (error) {
        console.error('CLEAR ERROR:', error);
        return false;
    }
}

// ===== BRIDGE THE CLASS METHODS TO THE WORKING INLINE FUNCTIONS =====
// The existing code calls this.updateManualEntryStats() but we need to bridge to working functions

// Add missing class methods to MinisFornumApp prototype
if (typeof MinisFornumApp !== 'undefined') {
    // Bridge updateManualEntryStats to working inline function
    MinisFornumApp.prototype.updateManualEntryStats = function() {
        console.log('BRIDGE: Class method calling inline function');
        if (typeof updateManualEntryStatsInline === 'function') {
            updateManualEntryStatsInline();
        } else {
            console.error('BRIDGE ERROR: updateManualEntryStatsInline not found');
        }
    };
    
    // Bridge validateManualEntry to working inline function
    MinisFornumApp.prototype.validateManualEntry = function() {
        console.log('BRIDGE: Class method calling inline validate function');
        if (typeof validateManualEntryInline === 'function') {
            validateManualEntryInline();
        } else {
            console.error('BRIDGE ERROR: validateManualEntryInline not found');
        }
    };
    
    // Bridge clearManualEntry to working inline function
    MinisFornumApp.prototype.clearManualEntry = function() {
        console.log('BRIDGE: Class method calling inline clear function');
        if (typeof clearManualEntryInline === 'function') {
            clearManualEntryInline();
        } else {
            console.error('BRIDGE ERROR: clearManualEntryInline not found');
        }
    };
    
    console.log('✅ BRIDGE: Class methods linked to working inline functions');
}

// ===== EMERGENCY BUTTON FIXER =====
// Force the Import Manual VINs button to appear and work
function forceShowImportManualButton() {
    console.log('FORCE: Showing Import Manual VINs button');
    const importManualBtn = document.getElementById('importManualVins');
    const startImportBtn = document.getElementById('startVinLogImport');
    
    if (importManualBtn) {
        importManualBtn.style.display = 'inline-block';
        importManualBtn.style.visibility = 'visible';
        importManualBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
        importManualBtn.style.color = 'white';
        importManualBtn.style.border = 'none';
        importManualBtn.style.padding = '10px 20px';
        importManualBtn.style.borderRadius = '6px';
        importManualBtn.style.cursor = 'pointer';
        console.log('✅ FORCE: Import Manual VINs button is now visible');
        
        // Hide the CSV import button when manual is active
        if (startImportBtn) {
            startImportBtn.style.display = 'none';
        }
    } else {
        console.log('❌ FORCE: Import Manual VINs button not found in DOM');
    }
}

// Force the CSV import button to show and hide manual when in CSV mode
function forceShowCsvImportButton() {
    console.log('FORCE: Showing CSV Import button');
    const importManualBtn = document.getElementById('importManualVins');
    const startImportBtn = document.getElementById('startVinLogImport');
    
    if (startImportBtn) {
        startImportBtn.style.display = 'inline-block';
        startImportBtn.style.visibility = 'visible';
        console.log('✅ FORCE: CSV Import button is now visible');
        
        // Hide the manual import button when CSV is active
        if (importManualBtn) {
            importManualBtn.style.display = 'none';
        }
    }
}

// Try to fix buttons on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM READY: Setting up emergency button management');
    
    // Setup permanent tab switching
    setTimeout(setupPermanentTabSwitching, 500);
    
    // Check for manual entry tab clicks (legacy support)
    const manualTab = document.getElementById('manualEntryTab');
    const csvTab = document.getElementById('csvImportTab');
    
    if (manualTab) {
        manualTab.addEventListener('click', function() {
            console.log('MANUAL TAB CLICKED: Forcing manual button visibility');
            setTimeout(forceShowImportManualButton, 100);
        });
    }
    
    if (csvTab) {
        csvTab.addEventListener('click', function() {
            console.log('CSV TAB CLICKED: Forcing CSV button visibility');
            setTimeout(forceShowCsvImportButton, 100);
        });
    }
});

// EMERGENCY CONSOLE COMMANDS - SAFE TO CALL
window.emergencyClear = function() {
    return clearManualEntryInline();
};

window.emergencyValidate = function() {
    return validateManualEntryInline();
};

window.forceManualButton = function() {
    return forceShowImportManualButton();
};

// HANDLE MANUAL VIN IMPORT
window.handleManualVinImport = function() {
    console.log('=== MANUAL VIN IMPORT CLICKED ===');
    const textarea = document.getElementById('manualOrderEntry');
    if (!textarea || !textarea.value.trim()) {
        alert('Please enter VIN data before importing.');
        return;
    }
    
    // Process the manual VIN data here
    console.log('Processing manual VIN data:', textarea.value);
    alert('Manual VIN import functionality - ready to implement!');
};

// PERMANENT TAB SWITCHING FIX
function setupPermanentTabSwitching() {
    const csvTab = document.getElementById('csvImportTab');
    const manualTab = document.getElementById('manualEntryTab');
    const csvSection = document.getElementById('csvImportSection');
    const manualSection = document.getElementById('manualEntrySection');
    const csvImportBtn = document.getElementById('startVinLogImport');
    const manualImportBtn = document.getElementById('importManualVins');
    
    if (csvTab && manualTab && csvSection && manualSection) {
        // CSV Tab Click
        csvTab.addEventListener('click', function() {
            console.log('=== CSV TAB CLICKED - PERMANENT ===');
            csvTab.classList.add('active');
            manualTab.classList.remove('active');
            csvSection.style.display = 'block';
            manualSection.style.display = 'none';
            
            if (csvImportBtn) csvImportBtn.style.display = 'inline-block';
            if (manualImportBtn) manualImportBtn.style.display = 'none';
        });
        
        // Manual Tab Click  
        manualTab.addEventListener('click', function() {
            console.log('=== MANUAL TAB CLICKED - PERMANENT ===');
            manualTab.classList.add('active');
            csvTab.classList.remove('active');
            manualSection.style.display = 'block';
            csvSection.style.display = 'none';
            
            if (csvImportBtn) csvImportBtn.style.display = 'none';
            if (manualImportBtn) manualImportBtn.style.display = 'inline-block';
        });
        
        console.log('✅ PERMANENT tab switching setup complete');
    } else {
        console.error('❌ Tab switching elements not found');
    }
}

// EMERGENCY BUTTON CREATION - CONSOLE SAFE
window.createManualButton = function() {
    console.log('=== EMERGENCY: Creating Import Manual VINs button ===');
    try {
        // Check if button already exists
        let manualBtn = document.getElementById('importManualVins');
        if (manualBtn) {
            console.log('Button already exists, making it visible');
            manualBtn.style.display = 'inline-block';
            return true;
        }
        
        // Create the button
        manualBtn = document.createElement('button');
        manualBtn.id = 'importManualVins';
        manualBtn.className = 'btn btn-success';
        manualBtn.innerHTML = '<i class="fas fa-keyboard"></i> Import Manual VINs';
        
        // Find modal footer and insert before the main import button
        const modalFooter = document.querySelector('#vinLogUpdateModal .modal-footer');
        const importBtn = document.getElementById('startVinLogImport');
        
        if (modalFooter && importBtn) {
            modalFooter.insertBefore(manualBtn, importBtn);
            console.log('SUCCESS: Manual button created and inserted');
            return true;
        } else {
            console.error('Could not find modal footer or import button');
            return false;
        }
    } catch (error) {
        console.error('ERROR creating manual button:', error);
        return false;
    }
};

// CACHE BREAK TIMESTAMP: 2025-08-27-15:55:00
console.log('=== EMERGENCY FUNCTIONS LOADED DIRECTLY INTO APP.JS - TIMESTAMP: 2025-08-27-15:55:00 ===');
console.log('Available:', typeof updateManualEntryStatsInline, typeof validateManualEntryInline, typeof clearManualEntryInline);

// FORCE GLOBAL FUNCTIONS - ENSURE THEY EXIST
window.validateManualEntryInline = validateManualEntryInline;
window.clearManualEntryInline = clearManualEntryInline;
window.updateManualEntryStatsInline = updateManualEntryStatsInline;

console.log('GLOBAL FUNCTIONS EXPORTED:', {
    validateManualEntryInline: typeof window.validateManualEntryInline,
    clearManualEntryInline: typeof window.clearManualEntryInline,
    updateManualEntryStatsInline: typeof window.updateManualEntryStatsInline
});
// CACHE BREAK FORCED: Wed, Aug 27, 2025  4:30:04 PM
console.log('=== CACHE BREAK SUCCESS - Wed, Aug 27, 2025  4:30:04 PM ===');

// FINAL FIX: Add missing functions directly to loaded version
console.log('=== ADDING FINAL FIXES TO LOADED VERSION ===');

// Emergency functions that work in console
window.emergencyClear = function() {
    console.log('=== EMERGENCY CLEAR CLICKED - CONSOLE SAFE ===');
    try {
        const textarea = document.getElementById('manualOrderEntry');
        const orderCountEl = document.getElementById('manualOrderCount');
        const vinCountEl = document.getElementById('manualVinCount');
        
        if (!textarea) {
            console.error('ERROR: Manual order entry textarea not found');
            return false;
        }
        
        textarea.value = '';
        if (orderCountEl) orderCountEl.textContent = '0';
        if (vinCountEl) vinCountEl.textContent = '0';
        console.log('SUCCESS: Manual entries cleared');
        return true;
    } catch (error) {
        console.error('CLEAR ERROR:', error);
        return false;
    }
};

window.emergencyValidate = function() {
    console.log('=== EMERGENCY VALIDATE CLICKED - DIRECT ===');
    const textarea = document.getElementById('manualOrderEntry');
    if (!textarea) {
        alert('ERROR: Manual order entry textarea not found');
        return;
    }
    
    const lines = textarea.value.split('\n').filter(line => line.trim());
    let orders = 0;
    let validVins = 0;
    
    for (let line of lines) {
        const trimmed = line.trim().toUpperCase();
        if (trimmed.match(/^ORDER[\s\d]/i) || trimmed.match(/^\d+$/) || trimmed.match(/^#\d+/)) {
            orders++;
        } else if (trimmed.match(/^[A-Z0-9]{17}$/)) {
            validVins++;
        }
    }
    
    alert(`Validation Results:\nOrders: ${orders}\nValid VINs: ${validVins}\nTotal entries: ${orders + validVins}`);
    console.log('EMERGENCY: Validation complete');
};

// Create Import Manual VINs button function
window.createManualButton = function() {
    console.log('=== EMERGENCY: Creating Import Manual VINs button ===');
    try {
        let manualBtn = document.getElementById('importManualVins');
        if (manualBtn) {
            console.log('Button already exists, FORCING IT VISIBLE');
            manualBtn.style.display = 'inline-block !important';
            manualBtn.style.visibility = 'visible !important';
            manualBtn.style.opacity = '1 !important';
            manualBtn.style.position = 'static !important';
            return true;
        }
        
        manualBtn = document.createElement('button');
        manualBtn.id = 'importManualVins';
        manualBtn.className = 'btn btn-success';
        manualBtn.style.display = 'inline-block !important';
        manualBtn.style.visibility = 'visible !important';
        manualBtn.style.opacity = '1 !important';
        manualBtn.style.marginLeft = '10px';
        manualBtn.innerHTML = '<i class="fas fa-keyboard"></i> Import Manual VINs';
        manualBtn.onclick = function() {
            console.log('=== MANUAL VIN IMPORT CLICKED ===');
            const textarea = document.getElementById('manualOrderEntry');
            if (!textarea || !textarea.value.trim()) {
                alert('Please enter VIN data before importing.');
                return;
            }
            alert('Manual VIN import functionality - ready to implement!');
        };
        
        const modalFooter = document.querySelector('#vinLogUpdateModal .modal-footer');
        const importBtn = document.getElementById('startVinLogImport');
        
        if (modalFooter && importBtn) {
            modalFooter.insertBefore(manualBtn, importBtn);
            console.log('SUCCESS: Manual button created and FORCED VISIBLE');
            return true;
        } else {
            console.error('Could not find modal footer or import button');
            return false;
        }
    } catch (error) {
        console.error('ERROR creating manual button:', error);
        return false;
    }
};

// Setup permanent tab switching
function setupPermanentTabSwitching() {
    const csvTab = document.getElementById('csvImportTab');
    const manualTab = document.getElementById('manualEntryTab');
    const csvSection = document.getElementById('csvImportSection');
    const manualSection = document.getElementById('manualEntrySection');
    const csvImportBtn = document.getElementById('startVinLogImport');
    
    if (csvTab && manualTab && csvSection && manualSection) {
        // CSV Tab Click
        csvTab.addEventListener('click', function() {
            console.log('=== CSV TAB CLICKED - PERMANENT ===');
            csvTab.classList.add('active');
            manualTab.classList.remove('active');
            csvSection.style.display = 'block';
            manualSection.style.display = 'none';
            
            if (csvImportBtn) csvImportBtn.style.display = 'inline-block';
            const manualImportBtn = document.getElementById('importManualVins');
            if (manualImportBtn) manualImportBtn.style.display = 'none';
        });
        
        // Manual Tab Click  
        manualTab.addEventListener('click', function() {
            console.log('=== MANUAL TAB CLICKED - PERMANENT ===');
            manualTab.classList.add('active');
            csvTab.classList.remove('active');
            manualSection.style.display = 'block';
            csvSection.style.display = 'none';
            
            if (csvImportBtn) csvImportBtn.style.display = 'none';
            
            // Create manual button if it doesn't exist
            setTimeout(function() {
                let manualImportBtn = document.getElementById('importManualVins');
                if (!manualImportBtn) {
                    createManualButton();
                } else {
                    manualImportBtn.style.display = 'inline-block';
                }
            }, 100);
        });
        
        console.log('✅ PERMANENT tab switching setup complete');
    } else {
        console.error('❌ Tab switching elements not found');
    }
}

// Auto-run setup when DOM is ready
setTimeout(function() {
    console.log('=== SETTING UP PERMANENT TAB SWITCHING ===');
    setupPermanentTabSwitching();
    
    // Wire buttons directly
    const validateBtn = document.getElementById('validateManualEntry');
    if (validateBtn) {
        validateBtn.onclick = emergencyValidate;
        console.log('✅ Validate button wired');
    }
    
    const clearBtn = document.getElementById('clearManualEntry');
    if (clearBtn) {
        clearBtn.onclick = emergencyClear;
        console.log('✅ Clear button wired');
    }
    
    // FORCE CREATE IMPORT MANUAL VINS BUTTON PERMANENTLY
    setTimeout(function() {
        console.log('=== FORCING PERMANENT IMPORT MANUAL VINS BUTTON ===');
        createManualButton();
    }, 500);
}, 2000);

// Handle Manual VIN Import button click
window.handleManualVinImport = function() {
    console.log('=== MANUAL VIN IMPORT CLICKED ===');
    const textarea = document.getElementById('manualOrderEntry');
    if (!textarea || !textarea.value.trim()) {
        alert('Please enter VIN data before importing.');
        return;
    }
    
    // Process the manual VIN data here
    console.log('Processing manual VIN data:', textarea.value);
    alert('Manual VIN import functionality - ready to implement!');
};

// PROPER MODAL BUTTON POSITIONING: Force button visible in correct modal footer location
window.forceManualButtonVisible = function() {
    console.log('=== FIXING IMPORT MANUAL VINS BUTTON IN MODAL FOOTER ===');
    
    // First, find the existing button in the HTML template
    const existingBtn = document.getElementById('importManualVins');
    if (existingBtn) {
        console.log('Found existing button in DOM, forcing visibility...');
        
        // FORCE VISIBILITY WITH NUCLEAR CSS
        existingBtn.style.cssText = `
            display: inline-block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 1000 !important;
            background: #28a745 !important;
            color: white !important;
            padding: 8px 16px !important;
            border: none !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            font-size: 14px !important;
            margin-left: 8px !important;
        `;
        
        // Ensure the modal footer is visible too
        const modalFooter = existingBtn.closest('.modal-footer');
        if (modalFooter) {
            modalFooter.style.cssText = `
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                align-items: center !important;
                gap: 8px !important;
            `;
            console.log('Modal footer visibility also forced');
        }
        
        console.log('SUCCESS: Existing button forced visible in modal footer');
        return true;
    }
    
    // Fallback: Create button in modal footer if not found
    console.log('Button not found in DOM, creating in modal footer...');
    const modalFooter = document.querySelector('#vinLogUpdateModal .modal-footer');
    if (!modalFooter) {
        console.error('VIN Log Update Modal footer not found!');
        return false;
    }
    
    // Create button and place it in the modal footer
    const btn = document.createElement('button');
    btn.id = 'importManualVins';
    btn.innerHTML = '<i class="fas fa-keyboard"></i> Import Manual VINs';
    btn.className = 'btn btn-success';
    btn.onclick = function() {
        console.log('=== MANUAL VIN IMPORT CLICKED ===');
        const textarea = document.getElementById('manualOrderEntry');
        if (!textarea || !textarea.value.trim()) {
            alert('Please enter VIN data before importing.');
            return;
        }
        alert('Manual VIN import functionality - ready to implement!');
    };
    
    // FORCE BUTTON STYLING FOR MODAL FOOTER
    btn.style.cssText = `
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: relative !important;
        z-index: 1000 !important;
        background: #28a745 !important;
        color: white !important;
        padding: 8px 16px !important;
        border: none !important;
        border-radius: 4px !important;
        cursor: pointer !important;
        font-size: 14px !important;
        margin-left: 8px !important;
    `;
    
    // Add to modal footer
    modalFooter.appendChild(btn);
    
    console.log('SUCCESS: Button created and added to modal footer');
    return true;
};

console.log('✅ FINAL FIXES LOADED - All functions should work now!');

// ============================================================================
// EMERGENCY TEMPLATE CACHE BYPASS (August 28, 2025) 
// ============================================================================

console.log('🚨 LOADING EMERGENCY TEMPLATE CACHE BYPASS SOLUTIONS...');

// DEBUG: Investigate available elements on ORDER # stage  
window.debugOrderStage = function() {
    console.log('🔍 DEBUGGING ORDER STAGE ELEMENTS...');
    
    // Log all visible elements
    const allVisible = document.querySelectorAll('*:not([style*="display: none"]):not([hidden])');
    console.log('All visible elements count:', allVisible.length);
    
    // Look for wizard steps
    const wizardSteps = document.querySelectorAll('[data-step], .wizard-step, .step');
    console.log('Wizard steps found:', wizardSteps.length);
    wizardSteps.forEach((step, i) => {
        console.log(`Step ${i}:`, {
            element: step,
            visible: step.style.display !== 'none' && !step.hidden,
            text: step.textContent.substring(0, 100),
            classes: step.className,
            dataStep: step.getAttribute('data-step')
        });
    });
    
    // Look for order-related content
    const orderElements = Array.from(allVisible).filter(el => {
        const text = el.textContent.toLowerCase();
        return text.includes('order') && text.includes('number');
    });
    console.log('Order-related elements:', orderElements.length);
    orderElements.forEach((el, i) => {
        console.log(`Order element ${i}:`, {
            element: el,
            text: el.textContent.substring(0, 100),
            tag: el.tagName,
            id: el.id,
            classes: el.className
        });
    });
    
    // Check for modal content
    const modalContent = document.querySelector('.modal-content, .wizard-content, .order-processing-modal');
    if (modalContent) {
        console.log('Modal content found:', modalContent);
        console.log('Modal content innerHTML preview:', modalContent.innerHTML.substring(0, 500));
    }
    
    return {wizardSteps, orderElements, modalContent};
};

// CRITICAL: Force Order Number Input Box to appear via DOM injection
function forceOrderNumberInput() {
    console.log('🔧 Checking for missing order number input...');
    
    // TARGETED FIX: Look for the specific step we found in debug
    const orderStep = document.querySelector('#modalOrderNumberStep');
    if (orderStep) {
        console.log('📍 Found order number step, checking for input...');
        
        // Check if input already exists
        const existingInput = document.getElementById('orderNumberInput') || document.getElementById('modalOrderNumber');
        if (!existingInput) {
            console.log('🚨 MISSING ORDER INPUT - INJECTING VIA DOM...');
            
            // Find the step content area - try multiple selectors
            const stepDescription = orderStep.querySelector('.step-description') ||
                                   orderStep.querySelector('.step-content') ||
                                   orderStep.querySelector('.wizard-content') ||
                                   orderStep;
            if (stepDescription) {
                // Create the missing form elements
                const inputHTML = `
                    <div class="order-number-input" style="margin: 20px 0;">
                        <div class="form-group">
                            <label for="orderNumberInput">Order Number:</label>
                            <input type="text" id="orderNumberInput" class="form-control" 
                                   placeholder="e.g., SF24001, Order123, etc." 
                                   maxlength="20" required>
                        </div>
                        <div class="form-group">
                            <button type="button" id="applyOrderNumberBtn" class="btn btn-primary" 
                                    onclick="wizard.applyOrderNumber()">
                                Apply Order Number
                            </button>
                        </div>
                        <div id="orderNumberPreview" class="order-preview" style="display: none;">
                            <h4>Order Preview</h4>
                            <div class="preview-content">
                                <div id="vinPreviewList"></div>
                            </div>
                        </div>
                        <div style="display: none;">
                            <div id="orderNumberDealershipDisplay"></div>
                            <div id="orderDealershipName"></div>
                            <div id="orderVinCount"></div>
                        </div>
                    </div>
                `;
                
                // Inject the HTML
                stepDescription.insertAdjacentHTML('afterend', inputHTML);
                console.log('✅ ORDER INPUT INJECTED SUCCESSFULLY via DOM!');
            }
        } else {
            console.log('✅ Order input already exists - no injection needed');
        }
    } else {
        console.log('❌ Could not find order step, trying fallback approach...');
        
        // Fallback: Look for any visible step with order-related content
        const allSteps = document.querySelectorAll('[data-step], .wizard-step, .step');
        for (const step of allSteps) {
            if (step.style.display !== 'none' && !step.hidden) {
                const stepText = step.textContent.toLowerCase();
                if (stepText.includes('order') || stepText.includes('number')) {
                    console.log('📍 Found potential order step via fallback, injecting input...');
                    
                    const existingInput = document.getElementById('orderNumberInput') || document.getElementById('modalOrderNumber');
                    if (!existingInput) {
                        const inputHTML = `
                            <div class="order-number-input" style="margin: 20px 0; padding: 20px; border: 2px solid #007bff; background: #f8f9fa;">
                                <h3>Order Number Input</h3>
                                <div class="form-group">
                                    <label for="orderNumberInput">Order Number:</label>
                                    <input type="text" id="orderNumberInput" class="form-control" 
                                           placeholder="e.g., SF24001, Order123, etc." 
                                           maxlength="20" required>
                                </div>
                                <button type="button" id="applyOrderNumberBtn" class="btn btn-primary" 
                                        onclick="window.modalWizard.generateFinalOutput()">
                                    Apply Order Number & Complete
                                </button>
                            </div>
                        `;
                        step.insertAdjacentHTML('beforeend', inputHTML);
                        console.log('✅ FALLBACK ORDER INPUT INJECTED!');
                        break;
                    }
                }
            }
        }
    }
}

// CRITICAL: Force fresh CSV data in review stage
function forceFreshReviewData() {
    console.log('🔧 Checking for stale review data...');
    
    // Find vehicle count element
    const vehicleCount = document.getElementById('vehicleCount');
    if (vehicleCount && vehicleCount.textContent === '27') {
        console.log('🚨 DETECTED STALE 27 VIN COUNT - FORCING REFRESH...');
        
        // Force the wizard to reload CSV with cache busting
        if (typeof wizard !== 'undefined' && wizard.currentOrderResult) {
            console.log('🔄 Forcing fresh CSV reload...');
            wizard.loadCSVIntoSpreadsheet(wizard.currentOrderResult);
        }
    }
}

// Monitor for wizard step changes and apply fixes
let lastStepCheck = '';
function monitorWizardSteps() {
    const currentStep = document.querySelector('.wizard-step.active')?.getAttribute('data-step') || '';
    
    if (currentStep !== lastStepCheck) {
        lastStepCheck = currentStep;
        console.log(`🎯 Wizard step changed to: ${currentStep}`);
        
        // Apply fixes based on current step
        if (currentStep === 'order-number' || currentStep === 'order') {
            setTimeout(forceOrderNumberInput, 500);
        } else if (currentStep === 'review') {
            setTimeout(forceFreshReviewData, 500);
        }
    }
}

// Start monitoring immediately and set interval
setTimeout(() => {
    console.log('🎯 Starting wizard step monitoring...');
    monitorWizardSteps();
    setInterval(monitorWizardSteps, 1000);
}, 2000);

console.log('✅ EMERGENCY TEMPLATE CACHE BYPASS LOADED - DOM injection ready!');

// FORCE INJECT MAINTENANCE OPTION INTO PROCESSING QUEUE PANELS
console.log('🔧 FORCING MAINTENANCE OPTION INTO PROCESSING QUEUE...');

const injectMaintenanceIntoQueue = () => {
    console.log('🔍 MAINTENANCE INJECTION: Starting scan...');
    
    // Debug: Check what exists in the DOM
    const processingQueue = document.getElementById('processingQueue');
    console.log('Processing Queue element exists:', !!processingQueue);
    
    const dealerPanels = document.querySelectorAll('.dealer-panel');
    console.log(`Found ${dealerPanels.length} total dealer panels in DOM`);
    
    // Look for order-type-toggle in multiple ways
    const toggles1 = document.querySelectorAll('.order-type-toggle');
    console.log(`Found ${toggles1.length} elements with class 'order-type-toggle'`);
    
    const toggles2 = document.querySelectorAll('.dealer-panel .order-type-toggle');
    console.log(`Found ${toggles2.length} elements matching '.dealer-panel .order-type-toggle'`);
    
    const toggles3 = document.querySelectorAll('#processingQueue .order-type-toggle');
    console.log(`Found ${toggles3.length} elements matching '#processingQueue .order-type-toggle'`);
    
    // Try to find radio buttons directly
    const radioGroups = document.querySelectorAll('.dealer-panel input[type="radio"][name*="order_type"]');
    console.log(`Found ${radioGroups.length} order type radio buttons`);
    
    // Log the actual HTML structure of first dealer panel if it exists
    if (dealerPanels.length > 0) {
        console.log('First dealer panel HTML structure:', dealerPanels[0].innerHTML.substring(0, 500));
    }
    
    // Target the processing queue panels specifically
    const queuePanels = document.querySelectorAll('#processingQueue .dealer-panel .order-type-toggle');
    
    if (queuePanels.length === 0) {
        console.log('❌ No queue panels with .order-type-toggle found, checking alternative selectors...');
        
        // Try alternative selectors
        const altPanels = document.querySelectorAll('#processingQueue .dealer-panel');
        if (altPanels.length > 0) {
            console.log(`Found ${altPanels.length} dealer panels in queue, but no .order-type-toggle elements`);
            
            // Check what's inside these panels
            altPanels.forEach((panel, i) => {
                const dealerName = panel.querySelector('.dealer-name')?.textContent || 'Unknown';
                const radioInputs = panel.querySelectorAll('input[type="radio"]');
                console.log(`Panel ${i} (${dealerName}): Has ${radioInputs.length} radio inputs`);
                
                // Look for toggle container by checking for radio buttons
                const toggleContainer = panel.querySelector('.toggle-container') || 
                                      panel.querySelector('.order-options') ||
                                      panel.querySelector('.radio-group') ||
                                      panel.querySelector('div:has(> input[type="radio"])');
                                      
                if (toggleContainer) {
                    console.log(`Found potential toggle container in ${dealerName}:`, toggleContainer.className);
                }
            });
        }
        
        return;
    }
    
    console.log(`Found ${queuePanels.length} queue panels to update with MAINTENANCE option`);
    
    queuePanels.forEach((toggleGroup, index) => {
        // Check if MAINTENANCE option already exists
        const existingMaintenance = toggleGroup.querySelector('.toggle-option[data-value="maintenance"]');
        
        if (!existingMaintenance) {
            const dealerPanel = toggleGroup.closest('.dealer-panel');
            const dealerName = dealerPanel?.querySelector('.dealer-name')?.textContent || `Dealer_${index}`;
            console.log(`Injecting MAINTENANCE option for ${dealerName}`);
            
            // Create MAINTENANCE option HTML
            const maintenanceOption = document.createElement('div');
            maintenanceOption.className = 'toggle-option';
            maintenanceOption.setAttribute('data-value', 'maintenance');
            maintenanceOption.style.display = 'flex';  // Force display
            maintenanceOption.innerHTML = `
                <input type="radio" id="orderTypeMaintenance_queue_${index}" name="order_type_queue_${index}" value="maintenance">
                <label for="orderTypeMaintenance_queue_${index}" class="modern-radio-label">
                    <div class="radio-indicator"></div>
                    <div class="radio-content">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color: currentColor;">
                            <path d="M21.71 8.71C22.1 8.32 22.1 7.69 21.71 7.3L16.7 2.29C16.31 1.9 15.68 1.9 15.29 2.29L13.29 4.29C12.9 4.68 12.9 5.31 13.29 5.7L15.29 7.7L9.29 13.7L7.29 11.7C6.9 11.31 6.27 11.31 5.88 11.7L3.88 13.7C3.49 14.09 3.49 14.72 3.88 15.11L8.89 20.12C9.28 20.51 9.91 20.51 10.3 20.12L12.3 18.12C12.69 17.73 12.69 17.1 12.3 16.71L10.3 14.71L16.3 8.71L18.3 10.71C18.69 11.1 19.32 11.1 19.71 10.71L21.71 8.71Z" fill="currentColor"/>
                            <circle cx="12" cy="12" r="1.5" fill="currentColor"/>
                        </svg>
                        <span class="radio-title">MAINTENANCE</span>
                        <span class="radio-desc">CAO + Manual VINs</span>
                    </div>
                </label>
            `;
            
            // Add after LIST option (or at the end)
            toggleGroup.appendChild(maintenanceOption);
            
            // Wire up the radio button functionality
            const radioInput = maintenanceOption.querySelector('input[type="radio"]');
            radioInput.addEventListener('change', function() {
                if (this.checked) {
                    console.log(`MAINTENANCE selected for ${dealerName}`);
                    
                    // Update the queue manager if available
                    if (window.queueManager && window.queueManager.processingQueue) {
                        const queueItem = window.queueManager.processingQueue.find(item => item.name === dealerName);
                        if (queueItem) {
                            queueItem.orderType = 'MAINTENANCE';
                            console.log(`Updated ${dealerName} to MAINTENANCE order type in queue`);
                        }
                    }
                    
                    // Update visual state
                    const panel = this.closest('.dealer-panel');
                    if (panel) {
                        panel.classList.remove('cao', 'list');
                        panel.classList.add('maintenance');
                    }
                }
            });
            
            console.log(`✅ MAINTENANCE option injected for ${dealerName}`);
        }
    });
};

// Try to inject immediately
setTimeout(() => {
    injectMaintenanceIntoQueue();
    
    // Monitor for queue changes
    const queueContainer = document.getElementById('processingQueue');
    if (queueContainer) {
        console.log('Setting up queue observer for MAINTENANCE injection...');
        const queueObserver = new MutationObserver((mutations) => {
            // Re-inject when queue changes
            setTimeout(injectMaintenanceIntoQueue, 100);
        });
        
        queueObserver.observe(queueContainer, {
            childList: true,
            subtree: true
        });
    }
}, 1000);

// Also inject periodically in case of dynamic updates
setInterval(() => {
    const panels = document.querySelectorAll('#processingQueue .dealer-panel');
    if (panels.length > 0) {
        const needsInjection = Array.from(panels).some(panel => {
            const toggle = panel.querySelector('.order-type-toggle');
            return toggle && !toggle.querySelector('.toggle-option[data-value="maintenance"]');
        });
        
        if (needsInjection) {
            console.log('Found panels missing MAINTENANCE option, injecting...');
            injectMaintenanceIntoQueue();
        }
    }
}, 2000);

console.log('✅ MAINTENANCE OPTION INJECTION SYSTEM LOADED');

// MANUAL DEBUGGING FUNCTION - Can be called from console
window.debugMaintenanceInjection = () => {
    console.log('=== MANUAL MAINTENANCE DEBUG ===');
    
    // Try multiple selectors for the queue
    const queue = document.getElementById('processingQueue') || 
                  document.querySelector('.processing-queue') ||
                  document.querySelector('[id*="queue"]') ||
                  document.querySelector('[class*="queue"]');
    
    if (!queue) {
        console.log('❌ No processing queue element found!');
        console.log('Searching for queue-like elements...');
        
        // Search for any element containing "Bommarito Cadillac"
        const allElements = document.querySelectorAll('*');
        let foundQueue = null;
        
        for (let elem of allElements) {
            if (elem.textContent && elem.textContent.includes('Bommarito Cadillac') && 
                elem.textContent.includes('CAO')) {
                console.log('Found element with Bommarito Cadillac:', elem);
                console.log('Element ID:', elem.id);
                console.log('Element classes:', elem.className);
                
                // Check if this looks like a queue panel
                const parent = elem.closest('.dealer-panel') || elem.closest('[class*="panel"]');
                if (parent) {
                    foundQueue = parent.parentElement;
                    console.log('Found parent queue container:', foundQueue);
                    break;
                }
            }
        }
        
        if (!foundQueue) {
            console.log('Still no queue found. Looking for Processing Queue header...');
            const headers = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5')).filter(h => 
                h.textContent.includes('Processing Queue')
            );
            if (headers.length > 0) {
                console.log('Found Processing Queue header:', headers[0]);
                const nextSibling = headers[0].nextElementSibling;
                console.log('Next sibling after header:', nextSibling);
                foundQueue = nextSibling;
            }
        }
        
        if (foundQueue) {
            queue = foundQueue;
        } else {
            return;
        }
    }
    
    console.log('✅ Processing queue found');
    console.log('Queue HTML (first 1000 chars):', queue.innerHTML.substring(0, 1000));
    
    // Find all dealer panels
    const panels = queue.querySelectorAll('.dealer-panel');
    console.log(`Found ${panels.length} dealer panels in queue`);
    
    if (panels.length === 0) {
        console.log('❌ No dealer panels in queue. Add a dealership first.');
        return;
    }
    
    // Examine first panel in detail
    const firstPanel = panels[0];
    console.log('First panel classes:', firstPanel.className);
    
    // Find all divs that might contain radio buttons
    const allDivs = firstPanel.querySelectorAll('div');
    console.log(`Panel has ${allDivs.length} div elements`);
    
    // Find radio buttons
    const radios = firstPanel.querySelectorAll('input[type="radio"]');
    console.log(`Panel has ${radios.length} radio buttons`);
    
    radios.forEach((radio, i) => {
        console.log(`Radio ${i}: name="${radio.name}", value="${radio.value}", id="${radio.id}"`);
        const label = firstPanel.querySelector(`label[for="${radio.id}"]`);
        if (label) {
            console.log(`  Label text: ${label.textContent.trim()}`);
        }
    });
    
    // Find the container that holds the radio buttons
    if (radios.length > 0) {
        const radioParent = radios[0].parentElement;
        console.log('Radio button parent element:', radioParent.className || radioParent.tagName);
        console.log('Radio button parent HTML:', radioParent.outerHTML.substring(0, 500));
        
        // Try to inject MAINTENANCE option here
        console.log('🔧 ATTEMPTING FORCE INJECTION...');
        
        const maintenanceHTML = `
            <div class="toggle-option" data-value="maintenance" style="display: flex !important;">
                <input type="radio" id="orderTypeMaintenance_debug" name="${radios[0].name}" value="maintenance">
                <label for="orderTypeMaintenance_debug" class="modern-radio-label">
                    <div class="radio-indicator"></div>
                    <div class="radio-content">
                        <span style="color: orange;">🔧</span>
                        <span class="radio-title">MAINTENANCE</span>
                        <span class="radio-desc">CAO + Manual VINs</span>
                    </div>
                </label>
            </div>
        `;
        
        // Insert after the last radio option
        const lastOption = radioParent.parentElement.querySelector('.toggle-option:last-child');
        if (lastOption) {
            lastOption.insertAdjacentHTML('afterend', maintenanceHTML);
            console.log('✅ MAINTENANCE option injected after last option!');
        } else {
            radioParent.insertAdjacentHTML('beforeend', maintenanceHTML);
            console.log('✅ MAINTENANCE option injected at end of container!');
        }
    }
};

console.log('🛠️ Manual debug function available: Run debugMaintenanceInjection() in console');

// DIRECT FORCE INJECTION - Works on visible panels
window.forceMaintenanceOption = () => {
    console.log('🔧 FORCE INJECTING MAINTENANCE OPTION...');
    
    // Find ALL panels that have Bommarito Cadillac
    const allPanels = Array.from(document.querySelectorAll('*')).filter(elem => {
        return elem.textContent && 
               elem.textContent.includes('Bommarito Cadillac') && 
               (elem.textContent.includes('CAO') || elem.textContent.includes('List'));
    });
    
    console.log(`Found ${allPanels.length} elements with Bommarito text`);
    
    if (allPanels.length === 0) {
        console.log('❌ No Bommarito panels found. Make sure it\'s added to queue.');
        return;
    }
    
    // Find the one that looks like a dealer panel
    let targetPanel = null;
    for (let panel of allPanels) {
        // Look for radio buttons nearby
        const radios = panel.querySelectorAll('input[type="radio"]');
        if (radios.length > 0) {
            targetPanel = panel;
            console.log('✅ Found panel with radio buttons:', panel);
            break;
        }
    }
    
    if (!targetPanel) {
        // Try the parent of the first match
        targetPanel = allPanels[0];
        console.log('Using first matching panel:', targetPanel);
    }
    
    // Find where the radio buttons are
    const existingRadios = targetPanel.querySelectorAll('input[type="radio"]');
    console.log(`Found ${existingRadios.length} existing radio buttons`);
    
    if (existingRadios.length === 0) {
        console.log('❌ No radio buttons found in panel');
        return;
    }
    
    // Check if MAINTENANCE already exists
    const existingMaintenance = Array.from(existingRadios).find(r => r.value === 'maintenance');
    if (existingMaintenance) {
        console.log('✅ MAINTENANCE option already exists!');
        existingMaintenance.checked = true;
        return;
    }
    
    // Get the container that holds the radio options
    const firstRadio = existingRadios[0];
    const optionContainer = firstRadio.closest('.toggle-option') || firstRadio.parentElement;
    const toggleGroup = optionContainer.parentElement;
    
    console.log('Radio container:', toggleGroup);
    
    // Create and inject MAINTENANCE option
    const maintenanceDiv = document.createElement('div');
    maintenanceDiv.className = 'toggle-option';
    maintenanceDiv.setAttribute('data-value', 'maintenance');
    maintenanceDiv.style.cssText = 'display: flex !important; visibility: visible !important;';
    
    // Get the name from existing radios
    const radioName = firstRadio.name || 'order_type';
    const uniqueId = 'orderTypeMaintenance_' + Date.now();
    
    maintenanceDiv.innerHTML = `
        <input type="radio" id="${uniqueId}" name="${radioName}" value="maintenance" style="display: block !important;">
        <label for="${uniqueId}" class="modern-radio-label" style="display: flex !important;">
            <div class="radio-indicator"></div>
            <div class="radio-content">
                <i class="fas fa-wrench" style="color: #ff6b35;"></i>
                <span class="radio-title">MAINTENANCE</span>
                <span class="radio-desc">CAO + Manual VINs</span>
            </div>
        </label>
    `;
    
    // Add it to the container
    toggleGroup.appendChild(maintenanceDiv);
    
    console.log('✅ MAINTENANCE option injected successfully!');
    
    // Wire up the functionality
    const newRadio = maintenanceDiv.querySelector('input[type="radio"]');
    newRadio.addEventListener('change', function() {
        if (this.checked) {
            console.log('MAINTENANCE selected!');
            
            // Update visual state
            const panel = this.closest('.dealer-panel');
            if (panel) {
                panel.classList.remove('cao', 'list');
                panel.classList.add('maintenance');
                
                // Update the data
                const dealerName = panel.querySelector('.dealer-name')?.textContent || 'Unknown';
                console.log(`Updated ${dealerName} to MAINTENANCE type`);
            }
        }
    });
    
    // Select it
    newRadio.checked = true;
    newRadio.dispatchEvent(new Event('change'));
};

console.log('🎯 Direct injection available: Run forceMaintenanceOption() in console');

// FORCE SHOW MAINTENANCE - Makes the existing hidden option visible
window.showMaintenanceOption = () => {
    console.log('🔍 SEARCHING FOR HIDDEN MAINTENANCE OPTION...');
    
    // Find ALL radio buttons with value="maintenance"
    const maintenanceRadios = document.querySelectorAll('input[type="radio"][value="maintenance"]');
    console.log(`Found ${maintenanceRadios.length} MAINTENANCE radio buttons`);
    
    if (maintenanceRadios.length === 0) {
        console.log('❌ No MAINTENANCE radio buttons found');
        return;
    }
    
    // Make each one and its container visible
    maintenanceRadios.forEach((radio, index) => {
        console.log(`Processing MAINTENANCE radio ${index + 1}:`);
        console.log('  Radio ID:', radio.id);
        console.log('  Radio name:', radio.name);
        console.log('  Current checked state:', radio.checked);
        console.log('  Current display:', window.getComputedStyle(radio).display);
        
        // Force the radio button to be visible
        radio.style.display = 'block !important';
        radio.style.visibility = 'visible !important';
        radio.style.opacity = '1 !important';
        
        // Find the parent toggle-option container
        let container = radio.closest('.toggle-option');
        if (!container) {
            container = radio.parentElement;
            console.log('  No .toggle-option container, using parent:', container.className);
        }
        
        if (container) {
            console.log('  Container class:', container.className);
            console.log('  Container current display:', window.getComputedStyle(container).display);
            
            // Force container to be visible with inline styles
            container.style.cssText = 'display: flex !important; visibility: visible !important; opacity: 1 !important; height: auto !important; overflow: visible !important;';
            container.removeAttribute('hidden');
            container.removeAttribute('aria-hidden');
            
            // Also check if it has a data-value attribute
            const dataValue = container.getAttribute('data-value');
            console.log('  Container data-value:', dataValue);
            
            // Check parent containers too
            let parent = container.parentElement;
            while (parent && parent !== document.body) {
                const parentDisplay = window.getComputedStyle(parent).display;
                if (parentDisplay === 'none') {
                    console.log('  ⚠️ Parent container is hidden:', parent.className);
                    parent.style.display = 'block !important';
                }
                parent = parent.parentElement;
            }
        }
        
        // Find and fix the label
        const label = document.querySelector(`label[for="${radio.id}"]`);
        if (label) {
            console.log('  Label found, making visible');
            label.style.display = 'flex !important';
            label.style.visibility = 'visible !important';
            label.style.opacity = '1 !important';
        }
        
        // Check final visibility
        const finalDisplay = window.getComputedStyle(radio).display;
        const containerFinalDisplay = container ? window.getComputedStyle(container).display : 'N/A';
        console.log(`  ✅ Final radio display: ${finalDisplay}`);
        console.log(`  ✅ Final container display: ${containerFinalDisplay}`);
    });
    
    // Also remove any CSS that might be hiding maintenance options
    const style = document.createElement('style');
    style.innerHTML = `
        .toggle-option[data-value="maintenance"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            height: auto !important;
            overflow: visible !important;
        }
        input[value="maintenance"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        label[for*="Maintenance"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
    `;
    document.head.appendChild(style);
    console.log('✅ Added override CSS to force visibility');
    
    // Try to click the first maintenance radio to select it
    if (maintenanceRadios.length > 0) {
        maintenanceRadios[0].click();
        console.log('✅ Clicked MAINTENANCE radio button to select it');
    }
};

console.log('🎨 Visibility fix available: Run showMaintenanceOption() in console');

// TARGET THE CORRECT QUEUE PANELS - Not the modal!
window.addMaintenanceToQueue = () => {
    console.log('🎯 TARGETING ACTUAL QUEUE PANELS (not modal)...');
    
    // Look for the queue container by its content
    const possibleQueues = [
        document.querySelector('.queue-container'),
        document.querySelector('.processing-queue'),
        document.querySelector('[class*="queue"]'),
        document.querySelector('.queue-items'),
        document.querySelector('.order-queue')
    ].filter(Boolean);
    
    console.log(`Found ${possibleQueues.length} potential queue containers`);
    
    // Find the container that has Bommarito Cadillac in it
    let queueContainer = null;
    const allContainers = document.querySelectorAll('*');
    
    for (let container of allContainers) {
        // Skip the modal
        if (container.classList.contains('modal') || container.closest('.modal')) {
            continue;
        }
        
        // Look for container with Bommarito Cadillac that's NOT in a modal
        if (container.textContent && 
            container.textContent.includes('Bommarito Cadillac') &&
            container.textContent.includes('CAO') &&
            !container.classList.contains('modal') &&
            container.querySelector && 
            container.querySelector('input[type="radio"]')) {
            
            console.log('Found potential queue panel:', container);
            console.log('Container classes:', container.className);
            console.log('Container ID:', container.id);
            
            queueContainer = container;
            break;
        }
    }
    
    if (!queueContainer) {
        console.log('❌ No queue panels found with Bommarito Cadillac');
        console.log('Looking for ANY panel with radio buttons that is NOT in a modal...');
        
        // Find all radio buttons
        const allRadios = document.querySelectorAll('input[type="radio"][name*="order"]');
        console.log(`Found ${allRadios.length} order-related radio buttons`);
        
        for (let radio of allRadios) {
            // Skip if in modal
            if (radio.closest('.modal')) {
                console.log('Skipping radio in modal:', radio.name);
                continue;
            }
            
            console.log('Found radio NOT in modal:', {
                name: radio.name,
                value: radio.value,
                id: radio.id,
                checked: radio.checked
            });
            
            // Get the panel this radio is in
            const panel = radio.closest('.dealer-panel') || 
                         radio.closest('[class*="panel"]') ||
                         radio.parentElement.parentElement;
            
            if (panel) {
                console.log('Found panel containing radio:', panel);
                queueContainer = panel;
                break;
            }
        }
    }
    
    if (!queueContainer) {
        console.log('❌ Still no queue panels found');
        return;
    }
    
    console.log('✅ Found queue container, looking for radio buttons...');
    
    // Find the radio buttons in this container
    const radios = queueContainer.querySelectorAll('input[type="radio"]');
    console.log(`Found ${radios.length} radio buttons in queue panel`);
    
    // Check if MAINTENANCE already exists
    const existingMaintenance = Array.from(radios).find(r => r.value === 'maintenance');
    if (existingMaintenance) {
        console.log('✅ MAINTENANCE already exists in queue panel!');
        existingMaintenance.checked = true;
        existingMaintenance.click();
        return;
    }
    
    // Need to add MAINTENANCE option
    if (radios.length > 0) {
        const firstRadio = radios[0];
        const radioContainer = firstRadio.parentElement.parentElement;
        
        console.log('Adding MAINTENANCE option to:', radioContainer);
        
        const maintenanceHTML = `
            <div class="toggle-option" data-value="maintenance" style="display: flex !important;">
                <input type="radio" id="${firstRadio.name}_maintenance" name="${firstRadio.name}" value="maintenance">
                <label for="${firstRadio.name}_maintenance" class="modern-radio-label" style="display: flex !important;">
                    <div class="radio-indicator"></div>
                    <div class="radio-content">
                        <i class="fas fa-wrench" style="color: #ff6b35;"></i>
                        <span class="radio-title">MAINTENANCE</span>
                        <span class="radio-desc">CAO + Manual</span>
                    </div>
                </label>
            </div>
        `;
        
        radioContainer.insertAdjacentHTML('beforeend', maintenanceHTML);
        
        // Click it
        const newRadio = radioContainer.querySelector('input[value="maintenance"]');
        if (newRadio) {
            newRadio.click();
            console.log('✅ MAINTENANCE option added and selected!');
        }
    }
};

console.log('🔧 Queue injection available: Run addMaintenanceToQueue() in console');
console.log('🎯 RAW STATUS FETCH ENABLED - TIMESTAMP: Mon, Sep  8, 2025 12:39:02 PM');
