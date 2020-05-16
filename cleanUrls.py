import sys
lines_seen = set() # holds lines already seen
skip_words= [".jpg" ,".gif", ".png" , ".jpeg" , ".woff" , ".css" , ".svg" , ".ttf" ,".pdf", ".woff2" ,".eot"]
for line in [x.rstrip() for x in sys.stdin]:
        flag=0
        for word in skip_words:
                if word in line:
                    flag=1
        if flag==1:
            continue
        nline=line.split("?")[0].rstrip()
        if nline not in lines_seen: # not a duplicate
          print(line)
          lines_seen.add(nline)
