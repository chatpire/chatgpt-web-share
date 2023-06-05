import json
import os.path
import sys


def create_config(args):
    if len(args) < 1:
        print("Usage: python manage.py create_config [config_dir_path]")
        sys.exit(1)
    config_dir_path = args[0]
    if not os.path.exists(config_dir_path):
        print(f"config_dir_path {config_dir_path} does not exist")
        sys.exit(1)
    from api.conf.config import Config
    from api.conf.credentials import Credentials
    Config().create(config_dir_path)
    Credentials().create(config_dir_path)


def get_config_schema(args):
    from api.conf.config import ConfigModel
    print(ConfigModel.schema_json(indent=2))


def get_credentials_schema(args):
    from api.conf.credentials import CredentialsModel
    print(CredentialsModel.schema_json(indent=2))


def get_model_definitions(args):
    from api.enums.models import OpenaiWebChatModels, OpenaiApiChatModels
    result = {
        "openai_web": [model.__str__() for model in OpenaiWebChatModels],
        "openai_api": [model.__str__() for model in OpenaiApiChatModels]
    }
    print(json.dumps(result))


commands = {
    "create_config": create_config,
    "get_config_schema": get_config_schema,
    "get_credentials_schema": get_credentials_schema,
    "get_model_definitions": get_model_definitions
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py [command] [args]")
        print("Available commands:")
        for command in commands:
            print(command)
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
