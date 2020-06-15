#!/bin/bash
#
# Retrieve files from NCBI FTP server

mkdir -p pmc_xmls

PREFIX="ftp://ftp.ncbi.nlm.nih.gov/pub/pmc"

elapsed="0"

while read pmc_id; do
	# ensure there is no extraneous whitespace or newlines
	pmc_id=$(echo -n $pmc_id | sed -E 's#(\S+)\n#\1#')
	
	request_url="$PREFIX/$pmc_id"
	
	output_path=$(echo -n $pmc_id | sed -E 's#oa_package/\w\w/\w\w/(\S+)#pmc_xmls/\1#')
	
	# Avoid making redundant requests
	if !([ -e $output_path ])
	then
		# track request time
		req_start=$(date +%s.%N)
		curl -o $output_path $request_url 2> curl.err
		elapsed=$(date +%s.%N --date="$req_start seconds ago")
	fi

	# avoid making more than 10 requests per second
	if (( $(echo "$elapsed<0.1" | bc -l) )); then
		wait_time=$(echo "0.1-$elapsed" | bc)
		sleep $wait_time
	fi
done < tester
