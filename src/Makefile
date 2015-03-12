override CFLAGS += -rdynamic -fno-omit-frame-pointer

all: mmap-demo io-demo sleep-demo

mmap-demo: mmap.c
	$(CC) -o $@ $(LDFLAGS) -pthread $(CFLAGS) $(AM_LDFLAGS) $(AM_CFLAGS) \
		$< $(LIBS)

io-demo: io.c
	$(CC) -o $@ $(LDFLAGS) $(CFLAGS) $(AM_LDFLAGS) $(AM_CFLAGS) \
		$< $(LIBS)

sleep-demo: sleep.c
	$(CC) -o $@ $(LDFLAGS) $(CFLAGS) $(AM_LDFLAGS) $(AM_CFLAGS) \
		$< $(LIBS)

clean:
	rm -f io-demo sleep-demo