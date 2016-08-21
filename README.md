# Pokémon GO - Live Map

<p align="center">
<img src="https://raw.githubusercontent.com/mchristopher/PokemonGo-DesktopMap/master/cover_img.png">
</p>

Electron app that bundles the great [PokemonGo-Map](https://github.com/AHAAAAAAA/PokemonGo-Map) project with HTML UI and Python dependencies. Shows live visualization of Pokémon in an area.

Checkout the *new* **Discord**: [<img src="http://vignette3.wikia.nocookie.net/siivagunner/images/9/9f/Discord_icon.svg/revision/latest/scale-to-width-down/50?cb=20160623172043">](https://discord.gg/mV2kCR6)

Getting Started
---------------

Running the application is easy! You can download the latest version from the [Release page](https://github.com/mchristopher/PokemonGo-DesktopMap/releases).

Once you have downloaded the appropriate ZIP file for your platform, extract it and run "Pokemon GO Live Map" and follow the instructions.

Development Environment
-----------------------

If you are pulling from git, you must first instruct git to fetch the included submodules. Run this after cloning:

    git submodule update --init --recursive

Development is currently done on OS X and tested on Windows 10. To get started, you'll need to install [NodeJS](https://nodejs.org/), Python 2.7, pip, and virtualenv. With Homebrew, I use:

    brew install python node
    pip install virtualenv
    npm install

To run the project, run:

    npm start


Contributing
------------

All contributions are welcome. If you would like to improve the map backend, please see the `package` branch on the [PokemonGo-Map](https://github.com/mchristopher/PokemonGo-Map/tree/package) repo.

Licensing
---------

This project is licensed under the MIT License.

Binary Python Modules
---------------------
 * xxhash
 * pyproj
 * Cryptodome
 
