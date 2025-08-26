/**
 * Order Processing Wizard - JavaScript Controller
 * Silver Fox Marketing - Guided Order Processing Interface
 * 
 * Handles wizard-style order processing with step-by-step workflow
 */

class OrderWizard {
    constructor() {
        this.currentStep = 0;
        this.steps = ['initialize', 'cao', 'list', 'review', 'order-number', 'complete'];
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
                vehicle_types: null,  // Use dealership-specific filtering rules from database
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
        
        // Load QR codes into preview grid
        this.loadQRCodesIntoGrid(result);
    }
    
    approveOutput() {
        // Check if we need order number for current dealership
        if (this.processedOrders.length > 0) {
            // Get the last processed order
            const lastOrder = this.processedOrders[this.processedOrders.length - 1];
            this.showOrderNumberStep(lastOrder.dealership, lastOrder.result);
        } else {
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
    }
    
    showDataEditor() {
        // Initialize data editor
        this.currentEditingData = null;
        this.dataEditorChanges = new Map();
        this.currentEditingFile = null;
        
        // Show the data editor step
        this.showStep('dataEditorStep');
        
        // Load CSV data for editing
        this.loadCSVDataForEditing();
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
        
        // Initialize VIN table when showing list step
        if (stepId === 'listStep') {
            console.log('List step is active, initializing VIN table...');
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                this.initializeVinTable();
            }, 100);
        }
        
        // Always ensure VIN table is properly initialized for list step
        if (stepId === 'listStep') {
            setTimeout(() => {
                const vinTableBody = document.getElementById('vinTableBody');
                console.log('Checking VIN table status...');
                console.log('VIN table body element:', vinTableBody);
                console.log('VIN table body children count:', vinTableBody ? vinTableBody.children.length : 'N/A');
                
                if (!vinTableBody) {
                    console.error('VIN table body not found - DOM issue!');
                } else if (vinTableBody.children.length === 0) {
                    console.log('VIN table is empty, forcing initialization...');
                    this.initializeVinTable();
                } else {
                    console.log('VIN table already has content, ensuring focus...');
                    const firstInput = document.getElementById('vin-input-1');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }
            }, 250);
        }
    }
    
    // ========== ORDER NUMBER STEP METHODS ==========
    
    showOrderNumberStep(dealershipName, orderResult) {
        console.log('Showing order number step for:', dealershipName);
        
        // Update progress
        this.updateProgress('order-number');
        this.showStep('orderNumberStep');
        
        // Store current order info
        this.currentOrderDealership = dealershipName;
        this.currentOrderVins = orderResult.processed_vins || [];
        
        // Update UI elements
        const dealershipDisplay = document.getElementById('orderNumberDealershipDisplay');
        const orderDealershipName = document.getElementById('orderDealershipName');
        const vinCountDisplay = document.getElementById('orderVinCount');
        const orderNumberInput = document.getElementById('orderNumberInput');
        const applyOrderNumberBtn = document.getElementById('applyOrderNumberBtn');
        const vinPreviewList = document.getElementById('vinPreviewList');
        
        if (dealershipDisplay) {
            dealershipDisplay.textContent = dealershipName;
        }
        
        if (orderDealershipName) {
            orderDealershipName.textContent = dealershipName;
        }
        
        if (vinCountDisplay) {
            vinCountDisplay.textContent = this.currentOrderVins.length;
        }
        
        // Generate suggested order number
        const currentDate = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const dealershipSlug = dealershipName.toUpperCase().replace(/[^A-Z0-9]/g, '_').replace(/_{2,}/g, '_').replace(/^_|_$/g, '');
        const orderType = orderResult.order_type || 'CAO';
        const suggestedOrderNumber = `${dealershipSlug}_${orderType}_${currentDate}_001`;
        
        if (orderNumberInput) {
            orderNumberInput.value = suggestedOrderNumber;
            orderNumberInput.addEventListener('input', () => {
                const hasValue = orderNumberInput.value.trim().length > 0;
                applyOrderNumberBtn.disabled = !hasValue;
                
                if (hasValue) {
                    this.showVinPreview();
                } else {
                    document.getElementById('orderNumberPreview').style.display = 'none';
                }
            });
            
            // Trigger initial preview
            if (suggestedOrderNumber) {
                this.showVinPreview();
                applyOrderNumberBtn.disabled = false;
            }
        }
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
        
        if (!this.currentOrderDealership || this.currentOrderVins.length === 0) {
            this.showMessage('No order data found to update', 'error');
            return;
        }
        
        // Disable button during processing
        applyOrderNumberBtn.disabled = true;
        applyOrderNumberBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
        
        try {
            console.log('Applying order number:', orderNumber, 'to', this.currentOrderVins.length, 'VINs for', this.currentOrderDealership);
            
            // Call backend to apply order number to VIN log
            const response = await fetch('/api/orders/apply-order-number', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealership_name: this.currentOrderDealership,
                    order_number: orderNumber,
                    vins: this.currentOrderVins
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to apply order number: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showMessage(`Order number ${orderNumber} applied to ${result.updated_vins || this.currentOrderVins.length} VINs`, 'success');
                
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
        this.updateProgress('review');
        this.showStep('dataEditorStep');
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
        const spreadsheetContainer = document.getElementById('csvTable');
        const placeholder = document.getElementById('csvPlaceholder');
        const vehicleCount = document.getElementById('vehicleCount');
        
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
        const table = document.getElementById('csvTable');
        
        if (!table) return;
        
        // Clear existing table content
        table.innerHTML = '';
        
        // Create table header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th style="width: 80px;">Actions</th>
                ${headers.map(header => `<th>${this.escapeHtml(header)}</th>`).join('')}
            </tr>
        `;
        table.appendChild(thead);
        
        // Create table body
        const tbody = document.createElement('tbody');
        tbody.innerHTML = rows.map((row, rowIndex) => {
            return `
                <tr data-row-index="${rowIndex}">
                    <td>
                        <div class="row-actions">
                            <button class="row-edit-btn" onclick="wizard.editRowWithModal(${rowIndex})">
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
        table.appendChild(tbody);
    }
    
    editRowWithModal(rowIndex) {
        if (!this.currentCSVData || !this.currentCSVData.rows[rowIndex]) {
            console.error('No CSV data available for editing');
            return;
        }
        
        const row = this.currentCSVData.rows[rowIndex];
        const headers = this.currentCSVData.headers;
        
        // Convert CSV row data to vehicle object format
        const vehicleData = this.csvRowToVehicleObject(row, headers);
        
        // Store the review data globally for the modal functions
        if (!reviewVehicleData[rowIndex]) {
            reviewVehicleData[rowIndex] = vehicleData;
        }
        
        // Open the modal
        openManualDataModal(rowIndex, vehicleData);
    }
    
    csvRowToVehicleObject(row, headers) {
        const vehicle = {};
        
        // Map CSV columns to vehicle properties
        headers.forEach((header, index) => {
            const value = row[index] || '';
            const headerLower = header.toLowerCase();
            
            // Map headers to standard vehicle properties
            if (headerLower.includes('year')) {
                vehicle.year = value;
            } else if (headerLower.includes('make')) {
                vehicle.make = value;
            } else if (headerLower.includes('model')) {
                vehicle.model = value;
            } else if (headerLower.includes('trim')) {
                vehicle.trim = value;
            } else if (headerLower.includes('stock')) {
                vehicle.stock = value;
            } else if (headerLower.includes('vin')) {
                vehicle.vin = value;
            } else if (headerLower.includes('price')) {
                vehicle.price = value;
            } else if (headerLower.includes('type')) {
                vehicle.type = value;
            } else if (headerLower.includes('color')) {
                vehicle.ext_color = value;
            } else if (headerLower.includes('mileage') || headerLower.includes('miles')) {
                vehicle.mileage = value;
            } else if (headerLower.includes('fuel')) {
                vehicle.fuel_type = value;
            } else if (headerLower.includes('transmission')) {
                vehicle.transmission = value;
            } else if (headerLower.includes('url')) {
                vehicle.vehicle_url = value;
            }
        });
        
        return vehicle;
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
    
    proceedToQRGeneration() {
        // Move to order number step (QR generation will happen in final step)
        if (this.processedOrders.length > 0) {
            const lastOrder = this.processedOrders[this.processedOrders.length - 1];
            this.showOrderNumberStep(lastOrder.dealership, lastOrder.result);
        } else {
            this.showError('No processed orders found');
        }
    }

    downloadCSV() {
        if (this.currentOrderResult && this.currentOrderResult.download_csv) {
            window.open(this.currentOrderResult.download_csv, '_blank');
        } else {
            this.showError('No CSV file available for download');
        }
    }
    
    previousStep() {
        // Navigate to previous step in the wizard
        const currentStepIndex = this.steps.indexOf(this.getCurrentStep());
        if (currentStepIndex > 0) {
            const previousStep = this.steps[currentStepIndex - 1];
            this.updateProgress(previousStep);
            this.showStep(previousStep + 'Step');
        }
    }

    getCurrentStep() {
        // Find current active step
        const activeStep = document.querySelector('.wizard-step.active');
        if (activeStep) {
            const stepId = activeStep.id;
            return stepId.replace('Step', '');
        }
        return 'initialize';
    }

    processListVins() {
        // Get VINs from the table instead of textarea
        const vins = this.getAllVinsFromTable();
        
        if (vins.length === 0) {
            this.showError('Please enter at least one VIN for processing');
            return;
        }

        // Validate all VINs before processing
        const invalidVins = vins.filter(vin => !this.isValidVin(vin));
        if (invalidVins.length > 0) {
            this.showError(`Please correct the following invalid VINs: ${invalidVins.join(', ')}`);
            return;
        }

        // Get current list order
        const currentOrder = this.listOrders[this.currentListIndex];
        if (!currentOrder) {
            this.showError('No current dealership found');
            return;
        }

        // Process the VINs
        this.processListOrder(currentOrder.name, vins)
            .then(result => {
                // Store result and show review
                this.processedOrders.push({
                    dealership: currentOrder.name,
                    type: 'list',
                    vins: vins,
                    result: result
                });

                this.showReviewStep(currentOrder.name, result);
            })
            .catch(error => {
                this.showError('Error processing VINs: ' + error.message);
            });
    }

    generateFinalOutput() {
        const orderNumberInput = document.getElementById('orderNumberInput');
        const orderNumber = orderNumberInput?.value.trim();
        
        if (!orderNumber) {
            this.showError('Please enter an order number');
            return;
        }

        // Apply order number and complete processing
        this.applyOrderNumber()
            .then(() => {
                this.completeProcessing();
            })
            .catch(error => {
                this.showError('Error completing order: ' + error.message);
            });
    }

    viewOrderFolder() {
        // Show information about where files are located
        this.showMessage('Order files are available in the designated output folders. Check the completion summary for specific paths.', 'info');
    }

    startNewOrder() {
        // Reset wizard and redirect to main page
        if (confirm('Start a new order? This will reset the current wizard.')) {
            window.location.href = '/';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // =============================================================================
    // VIN TABLE MANAGEMENT FUNCTIONS
    // =============================================================================

    initializeVinTable() {
        const tableBody = document.getElementById('vinTableBody');
        
        if (!tableBody) {
            console.error('VIN table body not found! Retrying...');
            
            // Retry after a delay if table body not found
            setTimeout(() => {
                this.initializeVinTable();
            }, 300);
            return;
        }

        // Clear existing rows and add initial 5 rows
        tableBody.innerHTML = '';
        
        // Create all rows synchronously first, then attach event listeners
        const rowsToCreate = 5;
        
        for (let i = 0; i < rowsToCreate; i++) {
            const rowNumber = i + 1;
            this.createVinRowElement(rowNumber);
        }
        
        // After all rows are created, attach event listeners with a delay
        setTimeout(() => {
            this.attachAllEventListeners();
            this.updateVinCounts();
            
            // Focus on first input
            const firstInput = document.getElementById('vin-input-1');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    }
    
    createVinRowElement(rowNumber) {
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody) return;

        const row = document.createElement('tr');
        row.className = 'vin-row';
        row.id = `vin-row-${rowNumber}`;

        row.innerHTML = `
            <td class="row-number">${rowNumber}</td>
            <td>
                <input type="text" 
                       class="vin-input" 
                       id="vin-input-${rowNumber}"
                       placeholder="Enter 17-character VIN"
                       maxlength="17"
                       data-row-number="${rowNumber}"
                       autocomplete="off"
                       spellcheck="false">
            </td>
            <td class="vin-status" id="vin-status-${rowNumber}">
                <i class="fas fa-minus-circle" style="color: #9ca3af;"></i>
            </td>
        `;

        tableBody.appendChild(row);
        console.log(`Created VIN row element ${rowNumber}`);
    }
    
    attachAllEventListeners() {
        console.log('Attaching event listeners to all VIN inputs...');
        const inputs = document.querySelectorAll('.vin-input');
        
        inputs.forEach(input => {
            const rowNumber = parseInt(input.getAttribute('data-row-number'));
            if (rowNumber && !input.hasAttribute('data-listeners-attached')) {
                // Use arrow functions to maintain 'this' context
                input.addEventListener('input', (event) => {
                    this.filterVinInput(event, rowNumber);
                    this.validateVin(rowNumber);
                });
                
                input.addEventListener('paste', (event) => {
                    this.handleVinPaste(event, rowNumber);
                });
                
                input.addEventListener('keydown', (event) => {
                    this.handleVinKeydown(event, rowNumber);
                });
                
                input.addEventListener('keypress', (event) => {
                    this.handleVinKeypress(event, rowNumber);
                });
                
                // Mark as having listeners attached to prevent double-binding
                input.setAttribute('data-listeners-attached', 'true');
                console.log(`Event listeners attached for VIN input row ${rowNumber}`);
            }
        });
    }

    addVinRow() {
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody) return;

        const rowNumber = tableBody.rows.length + 1;
        
        // Create the row element
        this.createVinRowElement(rowNumber);
        
        // Attach event listeners for the new row with a small delay
        setTimeout(() => {
            const input = document.getElementById(`vin-input-${rowNumber}`);
            if (input && !input.hasAttribute('data-listeners-attached')) {
                // Use arrow functions to maintain 'this' context
                input.addEventListener('input', (event) => {
                    this.filterVinInput(event, rowNumber);
                    this.validateVin(rowNumber);
                });
                
                input.addEventListener('paste', (event) => {
                    this.handleVinPaste(event, rowNumber);
                });
                
                input.addEventListener('keydown', (event) => {
                    this.handleVinKeydown(event, rowNumber);
                });
                
                input.addEventListener('keypress', (event) => {
                    this.handleVinKeypress(event, rowNumber);
                });
                
                // Mark as having listeners attached
                input.setAttribute('data-listeners-attached', 'true');
                console.log(`Event listeners added for new VIN input row ${rowNumber}`);
            } else if (input) {
                console.log(`Row ${rowNumber} already has event listeners attached`);
            } else {
                console.error(`Failed to find input element for new row ${rowNumber}`);
            }
            
            this.updateVinCounts();
        }, 50);
    }

    removeLastRow() {
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody || tableBody.rows.length <= 1) return;

        tableBody.removeChild(tableBody.lastElementChild);
        this.updateVinCounts();
    }

    validateVin(rowNumber) {
        console.log(`Validating VIN for row ${rowNumber}`);
        
        // Wait a moment for DOM to be ready if called immediately after element creation
        if (!document.getElementById(`vin-input-${rowNumber}`)) {
            console.log(`Element not ready for row ${rowNumber}, scheduling retry...`);
            setTimeout(() => {
                this.validateVin(rowNumber);
            }, 50);
            return;
        }
        
        // Use more robust element selection with multiple fallback strategies
        let input = document.getElementById(`vin-input-${rowNumber}`);
        let status = document.getElementById(`vin-status-${rowNumber}`);
        let row = document.getElementById(`vin-row-${rowNumber}`);
        
        // Additional fallback strategies
        if (!input) {
            input = document.querySelector(`input[data-row-number="${rowNumber}"]`);
            console.log(`Fallback querySelector found input for row ${rowNumber}: ${!!input}`);
        }
        if (!status) {
            status = document.querySelector(`#vin-status-${rowNumber}, .vin-status:nth-child(${rowNumber})`);
        }
        if (!row) {
            row = document.querySelector(`#vin-row-${rowNumber}`);
        }
        
        if (!input || !status || !row) {
            console.error(`Missing elements for row ${rowNumber}:`, {
                input: !!input,
                status: !!status, 
                row: !!row,
                availableInputs: document.querySelectorAll('.vin-input').length,
                targetId: `vin-input-${rowNumber}`
            });
            
            // Final retry attempt
            setTimeout(() => {
                console.log('Final retry attempt for validation...');
                this.validateVinRetry(rowNumber);
            }, 150);
            return;
        }

        const vin = input.value.trim().toUpperCase();
        input.value = vin; // Convert to uppercase
        
        console.log(`Row ${rowNumber} VIN: "${vin}" (length: ${vin.length})`);

        // Remove previous validation classes
        input.classList.remove('valid', 'invalid');
        status.classList.remove('valid', 'invalid');
        row.classList.remove('valid', 'invalid');

        if (vin.length === 0) {
            // Empty VIN
            status.innerHTML = '<i class="fas fa-minus-circle" style="color: #9ca3af;"></i>';
            console.log(`Row ${rowNumber}: Empty VIN`);
        } else {
            const isValid = this.isValidVin(vin);
            console.log(`Row ${rowNumber}: VIN validation result:`, isValid);
            
            if (isValid) {
                // Valid VIN
                input.classList.add('valid');
                status.classList.add('valid');
                row.classList.add('valid');
                status.innerHTML = '<i class="fas fa-check-circle"></i>';
                console.log(`Row ${rowNumber}: VIN marked as VALID`);
            } else {
                // Invalid VIN
                input.classList.add('invalid');
                status.classList.add('invalid');
                row.classList.add('invalid');
                status.innerHTML = '<i class="fas fa-times-circle"></i>';
                console.log(`Row ${rowNumber}: VIN marked as INVALID`);
                
                // Show notification for invalid length
                if (vin.length !== 17) {
                    this.showVinError(rowNumber, `VIN must be exactly 17 characters (currently ${vin.length})`);
                }
            }
        }

        this.updateVinCounts();
    }
    
    validateVinRetry(rowNumber) {
        // Retry validation with fresh element lookup
        const input = document.getElementById(`vin-input-${rowNumber}`);
        if (input) {
            console.log(`Retry validation successful for row ${rowNumber}`);
            this.validateVin(rowNumber);
        } else {
            console.error(`Retry validation failed - still cannot find input for row ${rowNumber}`);
        }
    }

    isValidVin(vin) {
        if (!vin || typeof vin !== 'string') return false;
        
        // Check length
        if (vin.length !== 17) return false;
        
        // Check for invalid characters (VINs don't contain I, O, Q)
        if (/[IOQ]/.test(vin)) return false;
        
        // Check for valid alphanumeric characters only
        if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) return false;
        
        return true;
    }

    showVinError(rowNumber, message) {
        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = 'vin-error-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fef2f2;
            border: 2px solid #dc2626;
            color: #dc2626;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            font-weight: 500;
        `;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <strong>Row ${rowNumber}:</strong><br>
                    ${message}
                </div>
            </div>
        `;

        document.body.appendChild(notification);

        // Remove notification after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    filterVinInput(event, rowNumber) {
        const input = event.target;
        if (!input) return;
        
        let value = input.value;
        
        // Remove invalid characters (I, O, Q, and non-alphanumeric except hyphens temporarily)
        let cleaned = value.replace(/[^A-HJ-NPR-Z0-9]/gi, '');
        
        // Convert to uppercase
        cleaned = cleaned.toUpperCase();
        
        // Limit to 17 characters
        if (cleaned.length > 17) {
            cleaned = cleaned.substring(0, 17);
        }
        
        // Update input value if it was changed
        if (value !== cleaned) {
            input.value = cleaned;
            console.log(`Filtered input for row ${rowNumber}: "${value}" → "${cleaned}"`);
        }
    }
    
    handleVinKeypress(event, rowNumber) {
        const char = String.fromCharCode(event.which || event.keyCode);
        
        // Allow control keys (backspace, delete, etc.)
        if (event.which < 32) return;
        
        // Check if character is valid for VIN
        if (!/[A-HJ-NPR-Z0-9]/i.test(char)) {
            event.preventDefault();
            console.log(`Blocked invalid character "${char}" for row ${rowNumber}`);
            
            // Show error for invalid characters
            if (/[IOQ]/i.test(char)) {
                this.showVinError(rowNumber, `Character "${char.toUpperCase()}" is not allowed in VINs`);
            }
        }
        
        // Check length limit
        const input = event.target;
        if (input && input.value.length >= 17) {
            event.preventDefault();
            console.log(`Blocked character - 17 character limit reached for row ${rowNumber}`);
        }
    }

    handleVinPaste(event, rowNumber) {
        // Get pasted data
        const pasteData = (event.clipboardData || window.clipboardData).getData('text');
        
        if (pasteData) {
            // Clean the pasted data
            let cleaned = pasteData.replace(/[^A-HJ-NPR-Z0-9]/gi, '');
            cleaned = cleaned.toUpperCase();
            cleaned = cleaned.substring(0, 17); // Limit to 17 characters
            
            // Prevent default paste and set cleaned value
            event.preventDefault();
            
            const input = event.target;
            if (input) {
                input.value = cleaned;
                console.log(`Pasted and cleaned VIN for row ${rowNumber}: "${pasteData}" → "${cleaned}"`);
                
                // Validate after paste
                setTimeout(() => {
                    this.validateVin(rowNumber);
                }, 10);
            }
        }
    }

    handleVinKeydown(event, rowNumber) {
        // Handle Enter key to create new row and jump to it
        if (event.key === 'Enter') {
            event.preventDefault();
            
            const input = document.getElementById(`vin-input-${rowNumber}`);
            if (!input) {
                console.error(`Cannot find input for row ${rowNumber}`);
                return;
            }
            
            const vin = input.value.trim().toUpperCase();
            
            console.log(`Enter key pressed on row ${rowNumber}, VIN: "${vin}" (length: ${vin.length})`);
            
            // Only create new row if current VIN is valid or if user wants to skip
            if (vin.length === 17 && this.isValidVin(vin)) {
                console.log(`Valid VIN entered, creating new row...`);
                // Add new row and focus on it
                this.addVinRow();
                const tableBody = document.getElementById('vinTableBody');
                const newRowNumber = tableBody ? tableBody.rows.length : rowNumber + 1;
                
                setTimeout(() => {
                    const newInput = document.getElementById(`vin-input-${newRowNumber}`);
                    if (newInput) {
                        newInput.focus();
                        console.log(`Focused on new row ${newRowNumber}`);
                    } else {
                        console.error(`Could not focus on new input ${newRowNumber}`);
                    }
                }, 100); // Increased delay to ensure DOM is updated
            } else if (vin.length > 0) {
                // Show error if VIN is not valid
                console.log(`Invalid VIN, showing error...`);
                this.showVinError(rowNumber, 'Please enter a valid 17-character VIN before moving to next row');
            } else {
                // Allow moving to next row even if current is empty
                console.log(`Empty VIN, moving to next row...`);
                this.focusNextRow(rowNumber);
            }
        }
    }

    focusNextRow(currentRow) {
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody) {
            console.error('Cannot find VIN table body');
            return;
        }
        
        // Check if next row exists
        const nextRowNumber = currentRow + 1;
        let nextInput = document.getElementById(`vin-input-${nextRowNumber}`);
        
        console.log(`Attempting to focus on row ${nextRowNumber}, input exists: ${!!nextInput}`);
        
        if (!nextInput) {
            // Create new row if it doesn't exist
            console.log(`Creating new row ${nextRowNumber}...`);
            this.addVinRow();
            setTimeout(() => {
                nextInput = document.getElementById(`vin-input-${nextRowNumber}`);
                if (nextInput) {
                    nextInput.focus();
                    console.log(`Successfully focused on new row ${nextRowNumber}`);
                } else {
                    console.error(`Failed to create/focus on row ${nextRowNumber}`);
                }
            }, 100);
        } else {
            nextInput.focus();
            console.log(`Focused on existing row ${nextRowNumber}`);
        }
    }

    getAllVinsFromTable() {
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody) return [];

        const vins = [];
        for (let i = 1; i <= tableBody.rows.length; i++) {
            const input = document.getElementById(`vin-input-${i}`);
            if (input && input.value.trim()) {
                vins.push(input.value.trim().toUpperCase());
            }
        }

        return vins;
    }

    updateVinCounts() {
        const vins = this.getAllVinsFromTable();
        const validVins = vins.filter(vin => this.isValidVin(vin));
        const invalidVins = vins.filter(vin => vin.length > 0 && !this.isValidVin(vin));

        document.getElementById('validCount').textContent = validVins.length;
        document.getElementById('invalidCount').textContent = invalidVins.length;
        document.getElementById('totalCount').textContent = vins.length;
    }

    clearVinTable() {
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody) return;

        // Clear all input values
        for (let i = 1; i <= tableBody.rows.length; i++) {
            const input = document.getElementById(`vin-input-${i}`);
            if (input) {
                input.value = '';
                this.validateVin(i);
            }
        }
    }
    
    debugVinTable() {
        // Debugging function to check the state of all VIN inputs
        console.log('=== VIN TABLE DEBUG INFO ===');
        const tableBody = document.getElementById('vinTableBody');
        if (!tableBody) {
            console.log('❌ Table body not found');
            return;
        }
        
        console.log(`📊 Total rows: ${tableBody.rows.length}`);
        
        const inputs = document.querySelectorAll('.vin-input');
        console.log(`🔍 Total VIN inputs found: ${inputs.length}`);
        
        inputs.forEach((input, index) => {
            const rowNumber = input.getAttribute('data-row-number');
            const hasListeners = input.hasAttribute('data-listeners-attached');
            const value = input.value;
            const id = input.id;
            
            console.log(`Row ${index + 1}:`, {
                id,
                rowNumber,
                hasListeners,
                value: value || '(empty)',
                exists: !!document.getElementById(id)
            });
        });
        
        // Test validation on all rows
        for (let i = 1; i <= tableBody.rows.length; i++) {
            const input = document.getElementById(`vin-input-${i}`);
            if (input && input.value.length === 17) {
                console.log(`🧪 Testing validation on row ${i} with VIN: ${input.value}`);
                this.validateVin(i);
            }
        }
        
        console.log('=== END DEBUG INFO ===');
    }
}

// Initialize wizard when page loads
let wizard;
document.addEventListener('DOMContentLoaded', () => {
    wizard = new OrderWizard();
    // Set global reference after initialization
    window.wizard = wizard;
    
    // Add global debugging functions for troubleshooting
    window.debugVinTable = () => {
        if (wizard) {
            wizard.debugVinTable();
        } else {
            console.log('❌ Wizard not initialized');
        }
    };
    
    window.repairVinValidation = () => {
        if (wizard) {
            console.log('🔧 Repairing VIN validation...');
            wizard.attachAllEventListeners();
            console.log('✅ VIN validation repair completed');
        } else {
            console.log('❌ Wizard not initialized');
        }
    };
    
    window.testVinValidation = (rowNumber) => {
        if (wizard && rowNumber) {
            console.log(`🧪 Testing validation on row ${rowNumber}`);
            wizard.validateVin(rowNumber);
        } else {
            console.log('❌ Wizard not initialized or row number not provided');
        }
    };
});

// Manual Data Entry Modal Functions
let currentEditingVehicle = null;
let currentEditingIndex = -1;
let reviewVehicleData = []; // Store the review data globally

function openManualDataModal(rowIndex, vehicleData) {
    currentEditingIndex = rowIndex;
    currentEditingVehicle = { ...vehicleData }; // Clone the data
    
    // Populate the form with current data
    document.getElementById('editYear').value = vehicleData.year || '';
    document.getElementById('editMake').value = vehicleData.make || '';
    document.getElementById('editModel').value = vehicleData.model || '';
    document.getElementById('editTrim').value = vehicleData.trim || '';
    document.getElementById('editStock').value = vehicleData.stock || '';
    document.getElementById('editVin').value = vehicleData.vin || '';
    document.getElementById('editPrice').value = vehicleData.price || '';
    document.getElementById('editType').value = vehicleData.type || 'Pre-Owned';
    document.getElementById('editColor').value = vehicleData.ext_color || '';
    document.getElementById('editMileage').value = vehicleData.mileage || '';
    document.getElementById('editFuelType').value = vehicleData.fuel_type || '';
    document.getElementById('editTransmission').value = vehicleData.transmission || '';
    document.getElementById('editVehicleUrl').value = vehicleData.vehicle_url || '';
    document.getElementById('editRowIndex').value = rowIndex;
    
    // Show the modal
    document.getElementById('manualDataEntryModal').style.display = 'flex';
    
    // Focus on the first input
    setTimeout(() => {
        document.getElementById('editYear').focus();
    }, 100);
}

function closeManualDataModal() {
    document.getElementById('manualDataEntryModal').style.display = 'none';
    currentEditingVehicle = null;
    currentEditingIndex = -1;
    
    // Clear the form
    document.getElementById('vehicleEditForm').reset();
}

function saveVehicleEdit() {
    const formData = new FormData(document.getElementById('vehicleEditForm'));
    const updatedVehicle = {};
    
    // Extract all form data
    for (let [key, value] of formData.entries()) {
        if (key !== 'rowIndex') {
            updatedVehicle[key] = value;
        }
    }
    
    // Validate required fields
    if (!updatedVehicle.vin || updatedVehicle.vin.length !== 17) {
        alert('VIN must be exactly 17 characters');
        return;
    }
    
    if (!updatedVehicle.year || updatedVehicle.year < 1900 || updatedVehicle.year > 2030) {
        alert('Please enter a valid year');
        return;
    }
    
    if (!updatedVehicle.make || !updatedVehicle.model) {
        alert('Make and Model are required');
        return;
    }
    
    // Update the vehicle data in the global array
    if (reviewVehicleData[currentEditingIndex]) {
        Object.assign(reviewVehicleData[currentEditingIndex], updatedVehicle);
    }
    
    // Update the displayed table
    updateReviewTableRow(currentEditingIndex, updatedVehicle);
    
    // Close the modal
    closeManualDataModal();
    
    // Show success message
    showNotification('Vehicle data updated successfully', 'success');
}

function updateReviewTableRow(rowIndex, vehicleData) {
    const table = document.querySelector('#modalReviewSummary table tbody');
    if (!table) return;
    
    const row = table.rows[rowIndex];
    if (!row) return;
    
    // Update table cells (adjust indices based on your table structure)
    const cells = row.cells;
    if (cells.length >= 7) {
        cells[1].textContent = `${vehicleData.year || ''} ${vehicleData.make || ''}`.trim();
        cells[2].textContent = vehicleData.model || '';
        cells[3].textContent = vehicleData.trim || '';
        cells[4].textContent = vehicleData.stock || '';
        cells[5].textContent = vehicleData.vin || '';
        // QR code column stays the same (index 6)
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        max-width: 300px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.borderColor = '#10b981';
        notification.style.background = 'rgba(16, 185, 129, 0.1)';
    } else if (type === 'error') {
        notification.style.borderColor = '#ef4444';
        notification.style.background = 'rgba(239, 68, 68, 0.1)';
    }
    
    // Add to document
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.id === 'manualDataEntryModal') {
        closeManualDataModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('manualDataEntryModal').style.display === 'flex') {
        closeManualDataModal();
    }
});