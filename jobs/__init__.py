import functools
import time
import base


PARSERS = {
    'json': json.loads, 
    'plain': utils.identity, 
}


def parse_job(s, format='plain'):
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
            queue=board.keys.queue, name=name)

    def pop(self, format='plain'):
        meta = self.client.jpop(1, self.key)
        return parse_format(meta, format)

    def listen(self, *vargs):
        if len(vargs) == 2:
            format, listener = vargs
        elif len(vargs) == 1:
            format = 'plain'
            listener = vargs[0]
        else:
            raise KeyError()
        
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

    def put(self, id, runner, payload, schedule, update=True):
        now = time.time()
        if update is True:
            setter = self.client.jset
        else:
            setter = self.client.jsetnx

        interval = utils.seconds(schedule)

        if schedule['repeat']:
            raise NotImplementedError()
        elif schedule['duration']:
            schedule.setdefault('start', now)
            schedule['stop'] = schedule['start'] + schedule['duration']

        return setter(
            3, self.keys['board'], self.keys['schedule'], self.keys['registry'], 
            now, id, runner, payload, interval, 
            schedule.get('start'), schedule.get('stop'), 
            schedule.get('lambda'), schedule.get('step'), 
            )

    def create(self, id, runner, payload, schedule):
        return self.put(id, runner, payload, schedule, update=False)

    def schedule(self, *vargs, **kwargs):
        raise NotImplementedError()

    @parse
    def show(self, id, format='plain'):
        meta = self.client.jget(1, 'jobs', id)
        return parse_job(meta, format)

    def dump(self):
        return self.client.hgetall('jobs')

    def remove(self, id):
        return self.client.jdel(2, self.keys.board, self.keys.schedule, id)

    def register(self, runner, command):
        raise NotImplementedError()

    def get_queue(self, name):
        return Queue(name, self)

    def tick(self, now=None):
        now = now or int(time.time())
        runners = self.client.hgetall(self.keys['registry'])
        queues = []
        for runner, command in runners.items():
            queue = self.get_queue(runner)
            queues.append(queue.key)

        n_queues = len(queues)
        n_keys = n_queues + 2

        arguments = queues + [now]

        return self.client.jtick(
            n_keys, self.keys['board'], self.keys['schedule'], 
            arguments
            )

    def respond(self, queue, fn):
        queue = self.get_queue(queue)
        queue.listen(fn)
