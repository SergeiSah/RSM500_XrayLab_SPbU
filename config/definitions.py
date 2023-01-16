import os

ROOT_DIR = os.path.relpath(os.path.join(os.path.dirname(__file__), '../..'))

FIRST_COUNTER = 2   # The HV electron multiplier before the sample holder
SECOND_COUNTER = 3  # The HV electron multiplier after the sample holder

MOTOR_0 = 0  # Energy scan
MOTOR_1 = 1  # Rotation of the sample holder
MOTOR_2 = 2  # Rotation of the second detector
MOTOR_3 = 3  # Sample holder movement along 'x' axis

KEY_FOR_INTERRUPTION = 'q'  # TODO: Перенести в settings
