import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import urlopen

OS = platform.system().lower()

# File & Directory Names
SOURCE_DIR_NAME = "src"
SSH_DIR_NAME = ".ssh"
TEMPLATES_DIR_NAME = "templates"

# GitConfig 
GC_TEMPLATES_DIR_NAME = "gitconfig"
GC_TOP_DIR_NAME = "top"
GC_ACCOUNT_DIR_NAME = "account"

GC_DEFAULT_FILE_NAME = "default"
GC_USER_FILE_NAME = "user"
GC_STANDARD_FILE_NAME = "standard"
GC_ORGANISATION_FILE_NAME = "organisation"
GC_FILE_NAME = ".gitconfig"
SSH_CONFIG_FILE_NAME = "config"

# Paths
HOME_DIR_PATH = Path.home()
SOURCE_DIR_PATH = HOME_DIR_PATH / SOURCE_DIR_NAME
SSH_DIR_PATH = HOME_DIR_PATH / SSH_DIR_NAME
SSH_CONFIG_PATH = SSH_DIR_PATH / SSH_CONFIG_FILE_NAME

# Version Controls
VERSION_CONTROL_SYSTEMS = [
    "bitbucket.org",
    "dev.azure.com",
    "github.com",
    "gitlab.com",
    "sourceforge.net",
]

@dataclass
class Account:
    name: str

@dataclass
class Organisation:
    name: str
    accounts: list["Account"] = field(default_factory=list)

@dataclass
class VersionControl:
    name: str
    organisations: list["Organisation"] = field(default_factory=list)
    accounts: list["Account"] = field(default_factory=list)


    def __str__(self) -> str:
        return f"{self.name}"

    def debug(self) -> None:
        print()
        print('---- DEBUG ----')
        print(f'VersionControl.name: {self.name}')
        print(f'VersionControl.organisations: {self.organisations}')
        print(f'VersionControl.accounts: {self.accounts}')

        # output organisations
        for idx, o in enumerate(self.organisations):
            print(f'VersionControl.organisations[{idx}]: {o.name}')

            # output organisational accounts
            for idxx, a in enumerate(o.accounts):
                print(f'VersionControl.organisations[{idx}].accounts[{idxx}]: {a.name}')


        # output standard accounts
        for idx, a in enumerate(self.accounts):
            print(f'>> VersionControl.accounts[{idx}]: {a.name}')

        print('---- DEBUG ----')
        print()




def get_github_id(username: str) -> str:
    id = ""
    gh_url = f"https://api.github.com/users/{username}"
    try:
        with urlopen(f"{gh_url}") as r:
            import json

            content = json.load(r)
            id = content["idx"]
    except KeyError:
        print(f"[INFO]: Could not resolve user.id at {gh_url}")
    return id



def get_valid_filename(filename: str) -> str:
    print(f"[DEBUG]: Received [{filename}]")
    # remove leading/trailing whitespace
    filename = filename.strip()

    # slice to 32 character max
    if len(filename) > 32:
        filename = filename[:32]
        print(f"[DEBUG]: Filename was over 32 characters, trimmed to [{filename}]")

    # remove any invalid character
    # https://github.com/django/django/blob/3283120cca5d5eba5c3619612d0de5ad49dcf054/django/utils/text.py#L235
    new_filename = re.sub(r"(?u)[^-\w.]", "", filename)
    if new_filename != filename:
        print(
            f"[DEBUG]: Filename contained invalid characters, substituted to [{new_filename}]"
        )

    return new_filename


def user_input(prompt: str, valid_responses: list[str] | None = None) -> str:
    """
    Prompt the user for input and return their response.

    Args:
        prompt (str): The message to display to the user
        valid_responses (list[str] | None): Optional list of valid responses for validation

    Returns:
        str: The user's validated response in lowercase

    Examples:
        >>> user_input("Enter name: ")
        Enter name: John
        'john'

        >>> user_input("Continue? [y/n]: ", ["y", "n"])
        Continue? [y/n]: y
        'y'
    """
    while True:
        try:
            response = input(prompt).strip().lower()

            if valid_responses is not None:
                if response in valid_responses:
                    return response
                print(f"Invalid input. Please enter one of: {', '.join(valid_responses)}")
            else:
                return response

        except EOFError:
            print("\nInput interrupted. Please try again.")



def create_src_directory(home_dir: Path, src_dir: str) -> Path:
    """
    Creates a /src/ directory within the user's home directory

    Args:
        home_dir (Path): The user's home directory path object
        src_dir (str): Name of the source directory to create

    Returns:
        Path: The full path to the created directory
    """
    src_path = home_dir / src_dir
    try:
        src_path.mkdir(parents=True, exist_ok=True)
        print(f"[INFO]: Created Directory: [{src_path}]")
    except Exception as e:
        print(f"[ERROR]: Failed to create directory: [{src_path}] - {str(e)}")

    return src_path

def _create_organisation(vcs_name: str) -> Organisation | None:
    """Helper function to create an organisation with accounts."""
    org_name = user_input("Type Organisation name and press enter (e.g. Contoso)\n> ")
    if not org_name:
        print("[ERROR]: Organisation name cannot be empty")
        return None

    org_name = get_valid_filename(org_name)
    organisation = Organisation(name=org_name)

    # Add accounts to organisation
    while True:
        if user_input(f"Add account to [{org_name}]? [y/n]\n> ", valid_responses=["y", "n"]) == "n":
            break

        account_name = user_input("Enter account name (e.g. john-doe or john@contoso.com)\n> ")
        if not account_name:
            print("[ERROR]: Account name cannot be empty")
            continue

        account_name = get_valid_filename(account_name)
        organisation.accounts.append(Account(name=account_name))

    return organisation if organisation.accounts else None

def _create_standard_accounts(vcs_name: str) -> list[Account]:
    """Helper function to create standard accounts."""
    accounts = []

    while True:
        if user_input(f"Add standard account for [{vcs_name}]? [y/n]\n> ", valid_responses=["y", "n"]) == "n":
            break

        account_name = user_input("Enter account name (e.g. john-doe)\n> ")
        if not account_name:
            print("[ERROR]: Account name cannot be empty")
            continue

        account_name = get_valid_filename(account_name)
        accounts.append(Account(name=account_name))

    return accounts

def generate_vcs_hierarchy() -> list[VersionControl]:
    """
    Creates a hierarchy of version control systems with organizations and accounts.

    The hierarchy supports two types of accounts:
    1. Organizational accounts: Accounts that belong to a specific organization/tenant
    2. Standard accounts: Personal or individual accounts

    Example structure:
        VersionControl (e.g. github.com)
        ├── Organisation (e.g. Contoso)
        │   ├── Account (e.g. john@contoso.com)
        │   └── Account (e.g. jane@contoso.com)
        └── Standard Accounts
            ├── Account (e.g. john-personal)
            └── Account (e.g. jane-personal)

    Returns:
        list[VersionControl]: List of configured version control systems
    """
    created_vcs = []
    for vcs in VERSION_CONTROL_SYSTEMS:
        menu_text = f"Configure [{vcs}]? [y/n]\n> "
        if user_input(f"{menu_text}", valid_responses=["y", "n"]) == "n":
            continue

        version_control = VersionControl(name=vcs)

        # Handle organisations
        menu_text = f"Add organisation to [{vcs}]? [y/n]\n> "
        while user_input(f"{menu_text}", valid_responses=["y", "n"]) == "y":
            if org := _create_organisation(vcs):
                version_control.organisations.append(org)

        # Handle standard accounts
        version_control.accounts.extend(_create_standard_accounts(vcs))

        # Only add VCS if it has either organisations or accounts
        if version_control.organisations or version_control.accounts:
            created_vcs.append(version_control)

    return created_vcs

def create_vcs_directories(src_path: Path, vcs_list: list[VersionControl]) -> None:
    """
    Creates directory structure for version control systems and their accounts.

    Creates directories for both organizational and standard accounts:
    /src
    ├── github.com
    │   ├── personal-account
    │   └── organization-name
    │       └── org-account

    Args:
        src_path (Path): Base source directory path
        vcs_list (list[VersionControl]): List of version control systems to process

    Example:
        /src
        ├── github.com
        │   ├── john-doe          # Standard account
        │   └── contoso          # Organization
        │       └── john-doe     # Organizational account
        └── gitlab.com
            └── jane-doe         # Standard account
    """
    def _create_directory(path: Path, context: str) -> None:
        """Helper function to create directory and handle errors."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"[INFO]: Created {context} directory: [{path}]")
        except Exception as e:
            print(f"[ERROR]: Failed to create {context} directory [{path}]: {str(e)}")

    def _process_organizational_accounts(vcs_path: Path, vcs: VersionControl) -> None:
        """Creates directories for organizational accounts."""
        for org in vcs.organisations:
            for account in org.accounts:
                account_path = vcs_path / org.name / account.name
                _create_directory(account_path, "organizational account")

    def _process_standard_accounts(vcs_path: Path, vcs: VersionControl) -> None:
        """Creates directories for standard accounts."""
        for account in vcs.accounts:
            account_path = vcs_path / account.name
            _create_directory(account_path, "standard account")

    try:
        # Process each version control system
        for vcs in vcs_list:
            vcs_path = src_path / vcs.name

            # Create organizational account directories
            _process_organizational_accounts(vcs_path, vcs)

            # Create standard account directories
            _process_standard_accounts(vcs_path, vcs)

    except Exception as e:
        print(f"[ERROR]: Unexpected error while creating directory structure: {str(e)}")

def create_ssh_directory(home_dir: Path, ssh_dir: str) -> Path:
    """
    Creates a .ssh directory in the home directory of the user.

    Args:
        home_dir (Path): The path object for user's home directory
        ssh_dir (str): The .ssh folder name to hold ssh config files

    Returns:
        Path: The full path to the .ssh directory
    """
    ssh_path = home_dir / ssh_dir
    try:
        ssh_path.mkdir(parents=True, exist_ok=True)
        print(f"[INFO]: Created Directory: [{ssh_path}]")
    except Exception as e:
        print(f"[ERROR]: Failed to create directory: [{ssh_path}] - {str(e)}")

    return ssh_path

def create_ssh_account_directories(ssh_path: Path, vcs: list[VersionControl]) -> None:
    """
    Creates SSH account directories for each VCS and account

    /.ssh
    ├── /github.com
    │   ├── /jane-doe
    │   ├── /john-doe
    ├── /gitlab.com
    ├── ....

    Args:
        ssh_path (Path): Path object for the .ssh directory
        vcs (list[VersionControl]): List of version control systems and their accounts
    """
    for vc in vcs:
        try:
            vc_path = ssh_path / vc.name

            for account in vc.accounts:
                # Create version control -> account directory
                account_path = vc_path / account.name
                account_path.mkdir(parents=True, exist_ok=True)
                print(f"[INFO]: Created directory: [{account_path}]")

                # Generate SSH key for this vcs/account
                generate_ssh_keys(ssh_account_path=account_path, account=account.name)

        except Exception as e:
            print(f"[ERROR]: Failed to create directory structure for {vc.name}: {str(e)}")

def generate_ssh_keys(ssh_account_path: Path, account: str) -> None:
    """
    Generates SSH keys for an account using ssh-keygen

    Args:
        ssh_account_path (Path): Path object for the account's .ssh directory
        account (str): Account name used for the key filename and comment

    Example paths:
        Windows: %USERPROFILE%\\.ssh\\github.com\\john-doe\\john-doe_rsa
        Unix: ~/.ssh/github.com/john-doe/john-doe_rsa

    SSH-keygen options:
        -t  type    Supported types: rsa, dsa, ecdsa, ed25519 (DEFAULT: rsa)
        -b  bits    Key size: 1024, 2048, 4096
        -C  comment User identifier/email
        -f  file    Output filename
    """
    key_filename = f"{account}_rsa"
    key_path = ssh_account_path / key_filename

    command = [
        "ssh-keygen",
        "-t", "rsa",
        "-b", "4096",
        "-f", str(key_path),  # ssh-keygen expects string path
        "-C", account
    ]

    try:
        subprocess.run(command, shell=True, check=True)
        print(f"[INFO]: Generated SSH key: [{key_path}]")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR]: Failed to create SSH key with command: {' '.join(command)}")
        print(f"[ERROR]: {str(e)}")

def create_ssh_config_file(ssh_dir_path: Path) -> Path:
    """
    Creates the `config` file within the `/.ssh/` directory and applies chmod 0600

    Args:
        ssh_dir_path (Path): Path object for the .ssh directory

    Returns:
        Path: Path object for the created config file

    Example paths:
        Windows: %USERPROFILE%\\.ssh\\config
        Unix: ~/.ssh/config
    """
    config_path = ssh_dir_path / "config"

    try:
        if not config_path.exists():
            # Create empty config file
            config_path.touch(mode=0o600)
            print(f"[INFO]: Created file: [{config_path}]")
        else:
            print(f"[INFO]: Config file already exists: [{config_path}]")

            # Ensure correct permissions even if file exists
            config_path.chmod(0o600)

        return config_path

    except Exception as e:
        print(f"[ERROR]: Failed to create/configure SSH config file: {str(e)}")
        raise  # Re-raise exception after logging


def load_template(path: str):
    """Loads a template from a file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template file [{path}] not found.")
    with open(SSH_CONFIG_FILE_NAME, "r") as file:
        return file.read()

def add_ssh_config(username: str, vcs: str, operating_system: str):
    """Adds an SSH config entry using a template file, avoiding duplicates."""

    # Load template
    template: str = load_template('CHANGE_ME_DIR')

    # Determine UseKeychain setting
    use_keychain = (
        "UseKeychain yes" if operating_system in ["mac", "linux"] else ""
    )

    # Populate the template
    config_block = template.format(
        USERNAME=username, VCS=vcs, USE_KEYCHAIN=use_keychain
    ).strip()

    # Read existing config
    if os.path.exists(SSH_CONFIG_PATH):
        with open(SSH_CONFIG_PATH, "r") as file:
            config_data = file.read()
    else:
        config_data = ""

    # Check for duplicate entry
    if f"Host {username}.{vcs}" in config_data:
        print(f"Entry for {username}.{vcs} already exists. Skipping.")
        return

    # Append new block
    with open(SSH_CONFIG_PATH, "a") as file:
        file.write("\n\n" + config_block)  # Ensure spacing

    print(f"Added SSH config for {username}.{vcs}")

def check_gitconfig_entry_exists(config_content: str, vcs_name: str, username: str, org_name: str = None) -> bool:
    """
    Checks if a gitconfig entry already exists.
    
    Args:
        config_content (str): Existing gitconfig content
        vcs_name (str): Name of the version control system
        username (str): Account username
        org_name (str, optional): Organization name if applicable
    
    Returns:
        bool: True if entry exists, False otherwise
    """
    # Create pattern to match based on account type
    if org_name:
        pattern = f"gitdir:~/{SOURCE_DIR_NAME}/{vcs_name}/{org_name}/{username}/"
    else:
        pattern = f"gitdir:~/{SOURCE_DIR_NAME}/{vcs_name}/{username}/"
    
    return pattern in config_content

def check_account_gitconfig_entry_exists(gitconfig_content: str, vcs_name: str, username: str, org_name: str = None) -> bool:
    """
    Checks if an account-level gitconfig entry already exists.
    
    Args:
        gitconfig_content (str): Existing gitconfig content
        vcs_name (str): Name of the version control system
        username (str): Account username
        org_name (str, optional): Organization name if applicable
    
    Returns:
        bool: True if entry exists, False otherwise
    """
    # Check for user section and matching configuration
    if org_name:
        pattern = f"email = {username}@{org_name}.com"
    elif "github" in vcs_name:
        pattern = f"name = {username}"
    else:
        pattern = f"name = {username}"
    
    return pattern in gitconfig_content

def create_account_level_gitconfig(account_path: Path, account_name: str, vcs_name: str, org_name: str = None) -> None:
    """Creates or updates account-level .gitconfig files using standardized templates."""
    gitconfig_path = account_path / GC_FILE_NAME
    template_path = Path(TEMPLATES_DIR_NAME) / GC_TEMPLATES_DIR_NAME / GC_ACCOUNT_DIR_NAME / vcs_name / GC_USER_FILE_NAME

    try:
        # Check if template exists
        if not template_path.exists():
            print(f"[WARNING]: No account template found for [{vcs_name}]")
            return

        # Check if gitconfig already exists and read content
        existing_content = ""
        if gitconfig_path.exists():
            with open(gitconfig_path, 'r') as f:
                existing_content = f.read()
            
            # Check for duplicate entry
            if check_account_gitconfig_entry_exists(existing_content, vcs_name, account_name, org_name):
                print(f"[INFO]: Account-level gitconfig entry already exists for [{account_name}] at [{gitconfig_path}]")
                return
            print(f"[INFO]: Updating existing gitconfig at [{gitconfig_path}]")
        else:
            print(f"[INFO]: Creating new gitconfig at [{gitconfig_path}]")

        # Read template content
        with open(template_path, 'r') as f:
            template_content = f.read()

        # Prepare template variables
        template_vars = {
            "USERNAME": account_name,
            "VCS": vcs_name
        }

        # Add specific variables based on VCS type
        if "github" in vcs_name:
            template_vars["GITHUB_ID"] = get_github_id(account_name)
        elif "azure" in vcs_name and org_name:
            template_vars["ORGANISATION"] = org_name
        elif any(vcs in vcs_name for vcs in ["gitlab", "sourceforge", "bitbucket"]):
            print(f"[WARNING]: Unsupported VCS [{vcs_name}]")
            return

        # Format template with variables
        new_config_content = template_content.format(**template_vars)

        # If there's existing content, append new content
        final_content = existing_content + "\n\n" + new_config_content if existing_content else new_config_content

        # Write the gitconfig file
        with open(gitconfig_path, 'w') as f:
            f.write(final_content)

        print(f"[INFO]: {'Updated' if existing_content else 'Created'} account-level gitconfig at [{gitconfig_path}]")

    except Exception as e:
        print(f"[ERROR]: Failed to create/update account-level gitconfig: {str(e)}")

def create_top_level_gitconfig(home_dir: Path, vcs_list: list[VersionControl]) -> None:
    """Creates or updates the top-level .gitconfig file using standardized templates."""
    gitconfig_path = home_dir / GC_FILE_NAME
    template_dir = Path(TEMPLATES_DIR_NAME) / GC_TEMPLATES_DIR_NAME / GC_TOP_DIR_NAME

    try:
        # Read existing config if it exists
        existing_content = ""
        if gitconfig_path.exists():
            with open(gitconfig_path, 'r') as f:
                existing_content = f.read()

        # Start with default configuration if file doesn't exist
        config_content = existing_content if existing_content else ""
        if not config_content:
            with open(template_dir / GC_DEFAULT_FILE_NAME, 'r') as f:
                config_content = f.read() + "\n\n"

        # Track if any new entries were added
        new_entries_added = False

        # Process each VCS system
        for vcs in vcs_list:
            vcs_template_dir = template_dir / vcs.name

            # Handle organizational accounts
            if vcs.organisations:
                org_template_path = vcs_template_dir / GC_ORGANISATION_FILE_NAME
                if org_template_path.exists():
                    with open(org_template_path, 'r') as f:
                        org_template = f.read()

                    for org in vcs.organisations:
                        for account in org.accounts:
                            if not check_gitconfig_entry_exists(config_content, vcs.name, account.name, org.name):
                                config_content += org_template.format(
                                    SRC_DIR=SOURCE_DIR_NAME,
                                    VCS=vcs.name,
                                    ORGANISATION=org.name,
                                    USERNAME=account.name
                                ) + "\n\n"
                                new_entries_added = True
                                print(f"[INFO]: Added organization config for [{account.name}] in [{org.name}] at [{vcs.name}]")
                            else:
                                print(f"[INFO]: Config already exists for [{account.name}] in [{org.name}] at [{vcs.name}]")

            # Handle standard accounts
            if vcs.accounts:
                std_template_path = vcs_template_dir / GC_STANDARD_FILE_NAME
                if std_template_path.exists():
                    with open(std_template_path, 'r') as f:
                        std_template = f.read()

                    for account in vcs.accounts:
                        if not check_gitconfig_entry_exists(config_content, vcs.name, account.name):
                            config_content += std_template.format(
                                SRC_DIR=SOURCE_DIR_NAME,
                                VCS=vcs.name,
                                USERNAME=account.name
                            ) + "\n\n"
                            new_entries_added = True
                            print(f"[INFO]: Added standard config for [{account.name}] at [{vcs.name}]")
                        else:
                            print(f"[INFO]: Config already exists for [{account.name}] at [{vcs.name}]")

        # Only write if new entries were added
        if new_entries_added:
            with open(gitconfig_path, 'w') as f:
                f.write(config_content)
            gitconfig_path.chmod(0o644)
            print(f"[INFO]: Updated top-level gitconfig at [{gitconfig_path}]")
        else:
            print("[INFO]: No new entries to add to gitconfig")

    except Exception as e:
        print(f"[ERROR]: Failed to create/update top-level gitconfig: {str(e)}")
def setup_git_config(home_dir: Path, src_dir: Path, vcs_list: list[VersionControl]) -> None:
    """
    Main function to set up all git configurations.
    
    Args:
        home_dir (Path): Path to user's home directory
        src_dir (Path): Path to source directory
        vcs_list (list[VersionControl]): List of configured VCS systems
    """
    try:
        # Create top-level .gitconfig
        create_top_level_gitconfig(home_dir, vcs_list)

        # Create account-level .gitconfig files
        for vcs in vcs_list:
            # Handle organizational accounts
            for org in vcs.organisations:
                for account in org.accounts:
                    account_path = src_dir / vcs.name / org.name / account.name
                    if account_path.exists():
                        create_account_level_gitconfig(
                            account_path, 
                            account.name, 
                            vcs.name, 
                            org.name
                        )
                    else:
                        print(f"[WARNING]: Account directory not found at [{account_path}]")

            # Handle standard accounts
            for account in vcs.accounts:
                account_path = src_dir / vcs.name / account.name
                if account_path.exists():
                    create_account_level_gitconfig(
                        account_path, 
                        account.name, 
                        vcs.name
                    )
                else:
                    print(f"[WARNING]: Account directory not found at [{account_path}]")

    except Exception as e:
        print(f"[ERROR]: Failed to setup git configurations: {str(e)}")
        
def generate_mock_data() -> list[VersionControl]:
    return [
        VersionControl(
            name="bitbucket.org",
            organisations=[Organisation(name="org1", accounts=[Account(name="org-acc1")])],
            accounts=[]
        ),
        VersionControl(
            name="dev.azure.com",
            organisations=[
                Organisation(name="lodlaw", accounts=[Account(name="colten-lod")]),
                Organisation(name="consilio", accounts=[Account(name="colten-cons")])
            ],
            accounts=[]
        ),
        VersionControl(
            name="github.com",
            organisations=[],
            accounts=[Account(name="pnc-nz"), Account(name="prayer-clan")]
        )
    ]

def run():
    version_controls = []


    DEBUG_TEST_MODE = True
    if DEBUG_TEST_MODE is True:
        src_path = ''
        ssh_dir_path = ''

        # CREATE: /src/
        if user_input("Create ~/src/ directory?\n> ", valid_responses=["y", "n"]) == "y":
            src_path = create_src_directory(HOME_DIR_PATH, SOURCE_DIR_NAME)
            print(src_path)

        # CREATE /src/.ssh/
        if user_input("Create ~/.ssh/ directory?\n> ", valid_responses=["y", "n"]) == "y":
            ssh_dir_path = create_ssh_directory(HOME_DIR_PATH, SSH_DIR_NAME)
            print(ssh_dir_path)


        # CREATE /src/.ssh/config
        if user_input("Create ~/src/.ssh/config file?\n> ", valid_responses=["y", "n"]) == "y":
            create_ssh_config_file(SSH_DIR_PATH)


    # GENERATE VCS HIERARCHY
    # generated_vcs = generate_vcs_hierarchy()

    # GENERATE GIT CONFIGs
    # setup_git_config(HOME_DIR_PATH, SOURCE_DIR_PATH, generated_vcs)

    # GENERATE MOCK DATA
    generated_vcs = generate_mock_data()

    for vcs in generated_vcs:
        vcs.debug()

    # GENERATE DIRECTORIES
    create_vcs_directories(SOURCE_DIR_PATH, generated_vcs)



    if version_controls.__len__() < 1:
        return



    # /.ssh/{vcs}/{organisation}/{user}
    # print("Create VCS account directories?")
    # if convert_yes_no_to_bool(user_input("[Y]es or [N]o\n> ")):
    #     create_ssh_account_directories(ssh_dir_path, version_controls)

    # /src/{vcs}/{user}

    # Example usage of add_ssh_config
    # add_ssh_config("myuser", "github.com", "mac")


# Run
if __name__ == "__main__":
    run()
