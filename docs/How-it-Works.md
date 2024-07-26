# How it Works

The project is layed out as a [docker-compose.yml](https://github.com/auditware/radar/blob/main/docker-compose.yml) specification, and the code is designed to run in docker instances.

Since the tool runs from a local/personal computer perspective, [radar.sh](https://github.com/auditware/radar/blob/main/radar.sh) is the layer that the generic user interacts with.

These are the containers being managed by radar:

`radar` - can be thought of as the client, performs basic operations like argument parsing and copying

`api` - django based backend that performs the AST generation, as wall as disatching of workers

`postgres` - database for the api container

`celeryworker` - instance to run api-initiated celery tasks, mostly template execution

`rabbitmq` - message queue for the api and celeryworker containers

When a contract path is passed to radar, it performs these high level operations:

1. Copy the contents of the contract to the execution containers
2. Parses the AST of the contract into a unified JSON AST file
3. Concurrently executes the rules within each template supplied against the AST
4. Copy results back to the personal computer

[How to use radar](https://github.com/auditware/radar/wiki/How-to-Use)
