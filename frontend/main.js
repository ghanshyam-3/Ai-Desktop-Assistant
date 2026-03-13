const { app, BrowserWindow, Tray, Menu, screen } = require('electron');
const path = require('path');

let mainWindow;
let tray;

function createWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    mainWindow = new BrowserWindow({
        width: 600,
        height: 600,
        x: width - 620, // Bottom Right corner
        y: height - 650,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
        },
    });

    // Load Vite Dev Server
    mainWindow.loadURL('http://localhost:5173');

    // mainWindow.webContents.openDevTools(); // Debugging

    mainWindow.on('closed', () => (mainWindow = null));
}

function createTray() {
    // Use a placeholder icon or ensure path exists
    const iconPath = path.join(__dirname, 'public', 'tray-icon.png');
    // Note: We need an actual icon file, otherwise this might fail or be invisible. 
    // For now, we'll try to start without it or handle error if needed, 
    // but Electron usually requires a valid path for Tray.
    // We'll skip Tray creation if icon is missing in this basic version, 
    // or use empty string which might show default.

    // tray = new Tray(iconPath);
    // const contextMenu = Menu.buildFromTemplate([
    //   { label: 'Show', click: () => mainWindow.show() },
    //   { label: 'Exit', click: () => app.quit() },
    // ]);
    // tray.setToolTip('Voice Assistant');
    // tray.setContextMenu(contextMenu);
}

app.on('ready', () => {
    createWindow();
    // createTray(); 
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) createWindow();
});
