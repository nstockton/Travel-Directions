# Travel Directions
A GUI front-end to Google Directions, accessible to screen reader users

## License
This project is licensed under the terms of the [Mozilla Public License, version 2.0.](https://www.mozilla.org/en-US/MPL/2.0/ "MPL2 official Site")

## Credits
This project was written by Nick Stockton.

## Installation
To install all the dependencies for this program, execute the following shell command from the top directory of this repo.
```
pip install -U -r requirements.txt
```
Additionally, you will need a **server** API key from Google. See the [API Keys](https://github.com/googlemaps/google-maps-services-python#user-content-api-keys "Google Maps Services Python API Keys Information") section of the Google Maps Services Python page for information on how to obtain one.
Once you have obtained your API key, create a file called **key.py** in the top level directory of this repo, and add a line that looks like this.
```
API_KEY = "my_api_key"
```
Where **my_api_key** is your API key from Google.
