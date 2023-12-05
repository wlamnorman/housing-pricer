# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
import signal
import time

from housing_pricer.scraping._utils._data_manager_utils import DelayedKeyboardInterrupt


def long_running_operation():
    time.sleep(0.1)


def test_delayed_keyboard_interrupt():
    was_interrupted = False
    interrupt_delayed = False
    with DelayedKeyboardInterrupt():
        try:
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            was_interrupted = True
            long_running_operation()
            interrupt_delayed = True

    assert interrupt_delayed, "The interrupt was not delayed."
    assert was_interrupted, "The interrupt was not handled after the operation."


def test_delayed_keyboard_interrupt_restores_original_handler():
    # pylint: disable=comparison-with-callable
    # pylint: disable=unused-argument
    def dummy_handler(signum, frame):
        pass

    original_handler = signal.getsignal(signal.SIGINT)

    signal.signal(signal.SIGINT, dummy_handler)
    with DelayedKeyboardInterrupt():
        long_running_operation()
    current_handler = signal.getsignal(signal.SIGINT)

    signal.signal(signal.SIGINT, original_handler)
    assert current_handler == dummy_handler, "Signal handler was not restored to its original state"
