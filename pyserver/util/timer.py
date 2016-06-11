import sys
import time

if sys.platform == 'win32':
    # On Windows, the best timer is time.clock
    timer = time.clock
else:
    # On most other platforms the best timer is time.time
    timer = time.time
