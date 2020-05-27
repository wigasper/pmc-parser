import re

def write_xml():
    pass

def remove_hex():
    hex_regex = re.compile("&#x.*;")
    pass

# Removes XML tags from a string
def remove_tags(string):
    tag_regex = re.compile("<[^>]+>")

    return tag_regex.sub("", string)

def parse_abstract(abstract):
    pass

def parse_body(body):
    pass

def parse_xml(fp, logger):
    title = ""
    clean_abstract = ""
    clean_body = ""

    title_group_start = re.compile("^\s*<title-group>\s*$")
    title_group_stop = re.compile("^\s*</title-group>\s*$")
    title_regex = re.compile("\s*<article-title>(.*)</article-title>")

    abstract_start = re.compile("\s*<abstract>")
    abstract_stop = re.compile("\s*<\abstract>")

    body_start = re.compile("\s*<body>")
    body_stop = re.compile("\s*</body>")

    abstract = []
    body = []

    try:
        with open(fp, "r") as handle:   
            line = handle.readline()
            while line:
                if title_group_start.search(line):
                    while not title_group_stop.search(line):
                        if title_regex.search(line):
                            title = title_regex.search(line).group(1)
                        line = handle.readline()
                
                if abstract_start.search(line):
                    while not abstract_stop.search(line):
                        abstract.append(line)
                        line = handle.readline()

                if body_start.search(line):
                    while not body_stop.search(line):
                        body.append(line)
                        line = handle.readline()

                line = handle.readline()
        
        clean_abstract = parse_abstract("".join(abstract))
        clean_body = parse_body("".join(body))

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(repr(e))
        logger.critical(trace)

    return (title, clean_abstract, clean_body)

if __name__ == "__main__":
    pmc_ids = []
    with open("pmc_ids", "r") as handle:
        for line in handle:
            pmc_ids.append(line.strip("\n"))

    for pmc_id in pmc_ids:
        # parse
        pass
