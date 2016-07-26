var path = require('path');

module.exports = function(grunt) {

  require('load-grunt-tasks')(grunt);

  grunt.loadNpmTasks('grunt-electron-installer');

  grunt.initConfig({
      electron: {
          macosBuild: {
              options: {
                  name: 'Fixture',
                  dir: 'app',
                  out: 'dist',
                  platform: 'darwin',
                  arch: 'x64'
              }
          }
      },
      'create-windows-installer': {
        ia32: {
          appDirectory: path.join(path.resolve(), 'pgowin32'),
          outputDirectory: path.join(path.resolve(), 'win32output'),
          title: 'Pokemon GO Live Map',
          exe: "Pokemon GO Live Map.exe"
        }
      }
  });

  grunt.registerTask('default', ['electron']);

};
