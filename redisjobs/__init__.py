import functools
import time
import json

from . import base
from . import utils


PARSERS = {
    'json': json.loads, 
    'plain': utils.identity, 
}


def parse(s, format='plain'):
    if isinstance(s, basestring):
        if format in PARSERS:
            return PARSERS[format](s)
        else:
            raise KeyError()
    else:
        return s


class Queue(object):
    def __init__(self, name, board):
        self.board = board
        self.client = board.client
        self.name = name
        self.key = "{queue}:{name}".format(
            queue=board.keys['queue'], name=name)

    def pop(self, format='plain'):
        meta = self.client.jpop(1, self.key)
        return parse(meta, format)

    def listen(self, listener, format='plain'):        
        def communicate():
            popped = self.pop(format)
            if popped:
                listener(popped)

        utils.forever(communicate)


class Board(object):
    def __init__(self, name='jobs', *vargs, **kwargs):
        self.name = name
        self.key = name
        self.keys = {
            'board': name, 
            'schedule': name + ":schedule", 
            'queue': name + ":queue", 
            'registry': name + ":runners", 
        }
        self.client = base.StrictRedis(*vargs, **kwargs)

    def put(self, id, runner, payload, **options):
        now = int(time.time())
        if options.get('update', True):
            setter = self.client.jset
        else:
            setter = self.client.jsetnx

        interval = utils.seconds(**options)

        if options.get('repeat'):
            raise NotImplementedError()
        elif options.get('duration'):
            options.setdefault('start', now)
            options['stop'] = options['start'] + options['duration']

        # in Redis, everything is a string, so passing on a None argument
        # leads to all sorts of weirdness; instead, we have sensible 
        # defaults for everything
        return setter(
            3, self.keys['board'], self.keys['schedule'], self.keys['registry'], 
            now, id, runner, payload, interval, 
            options.get('start', 0), options.get('stop', '+inf'), 
            options.get('decay', 1), options.get('step', utils.DAY), 
            )

    def create(self, id, runner, payload, **options):
        options['update'] = False
        return self.put(id, runner, payload, **options)

    def schedule(self, *vargs, **kwargs):
        raise NotImplementedError()

    def show(self, id, format='plain'):
        meta = self.client.jget(1, 'jobs', id)
        return parse(meta, format)

    def dump(self):
        runners = self.client.hgetall(self.keys['registry'])
        jobs = self.client.hgetall(self.keys['board'])
        out = {}
        out['runners'] = runners
        out['jobs'] = {}
        for job_id, serialized_meta in jobs.items():
            out['jobs'][job_id] = json.loads(serialized_meta)

        return out

    def load(self, board, update=False):
        # currently this bypasses `jset`, which makes it easier 
        # to guarantee that a loaded backup will return us to 
        # the exact state of Redis at the time of the backup,  
        # but does require care to make sure it continues to 
        # adhere to the Jobs API
        now = int(time.time())
        runners = board['runners']
        jobs = {job_id: json.dumps(meta) for job_id, meta in board['jobs'].items()}
        self.client.hmset(self.keys['registry'], runners)
        self.client.hmset(self.keys['board'], jobs)
        for job_id in board['jobs'].keys():
            self.client.jnext(2, self.keys['board'], self.keys['schedule'], now, job_id)
        return self.client.hlen(self.keys['board'])

    def count(self):
        runners = self.client.hgetall(self.keys['registry'])
        queues = [self.get_queue(runner).key for runner in runners.keys()]
        n_keys = 3 + len(queues)
        counts = self.client.jcount(n_keys, 
            self.keys['board'], self.keys['schedule'], self.keys['registry'], queues)
        return json.loads(counts)   

    def remove(self, id):
        return self.client.jdel(2, self.keys.board, self.keys.schedule, id)

    def register(self, runner, command):
        raise NotImplementedError()

    def get_queue(self, name):
        return Queue(name, self)

    def tick(self, now=None):
        now = now or int(time.time())
        runners = self.client.hgetall(self.keys['registry'])
        queues = [self.get_queue(runner).key for runner in runners.keys()]

        n_queues = len(queues)
        n_keys = n_queues + 2

        arguments = queues + [now]

        return self.client.jtick(
            n_keys, self.keys['board'], self.keys['schedule'], 
            arguments
            )

    def respond(self, queue, fn):
        queue = self.get_queue(queue)
        print(queue.key)
        queue.listen(fn, 'json')
