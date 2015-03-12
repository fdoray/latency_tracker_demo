// Copyright (c) 2015 Francois Doray <francois.pierre-doray@polymtl.ca>
//
// This file is part of trace-kit.
//
// trace-kit is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// trace-kit is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with trace-kit.  If not, see <http://www.gnu.org/licenses/>.
#include <stdio.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/stat.h>

static const char FILENAME[] = "file.bin";
static const int NUM_THREADS = 64;
static const int PAGE_SIZE = 4096;

int fd = -1;
int pages_per_thread = 0;

void DoSomeWork(long thread)
{
  uint8_t *buf;
  int sum = 0;
  long i;
  long length = pages_per_thread * PAGE_SIZE;
  long offset = length * thread;

  for (i = 0; i < length; i+= PAGE_SIZE) {
    buf = mmap(NULL, PAGE_SIZE, PROT_READ, MAP_PRIVATE, fd, offset + i);
    madvise(buf, PAGE_SIZE, MADV_SEQUENTIAL);

    sum += buf[0];

    munmap(buf, PAGE_SIZE);
  }
}

void Recursive(int num, long thread)
{
    if (num == 5)
    {
        DoSomeWork(thread);
        return;
    }
    Recursive(num + 1, thread);
}

void* Thread(void *arg)
{
  long thread = (long)arg;
  Recursive(0, thread);
  return NULL;
}

off_t Filesize(int fd) {
  struct stat stats;
  int ret = -1;
  if (fstat(fd, &stats) == 0) {
    ret = stats.st_size;
  }

  return ret;
}

void Iteration()
{
  long i;

  fd = open(FILENAME, O_RDONLY);
  if (fd == -1) {
    fprintf(stderr, "Error: cannot open file %s\n", FILENAME);
    exit(EXIT_FAILURE);
  }

  int size = Filesize(fd);
  if (size == -1) {
    fprintf(stderr, "Error: cannot get file size.\n");
    exit(EXIT_FAILURE);
  }
  pages_per_thread = (size / PAGE_SIZE) / NUM_THREADS;

  pthread_t threads[NUM_THREADS];
  for (i = 0; i < NUM_THREADS; ++i)
  {
    pthread_create(&threads[i], NULL, &Thread, (void*)i);
  }

  for (i = 0; i < NUM_THREADS; ++i)
  {
    pthread_join(threads[i], NULL);
  }

  close(fd);
}

int main()
{
  for (;;)
    Iteration();
}
