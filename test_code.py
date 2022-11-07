import serial
import io
import sys

class Motor:

    def execute(self, cmd: str, output=False):
        if self.isOpen():
            if '\n' not in cmd:
                cmd += '\n'
            print('command is: {:}'.format(cmd))
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

    def flush_output(self):
        self.connection.flush()
        output = []
        for _ in range(10):
            temp = self.connection.read()
            output.append(temp)
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
        self.timeout = 1/60.

        self.raw_connection = serial.Serial(self.addr, self.baud, timeout=self.timeout)
        self.connection = io.TextIOWrapper(io.BufferedRWPair(self.raw_connection, self.raw_connection))
        print('Connection to Ronnie is currently {:}'.format(self.isOpen()))


if __name__ == '__main__':

    try:
        ronnie = Motor()
        out = ronnie.set_velocity(velocity=0, output=True)

        print(out)

    except:
        ronnie.close_connection()
        raise SystemExit(0)