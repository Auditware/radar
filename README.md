<p align="center">
  <img src="./static/radar.png" alt="radar">
</p>

<p align="center">
<img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/auditware/radar/pytest.yml">
<a href="https://github.com/auditware/radar/issues/new/choose"><img alt="Issues" title="Issues" src="https://img.shields.io/github/issues-raw/auditware/radar"></a>
<a href="https://github.com/auditware/radar/tree/main/api/builtin_templates"><img alt="Templates" title="Templates" src="https://img.shields.io/github/directory-file-count/auditware/radar/api/builtin_templates?label=templates"></a>
<a href="https://mybinder.org/v2/gh/auditware/radar/HEAD?labpath=demo.ipynb"><img alt="Radar Jupyter Notebook Rule Running Playground" title="Radar Jupyter Notebook Rule Running Playground" src="https://img.shields.io/badge/launch-notebook-blue?link=https%3A%2F%2Fimg.shields.io%2Fbadge%2Ftext&logo=jupyter"></a>
<a href="https://discord.gg/8PTTMd96p4"><img alt="Audit Wizard Discord" title="Audit Wizard Discord" src="https://img.shields.io/discord/962101971081392128.svg?logo=discord"></a>
<a href="https://github.com/auditware/radar/wiki"><img alt="Wiki" title="Wiki" src="https://img.shields.io/badge/radar-Wiki-blue"></a>
</p>

A static analysis tool for anchor rust programs.

> `radar` allows you to write, share, and utilize [templates](https://github.com/auditware/radar/tree/main/api/builtin_templates) to identify security issues in rust-based smart contracts using a powerful python based rule engine that enables automating detection of vulnerable code patterns through logical expressions.

## ⚙️ Installation

1. Install and start docker

2. Install git

3. Install radar either from install script or from source

```bash
curl -L https://raw.githubusercontent.com/auditware/radar/main/install-radar.sh | bash
radar -p <your-contract-folder>
```

OR

```bash
git clone https://github.com/auditware/radar.git
cd radar
./radar -p <your-contract-folder>
```

## 👀 First run

A good contract to first test radar against is the beautiful repo [sealevel-attacks](https://github.com/coral-xyz/sealevel-attacks)
```bash
git clone https://github.com/coral-xyz/sealevel-attacks
radar -p sealevel-attacks
```


Check out the [Wiki](https://github.com/auditware/radar/wiki) for more details.
