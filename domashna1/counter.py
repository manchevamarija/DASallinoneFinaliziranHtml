import logging

class CountingHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.line_count = 0

    def emit(self, record):
        self.line_count += 1
        super().emit(record)
