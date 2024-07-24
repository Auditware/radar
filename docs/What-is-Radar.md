# What is radar

radar is a rule-based static analyzer for Anchor Rust Smart Contracts, designed to run from a terminal on anchor smart contracts downloaded locally.

It's written for smart contract develoeprs and security auditors, to aid in locating security vulnerabilities, by programmatically searching the analyzed codebase for patterns and heuristics.

As a key feature, radar exposes a pythonic querying mechanism that can empower creating new rules, whether for personal analysis or for community sharing. Each rule is shipped as a template file containing informational data on the vulnerability, and the logical rule to detect it.