const electron = require('electron');
const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;
const path = require('path');
const os = require('os');
//electron.crashReporter.start();

var mainWindow = null;
var mapWindow = null;
var procStarted = false;

app.on('window-all-closed', function() {
  app.quit();
});

app.on('ready', function() {

  mainWindow = new BrowserWindow({width: 800, height: 600});
  mainWindow.loadURL('file://' + __dirname + '/login.html');
  //mainWindow.openDevTools();

  mainWindow.on('closed', function() {
    mainWindow = null;
  });

  logData('hi')

});

function logData(str){
  console.log(str);
  // if(mainWindow){
  //   mainWindow.webContents.executeJavaScript('console.log(unescape("'+escape(str)+'"))');
  // }
  // if(mapWindow){
  //   mapWindow.webContents.executeJavaScript('console.log(unescape("'+escape(str)+'"))');
  // }
}

ipcMain.on('startPython', function(event, auth, code, lat, long) {
  if (!procStarted) {
    logData('Starting Python process...');
    startPython(auth, code, lat, long);
    mainWindow.close();
  }
  procStarted = true;
});

function startPython(auth, code, lat, long) {

  mapWindow = new BrowserWindow({width: 800, height: 600, webPreferences: {
    nodeIntegration: false
  }});
  mapWindow.loadURL('file://' + __dirname + '/loading.html');
  //mapWindow.openDevTools();

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
      port
    ];
    // console.log(cmdLine);
    logData('Maps path: ' + path.join(__dirname, 'map'));
    logData('python ' + cmdLine.join(' '))

    var pythonCmd = 'python';
    if (os.platform() == 'win32') {
      pythonCmd = path.join(__dirname, 'pywin', 'python.exe');
    }

    var subpy = require('child_process').spawn(pythonCmd, cmdLine, {
      cwd: path.join(__dirname, 'map')
    });

    // subpy.stdout.on('data', (data) => {
    //   logData(`Python: ${data}`);
    // });
    // subpy.stderr.on('data', (data) => {
    //   logData(`Python: ${data}`);
    // });

    var rq = require('request-promise');
    var mainAddr = 'http://localhost:' + port;

    var openWindow = function(){
      mapWindow.loadURL(mainAddr);
      mapWindow.on('closed', function() {
        mapWindow = null;
        subpy.kill('SIGINT');
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

