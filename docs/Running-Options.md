# Running Options

All the different possible ways to run radar, covering all use cases.

- For demo purposes `rustic_megaproject` will be the root directory containing the code to be scanned for issues via radar.
- For demo purposes, the running user starts the terminal from his Desktop, and `rustic_megaproject` was cloned there.

## 1. 💻 Run from terminal

Most common use case.

#### 1.1. Run on current working directory

Install: `curl -L https://raw.githubusercontent.com/Auditware/radar/main/install-radar.sh | bash`

```bash
cd rustic_megaproject && radar -p .
```

#### 1.2. Run on a target path (e.g. one directory back)

Install: `curl -L https://raw.githubusercontent.com/Auditware/radar/main/install-radar.sh | bash`

```bash
cd random_unrelated_dir && radar -p ../rustic_megaproject
```

## 2. 🧑‍💻 Run from source code

Adding `--dev` flag tells radar to work off the radar repo to build the images, rather than pulling the last deployed images from github container registry.

Use this if you made local changes to the source code.

Clone: `git clone https://github.com/auditware/radar.git`

```bash
cd radar && ./radar --dev -p ../rustic_megaproject
```

## 3. 🔂 Run as a CI workflow

On your github repo that you want scanned, create `.github/workflows/radar.yml` and place this workflow configuration to run radar as a CI job on every push.

Results will appear on github code scanning.

```yaml
name: radar Static Analysis
on: [push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: "recursive"

      - name: Run radar
        id: radar
        uses: auditware/radar-action@main
        with:
          path: "."
          ignore: "low"

      - name: Upload SARIF file
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: output.sarif
```

## 4. 🔙 Run as a pre-commit hook

If you're using [pre-commit](https://pre-commit.com), you could also add radar to your workflow by adding radar to your `.pre-commit-config.yaml` configuration like so:

```yaml
repos:
- repo: local
  hooks:
    - id: run-radar
      name: Run radar Static Analysis
      entry: radar -p . --ignore low
      language: system
      stages: [commit]
      pass_filenames: false
      always_run: true
```