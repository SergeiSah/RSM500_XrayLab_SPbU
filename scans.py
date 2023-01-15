import pandas as pd
import numpy as np
from constants import *
from bucket import Bucket
import time
import keyboard


class Scan:

    def __init__(self, rsm: Bucket):
        self.rsm = rsm
        self.results = pd.DataFrame(columns=['x_scale', 'counter_1', 'counter_2'])
        self.is_working = False

    def en_scan(self, direction: int, exposure: int, steps_num: int, step: int, start_rev: float):
        self.rsm.motor_select(MOTOR_0)
        self.results.rename({'x_scale': 'energy'}, inplace=True)
        sign = {1: 1, 0: -1}[direction]

        for step_num in range(steps_num + 1):
            data = self.measurement(exposure)

            # Attempt to realise interruption
            if data is None:
                break
            if not self.rsm.motor_moving():
                break

            x_scale = pd.DataFrame({'energy': np.linspace(0, step_num * sign * step, steps_num + 1)})
            data = pd.concat([x_scale, data], axis=1)
            self.results = pd.concat([self.results, data])

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
            return pd.DataFrame({'counter_1': self.rsm.counter_get(FIRST_COUNTER),
                                 'counter_2': self.rsm.counter_get(SECOND_COUNTER)})
        return None

    def save_results(self):
        pass


if __name__ == '__main__':
    print(np.linspace(0, 3 * -10, 4))
