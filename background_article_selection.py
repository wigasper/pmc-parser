#!/usr/bin/env python3
import sys
import random
import logging
from math import log

'''
Returns a map that maps a MeSH UID to the top level of each of 
its positions on the graph
'''
def get_term_top_ancestor_nodes():
    term_trees = {}
    with open("mesh_data.tab", "r") as handle:
        for line in handle:
            line = line.strip("\n").split("\t")
            positions = line[4].split(",")
            
            # only care about the top level
            positions = [l.split(".")[0] for l in positions]
            
            term_trees[line[0]] = positions
    
    return term_trees

'''
Returns a map that maps the PMCID of all articles in the OA 
subset to a PMID
'''
def get_oa_id_map():
    oa_articles = {}
    with open("oa_file_list.csv", "r") as handle:
        for line in handle:
            if not line.startswith("File"):
                line = line.split(",")
                oa_articles[line[2]] = line[4]
    
    return oa_articles

'''
Gets the MeSH terms for all articles in the PMC open access 
subset
'''
def get_pmcid_mesh_terms():
    article_terms = {}
    oa_articles = get_oa_id_map()

    pmid_to_pmcid = {val: key for key, val in oa_articles.items()}
    
    pmids = set([val for key, val in oa_articles.items()])

    with open("pm_doc_term_counts.csv", "r") as handle:
        for line in handle:
            line = line.strip("\n").split(",")
            if line[0] in pmids:
                # should only use articles that have been indexed
                if line[1]:
                    article_terms[pmid_to_pmcid[line[0]]] = line[1:]

    return article_terms

'''
Calculates Shannon index for an article set from the number of 
occurrences of each top level parent node
'''
def shannon(node_counts):
    sum_total = sum(node_counts.values())
    props = [val / sum_total for key, val in node_counts.items() if val != 0]

    if len(props) > 0:
        # init
        product = props[0] ** props[0]

        for prop in props[1:]:
            product = product * (prop ** prop)
    
    if product == 0:
        raise ValueError("product is 0, something is very wrong")

    return log(1 / product)

    
    pass

'''
Get a logger
'''
def initialize_logger(debug=False, quiet=False):
    level = logging.INFO
    if debug:
        level = logging.DEBUG

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.FileHandler("background_article_selection.log")
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
    logger = initialize_logger()
    logger.info("New run")

    term_trees = get_term_top_ancestor_nodes()
    pmc_doc_terms = get_pmcid_mesh_terms()

    # parent nodes are the parent nodes on the MeSH graph
    parent_nodes = [node for key, node_list in term_trees.items() for node in node_list]
    parent_nodes = list(dict.fromkeys(parent_nodes))
    parent_node_counts = {node: 0 for node in parent_nodes}
    
    # all PMCIDs in the OA subset
    pmc_ids = list(pmc_doc_terms.keys())

    # shuffle the list
    random.seed(42)
    random.shuffle(pmc_ids)

    # init
    current_shannon = 0
    selected_articles = []
    logger_update_interval = 2500

    # start adding to selected_articles
    for index, pmc_id in enumerate(pmc_ids):
        new_counts = {key: val for key, val in parent_node_counts.items()}
        for term in pmc_doc_terms[pmc_id]:
            for node in term_trees[term]:
                new_counts[node] += 1

        next_shannon = shannon(new_counts)
        
        if (next_shannon > current_shannon) or next_shannon > shannon_floor:
            current_shannon = next_shannon
            selected_articles.append(pmc_id)

            for term in pmc_doc_terms[pmc_id]:
                for node in term_trees[term]:
                    parent_node_counts[node] += 1
        
        # Update every update_interval
        if index % logger_update_interval == 0:
            logger.info(f"Current shannon: {current_shannon}, {len(selected_articles)} articles")

        if len(selected_articles) > 150000:
            break
    
    logger.info(f"Final selection: {len(selected_articles)} articles")
    with open("selected_articles", "w") as out:
        for article in selected_articles:
            out.write(f"{article}\n")

    
