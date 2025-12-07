from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QFileDialog, QMessageBox, QTextEdit, QLabel,
                             QSplitter, QMenuBar, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QClipboard
from PyQt5.QtWidgets import QApplication
from core.grabber_wrapper import GrabberWrapper
from gui.settings_dialog import SettingsDialog
from core.config_manager import ConfigManager
from argparse import Namespace
import os

class CaptureThread(QThread):
    """Thread for capturing oscilloscope screen without blocking GUI"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    output = pyqtSignal(str)
    
    def __init__(self, grabber):
        super().__init__()
        self.grabber = grabber
        # Set up output callback to emit signals
        self.grabber.set_output_callback(self.emit_output)
    
    def emit_output(self, line):
        """Callback to emit output line"""
        self.output.emit(line)
    
    def run(self):
        try:
            filename = self.grabber.capture_screen()
            self.finished.emit(filename)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grab-O-Scope GUI")
        self.setGeometry(100, 100, 900, 700)
        
        # Load configuration
        self.config = ConfigManager()
        config_data = self.config.load_config()
        
        # Create options from config
        self.options = Namespace(
            name=config_data.get('instrument_name'),
            filename=config_data.get('output_filename', 'grab-o-scope.png'),
            auto_view=False,
            verbose=True,  # Always verbose for GUI output
            trace=True  # Always enable trace mode for detailed output
        )
        self.grabber = GrabberWrapper(self.options)
        self.last_captured_image = None
        self.capture_thread = None

        self.init_ui()
        self.create_menu_bar()

    def init_ui(self):
        # Main layout with splitter
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create splitter for image and log
        splitter = QSplitter(Qt.Vertical)
        
        # Top section: Image display
        image_widget = QWidget()
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(5, 5, 5, 5)
        image_layout.setSpacing(5)
        
        image_label = QLabel("Captured Image:")
        image_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 2px;")
        image_label.setMaximumHeight(25)
        image_layout.addWidget(image_label)
        
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.image_display.setMinimumHeight(300)
        self.image_display.setText("No image captured yet")
        self.image_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_display.customContextMenuRequested.connect(self.show_image_context_menu)
        image_layout.addWidget(self.image_display, stretch=1)  # Give it stretch priority
        
        image_widget.setLayout(image_layout)
        splitter.addWidget(image_widget)
        
        # Bottom section: Log output
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(5, 5, 5, 5)
        log_layout.setSpacing(5)
        
        log_label = QLabel("Console Output:")
        log_label.setStyleSheet("font-weight: bold; font-size: 10pt; padding: 2px;")
        log_label.setMaximumHeight(25)
        log_layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)  # Minimum height
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 9pt;")
        log_layout.addWidget(self.log_output)
        
        log_widget.setLayout(log_layout)
        splitter.addWidget(log_widget)
        
        # Set splitter proportions (image section gets more space)
        # Also set initial sizes for the splitter sections
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([450, 200])  # Initial sizes, 450px for image, 200px for console
        
        main_layout.addWidget(splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setMinimumHeight(40)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #d13438;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #a52a2e;
            }
            QPushButton:pressed {
                background-color: #8b2327;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.clear_button.clicked.connect(self.clear_image)
        self.clear_button.setEnabled(False)  # Disabled until image is captured
        button_layout.addWidget(self.clear_button, stretch=1)
        
        self.capture_button = QPushButton("Capture Screen")
        self.capture_button.setMinimumHeight(40)
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.capture_button.clicked.connect(self.capture_screen)
        button_layout.addWidget(self.capture_button, stretch=2)
        
        self.save_button = QPushButton("💾 Save As...")
        self.save_button.setMinimumHeight(40)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0e6b0e;
            }
            QPushButton:pressed {
                background-color: #0c5a0c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_button.clicked.connect(self.save_image_as)
        self.save_button.setEnabled(False)  # Disabled until image is captured
        button_layout.addWidget(self.save_button, stretch=1)
        
        self.settings_button = QPushButton("⚙️ Settings")
        self.settings_button.setMinimumHeight(40)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(self.settings_button, stretch=1)
        
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.log("Grab-O-Scope GUI initialized")
        self.log(f"Ready to capture from oscilloscope")

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Image...', self)
        open_action.triggered.connect(self.open_image_file)
        file_menu.addAction(open_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        clear_log_action = QAction('Clear Log', self)
        clear_log_action.triggered.connect(self.clear_log)
        view_menu.addAction(clear_log_action)

    def log(self, message):
        """Add message to log output"""
        self.log_output.append(message)
        # Auto-scroll to bottom
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def clear_log(self):
        """Clear the log output"""
        self.log_output.clear()

    def capture_screen(self):
        """Start capture in separate thread"""
        if self.capture_thread and self.capture_thread.isRunning():
            self.log("⚠️ Capture already in progress...")
            return
        
        self.capture_button.setEnabled(False)
        self.capture_button.setText("⏳ Capturing...")
        self.log("=" * 50)
        self.log("Starting oscilloscope capture...")
        
        # Create and start capture thread
        self.capture_thread = CaptureThread(self.grabber)
        self.capture_thread.finished.connect(self.on_capture_finished)
        self.capture_thread.error.connect(self.on_capture_error)
        self.capture_thread.output.connect(self.log)
        self.capture_thread.start()

    def on_capture_finished(self, filename):
        """Handle successful capture"""
        self.capture_button.setEnabled(True)
        self.capture_button.setText("Capture Screen")
        self.log(f"Success! Screen captured and saved as: {filename}")
        self.last_captured_image = os.path.abspath(filename)
        self.display_image(self.last_captured_image)
        self.save_button.setEnabled(True)  # Enable Save button
        self.clear_button.setEnabled(True)  # Enable Clear button

    def on_capture_error(self, error_msg):
        """Handle capture error"""
        self.capture_button.setEnabled(True)
        self.capture_button.setText("Capture Screen")
        self.log(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "Capture Error", f"Failed to capture screen:\n{error_msg}")

    def display_image(self, image_path):
        """Display image in the GUI"""
        if not os.path.exists(image_path):
            self.log(f"⚠️ Image file not found: {image_path}")
            return
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.log(f"⚠️ Failed to load image: {image_path}")
            return
        
        # Scale image to fit display while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_display.width() - 10,
            self.image_display.height() - 10,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_display.setPixmap(scaled_pixmap)
        self.log(f"Displaying image: {os.path.basename(image_path)}")

    def clear_image(self):
        """Clear the displayed image"""
        self.image_display.clear()
        self.image_display.setText("No image captured yet")
        self.last_captured_image = None
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.log("🗑️ Image cleared")

    def open_image_file(self):
        """Open and display an image file"""
        image_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Image File", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if image_path:
            self.display_image(image_path)
            self.last_captured_image = image_path
            self.save_button.setEnabled(True)  # Enable Save button
            self.clear_button.setEnabled(True)  # Enable Clear button

    def save_image_as(self):
        """Save the current image to a new location"""
        if not self.last_captured_image:
            QMessageBox.warning(self, "No Image", "No image to save. Capture an image first.")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image As",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)"
        )
        if save_path:
            try:
                import shutil
                shutil.copy(self.last_captured_image, save_path)
                self.log(f"Image saved to: {save_path}")
                QMessageBox.information(self, "Success", f"Image saved to:\n{save_path}")
            except Exception as e:
                self.log(f"❌ Failed to save image: {str(e)}")
                QMessageBox.critical(self, "Save Error", f"Failed to save image:\n{str(e)}")

    def copy_to_clipboard(self):
        """Copy the current image to clipboard"""
        if not self.last_captured_image:
            QMessageBox.warning(self, "No Image", "No image to copy. Capture an image first.")
            return
        
        try:
            # Load the image as QPixmap
            pixmap = QPixmap(self.last_captured_image)
            if pixmap.isNull():
                self.log(f"❌ Failed to load image for clipboard")
                QMessageBox.warning(self, "Copy Error", "Failed to load image for clipboard")
                return
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            self.log("Image copied to clipboard")
        except Exception as e:
            self.log(f"❌ Failed to copy to clipboard: {str(e)}")
            QMessageBox.critical(self, "Copy Error", f"Failed to copy to clipboard:\n{str(e)}")
    
    def show_image_context_menu(self, position):
        """Show context menu for image display"""
        if not self.last_captured_image:
            return
        
        # Create context menu
        menu = QMenu(self)
        copy_action = menu.addAction("Copy Image to Clipboard")
        copy_action.triggered.connect(self.copy_to_clipboard)
        
        # Show menu at cursor position
        menu.exec_(self.image_display.mapToGlobal(position))

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            # Reload configuration
            config_data = self.config.load_config()
            self.options.name = config_data.get('instrument_name')
            self.options.filename = config_data.get('output_filename', 'grab-o-scope.png')
            self.options.trace = True  # Always keep trace mode enabled
            self.grabber.options = self.options
            self.log("⚙️ Settings updated")
