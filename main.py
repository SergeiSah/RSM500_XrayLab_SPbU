import re

import serial

from command_run import CommandRunner
from config.settings import Settings
from rsm500.bucket import Bucket


def main():
    """
    Program works as a command prompt. User should input commands in a form 'mode <parameter> [parameter...]'. All
    available modes are presented in the CommandRunner().modes dictionary of the command_run.py module. To close the
    program, one should input 'close', 'quit', 'exit', 'c' or 'q'.

    :return: None
    """
    s = Settings()  # global settings of the program

    # converts command to byte code and sends it to the controllers of the bucket of RSM
    rsm = Bucket(serial.Serial(port=s.port, baudrate=s.baudrate))
    cr = CommandRunner(rsm, s)

    while True:
        # extraction from the command the mode name and arguments
        mode, *args = re.sub('\s+', ' ', input('> ').strip()).split(' ')

        if mode in ['close', 'quit', 'exit', 'c', 'q']:
            break

        cr.run_command(mode, *args)


if __name__ == '__main__':
    main()