from nvnapython import nanoVNA
import serial.tools.list_ports

for p in serial.tools.list_ports.comports():
    print(p.device, hex(p.vid) if p.vid else None, hex(p.pid) if p.pid else None)

n = nanoVNA()
n.set_verbose(True)
found, connected = n.autoconnect()
print("found:", found, "connected:", connected)

n.disconnect()