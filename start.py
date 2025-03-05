import tkinter as tk
from tkinter import messagebox
import serial
import io
from threading import Thread
import time

class Motor:

	def execute(self, cmd: str, output=False):
		if self.isOpen():
			if '\n' not in cmd:
				cmd += '\n'
			#print('command is: {:}'.format(cmd))
			self.connection.write(cmd)
			

			if output: 
				return self.flush_output()
			else:
				self.flush_output()	  
				return True

		else: 
			return False 

	def set_velocity(self, velocity: int, output=False):
		
		return self.execute('SL {:}\r'.format(velocity), output=output)

	def read_velocity(self):
		return self.execute('PR V\r', output=True)	  

	def self_identify(self):
		return self.execute('PR AL\r', output=True)
	
	def read_position(self):
		return self.execute('PR P\r', output=True)
	
	def clear_position(self):
		return self.execute('P 0\r', output=True)

	def flush_output(self):
		self.connection.flush()
		output = []
		
		while True:
			temp = self.connection.read()
			output.append(temp)

			if not temp:
				break
			
		output = ''.join(output).split('\n')
		return output

	def close_connection(self):
		try:
			self.connection.close()
			return True
		except:
			raise 

	def isOpen(self):
		return self.raw_connection.is_open

	def __init__(self):
		self.addr = '/dev/ttyUSB0'
		self.baud = 9600
		self.timeout = 1/30
		
		self.velocity = 0
		
		self.raw_connection = serial.Serial(self.addr, self.baud, timeout=self.timeout)
		self.connection = io.TextIOWrapper(io.BufferedRWPair(self.raw_connection, self.raw_connection))
		# Initialize serial communication with motor	   
		self.__capacitor_discharging = False

		self.STEP_RESOLUTION = 51200

class StepperMotorControlApp:
	def __init__(self,root):
		self.root = root
		self.root.title("Stepper Motor Control")
		self.__active_motor = False

		# Initialize VISA resource manager
 

		# GUI Elements
		self.status_label = tk.Label(root, text="Motor Status: Disconnected", fg="red")
		self.status_label.pack(pady=10)

		self.connect_button = tk.Button(root, text="Connect", command=self.connect_motor)
		self.connect_button.pack(pady=5)

		self.velocity_label = tk.Label(root, text="Set Velocity (RPM):")
		self.velocity_label.pack(pady=5)
		
	
		self.velocity_entry = tk.Entry(root)
		self.velocity_entry.pack(pady=5)
		
		# Current velocity update thread
		self.cur_velocity = tk.StringVar(value='Current Velocity: 0')	   
		self.cur_velocity_label = tk.Label(root, textvariable=self.cur_velocity)
		self.cur_velocity_label.pack(pady=5)
		self.vel_thread = Thread(target=self.read_velocity)
		self.vel_thread.daemon = True
		self.vel_thread.start()

		self.set_velocity_button = tk.Button(root, text="Set Velocity", command=self.set_velocity)
		self.set_velocity_button.pack(pady=5)

		self.start_button = tk.Button(root, text="Start Motor", command=self.start_motor)
		self.start_button.pack(pady=5)

		self.stop_button = tk.Button(root, text="Stop Motor", command=self.stop_motor)
		self.stop_button.pack(pady=5)

		self.current_status_label = tk.Label(root, text="Current Status: Idle")
		self.current_status_label.pack(pady=10)

	def connect_motor(self):
		try:
			self.instrument = Motor()
			self.status_label.config(text="Motor Status: Connected", fg="green")
			messagebox.showinfo("Success", "Motor connected successfully!")
			self.__active_motor = True
			
		except Exception as e:
			messagebox.showerror("Error", f"Failed to connect to motor: {e}")

	def read_velocity(self):
		while True:
			try:
				if self.__active_motor:
					current_velocity = self.instrument.read_velocity()[2]
					self.cur_velocity_label.config('Current Velocity: {:}'.format(current_velocity))
					root.update()
					time.sleep(1)
				else: 
					self.cur_velocity.set('Current Velocity: 0'.format(current_velocity))
			except Exception as e:
				messagebox.showerror("Error", f"Failed to read motor velocity: {e}\n" + str(current_velocity))
				break
		
	def set_velocity(self):
		if self.instrument is None:
			messagebox.showerror("Error", "Motor is not connected!")
			return

		try:
			velocity = self.velocity_entry.get()
			if not velocity:
				messagebox.showerror("Error", "Please enter a velocity!")
				return

			# Send VISA command to set velocity (replace with actual command)
			self.instrument.velocity = velocity
			self.instrument.read_velocity()
			messagebox.showinfo("Success", f"Velocity set to {velocity} steps/sec")
		except Exception as e:
			messagebox.showerror("Error", f"Failed to set velocity: {e}")

	def start_motor(self):
		if self.instrument is None:
			messagebox.showerror("Error", "Motor is not connected!")
			return

		try:
			# Send VISA command to start motor (replace with actual command)
			self.instrument.set_velocity(self.instrument.velocity)
			self.instrument.read_velocity()
			self.current_status_label.config(text="Current Status: Running")
			messagebox.showinfo("Success", "Motor started successfully!")
		except Exception as e:
			messagebox.showerror("Error", f"Failed to start motor: {e}")

	def stop_motor(self):
		if self.instrument is None:
			messagebox.showerror("Error", "Motor is not connected!")
			return

		try:
			# Send VISA command to stop motor (replace with actual command)
			self.instrument.set_velocity(0)
			self.current_status_label.config(text="Current Status: Stopped")
			messagebox.showinfo("Success", "Motor stopped successfully!")
		except Exception as e:
			messagebox.showerror("Error", f"Failed to stop motor: {e}")

if __name__ == "__main__":
	root = tk.Tk()
	app = StepperMotorControlApp(root)
	app.root.mainloop()
