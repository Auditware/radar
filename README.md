# radar

A static analysis tool for anchor rust programs.

## Installation

1) Install and start docker

2) Install git

3) Install radar either from install script or from source

```bash
curl -L https://raw.githubusercontent.com/Auditware/radar/main/install-radar.sh | bash
radar -h
```

OR

```bash
git clone https://github.com/Auditware/radar.git
cd radar
./radar.sh -h
```

## Usage
```bash
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