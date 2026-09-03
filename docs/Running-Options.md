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
## 5. 🚦 Exit codes, gating, and incremental adoption

radar sets its exit code so a pipeline can gate on it:

| Code | Meaning |
|------|---------|
| `0`  | Clean - no findings at or above the fail-on threshold |
| `1`  | Findings at or above the fail-on threshold |
| `2`  | Operational error (parse/scan failure, or a template errored out) |

Control what fails the build with `--fail-on` (default `low` - any finding):

```bash
radar -p . --fail-on high     # only high/critical findings fail
radar -p . --fail-on none     # report only, never fail on findings
```

### Baseline

Accept everything present today and fail only on new findings:

```bash
radar -p . --baseline .radar-baseline.json --write-baseline   # snapshot
radar -p . --baseline .radar-baseline.json                    # gate on new findings only
```

The baseline fingerprints each finding by rule and project-relative location.
Commit the file so every developer and the CI share the same accepted set.

### Inline suppression

Silence a specific line in the source:

```rust
// radar-disable-next-line Missing_Signer_Check
pub struct UpdateAuthority<'info> { /* ... */ }

let x = risky(); // radar-disable-line
```

A bare marker suppresses any rule on the target line; listing rule ids (space or
comma separated) suppresses only those. Rule ids match the finding name loosely,
so `Missing_Signer_Check`, `missing-signer-check`, and `Missing Signer Check` all
work.
