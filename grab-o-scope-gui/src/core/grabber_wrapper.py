import subprocess
import os
import sys

class GrabberWrapper:
    def __init__(self, options):
        self.options = options
        # Get the path to the parent directory's grab_o_scope.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_parent_dir = os.path.dirname(os.path.dirname(current_dir))
        self.grab_o_scope_path = os.path.join(parent_parent_dir, '..', 'grab_o_scope.py')
        self.grab_o_scope_path = os.path.abspath(self.grab_o_scope_path)
        self.output_callback = None

    def set_output_callback(self, callback):
        """Set callback function to receive output lines"""
        self.output_callback = callback

    def capture_screen(self, filename=None):
        """Capture oscilloscope screen and return the filename"""
        if filename:
            self.options.filename = filename
        
        result = self.run_grab_o_scope()
        if result is not None:
            return self.options.filename
        else:
            raise Exception("Failed to capture screen from oscilloscope")

    def run_grab_o_scope(self):
        # Construct the command to run the grab_o_scope.py script
        command = [
            sys.executable,  # Use the same Python interpreter
            self.grab_o_scope_path
        ]

        # Add options to the command
        if self.options.name:
            command.extend(['--name', self.options.name])
        if self.options.filename:
            command.extend(['--filename', self.options.filename])
        if self.options.auto_view:
            command.append('--auto_view')
        if self.options.verbose:
            command.append('--verbose')
        if self.options.trace:
            command.append('--trace')

        # Execute the command and capture the output
        try:
            if self.output_callback:
                self.output_callback(f"Running: {' '.join(command)}")
            
            # Run process and capture output line by line
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            output_lines = []
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    output_lines.append(line)
                    if self.output_callback:
                        self.output_callback(line)
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                error_msg = '\n'.join(output_lines[-5:])  # Last 5 lines
                raise Exception(f"Process failed with code {return_code}: {error_msg}")
            
            return '\n'.join(output_lines)
            
        except subprocess.SubprocessError as e:
            error_msg = f"Subprocess error: {str(e)}"
            if self.output_callback:
                self.output_callback(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error running grab_o_scope: {str(e)}"
            if self.output_callback:
                self.output_callback(error_msg)
            raise Exception(error_msg)

    def set_options(self, name=None, filename=None, auto_view=False, verbose=False, trace=False):
        if name:
            self.options.name = name
        if filename:
            self.options.filename = filename
        self.options.auto_view = auto_view
        self.options.verbose = verbose
        self.options.trace = trace