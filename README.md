# Jobs

This is a Python client library for interacting with the [Jobs](https://github.com/debrouwere/jobs) scheduler.

Install with pip:

```shell
pip install redisjobs
```

```python
import redisjobs as jobs

# if Redis is not running on your local machine, 
# specify Redis host and port, otherwise you 
# can initialize the object without arguments
board = jobs.Board(host='127.0.0.1', port=6379)
schedule = {'minutes': 5}
board.put('my job', 'shell', 'echo "Hello world!"', schedule)
print board.get('my job')
```

Take a look at `jobs/__init__.py` for more information.