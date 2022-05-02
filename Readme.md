# ECE 437 Shared Code

System Verilog and Python Tools by Grant Geyer (lab partner Evan Thomas)

By the Spring 2021 syllabus, this code is non-synthesizeable and may be
shared.

The files are:
* ram_tracker.sv - Pretty straightforward. It tracks all reads and writes
  from memory and the time. Useful when caches get involved and memory
  dumps aren't matching, but the "executed" instructions match.
* cpu_tracker.sv - Couple additions here:
    * There is a PRINT_TIME parameter so that the time is printed to the
      file. Sorta messes up comparisons, but it does help to find the
      time when an issue occurs.
    * There is a CACHE_TRACKING parameter so that the trace output can
      be compared with a simulated cache output. Cache tracking will
      print hits, misses, blocks, etc. A lot of the formatting now
      prints with `"%0d"` rather than `"%d"` which omits spaces
      (so instead of "R0,       65532", it is "R0, 65532" is printed).
    * Then there's a few things added for multicore, LL&SC, and the link register.
* compare_traces.py - Changed this to run in Python3. It can run the
  simulator with caches and perform cleaning on cache trace files. It also
  runs the simulator and student CPUs simultaneously to be a little faster. 

Then two other semi-helpful ones I made:
* split_out.py - Python3 script. Not sure how useful this will be to most, but it
  splits a simulated trace into two so each core can be compared to the simulator.
* combine_cpu_out.py - Python3 script for merging two cpu traces from student CPUs
  to one file. It needs times written into the log and the result isn't terribly
  useful when a student's CPU executed instruction in a different order than the simulator.


Files from Spring 2021 semester. NGL, as of writing I don't remember if all this
will integrate right off the bat, but it should be pretty close.
