class ImageViewer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.window = None

    def show(self):
        from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt

        self.window = QMainWindow()
        self.window.setWindowTitle("Captured Image")

        layout = QVBoxLayout()
        label = QLabel()
        pixmap = QPixmap(self.image_path)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.window.setCentralWidget(central_widget)

        self.window.resize(pixmap.width(), pixmap.height())
        self.window.show()