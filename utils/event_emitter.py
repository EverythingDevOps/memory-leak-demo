"""
Event emitter system
✅ FIXED: Listeners are properly removed after use; once() support added
"""

from collections import defaultdict
from threading import Lock

class EventEmitter:
    """
    Simple event emitter

    ✅ FIXED:
    - on() registers a persistent listener (use sparingly; call off() when done)
    - once() registers a one-shot listener that auto-removes itself after firing
    - off() and remove_all_listeners() are now actively used for cleanup
    """
    
    def __init__(self):
        self.listeners = defaultdict(list)   # persistent listeners
        self._once_listeners = defaultdict(list)  # one-shot listeners
        self.lock = Lock()
    
    def on(self, event_name, callback):
        """
        Register a persistent event listener.

        Callers are responsible for calling off() when the listener is no
        longer needed to prevent accumulation.
        """
        with self.lock:
            self.listeners[event_name].append(callback)

    def once(self, event_name, callback):
        """
        Register a one-shot event listener.

        ✅ FIX: The listener is automatically removed after it fires once,
        preventing listener accumulation when used per-job.
        """
        with self.lock:
            self._once_listeners[event_name].append(callback)
    
    def emit(self, event_name, *args, **kwargs):
        """
        Emit an event to all registered listeners.

        ✅ FIX: One-shot listeners (registered via once()) are drained and
        cleared before invocation so they cannot accumulate.
        """
        with self.lock:
            persistent = list(self.listeners.get(event_name, []))
            # ✅ FIX: Drain and clear one-shot listeners atomically
            one_shot = list(self._once_listeners.pop(event_name, []))

        for callback in persistent + one_shot:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"❌ Error in event listener: {e}")

    def listener_count(self, event_name):
        """Get the number of listeners for an event (persistent + one-shot)"""
        with self.lock:
            return (len(self.listeners.get(event_name, [])) +
                    len(self._once_listeners.get(event_name, [])))

    def off(self, event_name, callback):
        """Remove a persistent event listener."""
        with self.lock:
            if event_name in self.listeners:
                try:
                    self.listeners[event_name].remove(callback)
                except ValueError:
                    pass  # Callback not found

    def remove_all_listeners(self, event_name=None):
        """Remove all listeners (both persistent and one-shot) for an event or all events."""
        with self.lock:
            if event_name:
                self.listeners[event_name].clear()
                self._once_listeners.pop(event_name, None)
            else:
                self.listeners.clear()
                self._once_listeners.clear()
