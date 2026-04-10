"""
Event emitter system
⚠️ THIS FILE CONTAINS INTENTIONAL MEMORY LEAKS
"""

from collections import defaultdict
from threading import Lock

class EventEmitter:
    """
    Simple event emitter
    
    ⚠️ MEMORY LEAK: Event listeners are registered but never removed!
    Each listener holds references to callbacks and their closures.
    """
    
    def __init__(self):
        # 🐛 MEMORY LEAK: Listeners accumulate here forever
        self.listeners = defaultdict(list)
        self.lock = Lock()
    
    def on(self, event_name, callback):
        """
        Register an event listener
        
        🐛 BUG: Listeners are added but NEVER removed!
        Should provide an 'off' method and clean up old listeners.
        """
        with self.lock:
            # Add listener to the list
            self.listeners[event_name].append(callback)
            
            # Show warning as listeners accumulate
            listener_count = len(self.listeners[event_name])
            if listener_count % 10 == 0:
                print(f"⚠️  WARNING: {listener_count} listeners for '{event_name}'")
    
    def emit(self, event_name, *args, **kwargs):
        """Emit an event to all registered listeners"""
        with self.lock:
            listeners = self.listeners.get(event_name, [])
        
        # Call all listeners (even the ones that should have been removed!)
        for callback in listeners:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"❌ Error in event listener: {e}")
    
    def listener_count(self, event_name):
        """Get the number of listeners for an event"""
        with self.lock:
            return len(self.listeners.get(event_name, []))
    
    def off(self, event_name, callback):
        """
        Remove an event listener
        
        🐛 BUG: This method exists but is NEVER called in the codebase!
        Listeners accumulate because nothing removes them.
        """
        with self.lock:
            if event_name in self.listeners:
                try:
                    self.listeners[event_name].remove(callback)
                except ValueError:
                    pass  # Callback not found
    
    def remove_all_listeners(self, event_name=None):
        """
        Remove all listeners for an event
        
        🐛 BUG: Also never called!
        """
        with self.lock:
            if event_name:
                self.listeners[event_name].clear()
            else:
                self.listeners.clear()
