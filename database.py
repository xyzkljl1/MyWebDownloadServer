import mysql.connector
def _Connect():
    return mysql.connector.connect(host="localhost", port="4321", user="root", password="pixivAss", database="youtubedl")

def GetQueue():
    queue=[]
    try:
        conn=_Connect()
        cursor=conn.cursor()
        cursor.execute("select Id,URL,Cookie,UserAgent,IgnoreError from queue where FailCount<20")
        for (id,url,cookie,useragent,ignore_error) in cursor:
            queue.append((id,url,cookie,useragent,ignore_error))
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Get Queue:", err)
    return queue

def GetTask(id:int):
    try:
        conn=_Connect()
        cursor=conn.cursor()
        cursor.execute("select Id,URL,Cookie,UserAgent,IgnoreError from queue where Id={0}".format(id))
        row=cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except mysql.connector.Error as err:
        print("Fail To Get Task:", err)
    return None

def InsertURL(url:str,cookie:str,useragent:str):
    try:
        conn = _Connect()
        conn.cmd_query("insert into queue(URL,Cookie,UserAgent) values('{0}','{1}','{2}') ".format(url,cookie,useragent))
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Add Task to Queue:", err)

def UpdateRow(id:int,message:str):
    try:
        conn = _Connect()
        tmp=message.replace("'","\\'").replace('"','\\"').replace("{","{{").replace("}","}}")
        conn.cmd_query("update queue set FailCount=FailCount+1,FailMessage='{0}' where id={1}".format(tmp,id))
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Update Row:", err)


def RemoveRow(id:int):
    try:
        conn = _Connect()
        conn.cmd_query("delete from queue where id={0}".format(id))
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Remove Row:", err)
