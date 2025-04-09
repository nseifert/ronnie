from digitizer import Pitaya 
import time
from matplotlib import pyplot as plt
import numpy as np 
from scipy.fftpack import fft, fftfreq

if __name__ == "__main__":
    FREQ = 10 # GHz
    NUM_AVERAGES = 10

    # Set up digitizer
    dig = Pitaya(host='192.168.0.2', name='Pitaya',
                 timeout=5.0,
                 two_channel= True,
                 trig_lvl = 0.1,
                 data_size = 30000, #4 ns per point; 250 pts per us
                 acq_len = 30000,)
    
    dig.ext_clock() # Enable external clock
    # Enable trigger source on Out1 --> CH2 Trig
    #dig.set_synth(freq=30E4, amp=1.0, channel=0,type='SINE')

    print(f'Building accumulation array of dimensions {dig.data_size} x {NUM_AVERAGES}')
    accumulated = np.zeros((int(dig.data_size), NUM_AVERAGES))
    for i in range(NUM_AVERAGES):
        accumulated[:,i] = dig.acquire()[0]
        print(f'Acquired {i+1}/{NUM_AVERAGES} acquistions')
    
    averaged = np.mean(accumulated,axis=1)

    # Calc fft
    out_fft = np.abs(fft(averaged))
    out_fft_freq = fftfreq(len(averaged),d=1/250E6)
    fft_mask = out_fft_freq > 0

    fig, ax = plt.subplots(3)
    for i in range(NUM_AVERAGES):
        ax[0].plot(accumulated[:,i],label=f'Shot {i}')
        ax[0].scatter(x=np.arange(0,len(accumulated[:,i]),1),y=accumulated[:,i],marker='x',color='k',s=5)
    ax[1].plot(averaged, 'r', label='Average acq')
    ax[2].plot(out_fft_freq[fft_mask]/1E6, out_fft[fft_mask])
    ax[2].set_xlim([25,35])
    
    plt.show()

    np.savetxt(f'Cavity_Decay\\10GHz_ON_RES_10dBm_all_acq.txt',accumulated)


        