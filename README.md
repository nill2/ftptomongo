# ftptomongo

This project created to store pictures from my IP camera.
The camera can only send pictures via FTP. the idea of the app to emulate an FTP server and store the content in the database (MongoDB).
also played with CI to make the process smooth and created unit and integrations tests.

## Installation

### Local installation

#### Prerequisites

Installed [python](https://docs.python.org/3/installing/index.html) with dependencies...

#### Clone this repository to your local machine

```shell
git clone https://github.com/nill2/ftptomongo
```

Install reqirements

```shell
pip install -r requirements.txt
```

Install [hashicorp vaults](https://developer.hashicorp.com/vault/tutorials/hcp-vault-secrets-get-started/hcp-vault-secrets-install-cli)

to make sure that environment is the same

```shell
conda env create -f environment.yml
```

Install pytest (if you want run unit or e2e tests) and other tools

```shell
          pip install pyftpdlib
          pip install pylint
          pip install psutil
          pip install pymongo
          pip install hvac
          pip install flake8
          pip install pytest
```

And run the application in the application folder

```shell
python3 ftptomongo
```

## Contributing

If you want to contribute to this project, please follow these guidelines.

CI is set up with Github Actions.
On a commit it will automatically check your branch with linters (pyling and flake8)
unit and e2e tests.

On each PR to MAIN branch docker image is automatically generated and deployed to ghcr.io

On each release python package is created and publiched to 

Check or run github actions [here] (https://github.com/nill2/ftptomongo/actions)

Explore the workflows code [here](https://github.com/nill2/ftptomongo/tree/main/.github/workflows)
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

You can reach out to the project maintainer by [email](mailto:danil.d.kabanov@gmail.com)
