from definitions import *


def rev_to_steps(rev: float) -> int:
    return int(rev * 75000)  # TODO: 75000 determine in settings


def distance_to_steps(distance: float) -> int:
    # TODO: determine dependence of distance on motor step
    return int(distance)


def grad_to_steps(grad: float) -> int:
    return int(round(grad * 8000 / 90))


def step_to_revs(motor_step: int) -> float:
    return round(motor_step / 75000, 4)


def step_to_grads(motor_step: int) -> float:
    return round(motor_step / 8000 * 90, 4)


def step_to_distance(motor_step: int) -> float:
    # TODO: determine dependence of distance on motor step
    pass


def to_motor_steps(motor: int, step: float) -> int:
    return {
        MOTOR_0: rev_to_steps(step),
        **dict.fromkeys([MOTOR_1, MOTOR_2], grad_to_steps(step)),
        MOTOR_3: distance_to_steps(step)
    }[motor]