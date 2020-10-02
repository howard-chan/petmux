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

# Program Execute TMUX (PetMux)

## 1. Overview

Program(Python) Execute TMUX (PeTmux) is a simple utility to automate the setup of your tmux session / window and drive the execution of shell operations for each targeted window in a controlled sequence.  This utility uses `tmux` commmand line interface to drive the session.  The setup and sequential execution are configured using a YAML or JSON file.

### 1.1. Features

1. Setup of tmux session, windows and pane layout
2. Control the delays in between shell commands
3. Support for regular expressions for capturing the shell command output into a shell variable
4. Support environment variables for shell commands
5. Configurations and sequences are described in `.yaml` or `.json`
6. Simple command line interface for controlling execution and sequences

### 1.2. Examples

For example, the following tmux setup

```sh




```

was configured with this YAML file

```yaml




```

## 2. Using petMux

### 2.1. Window Setup

#### 2.1.1. Window Keywords

### 2.2. Sequences

#### 2.2.1. Sequence Keywords

This section describes the **keywords** in a sequence that are always executed in the following order

```
"SESSION"
"WINDOW"
"PANE"
"SPLIT"
"CAPTURE"
"ECHO"
"SHELL"
"DELAY"
"PROMPT"
"PAUSE"
```

## 3. Architecture



## 4. Revision History
