import redis

from . import BaseStateHandler


class RedisStateHandler(BaseStateHandler):
    def load_state(self):
        r, prefix = self._get_redis_info()
        state = r.get(prefix + ':state')
        return state

    def save_state(self, state):
        r, prefix = self._get_redis_info()
        r.set(prefix + ':state', state)

    def _get_redis_info(self):
        r = redis.StrictRedis(host=self.config['host'], port=self.config['port'])
        prefix = 'slack'
        if 'prefix' in self.config:
            prefix = self.config['prefix']
        return r, prefix
