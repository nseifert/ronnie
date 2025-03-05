import redpitaya_scpi as scpi
import time

class Pitaya():

	def execute(self, cmd, **kwargs):
		return self.con.tx_txt(cmd, **kwargs)
	def query(self, cmd, **kwargs):
		self.execute(cmd, **kwargs)
		return self.con.rx_txt()

	def set_synth(self, freq, amp, **kwargs):
		gen_settings = {
		'channel': 0,
		'freq': 1.0E6,
		'type': {'SINE', 'SQUARE', 'TRIANGLE', 'SAWU', 'SAWD', 'PWM', 'ARBITRARY', 'DC', 'DC_NEG'},
		'amp': 0.5, # 0.5 Vpp default
		'offset': 0, # +0 V offset 
		'phase': 0, # in degrees
		'trigger': ['INT','EXT'],
		'trig_lvl': 0.25, # only if EXT is selected for trigger
		}

		for k in gen_settings.keys():
			if k in kwargs:
				gen_settings.update({k: kwargs[k]})
			if k == 'type':
				if k in kwargs:
					gen_settings.update(kwargs[k].upper())
				else:
					gen_settings.update({k: 'SINE'})
			if k == 'channel':
				if k in kwargs:
					if kwargs['channel'] not in [0,1]:
						print('ERROR: Requested channel for synthesizer is not valid; must either be 0 or 1. \n Requested channel: {}'.format(kwargs['channel']))
						raise 
			if k == 'trigger':
				if k in kwargs:
					if 'int' in kwargs['trigger'].lower():
						gen_settings.update({'trigger': 'INT'})
					elif 'ext' in kwargs['trigger'].lower():
						gen_settings.update({'trigger': 'EXT_PE'})
					else: # Just let Forrest run free!!!
						gen_settings.update({'trigger': 'INT'})
				if 'trig_lvl' in kwargs:
					gen_settings.update({'trig_lvl': kwargs['trig_lvl']})
		
	# Reset synthesizer
		self.execute('GEN:RST')

		# Set trigger
		self.execute(f'SOUR{gen_settings['channel']+1}:TRIg:SOUR {gen_settings['trigger']}')
		# Set parameters
		self.execute(f'SOUR{gen_settings['channel']+1}:FUNC {gen_settings['type']}')
		self.execute(f'SOUR{gen_settings['channel']+1}:FREQ:FIX {str(gen_settings['freq'])}')
		self.execute(f'SOUR{gen_settings['channel']+1}:VOLT {str(gen_settings['amp'])}')
		self.execute(f'SOUR{gen_settings['channel']+1}:PHAS {str(gen_settings['phase'])}')
		self.execute(f'SOUR{gen_settings['channel']+1}:VOLT:OFFS {str(gen_settings['offset'])}')

		try:
			status = self.synth_on(gen_settings['channel'])
			if not status:
				print('Synthesizer failed to power on.')
		except:
			raise
		print(f'Synthesizer set to {gen_settings['freq']} Hz, {gen_settings['amp']} V, trig: {gen_settings['trigger']}')
		return True

	def synth_on(self, channel):
		try:
			chan = channel + 1
			self.execute(f'OUTPUT{chan}: STATE ON')
			return True
		except:
			raise
			return False

	def synth_off(self, channel):
		try:
			chan = channel + 1
			self.execute(f'OUTPUT{chan}: STATE OFF')
			print('Synthesizer disabled successfully.')
			return True
		except:
			return False

	def acquire(self):
	
		# Reset and clear buffer
		self.execute('ACQ:RST')
		
		# Get memory region
		start_address = int(self.query('ACQ:AXI:START?'))
		size = int(self.query('ACQ:AXI:SIZE?'))
		if self.two_channel:
			start_address2 = round(start_address + size/2) 
		
		# Set decimation
		self.execute(f"ACQ:AXI:DEC {self.decimation}")
		
		# Set vertical axis to volts
		self.execute('ACQ:AXI:DATA:UNITS VOLTS')
		
		# Set trigger delay and buffer and enable DMA
		self.execute(f"ACQ:AXI:SOUR{self.master_channel}:Trig:Dly {self.data_size}")
		self.execute(f"ACQ:AXI:SOUR{self.master_channel}:SET:Buffer {start_address},{size/2}")
		self.execute(f"ACQ:AXI:SOUR{self.master_channel}:ENable ON")
		
		if self.two_channel:
			self.execute(f"ACQ:AXI:SOUR{self.slave_channel}:Trig:Dly {self.data_size}")
			self.execute(f"ACQ:AXI:SOUR{self.slave_channel}:SET:Buffer {start_address2},{size/2}")
			self.execute(f"ACQ:AXI:SOUR{self.slave_channel}:ENable ON")
			
		# Set trigger level
		self.execute(f"ACQ:TRig:LEV {self.trig_lvl}")
		
		# Begin acquisition
		self.execute('ACQ:START')
		self.execute('ACQ:TRig INT') # Trigger on channel 1 edge
	
		# Wait for trigger
		while 1: 

			q = self.query("ACQ:TRig:STAT?")
			if q == 'TD':
				acq_start = time.time()
				print('Triggered')
				break
		
		# Wait for filled ADC buffer
		while 1:
			q = self.query('ACQ:AXI:SOUR1:TRIG:FILL?')
			if q == '1':
				print('DMA buffer full\n')
				acq_end = time.time()
				break
		
		# Stop acquisition
		self.execute('ACQ:STOP')
		print(f"Acquistion timing: {acq_end - acq_start}")
		
		# Collect data
		
		# Get write pointer at trigger location

		posChA = int(self.query('ACQ:AXI:SOUR1:Trig:Pos?'))
		if self.two_channel:
			posChB = int(self.query('ACQ:AXI:SOUR2:Trig:Pos?'))

		ch1_data = self.query(f"ACQ:AXI:SOUR1:DATA:Start:N? {posChA},{self.data_size}")
		if self.two_channel: 
			ch2_data = self.query(f"ACQ:AXI:SOUR2:DATA:Start:N? {posChB},{self.data_size}")
		
		signal_ch1	= ch1_data.strip('{}\n\r').replace("  ", "").split(',')
		if self.two_channel:
			signal_ch2 = ch2_data.strip('{}\n\r').replace("	 ", "").split(',')
			
		# Disable Pitaya acquistion
		self.execute('ACQ:AXI:SOUR1:ENable OFF')
		if self.two_channel:
			self.execute('ACQ:AXI:SOUR2:ENable OFF')
			
		if self.two_channel:
			return signal_ch1, signal_ch2
		else:
			return signal_ch1
		

	def __init__(self, **kwargs):
	
		self.settings = {
			'host': '192.168.0.2', # Set to default value for Pitaya for Gerry
			'port': 5000, # Shouldn't change
			'timeout': None, # set to time in seconds if otherwise
			'name': 'Pitaya',

			'srate': 250E6,
			'data_size': 32768, #16 bit samples
			'acq_len': 16384,
			'num_avg': 20,
			'decimation': 1, # should always be set to 1 unless otherwise needed
			'two_channel': False,
			'master_channel': 1,
			'slave_channel': 2,
			'trig_lvl': 0.2
		}
		
		for k in self.settings.keys():
		
			if k in kwargs:
				self.__setattr__(k, kwargs[k])
			else:
				self.__setattr__(k, self.settings[k])

		try: 
			print(f'Connecting to {self.name} SCPI server @ {self.host}:{self.port}')
			self.con = scpi.scpi(host = self.host, port = self.port, timeout = self.timeout)
		except: # Connection failed
			print('WARNING: SCPI SERVER CONNECTION FAILED. Make sure the host address is correct and the SCPI server is enabled!')
			raise 
		else:
			print('Connection successful.')
if __name__ == '__main__':

	dig = Pitaya(host='192.168.0.2', name='Pitaya', timeout=5.0)

	# Test run -- enable AWG CW output on output channel 1 and
	# feed into input channel 1; enable 10 MHz external reference,
	# and use rising edge for this signal to trigger 
	dig.set_synth(freq=10.0E6, amp=0.5, channel=0)
	dig.acquire()	
	dig.synth_off()
