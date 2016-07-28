var path = require('path');

module.exports = function(grunt) {

  require('load-grunt-tasks')(grunt);

  grunt.loadNpmTasks('grunt-electron-installer');

  grunt.initConfig({
      'create-windows-installer': {
        ia32: {
          appDirectory: path.join(path.resolve(), 'Pokemon GO Live Map-win32-ia32'),
          outputDirectory: path.join(path.resolve(), 'win32output'),
          title: 'Pokemon GO Live Map',
          exe: "Pokemon GO Live Map.exe",
          setupIcon: path.join(path.resolve(), 'pokemon.ico'),
          iconUrl: 'https://raw.githubusercontent.com/mchristopher/PokemonGo-DesktopMap/master/pokemon.ico',
          loadingGif: path.join(path.resolve(), 'installing.gif')
        }
      }
  });

  grunt.registerTask('default', ['create-windows-installer']);

};
