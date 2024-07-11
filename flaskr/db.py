from mysql import connector

connection = connector.connect(
    user='root',
    password='heavenisthegoal',
    host='localhost:3306',
    database='vaultofideas_db'
)

connection.close()
