import redis
from functools import partial


class StrictRedis(redis.StrictRedis):
    def __init__(self, *vargs, **kwargs):
        super(StrictRedis, self).__init__(*vargs, **kwargs)
        commands = self.hgetall('commands')

        for command, sha in commands.items():
            method = partial(self.evalsha, sha)
            setattr(self, command, method)
