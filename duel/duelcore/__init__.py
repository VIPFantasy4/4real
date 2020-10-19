# -*- coding: utf-8 -*-

from .chain import *
from .gambler import *
from .exceptions import *

WAITING = 0
SERVING = 1
PENDING = 2

PRIORITY_LEVEL_HIGH = 1
PRIORITY_LEVEL_LOW = 2

BASE_TIMES = -15
DP_CLOSED_INTERVAL = [4, 17]
DP_LIFETIME = 4
GP_TIMEOUT = 10
PP_TIMEOUT = 7
MP_TIMEOUT = 20
BOT_DELAY = 2
