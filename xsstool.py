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

def getParameters(url,html):
    res = BeautifulSoup(html,features="html.parser")
    tags = res.findAll("input")
    param = []
    forms = re.findall(r'(?i)(?s)<form.*?</form.*?>', html)
    for form in forms:
        method = re.search(r'(?i)method=[\'"](.*?)[\'"]', form)
        inputs = re.findall(r'(?i)(?s)<input.*?>', html)
        #print(inputs)
        if inputs != None and method != None:
            for inp in inputs:
                inpName = re.search(r'(?i)name=[\'"](.*?)[\'"]', inp)
                if inpName:
                    param.append(inpName.group(1))
    if param:
        imurl = url.split('?')[0]
        keys = "?"+"=foo&".join(list(set(param)))+"=foo"
        return imurl+keys
    
def load_url(url, timeout):
    ans = requests.get(url, timeout=timeout, verify=False);
    if (ans.status_code < 400) : 
        result=getParameters(url,ans.text)
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
