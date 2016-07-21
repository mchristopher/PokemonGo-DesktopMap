# Pokémon GO - Live Map

<p align="center">
<img src="https://raw.githubusercontent.com/mchristopher/PokemonGo-DesktopMap/master/cover_img.png">
</p>

Electron app that bundles the great [PokemonGo-Map](https://github.com/AHAAAAAAA/PokemonGo-Map) project with an HTML UI and Python dependencies. Shows live visualizaiton of Pokémon in an area.

Getting Started
---------------

Running the application is easy! You can download the latest version from the [Release page](https://github.com/mchristopher/PokemonGo-DesktopMap/releases).

Once you have downloaded the appropriate ZIP file for your platform, extract it and run "Pokemon GO Live Map" and follow the instructions.

Development Environment
-----------------------

Development is currently done on OS X and tested on Windows 10. To get started, you'll need to install [NodeJS](https://nodejs.org/), Python 2.7, pip, and virtualenv. With Homebrew, I use:

    brew install python node
    pip install virtualenv
    npm install

You will also need to install the Python dependencies (assuming map is the PokemonGo-Map repo):

    cd map
    pip install -r requirements.txt

To run the project, `cd` into this directory and run:

    electron .


Contributing
------------

All contributions are welcome. If you would like to improve the map backend, please see the `package` branch on the [PokemonGo-Map](https://github.com/mchristopher/PokemonGo-Map/tree/package) repo.

Licensing
---------

This project is licensed under the MIT License.
