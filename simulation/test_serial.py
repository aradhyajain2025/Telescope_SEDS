"""Checks the serial front-end with a fake stream (no COM port needed)."""
import threading
import time

import onstep_sim


class FakeStream:
    def __init__(self, script):
        self.inbox, self.out, self.done = list(script), b"", False

    def read(self, n):
        time.sleep(0.01)
        return self.inbox.pop(0).encode() if self.inbox else None

    def write(self, b):
        self.out += b


m = onstep_sim.MountModel(time_scale=50, seed=1)
st = FakeStream([":GVP#:GVN#", ":Sr05:35:17#:Sd-05*23:14#", ":MS#", ":GR#:GD#"])
onstep_sim.serve_serial(None, m, stream=st)
print(st.out)
assert st.out.startswith(b"On-Step#4.24s (sim)#11" + b"0"), st.out
import re
assert re.search(rb"\d\d:\d\d:\d\d#[+-]\d\d\*\d\d:\d\d#$", st.out), st.out
print("serial front-end OK")
