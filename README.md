# ftptomongo

This project created to store pictures from my IP camera. 
The camera can only send pictures via FTP. the idea of the app to emulate an FTP server and store the content in the database (MongoDB).
also played with CI to make the process smooth and created unit and integrations tests.

## Installation

### Local installation
#### Prerequisites
Installed python with dependencies
https://docs.python.org/3/installing/index.html




#### Clone this repository to your local machine:

```shell
git clone https://github.com/nill2/ftptomongo
```

Install reqirements

```shell
pip install -r requirements.txt
```

Install hashicorp vaults
https://developer.hashicorp.com/vault/tutorials/hcp-vault-secrets-get-started/hcp-vault-secrets-install-cli 

And run the application in the application folder

```shell
python ftptomongo
```

## Contributing

If you want to contribute to this project, please follow these guidelines.

CI is set up with Github Actions.
On a commit it will automatically check your branch with linters (pyling and)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

You can reach out to the project maintainer at danil.d.kabanov@gmail.com
