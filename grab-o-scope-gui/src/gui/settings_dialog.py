from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QCheckBox,
                             QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config_data = config_manager.load_config()
        
        self.setWindowTitle("Grab-O-Scope Settings")
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Oscilloscope Settings Group
        scope_group = QGroupBox("Oscilloscope Settings")
        scope_layout = QFormLayout()
        
        self.instrument_name_input = QLineEdit()
        self.instrument_name_input.setPlaceholderText("e.g., 10.10.1.123 (IP address) or leave blank for auto-detect")
        self.instrument_name_input.setToolTip(
            "Enter part of the instrument's VISA resource name to filter detection:\n"
            "• IP address (e.g., 10.10.1.123)\n"
            "• Partial IP (e.g., 10.10.1)\n"
            "• Resource type (e.g., TCPIP)\n\n"
            "NOTE: This filters by VISA resource name, NOT by model name.\n"
            "Use the IP address for most reliable results.\n"
            "Leave blank to auto-detect all connected oscilloscopes."
        )
        scope_layout.addRow("Instrument Filter (IP):", self.instrument_name_input)
        
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)
        
        # Output Settings Group
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout()
        
        filename_layout = QHBoxLayout()
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("grab-o-scope.png")
        filename_layout.addWidget(self.filename_input)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_output_file)
        filename_layout.addWidget(browse_button)
        
        output_layout.addRow("Output Filename:", filename_layout)
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Leave blank for current directory")
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_input)
        
        browse_dir_button = QPushButton("Browse...")
        browse_dir_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(browse_dir_button)
        
        output_layout.addRow("Output Directory:", output_dir_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Info section
        info_label = QLabel(
            "<b>Tips:</b><br>"
            "• <b>Instrument Filter:</b> Leave blank for auto-detect (recommended)<br>"
            "• To filter by a specific scope, use its IP address (e.g., 10.10.1.231)<br>"
            "• <b>Note:</b> Model names (like DS1104Z) won't work - use IP address instead<br>"
            "• Output filename can include directory path"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.setMinimumWidth(100)
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def load_current_settings(self):
        """Load current settings into the form"""
        self.instrument_name_input.setText(self.config_data.get('instrument_name', ''))
        self.filename_input.setText(self.config_data.get('output_filename', 'grab-o-scope.png'))
        self.output_dir_input.setText(self.config_data.get('output_directory', ''))

    def browse_output_file(self):
        """Browse for output file location"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output File",
            self.filename_input.text() or "grab-o-scope.png",
            "PNG Images (*.png);;All Files (*.*)"
        )
        if filename:
            self.filename_input.setText(filename)

    def browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_input.text() or ""
        )
        if directory:
            self.output_dir_input.setText(directory)

    def save_settings(self):
        """Save settings to config file"""
        self.config_data['instrument_name'] = self.instrument_name_input.text()
        self.config_data['output_filename'] = self.filename_input.text() or 'grab-o-scope.png'
        self.config_data['output_directory'] = self.output_dir_input.text()
        
        self.config_manager.save_config(self.config_data)
        self.accept()