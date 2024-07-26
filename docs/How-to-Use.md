# How to Use

## Installation

After ensuring Docker is up and running on your system, install radar using curl:

```bash
curl -L https://raw.githubusercontent.com/Auditware/radar/main/install-radar.sh | bash
radar -h
```

Alternative - clone the repo:

```bash
git clone https://github.com/auditware/radar.git
cd radar
./radar.sh -h
```

The first scan will take a while, as radar collects and builds the necessary docker images from the [docker-compose.yml](https://github.com/auditware/radar/blob/main/docker-compose.yml) specifications. Unless you are changing the source of the project, or builtin tempaltes, rebuilding won't be necessary, and instead just turn the containers on/off.

## Usage

```
radar -h

Usage: radar [-p <path> [-s <source_directory_or_file>] [-t <templates_directory>]] [-d]
Options:
  -p, --path       Path to the contract on the host
  -s, --source     Specific source within the contract path (optional) (default - project root)
  -t, --templates  Path to the templates directory (optional) (default - builtin_templates folder)
  -a, --ast        Copy generated AST alongside the report
  -d, --down       Shut down radar containers
  -h, --help       Help message
```

The simplest way to start a scan is by running `radar -p <path-to-your-contract-root-folder>`.

So for example:

```bash
git clone https://github.com/coral-xyz/sealevel-attacks
radar -p sealevel-attacks
```

In some cases (such as the case above) the scanned repo has multiple programs. To work on a specific scope use the source argument as such:

```bash
radar -p sealevel-attacks -s programs/5-arbitrary-cpi
```

By default, only templates within the [`api/builtin_templates/`] folder will run on the contracts. To run custom templates, use the `-t` argument:

```bash
radar -p sealevel-attacks -t my_yaml_templates_folder
```

To create custom logical rules of your own, see [How to write templates](https://github.com/auditware/radar/wiki/How-to-Write-Templates).
