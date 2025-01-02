# EvenComfort

Experimental script to display Indoor Environmental Quality sensor data on Even Realities G1 glasses.

## Usage

1. Configure the microcontroller (serial port / baud rate / number of sensor) in `even_g1.py`

    - You can find the demo Arduino code and the quick build guides [here](/microcontroller): 

2. run `even_g1.py`

## Features

- Connect microcontroller via serial port

- TODO: Send sensor data to even-realities g1 smart glasses

    - Supports Bosch BME280 for air temperature, relative humidity, air pressure

    - Supports Sensirion SCD30 for CO2 concentration in ppm (it also has temperature and humidity data, but not recommended due to accuracy)

- TODO: Add evaluation of thermal comfort, indoor air quality

- TODO: Add support for [Ressourcenwächter](https://rw.e3d.rwth-aachen.de/en/homepage-en/)

## License

This project is licensed under the GNU General Public License v3.0 as it depends on [even_glasses](https://github.com/emingenc/even_glasses) (Thanks to @emingenc for the Python API).

If you only copy my part, you can consider it as MIT license.

## Expand the G1 open source ecosystem!

Technically, the microcontroller ESP32 I use also supports BLE connection, which can send sensor data directly to the glasses without needing a computer to run the script. But since my monitoring device on my desk is next to my laptop and will not be moved, I have not implemented this yet (too lazy :D).

Feel free to copy my code into your applications! Further development plans are to support some other devices I previously developed about Indoor Environmental Quality (they have more types of sensors, such as noise, light, VOC, etc.).

If you have other ideas, feel free to submit an issue labelled `enhancement`.

### Some cool repos for Even Realities G1 I found earlier:

- [EvenDemoApp](https://github.com/even-realities/EvenDemoApp): The official demo app from Even Realities.

- [@emingenc: even_glasses](https://github.com/emingenc/even_glasses): Very complete and powerful Python API.

- [@meyskens: fahrplan](https://github.com/meyskens/fahrplan): Integration for real time train info!

- [@emingenc: Emotional AI Voice Chat](https://github.com/emingenc/G1_voice_ai_assistant): Fast conversation with emotional AI with even-realities G1 smart glass connection.

- [@emingenc: g1_flutter_blue_plus](https://github.com/emingenc/g1_flutter_blue_plus): Another repo from @emingenc for Dart implementation.

- [@NyasakiAT: G1-Navigate](https://github.com/NyasakiAT/G1-Navigate): Further development of the Dart implementation and BMP composing code

If I find another repo, I will add it to this list. If you have a cool application, feel free to submit an issue labelled `enhancement`, or better yet, post it directly to the Even Realities official Discord group.