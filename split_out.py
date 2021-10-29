#!/usr/bin/python3
"""
Run this script (with python 3) to split the simulated trace into traces
for just each core. The CPU tracker must write traces into "cpu_traceN.log".
If you are diff-ing large files and would only like to do part of them, the
number of lines can be specified (ex: `python3 split_out.py 80000`).

Grant Geyer, GrantG012@yahoo.com, Spring 2021
"""
import sys
import subprocess
from multiprocessing import Process
import re as regex

import compare_traces


I_ADDR_REGEX = regex.compile(r"^[0-9A-F]{8}\(Core (?P<core>[12])\): +(?P<instr_hex>[0-9A-Fa-f]{8})")


def sim_trace(args: list) -> None:
    """Single function for a parallel process to create the simulator trace and split it."""
    compare_traces.create_sim_trace(False, True)
    if(len(args) >= 2):
        try:
            nLines = int(args[1])
        except ValueError:
            sys.exit(f"Expecting integer, not {args[1]}.")
        splitTraces(nLines)
    else:
        splitTraces()
    print("Split simulated traces.", flush = True)


def splitTraces(totalLines = 10_000_000) -> None:
    """Split the simulated trace into two traces with just the instructions of a single CPU."""
    with open("sim_trace.log", 'r') as outlogFile:
        with open("sim_trace_core1.log", 'w') as traceCore1File:
            with open("sim_trace_core2.log", 'w') as traceCore2File:
                files = {'1': traceCore1File, '2': traceCore2File}
                line = outlogFile.readline()
                while(line != "Starting simulation...\n"):
                    line = outlogFile.readline()
                while(not I_ADDR_REGEX.search(line)):
                    line = outlogFile.readline()
                core = '1'
                linesRead = 1
                while(line != "Done simulating...\n"):
                    m = I_ADDR_REGEX.search(line)
                    if(m):
                        core = m.group("core")
                        if(m.group("instr_hex") == '0' * 8):  # NOP
                            while(line != '\n'):
                                line = outlogFile.readline()
                            line = outlogFile.readline()
                            continue
                    if(not line.startswith("HALT executed(Core ")):
                        files[core].write(line)
                    linesRead += 1
                    if(linesRead > totalLines):
                        break
                    line = outlogFile.readline()
                traceCore1File.write('\n')
                traceCore2File.write('\n')


def diff_traces(core: int) -> None:
    """Diff the simulated and CPU trace for a single core."""
    cmd = ["diff", '-wiB', f"cpu_trace{core}.log", f"sim_trace_core{core}.log"]
    ret = subprocess.run(cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    if(ret.returncode):
        print(f"Difference found in Core {core}", flush = True)
        cmd = ["diff", "-ywiB",  f"cpu_trace{core}.log", f"sim_trace_core{core}.log"]
        with open(f"comp_out{core}.txt", 'w') as compOutFile:
            subprocess.run(cmd, stdout = compOutFile)
        print(f"Completed diff of core {core}.", flush = True)
    else:
        print(f"No differences between files for core {core}. Traces match.")


def main(args: list) -> None:
    """"""
    if(len(args) >= 2 and ('-h' in args or "--help" in args)):
        print(__doc__)
    else:
        cpu_proc = Process(target = compare_traces.create_cpu_trace)
        cpu_proc.start()
        sim_proc = Process(target = sim_trace, args = (args,))
        sim_proc.start()
        sim_proc.join()
        cpu_proc.join()

        diff_proc1 = Process(target = diff_traces, args = (1,))
        diff_proc1.start()
        diff_proc2 = Process(target = diff_traces, args = (2,))
        diff_proc2.start()
        diff_proc1.join()
        diff_proc2.join()


if(__name__ == "__main__"):
    main(sys.argv)
