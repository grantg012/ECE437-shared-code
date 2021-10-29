#!/usr/bin/python3
"""
Filename:    compare_traces.py
Created by:   Jacob R. Stevens
Email:        steven69@purdue.edu
Date Created: 06/27/2016
Description:  Compare the traces generated by the ISS and cpu_tracker.sv

Cache tracking additions by Grant Geyer (GrantG012@yahoo.com)
"""

import subprocess
from multiprocessing import Process
import argparse
import sys
import glob
import os
import re as regex


IMEM_ADDR = regex.compile(r"^[0-9A-Fa-f]{8} ?\(Core +[0-9]\):")
INSTR_SOLO = regex.compile(r"^ +[0-9A-Fa-f]{8} [A-Z]+")
HEX_CHARS = set("abcdef")


def hex_upper(s: str) -> str:
    """Converts only the lowercase hex characters (a-f) in the string to uppercase."""
    return ''.join(c.upper() if c in HEX_CHARS else c for c in s)


def cpu_trace(doCache: bool) -> None:
    """Single function for the process to call"""
    create_cpu_trace()
    clean_cpu_trace(doCache)


def sim_trace(doCache: bool) -> None:
    """Single function for the process to call"""
    create_sim_trace(doCache)
    clean_sim_trace(doCache)


def create_sim_trace(doCache: bool, doMulticore: bool) -> None:
    """Run the simulator to get the trace, possibly with caches."""
    cmd = ["sim", '-t'] + (['-c'] if doCache else []) + (['-m'] if doMulticore else [])
    with open("sim_trace.log", 'w') as log:
        ret = subprocess.run(cmd, stdout=log)
    if ret.returncode:
        sys.exit(f"ERROR: '{' '.join(cmd)}' command failed.")


def create_cpu_trace() -> None:
    """Create the trace for the CPU."""
    cmd = ["make", "system.sim"]
    ret = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ret.returncode:
        sys.exit('Error: make failed. Make sure your processor compiles first')
    print("Finished running CPU.", flush = True)


def clean_cpu_trace(doCache: bool) -> None:
    """Clean the CPU trace for comparison with the simulator."""
    cleaned_output = ''
    with open("cpu_trace.log", 'r') as trace_file:
        for line in trace_file:
            broken_line_arr = line.split()
            if(IMEM_ADDR.search(line)):
                if(not doCache):
                    # Modify beginning of instruction entry
                    # that is, the line with PC, core, instruction, and mnemonics
                    # turn instruction into uppercase hex
                    broken_line_arr[3] = broken_line_arr[3].upper()
                    # if the instruction is a jump, change the destination addr to hex
                    if broken_line_arr[4] == 'J' or broken_line_arr[4] == "JAL":
                        broken_line_arr[5] = broken_line_arr[5].upper()
                # turn PC into uppercase hex and remove space between PC and (Core n)
                first_entry = broken_line_arr[0].upper() + broken_line_arr[1]
                broken_line_arr = [first_entry] + broken_line_arr[2:]
                new_line = ' '.join(broken_line_arr) + '\n'
            elif(INSTR_SOLO.search(line)):
                broken_line_arr[0] = broken_line_arr[0].upper()
                if broken_line_arr[1] == 'J' or broken_line_arr[1] == "JAL":
                    broken_line_arr[2] = broken_line_arr[2].upper()
                new_line = "    " + ' '.join(broken_line_arr) + '\n'
            elif len(broken_line_arr) == 0:
                new_line = '\n'
            elif(broken_line_arr[0].startswith("I$")):
                new_line = line
            elif(broken_line_arr[0].startswith("D$")):
                if(" = " in line):
                    index = line.index(" = ")
                elif(" <-- " in line):
                    index = line.index(" <-- ")
                else:
                    raise ValueError("Error: No <-- or = in D$ line.")
                new_line = line[:index] + hex_upper(line[index:])
            elif broken_line_arr[0] == "PC" or broken_line_arr[0][0] == 'R':
                # Modify the line that updates the PC or a register
                broken_line_arr[2] = broken_line_arr[2].upper()
                new_line = "    " + ' '.join(broken_line_arr) + '\n'
            elif broken_line_arr[0] == "[word":
                # Modify the line that specifies where a word is read from
                broken_line_arr[3] = broken_line_arr[3].upper()
                new_line = "    " + ' '.join(broken_line_arr) + '\n'
            elif broken_line_arr[0][0] == '[':
                # Modify the line that updates a memory location
                broken_line_arr[0] = broken_line_arr[0].upper()
                broken_line_arr[2] = broken_line_arr[2].upper()
                new_line = "    " + ' '.join(broken_line_arr) + '\n'
            else:
                print("Non-matching-line: ", line, file = sys.stderr)
            cleaned_output += new_line
    with open("cleaned_cpu_trace.log", 'w') as trace_file:
        trace_file.write(cleaned_output[:-1])


def clean_sim_trace(doCache: bool) -> None:
    """Clean the simulator trace for comparison with the CPU."""
    cleaned_output = ''
    with open("sim_trace.log", 'r') as trace_file:
        line = trace_file.readline()
        # Skip past the header portion to the actual execution trace
        while line and line[8:13] != "(Core":
            line = trace_file.readline()
        # Clean up the instructions up through HALT
        while line and line[-5:-1] != "HALT":
            broken_line_arr = line.split()
            new_line = ''
            if(not IMEM_ADDR.search(line)):
                # Make the lines that specify updates have two indents
                # because I like it better that way.
                new_line = "    "
            new_line += ' '.join(broken_line_arr) + "\n"
            if(new_line.strip() == ''):
                new_line = '\n'
            cleaned_output += new_line
            line = trace_file.readline()
        # DO the Halt
        if line and line[-5:-1] == "HALT":
            broken_line_arr = line.split()
            new_line = ' ' * (4 * doCache) + ' '.join(broken_line_arr) + '\n'
            cleaned_output += new_line
            line = trace_file.readline()  # The PC line
            broken_line_arr = line.split()
            new_line = "    " + ' '.join(broken_line_arr) + '\n'
            cleaned_output += new_line
    with open("cleaned_sim_trace.log", 'w') as trace_file:
        trace_file.write(cleaned_output)


def main() -> None:
    """
    Compare your processor's trace to that of the simulator.
    This script expects to be ran at the top level of your repo.
    If a test name is provided, it should be the full name of the
    test case, but not include the file extension or path
    """
    help = "Run this specific test. Optional. If not specified, the current " \
        "meminit.hex is used."
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("test_name", metavar= "test_name", type=str, nargs='?',
                                            help=help)
    parser.add_argument("--cache", '-c', action = "store_true",
                help = "Run comparison with information about cache and misses." \
                "The CACHE_TRACKING parameter in cpu_tracker must be turned on.")
    args = parser.parse_args()
    if args.test_name:
        asm_dir = f"./asmFiles/{args.test_name}.asm"
        try:
            asm_file = glob.glob(asm_dir)[0]
        except:
            sys.exit("ERROR: Please provide the exact name of a test case.")
        ret = subprocess.run(['asm', asm_file])
        if ret.returncode:
            sys.exit('ERROR: ' + asm_file + ' could not be assembled.')
    elif not os.path.isfile('./meminit.hex'):
        sys.exit('ERROR: Could not find an existing meminit.hex.')
    # Run the cpu and sim simultaneously so it's faster.
    cpu_proc = Process(target = cpu_trace, args = (args.cache,))
    cpu_proc.start()
    sim_proc = Process(target = sim_trace, args = (args.cache,))
    sim_proc.start()
    sim_proc.join()
    cpu_proc.join()

    cmd = ['diff', 'cleaned_cpu_trace.log', 'cleaned_sim_trace.log']
    ret = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ret.returncode:
        cmd = ['diff', '-y', 'cleaned_cpu_trace.log', 'cleaned_sim_trace.log']
        subprocess.run(cmd)


if(__name__ == "__main__"):
    main()