from command_run import CommandRunner
from settings import Settings
import re
from bucket import Bucket
import serial


def main():
    s = Settings()
    rsm = Bucket(serial.Serial(port=s.port, baudrate=s.baudrate))
    cr = CommandRunner(rsm)

    while True:
        # extraction from the command the mode name and arguments
        mode, *args = re.sub('\s+', ' ', input('> ').strip()).split(' ')
        args = [eval(arg) for arg in args]

        if mode in ['close', 'quit', 'c', 'q']:
            break

        cr.run_command(mode, *args)


if __name__ == '__main__':
    main()