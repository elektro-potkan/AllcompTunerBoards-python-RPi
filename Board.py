# -*- coding: utf-8 -*-

#
#  Board.py
#
#  Copyright (c) 2015 Elektro-potkan <git@elektro-potkan.cz>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#


from smbus import SMBus
from RPi import GPIO

from DSP_TDA7313 import DSP_TDA7313 as DSP
from TUNER_BIG import TUNER_BIG as TUNER

from time import sleep
import math


class Board:
	# Methods list
	# * __init__(gpio_en, gpio_stby, i2cbus = None, gpio_mode_bcm = False)
	# * power(on = None)
	# * reset()
	# * mute(on = None)
	
	# Constants list
	# * DSP - holding instance of DSP control class
	# * TUNER - holding instance of TUNER control class
	
	# Internal variables list
	# * _gpio_en - GPIO pin connected to the EN pin of the board
	# * _gpio_stby - GPIO pin connected to the ST-BY pin of the board
	# * _bus - holding instance of SMBus providing I2C bus for communication with chips on the board
	# * _state - dictionary holding current setup of the board
	
	
	#*
	#* Inits class
	#* @param int gpio_en - GPIO pin connected to the EN pin of board
	#* @param int gpio_stby - GPIO pin connected to the ST-BY pin of board
	#* @param int i2cbus - number of i2c bus the board is connected to
	#* @param bool gpio_mode_bcm - if the mode of GPIO module used for specifying GPIO pins is BCM (True) or BOARD (False)
	#*
	def __init__(self, gpio_en, gpio_stby, i2cbus = None, gpio_mode_bcm = False):
		if i2cbus == None:
			raise Exception()#TODO auto selection based on RPI board revision
		
		self._gpio_en = gpio_en
		self._gpio_stby = gpio_stby
		
		self._bus = SMBus(i2cbus)
		sleep(0.5)
		
		GPIO.setmode(GPIO.BCM if gpio_mode_bcm else GPIO.BOARD)
		GPIO.setup(self._gpio_en, GPIO.OUT, GPIO.LOW)
		GPIO.setup(self._gpio_stby, GPIO.OUT, GPIO.LOW)
		
		self._state = {
			"power": False,
			"mute": True
		}
		
		self.DSP = DSP(self)
		self.TUNER = TUNER(self)
		
		# init GPIOs
		self.power(False)
		self.mute(True)
	# end of method __init__
	
	#*
	#* Destructor
	#*
	def __del__(self):
		self.power(False)
		GPIO.cleanup()
	# end of method __del__
	
	
	#*
	#* Turns on-board voltage regulators on or off
	#* @param bool on - True/False for setting the power state, None to return current state only
	#* @return bool - if the voltage regulators are on or off (software only)
	#*
	def power(self, on = None):
		if on != None:
			old_state = self._state["power"]
			
			self._state["power"] = bool(on)
			
			if not self._state["power"]:
				self.mute(True)
				self.DSP.beforePowerOff()
				self.TUNER.beforePowerOff()
				sleep(0.2)
			
			GPIO.output(self._gpio_en, self._state["power"])
			
			if not old_state and self._state["power"]:
				sleep(0.5)
				self.DSP.afterPowerOn()
				self.TUNER.afterPowerOn()
		
		return self._state["power"]
	# end of method power
	
	#*
	#* Resets board by turning it off and then on after 2 seconds
	#*
	def reset(self):
		self.power(False)
		sleep(2)
		self.power(True)
	# end of method reset
	
	#*
	#* Enables or disables amplifier stand-by mode
	#* @param bool on - True/False for setting the mute, None to return current state only
	#* @return bool - if the amplifier is muted or not (software only)
	#*
	def mute(self, on = None):
		if on != None:
			on = bool(on)
			
			if self._state["power"] or on:
				self._state["mute"] = on
				GPIO.output(self._gpio_stby, not self._state["mute"])
		
		return self._state["mute"]
	# end of method mute
	
	
	#*
	#* Send data over I2C if the Board is powered on
	#* @param int address - address byte
	#* @param tuple/list data - data bytes to be sent
	#*
	def _i2c_write(self, address, data):
		if address < 0 or len(data) < 1:
			return
		
		if not self._state["power"]:# send data to board but only if it is powered
			return
		
		if len(data) > 1:
			self._bus.write_i2c_block_data(address, data[0], data[1:])
		else:
			self._bus.write_byte(address, data[0])
	# end of method _i2c_write
# end of class Board
