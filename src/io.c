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
#include <stdlib.h> 

#define BUFFER_SIZE 128
#define FILE_SIZE 4096
#define WRITE_DIR "/var/tmp/demo"

void WriteFile(int filename)
{
  char filepath[BUFFER_SIZE];
  FILE *file = NULL;
  void* file_content = NULL;
  int i = 0;

  sprintf(filepath, "%s/%d", WRITE_DIR, filename);
  file = fopen(filepath, "w");

  if (file == NULL)
  {
    fprintf(stderr, "An error occured while opening file %s.", filepath);
    return;
  }

  file_content = malloc(FILE_SIZE * sizeof(char));

  fwrite(file_content, sizeof(char), FILE_SIZE, file);

  fclose(file);
  free(file_content);
}

void Recursive(int num, int filename)
{
    if (num == 5)
    {
        WriteFile(filename);
        return;
    }
    Recursive(num + 1, filename);
}

int main()
{
    int i = 0;
    for (;; ++i) {
        Recursive(0, i);
    }
}
