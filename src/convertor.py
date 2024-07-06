from .config import *


"""
MOTOR_0: 75000 motor steps ≡ 1 rev of the reel
MOTOR_1: 8000 motor steps ≡ 90 degrees,  90 / 8000 = 0.01125  
MOTOR_2: the same
MOTOR_3: 
"""


def rev_to_steps(rev: float) -> int:
    return int(rev * 75000)  # TODO: 75000 determine in settings


def distance_to_steps(distance: float) -> int:
    # TODO: determine dependence of distance on motor step
    return int(distance)


def degree_to_steps(degree: float) -> int:
    return int(round(degree / 0.01125))


def step_to_revs(motor_step: int) -> float:
    return motor_step / 75000


def step_to_degrees(motor_step: int) -> float:
    return round(motor_step * 0.01125, 5)


def step_to_distance(motor_step: int) -> float:
    # TODO: determine dependence of distance on motor step
    return float(motor_step)


def to_motor_steps(motor: int, unit_steps: float) -> int:
    return {
        MOTOR_0: rev_to_steps(unit_steps),
        **dict.fromkeys([MOTOR_1, MOTOR_2], degree_to_steps(unit_steps)),
        MOTOR_3: distance_to_steps(unit_steps)
    }[motor]


def to_step_units(motor: int, motor_steps: int) -> float:
    return {
        MOTOR_0: step_to_revs(motor_steps),
        **dict.fromkeys([MOTOR_1, MOTOR_2], step_to_degrees(motor_steps)),
        MOTOR_3: step_to_distance(motor_steps)
    }[motor]


def real_step(motor: int, step: float) -> float:
    return to_step_units(motor, to_motor_steps(motor, step))
