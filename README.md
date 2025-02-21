# Development Environment Builder

A Python-based CLI tool that automates the setup of development environments across multiple version control systems.

## Features

- Creates standardized directory structures for different VCS providers
- Configures SSH keys and config files
- Sets up Git configurations at both global and repository levels
- Supports multiple accounts and organizations
- Works across different operating systems (Windows, macOS, Linux)

## Supported Version Control Systems

- GitHub
- Azure DevOps
- Bitbucket
- GitLab
- SourceForge

## Directory Structure

The tool creates the following directory structure:

```text
~/
├── src/
│   ├── github.com/
│   │   ├── personal-account/
│   │   └── organization-name/
│   │       └── org-account/
│   └── dev.azure.com/
│       └── organization-name/
│           └── org-account/
└── .ssh/
    ├── config
    └── github.com/
        └── account-name/
            ├── account-name_rsa
            └── account-name_rsa.pub
```

## Requirements

- Python 3.9+
- SSH client (`ssh-keygen` command available)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dev-environment-builder.git
cd dev-environment-builder
```

2. (Optional) Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows
```

## Usage

1. Run the script:
```bash
python profile_setup.py
```

2. Follow the interactive prompts to:
   - Configure VCS providers
   - Add organizations
   - Add accounts
   - Generate SSH keys
   - Set up Git configurations

## Configuration Files

### SSH Config Template
Located at `templates/ssh/config`
- Configures SSH settings for each VCS/account combination

### Git Config Templates
Located in `templates/gitconfig/`
- `top/` - Global Git configurations
- `account/` - Repository-level Git configurations

## File Permissions

The tool automatically sets appropriate permissions:
- SSH private keys: `600` (owner read/write only)
- SSH public keys: `644` (owner read/write, others read)
- SSH config: `600`
- Git config: `644`

## Development

### Project Structure
```text
dev-environment-builder/
├── profile_setup.py
├── templates/
│   ├── gitconfig/
│   │   ├── account/
│   │   └── top/
│   └── ssh/
└── README.md
```

### Adding New VCS Support

1. Add the VCS name to `VERSION_CONTROL_SYSTEMS`
2. Create appropriate templates in:
   - `templates/gitconfig/account/{vcs}/user`
   - `templates/gitconfig/top/{vcs}/standard`
   - `templates/gitconfig/top/{vcs}/organisation`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)
