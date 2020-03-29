import concurrent.futures
import requests
import time
from bs4 import BeautifulSoup
import re
import sys
import jsbeautifier
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

out = []
CONNECTIONS = 100
TIMEOUT = 5
context_delimiter_str = "\n"

#tlds = open('urls.txt').read().splitlines()
urls = [x.rstrip() for x in sys.stdin]

# headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
                # 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                # 'Accept-Language' : 'en-US,en;q=0.5',
                # 'Accept-Encoding' : 'gzip, deflate',
                # 'Connection' : 'keep-alive',
                # 'Upgrade-Insecure-Requests' : '1'}
            
regex_str = r"""
  (?:"|')                               # Start newline delimiter
  (
    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
    |
    ((?:/|\.\./|\./)                    # Start with /,../,./
    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    [^"'><,;|()]{1,})                   # Rest of the characters can't be
    |
    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    [a-zA-Z0-9_\-/]{1,}                 # Resource name
    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
    |
    ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
    [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
    |
    ([a-zA-Z0-9_\-]{1,}                 # filename
    \.(?:php|asp|aspx|jsp|json|
         action|html|js|txt|xml)        # . + extension
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
  )
  (?:"|')                               # End newline delimiter
"""

def parser_file(url ,content, regex_str, mode=1, more_regex=None, no_dup=1):
    global context_delimiter_str
    if mode == 1:
        # Beautify
        if len(content) > 1000000:
            content = content.replace(";",";\r\n").replace(",",",\r\n")
        else:
            content = jsbeautifier.beautify(content)
    regex = re.compile(regex_str, re.VERBOSE)
    #print([m for m in re.finditer(regex, content)])
    if mode == 1:
        all_matches = [(m.group(1), m.start(0), m.end(0)) for m in re.finditer(regex, content)]
        items = getContext(all_matches, content, context_delimiter_str=context_delimiter_str)
    else:
        items = [{"link": m.group(1)} for m in re.finditer(regex, content)]

    if no_dup:
        # Remove duplication
        all_links = set()
        no_dup_items = []
        for item in items:
            if item["link"] not in all_links:
                all_links.add(item["link"])
                no_dup_items.append(item)
        items = no_dup_items
    # Match Regex
    filtered_items = []
    for item in items:
        # Remove other capture groups from regex results
        if more_regex:
            if re.search(more_regex, item["link"]):
                filtered_items.append(item)
        else:
            filtered_items.append(item)

    return filtered_items

def getContext(list_matches, content, include_delimiter=0, context_delimiter_str="\n"):
    '''
    Parse Input
    list_matches:       list of tuple (link, start_index, end_index)
    content:            content to search for the context
    include_delimiter   Set 1 to include delimiter in context
    '''
    items = []
    for m in list_matches:
        match_str = m[0]
        match_start = m[1]
        match_end = m[2]
        context_start_index = match_start
        context_end_index = match_end
        delimiter_len = len(context_delimiter_str)
        content_max_index = len(content) - 1

        while content[context_start_index] != context_delimiter_str and context_start_index > 0:
            context_start_index = context_start_index - 1

        while content[context_end_index] != context_delimiter_str and context_end_index < content_max_index:
            context_end_index = context_end_index + 1

        if include_delimiter:
            context = content[context_start_index: context_end_index]
        else:
            context = content[context_start_index + delimiter_len: context_end_index]

        item = {
            "link": match_str,
            "context": context
        }
        items.append(item)

    return items
    
def load_url(url, timeout,rgex):
    ans = requests.get(url, timeout=timeout , verify=False);
    if (ans.status_code < 400) : 
        result=parser_file(url,ans.text , rgex)
        if result is not None:
            print("*"*100)
            print(url)
            print("*"*100)
            for data in result:
                print(data["link"])
            print("\n")
    return url,ans.status_code

with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
	future_to_url = (executor.submit(load_url, url, TIMEOUT ,regex_str) for url in urls)
	time1 = time.time()
	for future in concurrent.futures.as_completed(future_to_url):
		try:
		    data = future.result()
		except Exception as exc:
		    data = str(type(exc))
		finally:
		    out.append(data);

