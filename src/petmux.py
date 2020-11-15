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
import subprocess
import tempfile
import re
import time
import argparse
import yaml
import json

# Colors for debug
RED = "\033[1;31m"
GRN = "\033[1;32m"
YEL = "\033[1;33m"
BLU = "\033[1;34m"
MAG = "\033[1;35m"
CYN = "\033[1;36m"
NON = "\033[0m"


class Tmux:
    """
    This class wraps the tmux command line interface for petmux
    """
    def __init__(self, is_debug=False, is_dryrun=False):
        """
        Constructs a new tmux instance.

        :param      is_debug:   Indicates if debug
        :type       is_debug:   boolean
        :param      is_dryrun:  Indicates if dryrun
        :type       is_dryrun:  boolean
        """
        self.cmd_delay = 0
        self.is_debug = is_debug
        self.is_dryrun = is_dryrun
        self.window_dict = {}
        self.pane_last = 1
        self.window_last = None
        self.session_last = None
        self.pattVAR = re.compile(r'\$\{(.*?)\}')
        self.var_dict = {}

    def _cmd(self, cmd, delay=0, check_output=False):
        delay = delay if delay else self.cmd_delay
        if self.is_debug:
            print("    tmux{}> {}".format( "(dly:{})".format(delay) if delay else "", cmd))
        if delay:
            time.sleep(delay)
        # Send the tmux command
        if check_output:
            return subprocess.check_output('tmux {}'.format(cmd).split())
        else:
            return os.system('tmux {}'.format(cmd))

    def _get_pane_str(self, pane):
        """
        Builds the target string from the session, window and pane.

        :param      pane:  The pane name
        :type       pane:  string or int

        :returns:   The pane string.
        :rtype:     str
        """
        pane_str = '{}:'.format(self.session_last) if self.session_last else ''
        pane_str += '{}.'.format(self.window_last) if self.window_last else ''
        pane = self.window_dict[self.window_last][pane] if pane in self.window_dict[self.window_last] else pane
        pane_str += '{}'.format(pane) if pane else ''
        return pane_str

    def name_pane(self, window, name, idx):
        """
        Associates the name with pane index into the window dictionary

        :param      window:  The window name
        :type       window:  str
        :param      name:    The pane name
        :type       name:    int
        :param      idx:     The pane index
        :type       idx:     int
        """
        if window in self.window_dict:
            self.window_dict[window][name] = idx
        else:
            self.window_dict[window] = { name : idx }

    def delay(self, delay):
        """
        Sets the per command delay for the group of SHELL commands (via
        self.shell(...))

        :param      delay:  The delay [in S]
        :type       delay:  int
        """
        self.cmd_delay = delay

    def set_env(self, key, value):
        """
        Sets the tmux environment variable and dictionary

        :param      key:    The new value
        :type       key:    str
        :param      value:  The value
        :type       value:  str
        """
        self.var_dict[key] = value
        self._cmd("""set-environment %s '%s'""" % (key, value))

    def get_env(self):
        """
        Gets the environment variable dictionary

        :returns:   The environment.
        :rtype:     dict
        """
        return self.var_dict

    def kill(self, window):
        """
        Kill the window in the session

        :param      window:  The window name
        :type       window:  str
        """
        self._cmd('kill-window -t %s' % window)

    def session(self, session):
        """
        Selects a session.  If the session doesn't exist, then it will prompt to create a session

        :param      session:  The session name
        :type       session:  str
        """
        if session:
            result = self._cmd('has-session -t %s' % session)
            # If session failed to be selected, then create it
            if result:
                resp = input("Session {} doesn't exist, Create[Y/n]? ")
                if resp == 'Y' or resp == '':
                    print("Creating Session: {}".format(session))
                    self._cmd('new-session -t %s' % session)
            # select the session
            self._cmd('switch-client -t %s' % session)
        self.session_last = session

    def window(self, window):
        """
        Selects a window.  If the window doesn't exist, then it shall create one

        :param      window:  The window name
        :type       window:  str
        """
        if self.is_debug:
            print("{}[ window: {} ]{}".format(BLU, window, NON))
        result = self._cmd('select-window -t %s' % window)
        # If window failed to be selected, then create it
        if result:
            print("Creating window: {}".format(window))
            self._cmd('new-window')
            self._cmd('rename-window %s' % window)
        self.window_last = window

    def pane(self, pane):
        """
        Selects the tmux pane

        :param      pane:  The pane name or number
        :type       pane:  str or int
        """
        if self.is_debug:
            print("{}[ {} ]{}".format(CYN, pane, NON))
        self.pane_last = pane
        pane = self.window_dict[self.window_last][pane] if pane in self.window_dict[self.window_last] else pane
        if type(pane) == int:
            self._cmd('select-pane -t %d' % pane)
        else:
            print("Error: Unknown pane {}".format(pane))

    def split(self, options):
        """
        Splits a tmux window

        :param      options:  The tmux split options
        :type       options:  str
        """
        self._cmd('split-window %s' % (options if options else ""))

    def shell(self, cmd, pane=None):
        """
        Sends a shell command or list of shell commands to a pane

        :param      cmd:   The command string
        :type       cmd:   str
        :param      pane:  target pane
        :type       pane:  str
        """
        if pane:
            self.pane_last = pane
        cmd_list = cmd if type(cmd) == list else [cmd]
        for cmd in cmd_list:
            pane_str = self._get_pane_str(self.pane_last)
            # Check for string replacement
            match = self.pattVAR.findall(cmd)
            for var in match:
                if var in self.var_dict:
                    cmd = cmd.replace("${%s}" % var, self.var_dict[var])
            # NOTE: triple quote required to prevent globbing of environment variables
            if self.is_dryrun:
                self._cmd("""send-keys "echo -t {} \'{}\'" C-m""".format(pane_str, cmd))
            else:
                self._cmd("""send-keys -t {} '{}' C-m""".format(pane_str, cmd))
        # Clear the command delay set by self.delay()
        self.cmd_delay = 0

    def capture(self, file=None):
        """
        Captures the last pane to a file or screen

        :param      file:  The name of capture file to save
        :type       file:  str

        :returns:   pane contents
        :rtype:     str
        """
        pane_str = self._get_pane_str(self.pane_last)
        # Capture pane contents, preserve line feeds
        self._cmd('capture-pane -J -t {} -b {}'.format(pane_str, self.pane_last))
        if file:
            # Append to the save buffer
            self._cmd('save-buffer -a -b {} {}'.format(self.pane_last, file))
        else:
            result = self._cmd('show-buffer -b {}'.format(self.pane_last), check_output=True)
            self._cmd('delete-buffer -b {}'.format(self.pane_last))
            if self.is_debug:
                print(result.decode('utf-8'))
            return result

    def extract(self, cmd_patt_var, delay=1):
        """
        Extracts the command contents from a regular expression to a variable list

        :param      cmd_patt_var:  The command pattern
        :type       cmd_patt_var:  command and regular expression
        :param      delay:         The delay before ending the pipe capture
        :type       delay:         number
        """
        pane_str = self._get_pane_str(self.pane_last)
        with tempfile.NamedTemporaryFile() as fobj:
            # Setup the pipe-pane to buffer
            self._cmd("""pipe-pane -t {} -o 'cat > {}' """.format(pane_str, fobj.name))
            # Send the command
            self.shell(cmd_patt_var[0])
            # Wait a bit before closing
            if delay:
                time.sleep(delay)
            # Close the pipe-pane
            self._cmd("""pipe-pane -t {}""".format(pane_str))
            # Examine results
            data = fobj.read()
            if data:
                match = re.search(cmd_patt_var[1], data.decode('utf-8'))
                if match:
                    for key, val in zip(cmd_patt_var[2:], match.groups()):
                        self.set_env(key, '{}'.format(val))


class PetMux:
    """
    This class describes the Program, Execute T-MUX (PetMux) utility to
    automatically setup a tmux window and run a command sequence in each window
    and pane.  Configurations are loaded from a YAML or JSON file.
    """

    class SequenceException(Exception):
        """
        Exception for signaling sequence change
        """
        def __init__(self, sequence):
            self.sequence = sequence


    def __init__(self, config, session=None, is_debug=True, is_dryrun=False, is_interactive=False):
        """
        Constructs a new instance.

        :param      config:          The configuration <.yaml|.json> file
        :type       config:          str
        :param      session:         The tmux session name
        :type       session:         str
        :param      is_debug:        Indicates if debug
        :type       is_debug:        boolean
        :param      is_dryrun:       Indicates if dry run (i.e. echo to shell)
        :type       is_dryrun:       boolean
        :param      is_interactive:  Indicates if interactive (i.e. single step mode)
        :type       is_interactive:  boolean
        """
        self.config = config
        self.session = session
        self.is_debug = is_debug
        self.is_interactive = is_interactive
        # Create a tmux object
        self.tmux = Tmux(self.is_debug, is_dryrun)
        # Populate keyword dictionary
        self.cfgkey_list = [
            "DEFINES",
            "TITLE",
            "DESC",
            "SESSION",
            "NEW_WINDOW",
            "NEW_PANES",
            "CMDS",
        ]
        # NOTE: This is an ordered dictionary that controls the sequence
        #       for the executing keywords
        self.key_func_dict = {
            "SESSION" : self.tmux.session,
            "WINDOW"  : self.tmux.window,
            "PANE"    : self.tmux.pane,
            "SPLIT"   : self.tmux.split,
            "DELAY"   : self.tmux.delay,
            "ECHO"    : self.echo,
            "SEQUENCE": self.sequence,
            "SHELL"   : self.tmux.shell,
            "EXTRACT" : self.tmux.extract,
            "CAPTURE" : self.tmux.capture,
            "PROMPT"  : self.prompt,
            "DECIDE"  : self.decide,
            "PAUSE"   : self.pause,
            "ABORT"   : self.abort,
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
        # Search for sequence that contains "NEW_WINDOW" which configures a window
        self.panes_dict = {}
        for seq in self.sequence_list:
            sequence = self.config[seq]
            if "NEW_WINDOW" in sequence.keys():
                # Found "NEW_PANES", so save the list
                window_name = sequence['NEW_WINDOW']
                self.panes_dict[window_name] = sequence['NEW_PANES']
                pane_num = 1
                for pane in self.panes_dict[window_name]:
                    # Workaround to get key and values for a pane
                    pane_name = [ k for k in pane.keys() ][0]
                    # Associate the pane_name to pane index
                    self.tmux.name_pane(window_name, pane_name, pane_num)
                    pane_num += 1

    def kill(self, window=None):
        """
        Kill specific window or all windows defined in the config file

        :param      window:  Window name, if None then all windows listed
        :type       window:  str
        """
        if self.is_debug:
            print("Killing windows")
        if self.session:
            self.tmux.session(self.session)
        window = window if window else self.panes_dict.keys()
        for win in window:
            self.tmux.kill(win)

    def list(self, sequence=None):
        """
        Print the list of available sequences or sequence contents

        :param      sequence:  None - List available sequence, otherwise the
                               content of sequence
        """
        if sequence in self.sequence_list:
            # print(json.dumps(self.config[sequence], indent=2))
            print(yaml.dump(self.config[sequence]))
        else:
            print(self.sequence_list)

    def pause(self, delay=1):
        """
        Wait for delay

        :param      delay:  The delay
        :type       delay:  number
        """
        if self.is_debug:
            print("Waiting(%d)..." % delay)
        time.sleep(delay)

    def abort(self, return_code):
        if self.is_debug:
            print("Aborting with {}".format(return_code))
        sys.exit(return_code)

    def echo(self, message):
        """
        Print message to user

        :param      message:  The message
        :type       message:  str
        """
        print(message)

    def prompt(self, banner_key):
        """
        Prompt user for input

        :param      banner_key:  The user banner prompt and optional key
        :type       banner_key:  str or list(str, str)
        """
        banner = banner_key[0] if type(banner_key) is list else banner_key
        key = banner_key[1] if type(banner_key) is list else None
        resp = input(YEL + banner + NON)
        if key:
            self.tmux.set_env(key, resp)

    def decide(self, decide_dict):
        """
        Changes the program flow based on the results of EXTRACT or PROMPT

        :param      decide_dict:  The decide dictionary
        :type       decide_dict:  dict
        """
        try:
            # Look for the KEY to make a decision upon
            key = decide_dict['KEY']
            # Check if this key has a value
            value = self.tmux.get_env()[key]
            if value in self.config:
                #TODO: Select the next sequence to run
                print("{}Selected Sequence {}{}".format(MAG, value, NON))
            elif value in decide_dict:
                # Invoke the command
                print("{}Matched {}{}".format(MAG, value, NON))
                cmd = decide_dict[value]
                cmd_list = cmd if type(cmd) is list else [cmd]
                for cmd in cmd_list:
                    if type(cmd) is dict:
                        for k, v in cmd.items():
                            self.key_func_dict[k](v)
                    else:
                        self.tmux.shell(cmd)
        except KeyError as e:
            print("{}Couldn't resolve {}{}".format(RED, e, NON))

    def sequence(self, sequence):
        if sequence in self.config:
            raise PetMux.SequenceException(sequence)
        else:
            print("{}No Sequence {} found!{}".format(RED, sequence, NON))

    def run(self, sequence):
        """
        Run the selected sequence

        :param      sequence:  The sequence dictionary
        :type       sequence:  dict

        :returns:   Next sequence if selected
        :rtype:     str
        """
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
        # Step 2a: Check if window's panes are present to setup
        if 'NEW_PANES' in sequence.keys() and 'NEW_WINDOW' in sequence.keys():
            if 'SESSION' in sequence.keys():
                self.tmux.session(sequence['SESSION'])
            else:
                self.tmux.session(self.session)
            window = sequence['NEW_WINDOW']
            # Each pane is setup by the keyword commands
            pane_cnt = 0
            for pane in self.panes_dict[window]:
                if self.is_debug:
                    pane_name = [ k for k in pane.keys() ][0]
                    print("{}[ {} ]{}".format(CYN, pane_name, NON))
                # Workaround to get values for a pane
                cmd_dict = [ v for v in pane.values() ][0]
                # if SPLIT option is not defined for the pane, then use default split
                if "SPLIT" not in cmd_dict and pane_cnt > 0:
                    self.tmux.split(None)
                pane_cnt += 1
                # Process the pane commands by the order of key_func_dict.
                for key in self.key_func_dict.keys():
                    if key == 'SHELL':
                        if self.is_interactive:
                            input("{}  >>> 'Enter' to run[{}]: {} <<<{}".format(YEL, key, cmd_dict[key], NON))
                        self.key_func_dict[key](cmd_dict[key], pane_cnt)
                    elif key in cmd_dict:
                        self.key_func_dict[key](cmd_dict[key],)
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
                        if self.is_interactive:
                            input("{}  >>> 'Enter' to run[{}]: {} <<<{}".format(YEL, key, cmd_dict[key], NON))
                        try:
                            self.key_func_dict[key](cmd_dict[key])
                        except PetMux.SequenceException as e:
                            # A new sequence is request, switch to it.
                            print("{}Switching sequence to {}{}".format(GRN, e.sequence, NON))
                            return e.sequence
        return None


def main(args):
    # Process the command line arguments
    parser = argparse.ArgumentParser(description="PetMux: Programmed Executive TMUX")
    parser.add_argument('-r', '--run', action="store", help='Run sequence(s): --run <sequence|"sequence1 [sequence2 ..]">')
    parser.add_argument('-f', '--file', action="store", default='petmux.yaml', help="input configuration file: --file <your.petmux.config.file>.<yaml|json>>")
    parser.add_argument('-s', '--session', action="store", default=None, help="Specify tmux session: --session <your.session.name>")
    parser.add_argument('-k', '--kill', action="store_true", help="Kill the windows")
    parser.add_argument('-l', '--list', action="store_true", help="List available sequences")
    group_debug = parser.add_argument_group('Debug')
    group_debug.add_argument('-q', '--quiet', action="store_true", help="Supress debug output")
    group_debug.add_argument('-d', '--dryrun', action="store_true", help="Dry run. Print shell commands instead of executing")
    group_debug.add_argument('-i', '--interactive', action="store_true", help="Interactively step through the sequence")

    # parser.add_argument('sequence', action='store', default="test", help='Run sequence')
    args = parser.parse_args()

    if args.run or args.list:
        # Load the configuration file
        with open(args.file, 'r') as file:
            ext = os.path.splitext(args.file)[1]
            if  ext == '.yaml' or ext == '.yml':
                config = yaml.load(file, Loader=yaml.FullLoader)
            elif ext == '.json':
                config = json.load(file)

            if config:
                # Create PetMux object
                pm = PetMux(config, args.session, args.quiet == False, args.dryrun, args.interactive)
                # Use the petmux object
                if args.kill:
                    pm.kill()
                if args.list:
                    pm.list(args.run)
                elif args.run:
                    for sequence in args.run.split():
                        while sequence:
                            sequence = pm.run(sequence)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main(sys.argv[1:])
