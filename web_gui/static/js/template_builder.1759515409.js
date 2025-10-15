/**
 * Template Builder JavaScript
 * Handles drag-and-drop template creation, field management, and live preview
 */

class TemplateBuilder {
    constructor() {
        this.currentTemplate = {
            id: null,
            name: '',
            description: '',
            type: 'standard',
            fields: { columns: [] }
        };
        this.draggedField = null;
        this.templates = [];
        this.dealerships = [];
        this.customCombinedFields = {};
        this.selectedFields = [];
        this.fieldSeparators = []; // Track individual separators between fields

        this.init();
        // Load custom fields from localStorage after initialization
        setTimeout(() => this.loadCustomFieldsFromStorage(), 100);
    }

    init() {
        console.log('[TEMPLATE BUILDER] Initializing...');
        this.bindEvents();
        this.setupDragAndDrop();
        this.loadTemplates();
        this.loadDealerships();
    }

    bindEvents() {
        // Template management buttons
        document.getElementById('newTemplateBtn')?.addEventListener('click', () => this.createNewTemplate());
        document.getElementById('saveTemplateBtn')?.addEventListener('click', () => this.saveTemplate());
        document.getElementById('updateTemplateBtn')?.addEventListener('click', () => this.updateTemplate());
        document.getElementById('templatePreviewBtn')?.addEventListener('click', () => this.previewTemplate());
        document.getElementById('clearTemplateBtn')?.addEventListener('click', () => this.clearTemplate());
        document.getElementById('addColumnBtn')?.addEventListener('click', () => this.addColumn());

        // Field concatenation button
        const createBtn = document.getElementById('createCombinedFieldBtn');
        console.log('[TEMPLATE BUILDER] createCombinedFieldBtn element:', createBtn);
        if (createBtn) {
            createBtn.addEventListener('click', (e) => {
                console.log('[TEMPLATE BUILDER] Create combined field button clicked');
                e.preventDefault();
                this.openFieldConcatenationModal();
            });
        } else {
            console.error('[TEMPLATE BUILDER] createCombinedFieldBtn element not found!');
        }

        // Template properties form
        document.getElementById('templateName')?.addEventListener('input', (e) => {
            this.currentTemplate.name = e.target.value;
        });

        document.getElementById('templateDescription')?.addEventListener('input', (e) => {
            this.currentTemplate.description = e.target.value;
        });

        document.getElementById('templateType')?.addEventListener('change', (e) => {
            this.currentTemplate.type = e.target.value;
        });

        // Preview dealership selection
        document.getElementById('previewDealership')?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadPreviewData(e.target.value);
            }
        });

        // Field concatenation modal events
        this.bindConcatenationModalEvents();
    }

    setupDragAndDrop() {
        // Make field items draggable
        this.setupFieldDragHandlers();

        // Setup drop zones
        this.setupDropZone();
    }

    setupFieldDragHandlers() {
        const fieldItems = document.querySelectorAll('.field-item[draggable="true"]');

        fieldItems.forEach(item => {
            // Skip if handlers already attached
            if (item.dataset.handlersAttached === 'true') {
                return;
            }

            // Mark handlers as attached
            item.dataset.handlersAttached = 'true';

            // Add click functionality
            item.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('[TEMPLATE BUILDER] Field clicked:', item.dataset.field);

                const fieldData = {
                    key: item.dataset.field,
                    label: item.querySelector('span').textContent,
                    type: this.getFieldType(item.dataset.field),
                    icon: item.querySelector('i').className
                };

                // Add visual feedback for click
                item.classList.add('field-clicked');
                setTimeout(() => {
                    item.classList.remove('field-clicked');
                }, 300);

                // Add field to template
                this.addFieldToTemplate(fieldData);
            });

            // Drag functionality
            item.addEventListener('dragstart', (e) => {
                const fieldData = {
                    key: item.dataset.field,
                    label: item.querySelector('span').textContent,
                    type: this.getFieldType(item.dataset.field),
                    icon: item.querySelector('i').className
                };

                this.draggedField = fieldData;
                item.classList.add('dragging');

                // Set drag data
                e.dataTransfer.setData('application/json', JSON.stringify(fieldData));
                e.dataTransfer.effectAllowed = 'copy';
            });

            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
                this.draggedField = null;
            });
        });
    }

    setupDropZone() {
        // Make the entire template canvas accept drops (not just the small dropZone box)
        const templateCanvas = document.getElementById('templateCanvas');
        const dropZone = document.getElementById('dropZone');
        const templateColumns = document.getElementById('templateColumns');

        // Setup the entire canvas as the drop zone
        if (templateCanvas) {
            templateCanvas.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';

                // Add visual feedback to the entire canvas
                templateCanvas.classList.add('drag-over');

                // Also add feedback to the small dropZone if it exists (when empty)
                if (dropZone && dropZone.classList.contains('drop-zone')) {
                    dropZone.classList.add('drag-over');
                }
            });

            templateCanvas.addEventListener('dragleave', (e) => {
                // Only remove if we're actually leaving the canvas area
                const rect = templateCanvas.getBoundingClientRect();
                if (e.clientX < rect.left || e.clientX >= rect.right ||
                    e.clientY < rect.top || e.clientY >= rect.bottom) {
                    templateCanvas.classList.remove('drag-over');

                    if (dropZone && dropZone.classList.contains('drop-zone')) {
                        dropZone.classList.remove('drag-over');
                    }
                }
            });

            templateCanvas.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();

                // Remove visual feedback
                templateCanvas.classList.remove('drag-over');
                if (dropZone && dropZone.classList.contains('drop-zone')) {
                    dropZone.classList.remove('drag-over');
                }

                try {
                    const fieldData = JSON.parse(e.dataTransfer.getData('application/json'));
                    this.addFieldToTemplate(fieldData);
                } catch (error) {
                    console.error('[TEMPLATE BUILDER] Error dropping field:', error);
                }
            });
        }

        // Also keep the templateColumns as a drop zone for backwards compatibility
        if (templateColumns) {
            templateColumns.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';
            });

            templateColumns.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();

                try {
                    const fieldData = JSON.parse(e.dataTransfer.getData('application/json'));
                    this.addFieldToTemplate(fieldData);
                } catch (error) {
                    console.error('[TEMPLATE BUILDER] Error dropping field:', error);
                }
            });
        }
    }

    addFieldToTemplate(fieldData) {
        console.log('[TEMPLATE BUILDER] Adding field to template:', fieldData);

        // Check if this is a custom combined field
        const isCustomCombined = this.customCombinedFields && this.customCombinedFields[fieldData.key];

        // Add to current template
        const fieldConfig = {
            key: fieldData.key,
            label: fieldData.label || (isCustomCombined ? this.customCombinedFields[fieldData.key].label : fieldData.key),
            type: fieldData.type || (isCustomCombined ? 'combined' : 'text'),
            source: fieldData.key,
            width: this.getDefaultWidth(fieldData.key),
            order: this.currentTemplate.fields.columns.length + 1
        };

        // If it's a custom combined field, add the combination definition
        if (isCustomCombined) {
            fieldConfig.isCombined = true;
            fieldConfig.combinedFields = this.customCombinedFields[fieldData.key].fields;
            fieldConfig.separator = this.customCombinedFields[fieldData.key].separator;
        }

        // Handle special calculated fields that need additional configuration
        if (fieldData.key === 'price_with_markup') {
            fieldConfig.calculation = 'price_markup';
            // Default markup amount - can be configured later
            fieldConfig.markup_amount = 1000;
        }

        this.currentTemplate.fields.columns.push(fieldConfig);

        // Update UI
        this.renderTemplateColumns();
        this.updatePreview();
    }

    renderTemplateColumns() {
        const templateColumns = document.getElementById('templateColumns');

        if (this.currentTemplate.fields.columns.length === 0) {
            templateColumns.innerHTML = `
                <div class="drop-zone empty" id="dropZone">
                    <div class="drop-message">
                        <i class="fas fa-mouse-pointer"></i>
                        <p>Click or drag fields to add them to your template</p>
                        <p class="help-text">Click any field from the Available Fields panel to add it</p>
                    </div>
                </div>
            `;
            this.setupDropZone();
            return;
        }

        let columnsHTML = '';

        this.currentTemplate.fields.columns.forEach((field, index) => {
            columnsHTML += `
                <div class="template-column" data-field="${field.key}">
                    <div class="column-header">
                        <div class="column-title">${field.label}</div>
                        <div class="column-controls">
                            <button class="btn-icon" onclick="templateBuilder.editField(${index})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-icon danger" onclick="templateBuilder.removeField(${index})" title="Remove">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="column-field">
                        <div class="field-info">
                            <i class="${this.getFieldIcon(field.key)}"></i>
                            <span>${field.key.toUpperCase()}</span>
                        </div>
                        <div class="field-controls">
                            ${index > 0 ? `<button class="btn-icon" onclick="templateBuilder.moveField(${index}, -1)" title="Move Left"><i class="fas fa-arrow-left"></i></button>` : ''}
                            ${index < this.currentTemplate.fields.columns.length - 1 ? `<button class="btn-icon" onclick="templateBuilder.moveField(${index}, 1)" title="Move Right"><i class="fas fa-arrow-right"></i></button>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        templateColumns.innerHTML = columnsHTML;
    }

    removeField(index) {
        this.currentTemplate.fields.columns.splice(index, 1);
        this.renderTemplateColumns();
        this.updatePreview();
    }

    moveField(index, direction) {
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= this.currentTemplate.fields.columns.length) return;

        const field = this.currentTemplate.fields.columns.splice(index, 1)[0];
        this.currentTemplate.fields.columns.splice(newIndex, 0, field);

        this.renderTemplateColumns();
        this.updatePreview();
    }

    editField(index) {
        // Simple prompt for now - could be enhanced with a modal
        const field = this.currentTemplate.fields.columns[index];
        const newLabel = prompt('Enter field label:', field.label);

        if (newLabel && newLabel.trim()) {
            field.label = newLabel.trim();
            this.renderTemplateColumns();
            this.updatePreview();
        }
    }

    addColumn() {
        // Add a placeholder column that user can configure
        const fieldConfig = {
            key: 'custom_field',
            label: 'Custom Field',
            type: 'text',
            source: 'custom_field',
            width: '20%',
            order: this.currentTemplate.fields.columns.length + 1
        };

        this.currentTemplate.fields.columns.push(fieldConfig);
        this.renderTemplateColumns();
        this.updatePreview();
    }

    clearTemplate() {
        if (confirm('Are you sure you want to clear the template? This will remove all fields.')) {
            this.currentTemplate.fields.columns = [];
            this.renderTemplateColumns();
            this.updatePreview();
        }
    }

    createNewTemplate() {
        this.currentTemplate = {
            id: null,
            name: '',
            description: '',
            type: 'standard',
            fields: { columns: [] }
        };

        document.getElementById('templateName').value = '';
        document.getElementById('templateDescription').value = '';
        document.getElementById('templateType').value = 'standard';

        this.renderTemplateColumns();
        this.updatePreview();
        this.updateButtonVisibility();
    }

    updateButtonVisibility() {
        const updateBtn = document.getElementById('updateTemplateBtn');
        const saveBtn = document.getElementById('saveTemplateBtn');

        if (this.currentTemplate.id) {
            // Template is loaded - show Update button
            updateBtn.style.display = 'inline-block';
            saveBtn.textContent = 'Save as New';
        } else {
            // New template - hide Update button
            updateBtn.style.display = 'none';
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Template';
        }
    }

    async saveTemplate() {
        if (!this.currentTemplate.name.trim()) {
            alert('Please enter a template name');
            return;
        }

        if (!this.currentTemplate.fields || !this.currentTemplate.fields.columns || this.currentTemplate.fields.columns.length === 0) {
            alert('Please add at least one field to the template');
            return;
        }

        // Include custom combined fields in the template data
        const templateData = {
            name: this.currentTemplate.name,
            description: this.currentTemplate.description,
            type: this.currentTemplate.type,
            fields: this.currentTemplate.fields,
            customCombinedFields: this.customCombinedFields || {}
        };

        console.log('[TEMPLATE SAVE] Saving template with data:', templateData);

        try {
            // Always create new template (save as new)
            const response = await fetch('/api/templates/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(templateData)
            });

            const result = await response.json();

            if (result.success) {
                alert('Template saved successfully!');
                // Update the current template ID to the new template
                if (result.template_id) {
                    this.currentTemplate.id = result.template_id;
                }
                this.loadTemplates();
                this.updateButtonVisibility();
            } else {
                alert('Error saving template: ' + result.error);
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Save error:', error);
            alert('Error saving template');
        }
    }

    async updateTemplate() {
        if (!this.currentTemplate.id) {
            alert('No template loaded to update');
            return;
        }

        if (!this.currentTemplate.name.trim()) {
            alert('Please enter a template name');
            return;
        }

        if (this.currentTemplate.fields.columns.length === 0) {
            alert('Please add at least one field to the template');
            return;
        }

        try {
            // Update existing template
            const response = await fetch(`/api/templates/${this.currentTemplate.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_name: this.currentTemplate.name,
                    description: this.currentTemplate.description,
                    template_type: this.currentTemplate.type,
                    fields: this.currentTemplate.fields
                })
            });

            const result = await response.json();

            if (result.success) {
                alert('Template updated successfully!');
                this.loadTemplates();
            } else {
                alert('Error updating template: ' + result.error);
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Update error:', error);
            alert('Error updating template');
        }
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/templates/list');
            const result = await response.json();

            if (result.success) {
                this.templates = result.templates;
                this.renderTemplateList();
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Load templates error:', error);
        }
    }

    renderTemplateList() {
        const templateList = document.getElementById('templateList');

        if (this.templates.length === 0) {
            templateList.innerHTML = `
                <div class="template-item sample">
                    <div class="template-info">
                        <div class="template-name">No templates found</div>
                        <div class="template-details">Create your first template</div>
                    </div>
                </div>
            `;
            return;
        }

        let templatesHTML = '';

        this.templates.forEach(template => {
            const statusClass = template.is_active ? '' : 'inactive';
            const statusLabel = template.is_active ? '' : ' (Inactive)';
            templatesHTML += `
                <div class="template-item ${template.id === this.currentTemplate.id ? 'active' : ''} ${statusClass}" onclick="templateBuilder.loadTemplate(${template.id})">
                    <div class="template-info">
                        <div class="template-name">${template.template_name}${statusLabel}</div>
                        <div class="template-details">${template.fields?.columns?.length || 0} columns • ${template.template_type}</div>
                    </div>
                    <div class="template-actions">
                        <button class="btn-icon" onclick="event.stopPropagation(); templateBuilder.loadTemplate(${template.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="event.stopPropagation(); templateBuilder.cloneTemplate(${template.id})" title="Clone">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn-icon danger" onclick="event.stopPropagation(); templateBuilder.deleteTemplate(${template.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });

        templateList.innerHTML = templatesHTML;
    }

    async loadTemplate(templateId) {
        try {
            const response = await fetch(`/api/templates/${templateId}`);
            const result = await response.json();

            if (result.success) {
                this.currentTemplate = {
                    id: result.template.id,
                    name: result.template.template_name,
                    description: result.template.description || '',
                    type: result.template.template_type,
                    fields: result.template.fields || { columns: [] }
                };

                // Load custom combined fields if present in the template
                if (result.template.fields && result.template.fields.customCombinedFields) {
                    this.customCombinedFields = result.template.fields.customCombinedFields;
                    // Also save to localStorage for persistence
                    this.saveCustomFieldsToStorage();
                    // Render the custom fields in the UI
                    this.renderStoredCustomFields();
                }

                // Update form
                document.getElementById('templateName').value = this.currentTemplate.name;
                document.getElementById('templateDescription').value = this.currentTemplate.description;
                document.getElementById('templateType').value = this.currentTemplate.type;

                // Update UI
                this.renderTemplateColumns();
                this.renderTemplateList();
                this.updatePreview();
                this.updateButtonVisibility();
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Load template error:', error);
        }
    }

    async deleteTemplate(templateId) {
        if (!confirm('Are you sure you want to delete this template?')) return;

        try {
            const response = await fetch(`/api/templates/${templateId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                alert('Template deleted successfully!');
                this.loadTemplates();

                if (this.currentTemplate.id === templateId) {
                    this.createNewTemplate();
                }
            } else {
                alert('Error deleting template: ' + result.error);
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Delete error:', error);
            alert('Error deleting template');
        }
    }

    async cloneTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        this.currentTemplate = {
            id: null,
            name: template.template_name + ' (Copy)',
            description: template.description || '',
            type: template.template_type,
            fields: JSON.parse(JSON.stringify(template.fields || { columns: [] }))
        };

        // Update form
        document.getElementById('templateName').value = this.currentTemplate.name;
        document.getElementById('templateDescription').value = this.currentTemplate.description;
        document.getElementById('templateType').value = this.currentTemplate.type;

        // Update UI
        this.renderTemplateColumns();
        this.updatePreview();
    }

    async loadDealerships() {
        try {
            const response = await fetch('/api/dealership-configs');
            const result = await response.json();

            if (result.success) {
                this.dealerships = result.dealerships;
                this.renderDealershipOptions();
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Load dealerships error:', error);
        }
    }

    renderDealershipOptions() {
        const select = document.getElementById('previewDealership');
        if (!select) return;

        let optionsHTML = '<option value="">Select dealership for sample data...</option>';

        this.dealerships.forEach(dealership => {
            optionsHTML += `<option value="${dealership.name}">${dealership.name}</option>`;
        });

        select.innerHTML = optionsHTML;
    }

    async loadPreviewData(dealershipName) {
        if (this.currentTemplate.fields.columns.length === 0) {
            this.updatePreview([]);
            return;
        }

        const requestData = {
            dealership: dealershipName,
            fields: {
                columns: this.currentTemplate.fields || []
            },
            sample_vin: null // Will be filled when user selects a specific VIN
        };

        console.log('[TEMPLATE BUILDER DEBUG] Request data:', requestData);

        try {
            const response = await fetch(`/api/templates/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            console.log('[TEMPLATE BUILDER DEBUG] API response:', result);

            if (result.success) {
                console.log('[TEMPLATE BUILDER DEBUG] Preview data:', result.preview);
                this.updatePreview(result.preview || []);
            } else {
                console.error('[TEMPLATE BUILDER] Preview error:', result.error);
                this.updatePreview([]);
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Preview request error:', error);
            this.updatePreview([]);
        }
    }

    updatePreview(sampleData = []) {
        const tableHead = document.getElementById('previewTableHead');
        const tableBody = document.getElementById('previewTableBody');

        if (this.currentTemplate.fields.columns.length === 0) {
            tableHead.innerHTML = `
                <tr>
                    <td colspan="100%" class="no-preview">
                        <i class="fas fa-info-circle"></i>
                        Add fields to see preview
                    </td>
                </tr>
            `;
            tableBody.innerHTML = '';
            return;
        }

        // Generate header
        let headerHTML = '<tr>';
        this.currentTemplate.fields.columns.forEach(field => {
            headerHTML += `<th>${field.label}</th>`;
        });
        headerHTML += '</tr>';
        tableHead.innerHTML = headerHTML;

        // Generate body
        if (sampleData.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="${this.currentTemplate.fields.columns.length}" class="no-preview">
                        <i class="fas fa-database"></i>
                        Select a dealership to load sample data
                    </td>
                </tr>
            `;
            return;
        }

        let bodyHTML = '';
        sampleData.slice(0, 5).forEach(row => {
            bodyHTML += '<tr>';
            this.currentTemplate.fields.columns.forEach(field => {
                const value = row[field.key] || row[field.key.toUpperCase()] || '';
                bodyHTML += `<td>${value}</td>`;
            });
            bodyHTML += '</tr>';
        });

        tableBody.innerHTML = bodyHTML;
    }

    previewTemplate() {
        const dealershipSelect = document.getElementById('previewDealership');
        const selectedDealership = dealershipSelect.value;

        if (!selectedDealership) {
            alert('Please select a dealership to preview template with sample data');
            dealershipSelect.focus();
            return;
        }

        this.loadPreviewData(selectedDealership);
    }

    // Helper methods
    getFieldType(fieldKey) {
        // Check if it's a custom combined field first
        if (this.customCombinedFields && this.customCombinedFields[fieldKey]) {
            return 'concatenated';
        }

        const typeMap = {
            'vin': 'text',
            'stock': 'text',
            'year': 'number',
            'make': 'text',
            'model': 'text',
            'trim': 'text',
            'price': 'currency',
            'msrp': 'currency',
            'qr_code': 'special',
            'days_on_lot': 'calculated',
            'price_with_markup': 'calculated',
            'year_make_model': 'concatenated',
            'stock_vin': 'concatenated'
        };

        return typeMap[fieldKey] || 'text';
    }

    getFieldIcon(fieldKey) {
        const iconMap = {
            'vin': 'fas fa-barcode',
            'stock': 'fas fa-hashtag',
            'year': 'fas fa-calendar',
            'make': 'fas fa-industry',
            'model': 'fas fa-car',
            'trim': 'fas fa-star',
            'price': 'fas fa-dollar-sign',
            'msrp': 'fas fa-tag',
            'qr_code': 'fas fa-qrcode',
            'days_on_lot': 'fas fa-clock',
            'year_make_model': 'fas fa-compress-alt',
            'stock_vin': 'fas fa-link'
        };

        return iconMap[fieldKey] || 'fas fa-question';
    }

    getDefaultWidth(fieldKey) {
        const widthMap = {
            'vin': '25%',
            'stock': '15%',
            'year': '10%',
            'make': '15%',
            'model': '20%',
            'trim': '15%',
            'price': '15%',
            'msrp': '15%',
            'qr_code': '10%',
            'days_on_lot': '10%',
            'year_make_model': '30%',
            'stock_vin': '25%'
        };

        return widthMap[fieldKey] || '20%';
    }

    // Field Concatenation Methods
    bindConcatenationModalEvents() {
        // Initialize concatenation state
        this.selectedFields = [];

        // Modal controls
        document.getElementById('closeConcatenationModal')?.addEventListener('click', () => this.closeConcatenationModal());
        document.getElementById('cancelConcatenation')?.addEventListener('click', () => this.closeConcatenationModal());
        document.getElementById('createCombinedField')?.addEventListener('click', () => this.createCombinedField());

        // Field name input - auto-generate key
        document.getElementById('combinedFieldName')?.addEventListener('input', (e) => {
            const name = e.target.value;
            const key = name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
            document.getElementById('combinedFieldKey').value = key;
            this.updateFieldPreview();
        });

        // Separator change
        document.getElementById('fieldSeparator')?.addEventListener('change', () => this.updateFieldPreview());

        // Field chip clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.field-chip') && e.target.closest('#availableFieldChips')) {
                this.toggleFieldSelection(e.target.closest('.field-chip'));
            }
        });

        // Close modal when clicking outside
        document.getElementById('fieldConcatenationModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'fieldConcatenationModal') {
                this.closeConcatenationModal();
            }
        });
    }

    openFieldConcatenationModal() {
        console.log('[TEMPLATE BUILDER] Opening field concatenation modal');

        // Reset form
        this.selectedFields = [];

        const nameField = document.getElementById('combinedFieldName');
        const keyField = document.getElementById('combinedFieldKey');
        const separatorField = document.getElementById('fieldSeparator');
        const modal = document.getElementById('fieldConcatenationModal');

        console.log('[TEMPLATE BUILDER] Modal elements:', {
            nameField,
            keyField,
            separatorField,
            modal
        });

        if (nameField) nameField.value = '';
        if (keyField) keyField.value = '';
        if (separatorField) separatorField.value = ' ';

        // Clear any selected state
        document.querySelectorAll('.field-chip').forEach(chip => {
            chip.classList.remove('selected');
        });

        // Reset builder area
        this.updateFieldCombinationBuilder();
        this.updateFieldPreview();

        // Show modal
        if (modal) {
            console.log('[TEMPLATE BUILDER] Showing modal');
            modal.style.display = 'flex';

            // Setup event listeners for field selection after modal is shown
            setTimeout(() => {
                this.setupModalFieldInteractions();
            }, 100);
        } else {
            console.error('[TEMPLATE BUILDER] Modal element not found!');
        }
    }

    closeConcatenationModal() {
        document.getElementById('fieldConcatenationModal').style.display = 'none';
        this.selectedFields = [];
    }

    setupDropZoneOnly() {
        const self = this;
        const builderArea = document.getElementById('fieldCombinationBuilder');
        if (!builderArea) return;

        // Remove old listeners by cloning
        const newBuilderArea = builderArea.cloneNode(true);
        builderArea.parentNode.replaceChild(newBuilderArea, builderArea);
        const dropZone = newBuilderArea;

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            e.dataTransfer.dropEffect = 'copy';
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const rect = dropZone.getBoundingClientRect();
            if (e.clientX < rect.left || e.clientX >= rect.right ||
                e.clientY < rect.top || e.clientY >= rect.bottom) {
                dropZone.classList.remove('drag-over');
            }
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');

            try {
                const dataStr = e.dataTransfer.getData('text/plain');
                if (!dataStr) {
                    console.error('[TEMPLATE BUILDER] No data in drop event');
                    return;
                }

                const fieldData = JSON.parse(dataStr);
                console.log('[TEMPLATE BUILDER] Field dropped:', fieldData);

                // Check if field is already selected
                if (!self.selectedFields.some(f => f.key === fieldData.key)) {
                    // Add to selected fields
                    self.selectedFields.push(fieldData);

                    // Update visual state
                    const sourceChip = document.querySelector(`#availableFieldChips [data-field="${fieldData.key}"]`);
                    if (sourceChip) {
                        sourceChip.classList.add('selected');
                    }

                    // Update UI
                    self.updateFieldCombinationBuilder();
                    self.updateFieldPreview();

                    // Re-setup drop zone after DOM update
                    setTimeout(() => {
                        self.setupDropZoneOnly();
                    }, 100);
                } else {
                    console.log('[TEMPLATE BUILDER] Field already selected:', fieldData.key);
                }
            } catch (err) {
                console.error('[TEMPLATE BUILDER] Error handling drop:', err);
            }
        });
    }

    setupModalFieldInteractions() {
        console.log('[TEMPLATE BUILDER] Setting up modal field interactions');
        console.log('[DEBUG] Current context:', this);
        console.log('[DEBUG] Initial selectedFields:', this.selectedFields);

        // Remove old event listeners by cloning
        const container = document.getElementById('availableFieldChips');
        if (!container) {
            console.error('[DEBUG] availableFieldChips container not found!');
            return;
        }

        const newContainer = container.cloneNode(true);
        container.parentNode.replaceChild(newContainer, container);

        // Setup click handlers for available field chips using arrow functions to preserve context
        document.querySelectorAll('#availableFieldChips .field-chip').forEach(chip => {
            // Click to select/deselect - arrow function preserves 'this'
            chip.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('[TEMPLATE BUILDER] Field chip clicked:', chip.dataset.field);
                console.log('[DEBUG] Context in click handler:', this);
                this.toggleFieldSelection(chip);
            });

            // Make draggable
            chip.draggable = true;

            chip.addEventListener('dragstart', (e) => {
                console.log('[TEMPLATE BUILDER] Drag started:', chip.dataset.field);
                e.dataTransfer.effectAllowed = 'copy';

                // Get the text content (excluding the icon)
                const textContent = chip.textContent.trim();
                const iconElement = chip.querySelector('i');
                const fieldLabel = textContent; // The text after the icon

                e.dataTransfer.setData('text/plain', JSON.stringify({
                    key: chip.dataset.field,
                    label: fieldLabel,
                    icon: iconElement ? iconElement.className : ''
                }));
                chip.classList.add('dragging');
            });

            chip.addEventListener('dragend', (e) => {
                console.log('[TEMPLATE BUILDER] Drag ended:', chip.dataset.field);
                chip.classList.remove('dragging');
                // Remove drag-over class from any drop zones
                document.querySelectorAll('.drag-over').forEach(el => {
                    el.classList.remove('drag-over');
                });
            });
        });

        // Setup drop zone for selected fields
        const builderArea = document.getElementById('fieldCombinationBuilder');

        if (builderArea) {
            // Remove existing listeners
            const newBuilderArea = builderArea.cloneNode(true);
            builderArea.parentNode.replaceChild(newBuilderArea, builderArea);
            const dropZone = newBuilderArea;

            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.dataTransfer.dropEffect = 'copy';
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                // Check if we're leaving the actual drop zone
                const rect = dropZone.getBoundingClientRect();
                if (e.clientX < rect.left || e.clientX >= rect.right ||
                    e.clientY < rect.top || e.clientY >= rect.bottom) {
                    dropZone.classList.remove('drag-over');
                }
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');

                try {
                    const dataStr = e.dataTransfer.getData('text/plain');
                    if (!dataStr) {
                        console.error('[TEMPLATE BUILDER] No data in drop event');
                        return;
                    }

                    const fieldData = JSON.parse(dataStr);
                    console.log('[TEMPLATE BUILDER] Field dropped:', fieldData);

                    // Check if field is already selected - use 'this' with arrow function
                    if (!this.selectedFields.some(f => f.key === fieldData.key)) {
                        // Add to selected fields
                        this.selectedFields.push(fieldData);
                        console.log('[TEMPLATE BUILDER] Selected fields now:', this.selectedFields);

                        // Update visual state
                        const sourceChip = document.querySelector(`#availableFieldChips [data-field="${fieldData.key}"]`);
                        if (sourceChip) {
                            sourceChip.classList.add('selected');
                        }

                        // Update UI without re-setting up drop zones
                        this.updateFieldCombinationBuilder();
                        this.updateFieldPreview();

                        // Re-setup interactions after DOM update
                        setTimeout(() => {
                            this.setupDropZoneOnly();
                        }, 100);
                    } else {
                        console.log('[TEMPLATE BUILDER] Field already selected:', fieldData.key);
                    }
                } catch (err) {
                    console.error('[TEMPLATE BUILDER] Error handling drop:', err);
                }
            });
        } else {
            console.error('[TEMPLATE BUILDER] fieldCombinationBuilder not found');
        }
    }

    toggleFieldSelection(fieldChip) {
        console.log('[DEBUG] toggleFieldSelection called');
        if (!fieldChip) {
            console.error('[DEBUG] fieldChip is null');
            return;
        }

        const fieldKey = fieldChip.dataset.field;
        const iconElement = fieldChip.querySelector('i');

        // Get the text content (the field label is the text after the icon)
        const textContent = fieldChip.textContent.trim();
        const fieldLabel = textContent;
        const fieldIcon = iconElement ? iconElement.className : '';

        console.log('[DEBUG] Field details:', {
            fieldKey,
            fieldLabel,
            fieldIcon,
            isSelected: fieldChip.classList.contains('selected'),
            currentSelectedFields: this.selectedFields
        });

        if (fieldChip.classList.contains('selected')) {
            // Remove from selection
            console.log('[DEBUG] Removing field from selection');
            fieldChip.classList.remove('selected');
            this.selectedFields = this.selectedFields.filter(f => f.key !== fieldKey);
        } else {
            // Check if field is already selected
            if (!this.selectedFields.some(f => f.key === fieldKey)) {
                // Add to selection
                console.log('[DEBUG] Adding field to selection');
                fieldChip.classList.add('selected');
                this.selectedFields.push({
                    key: fieldKey,
                    label: fieldLabel,
                    icon: fieldIcon
                });

                // Add visual feedback for click
                fieldChip.classList.add('field-clicked');
                setTimeout(() => {
                    fieldChip.classList.remove('field-clicked');
                }, 300);
            } else {
                console.log('[DEBUG] Field already selected');
            }
        }

        console.log('[DEBUG] Updated selectedFields:', this.selectedFields);
        console.log('[DEBUG] Calling updateFieldCombinationBuilder');
        this.updateFieldCombinationBuilder();
        console.log('[DEBUG] Calling updateFieldPreview');
        this.updateFieldPreview();
    }

    updateFieldCombinationBuilder() {
        console.log('[DEBUG updateFieldCombinationBuilder] Called with selectedFields:', this.selectedFields);
        const builder = document.getElementById('fieldCombinationBuilder');

        if (!builder) {
            console.error('[TEMPLATE BUILDER] fieldCombinationBuilder not found');
            return;
        }

        console.log('[DEBUG] Builder element found:', builder);
        console.log('[DEBUG] Number of selected fields:', this.selectedFields.length);

        if (this.selectedFields.length === 0) {
            console.log('[DEBUG] No fields selected, showing placeholder');
            builder.innerHTML = `
                <div class="combination-placeholder">
                    <i class="fas fa-mouse-pointer"></i>
                    <p>Click or drag fields from the left to add them here</p>
                </div>
            `;
        } else {
            console.log('[DEBUG] Rendering selected fields');

            // Initialize separators array if needed
            while (this.fieldSeparators.length < this.selectedFields.length - 1) {
                this.fieldSeparators.push(' '); // Default to space
            }

            const html = `
                <div class="field-combination-display">
                    ${this.selectedFields.map((field, index) => {
                        console.log('[DEBUG] Rendering field:', field);
                        const separator = this.fieldSeparators[index] || ' ';
                        return `
                        <div class="selected-field-item">
                            <i class="${field.icon}"></i>
                            <span>${field.label}</span>
                            <button class="remove-field" onclick="templateBuilder.removeSelectedField(${index})">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        ${index < this.selectedFields.length - 1 ? `
                        <div class="separator-selector">
                            <label>Separator:</label>
                            <select onchange="templateBuilder.updateSeparator(${index}, this.value)" class="separator-dropdown">
                                <option value=" " ${separator === ' ' ? 'selected' : ''}>Space</option>
                                <option value=" - " ${separator === ' - ' ? 'selected' : ''}>Space-Dash-Space</option>
                                <option value="-" ${separator === '-' ? 'selected' : ''}>Dash</option>
                                <option value="_" ${separator === '_' ? 'selected' : ''}>Underscore</option>
                                <option value=", " ${separator === ', ' ? 'selected' : ''}>Comma-Space</option>
                                <option value="" ${separator === '' ? 'selected' : ''}>None</option>
                            </select>
                        </div>
                        ` : ''}
                    `}).join('')}
                </div>
            `;
            console.log('[DEBUG] Generated HTML:', html);
            builder.innerHTML = html;
        }
        console.log('[DEBUG] updateFieldCombinationBuilder complete');
    }

    updateSeparator(index, value) {
        console.log(`[DEBUG] Updating separator at index ${index} to: "${value}"`);
        this.fieldSeparators[index] = value;
        this.updateFieldPreview();
    }

    removeSelectedField(index) {
        const removedField = this.selectedFields[index];
        this.selectedFields.splice(index, 1);

        // Also remove the separator after this field (if it exists)
        if (index < this.fieldSeparators.length) {
            this.fieldSeparators.splice(index, 1);
        }

        // Update UI
        const fieldChip = document.querySelector(`[data-field="${removedField.key}"]`);
        if (fieldChip) {
            fieldChip.classList.remove('selected');
        }

        this.updateFieldCombinationBuilder();
        this.updateFieldPreview();
    }

    updateFieldPreview() {
        const preview = document.getElementById('fieldPreview');
        const separatorElement = document.getElementById('fieldSeparator');

        if (!preview || !separatorElement) {
            console.error('[TEMPLATE BUILDER] Preview elements not found');
            return;
        }

        const separator = separatorElement.value;

        if (this.selectedFields.length === 0) {
            preview.innerHTML = '<span class="preview-text">Select fields to see preview</span>';
            return;
        }

        // Create sample data for preview
        const sampleData = {
            'vin': '1HGBH41JXMN109186',
            'stock': 'ST12345',
            'type': 'New',
            'year': '2024',
            'make': 'Honda',
            'model': 'Civic',
            'trim': 'LX',
            'price': '$25,999',
            'msrp': '$27,500',
            'ext_color': 'Blue',
            'body_style': 'Sedan',
            'fuel_type': 'Gasoline',
            'status': 'In Stock',
            'date_in_stock': '2024-01-15',
            'location': 'Main Lot',
            'street_address': '123 Main St',
            'locality': 'St Louis',
            'region': 'MO',
            'postal_code': '63101',
            'vehicle_url': 'https://dealer.com/vehicle/12345'
        };

        // Build preview text using individual separators
        let previewText = '';
        this.selectedFields.forEach((field, index) => {
            previewText += sampleData[field.key] || field.label;
            if (index < this.selectedFields.length - 1) {
                const sep = this.fieldSeparators[index] || ' ';
                previewText += sep;
            }
        });

        preview.innerHTML = `<span class="preview-sample">${previewText}</span>`;
    }

    createCombinedField() {
        const fieldName = document.getElementById('combinedFieldName').value.trim();
        const fieldKey = document.getElementById('combinedFieldKey').value.trim();
        const separator = document.getElementById('fieldSeparator').value;

        // Validation
        if (!fieldName) {
            alert('Please enter a field name');
            return;
        }

        if (!fieldKey) {
            alert('Please enter a field key');
            return;
        }

        if (this.selectedFields.length < 2) {
            alert('Please select at least 2 fields to combine');
            return;
        }

        // Check if field key already exists
        const existingField = document.querySelector(`[data-field="${fieldKey}"]`);
        if (existingField) {
            alert('A field with this key already exists. Please choose a different name.');
            return;
        }

        // Create the new combined field
        const newFieldHtml = `
            <div class="field-item combined custom-combined" data-field="${fieldKey}" draggable="true">
                <i class="fas fa-compress-alt"></i>
                <span>${fieldName}</span>
                <button class="remove-combined-field" onclick="templateBuilder.removeCombinedField('${fieldKey}')" title="Remove custom field">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add to the combined fields grid
        const combinedGrid = document.getElementById('combinedFieldsGrid');
        combinedGrid.insertAdjacentHTML('beforeend', newFieldHtml);

        // Store the combination definition for later use
        if (!this.customCombinedFields) {
            this.customCombinedFields = {};
        }

        // Generate dynamic formula for backend processing
        // Example: "{yearmake} - {stock_number}" for fields ['yearmake', 'stock'] with separator ' - '
        const formula = this._generateFormula(this.selectedFields, this.fieldSeparators);

        this.customCombinedFields[fieldKey] = {
            name: fieldName,
            fields: this.selectedFields.map(f => f.key),
            separator: separator, // Keep for backwards compatibility
            separators: [...this.fieldSeparators], // Array of individual separators
            formula: formula, // Dynamic formula for backend processing
            label: fieldName,
            icon: 'fas fa-compress-alt'
        };

        // Save to localStorage for persistence
        this.saveCustomFieldsToStorage();

        // Re-setup drag handlers for the new field
        this.setupFieldDragHandlers();

        // Close modal
        this.closeConcatenationModal();

        console.log('[TEMPLATE BUILDER] Created combined field:', fieldKey, this.customCombinedFields[fieldKey]);
    }

    _generateFormula(selectedFields, fieldSeparators) {
        /**
         * Generates a dynamic formula string for backend processing
         * Example: selectedFields = [{key: 'yearmake'}, {key: 'stock'}]
         *          fieldSeparators = [' - ']
         *          returns: "{yearmake} - {stock_number}"
         */
        if (!selectedFields || selectedFields.length === 0) {
            return '';
        }

        let formulaParts = [];

        for (let i = 0; i < selectedFields.length; i++) {
            const field = selectedFields[i];
            let placeholder = '';

            // Special handling for stock field - backend extracts just the stock number
            if (field.key === 'stock' || field.key === 'raw_stock') {
                placeholder = '{stock_number}';
            } else {
                // Direct field access for all other fields
                placeholder = `{${field.key}}`;
            }

            formulaParts.push(placeholder);

            // Add separator if not the last field
            if (i < selectedFields.length - 1 && fieldSeparators && fieldSeparators[i]) {
                formulaParts.push(fieldSeparators[i]);
            }
        }

        const formula = formulaParts.join('');
        console.log('[TEMPLATE BUILDER] Generated formula:', formula, 'from fields:', selectedFields.map(f => f.key));
        return formula;
    }

    saveCustomFieldsToStorage() {
        if (this.customCombinedFields) {
            localStorage.setItem('templateBuilderCustomFields', JSON.stringify(this.customCombinedFields));
        }
    }

    loadCustomFieldsFromStorage() {
        const stored = localStorage.getItem('templateBuilderCustomFields');
        if (stored) {
            try {
                this.customCombinedFields = JSON.parse(stored);
                // Re-render custom fields in the UI
                this.renderStoredCustomFields();
            } catch (e) {
                console.error('[TEMPLATE BUILDER] Error loading custom fields:', e);
                this.customCombinedFields = {};
            }
        }
    }

    renderStoredCustomFields() {
        if (!this.customCombinedFields || Object.keys(this.customCombinedFields).length === 0) {
            return;
        }

        const combinedGrid = document.getElementById('combinedFieldsGrid');
        if (!combinedGrid) return;

        Object.entries(this.customCombinedFields).forEach(([fieldKey, fieldData]) => {
            // Check if field already exists in DOM
            const existingField = document.querySelector(`[data-field="${fieldKey}"]`);
            if (!existingField) {
                const newFieldHtml = `
                    <div class="field-item combined custom-combined" data-field="${fieldKey}" draggable="true">
                        <i class="fas fa-compress-alt"></i>
                        <span>${fieldData.name || fieldData.label}</span>
                        <button class="remove-combined-field" onclick="templateBuilder.removeCombinedField('${fieldKey}')" title="Remove custom field">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
                combinedGrid.insertAdjacentHTML('beforeend', newFieldHtml);
            }
        });

        // Re-setup drag handlers for the restored fields
        this.setupFieldDragHandlers();
    }

    removeCombinedField(fieldKey) {
        if (confirm('Are you sure you want to remove this combined field?')) {
            // Remove from DOM
            const fieldElement = document.querySelector(`[data-field="${fieldKey}"]`);
            if (fieldElement) {
                fieldElement.remove();
            }

            // Remove from storage
            if (this.customCombinedFields && this.customCombinedFields[fieldKey]) {
                delete this.customCombinedFields[fieldKey];
                // Update localStorage
                this.saveCustomFieldsToStorage();
            }

            // Remove from current template if it exists there
            this.currentTemplate.fields.columns = this.currentTemplate.fields.columns.filter(
                col => col.key !== fieldKey
            );

            // Update template display
            this.renderTemplateColumns();
            this.updatePreview();
        }
    }
}

// Initialize when page loads
let templateBuilder;

document.addEventListener('DOMContentLoaded', () => {
    // Always create template builder instance for global access
    console.log('[TEMPLATE BUILDER] Initializing global instance...');
    templateBuilder = new TemplateBuilder();

    // Assign to global scope immediately
    window.templateBuilder = templateBuilder;
    console.log('[TEMPLATE BUILDER] Global assignment complete:', !!window.templateBuilder);

    // Debug: Check if template builder panel exists
    const panel = document.getElementById('template-builder-panel');
    console.log('[TEMPLATE BUILDER DEBUG] Panel found:', !!panel);
    if (panel) {
        console.log('[TEMPLATE BUILDER DEBUG] Panel classes:', panel.className);
        console.log('[TEMPLATE BUILDER DEBUG] Panel display style:', getComputedStyle(panel).display);

        // Check if the create button exists at this time
        const createBtn = document.getElementById('createCombinedFieldBtn');
        console.log('[TEMPLATE BUILDER DEBUG] createCombinedFieldBtn found at DOM ready:', !!createBtn);
    }

    // Add debugging for tab clicks
    const templateBuilderTab = document.querySelector('[data-tab="template-builder"]');
    if (templateBuilderTab) {
        console.log('[TEMPLATE BUILDER DEBUG] Tab button found:', templateBuilderTab);
        templateBuilderTab.addEventListener('click', () => {
            console.log('[TEMPLATE BUILDER DEBUG] Tab clicked - checking panel state...');
            setTimeout(() => {
                const panel = document.getElementById('template-builder-panel');
                console.log('[TEMPLATE BUILDER DEBUG] After click - Panel classes:', panel?.className);
                console.log('[TEMPLATE BUILDER DEBUG] After click - Panel display:', getComputedStyle(panel).display);
            }, 100);
        });
    } else {
        console.error('[TEMPLATE BUILDER DEBUG] Tab button NOT found!');
    }
});

// Global fallback event handler for the plus button
window.openFieldConcatenationModal = function() {
    console.log('[GLOBAL] openFieldConcatenationModal called');
    if (window.templateBuilder && window.templateBuilder.openFieldConcatenationModal) {
        window.templateBuilder.openFieldConcatenationModal();
    } else {
        console.error('[GLOBAL] templateBuilder not available');
        alert('Template builder not initialized. Please refresh the page and try again.');
    }
};

// Also add a direct click handler using event delegation
document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'createCombinedFieldBtn') {
        console.log('[DELEGATION] createCombinedFieldBtn clicked via event delegation');
        e.preventDefault();
        window.openFieldConcatenationModal();
    }
});