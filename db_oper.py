"""
M.Samek - 19.1.2023
fce na pristup k databazi
- connect
- get_
- insert

"""

from configparser import ConfigParser
# pripojeni k postgres
import psycopg2
import psycopg2.extras
from psycopg2.extensions import quote_ident

#from config import config
import logging
from typing import List, Dict
import pandas as pd
#import sqlalchemy

logger = logging.getLogger(__name__)

def pg_connect(config_filename='database.ini'):
    """
    pripojeni k PG
    :return cursor: vrati cursor
    """
    try:
        params, params_str = config(filename = config_filename)

        # connect to the PostgreSQL server
        logger.info('Connecting to the PostgreSQL database...')

        """yb_pool = psycopg2.pool.SimpleConnectionPool(1, 10, user="yugabyte",
                                                     password="yugabyte",
                                                     host="127.0.0.1",
                                                     port="5433",
                                                     database="yugabyte",
                                                     load_balance="True")
                                                    """
        #yb_pool = psycopg2.pool.SimpleConnectionPool(1, 10, params_str,  load_balance="True")
        #conn = yb_pool.getconn()
        print(params)
        conn = psycopg2.connect(**params)

        print(">>>> Successfully connected to YugabyteDB!")

        # create a cursor
        cur = conn.cursor()

        # execute a statement
        #print('PostgreSQL database version:')
        #cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        #db_version = cur.fetchone()
        #print(db_version)

        return  cur, conn

    except (Exception, psycopg2.DatabaseError) as error:
        logger.info(error)
        print(error)
        raise RuntimeError(error)
        #cursor.close()
        #conn.close()
    #finallyn:
    #    if conn is not None:
    #        conn.close()
    #        print('Database connection closed.')

def pg_disconnect(cursor, conn):
    """
    zavreni kurzoru
    :return:
    """
    cur.close()
    conn.close()

def get_select_desc(cursor, table : str):
    """
    vrata sloupce a datove typy v tabulce
    :param cursor:
    :param table:
    :return:
    """
    query = f"SELECT    table_name,     column_name,    data_type    FROM     information_schema.columns    WHERE    table_name = '{table}'  ORDER BY ordinal_position"
    st, result = pg_run_query(cursor, query)
    col_types = []
    col_names = []
    for i , res in enumerate(result):
        col_types.append(res[2])
        col_names.append(res[1])
    logger.debug(col_names)
    return col_names, col_types

def read_sql_file(file_path: str) -> str:
    """

    :param file_path:
    :return:
    """
    logger.info(f"reading file: {file_path}")
    with open(file_path, "r") as f:
        return f.read()



def format_update_values(col_names: list, col_values: list, col_types: list) -> str:
    """
    
    :param col_names: 
    :param col_values: 
    :param col_types: 
    :return:

    ['integer', 'timestamp without time zone', 'timestamp without time zone', 'timestamp without time zone', 'character varying', 'character varying', 'integer', 'integer', 'timestamp without time zone']
    """
    out: str = ""
    for i, col_value in enumerate(col_values):
        if col_value in [ '', 'NULL' ]:
            out = f"{out}, {col_names[i]} = NULL "
        elif col_value in [ 'DEFAULT' ]:
            out = f"{out}, {col_value} "
        elif col_types[i].count("timestamp") > 0 : # == "TIMESTAMP":
            out = f"{out}, {col_names[i]}='{col_value[:19]}'"
        elif col_types[i].count("integer") >  0: # == "INT":
            out = f"{out}, {col_names[i]} = {col_value}"
        else:
            out = f"{out}, {col_names[i]} = '{col_value}'"

    return f" {out[1:]} "

def sql_escape(value):
    """

    :param value:
    :return:
    """
    return str(value).replace("'","\'")

def format_insert_values(col_names: list, col_values: list,  col_types: list) -> str:
    """
     format values for insert

     ['integer', 'timestamp without time zone', 'timestamp without time zone', 'timestamp without time zone', 'character varying', 'character varying', 'integer', 'integer', 'timestamp without time zone']
    :param col_names:
    :param col_values:
    :param col_types:
    :return: col_names , col_values
    """

    out: str = ""
    col_name : str = ""
    col_val : str = ""
    #//print(col_names)
    #//print(col_values)
    for i, col_value in enumerate(col_values):
        col_name = f"{col_name}, {col_names[i]}"
        if col_value in [ '', 'NULL' ]:
            col_val = f"{col_val}, NULL "
        elif col_value in [ 'DEFAULT' ]:
            col_val = f"{col_val}, {col_value} "
        elif col_types[i].count("timestamp") > 0 : # "TIMESTAMP":
            col_val = f"{col_val}, '{col_value[:19]}'"
        elif col_types[i].count("integer") >  0 : #== "INT":
            col_val = f"{col_val}, {col_value}"
        else:
            col_val = f"{col_val}, '"+sql_escape(col_value).replace("'","&x27")+"'"  # osetreni apostrofu v textu

    return  f"{col_name[1:]}" , f" {col_val[1:]} "

def pg_run_query(cursor, query, fail_on_error = 1):
    """
    spusteni dotazu
    :return query_status: 1 - success, 0 - fail
    :return result list: list with results
    """
    try:
        logger.info(f"{query[0:1000]}")
        cursor.execute(query)
        # [(1, 100, "abc'def"), (2, None, 'dada'), (3, 42, 'bar')]
        if cursor.description: # pro SELECT
            results: List = cursor.fetchall()
        else: # pro ostatni INSERT UPDATE
            results : List = []
        return 1, results
    except Exception as err:
        msg = f"Query {query} failed on Exception: {err}"
        logger.error(msg)
        if fail_on_error == 1:
            raise RuntimeError(msg)
        # pokud query spadne, tak vratim prazdny vysledek a zpravu ve vysledku, pokud bych ji chtel propagovat dal
        return 0, [ msg ]


def pg_run_query2( conn, cursor, query, parameters=None):
    """

    :param cursor:
    :param conn:
    :param query:
    :param parameters:
    :return:
    """
    cursor = conn.cursor()
    try:
        conn.commit()
        print(f"{query}")
        cursor.execute(query, parameters)
    except (psycopg2.Error) as e:
        conn.rollback()
        raise e
    else:
        conn.commit()
        # cursor.description is None when
        # no rows are returned
        if cursor.description is not None:
            return cursor.fetchall()


def run_query_as_pandas(cursor, query):
    """
    return query in panda dataframa
    https://stackoverflow.com/questions/27884268/return-pandas-dataframe-from-postgresql-query-with-sqlalchemy
    :param connect:
    :return:
    """
    #from sqlalchemy import create_engine

    try:
         #    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
        logger.info(f"1-{query}")
        cursor.execute(query)
        tupples = cursor.fetchall()
        column_names : List[str] = [ r[0]  for r in cursor.description]

        df = pd.DataFrame(tupples, columns = column_names)
        #print(f"{df.head()}")
        return df
    except (Exception, psycopg2.Error) as err:
        logger.error(f"Query {query} failes with exc: {err}")
        raise RuntimeError(f"Query {query} failes with exc: {err}")


def run_query_to_csv(cursor, query: str, csv_path: str, delim = ",") -> None:
    """
    export query to csv
    :param cursor:
    :param query:
    :param csv_path:
    :param delim:
    :return:
    """
    cursor.execute(query)
    columns : List[str] = [ r[0] for f in cursor.description ]
    with open(csv_path, "w", newLine = '') as f:
        writer = csv.writer(f, delimiter = delim, quotechar = '"', quoting = csv.QUOTE_ALL, lineterminator = "\n")
        writer.writerow(columns)
        for row in cursor:
            writer.writerow(row)

def config(filename='database.iniXX', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    db_str = []
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            if param[1] != '':
                db[param[0]] = param[1]
                if  param[0] == "database":
                    db_str.append(f"dbname='{param[1]}'")
                else:
                    db_str.append(f"{param[0]}='{param[1]}'")
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    #print(db_str)
    return db, " ".join(db_str)




def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params, params_str = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn_str = psycopg2.connect(params_str)

        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT * FROM accounts')

        # display the PostgreSQL database server version
        db_acc = cur.fetchone()
        print(db_acc)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


def lookup_init( query, cursor ) -> int:
    """

    :param conn:
    :param query:
    :return:
    """
    return run_query_as_pandas(cursor = cursor , query = query)

def lookup(df, key, value):
    """

    :param df:
    :param key:
    :param value:
    :return:
    """
    return df[df[key]==value]

def lookup_value(df, key, value, column):
    """

    :param df:
    :param key:
    :param value:
    :param column:
    :return:
    """
    #print(f"{key}-{value}-{column}")
    return lookup(df, key, value)[column].values[0]

def lookup_list_values(df, key, vale, column):
    """

    :param df:
    :param key:
    :param vale:
    :param column:
    :return:
    """
    return lookup(df, key, value)[column].values

def lookup_exists(df, key, value):
    """
    check if value exists in lookup
    :param df:
    :param key:
    :param value:
    :return:
    """
    return len(df[key]==value)>0

"""
https://pythontic.com/pandas/serialization/postgresql
READ
 Example python program to read data from a PostgreSQL table
# and load into a pandas DataFrame
import psycopg2
import pandas as pds
from sqlalchemy import create_engine

# Create an engine instance
alchemyEngine   = create_engine('postgresql+psycopg2://test:@127.0.0.1', pool_recycle=3600);

# Connect to PostgreSQL server
dbConnection    = alchemyEngine.connect();
# Read data from PostgreSQL database table and load into a DataFrame instance
dataFrame       = pds.read_sql("select * from \"StudentScores\"", dbConnection);
pds.set_option('display.expand_frame_repr', False);

# Print the DataFrame
print(dataFrame);
# Close the database connection
dbConnection.close();

WRITE
# Example Python program to serialize a pandas DataFrame
# into a PostgreSQL table
from sqlalchemy import create_engine
import psycopg2
import pandas as pds

# Data - Marks scored
studentScores = [(57, 61, 76, 56, 67),
                 (77, 67, 65, 78, 62),
                 (65, 71, 56, 63, 70)
                ];

# Create a DataFrame
dataFrame   = pds.DataFrame(studentScores,
              index=(1211,1212,1213), # Student ids as index
              columns=("Physics", "Chemistry", "Biology", "Mathematics", "Language")
              );
     

alchemyEngine           = create_engine('postgresql+psycopg2://test:test@127.0.0.1/test', pool_recycle=3600);
postgreSQLConnection    = alchemyEngine.connect();
postgreSQLTable         = "StudentScores";

try:
    frame           = dataFrame.to_sql(postgreSQLTable, postgreSQLConnection, if_exists='fail');
except ValueError as vx:
    print(vx)
except Exception as ex:  
    print(ex)
else:
    print("PostgreSQL Table %s has been created successfully."%postgreSQLTable);
finally:
    postgreSQLConnection.close();

"""

if __name__ == '__main__':
    #connect()
    cur, conn = pg_connect()
    #cur = ''
    #r = pg_run_query(cursor = cur, query = "SELECT * FROM processes")
    #print(r)
    r = pg_run_query2(conn = conn, cursor = cur, query = "SELECT * FROM list_statuses")
    print(r)
    #exit(0)
    lkp_lpr =  lookup_init(cursor = cur,  query = "SELECT * FROM list_process_types")
    #try:
    lkp_lmo = lookup_init(cursor = cur,  query = "SELECT * FROM list_models")
    lkp_lmo.head()
    lkp_lst = lookup_init(cursor = cur,  query = "SELECT * FROM list_statuses")
    lkp_lst.head()
    #except (Exception, psycopg2.DatabaseError) as e:
    #    print("Exception while transferring money")
    #    print(e)

    r = pg_run_query(cursor = cur, query = "SELECT * FROM list_statuses")
    print(r)
    col_names, col_types = get_select_desc(cur, table = "list_statuses")
    print(col_names)
    print(col_types)
    r = pg_run_query(cursor = cur, query = """SELECT
    table_name,
    column_name,
    data_type
    FROM
    information_schema.columns
    WHERE
    table_name = 'processes'""")
    print(r)
