"""
Utilities.
"""

import hashlib
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


def as_hash(string: str) -> str:
    """
    Generate an MD5 hash for a given endpoint.

    This function takes a string representing an endpoint (such as a URL) and
    returns its MD5 hash. The hashing is performed using the MD5 algorithm, which
    produces a 128-bit hash value. This function is typically used for generating a
    consistent and unique identifier for each endpoint, especially useful in
    situations where you need to efficiently check if an endpoint has already been
    processed or stored.

    Parameters
    ----------
    string
        Any string that needs to be hashed.

    Returns
    -------
        The MD5 hash of the input string. The hash is returned as a hexadecimal
        string.

    Example
    -------
    >>> as_hash("http://example.com")
    '5ab439c7201d6e1e4f2e4f09a0038870'
    """
    return hashlib.md5(string.encode()).hexdigest()
