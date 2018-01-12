procmem
=======

`procmem` is a command line utility for Linux for reading and writing
to a processes memory, as well as printing information related to a
processes allocated memory. This is accomplished via the
`/proc/$PID/smaps` and `/proc/$PID/mem` files.


Installation
------------

    sudo -H pip3 install -r requirements.txt
    sudo -H pip3 install -e .


Examples
--------

### Memory Reading:

    $ procmem read -P '[heap]'
    000001c39000-000001f99000     3.38MiB  rw-p  [heap]
    0000000001c39000  00 00 00 00 00 00 00 00  51 02 00 00 00 00 00 00  |........Q.......|
    0000000001c39010  05 07 07 06 03 06 05 06  07 07 02 05 03 04 07 07  |................|
    0000000001c39020  01 05 04 03 04 04 05 05  04 01 07 01 02 01 06 00  |................|
    0000000001c39030  00 00 00 07 03 05 02 07  06 02 00 07 05 02 00 07  |................|
    0000000001c39040  02 07 03 00 07 03 04 00  02 00 00 05 02 01 07 01  |................|
    0000000001c39050  b0 a8 ea 01 00 00 00 00  00 0d d8 01 00 00 00 00  |................|
    0000000001c39060  a0 73 e7 01 00 00 00 00  a0 8b dc 01 00 00 00 00  |.s..............|
    0000000001c39070  20 97 dc 01 00 00 00 00  d0 de e0 01 00 00 00 00  |................|
    0000000001c39080  a0 d5 f3 01 00 00 00 00  20 40 f4 01 00 00 00 00  |.........@......|
    ...

### Memory Region Information:

    $ procmem -P xeyes info
    563f25e9f000-563f25ea4000    20.00KiB  r-xp  /usr/bin/xeyes
    563f260a3000-563f260a4000     4.00KiB  r--p  /usr/bin/xeyes
    563f260a4000-563f260a5000     4.00KiB  rw-p  /usr/bin/xeyes
    563f260a5000-563f260a6000     4.00KiB  rw-p
    563f263fd000-563f2643d000   256.00KiB  rw-p  [heap]
    7f905204b000-7f9052050000    20.00KiB  r-xp  /usr/lib/x86_64-linux-gnu/libXfixes.so.3.1.0
    7f9052050000-7f905224f000     2.00MiB  ---p  /usr/lib/x86_64-linux-gnu/libXfixes.so.3.1.0
    7f905224f000-7f9052250000     4.00KiB  r--p  /usr/lib/x86_64-linux-gnu/libXfixes.so.3.1.0
    7f9052250000-7f9052251000     4.00KiB  rw-p  /usr/lib/x86_64-linux-gnu/libXfixes.so.3.1.0
    7f9052253000-7f905225c000    36.00KiB  r-xp  /usr/lib/x86_64-linux-gnu/libXcursor.so.1.0.2
    7f905225c000-7f905245b000     2.00MiB  ---p  /usr/lib/x86_64-linux-gnu/libXcursor.so.1.0.2
    7f905245b000-7f905245c000     4.00KiB  r--p  /usr/lib/x86_64-linux-gnu/libXcursor.so.1.0.2
    7f905245c000-7f905245d000     4.00KiB  rw-p  /usr/lib/x86_64-linux-gnu/libXcursor.so.1.0.2
    7f9052463000-7f9052956000     4.95MiB  r--p  /usr/lib/locale/locale-archive
    ...


### Memory Writing:

    $ sudo procmem -P pingus write -a 000055e4e7c6a758 -s Options

### Memory Status:

    $ procmem -P xeyes statm
     49.30MiB  total program size
      4.54MiB  resident set size
      4.07MiB  shared size
     20.00KiB  text
    616.00KiB  data + stack


mmaptracker.gdb
---------------

The GDB script `mmaptracker.gdb` tracks all mmap() calls and prints
the backtrace at those points, this allows to figure out where a given
anonymous memory region came from. The gdb output is captured in the
file `/tmp/mmaptracker.log`.

Run with:

    gdb -x mmaptracker.gdb --args /usr/bin/you_application


Notes
-----

The following are empirical observations of a processes behaviour on
Linux 4.13.0 x86_64, other versions or architectures might behave
differently.

The region with the pathname `[heap]` is only used for `malloc()`
allocations smaller than 128KiB, everything larger will go into an
anonymous region after the `[heap]` region.

The smallest block returned by `malloc()` is 32 bytes.

Allocating memory and not initializing it or initializing it with
zeroes via `calloc()` will not actually use any RAM. Reading from that
memory will not cause it to use RAM either, only when the memory is
written to it starts to occupy RAM.

The 'total program size' is the size of (virtual) memory that is
mapped into the processes address space. RSS or 'resident set size' is
the amount of RAM actually used, pages that haven't been initialized
are not counted.

Reading `[vvar]` fails to read with `OSError: "[Errno 5] Input/output
error"`, procmem will filter it out by default.

Reading `[vsyscall]` fails with `OverflowError: "Python int #too large
to convert to C long"`, it gets filtered as well.
