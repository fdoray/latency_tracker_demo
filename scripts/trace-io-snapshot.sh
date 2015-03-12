#!/bin/bash

#lttng-sessiond --extra-kmod-probes=latency_tracker -d
lttng create --snapshot

lttng enable-channel k -k --subbuf-size 4M
lttng enable-event -c k -k sched_switch,block_rq_complete,block_rq_issue,block_bio_remap,block_bio_backmerge,netif_receive_skb,net_dev_xmit,sched_process_fork,sched_process_exec,lttng_statedump_process_state,lttng_statedump_file_descriptor,lttng_statedump_block_device,writeback_pages_written,mm_vmscan_wakeup_kswapd,mm_page_free,mm_page_alloc,block_dirty_buffer,irq_handler_entry,irq_handler_exit,softirq_entry,softirq_exit,softirq_raise
lttng enable-event -c k -k syscall_latency
lttng enable-event -c k -k syscall_latency_stack
lttng enable-event -c k -k --syscall -a

lttng enable-channel u -u --subbuf-size 1M
lttng enable-event -c u -u lttng_profile:off_cpu_sample
lttng add-context -c u -u -t vtid

lttng start

while true; do
    cat /proc/syscalls
    echo 'Recording snapshot...'
    lttng snapshot record
done

lttng stop
lttng destroy
