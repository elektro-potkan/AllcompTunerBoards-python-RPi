# -*- coding: utf-8 -*-

#
#  DSP_TDA7313.py
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


from BoardChip import BoardChip

import weakref
import math


class DSP_TDA7313(BoardChip):
	# Methods list
	# * __init__(board)
	# * volume(vol = None, dB = False)
	# * balance(left = None, right = None, dB = False)
	# * input(input = None, loudness = None, gain = None, dB = False)
	# * bass(level = None, dB = False)
	# * treble(level = None, dB = False)
	
	# Constants list
	# * INFO - type of the supported DSP
	# * INFO_TEXT - more verbose description of the supported DSP
	
	# Internal variables list
	# * _board - holding instance of Board the DSP is on
	# * _state - dictionary holding current setup of the DSP
	
	
	INFO = "TDA7313"
	INFO_TEXT = "TDA7313 simple DSP"
	
	#*
	#* Inits class
	#* @param object board - instance of Board the DSP is on
	#*
	def __init__(self, board):
		if board == None:
			raise NoBoardException("Cannot init DSP on no board!")
		
		self._board = weakref.ref(board)
		
		self._state = {
			"volume": 0,
			"balance_left": 31,
			"balance_right": 31,
			"input": 0,
			"input_loudness": True,
			"input_gain": 0,
			"bass": 0,
			"treble": 0
		}
		
		# init
		self._i2c()#TODO
	# end of method __init__
	
	def afterPowerOn(self):
		self._i2c()#TODO
	# end of method afterPowerOn
	
	
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
				
				self._state["volume"] = 63 + int( math.ceil( vol / 1.25 ) )
			else:
				if vol < 0:
					vol = 0
				elif vol > 63:
					vol = 63
				
				self._state["volume"] = int(vol)
			
			self._i2c()#TODO
		
		return self._state["volume"] if not dB else (self._state["volume"] - 63) * 1.25
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
					
					self._state["balance_left"] = 31 + int( math.ceil( left / 1.25 ) )
				else:
					if left < 0:
						left = 0
					elif left > 31:
						left = 31
					
					self._state["balance_left"] = int(left)
			
			if right != None:
				if dB:
					if right < -38.75:
						right = -38.75
					elif right > 0:
						right = 0
					
					self._state["balance_right"] = 31 + int( math.ceil( right / 1.25 ) )
				else:
					if right < 0:
						right = 0
					elif right > 31:
						right = 31
					
					self._state["balance_right"] = int(right)
			
			self._i2c()#TODO
		
		if not dB:
			return {"left": self._state["balance_left"], "right": self._state["balance_right"]}
		else:
			return {"left": (self._state["balance_left"] - 31) * 1.25, "right": (self._state["balance_right"] - 31) * 1.25}
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
				
				self._state["input"] = int(input)
			
			if loudness != None:
				self._state["input_loudness"] = bool(loudness)
			
			if gain != None:
				if gain < 0:
					gain = 0
				
				if dB:
					if gain > 11.25:
						gain = 11.25
					
					self._state["input_gain"] = int(math.ceil( gain / 3.75 ) )
				else:
					if gain > 3:
						gain = 3
					
					self._state["input_gain"] = int(gain)
			
			self._i2c()#TODO
		
		return {"input": self._state["input"], "loudness": self._state["input_loudness"], "gain": (self._state["input_gain"] if not dB else self._state["input_gain"] * 3.75)}
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
			
			self._state["bass"] = int(level)
			
			self._i2c()#TODO
		
		return self._state["bass"] if not dB else self._state["bass"] * 2
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
			
			self._state["treble"] = int(level)
			
			self._i2c()#TODO
		
		return self._state["treble"] if not dB else self._state["treble"] * 2
	# end of method treble
	
	
	#*
	#* Sends data over I2C to DSP
	#* @param
	#*
	def _i2c(self):
		#TODO choose bytes to be sent
		
		# build bytes from instance variables
		byte_volume = 63 - self._state["volume"]
		byte_balance_left_1 = (0b100 << 5) | (31 - self._state["balance_left"])
		byte_balance_left_2 = (0b110 << 5) | (31 - self._state["balance_left"])
		byte_balance_right_1 = (0b101 << 5) | (31 - self._state["balance_right"])
		byte_balance_right_2 = (0b111 << 5) | (31 - self._state["balance_right"])
		
		byte_input = (0b010 << 5)
		byte_input |= ((3 - self._state["input_gain"]) << 3)
		byte_input |= (0 if self._state["input_loudness"] else (1 << 2))
		byte_input |= self._state["input"]
		
		byte_bass = (0b0110 << 4)
		if self._state["bass"] < 0:
			byte_bass |= self._state["bass"] + 7
		else:
			byte_bass |= (1 << 3) | (7 - self._state["bass"])
		
		byte_treble = (0b0111 << 4)
		if self._state["treble"] < 0:
			byte_treble |= self._state["treble"] + 7
		else:
			byte_treble |= (1 << 3) | (7 - self._state["treble"])
		
		# send data
		self._board()._i2c_write(0x44, [byte_volume, byte_balance_left_1, byte_balance_left_2, byte_balance_right_1, byte_balance_right_2, byte_input, byte_bass, byte_treble])
	# end of method _i2c
# end of class DSP_TDA7313
