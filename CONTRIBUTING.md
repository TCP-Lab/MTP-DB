# Contributing to the MTP-DB

Thank you for your interest in collaborating on the project! We welcome all contributions, including documentation, testing, creation of issues, suggestions, pull requests, and general discussion.

If you want to contribute, you implicitly accept our Code of Conduct. Please refer to the [CODE_OF_CONDUCT.md file in the CMA-Lab's organization page](https://github.com/CMA-Lab/.github/blob/main/CODE_OF_CONDUCT.md) for more information.

We recognize all meaningful contributions. Please see the later section on Recognition.

## Opening issues
If you find a problem, want to point out an error, or have a suggestion or other public comment on the project please [open an issue](https://github.com/CMA-Lab/MTP-DB/issues/new)! Detail your issue and relevant information, and we will address it.

We also use issues to keep track of features that we want in the DB, or things we want to change. Please refer to the [ROADMAP.md](ROADMAP.md) file for the project's roadmap. Feel free to comment on roadmap issues or start working on an item in the roadmap by [creating a fork of the project](https://docs.github.com/en/get-started/quickstart/fork-a-repo).

## Code style
We strive to keep a unified code style. For this reason, we use [`pre-commit`](https://pre-commit.com/) to unify the style of our Python code. If you want to contribute code, please make sure you setup the pre-commit hooks with [`pre-commit`](https://pre-commit.com/).

## Commit Messages
We follow the [`conventional commits`](https://www.conventionalcommits.org/en/v1.0.0/) specification.
This means that your commit messages should follow the pattern `tag[!]: msg`,
where `tag` is one of:
- `feat`: This is an addition or a change that adds something new or changes something. Most commits are `feat` or `fix` commits.
- `fix`: This is a bugfix or issue fix. Add a reference to the issue or describe it in the commit message.
- `refactor`: This is a code refactoring. No logic is changed here.
- `docs`: Additions or changes to the documentation.
- `test`: Additions or chanegs to the testing facility.
- `chore`: A routine or necessary change to make something run / work (like changes related to a routine release).
- `ci`: A change to the GitHub actions or other automatic workflow.
- `style`: A change to the code style.
- `perf`: A change related to the code performance is some way (e.g. changes to make the codebase faster).

You can also add a scope to the tag like `feat(retrievers): msg` to specify what was changed, but it is optional. We do not have a specific list of scopes, so you can use whatever you think is ok, if you want to.

Add a `!` to the tag (e.g. `feat!: msg`) if the change is particularly breaking (like changes to the DB schema). A `!` commit should also be added to the `CHANGELOG`.

A `pre-commit` hook reminds you if you did not follow the convention, so you don't get it wrong by accident.

# Recognition
All contributions will be recognized in the [README.md](README.md) file. If you believe you should be credited but are not, or you are credited for the wrong reasons, please [open an issue](https://github.com/CMA-Lab/MTP-DB/issues/new).

Very significant contributions, or sustained contributions over a long period of time may warrant recognition as a proper Author. All authors will be listed in the [AUTHORS.md](AUTHORS.md) file, and will be given credit of all future scientific publications regarding the MTP-DB. Inclusion of new authors is given based on the decision of all existing authors in a public setting and with prior permission of the new author-to-be.

# Further information
If you wish, you can contact any of the authors (see the [AUTHORS.md](AUTHORS.md) file) for further information regarding particular research collaboration opportunities.
