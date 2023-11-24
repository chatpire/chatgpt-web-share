import argparse
import json
import os
import random
import string
import sys

from fastapi.encoders import jsonable_encoder
from ruamel.yaml import YAML

from api.conf.config import Config
from api.conf.credentials import Credentials


def generate_random_secret(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def create_config(args):
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    config = Config(load_config=False)
    credentials = Credentials(load_config=False)

    # Generate random secrets if needed
    if args.generate_secrets:
        config.auth.jwt_secret = generate_random_secret()
        config.auth.user_secret = generate_random_secret()

    # Set MongoDB URL and initial admin password if provided
    if args.mongodb_url:
        config.data.mongodb_url = args.mongodb_url
    if args.initial_admin_password:
        config.common.initial_admin_user_password = args.initial_admin_password
    if args.chatgpt_base_url:
        config.openai_web.chatgpt_base_url = args.chatgpt_base_url

    def save_config(base_config, config_filename):
        output_path = os.path.join(output_dir, config_filename)
        if os.path.exists(output_path):
            # Ask for confirmation before overwriting existing config
            print(f"File {output_path} already exists, do you want to overwrite it? (y/N)")
            choice = input().lower()
            if choice != 'y':
                print("Skipping...")
                return
        with open(output_path, mode='w', encoding='utf-8') as f:
            yaml = YAML()
            yaml.dump(jsonable_encoder(base_config.model().dict()), f)
            print(f"Config file saved to {output_path}.")

    save_config(config, 'config.yaml')
    save_config(credentials, 'credentials.yaml')


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


def main():
    parser = argparse.ArgumentParser(description='Manage.py utility for configuration and setup.')
    subparsers = parser.add_subparsers(dest='command')

    # create_config command
    create_config_parser = subparsers.add_parser('create_config', help='Create new configuration files.')
    create_config_parser.add_argument('--output-dir', '-O', type=str, default='./config_templates',
                                      help='Directory path for the configuration files.')
    create_config_parser.add_argument('--generate-secrets', '-G', action='store_true',
                                      help='Generate random secrets for auth settings.')
    create_config_parser.add_argument('--mongodb-url', '-M', type=str, help='MongoDB URL to set in the configuration.')
    create_config_parser.add_argument('--initial-admin-password', '-P', type=str,
                                      help='Initial admin password to set in the configuration.')
    create_config_parser.add_argument('--chatgpt-base-url', '-C', type=str)

    # Other command parsers
    subparsers.add_parser('get_config_schema', help='Get the JSON schema of the configuration model.')
    subparsers.add_parser('get_credentials_schema', help='Get the JSON schema of the credentials model.')
    subparsers.add_parser('get_model_definitions', help='Get the definitions of available models.')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        'create_config': create_config,
        'get_config_schema': get_config_schema,
        'get_credentials_schema': get_credentials_schema,
        'get_model_definitions': get_model_definitions,
    }

    command_function = commands.get(args.command)
    if command_function:
        command_function(args)
    else:
        print("Invalid command:", args.command)
        sys.exit(1)


if __name__ == "__main__":
    main()
