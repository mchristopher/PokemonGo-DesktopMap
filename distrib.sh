#!/bin/bash

find . -name "*.pyc" -delete

rm -fr PokemonGoMap-OSX.zip
node_modules/.bin/electron-packager . "Pokemon GO Live Map" --platform=darwin --arch=x64 --icon=pokemon.icns --overwrite --prune --osx-sign.identity="Mac Developer: Mike Christopher (35938FGD4K)" --ignore=PokemonGoMap-Lin-x64.zip --ignore=PokemonGoMap-OSX.zip --ignore=PokemonGoMap-Win.zip --ignore=map/ve --ignore="map/Easy Setup" --ignore=distrib.sh --ignore=pywin --ignore=package_python.sh
cd "Pokemon GO Live Map-darwin-x64"
zip -9rv ../PokemonGoMap-OSX.zip .
cd ..

rm -fr PokemonGoMap-Win.zip
node_modules/.bin/electron-packager . "Pokemon GO Live Map" --platform=win32 --arch=ia32 --icon=pokemon.ico --overwrite --prune --ignore=map/ve --ignore=PokemonGoMap-Lin-x64.zip --ignore=PokemonGoMap-OSX.zip --ignore=PokemonGoMap-Win.zip --ignore="map/Easy Setup" --ignore=distrib.sh --ignore=package_python.sh
cd "Pokemon GO Live Map-win32-ia32"
zip -9rv ../PokemonGoMap-Win.zip .
cd ..

rm -fr PokemonGoMap-Lin-x64.zip
node_modules/.bin/electron-packager . "Pokemon GO Live Map" --platform=linux --arch=x64 --icon=pokemon.ico --overwrite --prune --ignore=map/ve --ignore=PokemonGoMap-Lin-x64.zip --ignore=PokemonGoMap-OSX.zip --ignore=PokemonGoMap-Win.zip --ignore="map/Easy Setup" --ignore=distrib.sh --ignore=package_python.sh --ignore=pywin
cd "Pokemon GO Live Map-linux-x64"
zip -9rv ../PokemonGoMap-Lin-x64.zip .
cd ..
