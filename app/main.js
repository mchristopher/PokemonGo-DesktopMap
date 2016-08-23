const electron = require('electron');
const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;
const Menu = electron.Menu;
const path = require('path');
const os = require('os');
const express = require('express');
const http = require('http');
const httpProxy = require('express-http-proxy');
const autoUpdater = electron.autoUpdater;
//electron.crashReporter.start();

var platform = os.platform() + '_' + os.arch();
var version = app.getVersion();

var mainWindow = null;
var procStarted = false;
var subpy = null;
var mainAddr;
var restarting = false;

if (handleSquirrelEvent()) {
  // squirrel event handled and app will exit in 1000ms, so don't do anything else
  return;
}

try {
  autoUpdater.setFeedURL('https://pokemon-go-updater.mike.ai/update/'+platform+'/'+version);
} catch (e) {console.log(e)}

autoUpdater.on('update-downloaded', function(){
  mainWindow.webContents.send('update-ready');
});

try {
  autoUpdater.checkForUpdates();
} catch (e) {}

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
  if (restarting) {
    return;
  }
  if (subpy && subpy.pid) {
    killProcess(subpy.pid);
  }
  app.quit();
});

app.on('ready', function() {

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));

  setupMainWindow();
});

function setupMainWindow() {
  restarting = false;

  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    minWidth: 700,
    minHeight: 500,
    webPreferences: {
      partition: 'persist:pogolivemap'
    }
  });
  mainWindow.loadURL('file://' + __dirname + '/login.html');

  mainWindow.on('closed', function() {
    mainWindow = null;
    if (subpy && subpy.pid) {
      killProcess(subpy.pid);
    }
  });
}

function logData(str){
  console.log(str);
  if (mainWindow){
    mainWindow.webContents.send('appLog', {'msg': `${str}`});
  }
}

function killProcess(pid) {
  try {
    process.kill(-pid, 'SIGINT');
    process.kill(-pid, 'SIGTERM');
  } catch (e) {
    try {
      process.kill(pid, 'SIGTERM');
    } catch (e) {}
  }
}

ipcMain.on('logout', function(event, auth, code, lat, long, opts) {
  restarting = true;
  if (procStarted) {
    logData('Killing Python process...');
    if (subpy && subpy.pid) {
      killProcess(subpy.pid);
    }
  }
  procStarted = false;
  mainWindow.close();
  setupMainWindow();
});

ipcMain.on('startPython', function(event, auth, code, lat, long, opts) {
  if (!procStarted) {
    logData('Starting Python process...');
    startPython(auth, code, lat, long, opts);
  }
  procStarted = true;
});

ipcMain.on('getServer', function(event) {
  event.sender.send('server-up', mainAddr);
});

ipcMain.on('installUpdate', function(event) {
  autoUpdater.quitAndInstall();
});

function startPython(auth, code, lat, long, opts) {

  mainWindow.loadURL('file://' + __dirname + '/main.html');
  //mainWindow.openDevTools();

  // Find open port
  var portfinder = require('portfinder');
  portfinder.getPort(function (err, py_port) {

    logData('Got open python port: ' + py_port);

    // Run python web server
    var cmdLine = [
      './run_map.py',
      '--cors',
      '--auth-service',
      auth,
      '--location=' +
        parseFloat(lat).toFixed(7) + ',' + parseFloat(long).toFixed(7),
      '--port',
      py_port,
      '--db',
      path.join(app.getPath('userData'), 'pogom.db')
    ];
    
    if (opts.is_public) {
      cmdLine.push('--host');
      cmdLine.push('0.0.0.0');
    }

    if (opts.fast_scan) {
      cmdLine.push('--num-threads');
      cmdLine.push('5');
    }

    if (opts.maps_api_key) {
      cmdLine.push('--gmaps-key');
      cmdLine.push(opts.maps_api_key);
    }

    if (auth == 'ptc' && opts.username) {
      cmdLine.push('--username');
      cmdLine.push(opts.username);
      cmdLine.push('--password');
      cmdLine.push(opts.password);
    }

    if (auth == 'google' && code) {
      cmdLine.push('--token');
      cmdLine.push(code);
    }

    // Add options

    cmdLine.push('--step-limit');
    if (opts.radius && opts.radius != '') {
      cmdLine.push(opts.radius);
    } else {
      cmdLine.push('7');
    }

    // console.log(cmdLine);
    logData('Maps path: ' + path.join(__dirname));
    logData('python ' + cmdLine.join(' '));

    var pythonCmd = 'python';
    if (os.platform() == 'win32') {
      pythonCmd = path.join(__dirname, 'pywin', 'python.exe');
    }

    subpy = require('child_process').spawn(pythonCmd, cmdLine, {
      cwd: path.join(__dirname),
      detached: true
    });

    subpy.stdout.on('data', (data) => {
      console.log(`Python: ${data}`);
      mainWindow.webContents.send('pythonLog', {'msg': `${data}`});
    });
    subpy.stderr.on('data', (data) => {
      console.log(`Python: ${data}`);
      mainWindow.webContents.send('pythonLog', {'msg': `${data}`});
    });

    var rq = require('request-promise');
    var pyAddr = 'http://localhost:' + py_port;

    var openWindow = function(){
      mainWindow.webContents.send('server-up', mainAddr);
      mainWindow.on('closed', function() {
        mainWindow = null;
        if (subpy && subpy.pid) {
          killProcess(subpy.pid);
        }
        procStarted = false;
      });
    };

    var setupExpress = function() {
      portfinder.getPort(function(err, express_port) {
        logData('Got open express port: ' + express_port);

        mainAddr = 'http://localhost:' + express_port;

        var express_app = express();

        express_app.use('/static', express.static('map/static'));
        express_app.use('/', httpProxy(pyAddr));
        express_app.listen(express_port, function () {
          console.log('Express listening on port ' + express_port);
        });

        startUpExpress();
      });
    };

    var startUpExpress = function(){
      rq(mainAddr)
        .then(function(htmlString){
          logData('Express server started!');
          openWindow();
        })
        .catch(function(err){
          //console.log('waiting for the server start...');
          startUpExpress();
        });
    };

    var startUpPython = function(){
      rq(pyAddr)
        .then(function(htmlString){
          logData('Python server started!');
          setupExpress();
        })
        .catch(function(err){
          //console.log('waiting for the server start...');
          startUpPython();
        });
    };

    startUpPython();

  });

};

function handleSquirrelEvent() {
  if (process.argv.length === 1) {
    return false;
  }

  const ChildProcess = require('child_process');

  const appFolder = path.resolve(process.execPath, '..');
  const rootPokeFolder = path.resolve(appFolder, '..');
  const updateDotExe = path.resolve(path.join(rootPokeFolder, 'Update.exe'));
  const exeName = path.basename(process.execPath);

  const spawn = function(command, args) {
    let spawnedProcess, error;

    try {
      spawnedProcess = ChildProcess.spawn(command, args, {detached: true});
    } catch (error) {}

    return spawnedProcess;
  };

  const spawnUpdate = function(args) {
    return spawn(updateDotExe, args);
  };

  const squirrelEvent = process.argv[1];
  switch (squirrelEvent) {
    case '--squirrel-install':
    case '--squirrel-updated':
      // Optionally do things such as:
      // - Add your .exe to the PATH
      // - Write to the registry for things like file associations and
      //   explorer context menus

      // Install desktop and start menu shortcuts
      spawnUpdate(['--createShortcut', exeName]);

      setTimeout(app.quit, 1000);
      return true;

    case '--squirrel-uninstall':
      // Undo anything you did in the --squirrel-install and
      // --squirrel-updated handlers

      // Remove desktop and start menu shortcuts
      spawnUpdate(['--removeShortcut', exeName]);

      setTimeout(app.quit, 1000);
      return true;

    case '--squirrel-obsolete':
      // This is called on the outgoing version of your app before
      // we update to the new version - it's the opposite of
      // --squirrel-updated

      app.quit();
      return true;
  }
};

