from digitizer import Pitaya 
import time
from matplotlib import pyplot as plt
import numpy as np 

if __name__ == "__main__":
    NUM_AVERAGES = 10

    # Set up digitizer
    dig = Pitaya(host='192.168.0.2', name='Pitaya',
                 timeout=5.0,
                 two_channel= True,
                 trig_lvl = 0.25,
                 data_size = 5000,
                 acq_len = 5000,)
    
    dig.ext_clock() # Enable external clock
    # Enable trigger source on Out1 --> CH2 Trig
    dig.set_synth(freq=1.0E4, amp=1.0, channel=0,type='PWM')

    print(f'Building accumulation array of dimensions {dig.data_size} x {NUM_AVERAGES}')
    accumulated = np.zeros((int(dig.data_size), NUM_AVERAGES))
    for i in range(NUM_AVERAGES):
        accumulated[:,i] = dig.acquire()[0]
        print(f'Acquired {i+1}/{NUM_AVERAGES} acquistions')
    
    averaged = np.mean(accumulated,axis=1)
    fig, ax = plt.subplots(2)
    for i in range(NUM_AVERAGES):

        ax[0].plot(accumulated[:,i]+np.max(accumulated[:,i]),label=f'Shot {i}')
    ax[1].plot(averaged, 'r', label='Average acq')
    
    plt.show()

        