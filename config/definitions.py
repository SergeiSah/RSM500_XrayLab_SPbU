import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

COUNTER_1 = 2   # the HV electron multiplier before the sample holder
COUNTER_2 = 3   # after the sample holder

LOWER_THRESHOLD = 0  # identifier for the lower threshold for counts in a detector
UPPER_THRESHOLD = 1  # for upper threshold

MOTOR_0 = 0  # energy scan
MOTOR_1 = 1  # rotation of the sample holder
MOTOR_2 = 2  # rotation of the second detector
MOTOR_3 = 3  # sample holder movement along 'x' axis

KEY_FOR_INTERRUPTION = 'ctrl+q'  # TODO: Перенести в settings

DIRECTION = {
    'negative': {MOTOR_0: 0, MOTOR_1: 0, MOTOR_2: 1, MOTOR_3: 0},
    'positive': {MOTOR_0: 1, MOTOR_1: 1, MOTOR_2: 0, MOTOR_3: 1}
}
