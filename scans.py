import pandas as pd
from settings import Settings
from config.definitions import *
from convertor import *
from bucket import Bucket
import os
import re


class Scan:

    def __init__(self, rsm: Bucket):
        self.rsm = rsm
        self.path_to_files = Settings().path_for_files_save
        self.results = None

        self.initial_state()

    def initial_state(self):
        self.results = pd.DataFrame(columns=['x_scale', 'counter_1', 'counter_2'])
        self.rsm.motor_select(4)    # remove voltage from all motors

    def en_scan(self, direction: int, exposure: int, steps_num: int, step_rev: float, start_rev: float):
        meta = {'scan_type': 'energy scan',
                'exposure': f'{exposure} s'}
        self.rsm.motor_select(MOTOR_0)
        self.results.rename(columns={'x_scale': 'rev'}, inplace=True)
        sign = {1: 1, 0: -1}[direction]     # 1 - rev increasing, 0 - rev decreasing
        file_num = self.max_file_number()   # determine the file number to save results

        for step_num in range(steps_num + 1):
            data = self.measurement(exposure)

            # if the measurement was interrupted - stop scan
            if data is None:
                break

            self.rsm.motor_move(direction, rev_to_steps(step_rev))
            # if the motor moving was interrupted - stop scan
            if not self.rsm.motor_moving():
                break

            # Add obtained data to `results` attribute of the Scan object
            rev = start_rev + step_num * sign * step_rev
            x_scale = pd.DataFrame({'rev': [rev]})
            data = pd.concat([x_scale, data], axis=1)
            self.results = pd.concat([self.results, data])

            self.save_results(file_num, meta)

        self.initial_state()

    def dscan(self):
        pass

    def d2scan(self):
        pass

    def eff(self):
        pass

    def measurement(self, exposure: int):
        self.rsm.exposure_set(exposure * 10)
        self.rsm.counter_start()
        if self.rsm.counter_working():  # if the measurement was not interrupted, return the data obtained
            return pd.DataFrame({'counter_1': [self.rsm.counter_get(FIRST_COUNTER)],
                                 'counter_2': [self.rsm.counter_get(SECOND_COUNTER)]})
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
        with open(self.path_to_files + new_file) as file:
            for key, value in meta_data.items():
                file.write(f'# {key}: {value:>15}\n')   # definition of metadata string style

        self.results.to_csv(self.path_to_files + new_file,
                            sep='\t',
                            index=False,
                            mode='a',
                            float_format='%.3f')


if __name__ == '__main__':
    print()
