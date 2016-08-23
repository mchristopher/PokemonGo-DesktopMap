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

  var common_ignore_dir = [
    '/node_modules/grunt($|/)',
    '.DS_Store',
    '.gitignore',
    'ngrok-linux'
  ],
  mac_ignore_dir = [
    'ngrok-win32.exe',
    'pywin',
    'pylibs/win32'
  ],
  win_ignore_dir = [
    'ngrok-darwin',
    'pylibs/osx64'
  ];

  grunt.initConfig({
    clean: {
      dist: [path.join(path.resolve(), 'dist')],
      pyc: [path.join(path.resolve(), 'app', '**', '*.pyc')]
    },
    execute: {
      build_map_assets: {
        options: {
          cwd: path.join(path.resolve(), 'app', 'map')
        },
        src: ['npm install && npm run build']
      }
    },
    shell: {
      compressOsx: {
        command: [
          'cd dist/pokemon-go-map-darwin-x64',
          'mv "pokemon-go-map.app" "Pokemon GO Live Map.app"',
          'rm -fr LICENSE LICENSES.chromium.html version',
          'zip -9ryv ../PokemonGoMap-OSX.zip . >/dev/null'
        ].join('&&')
      }
    },
    'create-windows-installer': {
      ia32: {
        appDirectory: path.join(path.resolve(), 'dist', 'pokemon-go-map-win32-ia32'),
        outputDirectory: path.join(path.resolve(), 'dist', 'pokemon-go-map-win32-installer'),
        title: 'Pokemon GO Live Map',
        exe: "pokemon-go-map.exe",
        setupIcon: path.join(path.resolve(), 'pokemon.ico'),
        iconUrl: 'https://raw.githubusercontent.com/mchristopher/PokemonGo-DesktopMap/master/pokemon.ico',
        loadingGif: path.join(path.resolve(), 'installing.gif'),
        productName: 'Pokemon GO Live Map'
      }
    },
    'electron': {
      macos: {
        options: {
          name: appConfig.name,
          dir: 'app',
          out: 'dist',
          overwrite: true,
          asar: false,
          ignore: common_ignore_dir.concat(mac_ignore_dir),
          version: '1.3.3',
          platform: 'darwin',
          arch: 'x64',
          'app-version': appConfig.version,
          icon: path.join(path.resolve(), 'pokemon.icns'),
          'app-bundle-id': 'com.mchrstopher.pokemon-go-live-map',
          'osx-sign': {
            identity: 'Developer ID Application: EaglEye Computer Services, LLC (46DPF949NK)'
          }
        }
      },
      win32: {
        options: {
          name: appConfig.name,
          dir: 'app',
          out: 'dist',
          overwrite: true,
          asar: true,
          ignore: common_ignore_dir.concat(win_ignore_dir),
          version: '1.3.3',
          platform: 'win32',
          arch: 'ia32',
          'app-version': appConfig.version,
          icon: path.join(path.resolve(), 'pokemon.ico'),
          'version-string': {
            'CompanyName': appConfig.author,
            'FileDescription': 'Pokemon GO Live Map',
            'ProductName': 'Pokemon GO Live Map',
            'OriginalFilename': 'pokemon-go-map.exe'
          }
        }
      }
    }
  });

  grunt.registerTask('default', [
    'clean',
    'execute',
    'electron:macos',
    'shell:compressOsx'
  ]);
  grunt.registerTask('win32', [
    'clean',
    'electron:win32',
    'create-windows-installer',
  ]);

};
