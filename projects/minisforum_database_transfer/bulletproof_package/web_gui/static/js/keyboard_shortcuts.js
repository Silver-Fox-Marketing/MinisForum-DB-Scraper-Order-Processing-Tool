/**
 * Keyboard Shortcuts Module for Silver Fox Order Processing System
 * =================================================================
 *
 * Provides comprehensive keyboard navigation and shortcuts throughout the application
 *
 * @author Claude (Silver Fox Assistant)
 * @created September 2025
 */

class KeyboardShortcutManager {
    constructor() {
        this.shortcuts = new Map();
        this.isEnabled = true;
        this.helpVisible = false;
        this.currentContext = 'global';

        // Initialize shortcuts
        this.defineShortcuts();
        this.attachEventListeners();
        this.injectHelpModal();
        this.detectInitialContext();
    }

    detectInitialContext() {
        // Check which tab is currently active on page load
        const activeTab = document.querySelector('.sidebar-tab.active');
        if (activeTab && activeTab.dataset.tab) {
            this.currentContext = activeTab.dataset.tab;
            console.log(`[SHORTCUTS] Initial context detected: ${this.currentContext}`);
        }
    }

    defineShortcuts() {
        // Global Navigation Shortcuts - Match the actual tab structure
        this.registerShortcut('Alt+Q', {
            description: 'Go to Order Queue',
            category: 'Navigation',
            handler: () => this.switchTab('queue-management')
        });

        this.registerShortcut('Alt+D', {
            description: 'Go to Dealership Settings',
            category: 'Navigation',
            handler: () => this.switchTab('dealership-settings')
        });

        this.registerShortcut('Alt+S', {
            description: 'Go to Data Search',
            category: 'Navigation',
            handler: () => this.switchTab('data-search')
        });

        this.registerShortcut('Alt+T', {
            description: 'Go to Template Builder',
            category: 'Navigation',
            handler: () => this.switchTab('template-builder')
        });

        this.registerShortcut('Alt+Y', {
            description: 'Go to System Status',
            category: 'Navigation',
            handler: () => this.switchTab('system-status')
        });

        // Order Processing Shortcuts
        this.registerShortcut('Ctrl+N', {
            description: 'Create New Order',
            category: 'Orders',
            context: 'order-processing',
            handler: () => this.createNewOrder()
        });

        this.registerShortcut('Ctrl+Enter', {
            description: 'Submit Current Order',
            category: 'Orders',
            context: 'order-processing',
            handler: () => this.submitCurrentOrder()
        });

        this.registerShortcut('Ctrl+P', {
            description: 'Process Selected Orders',
            category: 'Orders',
            context: 'order-queue',
            handler: () => this.processSelectedOrders()
        });

        this.registerShortcut('Delete', {
            description: 'Delete Selected Orders',
            category: 'Orders',
            context: 'order-queue',
            handler: () => this.deleteSelectedOrders()
        });

        // Template Builder Shortcuts
        this.registerShortcut('Ctrl+S', {
            description: 'Save Template',
            category: 'Template Builder',
            context: 'template-builder',
            handler: () => this.saveTemplate()
        });

        this.registerShortcut('Ctrl+Shift+N', {
            description: 'New Template',
            category: 'Template Builder',
            context: 'template-builder',
            handler: () => this.newTemplate()
        });

        this.registerShortcut('Ctrl+Shift+C', {
            description: 'Create Combined Field',
            category: 'Template Builder',
            context: 'template-builder',
            handler: () => this.openCombinedFieldModal()
        });

        // Scraper Control Shortcuts
        this.registerShortcut('F5', {
            description: 'Refresh Scraper Status',
            category: 'Scraper',
            context: 'scraper-status',
            handler: () => this.refreshScraperStatus()
        });

        this.registerShortcut('Ctrl+R', {
            description: 'Run Selected Scrapers',
            category: 'Scraper',
            context: 'scraper-status',
            handler: () => this.runSelectedScrapers()
        });

        // Modal and Dialog Shortcuts
        this.registerShortcut('Escape', {
            description: 'Close Active Modal/Dialog',
            category: 'General',
            handler: () => this.closeActiveModal()
        });

        // Search and Filter Shortcuts
        this.registerShortcut('Ctrl+F', {
            description: 'Focus Search Field',
            category: 'General',
            handler: () => this.focusSearch()
        });

        this.registerShortcut('Ctrl+Shift+F', {
            description: 'Clear All Filters',
            category: 'General',
            handler: () => this.clearFilters()
        });

        // Selection Shortcuts
        this.registerShortcut('Ctrl+A', {
            description: 'Select All Items',
            category: 'Selection',
            handler: (e) => this.selectAll(e)
        });

        this.registerShortcut('Ctrl+Shift+A', {
            description: 'Deselect All Items',
            category: 'Selection',
            handler: () => this.deselectAll()
        });

        // Queue Management Shortcuts (only active in queue-management context)
        this.registerShortcut('Alt+P', {
            description: 'Process Queue',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.processQueue()
        });

        this.registerShortcut('Alt+K', {
            description: 'Clear Queue',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.clearQueue()
        });

        this.registerShortcut('Alt+M', {
            description: 'Toggle Testing Mode',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.toggleTestingMode()
        });

        this.registerShortcut('/', {
            description: 'Focus Dealership Search',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.focusDealershipSearch()
        });

        // Day selection shortcuts
        this.registerShortcut('1', {
            description: 'Select Monday',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.selectDay('monday')
        });

        this.registerShortcut('2', {
            description: 'Select Tuesday',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.selectDay('tuesday')
        });

        this.registerShortcut('3', {
            description: 'Select Wednesday',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.selectDay('wednesday')
        });

        this.registerShortcut('4', {
            description: 'Select Thursday',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.selectDay('thursday')
        });

        this.registerShortcut('5', {
            description: 'Select Friday',
            category: 'Queue Management',
            context: 'queue-management',
            handler: () => this.selectDay('friday')
        });

        // Help and Documentation
        this.registerShortcut('F1', {
            description: 'Show Keyboard Shortcuts Help',
            category: 'Help',
            handler: () => this.toggleHelp()
        });

        this.registerShortcut('?', {
            description: 'Show Keyboard Shortcuts Help',
            category: 'Help',
            handler: () => this.toggleHelp()
        });

        // Dark Mode Toggle
        this.registerShortcut('Alt+Shift+D', {
            description: 'Toggle Dark Mode',
            category: 'General',
            handler: () => this.toggleDarkMode()
        });

        // Quick Actions
        this.registerShortcut('Ctrl+,', {
            description: 'Open Settings',
            category: 'General',
            handler: () => this.openSettings()
        });

        // Navigation within lists
        this.registerShortcut('ArrowUp', {
            description: 'Navigate Up in List',
            category: 'Navigation',
            handler: (e) => this.navigateList(e, 'up')
        });

        this.registerShortcut('ArrowDown', {
            description: 'Navigate Down in List',
            category: 'Navigation',
            handler: (e) => this.navigateList(e, 'down')
        });

        this.registerShortcut('Enter', {
            description: 'Open/Edit Selected Item',
            category: 'Navigation',
            handler: (e) => this.openSelectedItem(e)
        });

        this.registerShortcut('Space', {
            description: 'Toggle Selection of Current Item',
            category: 'Selection',
            handler: (e) => this.toggleItemSelection(e)
        });
    }

    registerShortcut(key, options) {
        this.shortcuts.set(key.toLowerCase(), {
            key: key,
            ...options
        });
    }

    attachEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (!this.isEnabled) return;

            // Check if user is typing in an input field (unless it's a global shortcut)
            const activeElement = document.activeElement;
            const isTyping = activeElement &&
                (activeElement.tagName === 'INPUT' ||
                 activeElement.tagName === 'TEXTAREA' ||
                 activeElement.contentEditable === 'true');

            const keyCombo = this.getKeyCombo(e);
            const shortcut = this.shortcuts.get(keyCombo.toLowerCase());

            if (shortcut) {
                // Debug logging for troubleshooting
                console.log(`[SHORTCUTS] Key: ${keyCombo}, Context: ${this.currentContext}, IsTyping: ${isTyping}, Shortcut context: ${shortcut.context}`);

                // Allow certain shortcuts even when typing
                const allowedWhileTyping = ['escape', 'f1', '?'];
                if (isTyping && !allowedWhileTyping.includes(keyCombo.toLowerCase())) {
                    console.log(`[SHORTCUTS] Blocked - user is typing in input field`);
                    return;
                }

                // Check context
                if (shortcut.context && shortcut.context !== this.currentContext && shortcut.context !== 'global') {
                    console.log(`[SHORTCUTS] Blocked - wrong context. Expected: ${shortcut.context}, Current: ${this.currentContext}`);
                    return;
                }

                console.log(`[SHORTCUTS] Executing shortcut: ${shortcut.description}`);
                e.preventDefault();
                shortcut.handler(e);
            }
        });

        // Update context when tab changes
        document.addEventListener('tabChanged', (e) => {
            this.currentContext = e.detail.tabId;
        });

        // Also listen for when tabs are clicked to update context
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = e.currentTarget.dataset.tab;
                if (tabId) {
                    this.currentContext = tabId;
                    console.log(`[SHORTCUTS] Context changed to: ${tabId}`);
                }
            });
        });
    }

    getKeyCombo(e) {
        const keys = [];

        if (e.ctrlKey) keys.push('Ctrl');
        if (e.altKey) keys.push('Alt');
        if (e.shiftKey) keys.push('Shift');
        if (e.metaKey) keys.push('Meta');

        // Special keys
        const specialKeys = {
            'Escape': 'Escape',
            'Enter': 'Enter',
            'Delete': 'Delete',
            'Backspace': 'Backspace',
            'Tab': 'Tab',
            'Space': ' ',
            'ArrowUp': 'ArrowUp',
            'ArrowDown': 'ArrowDown',
            'ArrowLeft': 'ArrowLeft',
            'ArrowRight': 'ArrowRight',
            'F1': 'F1',
            'F2': 'F2',
            'F3': 'F3',
            'F4': 'F4',
            'F5': 'F5',
            'F6': 'F6',
            'F7': 'F7',
            'F8': 'F8',
            'F9': 'F9',
            'F10': 'F10',
            'F11': 'F11',
            'F12': 'F12'
        };

        if (specialKeys[e.key]) {
            keys.push(specialKeys[e.key]);
        } else if (e.key.length === 1) {
            keys.push(e.key.toUpperCase());
        }

        return keys.join('+');
    }

    // Navigation Handlers
    switchTab(tabId) {
        // Use the app object's switchTab method if available
        if (window.app && window.app.switchTab) {
            window.app.switchTab(tabId);
            console.log(`[SHORTCUTS] Switched to ${tabId} tab via app.switchTab`);
        } else {
            // Fallback: click the tab button directly
            const tabButton = document.querySelector(`[data-tab="${tabId}"]`);
            if (tabButton) {
                tabButton.click();
                console.log(`[SHORTCUTS] Switched to ${tabId} tab via click`);
            }
        }
    }

    // Order Processing Handlers
    createNewOrder() {
        const newOrderBtn = document.querySelector('#newOrderBtn');
        if (newOrderBtn) {
            newOrderBtn.click();
        }
    }

    submitCurrentOrder() {
        const submitBtn = document.querySelector('#submitOrderBtn');
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.click();
        }
    }

    processSelectedOrders() {
        const processBtn = document.querySelector('#processSelectedBtn');
        if (processBtn && !processBtn.disabled) {
            processBtn.click();
        }
    }

    deleteSelectedOrders() {
        const deleteBtn = document.querySelector('#deleteSelectedBtn');
        if (deleteBtn && !deleteBtn.disabled) {
            if (confirm('Delete selected orders?')) {
                deleteBtn.click();
            }
        }
    }

    // Template Builder Handlers
    saveTemplate() {
        if (window.templateBuilder) {
            window.templateBuilder.saveTemplate();
        }
    }

    newTemplate() {
        if (window.templateBuilder) {
            window.templateBuilder.createNewTemplate();
        }
    }

    openCombinedFieldModal() {
        if (window.openFieldConcatenationModal) {
            window.openFieldConcatenationModal();
        }
    }

    // Scraper Handlers
    refreshScraperStatus() {
        const refreshBtn = document.querySelector('#refreshScraperStatus');
        if (refreshBtn) {
            refreshBtn.click();
        } else {
            location.reload();
        }
    }

    runSelectedScrapers() {
        const runBtn = document.querySelector('#runSelectedScrapers');
        if (runBtn && !runBtn.disabled) {
            runBtn.click();
        }
    }

    // Modal Handlers
    closeActiveModal() {
        const modals = document.querySelectorAll('.modal[style*="display: flex"], .modal[style*="display: block"]');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }

    // Search and Filter Handlers
    focusSearch() {
        const searchFields = document.querySelectorAll('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"], #searchInput');
        if (searchFields.length > 0) {
            searchFields[0].focus();
            searchFields[0].select();
        }
    }

    clearFilters() {
        const clearBtn = document.querySelector('.clear-filters, #clearFiltersBtn');
        if (clearBtn) {
            clearBtn.click();
        }
    }

    // Selection Handlers
    selectAll(e) {
        // Prevent default browser behavior
        if (!e.target.matches('input, textarea')) {
            e.preventDefault();
            const checkboxes = document.querySelectorAll('.item-checkbox:not(:checked), input[type="checkbox"]:not(:checked)');
            checkboxes.forEach(cb => {
                if (!cb.disabled) cb.click();
            });
        }
    }

    deselectAll() {
        const checkboxes = document.querySelectorAll('.item-checkbox:checked, input[type="checkbox"]:checked');
        checkboxes.forEach(cb => cb.click());
    }

    // Dark Mode Handler
    toggleDarkMode() {
        if (window.toggleDarkMode) {
            window.toggleDarkMode();
        } else {
            document.body.dataset.theme = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', document.body.dataset.theme);
        }
    }

    // Settings Handler
    openSettings() {
        const settingsBtn = document.querySelector('#settingsBtn, .settings-button');
        if (settingsBtn) {
            settingsBtn.click();
        }
    }

    // Queue Management Handlers
    processQueue() {
        const processBtn = document.querySelector('#processQueueBtn');
        if (processBtn && !processBtn.disabled) {
            processBtn.click();
            console.log('[SHORTCUTS] Process queue triggered');
        }
    }

    clearQueue() {
        if (window.app && window.app.clearQueue) {
            window.app.clearQueue();
            console.log('[SHORTCUTS] Clear queue triggered');
        }
    }

    toggleTestingMode() {
        const testingToggle = document.querySelector('#modernTestingToggle');
        if (testingToggle) {
            testingToggle.click();
            console.log('[SHORTCUTS] Testing mode toggled');
        } else if (window.toggleTestingMode) {
            window.toggleTestingMode();
        }
    }

    focusDealershipSearch() {
        const searchInput = document.querySelector('#dealershipSearchInput');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
            console.log('[SHORTCUTS] Focused dealership search');
        }
    }

    selectDay(day) {
        const dayButton = document.querySelector(`[data-day="${day}"]`);
        if (dayButton) {
            dayButton.click();
            console.log(`[SHORTCUTS] Selected ${day}`);
        }
    }

    // List Navigation
    navigateList(e, direction) {
        const lists = document.querySelectorAll('.list-container, .table-container, tbody');
        // Implementation for navigating through lists with arrow keys
    }

    openSelectedItem(e) {
        if (!e.target.matches('input, textarea, button')) {
            const selected = document.querySelector('.item.selected, tr.selected');
            if (selected) {
                const editBtn = selected.querySelector('.edit-btn, .btn-edit');
                if (editBtn) editBtn.click();
            }
        }
    }

    toggleItemSelection(e) {
        if (!e.target.matches('input, textarea, button')) {
            e.preventDefault();
            const selected = document.querySelector('.item.selected, tr.selected');
            if (selected) {
                const checkbox = selected.querySelector('input[type="checkbox"]');
                if (checkbox) checkbox.click();
            }
        }
    }

    // Help Modal
    toggleHelp() {
        if (this.helpVisible) {
            this.hideHelp();
        } else {
            this.showHelp();
        }
    }

    showHelp() {
        const modal = document.getElementById('keyboardShortcutsModal');
        if (modal) {
            modal.style.display = 'flex';
            this.helpVisible = true;
            this.populateHelpContent();
        }
    }

    hideHelp() {
        const modal = document.getElementById('keyboardShortcutsModal');
        if (modal) {
            modal.style.display = 'none';
            this.helpVisible = false;
        }
    }

    populateHelpContent() {
        const container = document.getElementById('shortcutsContent');
        if (!container) return;

        const categories = {};

        // Group shortcuts by category
        this.shortcuts.forEach((shortcut) => {
            const category = shortcut.category || 'General';
            if (!categories[category]) {
                categories[category] = [];
            }
            categories[category].push(shortcut);
        });

        // Generate HTML
        let html = '';
        Object.keys(categories).sort().forEach(category => {
            html += `
                <div class="shortcut-category">
                    <h3>${category}</h3>
                    <div class="shortcut-list">
            `;

            categories[category].forEach(shortcut => {
                html += `
                    <div class="shortcut-item">
                        <kbd>${shortcut.key}</kbd>
                        <span>${shortcut.description}</span>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    injectHelpModal() {
        const modalHTML = `
            <div class="modal" id="keyboardShortcutsModal" style="display: none;">
                <div class="modal-content" style="max-width: 800px; max-height: 80vh; overflow-y: auto;">
                    <div class="modal-header">
                        <h2><i class="fas fa-keyboard"></i> Keyboard Shortcuts</h2>
                        <button class="modal-close" onclick="keyboardShortcuts.hideHelp()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div id="shortcutsContent"></div>
                    </div>
                    <div class="modal-footer">
                        <p class="help-hint">Press <kbd>?</kbd> or <kbd>F1</kbd> to toggle this help</p>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // Enable/Disable shortcuts
    enable() {
        this.isEnabled = true;
    }

    disable() {
        this.isEnabled = false;
    }

    // Debug method to test shortcuts
    testShortcut(key) {
        const shortcut = this.shortcuts.get(key.toLowerCase());
        if (shortcut) {
            console.log(`[SHORTCUTS] Testing shortcut: ${key} -> ${shortcut.description}`);
            console.log(`[SHORTCUTS] Current context: ${this.currentContext}, Required context: ${shortcut.context}`);
            shortcut.handler();
        } else {
            console.log(`[SHORTCUTS] No shortcut found for: ${key}`);
            console.log(`[SHORTCUTS] Available shortcuts:`, Array.from(this.shortcuts.keys()));
        }
    }

    // Debug method to manually set context
    setContext(context) {
        this.currentContext = context;
        console.log(`[SHORTCUTS] Context manually set to: ${context}`);
    }
}

// Initialize keyboard shortcuts when DOM is ready and app is available
document.addEventListener('DOMContentLoaded', () => {
    // Wait for app to be available before initializing shortcuts
    const initShortcuts = () => {
        if (window.app) {
            window.keyboardShortcuts = new KeyboardShortcutManager();
            console.log('[SHORTCUTS] Keyboard shortcuts initialized with app support');
        } else {
            // App not ready yet, try again in 100ms
            setTimeout(initShortcuts, 100);
        }
    };

    initShortcuts();
});

// Export for use in other modules
window.KeyboardShortcutManager = KeyboardShortcutManager;