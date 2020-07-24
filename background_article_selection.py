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
    with open("oa_last_10_years.csv", "r") as handle:
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


'''
Returns the Shannon index for a random sample of articles using 
the technique in the main routine
'''
def random_sample_shannon(sample_set_size):
    logger = initialize_logger(name="random_sample_shannon")
    random.seed(42)

    term_trees = get_term_top_ancestor_nodes()
    pmc_doc_terms = get_pmcid_mesh_terms()

    # parent nodes are the parent nodes on the MeSH graph
    parent_nodes = [node for key, node_list in term_trees.items() for node in node_list]
    parent_nodes = list(dict.fromkeys(parent_nodes))
    parent_node_counts = {node: 0 for node in parent_nodes}
    
    # all PMCIDs in the OA subset
    pmc_ids = list(pmc_doc_terms.keys())
    logger.debug(f"length pmc_ids: {len(pmc_ids)}")
    
    pmc_ids = random.sample(pmc_ids, sample_set_size)

    for pmc_id in pmc_ids:
        for term in pmc_doc_terms[pmc_id]:
            for node in term_trees[term]:
                parent_node_counts[node] += 1
    
    shannon_index = shannon(parent_node_counts)

    logger.info(f"Random sample size: {sample_set_size}")
    logger.info(f"Shannon index: {shannon_index}")

    return shannon_index

def write_ftp_paths(pmcids):
    article_set = set(pmcids)

    with open("oa_last_10_years.csv", "r") as handle:
        with open("selected_articles_ftp_paths", "w") as out:
            for line in handle:
                line = line.split(",")
                if line[2] in article_set:
                    out.write(line[0])
                    out.write("\n")

'''
Get a logger
'''
def initialize_logger(name="background_article_selection", debug=False, 
                    quiet=False):
    level = logging.INFO
    if debug:
        level = logging.DEBUG

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.FileHandler(f"{name}.log")
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
    logger = initialize_logger(debug=True)
    logger.info("New run")

    term_trees = get_term_top_ancestor_nodes()
    pmc_doc_terms = get_pmcid_mesh_terms()

    # parent nodes are the parent nodes on the MeSH graph
    parent_nodes = [node for key, node_list in term_trees.items() for node in node_list]
    parent_nodes = list(dict.fromkeys(parent_nodes))
    parent_node_counts = {node: 0 for node in parent_nodes}
    
    # all PMCIDs in the OA subset
    pmc_ids = list(pmc_doc_terms.keys())
    logger.debug(f"length pmc_ids: {len(pmc_ids)}")

    # set seed for reproducibility
    random.seed(42)

    # init
    # number of articles desired
    num_articles_required = 150000
    # rolling current Shannon index for the article set
    current_shannon = 0.0
    # minimum Shannon index allowed
    shannon_floor = 4.4
    # list for selection articles
    selected_articles = []
    # debug update after this many articles are checked
    logger_update_interval = 20000
    # get unused articles
    unused_articles = [pmc_id for pmc_id in pmc_ids]
    # number of passes to make
    max_passes = 3
    # current pass
    num_passes = 0

    # start adding to selected_articles
    while len(selected_articles) <= num_articles_required and num_passes < max_passes: 
        # pool of potential articles
        putative_article_pool = [pmc_id for pmc_id in unused_articles]
        # reset, will be added to for additional passes
        unused_articles = []
        # shuffle the list
        random.shuffle(putative_article_pool)
        
        logger.debug(f"length article_pool: {len(putative_article_pool)}")

        for index, pmc_id in enumerate(putative_article_pool):
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
            else:
                unused_articles.append(pmc_id)
            
            # Update every update_interval
            if index % logger_update_interval == 0:
                debug_msg_0 = f"Current Shannon: {current_shannon}"
                debug_msg_1 = f"{len(selected_articles)} articles"
                debug_msg_2 = f"index: {index}"
                logger.debug(f"{debug_msg_0}, {debug_msg_1}, {debug_msg_2}")
            
            if len(selected_articles) > num_articles_required:
                break
        
        num_passes += 1
        logger.info(f"completed {num_passes} passes, Shannon: {current_shannon}")
    
    logger.info(f"Final selection: {len(selected_articles)} articles")
    logger.info(f"Final Shannon: {current_shannon}")
    
    # Do some checking here
    deduped_articles = list(dict.fromkeys(selected_articles))
    if len(deduped_articles) != len(selected_articles):
        logger.error("Duplicates in selected article set")

    with open("selected_articles", "w") as out:
        for article in selected_articles:
            out.write(f"{article}\n")

    write_ftp_paths(selected_articles) 
