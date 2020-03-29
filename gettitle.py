import concurrent.futures
import requests
import time
from bs4 import BeautifulSoup
import re
import sys
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

out = []
CONNECTIONS = 100
TIMEOUT = 10
#tlds = open('urls.txt').read().splitlines()
urls = [x.rstrip() for x in sys.stdin]

def getTitle(url,html):
    res = BeautifulSoup(html,features="html.parser")
    title = res.find('title').text
    result = title + " ( " + url + " )"
    return result
    
def load_url(url, timeout):
    ans = requests.get(url, timeout=timeout , verify=False);
    if (ans.status_code < 400) : 
        result=getTitle(url,ans.text)
        if result is not None:
            print(result)
    return url,ans.status_code

with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
	future_to_url = (executor.submit(load_url, url, TIMEOUT) for url in urls)
	time1 = time.time()
	for future in concurrent.futures.as_completed(future_to_url):
		try:
		    data = future.result()
		except Exception as exc:
		    data = str(type(exc))
		finally:
		    out.append(data);
