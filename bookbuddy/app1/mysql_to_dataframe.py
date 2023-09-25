import pandas as pd
import mysql.connector

def mysql_dataframe(host, user, password, database, table):
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
        cursor = conn.cursor()

        # Fetch data from the MySQL table
        query = f"SELECT * FROM {table}"
        cursor.execute(query)

        # Fetch all rows and column names
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]

        # Create a Pandas DataFrame
        df = pd.DataFrame(data, columns=column_names)

        return df

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Example usage:
# host = 'localhost'
# user = 'root'
# password = 'maitry'
# database = 'data_testing'
# table = 'top50_books'

# df = mysql_dataframe(host, user, password, database, table)
