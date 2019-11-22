import glob
import os

from lib import proxy

if not os.path.exists("CA/certs"):
    raise Exception("The CA has not been initialized.")

exts = glob.glob("CA/exts/*")
for ext in exts:
    os.remove(ext)

p = proxy.Proxy(port=8443)
p.run()
