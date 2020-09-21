#!/usr/bin/python3
"""
The MIT License (MIT)

Copyright (c) 2020 Howard Chan
https://github.com/howard-chan/petmux

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sys
import os
import time
import argparse
# import re
import yaml
import json


#TODO:
# 1. Document APIs
# 2. Add read.md for how to use this
# 5. Search for default petmux.yaml as default
# 7. Add scheme for capture
# 8. Add unittest

class Tmux:
    def __init__(self, is_debug=False, is_dryrun=False):
        self.is_debug = is_debug
        self.is_dryrun = is_dryrun
        self.pane_dict = {}
        self.pane_last = 1
        self.window_last = None

    def name_pane(self, window, name, idx):
        if window in self.pane_dict:
            self.pane_dict[window][name] = idx
        else:
            self.pane_dict[window] = { name : idx }

    def cmd(self, cmd):
        if self.is_debug:
            print("    tmux> {}".format(cmd))
        return os.system('tmux {}'.format(cmd))

    def set_env(self, key, value):
        self.cmd('set-environment %s %s' % (key, value))

    def kill(self, window):
        self.cmd('kill-window -t %s' % window)

    def window(self, window):
        if self.is_debug:
            print("[ window: {} ]".format(window))
        result = self.cmd('select-window -t %s' % window)
        # If window failed to be selected, then create it
        if result:
            print("Creating window: {}".format(window))
            self.cmd('new-window')
            self.cmd('rename-window %s' % window)
        self.window_last = window

    def pane(self, pane):
        if self.is_debug:
            print("[ {} ]".format(pane))
        pane = self.pane_dict[self.window_last][pane] if pane in self.pane_dict[self.window_last] else pane
        self.pane_last = pane
        if type(pane) == int:
            self.cmd('select-pane -t %d' % pane)
        else:
            print("Error: Unknown pane {}".format(pane))

    def split(self, options):
        self.cmd('split-window %s' % (options if options else ""))

    def shell(self, cmd, pane=None):
        if pane:
            self.pane(pane)
        cmd_list = cmd if type(cmd) == list else [cmd]
        for cmd in cmd_list:
            # NOTE: triple quote required to prevent globbing of environment variables
            if self.is_dryrun:
                self.cmd("""send-keys "echo \'{}\'" C-m""".format(cmd))
            else:
                self.cmd("""send-keys '{}' C-m""".format(cmd))

    def capture(self, pane):
        self.cmd('capture-pane -p')



class PetMux:
    def __init__(self, config, is_debug=True, is_dryrun=False):
        self.config = config
        self.is_debug = is_debug
        # Create a tmux object
        self.tmux = Tmux(self.is_debug, is_dryrun)
        # Populate keyword dictionary
        self.cfgkey_list = [
            "DEFINES",
            "TITLE",
            "DESC",
            "NEW_WINDOW",
            "PANES",
        ]
        self.key_func_dict = {
            "WINDOW"  : self.tmux.window,
            "PANE"    : self.tmux.pane,
            "SPLIT"   : self.tmux.split,
            "ECHO"    : self.echo,
            "PROMPT"  : self.prompt,
            "SHELL"   : self.tmux.shell,
            "PAUSE"   : self.pause,
        }
        # Populate user defines into environment
        if "DEFINES" in self.config.keys():
            if self.is_debug:
                print("Loading environment")
            for key, value in self.config["DEFINES"].items():
                self.tmux.set_env(key, value)
        # Get sequence list (i.e. entries that are not keywords)
        self.sequence_list = list(set(self.config.keys()) - set(self.cfgkey_list))
        # Populate panes index
        # Search for seequence that contains "NEW_WINDOW" which configures a window
        self.panes_dict = {}
        for seq in self.sequence_list:
            sequence = self.config[seq]
            if "NEW_WINDOW" in sequence.keys():
                # Found "PANES", so save the list
                window_name = sequence['NEW_WINDOW']
                self.panes_dict[window_name] = sequence['PANES']
                pane_num = 1
                for pane in self.panes_dict[window_name]:
                    # Workaround to get key and values for a pane
                    pane_name = [ k for k in pane.keys() ][0]
                    # Associate the pane_name to pane index
                    self.tmux.name_pane(window_name, pane_name, pane_num)
                    pane_num += 1

    def kill(self):
        if self.is_debug:
            print("Killing windows")
        for window in self.panes_dict.keys():
            self.tmux.kill(window)

    def pause(self, delay=1):
        if self.is_debug:
            print("Waiting(%d)..." % delay)
        time.sleep(delay)

    def echo(self, message):
        print(message)

    def prompt(self, banner):
        input(banner)

    def run(self, sequence):
        # Step 1: Print title and description if any
        sequence = self.config[sequence]
        if 'NEW_WINDOW' in sequence.keys():
            title = sequence['NEW_WINDOW']
            sequence['WINDOW'] = title
        elif 'TITLE' in sequence.keys():
            title = sequence['TITLE']
        else:
            title = ""
        desc = sequence['DESC'] if 'DESC' in sequence.keys() else ""
        banner_length = max(len(title), len(desc))
        if title:
            print('\n' + '=' * banner_length)
            print(title)
            print('-' * banner_length)
        if desc:
            print(desc)
            print('-' * banner_length)
        # Select or add a window
        if 'WINDOW' in sequence.keys():
            self.tmux.window(sequence['WINDOW'])
        # Step 2a: Check if window'panes are present to setup
        if 'PANES' in sequence.keys():
            # Each pane is setup by the keyword commands
            pane_cnt = 0
            for pane in self.panes_dict[title]:
                if self.is_debug:
                    pane_name = [ k for k in pane.keys() ][0]
                    print("[ {} ]".format(pane_name))
                # Workaround to get values for a pane
                cmd_dict = [ v for v in pane.values() ][0]
                # if SPLIT option is not defined for the pane, then use default split
                if "SPLIT" not in cmd_dict and pane_cnt > 0:
                    self.tmux.split(None)
                pane_cnt += 1
                # Process the pane commands by the order of key_func_dict.
                for key in self.key_func_dict.keys():
                    if key in cmd_dict:
                        self.key_func_dict[key](cmd_dict[key])

        # Step 2b: Check if cmds are present to run
        elif 'CMDS' in sequence.keys():
            # Run the commands
            cmds_list = sequence['CMDS']
            for cmd_dict in cmds_list:
                # Report unknown commands
                unknown_cmds = list(set(cmd_dict) - set(self.key_func_dict.keys()))
                if unknown_cmds:
                    print('Warning: Unknown commands {} in sequence "{}"'.format(unknown_cmds, title))
                # Process the pane commands by the order of key_func_dict.
                for key in self.key_func_dict.keys():
                    if key in cmd_dict:
                        self.key_func_dict[key](cmd_dict[key])

    def list(self, sequence=None):
        if sequence in self.sequence_list:
            # print(json.dumps(self.config[sequence], indent=2))
            print(yaml.dump(self.config[sequence]))
        else:
            print(self.sequence_list)


def main(args):
    # Process the command line arguments
    parser = argparse.ArgumentParser(description="PetMux: Program Executing TMUX")
    parser.add_argument('-i', '--input', action="store", help="input file: --input <your.petmux.config.file>.<json|yaml>")
    parser.add_argument('-q', '--quiet', action="store_true", help="Supress debug output")
    parser.add_argument('-d', '--dryrun', action="store_true", help="Dry run. Print shell commands instead of executing")
    parser.add_argument('-k', '--kill', action="store_true", help="Kill the window")
    parser.add_argument('-l', '--list', action="store_true", help="List sequences")
    parser.add_argument('-r', '--run', action="store", help='Run sequence(s): --run <sequence|"sequence1 sequene2 ..">')
    # parser.add_argument('sequence', action='store', default="test", help='Run sequence')
    args = parser.parse_args()

    if args.input:
        # Load the configuration file
        with open(args.input, 'r') as file:
            ext = os.path.splitext(args.input)[1]
            if  ext == '.yaml' or ext == '.yml':
                config = yaml.load(file, Loader=yaml.FullLoader)
            elif ext == '.json':
                config = json.load(file)

            # Create PetMux object
            if config:
                pm = PetMux(config, args.quiet == False, args.dryrun)
                if args.kill:
                    pm.kill()
                if args.list:
                    pm.list(args.run)
                elif args.run:
                    for sequence in args.run.split():
                        pm.run(sequence)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main(sys.argv[1:])
