AllcompTunerBoards-python-RPi
=============================
Library providing classes allowing a Raspberry Pi to control the Tuner-Boards from the Allcomp a.s. CZ company


Prerequisities
==============
To be able to use this "Library", you need to have `smbus.SMBus` and `RPi.GPIO` python modules installed.

The `RPi.GPIO` is already installed in standard Raspbian releases but you may need to install the `smbus.SMBus` manually by
```bash
sudo apt-get update
sudo apt-get install python-smbus
```
You may also need to load the I2C kernel module at each start by
```bash
sudo modprobe i2c-dev
```

You can check if all is OK then by running the python console
```bash
sudo python
```
and typing in the commands
```python
from smbus import SMBus
from RPi import GPIO
SMBus(1)
```
if there was no `ImportError` nor `IOError` printed after enter, everything is OK. You can exit the console by calling the `quit()` command.


Usage
=====
Clone the repository or download it as a zip file.

To run the Tuner via direct commands, then in the project folder run the python console by typing
```bash
sudo python
```

The `sudo` there is necessary, because we need root to be allowed to access the GPIOs and I2C bus. If you are already running under the `root` user, then omit the `sudo` "pre-command".

Now in the python console, you need to import the library first
```python
from Board import Board
```
and then initialize a new instance by providing the following command with necessary data
```python
B = Board(gpio_en, gpio_stby, i2cbus = None, gpio_mode_bcm = False)
```
Replace:
 - `gpio_en` by the number of GPIO pin, the tuner-board `EN` pin is connected to
 - `gpio_stby` by the number of GPIO pin, the tuner-board `ST-BY` pin is connected to
 - `i2cbus` by the number of I2C bus the tuner-board is connected to (for newer RPIs, it is the `1` bus which is wired in the GPIO header, `0` for the older ones - model B v1) - auto-selection based on the board revision is planned but not implemented yet
 - `gpio_mode_bcm` set to `True` if you entered the GPIO parameters above as real GPIO numbers of the processor - if you used the GPIO-header numbering (see [RPi.GPIO module documentation](http://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/), section"Pin numbering"), then you can simply omit this parametr at all, `False` is the default value

So to initialize an instance by using processor-GPIO-numbering with the GPIO 18 as `EN`, GPIO 17 as `ST-BY` on the newer RPi (I2C bus number 1), the command will look like
```python
B = Board(18, 17, 1, True)
```

Now we can work with the methods it provides. Each method is always returning the current setting. If you don't want to change anything, just print the current setup, you can simply run the method providing no parameters or with `None` parameters you don't want to set. However, the return current setting of all methods is currently software-only.

So to power the tuner-board up, run
```python
B.power(True)
```

Then, you will need to tune it, increase the volume and unmute the amplifier by running
```python
B.TUNER.tune(frequency_in_MHz 30.4 - 108.1)
B.DSP.volume(volume_step 0 - 63)
B.mute(False)
```

As you can see, the control is separated for each part of the board - the `Board` instance itself can control its power and muting of the amplifier. To control the properties of the DSP chip, you need to get an instance of its control-class from the `Board` instance - the same for the TUNER (even when the TUNER inside is controlled by two chips though).

So to tune it to 95.0MHz and volume step 25, run
```python
B.TUNER.tune(95)
B.DSP.volume(25)
B.mute(False)
```

The actual instance stores internally the setup of the board and it is restoring this setup on each `power(True)` call, so you will get the last setup. It is also possible to change the parameters while the board is off and after powering it on, your setup will be send to the board. The only thing, which does not support this, is the control of the amplifier - you will always need to run the `B.mute(False)` after power-up.

As simply as above, you can also change all of the feautures of the tuner-board except for the finer setting of tuner. As for now, most of its setting bytes to be sent are created from instance variables (for which, there are no methods for simple access yet), but the changes in them are not chained together, so it is possible to change them and setup the tuner into "undefined" state - with no changes to them, the class will behave as there are following hardcoded bytes:
- `0x7A 0x01`
- `freq-low freq-high 0x37 0x00` for the tuner frontend chip

The DSP can be completely controlled via simple instance methods.

All available methods:
```python
# Board
power(on = None)
reset()
mute(on = None)

# DSP
volume(vol = None, dB = False)
balance(left = None, right = None, dB = False)
input(input = None, loudness = None, gain = None, dB = False)
bass(level = None, dB = False)
treble(level = None, dB = False)

# TUNER
tune(freq = None)
```
The `dB` parameters in some methods are there bacause the methods controlls volume, gain, etc. When used without the `dB` parameter or when set to `False`, they will accept and also print the setting in steps. The steps alwas starts at 0 meaning lowest volume, no gain, center of the range for bass or treble, etc. The number of steps are the number of different combinations that can be passed to the chips. You can get the highest/ lowest possible step by muting the amplifier and setting them to some really high/low value. The methods will limit the value inside the allowed range and returns the current limited setting. When the `dB` parameter is set to `True`, the method accept/returns the volume... parameters in dB values mentioned in the datasheets.

If you need more info about the methods, take a look at the source - each method has a comment what it does and what arguments you can pass to it.

To exit the python console, type in
```python
quit()
```
This will also completely disable the tuner-board (when deleting the `B` instance).
