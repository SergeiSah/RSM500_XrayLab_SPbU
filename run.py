import re

import serial

from src.command_run import CommandRunner
from src.config import Settings
from src.rsm500.rsm_controller import RSMController


def main():
    """
    Program works as a command prompt. User should input commands in a form 'mode <parameter> [parameter...]'. All
    available modes are presented in the CommandRunner().modes dictionary of the command_run.py module. To close the
    program, one should input 'close', 'quit', 'exit', 'c' or 'q'.

    :return: None
    """
    s = Settings()  # global settings of the program

    # set port for the connection to the RSM controller
    RSMController.set_port(serial.Serial(port=s.port, baudrate=s.baudrate))
    cr = CommandRunner(s)

    while True:
        # extraction from the command the mode name and arguments
        mode, *args = re.sub('\s+', ' ', input('> ').strip()).split(' ')

        if mode in ['close', 'quit', 'exit', 'c', 'q']:
            break

        cr.run_command(mode, *args)


if __name__ == '__main__':
    main()