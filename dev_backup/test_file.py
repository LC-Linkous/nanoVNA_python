from nvnapython import nanoVNA
nvna = nanoVNA()
nvna.set_verbose(True)
found, connected = nvna.autoconnect()
print("found:", found, "connected:", connected)

if connected:
    print("INFO   ->", repr(nvna.info()))
    print("VERSION->", repr(nvna.version()))
    print("SN     ->", repr(nvna.SN()))
    nvna.pause()
    print("SCAN   ->", repr(nvna.get_scan_s11(int(1e9), int(2e9), 51)))
    print("FREQS  ->", repr(nvna.frequencies()))
    nvna.resume()
    nvna.disconnect()


nvna = nanoVNA()
nvna.set_verbose(True)
found, connected = nvna.autoconnect()
print("found:", found, "connected:", connected)

if connected:
    print("INFO   ->", repr(nvna.info()))
    nvna.pause()
    print("SCAN   ->", repr(nvna.get_scan_s11(int(1e9), int(2e9), 51)))
    nvna.resume()
    nvna.disconnect()