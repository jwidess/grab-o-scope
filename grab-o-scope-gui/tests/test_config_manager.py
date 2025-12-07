import unittest
from src.core.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()

    def test_load_config(self):
        self.config_manager.load_config('test_config.json')
        self.assertEqual(self.config_manager.settings['oscilloscope_address'], 'TCPIP0::127.0.0.1::INSTR')

    def test_save_config(self):
        self.config_manager.settings['oscilloscope_address'] = 'TCPIP0::192.168.1.100::INSTR'
        self.config_manager.save_config('test_config.json')
        self.config_manager.load_config('test_config.json')
        self.assertEqual(self.config_manager.settings['oscilloscope_address'], 'TCPIP0::192.168.1.100::INSTR')

    def test_default_settings(self):
        self.assertEqual(self.config_manager.settings['oscilloscope_address'], 'TCPIP0::127.0.0.1::INSTR')
        self.assertEqual(self.config_manager.settings['image_format'], 'png')

if __name__ == '__main__':
    unittest.main()