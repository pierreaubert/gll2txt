from PySide6.QtCore import QThread, Signal


class ProcessThread(QThread):
    log_signal = Signal(int, str)
    progress_signal = Signal(int)
    process_complete_signal = Signal(bool)

    def __init__(self, process_manager):
        super().__init__()
        self.process_manager = process_manager

        # Disconnect any existing connections to prevent duplicate calls
        try:
            self.process_manager.log_signal.disconnect()
            self.process_manager.progress_signal.disconnect()
            self.process_manager.process_complete_signal.disconnect()
        except TypeError:
            # Ignore if no connections exist
            pass

        # Connect signals from process manager
        self.process_manager.log_signal.connect(self.log_signal.emit)
        self.process_manager.progress_signal.connect(self.progress_signal.emit)
        self.process_manager.process_complete_signal.connect(
            self.process_complete_signal.emit
        )

    def run(self):
        self.process_manager.process_gll_files()
