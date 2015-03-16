#!/usr/bin/env python3
#
# The MIT License (MIT)
#
# Copyright (C) 2015 - Francois Doray <francois.pierre-doray@polymtl.ca>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import time
import argparse
import re
import subprocess

try:
    from babeltrace import TraceCollection
except ImportError:
    # quick fix for debian-based distros
    sys.path.append("/usr/local/lib/python%d.%d/site-packages" %
                    (sys.version_info.major, sys.version_info.minor))
    from babeltrace import TraceCollection

demangle_cache = {}

# From http://stackoverflow.com/questions/6526500/c-name-mangling-library-for-python
def demangle(name):
    if name in demangle_cache:
        return demangle_cache[name]
    args = ['c++filt']
    args.extend([name])
    pipe = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = pipe.communicate()
    out = out.decode("utf-8")
    demangled = out.split("\n")
    demangle_cache[name] = demangled[0]
    assert len(demangled) == 2
    return demangled[0]

def clean_frame_name(name):
    name = re.sub(r'\+0x[a-f0-9]+(/0x[a-f0-9]+)*', '', name)
    first_parentesis = name.find("(")
    if first_parentesis == -1:
        return name
    between_parenthesis = name[name.find("(")+1:name.find(")")]
    if not between_parenthesis:
        return name
    return demangle(between_parenthesis)

class Latency:
    def __init__(self, start_ts, comm):
        self.start_ts = start_ts
        self.total_delay = 0
        self.comm = comm
        self.kernel_stacks = []
        self.user_stack = None

    def get_start_ts(self):
        return self.start_ts

    def set_total_delay(self, total_delay):
        self.total_delay = total_delay

    def has_total_delay(self):
        return self.total_delay != 0

    def add_kernel_stack(self, kernel_stack, delay):
        assert self.total_delay == 0
        self.kernel_stacks.append((kernel_stack, delay))

    def set_user_stack(self, user_stack):
        self.user_stack = user_stack

    def has_user_stack(self):
        return self.user_stack != None

    def stacks(self):
        if not self.has_user_stack():
            return
        assert self.has_total_delay()
        total_delay = 0
        for kernel_stack in self.kernel_stacks:
            stack = tuple(
                [clean_frame_name(frame) for frame in kernel_stack[0]] +
                ['-',] +
                [clean_frame_name(frame[0:frame.find(' ')])
                    for frame in self.user_stack] +
                ['[' + self.comm + ']',])
            assert kernel_stack[1] >= total_delay
            yield (stack, kernel_stack[1] - total_delay)
            total_delay = kernel_stack[1]
        assert total_delay <= self.total_delay

class TraceParser:
    def __init__(self, trace):
        self.trace = trace
        self.latencies_per_thread = {}

    def get_latencies_for_thread(self, pid):
        if pid not in self.latencies_per_thread:
            self.latencies_per_thread[pid] = []
        return self.latencies_per_thread[pid]

    def get_latency(self, pid, start_ts, comm):
        thread_latencies = self.get_latencies_for_thread(pid)
        
        if (not thread_latencies or
            thread_latencies[-1].get_start_ts() != start_ts):
            latency = Latency(start_ts, comm)
            thread_latencies.append(latency)
            return latency
        else:
            return thread_latencies[-1]

    def parse(self):
        # iterate over all the events
        for event in self.trace.events:
            method_name = "handle_%s" % event.name.replace(":", "_").replace("+", "_")
            # call the function to handle each event individually
            if hasattr(TraceParser, method_name):
                func = getattr(TraceParser, method_name)
                func(self, event)

    def generate_flame_graph(self):
        merged_stacks = {}

        for latencies in self.latencies_per_thread.values():
            for latency in latencies:
                for stack, delay in latency.stacks():
                    if stack in merged_stacks:
                        merged_stacks[stack] += delay
                    else:
                        merged_stacks[stack] = delay

        for stack, delay in merged_stacks.items():
            print(';'.join(reversed(stack)) + ' ' + str(delay))

    def handle_syscall_latency_stack(self, event):
        comm = event["comm"]
        pid = event["pid"]
        start_ts = event["start_ts"]
        delay = event["delay"]
        stack = event["stack"].splitlines()

        latency = self.get_latency(pid, start_ts, comm)
        latency.add_kernel_stack(stack, delay)

    def handle_syscall_latency(self, event):
        comm = event["comm"]
        pid = event["pid"]
        start_ts = event["start_ts"]
        delay = event["delay"]

        latency = self.get_latency(pid, start_ts, comm)
        latency.set_total_delay(delay)

    def handle_lttng_profile_off_cpu_sample(self, event):
        pid = event["vtid"]
        stack = event["stack"].splitlines()

        thread_latencies = self.get_latencies_for_thread(pid)
        if not thread_latencies:
            return

        # TODO: Libunwind does msync system calls, so it's possible to get
        # syscall_latency_stack events for new system calls before the
        # off_cpu_sample event has been generated. It's ok to set the same
        # userspace stack for all system calls that occured since the last
        # off_cpu_sample event.
        for i in range(1, min(len(thread_latencies), 3) + 1):
            latency = thread_latencies[-i]
            if not latency.has_total_delay():
                continue
            if latency.has_user_stack():
                break
            latency.set_user_stack(stack)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Trace parser')
    parser.add_argument('path', metavar="<path/to/trace>", help='Trace path')
    args = parser.parse_args()

    traces = TraceCollection()
    handle = traces.add_traces_recursive(args.path, "ctf")
    if handle is None:
        sys.exit(1)

    t = TraceParser(traces)
    t.parse()

    for h in handle.values():
        traces.remove_trace(h)

    t.generate_flame_graph()
