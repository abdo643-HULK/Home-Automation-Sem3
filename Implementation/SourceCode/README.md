# Home Automation

## Requirements
- device to run Homeassistant OS or Home assistant with appdameon
- device to run the person recognition software/script
- camera
- harmony hub and firetv for older devices or a smart tv (some code changes are needed if you don't use a harmony hub)

## Installation

### Home Assistant
Follow the instruction on installing it from https://www.home-assistant.io/installation. The following steps are for the OS version.

After installation and finishing the configuration you need to install the following Addons:
- Appdaemon, for the apps
- Studio Code Server, to edit the files

Then to add the harmony hub and the firetv follow the following Guides:
- [Fire TV/Android TV](https://www.home-assistant.io/integrations/androidtv/)
- [Harmony Hub](https://www.home-assistant.io/integrations/harmony/)

After installation open the code server and copy the files from the home-assistant directory and either change the entity-id in home-assistant or in the files. The Directory resambles the same structure as the one in home assistant.

Now everything should be up and running

### Person Recognition

To be able to get everything working you need [Python 3.5+](https://www.python.org/downloads/)

Because we use OpenCV you will need some dependencies which you can find here: https://docs.opencv.org/3.4/d7/d9f/tutorial_linux_install.html

After installing Python a good practice before installing any dependencies, is to use a virtual environment.

1. Go to the person-recognition directory
    ```shell
    $ cd ./person-recognition
    ```
2. Create a Virtual Environment
    ```shell
    $ python3 -m venv .
    ```
3. Activate venv
    ```shell
    $ source bin/activate
    ```
4. Install OpenCV and Requests
    ```shell
    $ python3 -m pip install opencv-python
    $ python3 -m pip install requests
    ```
5. Now to run the script
    ```shell
    $ python3 main.py
    ```
That's it, hopefully you don't get any lib errors that are missing.

Good luck and have fun