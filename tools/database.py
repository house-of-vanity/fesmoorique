#
# Copyright (c) 2019, UltraDesu <ultradesu@hexor.ru>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY UltraDesu <ultradesu@hexor.ru> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL UltraDesu <ultradesu@hexor.ru> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
.. module:: models
   :synopsis: Contains database actions primitives.
.. moduleauthor:: AB <github.com/house-of-vanity>
"""

import sqlite3
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


# class DataBase create or use existent SQLite database file. It provides 
# high-level methods for database.
class DataBase:
    """This class create or use existent SQLite database file. It provides 
    high-level methods for database."""
    def __init__(self, scheme, basefile='data.sqlite'):
        """
          Constructor creates new SQLite database if 
          it doesn't exist. Uses SQL code from file for DB init.
          :param scheme: sql filename
          :type scheme: string
          :return: None
        """
        self.scheme = ''
        self.basefile = basefile
        try:
            conn = self.connect(basefile=basefile)
        except:
            log.debug('Could not connect to DataBase.')
            return None
        with open(scheme, 'r') as scheme_sql:
            sql = scheme_sql.read()
            self.scheme = sql
            if conn is not None:
                try:
                    cursor = conn.cursor()
                    cursor.executescript(sql)
                except Exception as e:
                    log.debug(f'Could not create scheme - {e}')
            else:
                log.debug("Error! cannot create the database connection.")
        log.info('DB created.')
        self.close(conn)

    def connect(self, basefile):
        """
          Create connect object for basefile
          :param basefile: SQLite database filename
          :type basefile: string
          :return: sqlite3 connect object
        """
        log.debug("Open connection to %s" % basefile)
        return sqlite3.connect(basefile, check_same_thread=False)

    def execute(self, sql):
        """
          Execute SQL code. First of all connect to self.basefile. Close 
          connection after execution.
          :param sql: SQL code
          :type sql: string
          :return: list of response. Empty list when no rows are available.
        """
        conn = self.connect(basefile=self.basefile)
        log.debug("Executing: %s" % sql)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchall()
        self.close(conn)
        return result

    def get_subject(self, subject_id):
        sql = f"SELECT * FROM subjects WHERE rowid = '{subject_id}'"
        ret = self.execute(sql)
        return ret

    def get_group(self, group_id):
        """
          **Add new group and members**
          :param group_id: ID of a group
          :type group_id: int
          :returns: list
        """
        sql = """SELECT s.name, s.reg_date, g.name 
        FROM `students` s LEFT JOIN `groups` g 
        ON s.`group` = g.rowid WHERE g.rowid = '%s'""" % group_id
        ret = self.execute(sql)
        return ret

    def add_group(self, group_name, members, author):
        """
          **Add new group and members**
          :param group_name: Name of a group
          :type group_name: string
          :param members: Group members
          :type members: list
          :param author: User who create group.
          :type members: int

          :returns: None
        """
        sql = f"INSERT OR IGNORE INTO groups('name', 'author')  VALUES ('{group_name}', {author})"
        self.execute(sql)
        sql = f"SELECT rowid FROM groups WHERE name = '{group_name}'"
        ret = self.execute(sql)
        group_id = ret[0][0]
        for member in members:
            sql = f'''INSERT OR IGNORE INTO students('name', 'group', 'author') 
            VALUES ('{member}','{group_id}', '{author}')'''
            self.execute(sql)

    def subject_list(self, user):
        """
          **List user's subjects.**
          :param user: User who create subject.
          :type user: int

          :returns: list
        """
        sql = f"""SELECT name, reg_date, rowid
        FROM subjects
        WHERE author = '{user}'"""
        ret = self.execute(sql)
        print(ret)
        return ret

    def group_list(self, user='all', favourites=False):
        """
          **List user's groups or all groups.**
          :param user: User who create group.
          :type user: int

          :returns: list
        """
        if user != 'all':
            sql = f"""SELECT g.name, g.reg_date, g.rowid, count(s.rowid) 
            FROM `groups` g 
            LEFT JOIN `students` s ON s.`group` = g.rowid 
            WHERE g.author = {user} GROUP BY g.name"""
        else:
            sql = f"""SELECT g.name, g.reg_date, g.rowid, count(s.rowid), u.name 
            FROM `groups` g 
            LEFT JOIN `students` s ON s.`group` = g.rowid 
            LEFT JOIN users u ON u.rowid = g.author 
            GROUP BY g.name"""
        if (favourites and str(user)):
            sql = f"""SELECT g.name, g.reg_date, g.rowid, count(s.rowid), u.name, d.group_id
            FROM `groups` g 
            LEFT JOIN `students` s ON s.`group` = g.rowid 
            LEFT JOIN users u ON u.rowid = g.author 
            LEFT JOIN dashboard d ON d.group_id = g.rowid
            GROUP BY g.name"""
        ret = self.execute(sql)
        print(ret)
        return ret

    def add_to_favourites(self, group_id, user_id):
        """
          **Add group to user's favourites.**
          :param user_id: User who saved dashboard.
          :type user_id: int
          :param group_id: Group ID
          :type group_id: int

          :returns: None
        """
        sql = f"INSERT OR IGNORE INTO dashboard(user_id, group_id) VALUES ('{user_id}', '{group_id}')"
        self.execute(sql)

    def remove_from_favourites(self, group_id, user_id):
        """
          **Remove group from user's favourites.**
          :param user_id: User who saved dashboard.
          :type user_id: int
          :param group_id: Group ID
          :type group_id: int

          :returns: None
        """
        sql = f"DELETE FROM dashboard WHERE user_id='{user_id}' and group_id='{group_id}'"
        self.execute(sql)

    def get_dashboard(self, user):
        """
          **List user's saved groups on dashboard.**
          :param user: User who saved dashboard.
          :type user: int

          :returns: list
        """
        sql = f"""SELECT g.name, g.reg_date, g.rowid, count(s.rowid) FROM dashboard d
        LEFT JOIN users u ON u.rowid = d.user_id
        LEFT JOIN `groups` g ON g.rowid = d.group_id
        LEFT JOIN `students` s ON s.`group` = g.rowid
        WHERE d.user_id = {user}
        GROUP BY s.`group`
        """
        ret = self.execute(sql)
        print(ret)
        return ret

    def user(self, action, name, pass_hash):
        """
          **Perform action with users table**
          :param action: Requested action
          :type action: string
          :returns: None
        """
        if action == 'create':
            sql = '''INSERT INTO users('name', 'pass')
            VALUES ('%s', '%s')''' % (name, pass_hash)
            self.execute(sql)

    def login(self, name):
        """
          **Perform action with users table**
          :param action: Requested action
          :type action: string
          :returns: None ?
        """
        sql = "SELECT pass, rowid FROM users WHERE name = '%s'" % name
        ret = self.execute(sql)
        if len(ret) == 0:
            ret = False
        else:
            ret = ret[0]
        return ret

    def close(self, conn):
        """
          Close connection object instance.
          :param conn: sqlite3 connection object
          :type conn: object
          :return: None
        """
        log.debug("Close connection to %s" % self.basefile)
        conn.close()

