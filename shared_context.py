import threading

class AppContext:
    """
    Un objeto simple para mantener el estado y los eventos compartidos
    a través de toda la aplicación.
    """
    def __init__(self):
        self.scheduler_event = threading.Event()

app_context = AppContext()