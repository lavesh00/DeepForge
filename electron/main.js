/**
 * DeepForge Electron Main Process
 * VS Code-like foundation with agent-first interface
 */

// Only require Electron if running in Electron context
let app, BrowserWindow, ipcMain, Menu;
try {
    const electron = require('electron');
    app = electron.app;
    BrowserWindow = electron.BrowserWindow;
    ipcMain = electron.ipcMain;
    Menu = electron.Menu;
} catch (e) {
    console.error('Electron not available. This file must be run with Electron.');
    process.exit(1);
}

const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let apiServerProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
            webSecurity: false
        },
        titleBarStyle: 'hiddenInset',
        backgroundColor: '#1e1e1e'
    });

    // Load the VS Code-like UI
    const htmlPath = path.join(__dirname, '..', 'interface', 'ui', 'electron', 'index.html');
    mainWindow.loadFile(htmlPath);

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Create application menu
    createMenu();
}

function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                { label: 'New File', accelerator: 'CmdOrCtrl+N', click: () => sendToRenderer('menu:new-file') },
                { label: 'Open File', accelerator: 'CmdOrCtrl+O', click: () => sendToRenderer('menu:open-file') },
                { label: 'Open Folder', accelerator: 'CmdOrCtrl+K CmdOrCtrl+O', click: () => sendToRenderer('menu:open-folder') },
                { type: 'separator' },
                { label: 'Save', accelerator: 'CmdOrCtrl+S', click: () => sendToRenderer('menu:save') },
                { label: 'Save As', accelerator: 'CmdOrCtrl+Shift+S', click: () => sendToRenderer('menu:save-as') }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { label: 'Undo', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
                { label: 'Redo', accelerator: 'CmdOrCtrl+Shift+Z', role: 'redo' },
                { type: 'separator' },
                { label: 'Cut', accelerator: 'CmdOrCtrl+X', role: 'cut' },
                { label: 'Copy', accelerator: 'CmdOrCtrl+C', role: 'copy' },
                { label: 'Paste', accelerator: 'CmdOrCtrl+V', role: 'paste' },
                { type: 'separator' },
                { label: 'Find', accelerator: 'CmdOrCtrl+F', click: () => sendToRenderer('menu:find') },
                { label: 'Replace', accelerator: 'CmdOrCtrl+H', click: () => sendToRenderer('menu:replace') }
            ]
        },
        {
            label: 'View',
            submenu: [
                { label: 'Toggle Composer', accelerator: 'CmdOrCtrl+I', click: () => sendToRenderer('menu:toggle-composer') },
                { label: 'Toggle Chat', accelerator: 'CmdOrCtrl+L', click: () => sendToRenderer('menu:toggle-chat') },
                { label: 'Command Palette', accelerator: 'CmdOrCtrl+Shift+P', click: () => sendToRenderer('menu:command-palette') },
                { type: 'separator' },
                { label: 'Toggle Agent Sidebar', accelerator: 'CmdOrCtrl+B', click: () => sendToRenderer('menu:toggle-sidebar') },
                { label: 'Toggle Terminal', accelerator: 'Ctrl+`', click: () => sendToRenderer('menu:toggle-terminal') },
                { type: 'separator' },
                { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: () => mainWindow.reload() }
            ]
        },
        {
            label: 'Agent',
            submenu: [
                { label: 'Inline Edit', accelerator: 'CmdOrCtrl+K', click: () => sendToRenderer('menu:inline-edit') },
                { label: 'Run Agent', accelerator: 'CmdOrCtrl+Enter', click: () => sendToRenderer('menu:run-agent') },
                { label: 'Stop Agent', accelerator: 'CmdOrCtrl+Shift+Enter', click: () => sendToRenderer('menu:stop-agent') },
                { type: 'separator' },
                { label: 'Agent Settings', click: () => sendToRenderer('menu:agent-settings') }
            ]
        },
        {
            label: 'Help',
            submenu: [
                { label: 'About DeepForge', click: () => sendToRenderer('menu:about') }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

function sendToRenderer(channel, data) {
    if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send(channel, data);
    }
}

// Start API server
function startApiServer() {
    const projectRoot = path.join(__dirname, '..');
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    
    console.log(`Starting API server with ${pythonCmd}...`);
    
    apiServerProcess = spawn(pythonCmd, ['-m', 'interface.api.server'], {
        cwd: projectRoot,
        stdio: 'inherit',
        shell: process.platform === 'win32'
    });

    apiServerProcess.on('error', (err) => {
        console.error('Failed to start API server:', err);
    });

    apiServerProcess.on('exit', (code) => {
        if (code !== null && code !== 0) {
            console.error(`API server exited with code ${code}`);
        }
    });
}

// IPC handlers (only register if ipcMain is available)
if (ipcMain) {
    ipcMain.handle('api:request', async (event, { method, path, body }) => {
        try {
            // Use native fetch (Node 18+) or HTTP module
            const http = require('http');
            const url = require('url');
            
            return new Promise((resolve) => {
                const parsedUrl = url.parse(`http://localhost:8080${path}`);
                const options = {
                    hostname: parsedUrl.hostname,
                    port: parsedUrl.port || 8080,
                    path: parsedUrl.path,
                    method: method,
                    headers: { 'Content-Type': 'application/json' }
                };
                
                const req = http.request(options, (res) => {
                    let data = '';
                    res.on('data', (chunk) => { data += chunk; });
                    res.on('end', () => {
                        try {
                            const jsonData = JSON.parse(data);
                            resolve({ success: true, data: jsonData });
                        } catch (e) {
                            resolve({ success: false, error: 'Invalid JSON response' });
                        }
                    });
                });
                
                req.on('error', (error) => {
                    resolve({ success: false, error: error.message });
                });
                
                if (body) {
                    req.write(JSON.stringify(body));
                }
                req.end();
            });
        } catch (error) {
            return { success: false, error: error.message };
        }
    });
}

ipcMain.handle('workspace:open', async (event, folderPath) => {
    // Handle workspace opening
    return { success: true, path: folderPath };
});

ipcMain.handle('file:read', async (event, filePath) => {
    const fs = require('fs').promises;
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return { success: true, content };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('file:write', async (event, { filePath, content }) => {
    const fs = require('fs').promises;
    try {
        await fs.writeFile(filePath, content, 'utf-8');
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

app.whenReady().then(() => {
    startApiServer();
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (apiServerProcess) {
        apiServerProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

