# MTP-DB - The Membrane Transport Protein Database
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

Welcome to the repository for the MTP-DB, a database that aims to collect information regarding the transportome, and the proteins that make it up.

The repository contains Daedalus, a Python package to download, parse and rebuild the MTP-DB on the fly. You can also find database releases in the [releases page](https://github.com/CMA-Lab/MTP-DB/releases) with pre-generated database files.

Daedalus takes care of connecting to, downloading from, parsing and patching data retrieved from remote databases, compiling them into the MTP-DB. Daedalus is written in Python.

You can take a look at the [CHANGELOG.md](CHANGELOG.md) file for a changelog of each release of the database.

To browse the database locally, we suggest SQLite browsers such as [this FOSS program](https://sqlitebrowser.org/).

## Citing the MTP-DB

If you use the MTP-DB in your research, please cite:
> Coming soon

More information is present in the [CITATION.cff](CITATION.cff) file.

## Generating the MTP-DB locally
You have two options if you wish to regenerate the MTP-DB locally.

You can download the pre-built Docker container from our DockerHub repository and execute that. You will need to install [Docker](https://www.docker.com/) to do this:
```bash
docker run -it --rm -v "OUT_DIR:/app/out" "cmalabscience/mtpdb:VERSION" "/app/out" --help
```
Just replace `OUT_DIR` with the full path to the output directory of your choice and `VERSION` with a valid version (see our [releases](https://github.com/CMA-Lab/MTP-DB/releases) and our [Docker Hub repository](https://hub.docker.com/r/cmalabscience/mtpdb)). Any arguments to Daedalus (e.g. `--help`) can be passed at the end of the command. You can find a script ([`./src/scripts/run_remote_docker`](https://github.com/CMA-Lab/MTP-DB/blob/main/src/scripts/run_remote_docker)) that does this in a more user-friendly way in the scripts folder.

If you do not wish to use Docker, you wish to use the latest code, or you want to modify the code locally, clone the repository to your local machine. You will need to have Python `3.10.10` and `git` installed:
```bash
git clone git@github.com:CMA-Lab/MTP-DB.git
cd MTP-DB/src
# It is optional, but highly reccomended to work in a
# Python virtual environment
python -m venv env
source env/bin/activate

pip install -r requirements.txt
```

You can then run Daedalus with:
```bash
python -m daedalus --help
```

As an alternative, you can take a look in the `src/scripts` folder for helper scripts that regenerate and run a locally-made Docker container. This way, you can work on local code but without having to have Python installed (but having Docker installed). For example:
```bash
git clone git@github.com:CMA-Lab/MTP-DB.git
cd MTP-DB/src
./scripts/rrun --help
```
Be aware that these scripts are working-directory sensible, and will only work if your current WD is in `MTP-DB/src/`.

# Contributing
We are very fond of contributors and collaborators. Please take a look at the [contributing guide](CONTRIBUTING.md) if you wish to contribute.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Feat-FeAR"><img src="https://avatars.githubusercontent.com/u/88393554?v=4?s=100" width="100px;" alt="Federico Alessandro Ruffinatti"/><br /><sub><b>Federico Alessandro Ruffinatti</b></sub></a><br /><a href="https://github.com/CMA-Lab/MTP-DB/issues?q=author%3AFeat-FeAR" title="Bug reports">🐛</a> <a href="https://github.com/CMA-Lab/MTP-DB/commits?author=Feat-FeAR" title="Code">💻</a> <a href="#maintenance-Feat-FeAR" title="Maintenance">🚧</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
