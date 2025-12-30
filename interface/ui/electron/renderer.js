/**
 * DeepForge Renderer Process
 * VS Code-like UI with agent-first interface
 */

const { ipcRenderer } = require('electron');
const API_BASE = 'http://localhost:8080/api';

// Wait for API server to be ready
let apiReady = false;
async function waitForAPI() {
    for (let i = 0; i < 10; i++) {
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (response.ok) {
                apiReady = true;
                return;
            }
        } catch (e) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    console.warn('API server not ready, some features may not work');
}
waitForAPI();

// Monaco Editor instance
let monacoEditor = null;
let currentWorkspace = null;
let activeAgents = [];

// Initialize Monaco Editor (using CDN loader)
function initMonaco() {
    const monacoContainer = document.getElementById('monaco-container');
    if (!monacoContainer) {
        console.warn('monaco-container not found, skipping Monaco init');
        return;
    }
    
    // Wait for require to be available (loaded via script tag in HTML)
    function tryInit() {
        if (typeof require !== 'undefined' && require.config) {
            try {
                require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
                require(['vs/editor/editor.main'], () => {
                    try {
                        monacoEditor = monaco.editor.create(monacoContainer, {
                            value: '// Welcome to DeepForge\n// Press Cmd+K for inline edit, Cmd+I for Composer',
                            language: 'python',
                            theme: 'vs-dark',
                            automaticLayout: true,
                            minimap: { enabled: true },
                            fontSize: 14,
                            lineNumbers: 'on',
                            wordWrap: 'on'
                        });
                        console.log('Monaco editor initialized');
                        setupKeybindings();
                    } catch (error) {
                        console.error('Failed to create Monaco editor:', error);
                    }
                });
            } catch (error) {
                console.error('Failed to configure Monaco require:', error);
            }
        } else {
            // Retry after a short delay
            setTimeout(tryInit, 100);
        }
    }
    
    // Start trying after a short delay to ensure loader.js is loaded
    setTimeout(tryInit, 500);
}

// Setup keybindings
function setupKeybindings() {
    document.addEventListener('keydown', (e) => {
        const isMac = process.platform === 'darwin';
        const cmdOrCtrl = isMac ? e.metaKey : e.ctrlKey;

        // Cmd+K: Inline edit
        if (cmdOrCtrl && e.key === 'k' && !e.shiftKey) {
            e.preventDefault();
            showInlineEdit();
        }

        // Cmd+I: Toggle Composer
        if (cmdOrCtrl && e.key === 'i' && !e.shiftKey) {
            e.preventDefault();
            toggleComposer();
        }

        // Cmd+L: Toggle Chat
        if (cmdOrCtrl && e.key === 'l' && !e.shiftKey) {
            e.preventDefault();
            toggleComposer(); // Composer includes chat
        }

        // Cmd+Shift+P: Command Palette
        if (cmdOrCtrl && e.shiftKey && e.key === 'P') {
            e.preventDefault();
            showCommandPalette();
        }

        // Cmd+B: Toggle Sidebar
        if (cmdOrCtrl && e.key === 'b' && !e.shiftKey) {
            e.preventDefault();
            toggleSidebar();
        }
    });
}

// Activity bar handlers
function setupActivityBar() {
    const items = document.querySelectorAll('.activity-item');
    console.log(`Found ${items.length} activity items`);
    
    items.forEach(item => {
        item.addEventListener('click', (e) => {
            console.log('Activity item clicked:', item.dataset.view);
            e.preventDefault();
            e.stopPropagation();
            
            document.querySelectorAll('.activity-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            const view = item.dataset.view;
            if (view) {
                document.querySelectorAll('.sidebar-view').forEach(v => v.classList.remove('active'));
                const targetView = document.getElementById(`${view}-view`);
                if (targetView) {
                    targetView.classList.add('active');
                } else {
                    console.warn(`View ${view}-view not found`);
                }
            }
        });
    });
}

// Composer Panel
function toggleComposer() {
    const panel = document.getElementById('composer-panel');
    panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
}

document.getElementById('close-composer')?.addEventListener('click', () => {
    document.getElementById('composer-panel').style.display = 'none';
});

// Composer input
document.getElementById('composer-send')?.addEventListener('click', async () => {
    const input = document.getElementById('composer-input');
    const query = input.value.trim();
    if (!query) return;

    // Add user message
    addMessage('user', query);
    input.value = '';

    // Call agent API
    try {
        const response = await fetch(`${API_BASE}/missions/default/agent/iterate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();
        
        // Add assistant response
        let responseText = `Status: ${data.status}\n`;
        if (data.tool_calls && data.tool_calls.length > 0) {
            responseText += `\nTool calls:\n${data.tool_calls.map(tc => `- ${tc.name}`).join('\n')}`;
        }
        if (data.tool_results) {
            responseText += `\n\nResults:\n${JSON.stringify(data.tool_results, null, 2)}`;
        }

        addMessage('assistant', responseText, data.tool_results);
    } catch (error) {
        addMessage('assistant', `Error: ${error.message}`, null);
    }
});

function addMessage(role, content, toolResults = null) {
    const bubbles = document.getElementById('message-bubbles');
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${role}`;
    
    let html = `<div>${escapeHtml(content)}</div>`;
    
    if (toolResults) {
        toolResults.forEach(result => {
            if (result.results) {
                html += `<div class="code-block">${escapeHtml(JSON.stringify(result.results, null, 2))}</div>`;
            }
        });
    }
    
    bubble.innerHTML = html;
    bubbles.appendChild(bubble);
    bubbles.scrollTop = bubbles.scrollHeight;
}

// Inline Edit Overlay
function showInlineEdit() {
    if (!monacoEditor) return;

    const selection = monacoEditor.getSelection();
    const selectedText = monacoEditor.getModel().getValueInRange(selection);
    
    if (!selectedText) {
        alert('Select code to edit');
        return;
    }

    const overlay = document.getElementById('inline-edit-overlay');
    overlay.style.display = 'flex';

    // Call inline edit API
    fetch(`${API_BASE}/inline/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            file_path: 'current_file.py', // Would get from active tab
            selected_code: selectedText,
            query: prompt('Describe the edit:') || 'Improve this code',
            context_lines: 500
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.diff) {
            displayDiff(data.diff);
        }
    })
    .catch(err => {
        document.getElementById('diff-preview').textContent = `Error: ${err.message}`;
    });
}

function displayDiff(diffText) {
    const preview = document.getElementById('diff-preview');
    const lines = diffText.split('\n');
    
    preview.innerHTML = lines.map(line => {
        if (line.startsWith('+')) {
            return `<div class="diff-line added">${escapeHtml(line)}</div>`;
        } else if (line.startsWith('-')) {
            return `<div class="diff-line removed">${escapeHtml(line)}</div>`;
        } else {
            return `<div class="diff-line">${escapeHtml(line)}</div>`;
        }
    }).join('');
}

document.getElementById('apply-edit')?.addEventListener('click', async () => {
    // Apply edit via API
    const response = await fetch(`${API_BASE}/inline/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            file_path: 'current_file.py',
            new_content: '...' // Would get from diff
        })
    });

    if (response.ok) {
        document.getElementById('inline-edit-overlay').style.display = 'none';
        // Reload file in editor
    }
});

document.getElementById('close-inline-edit')?.addEventListener('click', () => {
    document.getElementById('inline-edit-overlay').style.display = 'none';
});

// Command Palette
function showCommandPalette() {
    const palette = document.getElementById('command-palette');
    palette.style.display = 'block';
    document.getElementById('command-input').focus();
}

document.getElementById('command-input')?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const commands = [
        { id: 'new-file', label: 'New File', action: () => console.log('New file') },
        { id: 'open-file', label: 'Open File', action: () => console.log('Open file') },
        { id: 'run-agent', label: 'Run Agent', action: () => console.log('Run agent') },
        { id: 'toggle-composer', label: 'Toggle Composer', action: toggleComposer }
    ];

    const filtered = commands.filter(cmd => cmd.label.toLowerCase().includes(query));
    displayCommands(filtered);
});

function displayCommands(commands) {
    const list = document.getElementById('command-list');
    list.innerHTML = commands.map(cmd => 
        `<div class="command-item" onclick="${cmd.action}">${cmd.label}</div>`
    ).join('');
}

// Load workspace
async function loadWorkspace() {
    try {
        const response = await fetch(`${API_BASE}/missions`);
        const missions = await response.json();
        
        // Load file tree
        // This would be implemented based on workspace structure
    } catch (error) {
        console.error('Failed to load workspace:', error);
    }
}

// Load agents
async function loadAgents() {
    // This would load active agents from API
    // For now, placeholder
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Electron renderer initialized');
    
    // Initialize Monaco
    initMonaco();
    
    // Setup all event handlers
    setupActivityBar();
    
    // Setup composer handlers
    const composerSend = document.getElementById('composer-send');
    if (composerSend) {
        composerSend.addEventListener('click', async () => {
            console.log('Composer send clicked');
            const input = document.getElementById('composer-input');
            const query = input?.value.trim();
            if (!query) {
                console.warn('Empty query');
                return;
            }
            
            // Add user message
            addMessage('user', query);
            input.value = '';
            
            // Call agent API
            try {
                console.log('Calling API:', `${API_BASE}/missions/default/agent/iterate`);
                const response = await fetch(`${API_BASE}/missions/default/agent/iterate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('API response:', data);
                
                // Add assistant response
                let responseText = `Status: ${data.status || 'unknown'}\n`;
                if (data.tool_calls && data.tool_calls.length > 0) {
                    responseText += `\nTool calls:\n${data.tool_calls.map(tc => `- ${tc.name}`).join('\n')}`;
                }
                if (data.tool_results) {
                    responseText += `\n\nResults:\n${JSON.stringify(data.tool_results, null, 2)}`;
                }
                
                addMessage('assistant', responseText, data.tool_results);
            } catch (error) {
                console.error('API error:', error);
                addMessage('assistant', `Error: ${error.message}`, null);
            }
        });
    } else {
        console.warn('composer-send button not found');
    }
    
    // Setup close handlers
    const closeComposer = document.getElementById('close-composer');
    if (closeComposer) {
        closeComposer.addEventListener('click', () => {
            const panel = document.getElementById('composer-panel');
            if (panel) panel.style.display = 'none';
        });
    }
    
    const closeInlineEdit = document.getElementById('close-inline-edit');
    if (closeInlineEdit) {
        closeInlineEdit.addEventListener('click', () => {
            const overlay = document.getElementById('inline-edit-overlay');
            if (overlay) overlay.style.display = 'none';
        });
    }
    
    // Setup apply edit handler
    const applyEdit = document.getElementById('apply-edit');
    if (applyEdit) {
        applyEdit.addEventListener('click', async () => {
            console.log('Apply edit clicked');
            // Apply edit via API
            try {
                const response = await fetch(`${API_BASE}/inline/apply`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_path: 'current_file.py',
                        new_content: '...' // Would get from diff
                    })
                });
                
                if (response.ok) {
                    const overlay = document.getElementById('inline-edit-overlay');
                    if (overlay) overlay.style.display = 'none';
                    // Reload file in editor
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                console.error('Failed to apply edit:', error);
                alert(`Failed to apply edit: ${error.message}`);
            }
        });
    }
    
    loadWorkspace();
    loadAgents();
    
    console.log('All event handlers attached');
});

