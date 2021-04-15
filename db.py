import config
import sqlite3
from sqlite3 import Error

try:
    conn = sqlite3.connect(config.db_file, check_same_thread=False)
    cursor = conn.cursor()
except Error as e:
    print(e)

try:
    cursor.execute("""CREATE TABLE data
                      (id text UNIQUE, 
                      state text, 
                      url text, 
                      exercises text, 
                      ex_key text,
                      counter integer, 
                      lookup  text,
                      word text, 
                      pos text                      )
                    """)
except Error as e:
    print(e)


def print_db(con=conn):
    with con:
        cursor.execute("SELECT * FROM data")
        print(cursor.fetchall())


def del_table(con=conn):
    cursor.execute('''DROP TABLE data''')
    con.commit()


def set_property(user_id, col, value, con=conn):
    sql = ''' UPDATE data              
              SET {} = ?  
              WHERE id = ?           
              '''.format(col)

    cursor.execute(sql, (value, user_id))
    con.commit()


def del_state(user_id, col, con=conn):
    set_property(user_id, col, None)
    con.commit()

def set_id(state_id, con=conn):
    sql = ''' INSERT OR REPLACE INTO data (id)
              VALUES (?)
              '''
    cursor.execute(sql, (state_id,))
    con.commit()


def get_current_state(state_id, col, con=conn):
    sql = '''SELECT {} FROM data WHERE id = ?'''.format(col)
    try:
        state = cursor.execute(sql, (state_id,)).fetchall()
        if len(state) == 1:
            if len(state[0]) == 1:
                return state[0][0]
        else:
            return False
    except KeyError:
         return config.States.START.value

