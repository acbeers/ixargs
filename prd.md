# ixargs

ixargs is a command line tool similar to xargs that lets you run commands
against a sequence of input arguments.   It's called like this:

some_tool | ixargs [options] cmd [args...]

For each line of the standard input, ixargs will call cmd with the arguments
listed and the line as the last argument.  ixargs will divide the screen into
two panels - one will contain the contents of the standard input, and the other
will contain the output of the command.  The user can scroll through the output
of the command, and also move between each line of standard input to run the
command with different inputs.  If the command produces color output, ixargs
will strive to preserve the color output.

## KEYBOARD SHORTCUTS

- `j`: move down one line
- `k`: move up one line
- ` `: move down one page
- `b`: move up one page
- `<`: move to the top of the output
- `>`: move to the bottom of output
- uparrow: move to the previous file
- downarray: move to the next file
- `q`: quit
- `?`: show help
- `/`: search
- `n`: search next
- `N`: search previous

## COMMAND LINE OPTIONS

- `-z`: split the window horizontally (list on left, default)
- `-v`: split the window vertically (list on top)
- `-I` replstr:  Replace replstr in the args list with the value of the line
  from stdin, rather than appending it after the arguments. 