from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
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
        self.loading_overlay.setText("⏳ Capturing...")
        self.loading_overlay.hide()
        
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
        self.image_changed.emit(image_path)
        return True
    
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
    
    def show_loading(self):
        """Show loading overlay"""
        self.loading_overlay.setGeometry(0, 0, self.image_display.width(), self.image_display.height())
        self.loading_overlay.show()
        self.loading_overlay.raise_()
    
    def hide_loading(self):
        """Hide loading overlay"""
        self.loading_overlay.hide()
    
    def set_navigation_state(self, prev_enabled, next_enabled):
        """Set the enabled state of navigation buttons"""
        self.prev_button.setEnabled(prev_enabled)
        self.next_button.setEnabled(next_enabled)
    
    def set_nav_info(self, text):
        """Set the navigation info label text"""
        self.nav_info_label.setText(text)
    
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
