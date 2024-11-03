# grab-o-scope
Capture your oscilliscope screen in a .png file

`grab-o-scope` is a Python-based command line utility to capture screenshots
a variety of oscilloscopes and save them as PNG files.

_Note: `grab-o-scope` currently supports the Rigol DHO924 and DS1054Z
oscilloscopes.  Other brands and models can be easily added -- see the
developer notes on on "Adding support for a new Oscilloscope"._

## Features

- Captures and saves screen images in PNG format.
- Optionally opens the captured image in the default system viewer.
- Verbose and trace modes for detailed logging and debugging.

## Requirements

- Python 3.8+
- `pipenv` for managing virtual environments
- `pyvisa` library for VISA instrument control
- A VISA-compatible resource manager, such as NI-VISA, installed on your system

## Installation

1. Clone this repository:
```bash
pip install pyvisa
git clone git@github.com:rdpoor/grab-o-scope.git # clone the respository
cd grab-o-scope
```
Note: Ensure that NI-VISA or a compatible VISA library is installed on your
system.  `grab-o-scope` relies on pyvisa to interface with the oscilloscope.

## Usage

```bash
cd grab-o-scope
python grab_oscope.py [options]
```
Command-line Options

    -n, --name: Specify the name or partial name of a specific instrument (e.g., LAN address or serial number).
    -f, --filename: Set the output file name (default: grab-o-scope.png).
    -a, --auto_view: Automatically open the saved PNG file in the system's default image viewer.
    -v, --verbose: Enable verbose output.
    -t, --trace: Enable trace mode for debugging output.

## Examples

### Most General
If you have exactly one grab-o-scope supported oscilloscope attached, this is
all you need.  It will grab the contents of oscilloscope screen write it to
`grab-o-scope.png` and then display the captured .png file:
```bash
python grab_o_scope.py --auto_view
```
This will use pyvisa to search for all connected instruments, then issues an
`*IDN?` command on each instrument to find an oscilloscope that `grab-o-scope`
recognizes.  If it finds a single instance, it will use that.  If it finds
multiple instances, it will prompt you to use the `--name` argument to narrow
the search.

### Faster
Note however a full search can be rather slow, especially if you have a lot of
test gear connected to your USB bus.  If you're impatient and you know already
know what's retuned by the VISA resource name, you can speed things up by
specifying it with the `--name` argument:
```bash
python grab_o_scope.py --name DHO --auto_view
```
In this case, `grab-o-scope` will search only for instruments that have `DHO`
as part of their VISA resource name (e.g. a Rigol DHO923).  This will run much
faster.

### Network Connected Oscilloscopes
If your device is connected via TCP/IP, you can use the `--name` argument to
single out the device, as in:
```bash
python grab_o_scope.py --name 127.0.0.5 --auto_view
```

### Writing to a custom filename
By default, `grab-o-scope` will write the captured screen to `grab-o-scope.png`
in the current directory.  Use the `--filename` argument to specify another
directory or filename:
```bash
python grab_o_scope.py --filename "custom_filename.png"
```

### Handy tip: timestamped filenames
This is not specific to `grab-o-scope`, but if you want to timestamp your .png
files, you can use the `time` command to create the filename:
```bash
python grab_o_scope.py --filename `date --iso-8601=seconds`.png
```
This will write a filename of the form "2024-11-03T07:29:02-08:00.png", which
sorts nicely and avoids spaces in the filenames.

## Developer Details

### How It Works

`grab-o-scope` uses the pyvisa module to search for connected instruments,
identifies compatible oscilloscopes by querying their IDN strings, and then uses
the appropriate grabber class (e.g., RigolDHO924Grabber or RigolDS1054ZGrabber)
to retrieve display data.

### Code Structure

    GrabOScope: The main class handling the search and identification of
      connected oscilloscopes, as well as managing the screen capture process.
    Grabber: Base class for oscilloscope-specific screen capture.
    RigolDHO924Grabber, RigolDS1054ZGrabber, etc: Subclasses of Grabber that
      define the screen capture process for specific oscilloscopes.

## Contributing

### Adding Support for New Oscilloscopes

#### Python experts:

To add support for a new oscilloscope model:

    Define a new subclass of Grabber.
    Specify an regexp IDN_PATTERN for matching the oscilloscope's IDN string.
    Implement a capture_screen method to retrieve the display data.
    Add your new Grabber class to GrabOScope.KNOWN_GRABBERS.

#### Not a Python expert?
If you have a specific oscilliscope that you want supported, do the following
to capture detailed debugging information about the connected instrument(s):
```bash
grab_o_scope.py --trace
```
Copy the resulting output and create a new issue in https://github.com/rdpoor/grab-o-scope/issues
with a subject of "Requesting support for \<oscilliscope make and model\>. When
possible, include a link to online programming documentation for your
oscilliscope.

We cannot promise that your instrument will get support, but with luck some good
netizen will take up the challenge.

### Other issues and bugs

Contributions are welcome! Feel free to submit issues, fork the repository and
open pull requests.

## License

MIT License. See LICENSE file for details.
