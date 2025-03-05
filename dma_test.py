import time
import matplotlib.pyplot as plt
import numpy as np

import redpitaya_scpi as scpi

IP = '192.168.0.2'          # local IP of Red Pitaya
rp = scpi.scpi(IP)            # open socket connection with Red Pitaya


## size in samples 16Bit
DATA_SIZE = 1024 * 16          # ((1024 * 1024 * 128) / 2)        ## for 128 MB ##
READ_DATA_SIZE = 1024 * 16     # (1024 * 256)                     ## for 128 MB ##

dec = 32
trig_lvl = 0

print("Start program")
## Reset Acquisition
rp.tx_txt('ACQ:RST')

# Get Memory region
start_address = int(rp.txrx_txt('ACQ:AXI:START?'))
size = int(rp.txrx_txt('ACQ:AXI:SIZE?'))
start_address2 = round(start_address + size/2)

print(start_address)
print(size)

print(f"Reserved memory Start: {start_address:x} Size: {size:x}\n")

# Set decimation
rp.tx_txt(f"ACQ:AXI:DEC {dec}")

# Set units
rp.tx_txt('ACQ:AXI:DATA:Units VOLTS')

# Set trigger delay for both channels
rp.tx_txt(f"ACQ:AXI:SOUR1:Trig:Dly {DATA_SIZE}")
rp.tx_txt(f"ACQ:AXI:SOUR2:Trig:Dly {DATA_SIZE}")

# Set-up the Channel 1 and channel 2 buffers to each work with half the available memory space.
rp.tx_txt(f"ACQ:AXI:SOUR1:SET:Buffer {start_address},{size/2}")
rp.tx_txt(f"ACQ:AXI:SOUR2:SET:Buffer {start_address2},{size/2}")

# Enable DMA
rp.tx_txt('ACQ:AXI:SOUR1:ENable ON')
rp.tx_txt('ACQ:AXI:SOUR2:ENable ON')
print('Enable CHA and CHB\n')

# Specify the acquisition trigger
rp.tx_txt(f"ACQ:TRig:LEV {trig_lvl}")


## ACQUISITION

rp.tx_txt('ACQ:START')
rp.tx_txt('ACQ:TRig CH1_PE')


print("Waiting for trigger\n")

# Wait for trigger
while 1:
    rp.tx_txt("ACQ:TRig:STAT?")
    if rp.rx_txt() == 'TD':
        print("Triggered")
        time.sleep(1)
        break

# wait for fill adc buffer
while 1:
    rp.tx_txt('ACQ:AXI:SOUR1:TRig:FILL?')
    if rp.rx_txt() == '1':
        print('DMA buffer full\n')
        break

# Stop Acquisition
rp.tx_txt('ACQ:STOP')

## Get write pointer at trigger location
posChA = int(rp.txrx_txt('ACQ:AXI:SOUR1:Trig:Pos?'))
posChB = int(rp.txrx_txt('ACQ:AXI:SOUR2:Trig:Pos?'))
print(posChA, posChB)

## Read & plot

rp.tx_txt(f"ACQ:AXI:SOUR1:DATA:Start:N? {posChA},{READ_DATA_SIZE}")
signal_str = rp.rx_txt()
rp.tx_txt(f"ACQ:AXI:SOUR2:DATA:Start:N? {posChB},{READ_DATA_SIZE}")
signal_str2 = rp.rx_txt()

print("Data Acquired\n")

buff1 = list(map(float, signal_str.strip('{}\n\r').replace("  ", "").split(',')))
buff2 = list(map(float, signal_str2.strip('{}\n\r').replace("  ", "").split(',')))

plt.plot(buff1, label="Ch1")
plt.plot(buff2, label="Ch2")
plt.legend()
plt.show()



# Writing data into a text file
# with open("Python_SCPI/out.txt", "w", encoding="ascii") as fp:
#     read_size = 0
#
#     while read_size < DATA_SIZE:
#         size1 = READ_DATA_SIZE
#         size2 = READ_DATA_SIZE
#         rp.tx_txt(f"ACQ:AXI:SOUR1:DATA:Start:N? {posChA},{size1}")
#         signal_str = rp.rx_txt()
#         rp.tx_txt(f"ACQ:AXI:SOUR2:DATA:Start:N? {posChB},{size2}")
#         signal_str2 = rp.rx_txt()
#
#         buff1 = list(map(float, signal_str.strip('{}\n\r').replace("  ", "").split(',')))
#         buff2 = list(map(float, signal_str2.strip('{}\n\r').replace("  ", "").split(',')))
#
#         for i in range(0, READ_DATA_SIZE):
#             fp.write(f"{i+1:6d}:  {buff1[i]:6f}\t{buff2[i]:6f}\n")
#
#         posChA += size1
#         posChB += size2
#         read_size += READ_DATA_SIZE
#         print(f"Saved data size {read_size}\n")


## Close connection with Red Pitaya
rp.tx_txt('ACQ:AXI:SOUR1:ENable OFF')
rp.tx_txt('ACQ:AXI:SOUR2:ENable OFF')
print('Releasing resources\n')
print("End program")
rp.close()