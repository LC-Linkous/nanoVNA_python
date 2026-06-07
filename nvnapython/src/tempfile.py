from nvnapython import nanoVNA
import nvnapython, nvnapython.core
print("package file:", nvnapython.__file__)
print("core file:", nvnapython.core.__file__)
n = nanoVNA()
print("has get_device_model:", hasattr(n, "get_device_model"))
print("maxPoints:", n.maxPoints)
n.set_verbose(True)
found, connected = n.autoconnect()
print("found:", found, "connected:", connected)