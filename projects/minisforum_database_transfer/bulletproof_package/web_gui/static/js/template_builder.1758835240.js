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