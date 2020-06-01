#!/bin/bash
#
# Call NCBI API and save resulting XMLs

mkdir -p pmc_xmls

export PREFIX="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id="
export SUFFIX="&rettype=xml&retmode=text"

# ensure no whitespace or newlines in key
NCBI_API_KEY=$(cat ncbi.key | sed -E 's#(\S+)\n#\1#')

while read pmc_id; do
	# ensure there is no extraneous whitespace or newlines
	pmc_id=$(echo -n $pmc_id | sed -E 's#(\S+)\n#\1#')
	
	request_url="$PREFIX$pmc_id&api_key=$NCBI_API_KEY$SUFFIX"
	
	output_path=$(echo -n $pmc_id | sed -E 's#(\S+)#pmc_xmls/\1.xml#')

	# TODO: need to check if file exists if doing potentially 
	# redundant runs

	# track request time
	req_start=$(date +%s.%N)
	wget -o pull.errs -nv -O $output_path $request_url
	elapsed=$(date +%s.%N --date="$req_start seconds ago")

	# avoid making more than 10 requests per second
	if (( $(echo "$elapsed<0.1" | bc -l) )); then
		wait_time=$(echo "0.1-$elapsed" | bc)
		sleep $wait_time
	fi
done < pmc_ids
