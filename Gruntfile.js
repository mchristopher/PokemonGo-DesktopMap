// var path = require('path');

// module.exports = function(grunt) {

//   require('load-grunt-tasks')(grunt);

//   grunt.loadNpmTasks('grunt-electron-installer');

//   grunt.initConfig({
//       'create-windows-installer': {
//         ia32: {
//           appDirectory: path.join(path.resolve(), 'Pokemon GO Live Map-win32-ia32'),
//           outputDirectory: path.join(path.resolve(), 'win32output'),
//           title: 'Pokemon GO Live Map',
//           exe: "Pokemon GO Live Map.exe",
//           setupIcon: path.join(path.resolve(), 'pokemon.ico'),
//           iconUrl: 'https://raw.githubusercontent.com/mchristopher/PokemonGo-DesktopMap/master/pokemon.ico',
//           loadingGif: path.join(path.resolve(), 'installing.gif')
//         }
//       }
//   });

//   grunt.registerTask('default', ['create-windows-installer']);

// };


const os = require('os');
var path = require('path');

module.exports = function(grunt) {

  require('load-grunt-tasks')(grunt);

  grunt.loadNpmTasks('grunt-electron-installer');
  grunt.loadNpmTasks('grunt-electron');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-compress');

  var appConfig = {
    name: require('./package.json').name,
    version: require('./package.json').version || '0.0.1',
    author: require('./package.json').author,
  };

  grunt.initConfig({
    clean: [path.join(path.resolve(), 'dist')],
    'create-windows-installer': {
      ia32: {
        appDirectory: path.join(path.resolve(), 'dist', 'GEMS-win32-ia32'),
        outputDirectory: path.join(path.resolve(), 'dist', 'GEMS-win32-installer'),
        title: 'GEMS',
        exe: "GEMS.exe",
        setupIcon: path.join(path.resolve(), 'pokemon.ico'),
        iconUrl: 'http://gems-online.cryptkeypr.com/GEMS.ico',
        loadingGif: path.join(path.resolve(), 'installing.gif'),
        productName: 'GEMS'
      }
    },
    'electron': {
      macosBuild: {
        options: {
          name: 'GEMS',
          dir: 'app',
          out: 'dist',
          overwrite: true,
          asar: true,
          version: '1.3.3',
          platform: 'darwin',
          arch: 'x64',
          'app-version': appConfig.version,
          icon: path.join(path.resolve(), 'pokemon.icns')
        }
      },
      win32Build: {
        options: {
          name: 'GEMS',
          dir: 'app',
          out: 'dist',
          overwrite: true,
          asar: true,
          version: '1.3.3',
          platform: 'win32',
          arch: 'ia32',
          'app-copyright': '© 2012-2016 Project CloudKey Inc. All rights reserved. KEYPR and GEMS are trademarks of Project CloudKey Inc.',
          'app-version': appConfig.version,
          icon: path.join(path.resolve(), 'pokemon.ico'),
          'version-string': {
            'CompanyName': appConfig.author,
            'FileDescription': 'KEYPR GEMS',
            'ProductName': 'GEMS',
            'OriginalFilename': 'KEYPR GEMS.exe'
          }
        }
      }
    },
    compress: {
      macOsx: {
        options: {
          archive: path.join(path.resolve(), 'dist', 'KEYPR-GEMS-OSX.zip'),
          level: 9
        },
        files: [{
          cwd: path.join(path.resolve(), 'dist', 'GEMS-darwin-x64', 'GEMS.app'),
          src: ['**'],
          dest: 'GEMS.app/',
          expand: true
        }]
      }
    }
  });

  grunt.registerTask('default', [
    'clean',
    'electron',
    'create-windows-installer',
    'compress'
  ]);

};