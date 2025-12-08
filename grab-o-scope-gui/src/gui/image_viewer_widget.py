from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap
import os


class ImageViewerWidget(QWidget):
    """Custom widget for displaying and navigating images with overlay support"""
    
    # Signals
    image_changed = pyqtSignal(str)  # Emitted when image changes (filepath)
    navigation_requested = pyqtSignal(str)  # 'prev' or 'next'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.current_image_path = None
        self.loading_dot_count = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._animate_loading)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
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
        
        layout.addLayout(header_layout)
        
        # Image display with navigation buttons
        image_nav_layout = QHBoxLayout()
        
        # Previous button
        self.prev_button = self._create_nav_button("◀", "Previous image (older)")
        self.prev_button.clicked.connect(lambda: self.navigation_requested.emit('prev'))
        image_nav_layout.addWidget(self.prev_button)
        
        # Image display
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.image_display.setMinimumHeight(300)
        self.image_display.setText("No image captured yet")
        self.image_display.setScaledContents(False)
        image_nav_layout.addWidget(self.image_display, stretch=1)
        
        # Loading overlay
        self.loading_overlay = QLabel(self.image_display)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            color: white;
            font-size: 24pt;
            font-weight: bold;
        """)
        self.loading_overlay.setText("⏳ Capturing")
        self.loading_overlay.hide()
        
        # Filename overlay (bottom left)
        self.filename_overlay = QLabel(self.image_display)
        self.filename_overlay.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.filename_overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 100);
            color: white;
            font-size: 10pt;
            padding: 4px 8px;
            border-radius: 3px;
        """)
        self.filename_overlay.hide()
        
        # Next button
        self.next_button = self._create_nav_button("▶", "Next image (newer)")
        self.next_button.clicked.connect(lambda: self.navigation_requested.emit('next'))
        image_nav_layout.addWidget(self.next_button)
        
        layout.addLayout(image_nav_layout)
        self.setLayout(layout)
    
    def _create_nav_button(self, text, tooltip):
        """Create a navigation button with consistent styling"""
        button = QPushButton(text)
        button.setMaximumWidth(50)
        button.setSizePolicy(button.sizePolicy().horizontalPolicy(), 
                            button.sizePolicy().Expanding)
        button.setStyleSheet("""
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
        button.setToolTip(tooltip)
        button.setEnabled(False)
        return button
    
    def display_image(self, image_path):
        """Display an image from the given path"""
        if not os.path.exists(image_path):
            return False
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return False
        
        self.original_pixmap = pixmap
        self.current_image_path = image_path
        self.scale_and_display_image()
        
        # Update filename overlay
        filename = os.path.basename(image_path)
        self.filename_overlay.setText(filename)
        self.filename_overlay.show()
        
        # Delay positioning to ensure layout is complete
        QTimer.singleShot(0, self._position_filename_overlay)
        
        self.image_changed.emit(image_path)
        return True
    
    def _position_filename_overlay(self):
        """Position and raise the filename overlay (called after layout is complete)"""
        self.update_filename_overlay_position()
        self.filename_overlay.raise_()
    
    def scale_and_display_image(self):
        """Scale the stored pixmap to fit the current display size"""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return
        
        available_width = self.image_display.width() - 10
        available_height = self.image_display.height() - 10
        
        scaled_pixmap = self.original_pixmap.scaled(
            available_width,
            available_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_display.setPixmap(scaled_pixmap)
    
    def clear_image(self):
        """Clear the displayed image"""
        self.image_display.clear()
        self.image_display.setText("No image captured yet")
        self.current_image_path = None
        self.original_pixmap = None
        self.filename_overlay.hide()
    
    def show_loading(self):
        """Show loading overlay with animated dots"""
        self.loading_dot_count = 0
        self.loading_overlay.setText("Capturing")
        self.loading_overlay.setGeometry(0, 0, self.image_display.width(), self.image_display.height())
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        self.loading_timer.start(300)  # Loading dots delay
    
    def hide_loading(self):
        """Hide loading overlay and stop animation"""
        self.loading_timer.stop()
        self.loading_overlay.hide()
    
    def _animate_loading(self):
        """Animate the loading dots from 0 to 3"""
        self.loading_dot_count = (self.loading_dot_count + 1) % 4
        dots = "." * self.loading_dot_count
        self.loading_overlay.setText(f"Capturing{dots}")
    
    def set_navigation_state(self, prev_enabled, next_enabled):
        """Set the enabled state of navigation buttons"""
        self.prev_button.setEnabled(prev_enabled)
        self.next_button.setEnabled(next_enabled)
    
    def set_nav_info(self, text):
        """Set the navigation info label text"""
        self.nav_info_label.setText(text)
    
    def update_filename_overlay_position(self):
        """Update the position of the filename overlay at bottom left"""
        if self.filename_overlay.isVisible():
            self.filename_overlay.adjustSize()
            x = 10  # 10px from left edge
            y = self.image_display.height() - self.filename_overlay.height() - 10  # 10px from bottom
            self.filename_overlay.move(x, y)
    
    def get_image_display_widget(self):
        """Get the QLabel widget for context menu attachment"""
        return self.image_display
    
    def resizeEvent(self, event):
        """Handle resize to rescale image and overlay"""
        super().resizeEvent(event)
        if self.original_pixmap is not None:
            self.scale_and_display_image()
        if self.loading_overlay.isVisible():
            self.loading_overlay.setGeometry(0, 0, self.image_display.width(), self.image_display.height())
        if self.filename_overlay.isVisible():
            self.update_filename_overlay_position()
