import sys
lines_seen = set() # holds lines already seen
outfile = open(sys.argv[2], "w")
skip_words= [".jpg" ,".gif", ".png" , ".jpeg" , ".woff" , ".css" , ".svg" , ".ttf" , ".woff2" ,".eot"]
for line in open(sys.argv[1], "r"):
        flag=0
        for word in skip_words:
                if word in line:
                    flag=1
        if flag==1:
            continue
        nline=line.split("?")[0].rstrip()
        if nline not in lines_seen: # not a duplicate
          outfile.write(line)
          lines_seen.add(nline)
outfile.close()
