import re
from multiprocessing import Pipe, Process
from typing import Union

import numpy as np
import pandas as pd

from config.settings import Settings
from convertor import *
from rsm500.bucket import Bucket
from visualization import ScanPlotter


class Scan:
    pattern = {
        'escan': 'DM',
        **dict.fromkeys(['ascan', 'rscan', 'a2scan', 'r2scan'], 'DS')
    }

    x_scale = {
        MOTOR_0: 'reel [rev]',
        MOTOR_1: 'theta [grad]',
        MOTOR_2: '2theta [grad]',
        MOTOR_3: 'y [mm]',
    }

    def __init__(self, rsm: Bucket, settings: Settings):
        self.rsm = rsm
        self.settings = settings
        self.results = None

        self.initial_state()

    def initial_state(self):
        self.results = pd.DataFrame(columns=['counter_1', 'counter_2'])
        self.rsm.motor_select(4)    # remove voltage from all motors

    def motor_scan(self,
                   scan_type: str,
                   motor: int,
                   start_val: float,  # it is assumed that the motor is already in this position
                   steps_num: int,
                   step_val: float,
                   exposure: float,
                   motor2: int = None):

        meta = {'scan_type': scan_type,
                'exposure': f'{exposure} s'}

        motors = [motor] if motor2 is None else [motor, motor2]
        directions = [DIRECTION['positive'][motor] if step_val > 0 else DIRECTION['negative'][motor]
                      for motor in motors]
        step_vals = [step_val * i for i in range(1, len(motors) + 1)]   # step for the motor 2 is twice greater

        self.results.index.name = self.x_scale[motor]
        file_num = self.max_file_number(self.pattern[scan_type] + r'_(\d*).txt')

        pipe, plot_process = self.initialize_plotter(scan_type, {'x_scale': self.x_scale[motor], 'y_scale': 'Counts'})

        was_stopped = False
        for step_num in range(steps_num):
            data = self.measurement(exposure)

            # if the measurement was interrupted - stop scan
            if data is None:
                was_stopped = True
                break

            # Add obtained data to `results` attribute of the Scan object
            value = start_val + step_num * step_val
            self.results.loc[value] = data

            pipe.send(self.results)  # send results to parallel process to plot them
            self.save_results(self.pattern[scan_type], file_num, meta)

            # exclude motor move from last step
            if step_num == steps_num - 1:
                break

            for motor, direction, step_val in zip(motors, directions, step_vals):
                self.rsm.motor_select(motor)
                bucket_pos_before_moving = self.rsm.motor_get_position()    # position of the motor in the controller
                # FIXME: if motor step will be >32768, an error will rise
                self.rsm.motor_move(direction, to_motor_steps(motor, abs(step_val)))

                # if the motor moving was interrupted - stop scan
                if not self.rsm.motor_moving():
                    was_stopped = True
                    if motor != MOTOR_0:
                        delta = self.rsm.motor_get_position() - bucket_pos_before_moving
                        self.settings.change_motor_apos(motor, delta)
                    break

                if motor != MOTOR_0:
                    self.settings.change_motor_apos(motor, to_motor_steps(motor, step_val))

            if was_stopped:
                break

        plot_process.terminate()
        self.initial_state()

        return was_stopped

    def eff(self):
        pass

    def manual_scan(self, exposure: float, time_steps_on_plot: int):
        # TODO: add parameters to settings
        meta = {'scan_type': 'mscan'}
        self.results = pd.DataFrame(data=[*np.zeros((time_steps_on_plot, 2))], columns=['counter_1', 'counter_2'])
        self.results.index = np.arange(-time_steps_on_plot * exposure, 0, exposure)
        pipe, plot_process = self.initialize_plotter(meta['scan_type'], {'x_scale': 'time [sec]', 'y_scale': 'CPS'})

        elapsed_time = 0
        while True:
            data = self.measurement(exposure)

            if data is None:
                break

            self.results.loc[elapsed_time] = list(map(lambda x: x / exposure, data))    # data in counts per second
            self.results.drop([self.results.index[0]], inplace=True)
            pipe.send(self.results)
            elapsed_time += exposure

        plot_process.terminate()
        self.initial_state()

    @staticmethod
    def initialize_plotter(scan_mode: str, scales: dict) -> Pipe and Process:
        data_pipe, plot_pipe = Pipe()
        plotter = ScanPlotter()
        plot_process = Process(target=plotter, args=(plot_pipe, scan_mode, scales), daemon=True)
        plot_process.start()

        return data_pipe, plot_process

    def measurement(self, exposure: Union[int, float]):
        self.rsm.exposure_set(int(exposure * 10))
        self.rsm.counter_start()
        if self.rsm.counter_working():  # if the measurement was not interrupted, return the data obtained
            return [self.rsm.counter_get(COUNTER_1), self.rsm.counter_get(COUNTER_2)]
        return None

    def max_file_number(self, pattern: str):
        # list of all .txt files in the directory with data files
        # data_files = list(filter(lambda f: '.txt' in f, os.listdir(self.settings.path_for_files_save)))
        data_files = [f for f in os.listdir(self.settings.path_for_files_save) if f.endswith('.txt')]
        # list of file numbers
        # nums_list = list(map(lambda f: re.findall(pattern, f), data_files))
        # nums_list = [int(el[0]) for el in nums_list if len(el) > 0]
        nums_list = [int(re.findall(pattern, f)[0]) for f in data_files if re.findall(pattern, f)]

        return max(nums_list) if nums_list else 0

    def save_results(self, file_symbol: str, file_num: int, meta_data: dict):
        # form new file name: DM_{four digits}.txt, for example: DM_0012.txt
        new_file = f'{file_symbol}_{str.zfill(str(file_num + 1), 4)}.txt'

        # save metadata at the header of the file
        with open(self.settings.path_for_files_save + new_file, 'w') as file:
            for key, value in meta_data.items():
                file.write(f'# {key}:\t{value}\n')   # definition of metadata string style
            file.write('\n')

        self.results.to_csv(self.settings.path_for_files_save + new_file,
                            sep='\t',
                            mode='a',
                            float_format='%.3f')
