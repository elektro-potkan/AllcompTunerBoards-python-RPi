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


from smbus import SMBus
from RPi import GPIO

from time import sleep
import math


class Board:
	# Methods list
	# * __init__(gpio_en, gpio_stby, i2cbus = None, gpio_mode_bcm = False)
	# * power(on = None)
	# * reset()
	# * mute(on = None)
	# * volume(vol = None, dB = False)
	# * balance(left = None, right = None, dB = False)
	# * input(input = None, loudness = None, gain = None, dB = False)
	# * bass(level = None, dB = False)
	# * treble(level = None, dB = False)
	# * tune(freq = None)
	# * tuner_enable_frontend_i2c(enable = None)
	
	# Internal variables list
	# * _gpio_en - GPIO pin connected to the EN pin of the board
	# * _gpio_stby - GPIO pin connected to the ST-BY pin of the board
	# * _bus - holding instance of SMBus providing I2C bus for communication with chips on the board
	# * _state - dictionary holding current setup of the board
	
	
	_gpio_en = None
	_gpio_stby = None
	_bus = None
	_state = None
	
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
			"power": False, "mute": True,
			"DSP": {
				"volume": 0,
				"balance_left": 31,
				"balance_right": 31,
				"input": 0,
				"input_loudness": True,
				"input_gain": 0,
				"bass": 0,
				"treble": 0
			},
			"TUNER": {
				"frontend_i2c_enabled": False,
				"freq": 0
			}
		}
		
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
	#* Sends actual settings to all I2C chips
	#*
	def setup_i2c_chips(self):
		self._i2c_send_dsp(None)#TODO
		self._i2c_send_tuner_backend(2)
		self._i2c_send_tuner_frontend(4)
	# end of method setup_i2c_chips
	
	
	#*** CONTROL OF POWER AND MODES OF AMPLIFIER ***
	
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
				sleep(0.2)
			
			GPIO.output(self._gpio_en, self._state["power"])
			
			if not old_state and self._state["power"]:
				sleep(0.5)
				self.setup_i2c_chips()
		
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
	
	
	#*** DSP CONTROL ***
	
	#*
	#* Sets main volume
	#* @param int/float vol - volume to be set (int level, float dB) or None to return current value only
	#* @param bool dB - if the volume is given in decibels
	#* @return int/float - current volume as level or in decibels (software only)
	#*
	def volume(self, vol = None, dB = False):
		if vol != None:
			if dB:
				if vol < -78.75:
					vol = -78.75
				elif vol > 0:
					vol = 0
				
				self._state["DSP"]["volume"] = 63 + int( math.ceil( vol / 1.25 ) )
			else:
				if vol < 0:
					vol = 0
				elif vol > 63:
					vol = 63
				
				self._state["DSP"]["volume"] = int(vol)
			
			self._i2c_send_dsp(None)#TODO
		
		return self._state["DSP"]["volume"] if not dB else (self._state["DSP"]["volume"] - 63) * 1.25
	# end of method volume
	
	#*
	#* Sets balance of channels
	#* @param int/float left - volume of left channel to be set (int level, float dB) or None to left untouched
	#* @param int/float right - volume of right channel to be set (int level, float dB) or None to left untouched
	#* @param bool dB - if the volume is given in decibels
	#* @return {"left": int/float, "right": int/float} - current balance of channels (software only)
	#*
	def balance(self, left = None, right = None, dB = False):
		if left != None or right != None:
			if left != None:
				if dB:
					if left < -38.75:
						left = -38.75
					elif left > 0:
						left = 0
					
					self._state["DSP"]["balance_left"] = 31 + int( math.ceil( left / 1.25 ) )
				else:
					if left < 0:
						left = 0
					elif left > 31:
						left = 31
					
					self._state["DSP"]["balance_left"] = int(left)
			
			if right != None:
				if dB:
					if right < -38.75:
						right = -38.75
					elif right > 0:
						right = 0
					
					self._state["DSP"]["balance_right"] = 31 + int( math.ceil( right / 1.25 ) )
				else:
					if right < 0:
						right = 0
					elif right > 31:
						right = 31
					
					self._state["DSP"]["balance_right"] = int(right)
			
			self._i2c_send_dsp(None)#TODO
		
		if not dB:
			return {"left": self._state["DSP"]["balance_left"], "right": self._state["DSP"]["balance_right"]}
		else:
			return {"left": (self._state["DSP"]["balance_left"] - 31) * 1.25, "right": (self._state["DSP"]["balance_right"] - 31) * 1.25}
	# end of method balance
	
	#*
	#* Switches inputs and sets parameters of selected input
	#* @param int input - number of input to switch to or None to left untouched
	#* @param bool loudness - if loudness for current input should be switched on or off or None to left untouched
	#* @param int/float - input gain to be set (int level, float dB) or None to left untouched
	#* @param bool dB - if the gain is given in decibels
	#* @return {"input": int, "loudness": bool, "gain": int/float} - current input and its parameters (software only)
	#*
	def input(self, input = None, loudness = None, gain = None, dB = False):
		if input != None or loudness != None or gain != None:
			if input != None:
				if input < 0:
					input = 0
				elif input > 2:
					input = 2
				
				self._state["DSP"]["input"] = int(input)
			
			if loudness != None:
				self._state["DSP"]["input_loudness"] = bool(loudness)
			
			if gain != None:
				if gain < 0:
					gain = 0
				
				if dB:
					if gain > 11.25:
						gain = 11.25
					
					self._state["DSP"]["input_gain"] = int(math.ceil( gain / 3.75 ) )
				else:
					if gain > 3:
						gain = 3
					
					self._state["DSP"]["input_gain"] = int(gain)
			
			self._i2c_send_dsp(None)#TODO
		
		return {"input": self._state["DSP"]["input"], "loudness": self._state["DSP"]["input_loudness"], "gain": (self._state["DSP"]["input_gain"] if not dB else self._state["DSP"]["input_gain"] * 3.75)}
	# end of method input
	
	#*
	#* Sets bass level
	#* @param int level - bass level to be set or None to return current value only
	#* @param bool dB - if the level is given in decibels
	#* @return int - current bass level (software only)
	#*
	def bass(self, level = None, dB = False):
		if level != None:
			if dB:
				level = level / 2
			
			if level < -7:
				level = -7
			elif level > 7:
				level = 7
			
			self._state["DSP"]["bass"] = int(level)
			
			self._i2c_send_dsp(None)#TODO
		
		return self._state["DSP"]["bass"] if not dB else self._state["DSP"]["bass"] * 2
	# end of method bass
	
	#*
	#* Sets treble level
	#* @param int level - treble level to be set or None to return current value only
	#* @param bool dB - if the level is given in decibels
	#* @return int - current treble level (software only)
	#*
	def treble(self, level = None, dB = False):
		if level != None:
			if dB:
				level = level / 2
			
			if level < -7:
				level = -7
			elif level > 7:
				level = 7
			
			self._state["DSP"]["treble"] = int(level)
			
			self._i2c_send_dsp(None)#TODO
		
		return self._state["DSP"]["treble"] if not dB else self._state["DSP"]["treble"] * 2
	# end of method treble
	
	
	#*** TUNER CONTROL ***
	
	#*
	#* Sets the frequency to be tuned (50kHz steps hardcoded for now)
	#* @param float freq - the new frequency to be set or None to return current value only
	#* @return float - current frequency (software only)
	#*
	def tune(self, freq = None):
		if freq != None:
			if freq < 30.4:
				freq = 30.4
			elif freq > 108.1:
				freq = 108.1
			
			self._state["TUNER"]["freq"] = float(freq)
			
			self._i2c_send_tuner_frontend(2)
		
		return self._state["TUNER"]["freq"]
	# end of method tune
	
	#*
	#* Enables or disables I2C to tuner frontend-chip (function provided by tuner backend-chip)
	#* @param bool enable - True/False for enabling or disabling it, None to return current state only
	#* @return bool - if the I2C bus to tuner frontend-chip is enabled or not (software only)
	#*
	def tuner_enable_frontend_i2c(self, enable = None):
		if enable != None:
			self._state["TUNER"]["frontend_i2c_enabled"] = bool(enable)
			
			self._i2c_send_tuner_backend(1)
		
		return self._state["TUNER"]["frontend_i2c_enabled"]
	# end of method tuner_enable_frontend_i2c
	
	
	#*** INTERNAL METHODS FOR SENDING DATA OVER I2C TO CHIPS ***
	
	#*
	#* Send data over I2C to DSP
	#* @param
	#*
	def _i2c_send_dsp(self, bytes):
		if not self._state["power"]:# send data to board but only if it is powered
			return
		
		#TODO choose bytes to be sent
		
		# build bytes from instance variables
		byte_volume = 63 - self._state["DSP"]["volume"]
		byte_balance_left_1 = (0b100 << 5) | (31 - self._state["DSP"]["balance_left"])
		byte_balance_left_2 = (0b110 << 5) | (31 - self._state["DSP"]["balance_left"])
		byte_balance_right_1 = (0b101 << 5) | (31 - self._state["DSP"]["balance_right"])
		byte_balance_right_2 = (0b111 << 5) | (31 - self._state["DSP"]["balance_right"])
		
		byte_input = (0b010 << 5)
		byte_input |= ((3 - self._state["DSP"]["input_gain"]) << 3)
		byte_input |= (0 if self._state["DSP"]["input_loudness"] else (1 << 2))
		byte_input |= self._state["DSP"]["input"]
		
		byte_bass = (0b0110 << 4)
		if self._state["DSP"]["bass"] < 0:
			byte_bass |= self._state["DSP"]["bass"] + 7
		else:
			byte_bass |= (1 << 3) | (7 - self._state["DSP"]["bass"])
		
		byte_treble = (0b0111 << 4)
		if self._state["DSP"]["treble"] < 0:
			byte_treble |= self._state["DSP"]["treble"] + 7
		else:
			byte_treble |= (1 << 3) | (7 - self._state["DSP"]["treble"])
		
		# send data
		self._bus.write_i2c_block_data(0x44, byte_volume, [byte_balance_left_1, byte_balance_left_2, byte_balance_right_1, byte_balance_right_2, byte_input, byte_bass, byte_treble])
		
		'''
		self._bus.write_byte(0x44, byte_volume)
		self._bus.write_i2c_block_data(0x44, byte_balance_left_1, [byte_balance_left_2])
		self._bus.write_i2c_block_data(0x44, byte_balance_right_1, [byte_balance_right_2])
		self._bus.write_byte(0x44, byte_input)
		self._bus.write_byte(0x44, byte_bass)
		self._bus.write_byte(0x44, byte_treble)
		'''
	# end of method _i2c_send_dsp
	
	#*
	#* Send data over I2C to tuner backend-chip
	#* @param int last_byte - number of last byte to be sent (inclusive)
	#*
	def _i2c_send_tuner_backend(self, last_byte):
		if not self._state["power"]:# send data to board but only if it is powered
			return
		
		if last_byte < 1:
			return
		elif last_byte > 2:
			last_byte = 2
		
		if last_byte > 1:
			byte_2 = 0x01
		
		byte_1 = 0x7A
		if self._state["TUNER"]["frontend_i2c_enabled"]:
			byte_1 |= (1 << 7)
		
		# send data
		if last_byte > 1:
			self._bus.write_i2c_block_data(0x61, byte_1, [byte_2])
		else:
			self._bus.write_byte(0x61, byte_1)
	# end of method _i2c_send_tuner_backend
	
	#*
	#* Send data over I2C to tuner frontend-chip
	#* @param int last_byte - number of last byte to be sent (inclusive)
	#*
	def _i2c_send_tuner_frontend(self, last_byte):
		if not self._state["power"]:# send data to board but only if it is powered
			return
		
		if last_byte < 1:
			return
		elif last_byte > 4:
			last_byte = 4
		
		if last_byte > 3:
			byte_4 = 0x00# testing byte
		
		if last_byte > 2:
			byte_3 = 0x37
		
		freq = int(self._state["TUNER"]["freq"] * 10) * 2 + 1442
		byte_1 = 0xFF & freq
		byte_2 = 0xFF & (freq >> 8)
		
		# enable I2C
		self.tuner_enable_frontend_i2c(True)
		# send data
		if last_byte > 3:
			self._bus.write_i2c_block_data(0x62, byte_1, [byte_2, byte_3, byte_4])
		elif last_byte > 2:
			self._bus.write_i2c_block_data(0x62, byte_1, [byte_2, byte_3])
		else:
			self._bus.write_i2c_block_data(0x62, byte_1, [byte_2])
		# disable I2C
		self.tuner_enable_frontend_i2c(False)
	# end of method _i2c_send_tuner_frontend
# end of class Board
