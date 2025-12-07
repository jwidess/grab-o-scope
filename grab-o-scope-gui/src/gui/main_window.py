from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QFileDialog, QMessageBox, QTextEdit, QLabel,
                             QSplitter, QMenu, QAction, QShortcut, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QClipboard, QKeySequence, QIcon
from PyQt5.QtWidgets import QApplication
from core.grabber_wrapper import GrabberWrapper
from gui.settings_dialog import SettingsDialog
from gui.image_viewer_widget import ImageViewerWidget
from core.config_manager import ConfigManager
from utils.navigation_manager import NavigationManager
from argparse import Namespace
import os
import platform
import subprocess
import shutil
from datetime import datetime


class CaptureThread(QThread):
    """Thread for capturing oscilloscope screen without blocking GUI"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    output = pyqtSignal(str)
    
    def __init__(self, grabber):
        super().__init__()
        self.grabber = grabber
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
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'resources', 'icons', 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize configuration and options
        self.config = ConfigManager()
        config_data = self.config.load_config()
        self.options = Namespace(
            name=config_data.get('instrument_name'),
            filename=None,
            auto_view=False,
            verbose=True,
            trace=True
        )
        
        # Initialize components
        self.grabber = GrabberWrapper(self.options)
        self.capture_thread = None
        self.nav_manager = NavigationManager(self.get_capture_directory)

        # Build UI
        self.init_ui()
        self.create_menu_bar()
        self.setup_keyboard_shortcuts()
        self.setup_refresh_timer()
        
        self.log("Grab-O-Scope GUI initialized")
        self.log("Ready to capture from oscilloscope")

    def init_ui(self):
        """Initialize the user interface"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)
        
        # Image viewer
        self.image_viewer = ImageViewerWidget()
        self.image_viewer.navigation_requested.connect(self.handle_navigation)
        self.image_viewer.get_image_display_widget().setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_viewer.get_image_display_widget().customContextMenuRequested.connect(self.show_image_context_menu)
        splitter.addWidget(self.image_viewer)
        
        # Console output
        log_widget = self._create_log_widget()
        splitter.addWidget(log_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([450, 200])
        main_layout.addWidget(splitter)
        
        # Control buttons
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _create_log_widget(self):
        """Create the console log widget"""
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
        self.log_output.setMinimumHeight(150)
        self.log_output.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; "
            "font-family: Consolas, monospace; font-size: 9pt;"
        )
        log_layout.addWidget(self.log_output)
        log_widget.setLayout(log_layout)
        return log_widget

    def _create_button_layout(self):
        """Create the control button layout"""
        button_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = self._create_button(
            "Clear", "#d13438", "#a52a2e", "#8b2327",
            self.clear_image, stretch=1
        )
        self.clear_button.setEnabled(False)
        button_layout.addWidget(self.clear_button, stretch=1)
        
        # Capture button
        self.capture_button = self._create_button(
            "Capture Screen", "#0078d4", "#106ebe", "#005a9e",
            self.capture_screen, stretch=2
        )
        button_layout.addWidget(self.capture_button, stretch=2)
        
        # Save button
        self.save_button = self._create_button(
            "💾 Save As...", "#107c10", "#0e6b0e", "#0c5a0c",
            self.save_image_as, stretch=1
        )
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button, stretch=1)
        
        # Settings button
        self.settings_button = self._create_button(
            "⚙️ Settings", "#5c5c5c", "#707070", "#4a4a4a",
            self.open_settings, stretch=1
        )
        button_layout.addWidget(self.settings_button, stretch=1)
        
        return button_layout

    def _create_button(self, text, color, hover, pressed, callback, stretch=1):
        """Create a styled button"""
        button = QPushButton(text)
        button.setMinimumHeight(40)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {pressed}; }}
            QPushButton:disabled {{ background-color: #cccccc; }}
        """)
        button.clicked.connect(callback)
        return button

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for navigation"""
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(lambda: self.handle_navigation('prev'))
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(lambda: self.handle_navigation('next'))

    def setup_refresh_timer(self):
        """Setup timer to check for file changes"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_navigation_state)
        self.refresh_timer.start(1000) # Refresh every second
        # Initial update
        self.update_navigation_buttons()

    def refresh_navigation_state(self):
        """Periodically refresh navigation buttons"""
        if not (self.capture_thread and self.capture_thread.isRunning()):
            self.update_navigation_buttons()

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        file_menu.addAction(self._create_action('Open Image...', self.open_image_file))
        file_menu.addAction(self._create_action('Save As...', self.save_image_as))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action('Open Captures Folder', self.open_captures_folder))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action('Exit', self.close))
        
        # View menu
        view_menu = menubar.addMenu('View')
        view_menu.addAction(self._create_action('Clear Log', self.clear_log))

    def _create_action(self, text, callback):
        """Create a menu action"""
        action = QAction(text, self)
        action.triggered.connect(callback)
        return action

    # ==================== Logging ====================
    
    def log(self, message):
        """Add message to log output"""
        self.log_output.append(message)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def clear_log(self):
        """Clear the log output"""
        self.log_output.clear()

    # ==================== Capture Directory ====================
    
    def get_capture_directory(self):
        """Get or create the captures directory"""
        config_data = self.config.load_config()
        capture_dir = config_data.get('capture_directory', '')
        
        if not capture_dir:
            capture_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'captures'
            )
        
        os.makedirs(capture_dir, exist_ok=True)
        return capture_dir

    def generate_timestamped_filename(self):
        """Generate a filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_dir = self.get_capture_directory()
        return os.path.join(capture_dir, f"capture_{timestamp}.png")

    # ==================== Capture ====================
    
    def capture_screen(self):
        """Start capture in separate thread"""
        if self.capture_thread and self.capture_thread.isRunning():
            self.log("⚠️ Capture already in progress...")
            return
        
        self.options.filename = self.generate_timestamped_filename()
        self.grabber.options = self.options
        
        self.capture_button.setEnabled(False)
        self.capture_button.setText("⏳ Capturing...")
        self.image_viewer.show_loading()
        self.image_viewer.set_navigation_state(False, False)
        
        self.log("=" * 50)
        self.log("Starting capture...")
        
        self.capture_thread = CaptureThread(self.grabber)
        self.capture_thread.finished.connect(self.on_capture_finished)
        self.capture_thread.error.connect(self.on_capture_error)
        self.capture_thread.output.connect(self.log)
        self.capture_thread.start()

    def on_capture_finished(self, filename):
        """Handle successful capture"""
        self.capture_button.setEnabled(True)
        self.capture_button.setText("Capture Screen")
        self.image_viewer.hide_loading()
        
        self.log(f"Success! Screen captured and saved as: {filename}")
        
        if self.image_viewer.display_image(filename):
            self.nav_manager.current_image = filename
            self.save_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            # Re-enable navigation after delay
            QTimer.singleShot(500, self.update_navigation_buttons)
        else:
            self.log(f"⚠️ Failed to display captured image")

    def on_capture_error(self, error_msg):
        """Handle capture error"""
        self.capture_button.setEnabled(True)
        self.capture_button.setText("Capture Screen")
        self.image_viewer.hide_loading()
        self.update_navigation_buttons()
        
        self.log(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "Capture Error", f"Failed to capture screen:\n{error_msg}")

    # ==================== Navigation ====================
    
    def handle_navigation(self, direction):
        """Handle navigation button/key press"""
        if direction == 'prev':
            image_path = self.nav_manager.get_previous_image()
        else:
            image_path = self.nav_manager.get_next_image()
        
        if image_path and self.image_viewer.display_image(image_path):
            self.nav_manager.current_image = image_path
            self.save_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update navigation button states"""
        nav_state = self.nav_manager.get_navigation_state(
            self.image_viewer.current_image_path
        )
        
        self.image_viewer.set_navigation_state(
            nav_state['prev_enabled'],
            nav_state['next_enabled']
        )
        self.image_viewer.set_nav_info(nav_state['info_text'])

    # ==================== Image Management ====================
    
    def clear_image(self):
        """Clear the displayed image"""
        self.image_viewer.clear_image()
        self.nav_manager.current_image = None
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.update_navigation_buttons()
        self.log("Image cleared")

    def open_image_file(self):
        """Open and display an image file"""
        image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if image_path and self.image_viewer.display_image(image_path):
            self.nav_manager.current_image = image_path
            self.save_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.update_navigation_buttons()

    def save_image_as(self):
        """Save the current image to a new location"""
        if not self.image_viewer.current_image_path:
            QMessageBox.warning(self, "No Image", "No image to save. Capture an image first.")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As", "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)"
        )
        if save_path:
            try:
                shutil.copy(self.image_viewer.current_image_path, save_path)
                self.log(f"Image saved to: {save_path}")
                QMessageBox.information(self, "Success", f"Image saved to:\n{save_path}")
            except Exception as e:
                self.log(f"❌ Failed to save image: {str(e)}")
                QMessageBox.critical(self, "Save Error", f"Failed to save image:\n{str(e)}")

    def copy_to_clipboard(self):
        """Copy the current image to clipboard"""
        if not self.image_viewer.current_image_path:
            QMessageBox.warning(self, "No Image", "No image to copy. Capture an image first.")
            return
        
        try:
            pixmap = QPixmap(self.image_viewer.current_image_path)
            if pixmap.isNull():
                raise Exception("Failed to load image")
            
            QApplication.clipboard().setPixmap(pixmap)
            self.log("Image copied to clipboard")
        except Exception as e:
            self.log(f"❌ Failed to copy to clipboard: {str(e)}")
            QMessageBox.critical(self, "Copy Error", f"Failed to copy to clipboard:\n{str(e)}")
    
    def delete_current_image(self):
        """Delete the currently displayed image"""
        if not self.image_viewer.current_image_path:
            QMessageBox.warning(self, "No Image", "No image to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete this image?\n\n{os.path.basename(self.image_viewer.current_image_path)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                file_to_delete = self.image_viewer.current_image_path
                
                # Try to navigate to another image first
                captures = self.nav_manager.get_sorted_captures()
                if len(captures) > 1:
                    # Try to get the next image, or previous if this is the last
                    current_idx = captures.index(file_to_delete) if file_to_delete in captures else -1
                    if current_idx >= 0:
                        if current_idx < len(captures) - 1:
                            # Show next image
                            self.image_viewer.display_image(captures[current_idx + 1])
                        elif current_idx > 0:
                            # Show previous image
                            self.image_viewer.display_image(captures[current_idx - 1])
                
                # Delete the file
                os.remove(file_to_delete)
                self.log(f"Deleted: {os.path.basename(file_to_delete)}")
                
                # If we only had one image, clear the display
                if len(captures) <= 1:
                    self.image_viewer.clear_image()
                
                # Update navigation
                self.update_navigation_buttons()
                
            except Exception as e:
                self.log(f"❌ Failed to delete image: {str(e)}")
                QMessageBox.critical(self, "Delete Error", f"Failed to delete image:\n{str(e)}")
    
    def rename_current_image(self):
        """Rename the currently displayed image"""
        if not self.image_viewer.current_image_path:
            QMessageBox.warning(self, "No Image", "No image to rename.")
            return
        
        old_path = self.image_viewer.current_image_path
        old_filename = os.path.basename(old_path)
        old_name_without_ext = os.path.splitext(old_filename)[0]
        old_ext = os.path.splitext(old_filename)[1]
        
        # Ask for new name
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Image",
            "Enter new filename (without extension):",
            text=old_name_without_ext
        )
        
        if ok and new_name:
            new_name = new_name.rstrip() # Strip trailing spaces
            
            if new_name == old_name_without_ext:
                return  # Name unchanged, return
            
            # Add extension back
            new_filename = new_name + old_ext
            new_path = os.path.join(os.path.dirname(old_path), new_filename)
            
            # Check if file already exists
            if os.path.exists(new_path) and new_path != old_path:
                QMessageBox.warning(self, "File Exists", f"A file named '{new_filename}' already exists.")
                return
            
            try:
                os.rename(old_path, new_path)
                self.log(f"Renamed: {old_filename} → {new_filename}")
                
                # Update the display with the new path
                self.image_viewer.current_image_path = new_path
                # Update the filename overlay
                self.image_viewer.filename_overlay.setText(new_filename)
                self.update_navigation_buttons()
                
            except Exception as e:
                self.log(f"❌ Failed to rename image: {str(e)}")
                QMessageBox.critical(self, "Rename Error", f"Failed to rename image:\n{str(e)}")
    
    def show_image_context_menu(self, position):
        """Show context menu for image display"""
        if not self.image_viewer.current_image_path:
            return
        
        menu = QMenu(self)
        
        # Copy to clipboard
        copy_action = menu.addAction("Copy Image to Clipboard")
        copy_action.triggered.connect(self.copy_to_clipboard)
        
        menu.addSeparator()
        
        # Rename image
        rename_action = menu.addAction("Rename Image...")
        rename_action.triggered.connect(self.rename_current_image)
        
        # Delete image
        delete_action = menu.addAction("Delete Image...")
        delete_action.triggered.connect(self.delete_current_image)
        
        menu.exec_(self.image_viewer.get_image_display_widget().mapToGlobal(position))

    # ==================== Settings & Utilities ====================
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            config_data = self.config.load_config()
            self.options.name = config_data.get('instrument_name')
            self.options.trace = True
            self.grabber.options = self.options
            self.log("⚙️ Settings updated")

    def open_captures_folder(self):
        """Open the captures folder in file explorer"""
        capture_dir = self.get_capture_directory()
        
        try:
            if platform.system() == 'Windows':
                os.startfile(capture_dir)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', capture_dir])
            else:
                subprocess.Popen(['xdg-open', capture_dir])
            
            self.log(f"Opened captures folder: {capture_dir}")
        except Exception as e:
            self.log(f"❌ Failed to open captures folder: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to open captures folder:\n{str(e)}")
