import requests as rq
from bs4 import BeautifulSoup


def main(url):
    soup = BeautifulSoup(rq.get(url=url).content.decode())

    ensgs = []
    symbols = []

    for i, table in enumerate(soup("table")):
        print(f"\n>>>>> BEGIN TABLE {i} <<<<<\n")
        for td in table("td"):
            if [
                "grac_category_simple"
            ] in td.attrs.values() and td.string == "Systematic nomenclature":
                symbol = td.find_next().string
                print(f"Gene: {symbol}")
                if symbol not in symbols:
                    symbols.append(symbol)

            if [
                "grac_category_simple"
            ] in td.attrs.values() and td.string == "Ensembl ID":
                ensg = td.find_next("a").string
                print(f"Ensg: {ensg}")
                if ensg not in ensgs:
                    ensgs.append(ensg)

    print(f"Scraped {len(ensgs)} ENSGs: {', '.join(ensgs)}")
    print("Same list, in new lines: {}".format("\n".join(ensgs)))
    print("New lined gene symbols: {}".format("\n".join(symbols)))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URl to scrape")

    args = parser.parse_args()

    main(args.url)
