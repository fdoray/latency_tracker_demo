#!/bin/bash

#lttng-sessiond --extra-kmod-probes=latency_tracker -d
lttng create

lttng enable-channel k -k
lttng enable-event -c k -k syscall_latency
lttng enable-event -c k -k syscall_latency_stack

lttng enable-channel u -u
lttng enable-event -c u -u lttng_profile:off_cpu_sample
lttng add-context -c u -u -t vtid

lttng start

echo 'Press any key to stop tracing.'
read

lttng stop
lttng destroy
echo 'Stopped tracing.'
