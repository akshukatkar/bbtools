#!/bin/bash

########################################
# Recon tool, Most of things copied from
# nahamsec lazy recon
########################################

# Global variables 
domain=$1
subfolder=$(date +"%d%m%y")
dir=./$domain/$subfolder


# Some fancy colouring
red=`tput setaf 1`
green=`tput setaf 2`
yellow=`tput setaf 3`
reset=`tput sgr0`

main() 
{
	init
	findsubdomains
	#wayback
}

init()
{
	if [ -d "./$domain" ]
	then
		echo "This is a known target."
		mkdir $dir
		
	else
		mkdir ./$domain
		mkdir $dir
	fi
}

findsubdomains()
{
	echo "${green}Recon started on $domain ${reset}"
	echo "${green}Finding subdomains $domain ${reset}"
	echo "${green}Assetfinder on $domain ${reset}"
	#assetfinder $domain -subs-only > $dir/tempdomains
	echo "${green}Amass started on $domain ${reset}"
	amass enum -d $domain >> $dir/tempdomains
	echo "${green}Subfinder started on $domain ${reset}"
	subfinder -d $domain >> $dir/tempdomains
	echo "${green}Finddomain started on $domain ${reset}"
	findomain -q -t $domain >> $dir/tempdomains 
	awk '!a[$0]++' $dir/tempdomains >> $dir/domains
	echo "${green}Resolving subdomains of $domain ${reset}"
	cat $dir/domains  | filter-resolved >> $dir/res_domains
	rm $dir/tempdomains
	echo "${green}Probing domains started on $domain ${reset}"
	cat $dir/res_domains | httprobe -c 50 -t 3000 >> $dir/probed	
}

wayback()
{
	urldir=$dir/URLS
	mkdir $dir/URLS
	
	cat $dir/res_domains | waybackurls > $urldir/urls_temp
	python tmux.py $urldir/urls_temp $urldir/urls
	
	cat $urldir/urls | unfurl format %s://%d%p?%q > $urldir/urlhavingpara
	cat $urldir/urls | unfurl --unique keys > $urldir/getparams
	cat $urldir/urls | grep -P "\w+\.js(\?|$)" > $urldir/jsfiles
	cat $urldir/urls | grep -P "\w+\.php(\?|$)" > $urldir/phpfiles
	cat $urldir/urls | grep -P "\w+\.asp(\?|$)" > $urldir/aspfiles
	cat $urldir/urls | grep -P "\w+\.cgi(\?|$)" > $urldir/cgifiles
	cat $urldir/urls | grep -P "\w+\.jsp(\?|$)" > $urldir/jspfiles

	#./anti-burl.sh $urldir/jsfiles > $urldir/jsfiles_200
	#./anti-burl.sh $urldir/phpfiles > $urldir/phpfiles_200
	#./anti-burl.sh $urldir/aspfiles > $urldir/aspfiles_200
	#./anti-burl.sh $urldir/cgifiles > $urldir/cgifiles_200
	#./anti-burl.sh $urldir/jspfiles > $urldir/jspfiles_200
	
}

main
