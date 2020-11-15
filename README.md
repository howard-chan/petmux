> The MIT License (MIT)
>
> Copyright (c) 2020 Howard Chan
> https://github.com/howard-chan/petmux
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

# Programmed Executive TMUX (PetMux)

- [Programmed Executive TMUX (PetMux)](#programmed-executive-tmux-petmux)
  - [1. Overview](#1-overview)
    - [1.1. Features](#11-features)
    - [1.2. Limitations](#12-limitations)
    - [1.3. Requirements](#13-requirements)
  - [2. Using PetMux](#2-using-petmux)
  - [3. PetMux Configuration file](#3-petmux-configuration-file)
    - [3.1. Window Sequence](#31-window-sequence)
      - [3.1.1. Window Keywords](#311-window-keywords)
    - [3.2. Task Sequences](#32-task-sequences)
      - [3.2.1. Sequence Keywords](#321-sequence-keywords)
  - [4. Cookbook](#4-cookbook)
    - [4.1. Examples](#41-examples)
  - [5. Revision History](#5-revision-history)

## 1. Overview

Programmed Executive TMUX (PetMux) is a simple python utility for automating tasks in a tmux session.  With PetMux you can for example:

1. Automate the setup of different tmux session/windows environment for development or testing.
2. Automate mundane tasks that requires interactions with the shell or command line programs that execute in a tmux pane.
3. Capture the output of a program and use it to dynamically change the sequence flow.
4. Share your .yaml or .json configuration file to replicate your environment and automations with your peers and friends.

PetMux utilizes `tmux`'s command line interface to drive the shell operations, interactions and output captures of command line programs the run in a pane.  Automation sequences can be modified to work interactively (via prompts) or dynamically through regular expressions and decisions trees.  Window setups are configured and sequences are described by a configuration file based on YAML or JSON.

### 1.1. Features

1. Setup of tmux session, windows and pane layout
2. Control the delays in between shell commands
3. Support for regular expressions for extracting the shell command output into a shell variable
4. Setting environment variables for shell commands
5. Capturing the contents of a pane to a file
6. Support for debug and interactive modes
7. Support for decision tree based flows and sequence reuse
8. Configurations and sequences are described in `.yaml` or `.json`
9. Simple command line interface for controlling execution and sequences

### 1.2. Limitations

At least 2 shells are required.  One for running the PetMux file and the other running a tmux session.

### 1.3. Requirements

1. `tmux` - This has been tested with tmux 3.0a, although other version will probably work as well.
2. `yaml` - Although `.json` can be used exclusively, `.yaml` is far easier to read.
3. `python3` - PetMux requires ordered dictionaries supported by Python 3.  Although, this script can be ported for Python 2 by replacing dictionaries from `collections.OrderedDict`.  Also `yaml` will need to be replaced by `oyaml` which supports ordered dictionaries.


## 2. Using PetMux

To use PetMux effectively, it is recommended to add the location of `petmux.py` to your path.

```sh
PetMux: Programmed Executive TMUX

optional arguments:
  -h, --help            show this help message and exit
  -r RUN, --run RUN     Run sequence(s): --run <sequence|"sequence1 [sequence2
                        ..]">
  -f FILE, --file FILE  input configuration file: --file
                        <your.petmux.config.file>.<json|yaml>>
  -s SESSION, --session SESSION
                        Specify tmux session: --session <your.session.name>
  -k, --kill            Kill the windows
  -l, --list            List available sequences

Debug:
  -q, --quiet           Supress debug output
  -d, --dryrun          Dry run. Print shell commands instead of executing
  -i, --interactive     Interactively step through the sequence
```

PetMux will check the current directory for `petmux.yaml` configuration file unless you specify the `.yaml` or `.json` file

    ```sh
    petmux.py -f <your.petmux.config.file>.<yaml|json>
    ```

The petmux config file is a dictionary that contains a list of sequences.  You can list these sequences with:

```sh
$ petmux.py -l
Loading environment
    tmux> set-environment HOME_DIR 'None'
    tmux> set-environment WORKING_DIR '~/Documents'
    tmux> set-environment EDITOR 'vi'
['setup2', 'test3', 'test2', 'test', 'setup1']
```

You can then specify the sequence(s) using `-r sequence` or `--run sequence`.  If multiple sequences are specified, then it needs to be quoted.  Usually there are at least 2 sequences in a configuration file.  One for the window layout and the other for the sequence.

```sh
$ petmux.py -r "setup2 test"
```

To start fresh, its best to also close the tmux window or have petmux perform this by kill all of the windows specified in the petmux configuration file.

```sh
$ petmux.py -r "setup2 test" -k
```

PetMux will issue commands to the last select tmux session.  To specify a specific tmux session, use `-s <SESSION>` or `--session <SESSION>`.  This will tell PetMux to issue all commands to a specific session, window and pane.

```sh
$ petmux.py -r "setup2 test" -s "MySession"
```

For debugging purposes, you can do a dry run of the sequence where it will echo the commands into the targeted pane instead of issue the command to the shell or program.

```sh
$ petmux.py -r "setup2 test" -d
```

If the sequence is running to fast or you are debugging the sequence flow, you can specify `-i` or `--interactive` to single step each command issued.

```sh
$ petmux.py -r "setup2 test" -i
```

## 3. PetMux Configuration file

Sequences maybe described in `.yaml` or `.json` configuration files.  Although `.yaml` is a superset of `.json`, it is preferred over `.json` since it is easier to read and supports comments/annotations.  Here is an example of a sample `.yaml` configuration file.

```yaml

#TODO
```

The PetMux configuration is an ordered dictionary containing sequences for the window setup and automating a task with multiple panes.  There are 2 types of sequences.
1. **Window Sequence** - A dictionary containing the key `NEW_WINDOW` and `NEW_PANES` used in setting up the tmux window/pane configuration and initial shell commands.
2. **Task Sequence** - A dictionary containing the key `CMDS` used to send the shell sequences to the panes.

### 3.1. Window Sequence

What makes tmux extremely useful is being able to interact and manage multiple programs residing in their own pane.  tmux provides a sufficient number of command-line APIs for controlling the programs running in these panes.

PetMux provides a mechanism to describe the layout of the panes for the programs to run in.


#### 3.1.1. Window Keywords

The following are the minimal keys for a window sequence.

- `NEW_WINDOW` - This key is used to selects or creates a window in the current session, unless `SESSION` is specified (see below).

    ```yaml
    # Example of a work environemnt setup
    NEW_WINDOW: MyWork
    ```

- `NEW_PANE` - This key contains a list of panes to be created.  Each listed pane can contain a dictionary

    ```yaml
        NEW_PANES:
        # The window layout is described here
        - editor:
            SHELL:
                - cd ${WORKING_DIR}
                - ${EDITOR}
        - vmstat:
            SHELL:
                - cd ${OUTPUT_DIR}
                - watch -n 1 vmstat
        - top:
            SPLIT: -v -p 70
            SHELL:
                - top
    ```
The following are optional, but used to proper describe a window sequence.

- `SESSION` - Selects the session by name
- `WINDOW` - Specifies the Window's name
- `SPLIT` - Splits the window vertically or horizontally
- `SHELL` -

Generally the window sequence should be kept as simple as possible, with a focus on setting up the panes in the window, the pane layout and initial set of `SHELL` commands


### 3.2. Task Sequences

Sequences is what PetMux is all about.  Once the panes in a window are setup, a sequence can drive multiple shell commands and interact with command line programs residing in their own pane.

In tmux   PetMux supports multiple sequences which can be nested

#### 3.2.1. Sequence Keywords

This section describes the **keywords** in a sequence that are always executed in the following order

1.  `SESSION` - Selects the tmux session by name to issue the commands to.
2.  `WINDOW` - Selects the tmux window by name to issue the commands to.
3.  `PANE` - Selects the pane by name to issue the commands to.
5.  `DELAY` - Specifies the delay in seconds between issued shell commands
6.  `ECHO` - Specifies a user message in the shell running tmux.
7.  `SEQUENCE` - Specifies a sequence by name to switch to immediately.  Used to change the program flow or to refactor other sequences.
8.  `SHELL` - Specifies a list of SHELL or Program interactions to be sent to the pane
9.  `EXTRACT` - Specifies the SHELL command, the regular expression to extract the value from the command output and the environment variable to save the extracted value to.
10. `CAPTURE` - Specifies a file to capture the current selected pane.
11. `PROMPT` - Specifies a user interactive prompt.  Uses to provide options to the user to respond to.
12. `DECIDE` - Dictionary containing the variable and a list of options to execute
13. `PAUSE` - Pauses for X number of seconds before running the next item in the sequence.
14. `ABORT` - Aborts the petmux session

**Provides examples of how to use each key**

## 4. Cookbook

**TODO**

### 4.1. Examples

**TODO**

For example, the following tmux setup

```sh




```

was configured with this YAML file

```yaml




```


## 5. Revision History
