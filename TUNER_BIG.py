# -*- coding: utf-8 -*-

#
#  TUNER_BIG.py
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


class TUNER_BIG(BoardChip):
	# Methods list
	# * __init__(board)
	# * tune(freq = None)
	
	# Constants list
	# * INFO - type of the supported TUNER
	# * INFO_TEXT - more verbose description of the supported TUNER
	
	# Internal variables list
	# * _board - holding instance of Board the TUNER is on
	# * _state - dictionary holding current setup of the board
	
	
	INFO = "BIG"
	INFO_TEXT = "Bigger tuner with TEA6825 backend and TEA6810 frontend chips"
	
	#*
	#* Inits class
	#* @param object board - instance of Board the TUNER is on
	#*
	def __init__(self, board):
		if board == None:
			raise NoBoardException("Cannot init TUNER on no board!")
		
		self._board = weakref.ref(board)
		
		self._state = {
			"stereo": True,
			"synthesizer_freq": 50,
			"tuning_mute": False,
			"SDS-SDR_hold": False,
			"mute": False,
			"frontend_i2c": False,
			"mode_FM": True,
			"SDR": False,
			"sensitivity_changed": False,
			"temperature_compensation": False,
			"noise_blanker": False,
			"freq": 95.0
		}
		
		# init
		self._i2c_backend(2)
		self._i2c_frontend(4)
	# end of method __init__
	
	def afterPowerOn(self):
		self._i2c_backend(2)
		self._i2c_frontend(4)
	# end of method afterPowerOn
	
	
	#*
	#* Sets the frequency to be tuned using given step
	#* @param float freq - the new frequency in MHz for FM and kHz for AM to be set or None to return current value only
	#* @param int step - the new step in kHz to be used for tuning (possible values are 3, 5, 10, 15, 25 and 50)
	#* @return {"freq": float, "step": int} - current frequency and tuning step (software only)
	#*
	def tune(self, freq = None, step = None):
		change_freq = False
		change_step = False
		
		if freq != None:
			if freq < 30.4:
				freq = 30.4
			elif freq > 108.1:
				freq = 108.1
			
			self._state["freq"] = float(freq)
			change_freq = True
		
		if step != None:
			raise Exception("Changing of tuning step is not fully supported yet!")
			step = int(step)
			if step in [3, 5, 10, 15, 25, 50]:
				self._state["synthesizer_freq"] = step
				change_step = True
		
		if change_step:
			self._i2c_backend(1)
			self._i2c_frontend(2)
		elif change_freq:
			self._i2c_frontend(2)
		
		return {"freq": self._state["freq"], "step": self._state["synthesizer_freq"]}
	# end of method tune
	
	
	#*
	#* Send data over I2C to tuner backend-chip
	#* @param int last_byte - number of last byte to be sent (inclusive)
	#*
	def _i2c_backend(self, last_byte):
		if last_byte < 1:
			return
		elif last_byte > 2:
			last_byte = 2
		
		if last_byte > 1:
			byte_2 = 1 if self._state["mode_FM"] else 0
			#
			#
			byte_2 |= (1 << 3) if self._state["SDR"] else 0
			#
			byte_2 |= (1 << 5) if self._state["sensitivity_changed"] else 0
			byte_2 |= (1 << 6) if self._state["temperature_compensation"] else 0
			byte_2 |= (1 << 7) if self._state["noise_blanker"] else 0
		
		byte_1 = 0 if self._state["stereo"] else 1
		byte_1 |= (([3, 5, 10, 15, 25, 50].index(self._state["synthesizer_freq"])) << 1)
		byte_1 |= 0 if self._state["tuning_mute"] else (1 << 4)
		byte_1 |= 0 if self._state["SDS-SDR_hold"] else (1 << 5)
		byte_1 |= 0 if self._state["mute"] else (1 << 6)
		byte_1 |= (1 << 7) if self._state["frontend_i2c"] else 0
		
		# send data
		if last_byte > 1:
			self._board()._i2c_write(0x61, [byte_1, byte_2])
		else:
			self._board()._i2c_write(0x61, [byte_1])
	# end of method _i2c_backend
	
	#*
	#* Send data over I2C to tuner frontend-chip
	#* @param int last_byte - number of last byte to be sent (inclusive)
	#*
	def _i2c_frontend(self, last_byte):
		if last_byte < 1:
			return
		elif last_byte > 4:
			last_byte = 4
		
		if last_byte > 2:
			byte_3 = 1 if self._state["mode_FM"] else 0
			byte_3 |= (0b11 << 1)
			byte_3 |= (0 << 3)
			byte_3 |= (1 << 4)
			byte_3 |= (1 << 5)
			byte_3 |= (0b00 << 6)
		
		freq = int(self._state["freq"] * 10) * 2 + 1442
		byte_1 = 0xFF & freq
		byte_2 = 0xFF & (freq >> 8)
		
		# enable I2C
		self._state["frontend_i2c"] = True
		self._i2c_backend(1)
		# send data
		if last_byte > 3:
			self._board()._i2c_write(0x62, [byte_1, byte_2, byte_3, 0x00])
		elif last_byte > 2:
			self._board()._i2c_write(0x62, [byte_1, byte_2, byte_3])
		else:
			self._board()._i2c_write(0x62, [byte_1, byte_2])
		# disable I2C
		self._state["frontend_i2c"] = False
		self._i2c_backend(1)
	# end of method _i2c_frontend
# end of class TUNER_BIG
