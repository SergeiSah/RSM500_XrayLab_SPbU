def rev_to_steps(rev: float) -> int:
    return int(rev * 75000)  # TODO: 75000 determine in settings


def grad_to_steps(grad: float) -> int:
    return int(grad * 8000 / 90)


def step_to_revs(step: int) -> float:
    return round(step / 75000, 4)


def step_to_grads(step: int) -> float:
    return round(step / 8000 * 90, 2)


def to_step(motor: int, step: float) -> int:
    return {
        0: rev_to_steps(step),
        **dict.fromkeys([1, 2, 3], grad_to_steps(step))
    }[motor]