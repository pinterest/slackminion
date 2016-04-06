import MySQLdb
import MySQLdb.cursors

from datetime import datetime

from . import BaseStateHandler


class MySQLStateHandler(BaseStateHandler):
    def load_state(self):
        conn, cursor = self._get_mysql_info()
        cursor.execute("SELECT id, data FROM state ORDER BY id DESC LIMIT 1")
        res = cursor.fetchone()
        self.log.info("Loaded state id %s", res['id'])
        state = res['data']
        cursor.close()
        return state

    def save_state(self, state):
        conn, cursor = self._get_mysql_info()
        cursor.execute(
            "INSERT INTO state (`timestamp`, `data`) VALUES (%s, %s)",
            (datetime.utcnow(), state)
        )
        conn.commit()

    def _get_mysql_info(self):
        conn = MySQLdb.connect(
            host=self.config['host'],
            user=self.config['user'],
            passwd=self.config['passwd'],
            db=self.config['db'],
            cursorclass=MySQLdb.cursors.DictCursor,
        )
        return conn, conn.cursor()
