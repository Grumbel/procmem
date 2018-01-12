# This GDB script tracks all mmap() calls and prints the backtrace at
# those points, this allows to figure out where a given anonymous
# memory region came from. The gdb output is captured in the file
# /tmp/mmaptracker.log
#
# Run with:
#
#  gdb -x mmaptracker.gdb --args /usr/bin/you_application
#

set pagination off
set breakpoint pending on

set logging file /tmp/mmaptracker.log
set logging on

# Change this line to point to an executable you want to investigate
# file /usr/bin/you_application

# Command line arguments can be passed to the executable via:
# set args ARG1 ARG2 ...

# Settup a breakpoint on mmap()
break mmap

# Run the program
run

# Each time mmap() is encountered, print a backtrace, the return value
# and continue
while 1
  echo --- backtrace\n
  backtrace
  echo \ - finish\n
  finish
  echo ---\n\n
  continue
end

# EOF #
