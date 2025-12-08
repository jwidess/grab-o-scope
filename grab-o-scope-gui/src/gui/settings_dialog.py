from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QCheckBox,
                             QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config_data = config_manager.load_config()
        
        self.setWindowTitle("Grab-O-Scope GUI Settings")
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Oscilloscope Settings Group
        scope_group = QGroupBox("Search Settings")
        scope_layout = QFormLayout()
        
        self.instrument_name_input = QLineEdit()
        self.instrument_name_input.setPlaceholderText("e.g., DHO924, 10.10.1.123, leave blank for auto-detect")
        self.instrument_name_input.setToolTip(
            "Filter oscilloscope detection (case-insensitive):\n"
            "• Model name or manufacturer (e.g., DS, DHO924, Rigol)\n"
            "• IP address (e.g., 10.10.1.123)\n"
            "• Resource type (e.g., TCPIP, USB)\n\n"
            "Searches both VISA resource names and device IDN strings.\n"
            "Leave blank to auto-detect all connected scopes."
        )
        scope_layout.addRow("Instrument Filter:", self.instrument_name_input)
        
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)
        
        # Output Settings Group
        output_group = QGroupBox("Capture Storage Settings")
        output_layout = QFormLayout()
        
        # Capture directory
        self.capture_dir_input = QLineEdit()
        self.capture_dir_input.setPlaceholderText("Leave blank for default 'captures' folder")
        capture_dir_layout = QHBoxLayout()
        capture_dir_layout.addWidget(self.capture_dir_input)
        
        browse_capture_dir_button = QPushButton("Browse...")
        browse_capture_dir_button.setAutoDefault(False)
        browse_capture_dir_button.clicked.connect(self.browse_capture_dir)
        capture_dir_layout.addWidget(browse_capture_dir_button)
        
        output_layout.addRow("Capture Directory:", capture_dir_layout)
        
        # Add note about automatic naming
        note_label = QLabel(
            "<i>Note: Captures are auto named with timestamp:<br>"
            "capture_YYYYMMDD_HHMMSS.png (e.g., capture_20251206_143052.png)</i>"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #888; font-size: 9pt; padding: 5px;")
        output_layout.addRow("", note_label)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Info section
        info_label = QLabel(
            "<b>Tips:</b><br>"
            "• <b>Instrument Filter:</b> Leave blank for auto-detect<br>"
            "• Search is case-insensitive<br>"
            "• Partial matches: 'DS' finds all DS series, '10.10.1' finds subnet<br>"
            "• Captures are automatically organized with timestamps<br>"
            "• Customize capture directory or use the default 'captures' folder"
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
        self.save_button.setDefault(True)  # Make Save the default button
        self.save_button.setAutoDefault(True)
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
        cancel_button.setAutoDefault(False)  # Prevent Cancel from being default
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
        self.capture_dir_input.setText(self.config_data.get('capture_directory', ''))

    def browse_capture_dir(self):
        """Browse for capture directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Capture Directory",
            self.capture_dir_input.text() or ""
        )
        if directory:
            self.capture_dir_input.setText(directory)

    def save_settings(self):
        """Save settings to config file"""
        self.config_data['instrument_name'] = self.instrument_name_input.text()
        self.config_data['capture_directory'] = self.capture_dir_input.text()
        
        self.config_manager.save_config(self.config_data)
        self.accept()
