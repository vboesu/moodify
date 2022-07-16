# moodify
Generate color palettes randomly or from an image and apply them in a search or to an image.
Implemented in Python (3.6+) and C for speed.

## Table of Contents
* [Installation](#install)
* [Setup](#setup)
* [Usage](#usage)

## Installation
To install the project, it suffices to download the repository into a folder and extract it. I recommend creating a virtual environment for the project using
```
$ virtualenv venv
$ source venv/bin/activate
```
Install all dependencies by running ```pip install -r requirements.txt```.

## Setup
Access to the Pixabay API which is used to search for images requires a private API key which can be obtained at [Pixabay's API Docs](https://pixabay.com/api/docs/).
The API key has to be stored either in the environment variable ```PIXABAY_API_KEY``` (by running ```EXPORT PIXABAY_API_KEY=[your API key]```) or by creating a file called ```key.txt``` in the root directory that contains only the your personal API key. It is then automatically loaded by the application on startup.

The shared C libaries used to create palettes from images and apply them to images are precompiled using the respective source files. If you want to make changes and apply them, you can manually recompile the C files using the commands
```
$ gcc -c -Wall -Werror -fpic [FILE].c
$ gcc -shared -o [FILE].so [FILE].o
```

## Usage
To start the web server, run ```flask run``` in your virtual environment. *Warning*: This should only be used for testing, not as a production server. You can find out more about deploying flask to production [here](https://flask.palletsprojects.com/en/2.0.x/tutorial/deploy/).

The database for moodify is created automatically when you first start up the app, as well as the ```uploads``` folder in the root directory of the project. Make sure that you have sufficient permissions to the project folder to avoid errors.
