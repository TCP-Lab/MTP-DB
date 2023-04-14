# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) with the format `MAJOR.YY.0W[_MINOR][-Modifier]`. The major version increases when the database schema changes. Minor tags are added for multiple releases in the same week, starting from `2` (the `1` is implicit). Modifiers are added for pre-releases (e.g. `beta` or `alpha`).

## Unrealeased

### Changes
- [c971e4a] Update run_rebuilder to be compatible with the new CLI;
- [1e17dd6, fb7a4b5] Write better READMEs.

## [0.23.15-beta] - First release

This is the first release of the database. The DB features data from 7 different databases, all joined up for ease of consumption. We include:
- [ENSEMBL](https://www.ensembl.org/index.html) gene IDs and information, making the backbone of the database IDs;
- [HGNC](https://www.genenames.org/) for up-to-date, official gene names and gene grouping;
- [IUPHAR](https://www.guidetopharmacology.org/) for target (in our case transporters) and ligand (i.e. drugs/internal compounds) interactions, as well as gene grouping, ion channel conductances, and more;
- [COSMIC](https://cancer.sanger.ac.uk/cosmic) for mutational information;
- [SLC tables](http://slc.bioparadigms.org/) for solute carrier information, such as their class and carried solute;
- [TCDB](https://www.tcdb.org/) for transporter classification information.

We apply manual patches to the data where expert information is lacking from the above databases.

The database is released as a `.sqlite` file at each release.

I highlight the latest changes:

### Changes
- [a03ab0b] **Major refactoring of Daedalus**
    - The current list of `IF-ELSE` statements to run or skip some parsers
    (for debugging purposes) was terrible. Now, a new class handles
    running them properly.
    - The `parsers.py` file was getting too long for comfort. It was broken up
    into chunks and ported to multiple files in `./parsers/`
    - A new `./constants` module holds all of the constants that were strewn
    about, with the exception of some constants that are very
    parser-specific.
    - A lot of things were removed from the module `init.py`, since they
    did not belong there.
    - The argparser was finally actually finished.
    - If the COSMIC username/password combo is not specified, the cosmic
    data will not be downloaded (at the user's risk).
    - New CLI parameters `run` and `skip` allow easier selective running of
    the different parsers, so that we don't commit breaking changes
    anymore by accident (aka `SKIP_ALL = True`)
    - We use `package.resources` everywhere now, without having to use
    wobbly relative paths. This should make us ready to convert to a
    proper package.
    - The `tests/` folder is now out of `./daedalus/.` It is probably
    completely broken now, but it was useless anyway.
- [8f29fbe] **Many Daedalus logic changes**
    - Changed Biomart's `XML`s to be more efficient. Should reduce download times a bit.
    - Allowed Biomart to download colnames too, therefore making manual colnames useless. I just standardize back to the same format we have used until now the names tha biomart gives us.
        - This means that all of the colnames around were updated to the new naming.
    - Changed from `CSV` to `TSV` the format for the BioMart data. It seems that the csv parser does not escape commas in the data. How fun! This makes the tsv option the only feasible one.
    - Moved to the top of the BioMart list the `entrez` entry, so that the retriever has to download little data before crashing (easier debugging!).
    - Moved the logic for saving a pickle of the data to the `ResourceCache` class, from the bad hack in `make_database`.
    - Made the downloads from multithreaded to single-threaded. Why were they multithreaded in the first place? I have no idea.
    - The parsers that fail are now skipped gracefully, before dumping all failures at once and aborting. This should make large-scale failures easier to debug, since all parsers do not depend on each other to run (they only write to the database, they cannot read from it).
    - Written comments here and there.
    - Added delays after the warnings when using `--overwrite` and `--regen-cache`, so that one can `CTRL-C` when mistakes are made.
- [960da8f] **Added a project changelog**
    - We will follow CalVer `MAJOR.YY.0W[_MINOR][-Modifier]` from now on.
