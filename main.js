const electron = require('electron');
const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;
const Menu = electron.Menu;
const path = require('path');
const os = require('os');
const autoUpdater = electron.autoUpdater;
//electron.crashReporter.start();

var platform = os.platform() + '_' + os.arch();
var version = app.getVersion();

var mainWindow = null;
var procStarted = false;
var subpy = null;
var mainAddr;

try {
  autoUpdater.setFeedURL('https://pokemon-go-updater.mike.ai/update/'+platform+'/'+version);
} catch (e) {}

autoUpdater.on('update-downloaded', function(){
  mainWindow.webContents.send('update-ready');
});

// Setup menu bar
var template = [{
    label: "Application",
    submenu: [{
        label: "About Application",
        selector: "orderFrontStandardAboutPanel:"
    }, {
        type: "separator"
    }, {
        label: "Quit",
        accelerator: "Command+Q",
        click: function() {
            app.quit();
        }
    }]
}, {
    label: "Edit",
    submenu: [{
        label: "Undo",
        accelerator: "CmdOrCtrl+Z",
        selector: "undo:"
    }, {
        label: "Redo",
        accelerator: "Shift+CmdOrCtrl+Z",
        selector: "redo:"
    }, {
        type: "separator"
    }, {
        label: "Cut",
        accelerator: "CmdOrCtrl+X",
        selector: "cut:"
    }, {
        label: "Copy",
        accelerator: "CmdOrCtrl+C",
        selector: "copy:"
    }, {
        label: "Paste",
        accelerator: "CmdOrCtrl+V",
        selector: "paste:"
    }, {
        label: "Select All",
        accelerator: "CmdOrCtrl+A",
        selector: "selectAll:"
    }]
},
{
    label: "Tools",
    submenu: [
      {
        label: "Refresh",
        accelerator: "CmdOrCtrl+R",
        click(item, focusedWindow) {
          if (focusedWindow) focusedWindow.reload();
        }
      },
      {
        label: 'Toggle Developer Tools',
        accelerator: process.platform === 'darwin' ? 'Alt+Command+I' : 'Ctrl+Shift+I',
        click(item, focusedWindow) {
          if (focusedWindow)
            focusedWindow.webContents.toggleDevTools();
        }
      }
    ]
}
];


app.on('window-all-closed', function() {
  if (subpy && subpy.pid) {
    killProcess(subpy.pid);
  }
  app.quit();
});

app.on('ready', function() {

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));

  mainWindow = new BrowserWindow({width: 800, height: 600, minWidth: 700, minHeight: 500});
  mainWindow.loadURL('file://' + __dirname + '/login.html');

  mainWindow.on('closed', function() {
    mainWindow = null;
    if (subpy && subpy.pid) {
      killProcess(subpy.pid);
    }
  });
});

function logData(str){
  console.log(str);
  // if(mainWindow){
  //   mainWindow.webContents.executeJavaScript('console.log(unescape("'+escape(str)+'"))');
  // }
}

function killProcess(pid) {
  try {
    process.kill(-pid, 'SIGINT');
  } catch (e) {
    process.kill(pid, 'SIGINT');
  }
}

ipcMain.on('startPython', function(event, auth, code, lat, long) {
  if (!procStarted) {
    logData('Starting Python process...');
    startPython(auth, code, lat, long);
  }
  procStarted = true;
});

ipcMain.on('getServer', function(event) {
  event.sender.send('server-up', mainAddr);
});

ipcMain.on('installUpdate', function(event) {
  autoUpdater.quitAndInstall();
});

function startPython(auth, code, lat, long) {

  mainWindow.loadURL('file://' + __dirname + '/main.html');
  //mainWindow.openDevTools();

  // Find open port
  var portfinder = require('portfinder');
  portfinder.getPort(function (err, port) {

    logData('Got open port: ' + port);

    // Run python web server
    var cmdLine = [
      './example.py',
      '--auth_service',
      auth,
      '--token',
      code,
      '--location',
      lat + ',' + long,
      '--auto_refresh',
      '10',
      '--step-limit',
      '7',
      //'--display-pokestop',
      '--display-gym',
      '--port',
      port,
      '--parent_pid',
      process.pid
    ];
    // console.log(cmdLine);
    logData('Maps path: ' + path.join(__dirname, 'map'));
    logData('python ' + cmdLine.join(' '))

    var pythonCmd = 'python';
    if (os.platform() == 'win32') {
      pythonCmd = path.join(__dirname, 'pywin', 'python.exe');
    }

    subpy = require('child_process').spawn(pythonCmd, cmdLine, {
      cwd: path.join(__dirname, 'map'),
      detached: true
    });

    subpy.stdout.on('data', (data) => {
      logData(`Python: ${data}`);
    });
    subpy.stderr.on('data', (data) => {
      logData(`Python: ${data}`);
    });

    var rq = require('request-promise');
    mainAddr = 'http://localhost:' + port;

    var openWindow = function(){
      mainWindow.webContents.send('server-up', mainAddr);
      mainWindow.webContents.executeJavaScript(
        'serverUp("'+mainAddr+'")');
      mainWindow.on('closed', function() {
        mainWindow = null;
        if (subpy && subpy.pid) {
          killProcess(subpy.pid);
        }
        procStarted = false;
      });
    };

    var startUp = function(){
      rq(mainAddr)
        .then(function(htmlString){
          logData('server started!');
          openWindow();
        })
        .catch(function(err){
          //console.log('waiting for the server start...');
          startUp();
        });
    };

    startUp();

  });

};
