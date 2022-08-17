# Travel Directions
A GUI front-end to Google Directions, accessible to screen reader users

## License
This project is licensed under the terms of the [Mozilla Public License, version 2.0.](https://www.mozilla.org/en-US/MPL/2.0/ "MPL2 official Site")

## Credits
This project was written by Nick Stockton.

## Installation
To install all the dependencies for this program, execute the following commands from the top directory of this repo.
```
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade "poetry==1.1.13"
poetry install
```

If you wish to contribute to this project, install the development dependencies with the following commands.
```
source .venv/bin/activate
pre-commit install -t pre-commit
pre-commit install -t pre-push
```

Additionally, you will need a **server** API key from Google. See the [API Keys](https://github.com/googlemaps/google-maps-services-python#user-content-api-keys "Google Maps Services Python API Keys Information") section of the Google Maps Services Python page for information on how to obtain one.
Once you have obtained your API key, copy the file src/travel_data/config.json.sample to src/travel_data/config.json. After that, add your server API key to config.json.
