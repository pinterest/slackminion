import redis

from . import BaseStateHandler


class RedisStateHandler(BaseStateHandler):
    def load_state(self):
        r = redis.StrictRedis(host=self.config['host'], port=self.config['port'])
        prefix = 'slack'
        if 'prefix' in self.config:
            prefix = self.config['prefix']
        state = r.get(prefix + ':state')
        return state

    def save_state(self, state):
        r = redis.StrictRedis(host=self.config['host'], port=self.config['port'])
        prefix = 'slack'
        if 'prefix' in self.config:
            prefix = self.config['prefix']
        r.set(prefix + ':state', state)
