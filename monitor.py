import requests
import pandas as pd
from io import StringIO
import json
import threading

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def okx():
    print("\nFetching OKX addresses...")
    audit_file = requests.get("https://www.okx.com/v2/asset/audit/list").json()["data"][0]["download"]
    addresses = pd.read_csv(StringIO(requests.get(audit_file).text.split("\n\n")[1]))
    addresses_obj = {}

    for [coin, address] in addresses[["coin", "address"]].values:
        if (addresses_obj.get(coin) == None):
            addresses_obj[coin] = []
        addresses_obj[coin].append(address) 

    with open('./reserves/okx.json', 'w', encoding='utf-8') as f:
        json.dump(addresses_obj, f, indent=4)
        print("Wrote " + str(len(addresses)) + " OKX addresses to json file")

UPDATE_INTERVAL = 15 * 60 # 15 minutes
def main():
    print("Starting address monitor...")
    okx()
    set_interval(okx, UPDATE_INTERVAL)

if __name__ == "__main__":
    main()