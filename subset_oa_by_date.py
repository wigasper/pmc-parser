
if __name__ == "__main__":

    with open("oa_file_list.csv", "r") as handle:
        with open("oa_last_10_years.csv", "w") as out:
            for line in handle:
                line = line.split(",")
                try:
                    year = int(line[1].split(";")[0].split()[-3])
                except:
                    print(f"Could not get year for: {line[2]}")
                    year = 0

                if year > 2009:
                    out.write(",".join(line))
