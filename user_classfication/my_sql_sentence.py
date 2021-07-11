

def my_sql(mysql_conn, sql):
    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute(sql)
        mysql_conn.commit()
        data = cursor.fetchall()
        if len(data) > 0:
            return data
    except Exception as e:
        print(sql)
        print("Commit Failed!")
        return None
