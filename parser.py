#!/usr/bin/env python3
import os
import re
import sys
import argparse
import logging
import traceback
from pathlib import Path

'''
text_elements is a tuple of (title, abstract, body)
'''
def write_xml(fp, text_elements):
    with open(fp, "w") as out:
        out.write("<title>\n")
        out.write(text_elements[0])
        out.write("\n</title>\n")

        out.write("<abstract>\n")
        out.write(text_elements[1])
        out.write("\n</abstract>\n")

        out.write("<body>\n")
        out.write(text_elements[2])
        out.write("\n</body>\n")


def remove_hex(string):
    hex_regex = re.compile("&#x.*;")
    
    # sub in quotation marks
    string = re.sub("&#x201C;", '"', string)
    string = re.sub("&#x201D;", '"', string)

    # sub in spaces for the non-breaking space code
    string = re.sub("&#xA0;", " ", string)

    # remove all other hex unicode
    string = hex_regex.sub("", string)

    return string

# Removes XML tags from a string
def remove_tags(string):
    tag_regex = re.compile("<[^>]+>")

    return tag_regex.sub("", string)

def remove_empty_lines(string):
    string = string.split("\n")
    string = [line for line in string if re.search("\S", line)]
    
    return "\n".join(string)


'''
abstract should be a string, can contain tags and hexadecimal unicode
returns a string without HTML tags and hexadecimal unicode
'''
def parse_abstract(abstract):
    # remove title
    abstract = re.sub("\s*<title>.*</title>", "", abstract)
    
    # remove tags
    abstract = remove_tags(abstract)

    # remove hexadecimal unicode
    abstract = remove_hex(abstract)

    abstract = remove_empty_lines(abstract)

    return abstract

def parse_body(body):
    # remove titles
    body = re.sub("\s*<title>.*</title>", "", body)

    # remove figure labels
    body = re.sub("\s*<label>.*</label>", "", body)
    
    # remove tags
    body = remove_tags(body)

    # remove hexadecimal unicode
    body = remove_hex(body)

    body = remove_empty_lines(body)

    return body

def parse_xml(fp, logger):
    title = ""
    clean_abstract = ""
    clean_body = ""

    title_group_start = re.compile("^\s*<title-group>\s*$")
    title_group_stop = re.compile("^\s*</title-group>\s*$")
    title_regex = re.compile("\s*<article-title>(.*)</article-title>")

    abstract_start = re.compile("\s*<abstract>")
    abstract_stop = re.compile("\s*</abstract>")

    body_start = re.compile("\s*<body>")
    body_stop = re.compile("\s*</body>")

    abstract = []
    body = []

    try:
        with open(fp, "r") as handle:
            line = handle.readline()
            logger.debug("starting line loop")
            while line:
                
                if title_group_start.search(line):
                    logger.debug("found title group start tag")
                    while not title_group_stop.search(line):
                        if title_regex.search(line):
                            title = title_regex.search(line).group(1)
                        line = handle.readline()
                
                if abstract_start.search(line):
                    logger.debug("found abstract start tag")
                    while not abstract_stop.search(line):
                        abstract.append(line)
                        line = handle.readline()

                if body_start.search(line):
                    logger.debug("found body start tag")
                    while not body_stop.search(line):
                        body.append(line)
                        line = handle.readline()

                line = handle.readline()
            logger.debug("end line loop")
        clean_abstract = parse_abstract("".join(abstract))
        clean_body = parse_body("".join(body))

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(repr(e))
        logger.critical(trace)

    return (title, clean_abstract, clean_body)


def get_file_list(directory):
    absolute_path = Path(directory).resolve()
    files = os.listdir(directory)
    
    return [os.path.join(absolute_path, f) for f in files]

def get_logger(debug=False, quiet=False):
    level = logging.INFO
    if debug:
        level = logging.DEBUG

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.FileHandler("pmc-parser.log")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if not quiet:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Directory containing PMC XML files",
                        required=True)
    parser.add_argument("-o", "--output", help="Directory to write output XML files to",
                        required=True)
    parser.add_argument("-q", "--quiet", help="Suppress printing of log messages to STDOUT. " \
                        "Warning: exceptions will not be printed to console", 
                        action="store_true", default=False)
    parser.add_argument("-d", "--debug", help="Set log level to DEBUG", action="store_true", 
                        default=False)

    args = parser.parse_args()

    logger = get_logger(args.debug, args.quiet)

    logger.info("Starting parser, input dir: {input}, output dir: {output}")
    logger.debug("Getting file list")
    input_files = get_file_list(args.input)

    logger.debug("Starting parse loop")
    for input_file in input_files:
        # clean_text is a tuple (title, abs, body)
        clean_text = parse_xml(input_file, logger)
        pmc_id = input_file.split("/")[-1].split(".")[0]
        write_xml(f"{args.output}/{pmc_id}.xml", clean_text)
        
