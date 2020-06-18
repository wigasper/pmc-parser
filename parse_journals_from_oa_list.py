import re

from collections import Counter

def main():
    journals = []
    with open("oa_last_10_years.csv", "r") as handle:
        for line in handle:
            line = line.split(",")
            journal = line[1]
            journal = journal.split(";")[0]
            journal = journal.split(".")[0]            
            journals.append(journal)

    journals = Counter(journals)
    journals = [[key, val] for key, val in journals.items()]
    journals = sorted(journals, key = lambda journals: journals[1], reverse=True)

    with open("journals_counts", "w") as out:
        for journal in journals:
            out.write(",".join([journal[0], str(journal[1])]))
            out.write("\n")

if __name__ == "__main__":
    main()
