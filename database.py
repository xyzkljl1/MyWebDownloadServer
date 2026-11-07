import mysql.connector
def _Connect():
    return mysql.connector.connect(host="localhost", port="4321", user="root", password="pixivAss", database="youtubedl")

def GetQueue():
    queue=[]
    try:
        conn=_Connect()
        cursor=conn.cursor()
        cursor.execute("select Id,URL,Cookie,UserAgent,IgnoreError,TargetDir from queue where FailCount<20")
        for row in cursor:
            queue.append(row)
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print("Fail To Get Queue:", err)
    return queue

def GetTask(id:int):
    try:
        conn=_Connect()
        cursor=conn.cursor()
        cursor.execute("select Id,URL,Cookie,UserAgent,IgnoreError,TargetDir from queue where Id=%s", (id,))
        row=cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except mysql.connector.Error as err:
        print("Fail To Get Task:", err)
    return None

def InsertURL(url:str,cookie:str,useragent:str,relative_dir=None):
    import download_paths

    conn = cursor = None
    try:
        conn = _Connect()
        cursor = conn.cursor()
        suffix = 0
        while True:
            target = None
            if relative_dir:
                target = download_paths.candidate(url, relative_dir, suffix)
                suffix += 1
                if download_paths.occupied(target):
                    continue
            try:
                cursor.execute(
                    "INSERT INTO queue(URL,Cookie,UserAgent,TargetDir) VALUES(%s,%s,%s,%s)",
                    (url, cookie, useragent or "", target))
                conn.commit()
                return cursor.lastrowid, target
            except mysql.connector.IntegrityError as error:
                conn.rollback()
                # The unique index also reserves paths for concurrent requests.
                if (target is None or error.errno != 1062 or
                        "uq_queue_target_dir" not in str(error)):
                    raise
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

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


def GetNHentaiApiToken():
    conn = _Connect()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT ApiToken FROM download_auth WHERE Site=%s", ("nhentai",))
            row = cursor.fetchone()
            return row[0] if row else ""
        finally:
            cursor.close()
    finally:
        conn.close()
