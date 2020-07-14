# -*- coding: utf-8 -*-

import inspect


def generate_traceback():
    return inspect.getframeinfo(inspect.currentframe().f_back)


class DuelRuntimeError(RuntimeError):
    pass


class ChainRuntimeError(RuntimeError):
    pass


class DrawPhaseRuntimeError(RuntimeError):
    pass


class HumanOperationResume(RuntimeError):
    pass
