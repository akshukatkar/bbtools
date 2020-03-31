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
TIMEOUT = 5
#tlds = open('urls.txt').read().splitlines()
urls = [x.rstrip() for x in sys.stdin]

headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language' : 'en-US,en;q=0.5',
                'Accept-Encoding' : 'gzip, deflate',
                'Connection' : 'keep-alive',
                'Upgrade-Insecure-Requests' : '1'}

    
def load_url(url, timeout):
    ans = requests.get(url, timeout=timeout, verify=False);
    #print(type(ans.status_code))
    if (ans.status_code < 501): 
        print(url)
    return ans.status_code , url , len(ans.content)

with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
	future_to_url = (executor.submit(load_url, url, TIMEOUT) for url in urls)
	#time1 = time.time()
	for future in concurrent.futures.as_completed(future_to_url):
		try:
		    data = future.result()
		except Exception as exc:
		    data = str(type(exc))
		finally:
		    out.append(data);
