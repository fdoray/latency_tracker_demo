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
#include <time.h>
#include <unistd.h>

void Recursive(int num)
{
    if (num == 5)
    {
        int duration_us = rand() % 8000000;
        printf("going to sleep for %d us\n", duration_us);
        usleep(duration_us);
        return;
    }
    Recursive(num + 1);
}

int main()
{
	srand(time(NULL));
    for (;;)
        Recursive(0);
}
