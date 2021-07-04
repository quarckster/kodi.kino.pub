import threading

from resources.lib import proxy

threading.Thread(target=proxy.main).start()
