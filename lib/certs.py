import os
import subprocess

DCOH_C = os.environ.get("DCOH_C", "JP")
DCOH_ST = os.environ.get("DCOH_C", "Tokyo")
DCOH_L = os.environ.get("DCOH_L", "Minato-ku")
DCOH_O = os.environ.get("DCOH_O", "dcoh")
DCOH_OU = os.environ.get("DCOH_OU", "dcoh")


def create_cert(domain):
    cmd = f"echo subjectAltName = DNS:{domain} > CA/exts/{domain}.ext"
    subprocess.run(cmd, shell=True, check=True)
    if (os.path.exists(f"CA/certs/{domain}.crt") and
            os.path.getsize(f"CA/certs/{domain}.crt") != 0):
        return
    elif (os.path.exists(f"CA/certs/{domain}.crt") and
            os.path.getsize(f"CA/certs/{domain}.crt") == 0):
        os.remove(f"CA/certs/{domain}.crt")
        number = None
        f = open("CA/demoCA/index.txt", "r")
        for line in f:
            if line.startswith("V"):
                if f"CN={domain}" in line:
                    number = line.split("\t")[3]
                    break
        csr_cmd = (f"cd CA && openssl ca -revoke "
                   f"demoCA/newcerts/{number}.pem > /dev/null 2>&1")
        if number:
            try:
                subprocess.run(csr_cmd, shell=True, check=True)
            except Exception:
                pass
    err_count = 0
    csr_cmd = (f"openssl req -new -key CA/demoCA/private/cakey.pem "
               f"-out CA/csreq/{domain}.csr -subj \"/C={DCOH_C}/"
               f"ST={DCOH_ST}/L={DCOH_L}/O={DCOH_O}/OU={DCOH_OU}"
               f"/CN={domain}\" > /dev/null 2>&1")
    crt_cmd = (f"cd CA && openssl ca -create_serial -days 3650 -keyfile "
               f"demoCA/private/cakey.pem -cert demoCA/cacert.pem "
               f"-in csreq/{domain}.csr -out certs/{domain}.crt -extfile "
               f"exts/{domain}.ext -batch > /dev/null 2>&1")
    for i in range(3):
        try:
            subprocess.run(csr_cmd, shell=True, check=True)
            subprocess.run(crt_cmd, shell=True, check=True)
            break
        except Exception as e:
            err_count += 1
            err = e
    if err_count == 3:
        raise err


def refresh_cert(domain):
    os.remove(f"CA/certs/{domain}.crt")
    number = None
    f = open("CA/demoCA/index.txt", "r")
    for line in f:
        if line.startswith("V"):
            if f"CN={domain}" in line:
                number = line.split("\t")[3]
                break
    csr_cmd = (f"cd CA && openssl ca -revoke "
               f"demoCA/newcerts/{number}.pem > /dev/null 2>&1")
    if number:
        try:
            subprocess.run(csr_cmd, shell=True, check=True)
        except Exception:
            pass
