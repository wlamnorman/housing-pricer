# pylint: disable=missing-module-docstring

import signal


class DelayedKeyboardInterrupt:
    """
    Context manager for ensuring that keyboard interrupts can be
    delayed until a block of code has been executed.
    """

    def __init__(self):
        self.signal_received = None
        self.old_handler = None

    def _handler(self, sig, frame):
        self.signal_received = (sig, frame)

    def __enter__(self):
        self.signal_received = None
        self.old_handler = signal.signal(signal.SIGINT, self._handler)

    def __exit__(self, _type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received is not None:
            if callable(self.old_handler):
                self.old_handler(*self.signal_received)
