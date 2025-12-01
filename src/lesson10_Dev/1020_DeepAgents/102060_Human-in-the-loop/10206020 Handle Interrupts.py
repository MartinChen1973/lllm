import signal
import sys
from typing import Optional

class InterruptHandler:
    def __init__(self):
        self._interrupted = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print(f"\nReceived interrupt signal {signum}, cleaning up...")
        self._interrupted = True

    @property
    def interrupted(self) -> bool:
        return self._interrupted

def main_loop(handler: Optional[InterruptHandler] = None):
    """Example main loop with interrupt handling"""
    if handler is None:
        handler = InterruptHandler()
    
    try:
        while not handler.interrupted:
            # Your main processing logic here
            print("Working... Press Ctrl+C to interrupt")
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        if not handler.interrupted:
            print("\nReceived keyboard interrupt, cleaning up...")
            handler._handle_signal(signal.SIGINT, None)
    
    print("Cleanup complete, exiting gracefully")

if __name__ == "__main__":
    print("Starting with interrupt handling")
    handler = InterruptHandler()
    main_loop(handler)