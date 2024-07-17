# radar

A static analysis tool for anchor rust programs.

## Installation

1) Install and start docker

2) In first use, the `radar.sh` script will build the docker-compose.yml specifications.

```bash
git clone https://github.com/Auditware/radar.git
cd radar
./radar.sh -p <contract>
```

## Usage
```bash
./radar.sh -h

Usage: ./radar.sh [-p <path> [-s <source_directory_or_file>] [-t <templates_directory>]] [-d]
Options:
  -p, --path       Path to the contract on the host.
  -s, --source     Specific source within the contract path (optional) (default - project root).
  -t, --templates  Path to the templates directory (optional) (default - builtin_templates folder).
  -d, --down       Shut down radar containers.
  -h, --help       Help message.
```