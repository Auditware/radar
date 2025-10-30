# Technical Decisions

In this page we share about some of our decisions and unique paths while developing radar. See [How radar works](https://github.com/auditware/radar/wiki/How-it-Works) for a more high level explanation.

<br>

## Technological Stack
##### | Why docker? |

The project is a dockerized Django / Celery / Postgres environment, wrapped within a CLI tool look and feel.

We took this approach of a docker-only CLI tool to have a stable setup across different operating system, without the necessary lift to support multiple operating systems and their prerequisites. This allowed us to allocate more time into other prioritized parts of the project.

Most of the logic occurs within the django container (`api`), parsing the AST and managing task executions by running them concurrently using `Celery` tasks.

[docker-compose.yml](https://github.com/auditware/radar/blob/main/docker-compose.yml) specifies the radar containers, and a bash script [radar](https://github.com/auditware/radar/blob/main/radar) is used as a convinent user interaction layer.

<br>

## AST as the base of the analysis
##### | What data are the rules running on? | Why not regex? | Why not LLVM-IR? |

To get a program (or specifically our python queries) to understand a code you have a couple of strategies you can consider.

- Regex or any grep-based strategy is not a fit for our scalability considerations
- Solidity static analysis tooling almost exclusively are using `solc` (or an SDK running solc under the hood), which supports returning an AST of the contract stdio. Rust-based contracts however are a bit of a different story (Anchor for example does not provide the same AST output generation out of the box).
- We also considered writing a full lexer/parser (e.g. using libraries like https://github.com/lark-parser/lark) and to use it to generate an AST ourselves, but the necessary definitions and support requirements for this would've been too demanding for our use case.

Another approach was to expose the template rules to LLVM-IR, with the downside of much less readable data for the query writers.

For example, for a Solana smart contract to be executed it is first compiled from rust to LLVM-IR ([LLVM](https://llvm.org/docs/LangRef.html) Intermediate Representation), then to BPF/SBF (Berkeley Packet Filter/Solana Binary Format), and then the bytecode is stored on the blockchain. the validators compile the SBF to instructions per the hardware and so on.

In theory the process would be first parsing the rust code into an AST and then to LLVM-IR, something like this

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

↓

```json
{
  "type": "Function",
  "name": "add",
  "parameters": [
    {
      "name": "a",
      "type": "i32"
    },
    {
      "name": "b",
      "type": "i32"
    }
  ],
  "returnType": "i32",
  "body": {
    "type": "BinaryOperation",
    "operator": "+",
    "left": {
      "type": "Identifier",
      "name": "a"
    },
    "right": {
      "type": "Identifier",
      "name": "b"
    }
  }
}
```

↓

```llvm
define i32 @add(i32 %a, i32 %b) {
entry:
  %1 = add i32 %a, %b
  ret i32 %1
}
```

However while we explored this approach we came to the conclusion that most of the potential future template authors or contributors would prefer working on the AST itself, as it's more intuitive to read and compare to the code itself than LLVM-IR.

We ended up using existing libraries to parse the rust AST from source, and unified the results logically to have one single AST JSON with the data necessary to understand the contract.

<br>

## Templates and Rules
##### | What are radar rules? | Why python? |

Often times when templates are aimed to be generically easy to understand, developers create a DSL (Domain Specific Language) with very high abstractions around the inner operations, to allow a quick and smooth experience when writing new templates.

Such a DSL can look something like this (example found from google)

```yaml
And:
  - hostname:
      equals: example.com
  - Or:
      - url:
          starts: /some_handler
      - url:
          starts: /xyz
  - Not:
      url:
        starts: /some_handler_internal
  - user_agent:
      contains: Firefox
  - ip:
      starts: "::ffff:"
```

Then the DSL is translated on the backend to operations to be performed.

That approach is very organized, but has some disadvantages.

One is the order of cases that needs to be supported to provide a strong expressive ability for the author, and the other one is that in complex operations occurring as the tool grows, the way tp express very complicated operations leaves us with a barely readable template.

To overcome this, we chose to use Python as the DSL / rule language

```python
# Iterate over `ast` which is auto-injected by the rule engine
# nodes are AST nodes representing singular code structure
for source, nodes in ast:
    try:
        # `find_chained_calls` is an example of a utility baked into the engine to do complex AST lookups easily (basically english)
        # `exit_on_none()` says - if you didn't find anything, just jump to the next node
        cpi_groups = nodes.find_chained_calls("solana_program", "program", "invoke").exit_on_none()

        # Another call, exit if the comparison is existing, as this is no longer a candidate for a vulnerability in that case
        nodes.find_comparisons("spl_token", "token_program").exit_on_value()
        

        for cpi_group in cpi_groups:
            # printing nodes marks them a detected, vulnerable occurrence, tracking the code location from the ast
            print(cpi_group.first().parent.to_result())
    except:
        # On fail, move on to next silently
        continue
```

This way, template contributors can use python, which has one of the fastest programming language learning curves, to express the logic of a security issue or insights that can occur in the smart contract.

On top of that we add some "magic" around the rule, for example, to have it already hold the parsed `ast` data without writing anything. we also added functionalities and iterators to be able to abstractly express the analysis.

This gives a lot of power to the rule writer to use for loops, nested for loops, try/except blocks, and much more, out of the box.
