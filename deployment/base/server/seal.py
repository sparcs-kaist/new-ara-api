from pathlib import Path
from base64 import b64encode, b64decode
from os import system
import yaml

def encrypt(path: Path, certurl: str = None):
    if not certurl: certurl = input("cert url > ")

    target = path.resolve()
    b64target = (target.parent / f"b64-{target.stem}.yaml").resolve()
    sealedtarget = (target.parent / f"sealed-{target.stem}.yaml").resolve()
    

    if not target.exists(): raise FileNotFoundError("File not found.")
    if not target.is_file(): raise FileNotFoundError("It is not a file.")
    if not target.suffix == ".yaml": raise TypeError("File must be a YAML file.")

    thisyaml = yaml.safe_load(target.read_text())

    if not thisyaml["apiVersion"] == "v1": raise TypeError("File must be a Kubernetes YAML file.")
    for onedata in thisyaml["data"]:
        if not thisyaml["data"][onedata]:
            thisyaml["data"].pop(onedata)
        thisyaml["data"][onedata] = b64encode(str(thisyaml["data"][onedata]).encode()).decode()

    b64target.write_text(yaml.dump(thisyaml))
    if Path("kubeseal").exists():
        kubeseal = "./kubeseal"
    else:
        kubeseal = "kubeseal"
    rtn = system(f"{kubeseal} --cert {certurl} < {b64target} > {sealedtarget}")
    b64target.unlink()
    if rtn != 0:
        sealedtarget.unlink()
        raise RuntimeError("Failed to encrypt. Please check that kubeseal is installed.")
    
    print("Successfully encrypted.")
    return

def dec(path):
    path = Path(path).resolve()
    if not path.exists(): raise FileNotFoundError("File not found.")
    if not path.is_file(): raise FileNotFoundError("It is not a file.")
    if not path.suffix == ".yaml": raise TypeError("File must be a YAML file.")

    thisyaml = yaml.safe_load(path.read_text())
    
    if not thisyaml["apiVersion"] == "v1": raise TypeError("File must be a Kubernetes YAML file.")
    for onedata in thisyaml["data"]:
        thisyaml["data"][onedata] = b64decode(str(thisyaml["data"][onedata]).encode()).decode()
    
    path.write_text(yaml.dump(thisyaml))
    print(yaml.dump(thisyaml))

    return


if __name__ == "__main__":
    certurl = "https://s3.ap-northeast-2.amazonaws.com/wheel.sparcs.org/public/secret-seal.pem"
    encrypt(Path("secret.yaml"), certurl)

