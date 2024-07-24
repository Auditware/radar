# How it Works

The whole project is layed out as a [docker-compose.yml](https://github.com/Auditware/radar/blob/main/docker-compose.yml) specification, and the code is designed to run in docker instances.

Since the tool runs from a local/personal computer perspective, [radar.sh](https://github.com/Auditware/radar/blob/main/radar.sh) is the layer that the generic user interacts with.

When a contract path is passed to radar, it performs these high level operations:
1. Copy the contents of the contract to the execution containers
2. Parses the AST of the contract into a unified JSON AST file
3. Concurrently executes the rules within each template supplied against the AST
4. Copy results back to the personal computer