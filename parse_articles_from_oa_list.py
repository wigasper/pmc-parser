

def main():
    target_journal = "Front Immunol"

    pmc_ids = []

    with open("oa_last_10_years.csv", "r") as handle:
        for line in handle:
            line = line.split(",")
            journal = line[1].split(";")[0]
            journal = journal.split(".")[0]
            if journal == target_journal:
                pmc_ids.append(line[2])

    with open("specialized_articles", "w") as out:
        for pmc_id in pmc_ids:
            out.write(f"{pmc_id}\n")


if __name__ == "__main__":
    main()
