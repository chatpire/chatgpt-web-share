import sys


def init_config(args):
    raise NotImplementedError()


def get_config_schema(args):
    from api.conf.config import ConfigModel
    print(ConfigModel.schema_json(indent=2))


def get_credentials_schema(args):
    from api.conf.credentials import CredentialsModel
    print(CredentialsModel.schema_json(indent=2))


commands = {
    "init_config": init_config,
    "get_config_schema": get_config_schema,
    "get_credentials_schema": get_credentials_schema,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py [command] [args]")
        sys.exit(1)

    command = sys.argv[1]
    args = []
    if len(sys.argv) > 2:
        args = sys.argv[2:]

    if command in commands:
        commands[command](args)
    else:
        print("Invalid command:", command)
        sys.exit(1)
