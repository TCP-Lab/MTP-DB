# Scripts

This folder hosts scripts to help doing the day-to-day running of the MTP-DB.

- `make_release_docker` makes and tags a docker for publishing on DockerHub. It also pushes it to our repository.
- `rebuild_docker` makes a local docker, does not push it, and tags it as `mtpdb:bleeding`.
- `run_rebuilder` wraps the correct command to run the local docker made by `rebuild_docker`. It is an easy way to run the local bleeding docker without specifying the version every time.
- `run_remote_docker` wraps the correct command to run the docker container from the remote Docker Hub repository, but you have to specify the version manually.
- `test_daedalus` wraps a test call, in order to test the docker container. It will tag it as `mtpdb_test:bleeding`.
