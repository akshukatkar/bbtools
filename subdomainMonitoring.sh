#!/bin/bash
#in target.txt add domains line by line like google.com, dell.com etc
filename="/root/automation/target.txt"

# Check if the file exists
if [ ! -f "$filename" ]; then
    echo "Error: File '$filename' not found."
    exit 1
fi

# Loop through each line in the file and print it
while IFS= read -r line; do
        echo "$line" | haktrails subdomains > /root/automation/tmp
        cat /root/automation/tmp | anew /root/automation/$line.subdomains > /root/automation/$line.newsubs
        cat /root/automation/$line.newsubs | naabu --rate 1000000 > /root/automation/$line.newsubs.ports
        cat /root/automation/$line.newsubs | httpx > /root/automation/$line.newsubs.httpx
        cat /root/automation/$line.newsubs.ports | httpx > /root/automation/$line.newsubs.ports.httpx
        cat /root/automation/$line.newsubs.ports.httpx /root/automation/$line.newsubs.httpx |/usr/local/go/packages/bin/nuclei -etags ssl -es info,unknown >> /root/automation/$line.nuk
        notify -bulk -i /root/automation/$line.newsubs.ports
        notify -bulk -i /root/automation/$line.newsubs.httpx
        notify -bulk -i /root/automation/$line.nuk
done < "$filename"
