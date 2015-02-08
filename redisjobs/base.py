from functools import partial
import redis


class StrictRedis(redis.StrictRedis):
    def __init__(self, *vargs, **kwargs):
        kwargs['decode_responses'] = True
        super(StrictRedis, self).__init__(*vargs, **kwargs)
        commands = self.hgetall('commands')

        for command, sha in commands.items():
            method = partial(self.evalsha, sha)
            setattr(self, command, method)
