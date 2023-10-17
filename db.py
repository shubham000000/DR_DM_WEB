import mysql.connector
from mysql.connector import errorcode
from enum import Enum

class DatabaseWrapper:
    """Encapsulates MySQL actions"""
    def __init__(self, app, db_name = None):
        try:
            if db_name:
                self.cnx = mysql.connector.connect(user=app.config["DB_USER_NAME"],
                                        password=app.config["DB_USER_PWD"],
                                        host=app.config["DB_HOST"],
                                        database=db_name)
            else:                                               
                self.cnx = mysql.connector.connect(user=app.config["DB_USER_NAME"],
                                        password=app.config["DB_USER_PWD"],
                                        host=app.config["DB_HOST"])
        
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Fail to Connect to Database with invalid user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    
    def __del__(self):
        self.cnx.close()

    def create_database(self, db_name):
        try:
            cursor = self.cnx.cursor()
            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        except mysql.connector.Error as err:
            print("Failed creating databse: {}".format(err))
        finally:
            cursor.close()
    
    def create_tables(self, tables):
        cursor = self.cnx.cursor()
        for table_name in tables:
            table_description = tables[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                cursor.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")

        cursor.close()
    
    def switch_database(self, db_name):
        try:
            cursor = self.cnx.cursor()
            cursor.execute(
                "USE {}".format(db_name))
        except mysql.connector.Error as err:
            print("Failed switching databse: {}".format(err))
        finally:
            cursor.close()

    def insert_record(self, table_name, record):
        columns = TableColumn[table_name]
        column_sql = "(" + ",".join(columns) + ")"
        values_sql = "(" + ",".join(["%({})s".format(item) for item in columns]) + ")"
        query = """INSERT INTO {} {}
        VALUES {}""".format(table_name, column_sql, values_sql)

        try:
            cursor = self.cnx.cursor()
            cursor.execute(query, record)
        except mysql.connector.Error as err:
            print("Failed inserting record to databse: {}".format(err))
        finally:
            cursor.close()

    def query_records(self, query):
        try:
            cursor = self.cnx.cursor()
            cursor.execute(query)
            # fetch all rows
            rows = cursor.fetchall()

            return rows
        except mysql.connector.Error as err:
            print("Failed retrieving record from databse: {}".format(err))
        finally:
            cursor.close()
    

class TableColumn(Enum):
    USEER = ["fullname", "email", "gender", "username", "birthdate"]
    


    