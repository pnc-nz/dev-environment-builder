from cgitb import reset
from genericpath import isdir
import platform
import re
import os
import subprocess
from os.path import expanduser
from pathlib import Path
from urllib.request import urlopen

OS = platform.system().lower()
HOME_DIR = Path.home()
SOURCE_DIR = 'src'
SSH_DIR = '.ssh'
VERSION_CONTROLS = [
    'bitbucket.org',
    'dev.azure.com',
    'github.com',
    'gitlab.com',
    'sourceforge.net',
]


class VersionControl():
    def __init__(self, name: str, accounts: list[str] = []) -> None:
        self.name = name
        self.accounts = accounts

    def __str__(self) -> str:
        return f'{self.name}'


def get_github_id(username: str) -> str:
    id = ''
    gh_url = f'https://api.github.com/users/{username}'
    try:
        with urlopen(f'{gh_url}') as r:
            import json
            content = json.load(r)
            id = content['idx']
    except KeyError:
        print(f'[INFO]: Could not resolve user.id at {gh_url}')
    return id


def set_operating_system() -> str:
    """Checks for a valid operating system and returns the value

    Raises:
        OSError: Error message to indicate an unsupported Operating System

    Returns:
        str: Operating System name from platform.system()
    """
    operating_system = platform.system().lower()
    supported_os = ['windows', 'linux', 'darwin']
    if operating_system not in supported_os:
        raise OSError('Invalid Operating System!')
    else:
        print(f'Operating System Set: {operating_system}')
        return operating_system


def set_user_home_path() -> str:
    """Sets the default home path for the current user (e.g. `%USERPROFILE%` or `~` equivalent)
    
    Raises:
        RuntimeError: Error message to indicate an issue in resolving Path
        
    Returns:
        str: The Home Path of the current User
    """
    try:
        home_path = Path.home()
        print(f'Home Path Set: {home_path}')
        return home_path
    except RuntimeError as e:
        raise (e)


def set_github_accounts() -> list[str]:
    pass


def set_version_controls() -> list[str]:
    version_controls = []
    for version_control in VERSION_CONTROLS:
        pass
    pass


def get_valid_filename(filename: str) -> bool:
    print(f'[DEBUG]: Received [{filename}]')
    # remove leading/trailing whitespace
    filename = filename.strip()

    # slice to 32 character max
    if len(filename) > 32:
        filename = filename[:32]
        print(
            f'[DEBUG]: Filename was over 32 characters, trimmed to [{filename}]')

    # remove any invalid character
    # https://github.com/django/django/blob/3283120cca5d5eba5c3619612d0de5ad49dcf054/django/utils/text.py#L235
    new_filename = re.sub(r'(?u)[^-\w.]', '', filename)
    if new_filename != filename:
        print(
            f'[DEBUG]: Filename contained invalid characters, substituted to [{new_filename}]')

    return new_filename


def get_user_input_loop(user_input: str) -> str:
    get_input = True
    while get_input:
        try:
            response = input(f'{user_input}')
            get_input = False
            return response.lower()
        except EOFError as e:
            print(e)


def convert_yes_no_to_bool(user_input: str) -> bool:
    if user_input.startswith('y'):
        return True
    return False


def create_src_directory(home_path: str, src_dir: str) -> str:
    src_path = os.path.join(home_path, src_dir)
    try:
        Path(f'{src_path}').mkdir(parents=True)
        print(f'[INFO]: Created Directory: [{src_path}]')

    except FileExistsError:
        print(f'[INFO]: Directory Exists: [{src_path}]')

    return src_path


def create_vcs_directories(src_path: str) -> list[VersionControl]:
    # Check / Create the skeleton for various providers
    """
    /src
    ├── /github.com
    │   ├── /pnc-nz
    │   ├── /prayer-clan 
    ├── /gitlab.com
    ├── /dev.azure.com
    ├── /bitbucket.org
    ├── /sourceforge.net
    """
    created_vcs = []
    # for VERSION_CONTROLS providers
    for vc in VERSION_CONTROLS:
        print(f'Create Directory for [{vc}]?')
        response = get_user_input_loop('[Y]es or [N]o\n> ')
        while response != response.startswith('y') or response != response.startswith('n'):
            if response.startswith('y'):
                # create vc dir
                try:
                    vc_path = os.path.join(src_path, vc)
                    Path(vc_path).mkdir(parents=True)
                    print(f'[INFO]: Created directory: [{vc_path}]')
                except FileExistsError:
                    print(f'[INFO]: Directory already exists [{vc_path}]')
                version_control = VersionControl(name=vc)

                # account loop for vc dir
                add_more_accounts = True
                while add_more_accounts:
                    account = get_valid_filename(get_user_input_loop(
                        f'Enter the account name for [{vc}]\n> '))
                    try:
                        account_path = os.path.join(vc_path, account)
                        Path(f'{account_path}').mkdir(parents=True)
                        print(
                            f'[INFO]: Created directory for: [{account_path}]')
                    except FileExistsError:
                        print(
                            f'[INFO]: Directory already exists [{account_path}]')
                    version_control.accounts.append(account)

                    # additional accounts under this organisation
                    print(f'Add another account name for [{vc}]?')
                    add_more_accounts = convert_yes_no_to_bool(
                        get_user_input_loop('[Y]es or [N]o\n> '))
                break
            elif response.startswith('n'):
                break
    created_vcs.append(version_control)
    return created_vcs


def create_ssh_directory(home_path: str, ssh_dir: str):
    ssh_path = os.path.join(home_path, ssh_dir)
    try:
        Path(f'{ssh_path}').mkdir(parents=True)
        print(f'[INFO]: Created Directory: [{ssh_path}]')
    except FileExistsError:
        print(f'[INFO]: Directory Exists: [{ssh_path}]')
    return ssh_path


def create_ssh_account_directories(ssh_path: str, vcs: list[VersionControl]):
    # create the SSH skeleton
    """
    /.ssh
    ├── /github.com
    │   ├── /pnc-nz
    │   ├── /prayer-clan 
    ├── /gitlab.com
    ├── ....
    """
    for vc in vcs:
        try:
            vc_path = os.path.join(ssh_path, vc.name)
            # Path(vc_path).mkdir(parents=True)
            # print(f'[INFO]: Created directory: [{vc_path}]')
            for account in vc.accounts:
                # create version control -> account directory
                account_path = os.path.join(vc_path, account)
                Path(account_path).mkdir(parents=True)
                print(f'[INFO]: Created directory: [{account_path}]')

                # generate SSH key for this vcs/account
                generate_ssh_keys(
                    ssh_account_path=account_path, account=account)

        except FileExistsError:
            print(f'[INFO]: Directory already exists [{vc_path}]')


def generate_ssh_keys(ssh_account_path: str, account: str):
    """
    -t  type    rsa1, rsa, dsa (DEFAULT: rsa)
    -b  bits    1024, 2048, 4096
    -C  comment 
    """
    # ssh_account_path
    # c:\users\ego\.ssh\github.com\pnc-nz
    #   ...\pnc_nz_rsa
    filename = os.path.join(ssh_account_path, f'{account}_rsa')
    type = 'rsa'
    bits = '4096'
    command = [
        'ssh-keygen',
        '-t', f'{type}',
        '-b', f'{bits}',
        '-f', f'{filename}',
        '-C', f'{account}',
    ]

    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(
            f'[INFO]: Error creating ssh key with ssh-keygen\n Command: {command}')


def create_ssh_config(ssh_path: str) -> str:
    # 'c:\users\ego\.ssh'
    config_file = 'config'
    config_path = os.path.join(ssh_path, config_file)
    if not os.path.exists(f'{config_path}'):
        # touch `config`
        open(config_path, 'w').close()
        print(f'[INFO]: Created file [{config_path}]')

        # chmod 600 owner read/write
        os.chmod(config_path, 0o600)
    else:
        print(f'[INFO]: {config_path} already exists!')
    return config_path

# TODO: finish writing this


def update_ssh_config(ssh_dir):
    """
    # Primary Personal GitHub - john.doe@personal.com
    Host personal.github.com
        HostName github.com
        User git
        AddKeysToAgent yes
        UseKeychain yes
        IdentityFile ~/.ssh/github.com/personal_id_rsa
        IdentitiesOnly yes
    
    
    # {vcs.name} - {vcs.account}
    Host {vcs.account}.{vcs.name}
        HostName {vcs.name}
        User git
        AddKeysToAgent yes
        UseKeychain yes
        IdentityFile ~/.ssh/{vcs.name}/{vcs.account}_id_rsa
        IdentitiesOnly yes
    
    """
    ssh_file = open("")
    pass


# TODO: finish writing this
def create_git_config():
    # TODO: Creates the top-level `.gitconfig` file
    #  handles url-rewriting rules for each version control + accounts
    pass


def run():
    operating_system = set_operating_system()
    home_path = set_user_home_path()
    version_controls = []
    # get_github_id('prayer-clan')

    # src setup; based on vcs
    print('Setup Source directories?')
    if (convert_yes_no_to_bool(get_user_input_loop('[Y]es or [N]o\n> '))):
        src_path = create_src_directory(HOME_DIR, SOURCE_DIR)
        version_controls = create_vcs_directories(src_path)

    if version_controls.__len__() < 1:
        return

    # ssh setup; based on vcs
    print('Setup SSH key directories?')
    if (convert_yes_no_to_bool(get_user_input_loop('[Y]es or [N]o\n> '))):
        ssh_path = create_ssh_directory(HOME_DIR, SSH_DIR)
        ssh_config_path = create_ssh_config(ssh_path)
        create_ssh_account_directories(ssh_path, version_controls)


# Run
if __name__ == "__main__":
    run()
