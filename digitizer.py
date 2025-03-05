from Instrument import Instrument
import redpitaya_scpi as scpi

class Pitaya():

	def execute(self, cmd, **kwargs):
		return self.con.tx_txt(cmd, **kwargs)
	def query(self, cmd, **kwargs):
		self.execute(cmd, **kwargs)
		return self.con.rx_txt()

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
		self.execute('ACQ:TRig CH1_PE') # Trigger on channel 1 edge
	
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
			'host': '192.168.0.2' # Set to default value for Pitaya for Gerry
			'port': 5000 # Shouldn't change
			'timeout': None # set to time in seconds if otherwise
			'srate': 250E6,
			'data_size': 32768, #16 bit samples
			'acq_len': 16384,
			'num_avg': 20,
			'decimation': 1, # should always be set to 1 unless otherwise needed
			'two_channel': False,
			'master_channel': 1,
			'slave_channel': 2,
			'trig_lvl': 0.0
		}
		
		for k in kwargs.keys():
		
			if k in self.settings:
				self.__setattr__(k, kwargs[k])
			else:
				self.__setattr__(k, self.settings[k])

		try: 
			self.con = scpi(host = self.host, port = self.port, timeout = self.timeout)
		except: # Connection failed
			raise 
if __name__ == '__main__':
	dig = Pitaya(addr='192.168.0.69', name='Pitaya')
	