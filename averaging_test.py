from digitizer import Pitaya 
import time
from matplotlib import pyplot as plt
import numpy as np 

if __name__ == "__main__":
    NUM_AVERAGES = 100

    # Set up digitizer
    dig = Pitaya(host='192.168.0.2', name='Pitaya',
                 timeout=5.0,
                 two_channel= False,
                 trig_lvl = 0.025,
                 data_size = 16384//8,
                 acq_len = 16384//8)

    print(f'Building accumulation array of dimensions {dig.data_size} x {NUM_AVERAGES}')
    accumulated = np.zeros((int(dig.data_size), NUM_AVERAGES))
    for i in range(NUM_AVERAGES):
        accumulated[i,:] = dig.acquire()
        print(f'Acquired {i+1}/{NUM_AVERAGES} acquistions')
    
    averaged = np.mean(accumulated,axis=1)
    plt.plot(accumulated[0,:],'--',label='First shot')
    plt.plot(averaged, label='Average acq')
    plt.show()

        