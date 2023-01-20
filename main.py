import re

import serial

from bucket import Bucket
from command_run import CommandRunner
from settings import Settings


def main():
    s = Settings()
    rsm = Bucket(serial.Serial(port=s.port, baudrate=s.baudrate))
    cr = CommandRunner(rsm)

    while True:
        # extraction from the command the mode name and arguments
        mode, *args = re.sub('\s+', ' ', input('> ').strip()).split(' ')

        if mode in ['close', 'quit', 'c', 'q']:
            break

        cr.run_command(mode, *args)


if __name__ == '__main__':
    main()