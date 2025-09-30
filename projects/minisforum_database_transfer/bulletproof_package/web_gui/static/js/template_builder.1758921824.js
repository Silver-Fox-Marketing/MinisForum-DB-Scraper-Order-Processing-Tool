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

        this.init();
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
        const dropZone = document.getElementById('dropZone');
        const templateColumns = document.getElementById('templateColumns');

        [dropZone, templateColumns].forEach(zone => {
            if (!zone) return;

            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';

                if (zone.classList.contains('drop-zone')) {
                    zone.classList.add('drag-over');
                }
            });

            zone.addEventListener('dragleave', (e) => {
                if (zone.classList.contains('drop-zone')) {
                    zone.classList.remove('drag-over');
                }
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();

                if (zone.classList.contains('drop-zone')) {
                    zone.classList.remove('drag-over');
                }

                try {
                    const fieldData = JSON.parse(e.dataTransfer.getData('application/json'));
                    this.addFieldToTemplate(fieldData);
                } catch (error) {
                    console.error('[TEMPLATE BUILDER] Error dropping field:', error);
                }
            });
        });
    }

    addFieldToTemplate(fieldData) {
        console.log('[TEMPLATE BUILDER] Adding field to template:', fieldData);

        // Add to current template
        const fieldConfig = {
            key: fieldData.key,
            label: fieldData.label,
            type: fieldData.type,
            source: fieldData.key,
            width: this.getDefaultWidth(fieldData.key),
            order: this.currentTemplate.fields.columns.length + 1
        };

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
                        <p>Drag and drop fields here to create your template</p>
                        <p class="help-text">Start by dragging a field from the Available Fields panel</p>
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
    }

    async saveTemplate() {
        if (!this.currentTemplate.name.trim()) {
            alert('Please enter a template name');
            return;
        }

        if (this.currentTemplate.fields.columns.length === 0) {
            alert('Please add at least one field to the template');
            return;
        }

        try {
            const response = await fetch('/api/templates/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.currentTemplate)
            });

            const result = await response.json();

            if (result.success) {
                alert('Template saved successfully!');
                this.loadTemplates();
            } else {
                alert('Error saving template: ' + result.error);
            }
        } catch (error) {
            console.error('[TEMPLATE BUILDER] Save error:', error);
            alert('Error saving template');
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
            templatesHTML += `
                <div class="template-item ${template.id === this.currentTemplate.id ? 'active' : ''}" onclick="templateBuilder.loadTemplate(${template.id})">
                    <div class="template-info">
                        <div class="template-name">${template.template_name}</div>
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

                // Update form
                document.getElementById('templateName').value = this.currentTemplate.name;
                document.getElementById('templateDescription').value = this.currentTemplate.description;
                document.getElementById('templateType').value = this.currentTemplate.type;

                // Update UI
                this.renderTemplateColumns();
                this.renderTemplateList();
                this.updatePreview();
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
        } else {
            console.error('[TEMPLATE BUILDER] Modal element not found!');
        }
    }

    closeConcatenationModal() {
        document.getElementById('fieldConcatenationModal').style.display = 'none';
        this.selectedFields = [];
    }

    toggleFieldSelection(fieldChip) {
        const fieldKey = fieldChip.dataset.field;
        const fieldLabel = fieldChip.querySelector('span').textContent;
        const fieldIcon = fieldChip.querySelector('i').className;

        if (fieldChip.classList.contains('selected')) {
            // Remove from selection
            fieldChip.classList.remove('selected');
            this.selectedFields = this.selectedFields.filter(f => f.key !== fieldKey);
        } else {
            // Add to selection
            fieldChip.classList.add('selected');
            this.selectedFields.push({
                key: fieldKey,
                label: fieldLabel,
                icon: fieldIcon
            });
        }

        this.updateFieldCombinationBuilder();
        this.updateFieldPreview();
    }

    updateFieldCombinationBuilder() {
        const builder = document.getElementById('fieldCombinationBuilder');

        if (this.selectedFields.length === 0) {
            builder.innerHTML = `
                <div class="combination-placeholder">
                    <i class="fas fa-mouse-pointer"></i>
                    <p>Click fields from the left to add them here</p>
                </div>
            `;
            return;
        }

        builder.innerHTML = `
            <div class="field-combination-display">
                ${this.selectedFields.map((field, index) => `
                    <div class="selected-field-item">
                        <i class="${field.icon}"></i>
                        <span>${field.label}</span>
                        <button class="remove-field" onclick="templateBuilder.removeSelectedField(${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    removeSelectedField(index) {
        const removedField = this.selectedFields[index];
        this.selectedFields.splice(index, 1);

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
        const separator = document.getElementById('fieldSeparator').value;

        if (this.selectedFields.length === 0) {
            preview.innerHTML = '<span class="preview-text">Select fields to see preview</span>';
            return;
        }

        // Create sample data for preview
        const sampleData = {
            'vin': '1HGBH41JXMN109186',
            'stock': 'ST12345',
            'year': '2024',
            'make': 'Honda',
            'model': 'Civic',
            'trim': 'LX',
            'price': '$25,999',
            'msrp': '$27,500',
            'ext_color': 'Blue',
            'mileage': '12'
        };

        const previewText = this.selectedFields.map(field => sampleData[field.key] || field.label).join(separator);

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

        this.customCombinedFields[fieldKey] = {
            name: fieldName,
            fields: this.selectedFields.map(f => f.key),
            separator: separator,
            label: fieldName
        };

        // Re-setup drag handlers for the new field
        this.setupFieldDragHandlers();

        // Close modal
        this.closeConcatenationModal();

        console.log('[TEMPLATE BUILDER] Created combined field:', fieldKey, this.customCombinedFields[fieldKey]);
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
    // Debug: Check if template builder panel exists
    const panel = document.getElementById('template-builder-panel');
    console.log('[TEMPLATE BUILDER DEBUG] Panel found:', !!panel);
    if (panel) {
        console.log('[TEMPLATE BUILDER DEBUG] Panel classes:', panel.className);
        console.log('[TEMPLATE BUILDER DEBUG] Panel display style:', getComputedStyle(panel).display);

        // Check if the create button exists at this time
        const createBtn = document.getElementById('createCombinedFieldBtn');
        console.log('[TEMPLATE BUILDER DEBUG] createCombinedFieldBtn found at DOM ready:', !!createBtn);

        templateBuilder = new TemplateBuilder();
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

// Export for global access
window.templateBuilder = templateBuilder;