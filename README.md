# MTP-DB - The Membrane Transport Protein Database

Welcome to the repository for the MTP-DB, a database that aims to collect information regarding the transportome, and the proteins that make it up.

The repository contains Daedalus, a Python package to download, parse and rebuild the MTP-DB on the fly. You can also find database releases in the [releases page](https://github.com/CMA-Lab/MTP-DB/releases) with pre-generated database files.

To browse the database locally, we suggest SQLite browsers such as [this FOSS program](https://sqlitebrowser.org/).

## Citing the MTP-DB

If you use the MTP-DB in your research, please cite:
> Coming soon
More information is present in the [CITATION.cff](CITATION.cff) file.

## Generating the MTP-DB locally
You have two options if you wish to regenerate the MTP-DB locally.

You can download the pre-built Docker container from our DockerHub repository and execute that. You will need to install [Docker](https://www.docker.com/) to do this:
```bash
docker run <ADD ME!> --help
```

If you do not wish to use Docker, you wish to use the latest code, or you want to modify the code locally, clone the repository to your local machine. You will need to have Python `3.10.10` and `git` installed:
```bash
git clone git@github.com:CMA-Lab/MTP-DB.git
cd MTP-DB/src
# It is optional, but highly reccomended to work in a
# Python virtual environment
python -m venv env
source env/bin/activate

python -m daedalus --help
```

As an alternative, you can take a look in the `src/scripts` folder for helper scripts that regenerate and run a locally-made Docker container. In this way, you can work on local code but without having to have Python installed (but having Docker installed). For example:
```bash
git clone git@github.com:CMA-Lab/MTP-DB.git
cd MTP-DB/src
./scripts/rrun --help
```
Be aware that these scripts are working-directory sensible, and will only work if your current WD is in `MTP-DB/src/`.

### Sister repositories
Other repositories contain code closely related to the MTP-DB. In particular:
- [Transportome Profiler](https://github.com/CMA-Lab/transportome_profiler): Code for our analysis on the transportome based on the data included in the Database.

# Contributing
We are very fond of contributors. Please take a look at the [contributing guide](CONTRIBUTING.md) if you wish to contribute.
