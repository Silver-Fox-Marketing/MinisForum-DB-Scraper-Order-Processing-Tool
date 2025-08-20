/**
 * Order Processing Wizard - JavaScript Controller v2.1 FINAL
 * Silver Fox Marketing - Guided Order Processing Interface
 * 
 * UPDATED: Continue to Data Editor button DISABLED
 * WORKFLOW: QR Generation → Enter Order Number → VIN Logging
 * VERSION: 2025-08-19 17:25 - BUTTON ELIMINATION COMPLETE
 * 
 * Handles wizard-style order processing with step-by-step workflow
 */

// FORCE CACHE REFRESH - DISABLE DATA EDITOR WORKFLOW
console.log('🔥 ORDER WIZARD v2.1 LOADED - DATA EDITOR DISABLED');
console.log('✅ Correct workflow: QR Generation → Enter Order Number → VIN Log');
console.log('❌ Continue to Data Editor button functionality ELIMINATED');

// GLOBAL FUNCTION to handle ANY calls to proceedToDataEditor (even from cached templates)
window.proceedToDataEditor = function() {
    console.log('❌ proceedToDataEditor() called but DISABLED - redirecting to QR generation');
    alert('Data Editor workflow has been disabled.\n\nCorrect workflow: QR Generation → Enter Order Number → VIN Logging');
    
    // Find wizard instance and redirect to correct workflow
    if (window.wizard && typeof window.wizard.proceedToQRGeneration === 'function') {
        window.wizard.proceedToQRGeneration();
    } else {
        console.error('Could not find wizard instance for redirect');
    }
    return false;
};

// GLOBAL wizard reference for proceedToDataEditor function
window.wizard = null;

class OrderWizard {
    constructor() {
        this.currentStep = 0;
        this.steps = ['initialize', 'cao', 'list', 'review', 'qr-generation', 'order-number', 'complete'];
        this.queueData = [];
        this.caoOrders = [];
        this.listOrders = [];
        this.currentListIndex = 0;
        this.processedOrders = [];
        this.currentOrderVins = [];
        this.currentOrderDealership = null;
        this.processingResults = {
            totalDealerships: 0,
            caoProcessed: 0,
            listProcessed: 0,
            totalVehicles: 0,
            filesGenerated: 0,
            errors: []
        };
        
        this.init();
    }
    
    init() {
        console.log('Initializing Order Processing Wizard...');
        
        // Make wizard instance globally available for proceedToDataEditor override
        window.wizard = this;
        
        // Load queue data from localStorage
        this.loadQueueData();
        
        // Initialize the first step
        this.initializeStep();
    }
    
    loadQueueData() {
        try {
            const queueData = localStorage.getItem('orderWizardQueue');
            if (queueData) {
                this.queueData = JSON.parse(queueData);
                console.log('Loaded queue data:', this.queueData);
                
                // Separate CAO and List orders
                this.caoOrders = this.queueData.filter(item => item.orderType === 'CAO');
                this.listOrders = this.queueData.filter(item => item.orderType === 'LIST');
                
                this.processingResults.totalDealerships = this.queueData.length;
            } else {
                console.error('No queue data found');
                this.showError('No queue data available. Please return to the main dashboard and setup your queue.');
            }
            
            // Load testing mode setting from localStorage
            const testingMode = localStorage.getItem('orderWizardTestingMode') === 'true';
            const testingCheckbox = document.getElementById('skipVinLogging');
            if (testingCheckbox) {
                testingCheckbox.checked = testingMode;
                console.log('Applied testing mode setting:', testingMode);
            }
            
        } catch (error) {
            console.error('Error loading queue data:', error);
            this.showError('Error loading queue data: ' + error.message);
        }
    }
    
    initializeStep() {
        // Update total dealerships display
        const totalElement = document.getElementById('totalDealerships');
        if (totalElement) {
            totalElement.textContent = this.queueData.length;
        }
        
        // Create queue summary display
        this.renderQueueSummary();
    }
    
    renderQueueSummary() {
        const summaryContainer = document.getElementById('queueSummaryDisplay');
        if (!summaryContainer) return;
        
        const caoCount = this.caoOrders.length;
        const listCount = this.listOrders.length;
        
        summaryContainer.innerHTML = `
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="card-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="card-content">
                        <h3>CAO Orders (Automatic)</h3>
                        <div class="card-value">${caoCount}</div>
                        <div class="card-details">
                            ${this.caoOrders.map(order => order.name).join(', ') || 'None'}
                        </div>
                    </div>
                </div>
                
                <div class="summary-card">
                    <div class="card-icon">
                        <i class="fas fa-list"></i>
                    </div>
                    <div class="card-content">
                        <h3>List Orders (VIN Entry)</h3>
                        <div class="card-value">${listCount}</div>
                        <div class="card-details">
                            ${this.listOrders.map(order => order.name).join(', ') || 'None'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    startProcessing() {
        this.updateProgress('cao');
        this.showStep('caoStep');
        
        if (this.caoOrders.length > 0) {
            this.processCaoOrders();
        } else {
            // Skip to list processing if no CAO orders
            setTimeout(() => {
                this.proceedToListProcessing();
            }, 1000);
        }
    }
    
    async processCaoOrders() {
        const statusContainer = document.getElementById('caoProcessingStatus');
        if (!statusContainer) return;
        
        statusContainer.innerHTML = `
            <div class="processing-header">
                <h3>Processing ${this.caoOrders.length} CAO Orders...</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="caoProgressFill" style="width: 0%"></div>
                </div>
            </div>
            <div class="processing-list" id="caoProcessingList"></div>
        `;
        
        const processingList = document.getElementById('caoProcessingList');
        const progressFill = document.getElementById('caoProgressFill');
        
        for (let i = 0; i < this.caoOrders.length; i++) {
            const order = this.caoOrders[i];
            
            // Add processing item
            const processingItem = document.createElement('div');
            processingItem.className = 'processing-item';
            processingItem.innerHTML = `
                <div class="processing-dealership">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>${order.name}</span>
                </div>
                <div class="processing-status">Processing...</div>
            `;
            processingList.appendChild(processingItem);
            
            try {
                // Process CAO order
                const result = await this.processCaoOrder(order.name);
                
                // Store result for review and data editing
                this.processedOrders.push({
                    dealership: order.name,
                    type: 'cao',
                    result: result
                });
                
                // Update item status
                processingItem.innerHTML = `
                    <div class="processing-dealership">
                        <i class="fas fa-check text-success"></i>
                        <span>${order.name}</span>
                    </div>
                    <div class="processing-status text-success">
                        ${result.vehicles_processed || 0} vehicles processed
                    </div>
                `;
                
                this.processingResults.caoProcessed++;
                this.processingResults.totalVehicles += result.vehicles_processed || 0;
                this.processingResults.filesGenerated += result.files_generated || 0;
                
            } catch (error) {
                // Update item status with error
                processingItem.innerHTML = `
                    <div class="processing-dealership">
                        <i class="fas fa-times text-error"></i>
                        <span>${order.name}</span>
                    </div>
                    <div class="processing-status text-error">
                        Error: ${error.message}
                    </div>
                `;
                
                this.processingResults.errors.push(`${order.name}: ${error.message}`);
            }
            
            // Update progress
            const progress = ((i + 1) / this.caoOrders.length) * 100;
            progressFill.style.width = `${progress}%`;
            
            // Small delay between processing
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // Check if we have processed orders that need review
        if (this.processedOrders.length > 0) {
            // Show review step for processed CAO orders
            const lastProcessedOrder = this.processedOrders[this.processedOrders.length - 1];
            this.showReviewStep(lastProcessedOrder.dealership, lastProcessedOrder.result);
        } else {
            // Show continue button if no orders were processed
            const nextBtn = document.getElementById('caoNextBtn');
            if (nextBtn) {
                nextBtn.style.display = 'inline-flex';
            }
        }
    }
    
    async processCaoOrder(dealershipName) {
        // Get testing mode checkbox state
        const skipVinLogging = document.getElementById('skipVinLoggingCAO')?.checked || false;
        
        const response = await fetch('/api/orders/process-cao', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dealerships: [dealershipName],
                vehicle_types: ['new', 'cpo', 'used'],
                skip_vin_logging: skipVinLogging
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to process CAO order: ${response.statusText}`);
        }
        
        const results = await response.json();
        const result = results[0] || results; // Handle both array and single object responses
        
        // Map backend fields to frontend expected fields
        const mappedResult = {
            vehicles_processed: result.new_vehicles || 0,
            files_generated: result.qr_codes_generated || 0,
            success: result.success,
            dealership: result.dealership,
            download_csv: result.download_csv,
            qr_folder: result.qr_folder,
            csv_file: result.csv_file,
            timestamp: result.timestamp
        };
        
        return mappedResult;
    }
    
    skipCAO() {
        this.proceedToListProcessing();
    }
    
    proceedToListProcessing() {
        if (this.listOrders.length === 0) {
            // Skip to completion if no list orders
            this.completeProcessing();
            return;
        }
        
        this.updateProgress('list');
        this.showStep('listStep');
        this.showCurrentListOrder();
    }
    
    showCurrentListOrder() {
        if (this.currentListIndex >= this.listOrders.length) {
            this.completeProcessing();
            return;
        }
        
        const currentOrder = this.listOrders[this.currentListIndex];
        
        // Update dealership display
        const dealershipNameEl = document.getElementById('currentDealershipName');
        const dealershipDisplayEl = document.getElementById('dealershipDisplayName');
        
        if (dealershipNameEl) dealershipNameEl.textContent = currentOrder.name;
        if (dealershipDisplayEl) dealershipDisplayEl.textContent = currentOrder.name;
        
        // Clear VIN input
        const vinInput = document.getElementById('vinInput');
        if (vinInput) {
            vinInput.value = '';
            vinInput.focus();
        }
    }
    
    async processCurrentDealership() {
        const currentOrder = this.listOrders[this.currentListIndex];
        const vinInput = document.getElementById('vinInput');
        
        if (!vinInput || !vinInput.value.trim()) {
            alert('Please enter VINs for this dealership');
            return;
        }
        
        // Parse VINs
        const vins = vinInput.value.trim().split('\n')
            .map(vin => vin.trim())
            .filter(vin => vin.length > 0);
        
        if (vins.length === 0) {
            alert('Please enter valid VINs');
            return;
        }
        
        try {
            // Process list order
            const result = await this.processListOrder(currentOrder.name, vins);
            
            // Store result for review
            this.processedOrders.push({
                dealership: currentOrder.name,
                vins: vins,
                result: result
            });
            
            this.processingResults.listProcessed++;
            this.processingResults.totalVehicles += result.vehicles_processed || 0;
            this.processingResults.filesGenerated += result.files_generated || 0;
            
            // Show review step
            this.showReviewStep(currentOrder.name, result);
            
        } catch (error) {
            alert(`Error processing ${currentOrder.name}: ${error.message}`);
            this.processingResults.errors.push(`${currentOrder.name}: ${error.message}`);
        }
    }
    
    async processListOrder(dealershipName, vins) {
        // Get testing mode checkbox state
        const skipVinLogging = document.getElementById('skipVinLogging')?.checked || false;
        
        const response = await fetch('/api/orders/process-list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dealership: dealershipName,
                vins: vins,
                skip_vin_logging: skipVinLogging
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to process list order: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    showReviewStep(dealershipName, result) {
        this.updateProgress('review');
        this.showStep('reviewStep');
        
        // Update dealership name
        const reviewDealershipEl = document.getElementById('reviewDealershipName');
        if (reviewDealershipEl) {
            reviewDealershipEl.textContent = dealershipName;
        }
        
        // Show generated files
        this.renderOutputFiles(result);
    }
    
    renderOutputFiles(result) {
        // Store the result for later use
        this.currentOrderResult = result;
        
        // Load CSV data into spreadsheet view
        this.loadCSVIntoSpreadsheet(result);
        
        // Load QR codes into preview grid (if they exist)
        this.loadQRCodesIntoGrid(result);
    }
    
    // Navigate from CSV review to QR generation
    proceedToQRGeneration() {
        if (!this.currentOrderResult) {
            console.error('No current order result available for QR generation');
            return;
        }
        
        this.showQRGenerationStep(this.currentOrderResult.dealership, this.currentOrderResult);
    }
    
    // Navigate from QR generation to order number entry
    proceedToOrderNumber() {
        console.log('🔍 DEBUG: proceedToOrderNumber called');
        console.log('🔍 DEBUG: currentOrderResult:', !!this.currentOrderResult);
        console.log('🔍 DEBUG: currentQRResult:', !!this.currentQRResult);
        
        if (!this.currentOrderResult) {
            console.error('No current order result available for order number entry');
            return;
        }
        
        // Ensure QR result is available for the order number step
        if (!this.currentQRResult && this.currentOrderResult) {
            console.log('🔍 DEBUG: Using currentOrderResult as QR result');
            this.currentQRResult = this.currentOrderResult;
        }
        
        this.showOrderNumberStep(this.currentOrderResult.dealership, this.currentOrderResult);
    }
    
    showQRGenerationStep(dealershipName, result) {
        console.log('🆕 CLEAN QR GENERATION STEP - NO DATA EDITOR POSSIBLE');
        this.updateProgress('qr-generation');
        
        // FIND THE CORRECT CONTAINER - TRY MULTIPLE POSSIBLE IDs
        let container = document.getElementById('wizardContent') || 
                       document.getElementById('app') || 
                       document.querySelector('.wizard-container') ||
                       document.querySelector('.container') ||
                       document.body;
        
        if (!container) {
            console.error('❌ Could not find container element');
            alert('Container element not found - cannot display QR generation step');
            return;
        }
        
        console.log('✅ Found container:', container.id || container.className || container.tagName);
        
        // COMPLETELY RECREATE THE QR GENERATION HTML - NO DATA EDITOR BUTTON
        container.innerHTML = `
            <div class="wizard-step active" id="qrGenerationStep">
                <div class="step-header">
                    <h2 class="step-title"><i class="fas fa-qrcode"></i> QR Code Generation</h2>
                    <p class="step-description">Generate QR codes for ${dealershipName} vehicles</p>
                </div>
                
                <div class="qr-status-card">
                    <div class="status-header">
                        <i class="fas fa-info-circle"></i>
                        <span>Ready to generate QR codes for <strong>${result.vehicles_processed || 0}</strong> vehicles</span>
                    </div>
                    <div class="status-details">
                        <p>CSV File: ${result.download_csv ? result.download_csv.split('/').pop() : 'Available'}</p>
                        <p>Dealership: ${dealershipName}</p>
                    </div>
                </div>
                
                <div class="qr-results" id="qrResults" style="display: none;">
                    <div class="success-message">
                        <i class="fas fa-check-circle"></i>
                        <span>QR codes generated successfully!</span>
                    </div>
                </div>
                
                <!-- CLEAN ACTION BUTTONS - NO DATA EDITOR -->
                <div class="wizard-actions">
                    <button class="btn-wizard secondary" onclick="wizard.backToCsvReview()">
                        <i class="fas fa-arrow-left"></i>
                        Back to CSV Review
                    </button>
                    <button class="btn-wizard primary" onclick="wizard.generateQRCodes()" id="generateQRBtn">
                        <i class="fas fa-qrcode"></i>
                        Generate QR Codes
                    </button>
                    <button class="btn-wizard primary" onclick="wizard.proceedToOrderNumber()" id="qrProceedBtn" style="display: none;">
                        <i class="fas fa-hashtag"></i>
                        Enter Order Number
                    </button>
                </div>
            </div>
        `;
        
        console.log('✅ QR Generation HTML recreated - ONLY "Enter Order Number" button exists');
    }
    
    setupQRGenerationDetails(dealershipName, result) {
        // Update QR generation details
        const qrCsvFileName = document.getElementById('qrCsvFileName');
        const qrVehicleCount = document.getElementById('qrVehicleCount');
        const qrOrderNumber = document.getElementById('qrOrderNumber');
        const qrOutputFolder = document.getElementById('qrOutputFolder');
        
        if (qrCsvFileName && result.download_csv) {
            // Extract filename from download path
            const filename = result.download_csv.split('/').pop();
            qrCsvFileName.textContent = filename;
        }
        
        if (qrVehicleCount) {
            qrVehicleCount.textContent = result.vehicles_processed || 0;
        }
        
        if (qrOrderNumber) {
            // Try to get order number from current context or show as "Auto-Generated"
            qrOrderNumber.textContent = this.currentOrderNumber || 'Auto-Generated';
        }
        
        if (qrOutputFolder) {
            // Show expected output folder pattern
            const cleanDealership = dealershipName.replace(/[^a-zA-Z0-9]/g, '_');
            const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
            qrOutputFolder.textContent = `${cleanDealership}_${today}_QRCodes/`;
        }
    }
    
    toggleTechnicalDetails() {
        const details = document.getElementById('qrTechnicalDetails');
        const toggleBtn = document.getElementById('qrToggleBtn');
        
        if (details.style.display === 'none') {
            details.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Technical Details';
        } else {
            details.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Show Technical Details';
        }
    }
    
    toggleQRFileList() {
        const fileList = document.getElementById('qrFileList');
        const toggleBtn = document.getElementById('qrPreviewToggle');
        
        if (fileList.style.display === 'none') {
            fileList.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Details';
        } else {
            fileList.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Show Details';
        }
    }
    
    async generateQRCodes() {
        console.log('🆕 CLEAN QR GENERATION - NO DATA EDITOR WORKFLOW');
        
        if (!this.currentOrderResult) {
            console.error('No current order result available');
            return;
        }
        
        const generateQRBtn = document.getElementById('generateQRBtn');
        const qrProceedBtn = document.getElementById('qrProceedBtn');
        const qrResults = document.getElementById('qrResults');
        
        try {
            // Show progress and disable button
            generateQRBtn.disabled = true;
            generateQRBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            qrResults.style.display = 'none';
            
            // Extract CSV filename from the result
            let csvFilename = '';
            if (this.currentOrderResult.download_csv) {
                csvFilename = this.currentOrderResult.download_csv.split('/').pop();
            } else if (this.currentOrderResult.csv_file) {
                csvFilename = this.currentOrderResult.csv_file.split('/').pop().replace(/\\\\/g, '/').split('/').pop();
            }
            
            if (!csvFilename) {
                throw new Error('No CSV file available for QR generation');
            }
            
            console.log('[QR GENERATION] Starting with CSV file:', csvFilename);
            
            // Call the QR generation API
            const response = await fetch('/api/qr/generate-from-csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    csv_filename: csvFilename,
                    dealership_name: this.currentOrderResult.dealership,
                    order_number: this.currentOrderNumber || ''
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'QR generation failed');
            }
            
            const result = await response.json();
            console.log('[QR GENERATION] Success:', result);
            
            // IMMEDIATELY CREATE ORDER NUMBER BUTTON - NO WAITING
            const container = generateQRBtn.parentElement;
            let orderBtn = document.getElementById('qrProceedBtn');
            if (!orderBtn) {
                orderBtn = document.createElement('button');
                orderBtn.id = 'qrProceedBtn';
                orderBtn.className = 'btn-wizard primary';
                orderBtn.style.marginLeft = '20px';
                orderBtn.onclick = () => this.proceedToOrderNumber();
                orderBtn.innerHTML = '<i class="fas fa-hashtag"></i> Enter Order Number';
                container.appendChild(orderBtn);
                console.log('✅ FORCE CREATED Order Number button after QR success');
            }
            
            // Reset generate button
            generateQRBtn.disabled = false;
            const billingText = result.billing_csv_generated ? ' + Billing CSV' : '';
            generateQRBtn.innerHTML = `<i class="fas fa-check"></i> QR Codes Generated${billingText}`;
            generateQRBtn.style.background = '#28a745';
            
            // FORCE SHOW THE BUTTON - MULTIPLE METHODS
            setTimeout(() => {
                let orderBtn = document.getElementById('qrProceedBtn');
                if (orderBtn) {
                    orderBtn.style.display = 'inline-flex';
                    orderBtn.style.visibility = 'visible';
                    orderBtn.style.opacity = '1';
                    console.log('✅ Made existing Order Number button visible');
                } else {
                    // Create it again if it doesn't exist
                    const newBtn = document.createElement('button');
                    newBtn.id = 'qrProceedBtn';
                    newBtn.className = 'btn-wizard primary';
                    newBtn.style.cssText = 'margin-left: 20px; display: inline-flex !important; visibility: visible !important; opacity: 1 !important;';
                    newBtn.onclick = () => this.proceedToOrderNumber();
                    newBtn.innerHTML = '<i class="fas fa-hashtag"></i> Enter Order Number';
                    generateQRBtn.parentElement.appendChild(newBtn);
                    console.log('🚨 EMERGENCY: Re-created Order Number button');
                }
                
                // Also add a bright red emergency button as backup
                const emergencyBtn = document.createElement('button');
                emergencyBtn.className = 'btn-wizard';
                emergencyBtn.style.cssText = 'background: red !important; color: white !important; margin-left: 20px !important; display: inline-flex !important;';
                emergencyBtn.onclick = () => {
                    alert('Emergency Order Number Entry');
                    this.proceedToOrderNumber();
                };
                emergencyBtn.innerHTML = '🚨 EMERGENCY: Enter Order Number';
                generateQRBtn.parentElement.appendChild(emergencyBtn);
                console.log('🚨 Created bright red emergency button as backup');
                
            }, 500);
            
            // Handle case where QR codes already exist
            if (result.qr_codes_exist) {
                // Hide progress and show results immediately
                qrProgress.style.display = 'none';
                qrResults.style.display = 'block';
                
                // Update result stats for existing QR codes
                const qrGeneratedCount = document.getElementById('qrGeneratedCount');
                const qrFolderName = document.getElementById('qrFolderName');
                const qrVehicleCount = document.getElementById('qrVehicleCount');
                
                if (qrGeneratedCount) qrGeneratedCount.textContent = result.vehicles_with_urls || result.total_vehicles || 'N/A';
                if (qrFolderName) qrFolderName.textContent = 'Previously Generated';
                if (qrVehicleCount) qrVehicleCount.textContent = result.total_vehicles || 'N/A';
                
                // Show message that QR codes already exist
                const qrStatusCard = document.querySelector('.qr-status-card');
                if (qrStatusCard) {
                    qrStatusCard.innerHTML = `
                        <div class="qr-info">
                            <h4><i class="fas fa-check-circle"></i> QR Codes Already Generated</h4>
                            <p>${result.message}</p>
                            <p><strong>Total Vehicles:</strong> ${result.total_vehicles}</p>
                            ${result.vehicles_with_urls ? `<p><strong>Vehicles with URLs:</strong> ${result.vehicles_with_urls}</p>` : ''}
                            ${result.vehicles_without_urls ? `<p><strong>Vehicles without URLs:</strong> ${result.vehicles_without_urls}</p>` : ''}
                        </div>
                    `;
                }
                
                // Store result and show proceed button
                this.currentQRResult = result;
                
                // Show proceed button or create one if it doesn't exist
                if (qrProceedBtn) {
                    qrProceedBtn.style.display = 'inline-flex';
                } else {
                    // Create the Enter Order Number button if it doesn't exist
                    const actionsContainer = document.querySelector('.wizard-actions') || 
                                           document.querySelector('.qr-actions') ||
                                           generateQRBtn.parentElement;
                    
                    if (actionsContainer) {
                        const newButton = document.createElement('button');
                        newButton.className = 'btn-wizard primary';
                        newButton.id = 'qrProceedBtn';
                        newButton.onclick = () => this.proceedToOrderNumber();
                        newButton.innerHTML = '<i class="fas fa-hashtag"></i> Enter Order Number';
                        actionsContainer.appendChild(newButton);
                        console.log('✅ Created "Enter Order Number" button');
                    }
                }
                
            } else {
                // Normal QR generation flow
                // Update progress to 100%
                const progressFill = document.getElementById('qrProgressFill');
                const progressCount = document.getElementById('qrProgressCount');
                if (progressFill) progressFill.style.width = '100%';
                if (progressCount) progressCount.textContent = `${result.qr_codes_generated}/${result.qr_codes_generated}`;
                
                // Hide progress and show results
                setTimeout(() => {
                    qrProgress.style.display = 'none';
                    qrResults.style.display = 'block';
                    
                    // Update result stats
                    const qrGeneratedCount = document.getElementById('qrGeneratedCount');
                    const qrFolderName = document.getElementById('qrFolderName');
                    
                    if (qrGeneratedCount) qrGeneratedCount.textContent = result.qr_codes_generated;
                    if (qrFolderName) qrFolderName.textContent = result.qr_folder_name;
                    
                    // Render QR file list
                    this.renderQRFileList(result.qr_files);
                    
                    // Store QR result for later use
                    this.currentQRResult = result;
                    
                    // Show proceed button or create one if it doesn't exist
                    if (qrProceedBtn) {
                        qrProceedBtn.style.display = 'inline-flex';
                    } else {
                        // Create the Enter Order Number button if it doesn't exist
                        const actionsContainer = document.querySelector('.wizard-actions') || 
                                               document.querySelector('.qr-actions') ||
                                               generateQRBtn.parentElement;
                        
                        if (actionsContainer) {
                            const newButton = document.createElement('button');
                            newButton.className = 'btn-wizard primary';
                            newButton.id = 'qrProceedBtn';
                            newButton.onclick = () => this.proceedToOrderNumber();
                            newButton.innerHTML = '<i class="fas fa-hashtag"></i> Enter Order Number';
                            actionsContainer.appendChild(newButton);
                            console.log('✅ Created "Enter Order Number" button');
                        }
                    }
                    
                }, 1000);
            }
            
        } catch (error) {
            console.error('[QR GENERATION] Error:', error);
            alert(`QR Generation Error: ${error.message}`);
            
            // Reset generate button and CREATE ORDER NUMBER BUTTON
            generateQRBtn.disabled = false;
            generateQRBtn.innerHTML = '<i class="fas fa-qrcode"></i> Generate QR Codes';
            
            // FORCE CREATE THE ORDER NUMBER BUTTON - BYPASS ALL TEMPLATE ISSUES
            const container = generateQRBtn.parentElement;
            const orderBtn = document.createElement('button');
            orderBtn.className = 'btn-wizard primary';
            orderBtn.style.marginLeft = '20px';
            orderBtn.onclick = () => this.proceedToOrderNumber();
            orderBtn.innerHTML = '<i class="fas fa-hashtag"></i> Enter Order Number';
            container.appendChild(orderBtn);
            console.log('🚨 EMERGENCY: Created Order Number button after error');
        }
    }
    
    renderQRFileList(qrFiles) {
        const qrFileList = document.getElementById('qrFileList');
        if (!qrFileList || !qrFiles || qrFiles.length === 0) return;
        
        // Clear and populate with a cleaner layout
        qrFileList.innerHTML = '';
        
        const fileListContainer = document.createElement('div');
        fileListContainer.className = 'qr-file-grid';
        fileListContainer.style.padding = 'var(--spacing-md)';
        
        // Show first few files as preview, with option to show all
        const previewCount = Math.min(3, qrFiles.length);
        const filesToShow = qrFiles.slice(0, previewCount);
        
        filesToShow.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'qr-file-item';
            fileItem.innerHTML = `
                <div class="qr-file-header">
                    <span class="file-number">#${index + 1}</span>
                    <strong class="filename">${file.filename}</strong>
                </div>
                <div class="qr-vehicle-info">
                    <span class="vin"><i class="fas fa-barcode"></i> ${file.vin}</span>
                    <span class="vehicle"><i class="fas fa-car"></i> ${file.vehicle_info}</span>
                    ${file.stock ? `<span class="stock"><i class="fas fa-tag"></i> Stock: ${file.stock}</span>` : ''}
                </div>
                <div class="qr-file-url">
                    <i class="fas fa-link"></i>
                    <span class="url-text">${this.truncateUrl(file.url)}</span>
                </div>
            `;
            fileListContainer.appendChild(fileItem);
        });
        
        // If there are more files, show a summary
        if (qrFiles.length > previewCount) {
            const moreInfo = document.createElement('div');
            moreInfo.className = 'qr-more-info';
            moreInfo.innerHTML = `
                <i class="fas fa-ellipsis-h"></i>
                <span>+ ${qrFiles.length - previewCount} more QR codes generated</span>
            `;
            fileListContainer.appendChild(moreInfo);
        }
        
        qrFileList.appendChild(fileListContainer);
    }
    
    truncateUrl(url) {
        if (url.length <= 50) return url;
        return url.substring(0, 25) + '...' + url.substring(url.length - 20);
    }
    
    backToCsvReview() {
        this.updateProgress('review');
        this.showStep('reviewStep');
    }
    
    approveOutput() {
        // Navigate to QR generation step after CSV review
        this.proceedToQRGeneration();
    }
    
    showDataEditor() {
        // DISABLED: This function creates the "Continue to Data Editor" button
        // User explicitly requested this workflow be removed
        console.log('❌ showDataEditor() DISABLED - redirecting to QR generation');
        
        // Redirect to proper workflow: QR Generation → Order Number → VIN Log
        this.proceedToQRGeneration();
        return;
        
        // OLD CODE COMMENTED OUT:
        // Initialize data editor
        // this.currentEditingData = null;
        // this.dataEditorChanges = new Map();
        // this.currentEditingFile = null;
        // 
        // Show the data editor step
        // this.showStep('dataEditorStep');
        // 
        // Load CSV data for editing
        // this.loadCSVDataForEditing();
    }
    
    async loadCSVDataForEditing() {
        try {
            // Get the current dealership and CSV file information
            const currentOrder = this.processedOrders[this.processedOrders.length - 1];
            if (!currentOrder || !currentOrder.result || !currentOrder.result.download_csv) {
                this.showError('No CSV file available for editing');
                return;
            }
            
            this.currentEditingFile = currentOrder.result.download_csv;
            
            // Extract filename from download_csv path
            const csvFilename = this.extractFilenameFromPath(this.currentEditingFile);
            
            // Fetch the CSV data from the server
            const response = await fetch(`/api/csv/get-data/${csvFilename}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const csvData = await response.json();
            this.currentEditingData = csvData;
            
            // Populate the data editor table
            this.populateDataEditor(csvData);
            
        } catch (error) {
            console.error('Error loading CSV data:', error);
            this.showError('Failed to load CSV data for editing: ' + error.message);
        }
    }
    
    populateDataEditor(csvData) {
        const table = document.getElementById('dataEditorTable');
        const headers = document.getElementById('dataEditorHeaders');
        const body = document.getElementById('dataEditorBody');
        
        if (!csvData || !csvData.headers || !csvData.rows) {
            this.showError('Invalid CSV data format');
            return;
        }
        
        // Clear existing content
        headers.innerHTML = '';
        body.innerHTML = '';
        
        // Create headers
        csvData.headers.forEach((header, index) => {
            const th = document.createElement('th');
            th.textContent = header;
            th.setAttribute('data-column', index);
            headers.appendChild(th);
        });
        
        // Add actions column
        const actionsHeader = document.createElement('th');
        actionsHeader.textContent = 'Actions';
        actionsHeader.style.width = '80px';
        headers.appendChild(actionsHeader);
        
        // Create data rows
        csvData.rows.forEach((row, rowIndex) => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-row', rowIndex);
            
            // Create data cells
            row.forEach((cellValue, colIndex) => {
                const td = document.createElement('td');
                td.classList.add('editable-cell');
                td.textContent = cellValue;
                td.setAttribute('data-row', rowIndex);
                td.setAttribute('data-col', colIndex);
                td.addEventListener('click', () => this.editCell(rowIndex, colIndex));
                tr.appendChild(td);
            });
            
            // Create actions cell
            const actionsTd = document.createElement('td');
            actionsTd.innerHTML = `
                <div class="row-actions">
                    <button class="row-btn duplicate" onclick="wizard.duplicateRow(${rowIndex})" title="Duplicate">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="row-btn delete" onclick="wizard.deleteRow(${rowIndex})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            tr.appendChild(actionsTd);
            
            body.appendChild(tr);
        });
        
        // Update stats
        this.updateEditorStats();
        
        // Run validation
        this.validateData();
    }
    
    editCell(rowIndex, colIndex) {
        // Get the cell element
        const cell = document.querySelector(`[data-row="${rowIndex}"][data-col="${colIndex}"]`);
        if (!cell || cell.classList.contains('editing')) return;
        
        // Store original value
        const originalValue = cell.textContent;
        
        // Create input element
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'cell-input';
        input.value = originalValue;
        
        // Replace cell content with input
        cell.innerHTML = '';
        cell.appendChild(input);
        cell.classList.add('editing');
        input.focus();
        input.select();
        
        // Handle save on enter or blur
        const saveEdit = () => {
            const newValue = input.value.trim();
            
            // Remove input and restore cell
            cell.innerHTML = newValue;
            cell.classList.remove('editing');
            
            // Track changes
            if (newValue !== originalValue) {
                const changeKey = `${rowIndex}-${colIndex}`;
                this.dataEditorChanges.set(changeKey, {
                    row: rowIndex,
                    col: colIndex,
                    oldValue: originalValue,
                    newValue: newValue
                });
                
                // Update data
                this.currentEditingData.rows[rowIndex][colIndex] = newValue;
                
                // Mark cell as changed
                cell.classList.add('cell-changed');
                
                // Update stats
                this.updateEditorStats();
                
                // Re-validate
                this.validateData();
            }
        };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                saveEdit();
            } else if (e.key === 'Escape') {
                // Cancel editing
                cell.innerHTML = originalValue;
                cell.classList.remove('editing');
            }
        });
    }
    
    addNewRow() {
        if (!this.currentEditingData) return;
        
        // Create new row with empty values
        const newRow = new Array(this.currentEditingData.headers.length).fill('');
        this.currentEditingData.rows.push(newRow);
        
        // Re-populate the table
        this.populateDataEditor(this.currentEditingData);
        
        // Scroll to bottom
        const tableContainer = document.querySelector('.data-table-container');
        tableContainer.scrollTop = tableContainer.scrollHeight;
    }
    
    duplicateRow(rowIndex) {
        if (!this.currentEditingData || rowIndex >= this.currentEditingData.rows.length) return;
        
        // Clone the row
        const originalRow = this.currentEditingData.rows[rowIndex];
        const duplicatedRow = [...originalRow];
        
        // Insert after the original row
        this.currentEditingData.rows.splice(rowIndex + 1, 0, duplicatedRow);
        
        // Re-populate the table
        this.populateDataEditor(this.currentEditingData);
    }
    
    deleteRow(rowIndex) {
        if (!this.currentEditingData || rowIndex >= this.currentEditingData.rows.length) return;
        
        if (confirm('Are you sure you want to delete this row?')) {
            // Remove the row
            this.currentEditingData.rows.splice(rowIndex, 1);
            
            // Remove any changes tracking for this row
            for (let [key, change] of this.dataEditorChanges) {
                if (change.row === rowIndex) {
                    this.dataEditorChanges.delete(key);
                } else if (change.row > rowIndex) {
                    // Update row indices for rows that moved up
                    change.row -= 1;
                    const newKey = `${change.row}-${change.col}`;
                    this.dataEditorChanges.delete(key);
                    this.dataEditorChanges.set(newKey, change);
                }
            }
            
            // Re-populate the table
            this.populateDataEditor(this.currentEditingData);
        }
    }
    
    resetData() {
        if (confirm('Are you sure you want to reset all changes? This cannot be undone.')) {
            // Clear changes
            this.dataEditorChanges.clear();
            
            // Reload original data
            this.loadCSVDataForEditing();
        }
    }
    
    searchData() {
        const searchTerm = document.getElementById('editorSearchInput').value.toLowerCase();
        const rows = document.querySelectorAll('#dataEditorBody tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let found = false;
            
            for (let cell of cells) {
                if (cell.textContent.toLowerCase().includes(searchTerm)) {
                    found = true;
                    break;
                }
            }
            
            row.style.display = found ? '' : 'none';
        });
    }
    
    updateEditorStats() {
        // Update vehicle count
        const vehicleCount = this.currentEditingData ? this.currentEditingData.rows.length : 0;
        const vehicleElement = document.getElementById('editorVehicleCount');
        if (vehicleElement) vehicleElement.textContent = vehicleCount;
        
        // Update changes count
        const changesElement = document.getElementById('editorChangeCount');
        if (changesElement) changesElement.textContent = this.dataEditorChanges.size;
    }
    
    validateData() {
        const validationResults = document.getElementById('validationResults');
        if (!validationResults || !this.currentEditingData) return;
        
        const errors = [];
        const warnings = [];
        const successes = [];
        
        // Validate each row
        this.currentEditingData.rows.forEach((row, rowIndex) => {
            // Check for required fields (VIN, STOCK)
            const vin = row[4]; // VIN column
            const stock = row[3]; // STOCK column
            
            if (!vin || vin.trim() === '') {
                errors.push(`Row ${rowIndex + 1}: Missing VIN`);
            } else if (vin.length !== 17) {
                errors.push(`Row ${rowIndex + 1}: Invalid VIN length (${vin.length} chars)`);
            }
            
            if (!stock || stock.trim() === '') {
                errors.push(`Row ${rowIndex + 1}: Missing Stock Number`);
            }
            
            // Check for duplicates
            const duplicateVins = this.currentEditingData.rows.filter(r => r[4] === vin).length;
            if (duplicateVins > 1) {
                warnings.push(`Row ${rowIndex + 1}: Duplicate VIN found`);
            }
        });
        
        if (errors.length === 0 && warnings.length === 0) {
            successes.push('All data validation checks passed');
        }
        
        // Update error count
        const errorElement = document.getElementById('editorErrorCount');
        if (errorElement) errorElement.textContent = errors.length;
        
        // Display validation results
        validationResults.innerHTML = '';
        
        [...errors, ...warnings, ...successes].forEach(message => {
            const item = document.createElement('div');
            item.className = 'validation-item';
            
            if (errors.includes(message)) {
                item.classList.add('error');
                item.innerHTML = `<i class="fas fa-exclamation-circle validation-icon"></i><span>${message}</span>`;
            } else if (warnings.includes(message)) {
                item.classList.add('warning');
                item.innerHTML = `<i class="fas fa-exclamation-triangle validation-icon"></i><span>${message}</span>`;
            } else {
                item.classList.add('success');
                item.innerHTML = `<i class="fas fa-check-circle validation-icon"></i><span>${message}</span>`;
            }
            
            validationResults.appendChild(item);
        });
    }
    
    async saveAndRegenerate() {
        if (!this.currentEditingData || !this.currentEditingFile) {
            this.showError('No data to save');
            return;
        }
        
        try {
            // Save the edited data back to server
            const response = await fetch('/api/csv/save-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.extractFilenameFromPath(this.currentEditingFile),
                    data: this.currentEditingData
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Data saved successfully');
                
                // Regenerate QR codes if needed
                if (this.dataEditorChanges.size > 0) {
                    await this.regenerateQRCodes();
                }
                
                // Clear changes tracking
                this.dataEditorChanges.clear();
                this.updateEditorStats();
            } else {
                throw new Error(result.error || 'Save failed');
            }
            
        } catch (error) {
            console.error('Error saving data:', error);
            this.showError('Failed to save data: ' + error.message);
        }
    }
    
    async regenerateQRCodes() {
        try {
            const response = await fetch('/api/qr/regenerate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.extractFilenameFromPath(this.currentEditingFile)
                })
            });
            
            if (response.ok) {
                this.showSuccess('QR codes regenerated successfully');
            }
        } catch (error) {
            console.error('Error regenerating QR codes:', error);
            this.showWarning('Data saved but QR regeneration failed');
        }
    }
    
    finalizeCorrectedData() {
        // Validate data one more time
        this.validateData();
        
        const errorCount = document.getElementById('editorErrorCount');
        const errors = parseInt(errorCount.textContent) || 0;
        
        if (errors > 0) {
            if (!confirm('There are still validation errors. Continue anyway?')) {
                return;
            }
        }
        
        // Check if we need order number for current dealership
        if (this.processedOrders.length > 0) {
            const lastOrder = this.processedOrders[this.processedOrders.length - 1];
            this.showOrderNumberStep(lastOrder.dealership, lastOrder.result);
        } else {
            // Go back to review step
            this.backToReview();
            
            // Show success message
            this.showSuccess('Data changes applied successfully');
        }
    }
    
    backToReview() {
        this.showStep('reviewStep');
    }
    
    showQRUrlEditor() {
        // Initialize QR URL data
        this.qrUrlData = [];
        
        if (!this.currentEditingData || !this.currentEditingData.rows) {
            this.showError('No vehicle data available for QR editing');
            return;
        }
        
        // Create QR URL data from current vehicle data
        this.currentEditingData.rows.forEach((row, index) => {
            const stock = row[3] || ''; // STOCK column
            const year = row[0] || ''; // YEARMAKE column  
            const make = row[0] ? row[0].split(' ')[1] || '' : ''; // Extract make from YEARMAKE
            const model = row[1] || ''; // MODEL column
            const vin = row[4] || ''; // VIN column
            
            this.qrUrlData.push({
                index: index,
                stock: stock,
                year: year.split(' ')[0] || '',
                make: make,
                model: model,
                vin: vin,
                url: '' // User will enter this
            });
        });
        
        // Show the modal
        document.getElementById('qrUrlEditorModal').style.display = 'flex';
        
        // Populate the URL list
        this.populateUrlList();
    }
    
    populateUrlList() {
        const urlListBody = document.getElementById('urlListBody');
        const urlsCompleteCount = document.getElementById('urlsCompleteCount');
        const urlsTotalCount = document.getElementById('urlsTotalCount');
        
        if (!urlListBody) return;
        
        urlListBody.innerHTML = '';
        
        this.qrUrlData.forEach((vehicle, index) => {
            const row = document.createElement('div');
            row.className = 'url-row';
            
            row.innerHTML = `
                <div class="url-cell">
                    <strong>${vehicle.stock}</strong>
                </div>
                <div class="url-cell">
                    <div class="vehicle-info">
                        ${vehicle.year} ${vehicle.make}<br>
                        <small>${vehicle.model}</small>
                    </div>
                </div>
                <div class="url-cell">
                    <input type="url" 
                           class="url-input" 
                           placeholder="https://dealership.com/vehicle/${vehicle.stock}"
                           value="${vehicle.url}"
                           data-index="${index}"
                           onchange="wizard.updateVehicleUrl(${index}, this.value)">
                </div>
                <div class="url-cell url-preview">
                    <button class="qr-preview-btn" 
                            onclick="wizard.previewQR(${index})"
                            ${vehicle.url ? '' : 'disabled'}>
                        Preview
                    </button>
                </div>
            `;
            
            urlListBody.appendChild(row);
        });
        
        // Update stats
        const completeUrls = this.qrUrlData.filter(v => v.url && v.url.trim() !== '').length;
        if (urlsCompleteCount) urlsCompleteCount.textContent = completeUrls;
        if (urlsTotalCount) urlsTotalCount.textContent = this.qrUrlData.length;
    }
    
    updateVehicleUrl(index, url) {
        if (this.qrUrlData[index]) {
            this.qrUrlData[index].url = url.trim();
            
            // Update the preview button state
            const previewBtn = document.querySelector(`[onclick="wizard.previewQR(${index})"]`);
            if (previewBtn) {
                previewBtn.disabled = !url.trim();
            }
            
            // Update stats
            this.updateUrlStats();
        }
    }
    
    updateUrlStats() {
        const urlsCompleteCount = document.getElementById('urlsCompleteCount');
        const completeUrls = this.qrUrlData.filter(v => v.url && v.url.trim() !== '').length;
        if (urlsCompleteCount) urlsCompleteCount.textContent = completeUrls;
    }
    
    applyBulkUrlTemplate() {
        const templateInput = document.getElementById('bulkUrlTemplate');
        const template = templateInput.value.trim();
        
        if (!template) {
            this.showError('Please enter a URL template');
            return;
        }
        
        // Apply template to all vehicles
        this.qrUrlData.forEach(vehicle => {
            let url = template;
            url = url.replace('{STOCK}', vehicle.stock);
            url = url.replace('{VIN}', vehicle.vin);
            url = url.replace('{YEAR}', vehicle.year);
            url = url.replace('{MAKE}', vehicle.make);
            url = url.replace('{MODEL}', vehicle.model);
            
            vehicle.url = url;
        });
        
        // Re-populate the list
        this.populateUrlList();
        
        this.showSuccess('URL template applied to all vehicles');
    }
    
    previewQR(index) {
        const vehicle = this.qrUrlData[index];
        if (!vehicle || !vehicle.url) return;
        
        // Create a simple QR preview (you could enhance this with actual QR generation)
        const previewWindow = window.open('', '_blank', 'width=300,height=350');
        previewWindow.document.write(`
            <html>
                <head><title>QR Preview - ${vehicle.stock}</title></head>
                <body style="text-align: center; padding: 20px; font-family: Arial;">
                    <h3>QR Code Preview</h3>
                    <p><strong>Stock:</strong> ${vehicle.stock}</p>
                    <p><strong>Vehicle:</strong> ${vehicle.year} ${vehicle.make} ${vehicle.model}</p>
                    <p><strong>URL:</strong><br><small>${vehicle.url}</small></p>
                    <div style="margin: 20px; padding: 20px; border: 2px dashed #ccc;">
                        <p>QR Code will contain:</p>
                        <code style="word-break: break-all;">${vehicle.url}</code>
                    </div>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        `);
    }
    
    async regenerateQRWithUrls() {
        // Validate that all vehicles have URLs
        const missingUrls = this.qrUrlData.filter(v => !v.url || v.url.trim() === '');
        
        if (missingUrls.length > 0) {
            if (!confirm(`${missingUrls.length} vehicles are missing URLs. Continue anyway?`)) {
                return;
            }
        }
        
        try {
            // Send the URL data to the server for QR generation
            const response = await fetch('/api/qr/regenerate-with-urls', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.currentEditingFile,
                    vehicle_urls: this.qrUrlData
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`Generated ${result.qr_codes_generated} QR codes with custom URLs`);
                this.closeQRUrlEditor();
            } else {
                throw new Error(result.error || 'QR generation failed');
            }
            
        } catch (error) {
            console.error('Error regenerating QR codes:', error);
            this.showError('Failed to regenerate QR codes: ' + error.message);
        }
    }
    
    closeQRUrlEditor() {
        document.getElementById('qrUrlEditorModal').style.display = 'none';
        this.qrUrlData = [];
    }
    
    backToVINEntry() {
        this.updateProgress('list');
        this.showStep('listStep');
    }
    
    skipCurrentDealership() {
        this.currentListIndex++;
        this.showCurrentListOrder();
    }
    
    completeProcessing() {
        this.updateProgress('complete');
        this.showStep('completeStep');
        this.renderCompletionStats();
    }
    
    renderCompletionStats() {
        const statsContainer = document.getElementById('completionStats');
        if (!statsContainer) return;
        
        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-number">${this.processingResults.totalDealerships}</div>
                <div class="stat-label">Total Dealerships</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.processingResults.caoProcessed}</div>
                <div class="stat-label">CAO Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.processingResults.listProcessed}</div>
                <div class="stat-label">List Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.processingResults.totalVehicles}</div>
                <div class="stat-label">Total Vehicles</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.processingResults.filesGenerated}</div>
                <div class="stat-label">Files Generated</div>
            </div>
            <div class="stat-card ${this.processingResults.errors.length > 0 ? 'error' : 'success'}">
                <div class="stat-number">${this.processingResults.errors.length}</div>
                <div class="stat-label">Errors</div>
            </div>
        `;
    }
    
    downloadAllFiles() {
        // Download all generated files from processed orders
        if (this.processedOrders.length === 0) {
            this.showWarning('No files to download');
            return;
        }
        
        this.showSuccess('Preparing downloads...');
        
        // Iterate through all processed orders and download their files
        this.processedOrders.forEach((order, index) => {
            if (order.result && order.result.success) {
                // Download CSV file
                if (order.result.download_csv) {
                    setTimeout(() => {
                        const csvLink = document.createElement('a');
                        csvLink.href = order.result.download_csv;
                        csvLink.download = `${order.dealership.replace(/\s+/g, '_')}_order.csv`;
                        document.body.appendChild(csvLink);
                        csvLink.click();
                        document.body.removeChild(csvLink);
                    }, index * 500); // Stagger downloads
                }
                
                // Download QR codes (if we have a download endpoint for the folder)
                if (order.result.qr_folder) {
                    setTimeout(() => {
                        // Create a request to zip and download QR folder
                        fetch('/api/download/qr-folder', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                folder_path: order.result.qr_folder,
                                dealership: order.dealership
                            })
                        })
                        .then(response => response.blob())
                        .then(blob => {
                            const qrLink = document.createElement('a');
                            qrLink.href = URL.createObjectURL(blob);
                            qrLink.download = `${order.dealership.replace(/\s+/g, '_')}_qr_codes.zip`;
                            document.body.appendChild(qrLink);
                            qrLink.click();
                            document.body.removeChild(qrLink);
                        })
                        .catch(error => {
                            console.error('Error downloading QR codes:', error);
                        });
                    }, (index * 500) + 250); // Stagger QR downloads
                }
            }
        });
        
        this.showSuccess(`Downloading files for ${this.processedOrders.length} dealerships...`);
    }
    
    downloadFile(filePath) {
        // Download individual file
        const link = document.createElement('a');
        link.href = filePath;
        link.download = filePath.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    downloadCSV(filename) {
        // Download CSV file using the Flask route
        const link = document.createElement('a');
        link.href = `/download_csv/${filename}`;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    previewCSV(filename) {
        // Preview CSV file in a new window
        const previewWindow = window.open(`/download_csv/${filename}`, '_blank', 'width=800,height=600');
        previewWindow.focus();
    }
    
    downloadQRFolder(folderPath) {
        // Create a ZIP download of QR codes (would need backend support)
        // For now, show a message about individual QR downloads
        this.showMessage('QR codes are available in the folder: ' + folderPath + '. Individual QR files can be accessed through the file system.', 'info');
    }
    
    previewQRFolder(folderPath) {
        // Preview QR codes in a gallery view
        const previewWindow = window.open('', '_blank', 'width=900,height=700');
        previewWindow.document.write(`
            <html>
                <head>
                    <title>QR Code Preview</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .qr-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
                        .qr-item { text-align: center; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                        .qr-img { max-width: 150px; max-height: 150px; }
                        .qr-info { margin-top: 10px; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <h2>QR Code Preview</h2>
                    <p>QR codes generated in: <code>${folderPath}</code></p>
                    <div class="qr-gallery">
                        <div class="qr-item">
                            <div style="width: 150px; height: 150px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                QR Code Preview<br><small>View files in folder for actual QR codes</small>
                            </div>
                            <div class="qr-info">Individual QR files available in the specified folder</div>
                        </div>
                    </div>
                    <button onclick="window.close()" style="margin-top: 20px; padding: 10px 20px;">Close</button>
                </body>
            </html>
        `);
    }
    
    extractFilenameFromPath(filePath) {
        // Extract filename from download_csv path (removes /download_csv/ prefix)
        if (!filePath) return '';
        return filePath.replace('/download_csv/', '').replace('download_csv/', '');
    }
    
    updateProgress(stepName) {
        // Update progress indicators
        document.querySelectorAll('.progress-step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        const stepIndex = this.steps.indexOf(stepName);
        for (let i = 0; i <= stepIndex; i++) {
            const stepEl = document.getElementById(`step-${this.steps[i]}`);
            if (stepEl) {
                if (i === stepIndex) {
                    stepEl.classList.add('active');
                } else {
                    stepEl.classList.add('completed');
                }
            }
        }
    }
    
    showStep(stepId) {
        // Hide all steps
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show target step
        const targetStep = document.getElementById(stepId);
        if (targetStep) {
            targetStep.classList.add('active');
        }
    }
    
    // ========== ORDER NUMBER STEP METHODS ==========
    
    showOrderNumberStep(dealershipName, orderResult) {
        console.log('🎯 SHOWING ORDER NUMBER STEP for:', dealershipName);
        
        // Store current order info
        this.currentOrderDealership = dealershipName;
        this.currentOrderVins = orderResult.processed_vins || [];
        
        // Debug what QR result data we have
        console.log('🔍 DEBUG: QR Result available:', !!this.currentQRResult);
        if (this.currentQRResult) {
            console.log('🔍 DEBUG: QR Result keys:', Object.keys(this.currentQRResult));
            console.log('🔍 DEBUG: CSV file in QR result:', this.currentQRResult.csv_file);
            console.log('🔍 DEBUG: qr_codes_generated value:', this.currentQRResult.qr_codes_generated);
            console.log('🔍 DEBUG: vehicles_processed value:', this.currentQRResult.vehicles_processed);
            console.log('🔍 DEBUG: files_generated value:', this.currentQRResult.files_generated);
        }
        
        // If no VINs in orderResult, get them from the QR generation result
        if (this.currentOrderVins.length === 0 && this.currentQRResult) {
            // The QR result should contain the original CSV data with VINs
            if (this.currentQRResult.csv_data && Array.isArray(this.currentQRResult.csv_data)) {
                this.currentOrderVins = this.currentQRResult.csv_data.map(row => row.VIN || row.vin).filter(vin => vin);
                console.log(`📊 Extracted ${this.currentOrderVins.length} VINs from CSV data for order processing`);
            }
            // Alternative: extract from vehicle data if available
            else if (this.currentQRResult.vehicles && Array.isArray(this.currentQRResult.vehicles)) {
                this.currentOrderVins = this.currentQRResult.vehicles.map(v => v.VIN || v.vin).filter(vin => vin);
                console.log(`📊 Extracted ${this.currentOrderVins.length} VINs from vehicle data for order processing`);
            }
            // Last resort: read from the CSV file that was processed
            else if (this.currentQRResult.csv_file) {
                console.log(`📊 Will extract VINs from CSV file: ${this.currentQRResult.csv_file}`);
                // Set a flag that we need to extract VINs from CSV file
                this.currentOrderVins = ['EXTRACT_FROM_CSV'];
                this.csvFileForVinExtraction = this.currentQRResult.csv_file;
            }
        }
        
        // Calculate display values for debugging
        const vehiclesProcessed = this.currentQRResult?.qr_codes_generated || this.currentQRResult?.vehicles_processed || orderResult?.vehicles_processed || 0;
        const qrCodesGenerated = this.currentQRResult?.qr_codes_generated || this.currentQRResult?.files_generated || (this.currentQRResult?.qr_files?.length) || orderResult?.qr_codes_generated || 0;
        
        console.log('🔍 DEBUG: Display values being used:');
        console.log('   - Vehicles Processed:', vehiclesProcessed);
        console.log('   - QR Codes Generated:', qrCodesGenerated);
        
        // FIND CONTAINER AND CREATE ORDER NUMBER HTML
        let container = document.getElementById('wizardContent') || 
                       document.getElementById('app') || 
                       document.querySelector('.wizard-container') ||
                       document.body;
        
        // CREATE ORDER NUMBER STEP HTML
        container.innerHTML = `
            <div class="wizard-step active" id="orderNumberStep">
                <div class="step-header">
                    <h2 class="step-title">📝 Enter Order Number</h2>
                    <p class="step-description">Apply order number to processed vehicles for ${dealershipName}</p>
                </div>
                
                <div class="order-info-card">
                    <div class="info-row">
                        <strong>Dealership:</strong> ${dealershipName}
                    </div>
                    <div class="info-row">
                        <strong>Vehicles Processed:</strong> ${vehiclesProcessed}
                    </div>
                    <div class="info-row">
                        <strong>QR Codes Generated:</strong> ${qrCodesGenerated}
                    </div>
                    ${this.currentQRResult?.billing_csv_generated ? `
                    <div class="info-row">
                        <strong>Billing CSV Generated:</strong> ✅ Yes
                    </div>` : ''}
                </div>
                
                <div class="order-input-section">
                    <label for="orderNumberInput" class="input-label">Order Number:</label>
                    <input type="text" id="orderNumberInput" class="form-control" 
                           placeholder="Enter order number (e.g., ORD-12345)" 
                           style="margin: 10px 0; padding: 12px; font-size: 16px; width: 100%; border: 2px solid #ddd; border-radius: 8px;">
                    
                    <div class="order-actions">
                        <button class="btn-wizard secondary" onclick="wizard.backToQRGeneration()">
                            <i class="fas fa-arrow-left"></i>
                            Back to QR Generation
                        </button>
                        <button class="btn-wizard primary" onclick="wizard.applyOrderNumber()" id="applyOrderNumberBtn">
                            <i class="fas fa-check"></i>
                            Apply Order Number & Complete
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        console.log('✅ ORDER NUMBER STEP HTML CREATED SUCCESSFULLY');
        
        // Focus on the input field
        setTimeout(() => {
            const input = document.getElementById('orderNumberInput');
            if (input) input.focus();
        }, 100);
    }
    
    showVinPreview() {
        const orderNumberInput = document.getElementById('orderNumberInput');
        const orderNumberPreview = document.getElementById('orderNumberPreview');
        const vinPreviewList = document.getElementById('vinPreviewList');
        
        if (!orderNumberInput?.value.trim()) {
            orderNumberPreview.style.display = 'none';
            return;
        }
        
        // Show VIN preview
        if (this.currentOrderVins.length > 0) {
            vinPreviewList.innerHTML = this.currentOrderVins
                .slice(0, 10) // Show first 10 VINs
                .map(vin => `<div style="padding: 2px 0;">${vin}</div>`)
                .join('');
            
            if (this.currentOrderVins.length > 10) {
                vinPreviewList.innerHTML += `<div style="color: #999; padding: 5px 0; font-style: italic;">... and ${this.currentOrderVins.length - 10} more VINs</div>`;
            }
            
            orderNumberPreview.style.display = 'block';
        } else {
            vinPreviewList.innerHTML = '<div style="color: #999; font-style: italic;">No VINs to update</div>';
            orderNumberPreview.style.display = 'block';
        }
    }
    
    async applyOrderNumber() {
        const orderNumberInput = document.getElementById('orderNumberInput');
        const applyOrderNumberBtn = document.getElementById('applyOrderNumberBtn');
        
        const orderNumber = orderNumberInput?.value.trim();
        if (!orderNumber) {
            this.showMessage('Please enter an order number', 'error');
            return;
        }
        
        // Use QR result data if currentOrderVins is empty
        let vinsToUpdate = this.currentOrderVins;
        
        // Determine actual number of vehicles to be processed
        let actualVehicleCount = this.currentQRResult?.qr_codes_generated || this.currentQRResult?.vehicles_processed || 0;
        
        console.log(`📊 Starting order number application:`);
        console.log(`   - Vehicles to process: ${actualVehicleCount} (from QR generation)`);
        console.log(`   - Current VINs: ${vinsToUpdate.length} (${vinsToUpdate.slice(0, 2).join(', ')}${vinsToUpdate.length > 2 ? '...' : ''})`);
        console.log(`   - CSV file available: ${this.csvFileForVinExtraction || 'none'}`);
        
        if (vinsToUpdate.length === 0 && this.currentQRResult) {
            // Extract VINs from QR result or use the CSV file data  
            vinsToUpdate = this.currentQRResult.qr_files?.map(f => f.vin).filter(vin => vin) || [];
            console.log('📊 Extracted VINs from QR result:', vinsToUpdate.length);
        }
        
        if (!this.currentOrderDealership) {
            this.showMessage('No dealership selected', 'error');
            return;
        }
        
        if (vinsToUpdate.length === 0) {
            // Last attempt: ask backend to extract VINs from CSV file
            if (this.currentQRResult?.csv_file) {
                console.log('📊 Requesting VIN extraction from CSV file:', this.currentQRResult.csv_file);
                // Set flag to tell backend to extract VINs from CSV file
                vinsToUpdate = ['EXTRACT_FROM_CSV'];
            } else {
                console.log('No specific VINs found, creating generic order for dealership');
                vinsToUpdate = ['GENERIC_ORDER'];
            }
        }
        
        // Disable button during processing
        applyOrderNumberBtn.disabled = true;
        applyOrderNumberBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
        
        try {
            const displayCount = vinsToUpdate.includes('EXTRACT_FROM_CSV') ? actualVehicleCount : vinsToUpdate.length;
            console.log('Applying order number:', orderNumber, 'to', displayCount, 'VINs for', this.currentOrderDealership);
            
            // Call backend to apply order number to VIN log
            const response = await fetch('/api/orders/apply-order-number', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership_name: this.currentOrderDealership,
                    order_number: orderNumber,
                    vins: vinsToUpdate,
                    csv_file: this.csvFileForVinExtraction || this.currentQRResult?.csv_file || null,
                    qr_codes_generated: this.currentQRResult?.qr_codes_generated || 0
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to apply order number: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Use backend result first, then fall back to QR generation count, never use currentOrderVins.length for EXTRACT_FROM_CSV case
                const actualCount = result.updated_vins || this.currentQRResult?.qr_codes_generated || this.currentQRResult?.vehicles_processed || 'unknown number of';
                this.showMessage(`Order number ${orderNumber} applied to ${actualCount} VINs`, 'success');
                
                // Continue to next dealership or completion
                this.continueAfterOrderNumber();
            } else {
                throw new Error(result.error || 'Unknown error applying order number');
            }
            
        } catch (error) {
            console.error('Error applying order number:', error);
            this.showMessage('Error applying order number: ' + error.message, 'error');
            
            // Re-enable button
            applyOrderNumberBtn.disabled = false;
            applyOrderNumberBtn.innerHTML = '<i class="fas fa-check"></i> Apply Order Number';
        }
    }
    
    continueAfterOrderNumber() {
        // Clear current order data
        this.currentOrderDealership = null;
        this.currentOrderVins = [];
        
        // Remove the processed order from the array since it's complete
        this.processedOrders.pop();
        
        // Move to next dealership or complete
        this.currentListIndex++;
        
        if (this.currentListIndex < this.listOrders.length) {
            // Show next dealership
            this.updateProgress('list');
            this.showStep('listStep');
            this.showCurrentListOrder();
        } else {
            // All list orders complete
            this.completeProcessing();
        }
    }
    
    backToDataEditor() {
        // DISABLED: Redirect to proper review step instead of data editor
        console.log('❌ backToDataEditor() DISABLED - redirecting to review');
        this.updateProgress('review');
        this.showStep('reviewStep');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'wizard-error';
        errorDiv.innerHTML = `
            <div class="error-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="error-message">${message}</div>
            <button onclick="window.close()">Close Wizard</button>
        `;
        document.body.appendChild(errorDiv);
    }
    
    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `wizard-message wizard-${type}`;
        
        let icon = 'fas fa-info-circle';
        if (type === 'success') icon = 'fas fa-check-circle';
        if (type === 'error') icon = 'fas fa-exclamation-triangle';
        if (type === 'warning') icon = 'fas fa-exclamation-circle';
        
        messageDiv.innerHTML = `
            <div class="message-icon">
                <i class="${icon}"></i>
            </div>
            <div class="message-text">${message}</div>
            <button onclick="this.parentElement.remove()" style="margin-left: 10px; padding: 5px 10px;">Close</button>
        `;
        
        // Auto-remove after 5 seconds for info messages
        if (type === 'info') {
            setTimeout(() => {
                if (messageDiv.parentElement) {
                    messageDiv.remove();
                }
            }, 5000);
        }
        
        document.body.appendChild(messageDiv);
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'wizard-success';
        successDiv.innerHTML = `
            <div class="success-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <div class="success-message">${message}</div>
        `;
        document.body.appendChild(successDiv);
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
    }
    
    showWarning(message) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'wizard-warning';
        warningDiv.innerHTML = `
            <div class="warning-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="warning-message">${message}</div>
        `;
        document.body.appendChild(warningDiv);
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            if (warningDiv.parentNode) {
                warningDiv.parentNode.removeChild(warningDiv);
            }
        }, 4000);
    }
    
    // =============================================================================
    // SPREADSHEET VIEW FUNCTIONALITY
    // =============================================================================
    
    async loadCSVIntoSpreadsheet(result) {
        const spreadsheetContainer = document.getElementById('csvSpreadsheet');
        const placeholder = document.getElementById('csvPlaceholder');
        const vehicleCount = document.getElementById('csvVehicleCount');
        
        if (!result.download_csv) {
            // Show placeholder if no CSV available
            if (spreadsheetContainer) spreadsheetContainer.style.display = 'none';
            if (placeholder) placeholder.style.display = 'block';
            if (vehicleCount) vehicleCount.textContent = '0';
            return;
        }
        
        try {
            // Fetch CSV content
            const response = await fetch(result.download_csv);
            const csvText = await response.text();
            
            // Parse CSV
            const lines = csvText.split('\n').filter(line => line.trim());
            if (lines.length < 2) {
                throw new Error('CSV file appears to be empty or invalid');
            }
            
            // Parse header row
            const headers = this.parseCSVLine(lines[0]);
            
            // Parse data rows
            const rows = [];
            for (let i = 1; i < lines.length; i++) {
                const row = this.parseCSVLine(lines[i]);
                if (row.length > 0) {
                    rows.push(row);
                }
            }
            
            // Store the CSV data
            this.currentCSVData = { headers, rows };
            
            // Render the spreadsheet
            this.renderSpreadsheet(headers, rows);
            
            // Update vehicle count
            if (vehicleCount) vehicleCount.textContent = rows.length.toString();
            
            // Show spreadsheet, hide placeholder
            if (spreadsheetContainer) spreadsheetContainer.style.display = 'table';
            if (placeholder) placeholder.style.display = 'none';
            
        } catch (error) {
            console.error('Error loading CSV:', error);
            this.showError('Failed to load CSV data: ' + error.message);
            
            // Show placeholder on error
            if (spreadsheetContainer) spreadsheetContainer.style.display = 'none';
            if (placeholder) placeholder.style.display = 'block';
            if (vehicleCount) vehicleCount.textContent = '0';
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
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        
        result.push(current.trim());
        return result;
    }
    
    renderSpreadsheet(headers, rows) {
        const thead = document.getElementById('csvTableHead');
        const tbody = document.getElementById('csvTableBody');
        
        if (!thead || !tbody) return;
        
        // Render headers
        thead.innerHTML = `
            <tr>
                <th style="width: 80px;">Actions</th>
                ${headers.map(header => `<th>${this.escapeHtml(header)}</th>`).join('')}
            </tr>
        `;
        
        // Render rows
        tbody.innerHTML = rows.map((row, rowIndex) => {
            return `
                <tr data-row-index="${rowIndex}">
                    <td>
                        <div class="row-actions">
                            <button class="row-edit-btn" onclick="wizard.editRow(${rowIndex})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                        </div>
                    </td>
                    ${row.map((cell, cellIndex) => 
                        `<td data-cell-index="${cellIndex}" title="${this.escapeHtml(cell)}">${this.escapeHtml(cell)}</td>`
                    ).join('')}
                </tr>
            `;
        }).join('');
    }
    
    editRow(rowIndex) {
        const row = document.querySelector(`tr[data-row-index="${rowIndex}"]`);
        if (!row || row.classList.contains('editing')) return;
        
        // Mark as editing
        row.classList.add('editing');
        
        // Store original values
        const originalValues = [];
        const cells = row.querySelectorAll('td[data-cell-index]');
        
        cells.forEach((cell, cellIndex) => {
            const originalValue = this.currentCSVData.rows[rowIndex][cellIndex] || '';
            originalValues.push(originalValue);
            
            cell.innerHTML = `
                <input type="text" class="cell-edit-input" 
                       value="${this.escapeHtml(originalValue)}" 
                       data-original="${this.escapeHtml(originalValue)}">
            `;
        });
        
        // Update action buttons
        const actionsCell = row.querySelector('td:first-child .row-actions');
        actionsCell.innerHTML = `
            <button class="row-save-btn" onclick="wizard.saveRow(${rowIndex})">
                <i class="fas fa-save"></i> Save
            </button>
            <button class="row-cancel-btn" onclick="wizard.cancelEditRow(${rowIndex})">
                <i class="fas fa-times"></i> Cancel
            </button>
        `;
    }
    
    saveRow(rowIndex) {
        const row = document.querySelector(`tr[data-row-index="${rowIndex}"]`);
        if (!row) return;
        
        const cells = row.querySelectorAll('td[data-cell-index]');
        const newValues = [];
        
        // Collect new values
        cells.forEach(cell => {
            const input = cell.querySelector('.cell-edit-input');
            if (input) {
                newValues.push(input.value);
            }
        });
        
        // Update the stored data
        this.currentCSVData.rows[rowIndex] = newValues;
        
        // Exit edit mode
        this.cancelEditRow(rowIndex);
        
        // Re-render the row with new values
        cells.forEach((cell, cellIndex) => {
            const newValue = newValues[cellIndex] || '';
            cell.innerHTML = this.escapeHtml(newValue);
            cell.title = this.escapeHtml(newValue);
        });
        
        this.showSuccess(`Row ${rowIndex + 1} updated successfully`);
    }
    
    cancelEditRow(rowIndex) {
        const row = document.querySelector(`tr[data-row-index="${rowIndex}"]`);
        if (!row) return;
        
        // Remove editing class
        row.classList.remove('editing');
        
        // Restore original values
        const cells = row.querySelectorAll('td[data-cell-index]');
        cells.forEach((cell, cellIndex) => {
            const input = cell.querySelector('.cell-edit-input');
            if (input) {
                const originalValue = input.dataset.original || '';
                cell.innerHTML = this.escapeHtml(originalValue);
                cell.title = this.escapeHtml(originalValue);
            }
        });
        
        // Restore edit button
        const actionsCell = row.querySelector('td:first-child .row-actions');
        actionsCell.innerHTML = `
            <button class="row-edit-btn" onclick="wizard.editRow(${rowIndex})">
                <i class="fas fa-edit"></i> Edit
            </button>
        `;
    }
    
    loadQRCodesIntoGrid(result) {
        const qrGrid = document.getElementById('qrCodeGrid');
        if (!qrGrid) return;
        
        if (result.qr_folder && result.qr_codes_generated > 0) {
            // Create QR code items (placeholder since we can't directly access folder contents)
            const qrCount = result.qr_codes_generated;
            const qrItems = [];
            
            for (let i = 0; i < Math.min(qrCount, 12); i++) { // Show max 12 for preview
                qrItems.push(`
                    <div class="qr-item">
                        <div style="width: 80px; height: 80px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 4px;">
                            <i class="fas fa-qrcode" style="font-size: 2rem; color: #ccc;"></i>
                        </div>
                        <div class="qr-label">QR ${i + 1}</div>
                    </div>
                `);
            }
            
            if (qrCount > 12) {
                qrItems.push(`
                    <div class="qr-item">
                        <div style="width: 80px; height: 80px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 2px dashed #ccc;">
                            <span style="font-size: 0.8rem; color: #666;">+${qrCount - 12} more</span>
                        </div>
                        <div class="qr-label">More codes...</div>
                    </div>
                `);
            }
            
            qrGrid.innerHTML = qrItems.join('');
        } else {
            qrGrid.innerHTML = `
                <div class="qr-item">
                    <div style="width: 80px; height: 80px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; border-radius: 4px;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 1.5rem; color: #ffc107;"></i>
                    </div>
                    <div class="qr-label">No QR codes</div>
                </div>
            `;
        }
    }
    
    downloadCSV() {
        if (this.currentOrderResult && this.currentOrderResult.download_csv) {
            window.open(this.currentOrderResult.download_csv, '_blank');
        } else {
            this.showError('No CSV file available for download');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Wizard initialization is handled in the HTML template to avoid conflicts
// This ensures proper loading order and prevents duplicate declarations