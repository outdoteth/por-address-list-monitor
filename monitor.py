import requests
import pandas as pd
from io import StringIO
import json
import threading
import xmltodict
from datetime import datetime
import yaml
from clint.textui import progress

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def fetch_with_progress(url):
    print("Loading from " + url)
    res = requests.get(url, stream=True)
    if (res.headers.get("content-length") == None):
        return res.text

    total_length = int(res.headers.get('content-length'))
    chunks = b''
    for chunk in progress.bar(res.iter_content(chunk_size=4096), expected_size=(total_length/4096) + 1):
        chunks += chunk

    return chunks.decode("utf-8") 

def okx():
    print("\nFetching OKX addresses...")

    # this endpoint was found by inspecting the network requests made by the OKX website;
    # it's not actually part of their API
    root_url = "https://www.okx.com/v2/asset/audit/list"
    audit_file = requests.get(root_url).json()["data"][0]["download"]
    res_txt = fetch_with_progress(audit_file)

    addresses = pd.read_csv(StringIO(res_txt.split("\n\n")[1]))
    addresses_obj = {}

    for [coin, address] in addresses[["coin", "address"]].values:
        coin = coin.replace("ERC20", "ETH")
        coin = coin.replace("TRC20", "TRON")
        if (addresses_obj.get(coin) == None):
            addresses_obj[coin] = []
        addresses_obj[coin].append(address) 

    with open('./reserves/okx.json', 'w', encoding='utf-8') as f:
        json.dump(addresses_obj, f, indent=4)
        print("Wrote " + str(len(addresses)) + " OKX addresses to json file")

def bitmex():
    print("\nFetching BitMEX addresses...")

    def parse(file):
        new_file = {}
        new_file["timestamp"] = datetime.strptime(file["LastModified"], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
        new_file["name"] = file["Key"]
        return new_file

    # this endpoint was found by inspecting the network requests made by the BitMEX website, it's not actually part of their API
    # amazon s3 response only returns XML so it must be parsed first
    root_url = "https://s3-eu-west-1.amazonaws.com/public.bitmex.com/?prefix=data/porl/"
    files = xmltodict.parse(requests.get(root_url).text)["ListBucketResult"]["Contents"]
    files = [parse(x) for x in files if "reserves" in x["Key"]]
    files.sort(key=lambda x: x["timestamp"], reverse=True)

    audit_file = "https://s3-eu-west-1.amazonaws.com/public.bitmex.com/" + files[0]["name"]
    res_txt = fetch_with_progress(audit_file)

    addresses = yaml.safe_load(res_txt)["address"]
    addresses_obj = {
        "BTC": [x["addr"] for x in addresses],
    }

    with open('./reserves/bitmex.json', 'w', encoding='utf-8') as f:
        json.dump(addresses_obj, f, indent=4)
        print("Wrote " + str(len(addresses)) + " BitMEX addresses to json file")
    

UPDATE_INTERVAL = 30 * 60 # 30 minutes
def main():
    print("Starting address monitor...")
    okx()
    bitmex()

    set_interval(okx, UPDATE_INTERVAL)
    set_interval(bitmex, UPDATE_INTERVAL)

if __name__ == "__main__":
    main()