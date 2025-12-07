from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QFileDialog, QMessageBox, QTextEdit, QLabel,
                             QSplitter, QMenuBar, QMenu, QAction, QShortcut)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QClipboard, QKeySequence
from PyQt5.QtWidgets import QApplication
from core.grabber_wrapper import GrabberWrapper
from gui.settings_dialog import SettingsDialog
from core.config_manager import ConfigManager
from argparse import Namespace
import os
from datetime import datetime

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
        
        # Create options from config (filename will be set dynamically per capture)
        self.options = Namespace(
            name=config_data.get('instrument_name'),
            filename=None,  # Will be set dynamically with timestamp
            auto_view=False,
            verbose=True,  # Always verbose for GUI output
            trace=True  # Always enable trace mode for detailed output
        )
        self.grabber = GrabberWrapper(self.options)
        self.last_captured_image = None
        self.capture_thread = None

        self.init_ui()
        self.create_menu_bar()
        
        # Update navigation state on startup
        self.update_navigation_buttons()
        
        # Set up timer to periodically check for file changes in captures directory
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_navigation_state)
        self.refresh_timer.start(1000)

    def refresh_navigation_state(self):
        """Periodically refresh navigation buttons to detect external file changes"""
        # Only update if not actively capturing
        if not (self.capture_thread and self.capture_thread.isRunning()):
            self.update_navigation_buttons()

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
        
        # Header with title and navigation info
        header_layout = QHBoxLayout()
        image_label = QLabel("Captured Image:")
        image_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 2px;")
        image_label.setMaximumHeight(25)
        header_layout.addWidget(image_label)
        
        header_layout.addStretch()
        
        self.nav_info_label = QLabel("")
        self.nav_info_label.setStyleSheet("color: #666; font-size: 10pt; padding: 2px;")
        self.nav_info_label.setMaximumHeight(25)
        header_layout.addWidget(self.nav_info_label)
        
        image_layout.addLayout(header_layout)
        
        # Create horizontal layout for image with navigation buttons
        image_nav_layout = QHBoxLayout()
        
        # Left arrow button
        self.prev_button = QPushButton("◀")
        self.prev_button.setMaximumWidth(50)
        self.prev_button.setSizePolicy(self.prev_button.sizePolicy().horizontalPolicy(), 
                                       self.prev_button.sizePolicy().Expanding)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                font-size: 20pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #999999;
            }
        """)
        self.prev_button.setToolTip("Previous image (older)")
        self.prev_button.clicked.connect(self.show_previous_image)
        self.prev_button.setEnabled(False)
        image_nav_layout.addWidget(self.prev_button)
        
        # Image display in the center
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.image_display.setMinimumHeight(300)
        self.image_display.setText("No image captured yet")
        self.image_display.setScaledContents(False)  # We'll handle scaling manually
        self.image_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_display.customContextMenuRequested.connect(self.show_image_context_menu)
        image_nav_layout.addWidget(self.image_display, stretch=1)  # Give it stretch priority
        
        # Store original pixmap for rescaling
        self.original_pixmap = None
        
        # Right arrow button
        self.next_button = QPushButton("▶")
        self.next_button.setMaximumWidth(50)
        self.next_button.setSizePolicy(self.next_button.sizePolicy().horizontalPolicy(), 
                                       self.next_button.sizePolicy().Expanding)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                font-size: 20pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #999999;
            }
        """)
        self.next_button.setToolTip("Next image (newer)")
        self.next_button.clicked.connect(self.show_next_image)
        self.next_button.setEnabled(False)
        image_nav_layout.addWidget(self.next_button)
        
        image_layout.addLayout(image_nav_layout)
        
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
        
        # Set up keyboard shortcuts for navigation
        self.setup_keyboard_shortcuts()
        
        self.log("Grab-O-Scope GUI initialized")
        self.log(f"Ready to capture from oscilloscope")

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for navigation"""
        # Left arrow key for previous image
        left_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        left_shortcut.activated.connect(self.show_previous_image)
        
        # Right arrow key for next image
        right_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        right_shortcut.activated.connect(self.show_next_image)

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
        
        open_captures_folder_action = QAction('Open Captures Folder', self)
        open_captures_folder_action.triggered.connect(self.open_captures_folder)
        file_menu.addAction(open_captures_folder_action)
        
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

    def get_capture_directory(self):
        """Get or create the captures directory"""
        config_data = self.config.load_config()
        capture_dir = config_data.get('capture_directory', '')
        
        # If no custom directory, use default 'captures' folder in GUI directory
        if not capture_dir:
            capture_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'captures')
        
        # Create directory if it doesn't exist
        os.makedirs(capture_dir, exist_ok=True)
        return capture_dir

    def generate_timestamped_filename(self):
        """Generate a filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_dir = self.get_capture_directory()
        filename = os.path.join(capture_dir, f"capture_{timestamp}.png")
        return filename

    def capture_screen(self):
        """Start capture in separate thread"""
        if self.capture_thread and self.capture_thread.isRunning():
            self.log("⚠️ Capture already in progress...")
            return
        
        # Generate timestamped filename for this capture
        self.options.filename = self.generate_timestamped_filename()
        self.grabber.options = self.options
        
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
        
        # Store original pixmap for rescaling on resize
        self.original_pixmap = pixmap
        
        # Scale and display
        self.scale_and_display_image()
        
        # Update navigation buttons
        self.update_navigation_buttons()

    def scale_and_display_image(self):
        """Scale the stored pixmap to fit the current display size"""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return
        
        # Get the available size (account for margins and borders)
        available_width = self.image_display.width() - 10
        available_height = self.image_display.height() - 10
        
        # Scale image to fit display while maintaining aspect ratio
        scaled_pixmap = self.original_pixmap.scaled(
            available_width,
            available_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_display.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Handle window resize to rescale the image"""
        super().resizeEvent(event)
        # Rescale image when window is resized
        if self.original_pixmap is not None:
            self.scale_and_display_image()

    def get_sorted_captures(self):
        """Get list of image files from captures directory sorted by modification time"""
        capture_dir = self.get_capture_directory()
        
        if not os.path.exists(capture_dir):
            return []
        
        # Get all image files
        image_files = []
        for filename in os.listdir(capture_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                filepath = os.path.join(capture_dir, filename)
                if os.path.isfile(filepath):
                    image_files.append(filepath)
        
        # Sort by modification time (oldest first)
        image_files.sort(key=lambda x: os.path.getmtime(x))
        
        return image_files

    def update_navigation_buttons(self):
        """Update the enabled/disabled state of navigation buttons"""
        sorted_captures = self.get_sorted_captures()
        
        # If no captures exist at all, disable navigation
        if not sorted_captures:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.nav_info_label.setText("")
            return
        
        # If we have captures but no image is loaded, enable both to allow initial navigation
        if not self.last_captured_image or not os.path.exists(self.last_captured_image):
            self.prev_button.setEnabled(len(sorted_captures) > 0)
            self.next_button.setEnabled(len(sorted_captures) > 0)
            self.nav_info_label.setText(f"Total images: {len(sorted_captures)} | Use ← → arrow keys to navigate")
            return
        
        # If current image is not in the list (was deleted or modified), enable both buttons
        # to allow user to navigate to find valid images
        if self.last_captured_image not in sorted_captures:
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.nav_info_label.setText(f"Total images: {len(sorted_captures)} | Use ← → arrow keys to navigate")
            return
        
        current_index = sorted_captures.index(self.last_captured_image)
        total_images = len(sorted_captures)
        
        # Update info label
        self.nav_info_label.setText(f"Image {current_index + 1} of {total_images} | Use ← → arrow keys to navigate")
        
        # Enable previous button if not at the beginning
        self.prev_button.setEnabled(current_index > 0)
        
        # Enable next button if not at the end
        self.next_button.setEnabled(current_index < len(sorted_captures) - 1)

    def show_previous_image(self):
        """Show the previous image (older in time)"""
        if not self.last_captured_image:
            # If no image loaded, try to load the most recent one
            sorted_captures = self.get_sorted_captures()
            if sorted_captures:
                self.last_captured_image = sorted_captures[-1]
                self.display_image(self.last_captured_image)
                self.save_button.setEnabled(True)
                self.clear_button.setEnabled(True)
            return
        
        sorted_captures = self.get_sorted_captures()
        if not sorted_captures:
            return
        
        # If current image was deleted/modified, find the closest one by timestamp
        if self.last_captured_image not in sorted_captures:
            current_mtime = os.path.getmtime(self.last_captured_image) if os.path.exists(self.last_captured_image) else 0
            # Find the closest image that's older
            prev_image = None
            for img in sorted_captures:
                img_mtime = os.path.getmtime(img)
                if img_mtime < current_mtime:
                    prev_image = img
                else:
                    break
            if prev_image:
                self.last_captured_image = prev_image
                self.display_image(prev_image)
                self.save_button.setEnabled(True)
                self.clear_button.setEnabled(True)
            return
        
        current_index = sorted_captures.index(self.last_captured_image)
        if current_index > 0:
            prev_image = sorted_captures[current_index - 1]
            self.last_captured_image = prev_image
            self.display_image(prev_image)
            self.save_button.setEnabled(True)
            self.clear_button.setEnabled(True)

    def show_next_image(self):
        """Show the next image (newer in time)"""
        if not self.last_captured_image:
            # If no image loaded, try to load the oldest one
            sorted_captures = self.get_sorted_captures()
            if sorted_captures:
                self.last_captured_image = sorted_captures[0]
                self.display_image(self.last_captured_image)
                self.save_button.setEnabled(True)
                self.clear_button.setEnabled(True)
            return
        
        sorted_captures = self.get_sorted_captures()
        if not sorted_captures:
            return
        
        # If current image was deleted/modified, find the closest one by timestamp
        if self.last_captured_image not in sorted_captures:
            current_mtime = os.path.getmtime(self.last_captured_image) if os.path.exists(self.last_captured_image) else float('inf')
            # Find the closest image that's newer
            next_image = None
            for img in reversed(sorted_captures):
                img_mtime = os.path.getmtime(img)
                if img_mtime > current_mtime:
                    next_image = img
                else:
                    break
            if next_image:
                self.last_captured_image = next_image
                self.display_image(next_image)
                self.save_button.setEnabled(True)
                self.clear_button.setEnabled(True)
            return
        
        current_index = sorted_captures.index(self.last_captured_image)
        if current_index < len(sorted_captures) - 1:
            next_image = sorted_captures[current_index + 1]
            self.last_captured_image = next_image
            self.display_image(next_image)
            self.save_button.setEnabled(True)
            self.clear_button.setEnabled(True)

    def clear_image(self):
        """Clear the displayed image"""
        self.image_display.clear()
        self.image_display.setText("No image captured yet")
        self.last_captured_image = None
        self.original_pixmap = None  # Clear stored pixmap
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        # Update navigation - will enable buttons if captures exist
        self.update_navigation_buttons()
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
            self.options.trace = True  # Always keep trace mode enabled
            self.grabber.options = self.options
            self.log("⚙️ Settings updated")

    def open_captures_folder(self):
        """Open the captures folder in file explorer"""
        import subprocess
        import platform
        
        capture_dir = self.get_capture_directory()
        
        try:
            if platform.system() == 'Windows':
                os.startfile(capture_dir)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', capture_dir])
            else:  # Linux
                subprocess.Popen(['xdg-open', capture_dir])
            
            self.log(f"Opened captures folder: {capture_dir}")
        except Exception as e:
            self.log(f"❌ Failed to open captures folder: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to open captures folder:\n{str(e)}")


