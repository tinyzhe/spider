# coding=utf-8
import MySQLdb
import MySQLdb.cursors
import string
import datetime
from conf import config
from MySQLdb.cursors import DictCursor
from DBUtils.PooledDB import PooledDB

_conn = None

def getConn():
    global _conn
    if _conn == None:
        _conn = DB()
    return _conn

class DB(object):

    #连接池对象
    __pool = {}

    def __init__(self, conf=None):

        #数据库构造函数，从连接池中取出连接，并生成操作游标
        self.conn = DB.__getConn(conf)
        self.cursor = self.conn.cursor()
        # Enforce UTF-8 for the connection.
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    @staticmethod
    def __getConn(conf=None):
        """
        @summary: 静态方法，从连接池中取出连接
        @return MySQLdb.connection
        """
        if not(conf):
            conf = config.DB

        key = "%s-%s" % (conf['host'], conf["dbname"])

        if DB.__pool.has_key(key)==False or not(DB.__pool[key]):
            DB.__pool[key] = PooledDB(creator=MySQLdb, mincached=1, maxcached=100,
                              host=conf['host'], port=conf['port'], user=conf['user'], passwd=conf['password'],
                              db=conf['dbname'], use_unicode=True, charset='utf8', cursorclass=DictCursor, setsession=['SET AUTOCOMMIT = 1'])
            DB.__pool[key].connection()

        return DB.__pool[key].connection()

    # instance methods
    ###########################
    def execute(self, sql, param=None):
        """ 执行sql语句 """
        rowcount = 0
        # print sql
        # try:
        if param == None:
            rowcount = self.cursor.execute(sql)
        else:
            rowcount = self.cursor.execute(sql, param)
        return rowcount
        # except Exception,e:
        #     print '--------------Error--------'
        #     print e
        #     return 0

    def queryOne(self, sql, param=None):
        """ 获取一条信息 """
        rowcount = self.cursor.execute(sql, param)
        if rowcount > 0:
            res = self.cursor.fetchone()
        else:
            res = None

        return res

    def queryAll(self, sql, param=None):
        """ 获取所有信息 """
        rowcount = self.cursor.execute(sql, param)
        if rowcount > 0:
            res = self.cursor.fetchall()
        else:
            res = []
        return res

    def begin(self):
        """
        @summary: 开启事务
        """
        self.cursor.execute("SET AUTOCOMMIT = 0")
        #self.conn.autocommit(0)

    def end(self):
        self.cursor.execute("SET AUTOCOMMIT = 1")
        #self.conn.autocommit(1)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def select(self, table_name, columns='*', where=None):
        if isinstance(columns, (str, unicode)):
            columns_str = str(columns)
        elif isinstance(columns, (list, tuple)):
            if not columns:
                columns_str = '*'
            else:
                columns_str = ','.join(c.__str__() for c in columns)

        if isinstance(where, dict) and where:
            items = where.items()
            if len(items) == 1 and isinstance(items[0][0], (list, tuple)) and items[0][0]:
                self.execute("SELECT %s FROM %s WHERE %s in (%s)" % (
                columns_str, table_name, items[0], ','.join(e.__str__() for e in items[1])))
            else:
                # where_str = " AND ".join(["%s='%s'" % (str(x[0]), str(x[1])) for x in where.items()])
                # self.execute("SELECT %s FROM %s WHERE %s" % (columns_str,table_name,where_str))

                sql, values = self.sql_and_values_for_dict(table_name, columns, where)
                self.execute(sql, values)
        elif isinstance(where, (str, unicode)) and where:
            self.execute("SELECT %s FROM %s WHERE %s" % (columns_str, table_name, where))
        else:
            self.execute("SELECT %s FROM %s " % (columns_str, table_name))

            # slect one

    def selectOne(self, table_name, columns='*', where=None):
        self.select(table_name, columns, where)
        return self.cursor.fetchone()

        # select

    def selectAll(self, table_name, columns='*', where=None):
        self.select(table_name, columns, where)
        return self.cursor.fetchall()

        # find by id

    def find_by_id(self, table_name, id):
        return self.queryOne("select * from %s WHERE id = '%s'" % (table_name, id))

        # find by dict

    def find_id_by_dict(self, table_name, params_dic):
        return self.find_columns_by_dict(table_name, 'id', params_dic)

    def sql_and_values_for_dict(self, table_name, columns, params_dic):
        inputs = ''
        index = 0
        for x in params_dic.keys():
            inputs = inputs + (" AND " if index > 0 else '') + x.__str__() + "=%s"
            index += 1
        values = map(lambda x: str(x), params_dic.values())
        sql = u"select %s from %s WHERE %s" % (columns, table_name, inputs)
        return sql, values

        # find comumns by dict

    def find_columns_by_dict(self, table_name, columns, params_dic, queryOne=True):
        sql, values = self.sql_and_values_for_dict(table_name, columns, params_dic)
        if queryOne:
            return self.queryOne(sql, values)
        else:
            return self.queryAll(sql, values)

            # find by dict

    def find_one_by_dict(self, table_name, params_dic):
        return self.find_columns_by_dict(table_name, '*', params_dic)

        # insert

    def insert(self, table_name, params_dic, update_date=True):
        #if update_date:
            #now = type(self).get_datetime_string()
            #params_dic.update({'created_at': now, 'updated_at': now})
        keys = string.join(params_dic.keys(), "`,`")
        inputs = ','.join(("%s",) * len(params_dic))
        values = map(lambda x: str(x), params_dic.values())
        sql = "INSERT INTO " + table_name + " (`" + keys + "`) VALUES (" + inputs + ")"
        return self.execute(sql, values)

        # update

    def update(self, table_name, params_dic, where=None, update_date=True):
        #if update_date:
            #params_dic.update({'updated_at': type(self).get_datetime_string()})
        edit_sql = ",".join([("%s" % (str(x)) + "=%s") for x in params_dic.keys()])
        values = map(lambda x: str(x), params_dic.values())
        where_sql = ''

        if where:
            if isinstance(where, (str, unicode)):
                where_sql = str(where)
            elif isinstance(where, dict):
                where_sql = " AND ".join([("%s" % (str(x)) + "=%s") for x in where.keys()])
                where_values = map(lambda x: str(x), where.values())
                values = values + where_values
            sql = "UPDATE %s SET %s WHERE %s" % (table_name, edit_sql, where_sql)
        else:
            sql = "UPDATE %s SET %s " % (table_name, edit_sql)

        return self.execute(sql, values)

    # delete
    def delete(self, table_name, where=None):
        where_sql = ''
        if where:
            if isinstance(where, str):
                where_sql = where
            elif isinstance(where, dict):
                where_sql = " AND ".join(["%s='%s'" % (str(x[0]), str(x[1])) for x in where.items()])
            sql_prefix = "DELETE FROM %s WHERE %s "
            sql = sql_prefix % (table_name, where_sql)
        else:
            sql_prefix = "DELETE FROM %s "
            sql = sql_prefix % (table_name)

        return self.execute(sql)

    def get_inserted_id(self):
        """
        获取当前连接最后一次插入操作[自增长]生成的id,如果没有则为０
        """
        result = self.queryAll("SELECT @@IDENTITY AS id")
        if result:
            return result[0].get('id')
        return 0
        #################### classmethods

    @classmethod
    def get_datetime_string(cls):
        return datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def generate_code(cls):
        import time
        import random
        return '%x%x' % (int(time.time()), random.randint(1, 0x0ffff))

    @classmethod
    def generate_id(cls):
        return "n%s" % cls.generate_code()