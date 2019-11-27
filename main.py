import glob
import multiprocessing
import os

from lib import http_proxy, https_proxy

if not os.path.exists("CA/certs"):
    raise Exception("The CA has not been initialized.")

exts = glob.glob("CA/exts/*")
for ext in exts:
    os.remove(ext)

http_px = http_proxy.Proxy(port=8080)
http_p = multiprocessing.Process(target=http_px.run)
http_p.daemon = True
http_p.start()

https_px = https_proxy.Proxy(port=8443)
https_p = multiprocessing.Process(target=https_px.run)
https_p.daemon = True
https_p.start()

http_p.join()
https_p.join()
