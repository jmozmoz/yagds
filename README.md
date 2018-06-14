# yagds
Yet another garage door sensor

## Hardware

### ESP-01

### Carrier Board

See folder [layout_kicad](layout_kicad/) using [KiCad](http://kicad-pcb.org/)

![carrier board schematics](/pics/schematic.png)

![carrier board 3d](/pics/esp01carrier.png)

<img src="pics/boxed_carrier_board_cad.jpg" width="45%"> <img src="pics/boxed_carrier_board.jpg" width="45%">


## Software

### ESP-01 Firmware
See folder [uploadSensorData](uploadSensorData/) using [PlatformIO](https://platformio.org/)

Used libraries:
* [Homie](https://github.com/marvinroger/homie-esp8266)
* [simpleTimer](https://github.com/jfturcot/SimpleTimer)
* [jled](https://github.com/jandelgado/jled)

### Telegram Bot with state machine
See folder [mqtt_telegram_bot](mqtt_telegram_bot/)

![garage door states](/pics/my_state_diagram.png)

Used libraries:
* [Python Telegram Bot](https://pypi.org/project/python-telegram-bot/)
* [paho-mqtt](https://pypi.org/project/paho-mqtt/)
* Python state machine: [transitions](https://pypi.org/project/transitions/)

## Authors

* **Joachim Herb** - [jmozmoz](https://github.com/jmozmoz)

## License

This project is licensed under [GPL v3](LICENSE)