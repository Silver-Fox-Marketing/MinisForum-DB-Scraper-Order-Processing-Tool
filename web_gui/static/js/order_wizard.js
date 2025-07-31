/**
 * Order Processing Wizard - JavaScript Controller
 * Silver Fox Marketing - Guided Order Processing Interface
 * 
 * Handles wizard-style order processing with step-by-step workflow
 */

class OrderWizard {
    constructor() {
        this.currentStep = 0;
        this.steps = ['initialize', 'cao', 'list', 'review', 'complete'];
        this.queueData = [];
        this.caoOrders = [];
        this.listOrders = [];
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
        // Simulate CAO order processing
        // In real implementation, this would call the backend API
        const response = await fetch('/api/orders/process-cao', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dealerships: [dealershipName],
                vehicle_types: ['new', 'cpo', 'used']
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to process CAO order: ${response.statusText}`);
        }
        
        const results = await response.json();
        const result = results[0] || results; // Handle both array and single object responses
        
        // Map backend fields to frontend expected fields
        return {
            vehicles_processed: result.new_vehicles || 0,
            files_generated: result.qr_codes_generated || 0,
            success: result.success,
            dealership: result.dealership,
            download_csv: result.download_csv,
            qr_folder: result.qr_folder,
            csv_file: result.csv_file,
            timestamp: result.timestamp
        };
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
        const response = await fetch('/api/orders/process-list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dealership: dealershipName,
                vins: vins
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
        const csvFileList = document.getElementById('csvFileList');
        const qrFileList = document.getElementById('qrFileList');
        
        if (csvFileList && result.csv_files) {
            csvFileList.innerHTML = result.csv_files.map(file => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${file.size || 'Unknown size'}</div>
                    </div>
                    <button class="download-btn" onclick="wizard.downloadFile('${file.path}')">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            `).join('');
        }
        
        if (qrFileList && result.qr_files) {
            qrFileList.innerHTML = result.qr_files.map(file => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${file.count || 0} QR codes</div>
                    </div>
                    <button class="download-btn" onclick="wizard.downloadFile('${file.path}')">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            `).join('');
        }
    }
    
    approveOutput() {
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
            
            // Fetch the CSV data from the server
            const response = await fetch(`/api/csv/get-data/${this.currentEditingFile}`);
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
                    filename: this.currentEditingFile,
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
                    filename: this.currentEditingFile
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
        
        // Go back to review step
        this.backToReview();
        
        // Show success message
        this.showSuccess('Data changes applied successfully');
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
}

// Initialize wizard when page loads
let wizard;
document.addEventListener('DOMContentLoaded', () => {
    wizard = new OrderWizard();
    // Set global reference after initialization
    window.wizard = wizard;
});