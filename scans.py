import os
import re
from multiprocessing import Pipe, Process

import pandas as pd

from bucket import Bucket
from config.definitions import *
from convertor import *
from settings import Settings
from visualization import Plotter


class Scan:

    def __init__(self, rsm: Bucket):
        self.rsm = rsm
        self.path_to_files = Settings().path_for_files_save
        self.results = None

        self.initial_state()

    def initial_state(self):
        self.results = pd.DataFrame(columns=['x_scale', 'counter_1', 'counter_2'])
        self.rsm.motor_select(4)    # remove voltage from all motors

    def en_scan(self, exposure: int, steps_num: int, step_rev: float, start_rev: float):
        meta = {'scan_type': 'en_scan',
                'exposure': f'{exposure} s'}

        self.rsm.motor_select(MOTOR_0)
        self.results.rename(columns={'x_scale': 'rev'}, inplace=True)
        direction = DIRECTION['positive'][MOTOR_0] if step_rev > 0 else DIRECTION['negative'][MOTOR_0]
        file_num = self.max_file_number()   # determine the file number to save results

        # create parallel process for plotter and connection to it (pipe)
        pipe, plot_process = self.initialize_plotter(meta['scan_type'])

        was_stopped = False
        for step_num in range(steps_num + 1):
            data = self.measurement(exposure)

            # if the measurement was interrupted - stop scan
            if data is None:
                was_stopped = True
                break

            self.rsm.motor_move(direction, rev_to_steps(abs(step_rev)))
            # if the motor moving was interrupted - stop scan
            if not self.rsm.motor_moving():
                was_stopped = True
                break

            # Add obtained data to `results` attribute of the Scan object
            rev = start_rev + step_num * step_rev
            x_scale = pd.DataFrame({'rev': [rev]})
            data = pd.concat([x_scale, data], axis=1)
            self.results = pd.concat([self.results, data])

            pipe.send(self.results)  # send results to parallel process to plot them

            self.save_results(file_num, meta)

        plot_process.terminate()
        self.initial_state()

        return was_stopped

    def dscan(self):
        pass

    def one_motor_scan(self):
        # sceleton for wrappers dscan and en_scan
        pass

    def d2scan(self):
        pass

    def eff(self):
        pass

    @staticmethod
    def initialize_plotter(scan_mode: str) -> Pipe and Process:
        data_pipe, plot_pipe = Pipe()
        plotter = Plotter()
        plot_process = Process(target=plotter, args=(plot_pipe, scan_mode), daemon=True)
        plot_process.start()

        return data_pipe, plot_process

    def measurement(self, exposure: int):
        self.rsm.exposure_set(exposure * 10)
        self.rsm.counter_start()
        if self.rsm.counter_working():  # if the measurement was not interrupted, return the data obtained
            return pd.DataFrame({'counter_1': [self.rsm.counter_get(COUNTER_1)],
                                 'counter_2': [self.rsm.counter_get(COUNTER_2)]})
        return None

    def max_file_number(self):
        # list of all .txt files in the directory with data files
        data_files = list(filter(lambda f: '.txt' in f, os.listdir(self.path_to_files)))
        # list of file numbers: DM_{number}.txt
        nums_list = list(map(lambda f: int(re.findall(r"DM_(\d*).txt", f)[0]), data_files))

        if len(nums_list) == 0:
            return 0
        return max(nums_list)

    def save_results(self, file_num: int, meta_data: dict):
        # form new file name: DM_{four digits}.txt, for example: DM_0012.txt
        new_file = f'DM_{str.zfill(str(file_num + 1), 4)}.txt'

        # save metadata at the header of the file
        with open(self.path_to_files + new_file, 'w') as file:
            for key, value in meta_data.items():
                file.write(f'# {key}:\t{value}\n')   # definition of metadata string style
            file.write('\n')

        self.results.to_csv(self.path_to_files + new_file,
                            sep='\t',
                            index=False,
                            mode='a',
                            float_format='%.3f')


if __name__ == '__main__':
    print()
