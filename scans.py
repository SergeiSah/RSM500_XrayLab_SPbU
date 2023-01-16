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
        self.results = pd.DataFrame(columns=['x_scale', 'counter_1', 'counter_2'])
        self.path_to_files = Settings().path_for_files_save

    def en_scan(self, direction: int, exposure: int, steps_num: int, step_rev: float, start_rev: float):
        self.rsm.motor_select(MOTOR_0)
        self.results.rename(columns={'x_scale': 'rev'}, inplace=True)
        sign = {1: 1, 0: -1}[direction]
        file_num = self.max_file_number()

        for step_num in range(steps_num + 1):
            data = self.measurement(exposure)

            # Attempt to realise interruption
            if data is None:
                break

            self.rsm.motor_move(direction, rev_to_steps(step_rev))
            if not self.rsm.motor_moving():
                break

            # Add obtained data to `results` attribute of the Scan object
            rev = start_rev + step_num * sign * step_rev
            x_scale = pd.DataFrame({'rev': [rev]})
            data = pd.concat([x_scale, data], axis=1)
            self.results = pd.concat([self.results, data])
            self.save_results(file_num)

        self.rsm.motor_select(4)

    def dscan(self):
        pass

    def d2scan(self):
        pass

    def eff(self):
        pass

    def measurement(self, exposure: int):
        self.rsm.exposure_set(exposure * 10)
        self.rsm.counter_start()
        if self.rsm.counter_working():
            return pd.DataFrame({'counter_1': [self.rsm.counter_get(FIRST_COUNTER)],
                                 'counter_2': [self.rsm.counter_get(SECOND_COUNTER)]})
        return None

    def max_file_number(self):
        data_files = list(filter(lambda f: '.txt' in f, os.listdir(self.path_to_files)))
        nums_list = list(map(lambda f: int(re.findall(r"DM_(\d*).txt", f)[0]), data_files))
        if len(nums_list) == 0:
            return 0
        return max(nums_list)

    def save_results(self, file_num):
        new_file = f'DM_{str.zfill(str(file_num + 1), 4)}.txt'
        self.results.to_csv(self.path_to_files + new_file, sep='\t', index=False)


if __name__ == '__main__':
    print()
