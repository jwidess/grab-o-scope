# grab-o-scope-gui
_...a GUI wrapper for the grab-o-scope command-line tool, designed to simplify the process of capturing oscilloscope screen images._

`grab-o-scope-gui` is a Python-based graphical user interface that allows users to easily capture screenshots from various oscilloscopes and display them. This project serves as a wrapper around the existing `grab_o_scope.py` script, providing a user-friendly interface while keeping the original functionality intact for future enhancements.

![example screen grab](./resources/assets/example-grab.png)

## Features

- Intuitive GUI for capturing oscilloscope screen images
- Options to configure oscilloscope settings, such as network address
- Display captured images in a dedicated viewer
- Easy access to the original command-line functionality

## Supported Devices

- Keysight InfiniVision 3000T X-Series Oscilloscopes
- Rigol DHO924
- Rigol DS1054Z

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/grab-o-scope-gui.git
cd grab-o-scope-gui
```

### 2. Install required modules

You can install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

### 3. Run the application

To start the GUI application, run:

```bash
python src/main.py
```

## Usage

1. Launch the application.
2. Enter the oscilloscope's network address in the settings dialog.
3. Click the "Capture" button to take a screenshot of the oscilloscope display.
4. The captured image will be displayed in the image viewer.

## Development

To contribute to the project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your branch and create a pull request.

## Packaging

For Windows users, the application can be packaged into a single executable using the provided build scripts. Refer to the `build` directory for instructions on creating an installer.

## License

MIT License. See LICENSE file for details.