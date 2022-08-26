from sqlite3 import Error
import sqlite3
import variables

##############################
#
#   DEFAULT FOR EVERYTHING
#
##############################

def SQL_createConnection(databasePath):
    databaseConnection = None
    try:
        databaseConnection = sqlite3.connect(databasePath, check_same_thread = False)
    except Error as e:
        variables.logging.error("[SQL]: Failed to create connection to the SQLite3 database (%s). Exception: %s" %(databasePath,e))
        return None
    else:
        return databaseConnection

def SQL_checkTableExists(databaseType, tableName):
    if databaseType == "alertDatabase":
        databasePath = variables.alertDatabase
    elif databaseType == "threadDatabase":
        databasePath = variables.threadDatabase

    try:
        databaseConnection = SQL_createConnection(databasePath)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute('SELECT count(name) FROM sqlite_master WHERE type="table" AND name=?', (tableName,))
            entry = sqlCursor.fetchone()
    
            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
      raise Exception()
    else:
      if entry[0]==1:
          return 0
      else:
          return 1

def SQL_checkRowExists(databaseType, tableName, id):
    if databaseType == "alertDatabase":
        databasePath = variables.alertDatabase
    elif databaseType == "threadDatabase":
        databasePath = variables.threadDatabase

    try:
        checkTemplate = "SELECT * FROM %s WHERE id=?" %tableName

        databaseConnection = SQL_createConnection(databasePath)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate, (id,))
            entry = sqlCursor.fetchone()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
      raise Exception()
    else:
        if entry is None:
            return 1
        else:
            return 0


##############################
#
#   threadDatabase ONLY!
#
##############################

def SQL_checkAlertResolved(id):
    try:
        checkTemplate = "SELECT * FROM resolvedThreads WHERE prometheusAlertId=?"

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate, (id,))
            entry = sqlCursor.fetchone()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
      raise Exception()
    else:
        if entry is None:
            return 1
        else:
            return 0

def SQL_createFiringThread(tableName, threadId, status, prometheusAlertRule, prometheusAlertId, prometheusAlertName, prometheusAlertDescription, prometheusAlertSeverity, prometheusAlertImportance):
    try:
        insertTemplate = "INSERT INTO %s(id,status,prometheusAlertRule,prometheusAlertId, prometheusAlertName, prometheusAlertDescription, prometheusAlertSeverity, prometheusAlertImportance) VALUES(?,?,?,?,?,?,?,?)" %tableName

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(insertTemplate, (threadId,status,prometheusAlertRule,prometheusAlertId,prometheusAlertName,prometheusAlertDescription,prometheusAlertSeverity,prometheusAlertImportance))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_createResolvedThread(tableName, threadId, status, prometheusAlertRule, prometheusAlertId):
    try:
        insertTemplate = "INSERT INTO %s(id,status,prometheusAlertRule,prometheusAlertId) VALUES(?,?,?,?)" %tableName

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(insertTemplate, (threadId,status,prometheusAlertRule,prometheusAlertId))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_createThreadTable():
    try:
        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute("CREATE TABLE IF NOT EXISTS firingThreads(id,status,prometheusAlertRule,prometheusAlertId, prometheusAlertName, prometheusAlertDescription, prometheusAlertSeverity, prometheusAlertImportance)")
            sqlCursor.execute("CREATE TABLE IF NOT EXISTS resolvedThreads(id,status,prometheusAlertRule,prometheusAlertId)")
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_deleteThread(threadId, tableName):
    try:
        deleteTemplate = "DELETE FROM %s WHERE id=%s" %(tableName,threadId)

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(deleteTemplate)
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_updateThreadStatus(threadId, tableName, status):
    try:
        updateTemplate = "UPDATE %s SET status=? WHERE id=?" %tableName

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(updateTemplate, (status,threadId))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_getNumberOfThreads():
    try:
        checkTemplate = "SELECT (SELECT COUNT(*) FROM firingThreads) + (SELECT COUNT(*) FROM resolvedThreads) AS SumCount"

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate)
            entry = sqlCursor.fetchone()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return '%s' %entry

def SQL_getListOfThreads(tableName):
    try:
        checkTemplate = "SELECT id FROM %s" %tableName

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate)
            listOfRows = sqlCursor.fetchall()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        listA = []
        if listOfRows:
            for value in listOfRows:
                listA.append('%s' %value)
            return listA
        else:
            return listOfRows

def SQL_getThreadInformation(tableName, id):
    try:
        checkTemplate = "SELECT * FROM %s WHERE id=%s" %(tableName,id)

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate)
            row = sqlCursor.fetchone()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return row

##############################
#
#   alertDatabase ONLY!
#
##############################


def SQL_createAlert(tableName, prometheusAlertId, timestemp):
    try:
        insertTemplate = "INSERT INTO %s(id,status,timestemp) VALUES(?,?,?)" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(insertTemplate, (prometheusAlertId,"CREATED",timestemp))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_deleteAlert(tableName, prometheusAlertId):
    try:
        deleteTemplate = "DELETE FROM %s WHERE id=?" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(deleteTemplate, (prometheusAlertId,))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_createAlertTable(tableName):
    try:
        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute("CREATE TABLE IF NOT EXISTS %s(id,status,timestemp)" %tableName)
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_deleteAlertTable(tableName):
    try:
        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute("DROP TABLE %s" %tableName)
            databaseConnection.commit()
    
            databaseConnection.close()
        else:
            raise Exception("")
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_updateAlertTime(tableName, prometheusAlertId, timestemp):
    try:
        updateTamplate = "UPDATE %s SET timestemp=? WHERE id=?" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(updateTamplate, (timestemp, prometheusAlertId))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_updateAlertStatus(tableName, prometheusAlertId, status):
    try:
        updateTamplate = "UPDATE %s SET status=? WHERE id=?" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(updateTamplate, (status, prometheusAlertId))
            databaseConnection.commit()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return 0

def SQL_getAlertStatus(tableName, prometheusAlertId):
    try:
        checkTemplate = "SELECT status from %s where id=?" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate, (prometheusAlertId,))
            alertstatus = sqlCursor.fetchone()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return '%s' %alertstatus

def SQL_getListOfAlets(tableName):
    try:
        checkTemplate = "SELECT id FROM %s WHERE status NOT LIKE 'EPILOG'" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate)
            listOfRows = sqlCursor.fetchall()

            databaseConnection.close()
        else:
            variables.logging.error("[SQL - alertDatabase]: Cannot get list of prometheusAlerts from SQL Table. SQL Connection failed")
            return None
    except Error as e:
        variables.logging.error("[SQL - alertDatabase]: Failed to get list of prometheusAlers in SQL Tables: %s. Exception: %s" %(tableName, e))
        return None
    else:
        listA = []
        if listOfRows:
            for value in listOfRows:
                listA.append('%s' %value)
            return listA
        else:
            return listOfRows

def SQL_getListOfAlertsRule():
    try:
        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            listOfTables = sqlCursor.fetchall()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return listOfTables

def SQL_getActiveAlertOlderThan(tableName,time):
    try:
        checkTemplate = "SELECT id from %s where timestemp <= ? AND status NOT LIKE 'EPILOG'" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate, (time,))
            listOfOlders = sqlCursor.fetchall()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        listOlders = []
        if listOfOlders:
            for value in listOfOlders:
                listOlders.append('%s' %value)
            return listOlders
        else:
            return listOfOlders

##############################
#
#   Functions for Applicatation deleteing menu
#
##############################

def SQL_MENU_getListOfThreads(tableName):
    try:
        getTemplate = "SELECT * from %s" %tableName

        databaseConnection = SQL_createConnection(variables.threadDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(getTemplate)
            listOfAlerts = sqlCursor.fetchall()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return listOfAlerts

def SQL_MENU_getListOfAlerts(tableName):
    try:
        getTemplate = "SELECT * from %s" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(getTemplate)
            listOfAlerts = sqlCursor.fetchall()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return listOfAlerts

def SQL_MENU_getAlertInfo(tableName, id):
    try:
        checkTemplate = "SELECT * from %s where id=?" %tableName

        databaseConnection = SQL_createConnection(variables.alertDatabase)
        if databaseConnection is not None:
            sqlCursor = databaseConnection.cursor()
            sqlCursor.execute(checkTemplate, (id,))
            alertinfo = sqlCursor.fetchone()

            databaseConnection.close()
        else:
            raise Exception()
    except Error as e:
        raise Exception()
    else:
        return alertinfo
