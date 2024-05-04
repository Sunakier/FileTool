import sqlite3


# TODO: 异步处理和读写分离的实现
# TODO: 多数据库的支持
# TODO: 云和集群的同步支持

class FileStorageServer:
    _conn = None

    def __init__(self):
        self.conn = self.get_connection("data.db")
        self.check_tables()

    @classmethod
    def get_connection(cls, db_file):
        if cls._conn is None:
            cls._conn = sqlite3.connect(db_file, check_same_thread=False)
        return cls._conn

    def check_tables(self):
        cursor = self.conn.cursor()
        # 创建files表
        cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                            file_id TEXT PRIMARY KEY,
                            size INTEGER,
                            time TEXT,
                            ip TEXT
                        )''')
        # 创建tokens表
        cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
                            token TEXT PRIMARY KEY,
                            sync_file BLOB,
                            time INTEGER
                        )''')
        self.conn.commit()

    def add_file_id(self, file_id, size, time, ip):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO files (file_id, size, time, ip) VALUES (?, ?, ?, ?)", (file_id, size, time, ip,))
        self.conn.commit()

    def read_file_id(self, file_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_id, size, time, ip FROM files WHERE file_id=?", (file_id,))
        result = cursor.fetchone()
        if result:
            return result
        return None

    def write_token(self, token, sync_file, version_time):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO tokens (token, sync_file, time) VALUES (?, ?, ?)", (token, sync_file, version_time,))
        self.conn.commit()

    def read_token(self, token):
        cursor = self.conn.cursor()
        cursor.execute("SELECT token, sync_file, time FROM tokens WHERE token=?", (token,))
        result = cursor.fetchone()
        if result:
            return result
        return None

    def debug_read_all_files(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_id, size, time, ip FROM files", )
        result = cursor.fetchall()
        if result:
            return result
        return None


sql = FileStorageServer()

if __name__ == "__main__":
    sql.write_token("1234debug", "{}", 2)
    print(sql.read_token("1234debug"))
