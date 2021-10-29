#!/usr/bin/python3
"""
This script combines the two traces from each core of a CPU and combines them
before comparing them to the simulated CPU. The time of the instruction executed
completion needs to be printed. This expects the CPU to already have been run.

Grant Geyer, GrantG012@yahoo.com, Spring 2021
"""
import sys
import subprocess
from multiprocessing import Process

import compare_traces


DIGIT_SET = set("0123456789")

def readInstructionLines(file: "TextIO") -> list:
    """Reads the lines associated with an instruction."""
    lines = []
    while(not lines or (lines[-1] != '\n' and lines[-1] != '')):
        lines.append(file.readline())
    return lines


def getTime(lines: list) -> int:
    """Parses the three lines (or more) for an instruction to get the time it was executed at."""
    assert len(lines) >= 3
    assert lines[1].lstrip().startswith("time = ")
    return int(''.join(c for c in lines[1] if c in DIGIT_SET))


def sim_trace(totalLines: int) -> None:
    """Single function for starting the sim trace functions in parallel."""
    compare_traces.create_sim_trace(False, True)
    clean_sim_trace(totalLines)
    print("Created clean sim trace", flush = True)


def clean_sim_trace(totalLines: int) -> None:
    """Parse and clean the simulated trace to for comparison with the CPU."""
    linesWritten = 0
    with open('sim_trace.log', 'r') as trace_file:
        with open('cleaned_sim_trace.log', 'w') as clean_trace_file:
            line = trace_file.readline()
            # Skip past the header portion to the actual execution trace
            while line and line[8:13] != '(Core':
                line = trace_file.readline()
            # Clean up the instructions up through HALT
            while line and line[-5:-1] != 'HALT':
                broken_line_arr = line.split()
                if 0 < len(broken_line_arr) < 5:
                    # Make the lines that specify updates have two indents
                    # because I like it better that way.
                    new_line = '    ' + ' '.join(broken_line_arr) + '\n'
                else:
                    new_line = ' '.join(broken_line_arr) + '\n'
                clean_trace_file.write(new_line)
                linesWritten += 1
                if(linesWritten > totalLines):
                    break
                line = trace_file.readline()
            # DO the Halt
            if line and line[-5:-1] == 'HALT':
                broken_line_arr = line.split()
                new_line = ' '.join(broken_line_arr) + '\n'
                clean_trace_file.write(new_line)
                line = trace_file.readline()
                broken_line_arr = line.split()
                new_line = '    ' + ' '.join(broken_line_arr) + '\n'
                clean_trace_file.write(new_line)


def mergeCPUTraces(totalLines: int) -> None:
    """Merge the two CPU traces from core 1 & 2."""
    with open("cpu_trace1.log", 'r') as cpuTrace1File:
        with open("cpu_trace2.log", 'r') as cpuTrace2File:
            with open("cpu_trace_merged.log", 'w') as cpuMergedFile:
                lines1 = readInstructionLines(cpuTrace1File)
                lines2 = readInstructionLines(cpuTrace2File)
                time1 = getTime(lines1)
                time2 = getTime(lines2)
                linesWritten = 0
                while(linesWritten < totalLines):
                    if(time1 <= time2):
                        cpuMergedFile.writelines(lines1)
                        linesWritten += len(lines1)
                        lines1 = readInstructionLines(cpuTrace1File)
                        if(lines1 == ['']):
                            # Reached the end of file 1
                            # TODO: Fix that this ignores the line count
                            cpuMergedFile.writelines(lines2)
                            cpuMergedFile.writelines(cpuTrace2File.readlines())
                            break
                        time1 = getTime(lines1)
                    else:
                        cpuMergedFile.writelines(lines2)
                        linesWritten += len(lines2)
                        lines2 = readInstructionLines(cpuTrace2File)
                        if(lines2 == ['']):
                            # Reached the end of file 2
                            # TODO: Fix that this ignores the line count
                            cpuMergedFile.writelines(lines1)
                            cpuMergedFile.writelines(cpuTrace1File.readlines())
                            break
                        time2 = getTime(lines2)
    print("Merged CPU Traces", flush = True)


def main(args: list) -> None:
    """"""
    if(len(args) >= 2 and ('-h' in args or "--help" in args)):
        print(__doc__)
    else:
        if(len(args) >= 2):
            try:
                totalLines = int(args[1])
            except ValueError as e:
                print(f"Expecting integer, not {args[1]}.")
                return
        else:
            totalLines = 150_000

        cpu_merge_proc = Process(target = mergeCPUTraces, args = (totalLines,))
        cpu_merge_proc.start()
        sim_trace_proc = Process(target = sim_trace, args = (totalLines,))
        sim_trace_proc.start()
        sim_trace_proc.join()
        cpu_merge_proc.join()

        with open("comp_out.txt", 'w') as compOutFile:
            cmd = ["diff", "-ywiB", "cpu_trace_merged.log", "cleaned_sim_trace.log"]
            subprocess.run(cmd, stdout = compOutFile)


if(__name__ == "__main__"):
    main(sys.argv)
