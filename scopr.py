import requests
import time
import json
import argparse
import csv
import html
from datetime import datetime
# used for parsing of the program HTML pages to grab React JSON data because there is no API :(
from bs4 import BeautifulSoup

bugcrowd_url = "https://bugcrowd.com"

def get_program_scope_data(code):
    scope_data = []
    targets = []
    target_groups_url = "%s/%s/target_groups.json" % (bugcrowd_url,code)
    resp = requests.get(target_groups_url, headers=headers)
    if(resp.status_code != 404):
        try:
            data = json.loads(resp.text)
        except:
            pass
        try:
            targets_url = data["groups"][0]["targets_url"]
            target_url = "%s/%s.json" % (bugcrowd_url,targets_url)
            target_resp = requests.get(target_url, headers=headers)
            data = json.loads(target_resp.text)
            targets = data["targets"]
        except:
            pass
        for target in targets:
            target_data = {"code":code ,"name":target["name"] , "uri":target["uri"], "category": target["category"]}
            scope_data.append(target_data)
    return scope_data 

def get_all_programs_scope_data():
    programs_url = "%s/programs.json" % (bugcrowd_url)
    resp = requests.get(programs_url, headers=headers)
    #print(resp.text)
    data = json.loads(resp.text)
    progtotal = data["meta"]["quickFilterCounts"]["all"]
    print("[+] Total Programs : %s " %(progtotal), flush=1, end='\n')
    offsets = 25
    progcount = 0
    all_targets_data = []

    for offset in range(progcount,progtotal,offsets):
        search_url = "%s?%s&offset[]=%d" % (programs_url,args.search_params, offset)
        resp = requests.get(search_url, headers=headers)
        try:
            data = json.loads(resp.text)
        except:
            continue
        progcount += len(data["programs"])
        print("[+] Collecting... (%d programs)                              "%(progcount), flush=1, end='\n')
        for program in data["programs"]:
            time.sleep(2)
            all_targets_data.append(get_program_scope_data(program["code"]))
    return [item for sublist in all_targets_data for item in sublist]

def write_csv_output(output,file):
    keys = output[0].keys()
    with open(file, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--session_cookie", help="Value of your _crowdcontrol_session cookie", required=True)
    parser.add_argument("-p", "--search_params", default="sort[]=promoted-desc&hidden[]=false", help="Search params for the program search", required=False)
    parser.add_argument("-o", "--output_file", help="Output file path", required=True)
    args = parser.parse_args()

    ### global vars
    headers = {
        "Cookie":"_crowdcontrol_session=%s" % args.session_cookie
    }

    ## Execution
    write_csv_output(get_all_programs_scope_data(),args.output_file)
    


