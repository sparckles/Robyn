## Environment Variables

There are some environment variables that Robyn looks out for. e.g. `ROBYN_URL` and `ROBYN_PORT`.

You can have a `robyn.env` file to load them automatically in your environment.

The server will check for the `robyn.env` file in the root of the project. If it is able to find one, it will parse the environment variables and the set your environment.

e.g. structure

```bash
--project/
  --robyn.env
  --index.py
  ...
```

Sample `robyn.env`

```bash
ROBYN_PORT=8080
ROBYN_URL=127.0.0.1
RANDOM_ENV=123
```

To configure the max payload size, you can set the `ROBYN_MAX_PAYLOAD_SIZE` environment variable. The default value is `1000000` bytes.

```bash
#robyn.env
ROBYN_MAX_PAYLOAD_SIZE=1000000
```

