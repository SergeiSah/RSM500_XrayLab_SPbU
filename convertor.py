from config.definitions import *


def rev_to_steps(rev: float) -> int:
    return int(rev * 75000)  # TODO: 75000 determine in settings


def distance_to_steps(distance: float) -> int:
    # TODO: determine dependence of distance on motor step
    return int(distance)


def degree_to_steps(degree: float) -> int:
    return int(round(degree * 8000 / 90))


def step_to_revs(motor_step: int) -> float:
    return round(motor_step / 75000, 4)


def step_to_degrees(motor_step: int) -> float:
    return round(motor_step / 8000 * 90, 4)


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