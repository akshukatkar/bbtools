import sys
def check_diff(file1,file2):
    check = {}
    for file in [file1,file2]:
        with open(file,'r') as f:
            check[file] = []
            for line in f:
                check[file].append(line)
    diff = set(check[file1]) - set(check[file2])
    for line in diff:
        print(line.rstrip())
check_diff(sys.argv[2],sys.argv[3])
