from scans import Scan
from bucket import Bucket
from inspect import signature
from convertor import *
from definitions import *


class CommandRunner:

    def __init__(self, rsm: Bucket):
        self.rsm = rsm
        self.modes = {
                'en_scan': self.run_en_scan,
                'move': self.run_motor_move
            }

    def run_command(self, mode, *args):
        try:
            self.modes[mode](*args)
        except AttributeError:
            print(f'Command {mode} does not exist.')

    def run_en_scan(self, *args):
        s = Scan(self.rsm)
        f_params = signature(s.en_scan).parameters  # determine number of arguments of the en_scan function

        if not args or len(args) != len(f_params):
            # TODO: Determine, why 1 sec exposure doesn't work
            exposure = int(input('Input exposure in seconds: '))
            step_num = int(input('Input number of steps: '))
            step = float(input('Input step value in rev of the reel: '))
            start = float(input('Input start rev of the reel: '))
            args = (exposure, step_num, step, start)

        s.en_scan(*args)

    def run_motor_move(self, *args):
        if not args or len(args) != 2:
            motor = int(input('Input motor number: '))
            steps = float(input('Input step: '))
            args = (motor, steps)

        if args[1] < 0:
            direction = DIRECTION['negative'][args[0]]
        elif args[1] > 0:
            direction = DIRECTION['positive'][args[0]]
        else:
            print('Step cannot be 0.')
            return -1

        self.rsm.motor_select(args[0])
        step = to_step(args[0], abs(args[1]))
        self.rsm.motor_move(direction, step)
        if self.rsm.motor_moving():
            print('Arrived')
        else:
            print('Interrupted')

        self.rsm.motor_select(4)


if __name__ == '__main__':
    cr = CommandRunner()
    print(cr.run_command('en_scan'))