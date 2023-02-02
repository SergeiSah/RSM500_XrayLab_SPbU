import re
from multiprocessing import Pipe, Process
from typing import Union

import numpy as np
import pandas as pd

from bucket import Bucket
from convertor import *
from settings import Settings
from visualization import Plotter


class Scan:
    pattern = {
        'escan': 'DM',
        **dict.fromkeys(['ascan', 'rscan'], 'DS')
    }

    x_scale = {
        MOTOR_0: 'rev',
        MOTOR_1: 'grad',
        MOTOR_2: 'grad',
        MOTOR_3: 'mm',
    }

    def __init__(self, rsm: Bucket, settings: Settings):
        self.rsm = rsm
        self.settings = settings
        self.results = None

        self.initial_state()

    def initial_state(self):
        self.results = pd.DataFrame(columns=['counter_1', 'counter_2'])
        self.rsm.motor_select(4)    # remove voltage from all motors

    def ascan(self, motor_num: int, steps_num: int, step_val: float, start: float, exposure: float):
        meta = {'scan_type': 'ascan',
                'exposure': f'{exposure} s'}

        self.rsm.motor_select(motor_num)
        direction = DIRECTION['positive'][motor_num] if step_val > 0 else DIRECTION['negative'][motor_num]
        pass

    def rscan(self):
        pass

    def one_motor_scan(self,
                       scan_type: str,
                       motor_num: int,
                       exposure: float,
                       steps_num: int,
                       step_val: float,
                       start_val: float):

        meta = {'scan_type': scan_type,
                'exposure': f'{exposure} s'}

        self.rsm.motor_select(motor_num)
        direction = DIRECTION['positive'][motor_num] if step_val > 0 else DIRECTION['negative'][motor_num]
        self.results.index.name = self.x_scale[motor_num]
        file_num = self.max_file_number(self.pattern[scan_type] + r'_(\d*).txt')

        pipe, plot_process = self.initialize_plotter(scan_type)

        was_stopped = False
        for step_num in range(steps_num + 1):
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

            bucket_pos_before_moving = self.rsm.motor_get_position()    # position of motor in controller
            self.rsm.motor_move(direction, to_motor_steps(motor_num, abs(step_val)))

            # if the motor moving was interrupted - stop scan
            if not self.rsm.motor_moving():
                was_stopped = True
                if motor_num != MOTOR_0:
                    delta = self.rsm.motor_get_position() - bucket_pos_before_moving
                    self.settings.change_motor_apos(motor_num, delta)
                break

            if motor_num != MOTOR_0:
                self.settings.change_motor_apos(motor_num, to_motor_steps(motor_num, step_val))

        plot_process.terminate()
        self.initial_state()

        return was_stopped

    def d2scan(self):
        pass

    def eff(self):
        pass

    def manual_scan(self, exposure: float, time_steps_on_plot: int):
        # TODO: add parameters to settings
        meta = {'scan_type': 'mscan'}
        self.results = pd.DataFrame(data=[*np.zeros((time_steps_on_plot, 2))], columns=['counter_1', 'counter_2'])
        self.results.index = np.arange(-time_steps_on_plot * exposure, 0, exposure)
        pipe, plot_process = self.initialize_plotter(meta['scan_type'])

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
    def initialize_plotter(scan_mode: str) -> Pipe and Process:
        data_pipe, plot_pipe = Pipe()
        plotter = Plotter()
        plot_process = Process(target=plotter, args=(plot_pipe, scan_mode), daemon=True)
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
        data_files = list(filter(lambda f: '.txt' in f, os.listdir(self.settings.path_for_files_save)))
        # list of file numbers: DM_{number}.txt
        nums_list = list(map(lambda f: int(re.findall(pattern, f)[0]), data_files))

        if len(nums_list) == 0:
            return 0
        return max(nums_list)

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
