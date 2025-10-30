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
./radar -h
```

The first scan will take a while, as radar collects and builds the necessary docker images from the [docker-compose.yml](https://github.com/auditware/radar/blob/main/docker-compose.yml) specifications. Unless you are changing the source of the project, or builtin tempaltes, rebuilding won't be necessary, and instead just turn the containers on/off.

## Usage

```
radar -h

Usage: ./radar [-p <path> [-s <source_directory_or_file>] [-t <templates_directory>]] [-i <severities_to_ignore>] [-o <output_directory>] [-a] [-d] [--dev] [-ss] [--no-update] [-h]
Options:
  -p, --path            Path to the target contract on the local filesystem                                           (required)
  -s, --source          Specific source/scope within the contract path                                                (optional) (default - project root)
  -t, --templates       Path to the templates directory                                                               (optional) (default - builtin_templates folder)
  -i, --ignore          Comma-separated severities to ignore in the scan (e.g. low,medium)                            (optional)
  -o, --output          Results output file path (output type controlled by extension e.g. .json/.md/.sarif)          (optional) (default - current directory)
  -a, --ast             Additionally output the scanned contract's parsed AST                                         (optional)
  -d, --dev             Use development docker-compose file for local builds and enable debug output                  (optional)
  -ss, --store-sarif    Store and accumulate SARIF results from previous runs                                         (optional) (default - clean slate)
  -nu, --no-update      Skip automatic update check for Docker images                                                 (optional)
  -h, --help            Show this help message                                                                        (optional)
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

To explore more running options, see [All the ways to run radar](https://github.com/auditware/radar/wiki/Running-Options).

To create custom logical rules of your own, see [How to write templates](https://github.com/auditware/radar/wiki/How-to-Write-Templates).
