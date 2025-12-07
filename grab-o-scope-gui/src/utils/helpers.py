def validate_ip_address(ip):
    import re
    pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    return re.match(pattern, ip) is not None

def format_timestamp(timestamp):
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def show_message_box(title, message):
    from PyQt5.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.exec_()