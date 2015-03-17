#!/bin/bash

destroy()
{
  lttng stop
  lttng destroy
  echo "You can now launch the analyses scripts on /$TRACEPATH"
  exit 0
}

#lttng-sessiond --extra-kmod-probes=latency_tracker -d
lttng create --snapshot >/tmp/lttngout
[[ $? != 0 ]] && exit 2
export TRACEPATH=$(grep Default /tmp/lttngout | cut -d'/' -f2-)

trap "destroy" SIGINT SIGTERM

lttng enable-channel k -k --subbuf-size 2M
lttng enable-event -c k -k sched_switch,block_rq_complete,block_rq_issue,block_bio_remap,block_bio_backmerge,netif_receive_skb,net_dev_xmit,sched_process_fork,sched_process_exec,lttng_statedump_process_state,lttng_statedump_file_descriptor,lttng_statedump_block_device,writeback_pages_written,mm_vmscan_wakeup_kswapd,mm_page_free,mm_page_alloc,block_dirty_buffer,irq_handler_entry,irq_handler_exit,softirq_entry,softirq_exit,softirq_raise
lttng enable-event -c k -k syscall_latency
lttng enable-event -c k -k syscall_latency_stack
lttng enable-event -c k -k --syscall -a

lttng enable-channel u -u
lttng enable-event -c u -u lttng_profile:off_cpu_sample
lttng add-context -c u -u -t vtid

lttng start

while true; do
    cat /proc/syscalls
    echo 'Recording snapshot...'
    lttng stop
    lttng snapshot record
    lttng start
    echo 'Did record snapshot.'
done

lttng stop
lttng destroy
