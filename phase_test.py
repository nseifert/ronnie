from digitizer import Pitaya 
import time
from matplotlib import pyplot as plt
import numpy as np 

if __name__ == "__main__":
    rng = np.random.default_rng()

    TOTAL_TIME = 5 * 60 # 5 minutes

    # Generate a set of random intervals to acquire and check phase
    # 1 to 25 seconds?
    INTERVALS = rng.integers(low=1,high=25, size=int(TOTAL_TIME/25))

    # Set up digitizer
    dig = Pitaya(host='192.168.0.2', name='Pitaya', timeout=5.0,
                 two_channel=False,
                 trig_lvl = 0.025,
                 data_size = 16384/8,
                 acq_len = 16384/8)

    # Set start_time
    start_time = time.time()
    final_time = start_time + TOTAL_TIME

    inter_idx = 0
    accumulated_data = []
    while True:
        cur_time = time.time() 
        if cur_time > final_time:
            break 
        if inter_idx > int(TOTAL_TIME/25) - 1:
            break 

        else: 
            print(f'Acquiring data; interval #{inter_idx}; wait time {INTERVALS[inter_idx]}')
            wait_time = INTERVALS[inter_idx]
            time.sleep(wait_time)

            data = dig.acquire()
            accumulated_data.append(data)
            inter_idx += 1
    print('Phase test complete. Plotting results.')
    for i in range(len(accumulated_data)):
        plt.plot(accumulated_data[i],label=f'Acquisition {i}')
    plt.show()
        