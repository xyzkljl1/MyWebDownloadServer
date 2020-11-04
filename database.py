import mysql.connector
def _Connect():
    return mysql.connector.connect(host="localhost", port="4321", user="root", password="pixivAss", database="youtubedl")

def GetQueue():
    queue=[]
    try:
        conn=_Connect()
        cursor=conn.cursor()
        cursor.execute("select Id,URL from queue")
        for (id,url) in cursor:
            queue.append((id,url))
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Get Queue:", err)
    return queue

def InsertURL(url:str):
    try:
        conn = _Connect()
        conn.cmd_query("insert into queue(URL) values('{0}')".format(url))
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Add Task to Queue:", err)

def RemoveRow(id:int):
    try:
        conn = _Connect()
        conn.cmd_query("delete from queue where id={0}".format(id))
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Remove Row:", err)
