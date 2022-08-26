from time import sleep
import time
import requests
import random
import threading
import json
import sys
    # Files
import variables
from functions import sql as sqlFunctions
from functions import zabbix as zabbixFunctions
    # Thread bodies
import new_body_firing
import new_body_resolved

def prometheusAlertRuleManager():
    currentPrometheusRules = []
    currentZabbixItems = []
    currentSQLTables = []

    # list of PrometheusAlertRules from Prometheus itself.
    try:
        prometheusResponse = requests.get(url = variables.prometheusUrl + "/api/v1/rules")
    except:
        variables.logging.fatal('Cannot get list of prometheusAlertRules from %s/api/v1/rules' %variables.prometheusUrl)
        sys.exit(1)
    else:
        if prometheusResponse is not None:
            # PrometheusAlertRules - list of PrometheusAlertRules from Prometheus. (Prometheus)
            variables.logging.debug('PrometheusAlertRules /(Prometheus)\ - List of prometheusAlertRules - Started')
            prometheusAlertRules = prometheusResponse.json()

            for prometheusAlertGroups in prometheusAlertRules['data']['groups']:
                if 'alerts' in prometheusAlertGroups['name']:
                    for prometheusAlertGroup in prometheusAlertGroups['rules']:
                        currentPrometheusRules.append(prometheusAlertGroup['name'])
            variables.logging.debug('PrometheusAlertRules /(Prometheus)\ - List of prometheusAlertRules - Finished')


            # PrometheusAlertRules - list of PrometheusAlertRules from local storage. (SQL Tables)
            variables.logging.debug('PrometheusAlertRules /(SQL)\ - List of prometheusAlertRules - Started')
            try:
                sqlListOfTables = sqlFunctions.SQL_getListOfAlertsRule()
            except Exception as error:
                variables.logging.fatal('PrometheusAlertRules /(SQL)\ - List of prometheusAlertRules - Failed')
                sys.exit(1)
            else:
                for sqlTable in sqlListOfTables:
                    currentSQLTables.append('%s' %sqlTable)
            variables.logging.debug('PrometheusAlertRules /(SQL)\ - List of prometheusAlertRules - Finished')
            

            # PrometheusAlertRules - list of PrometheusAlertRules from Zabbix. (Zabbix)
            variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - List of prometheusAlertRules - Started')
            try:
                zabbixItems = zabbixFunctions.getListOfItems()
            except Exception as error:
                variables.logging.fatal('PrometheusAlertRules /(Zabbix)\ - List of prometheusAlertRules - Failed')
                sys.exit(1)
            else:
                if zabbixItems:
                    for zabbixItem in zabbixItems:
                        currentZabbixItems.append(zabbixItem['name'])
            variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - List of prometheusAlertRules - Finished')

            # --- Lists ---

            addSQLTables = list(set(currentPrometheusRules) - set(currentSQLTables)) 
            deleteSQLTables = list(set(currentSQLTables) - set(currentPrometheusRules))

            addItemToZabbix = list(set(currentPrometheusRules) - set(currentZabbixItems))
            deleteItemFromZabbix = list(set(currentZabbixItems) - set(currentPrometheusRules))

            if not addSQLTables and not deleteSQLTables and not addItemToZabbix and not deleteItemFromZabbix:
                variables.logging.debug('')
                variables.logging.info('Alert database is up to date')
                variables.logging.debug('')
            else:
                variables.logging.debug('')
                variables.logging.info('List of scheduled changes:')
                variables.logging.info('- - Will be added to SQL: %s' %addSQLTables)
                variables.logging.info('- - Will be removed from SQL: %s' %deleteSQLTables)
                variables.logging.info('- - Will be added to Zabbix: %s' %addItemToZabbix)
                variables.logging.info('- - Will be removed from Zabbix: %s' %deleteItemFromZabbix)
                variables.logging.debug('')

            # Modify SQL - Add
            variables.logging.debug('PrometheusAlertRules /(SQL)\ - Adding missing items - Started')
            if addSQLTables:
                for sqlTableToCreate in addSQLTables:
                    try:
                        sqlFunctions.SQL_createAlertTable(sqlTableToCreate)
                    except Exception as error:
                        variables.logging.fatal('PrometheusAlertRules /(SQL)\ - Adding missing items - Failed')
                        sys.exit(1)
            else:
                variables.logging.debug('PrometheusAlertRules /(SQL)\ - No item is missing')
            variables.logging.debug('PrometheusAlertRules /(SQL)\ - Adding missing items - Finished')

            # Modify SQL - Remove
            variables.logging.debug('PrometheusAlertRules /(SQL)\ - Removing items - Started')
            if deleteSQLTables:
                for sqlTableToDelete in deleteSQLTables:
                    try:
                        sqlFunctions.SQL_deleteAlertTable(sqlTableToDelete)
                    except Exception as error:
                        variables.logging.fatal('PrometheusAlertRules /(SQL)\ - Removing items - Failed')
                        sys.exit(1)
            else:
                variables.logging.debug('PrometheusAlertRules /(SQL)\ - No item is required to remove')
            variables.logging.debug('PrometheusAlertRules /(SQL)\ - Removing items - Finished')


            # Modify Zabbix - Add
            variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - Adding missing items - Started')
            addItemToZabbixJsonList = []
            if addItemToZabbix:
                try:
                    hostnameID = zabbixFunctions.getHostnameId()
                except Exception as error:
                    variables.logging.fatal('PrometheusAlertRules /(Zabbix)\ - Adding missing items - Failed')
                    sys.exit(1)
                else:
                    for zabbixItemToCreate in addItemToZabbix:
                        addItemToZabbixJsonList.append('{"hostid": "%s", "name": "%s", "key_": "%s", "type": "2", "value_type": "2"}' %(hostnameID, zabbixItemToCreate, zabbixItemToCreate))
                    valueZabbix = '[' + ', '.join(addItemToZabbixJsonList) + ']'
                    valueZabbixJson = json.loads(valueZabbix)
                    try:
                        zabbixFunctions.createMultipleItems(valueZabbixJson)
                    except Exception as error:
                        variables.logging.fatal('PrometheusAlertRules /(Zabbix)\ - Adding missing items - Failed')
                        sys.exit(1)
            else:
                variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - No item is missing')
            variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - Adding missing items - Finished')

            # Modify Zabbix - Remove
            variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - Removing items - Started')
            if deleteItemFromZabbix:
                for zabbixItemToDelete in deleteItemFromZabbix:
                    try:
                        zabbixFunctions.deleteItem(zabbixItemToDelete)
                    except Exception as error:
                        variables.logging.fatal('PrometheusAlertRules /(Zabbix)\ - Removing items - Failed')
                        sys.exit(1)
            else:
                variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - No item is required to remove')
            variables.logging.debug('PrometheusAlertRules /(Zabbix)\ - Removing items - Finished')
        else:
            variables.logging.fatal('Got list of PrometheusAlertRules, but reponse is empty. Couldnt be empty!')
            sys.exit(1)


def add_values_in_dict(sample_dict, key, list_of_values):
    if key not in sample_dict:
        sample_dict[key] = list()
    sample_dict[key].extend(list_of_values)
    return sample_dict

def prometheusAlertManager():
    getSearchTime = time.time() - variables.itemCleanThreshold
    listOfAlertsPerTable = {}
    try:
        sqlListOfTables = sqlFunctions.SQL_getListOfAlertsRule()
    except Exception as error:
        variables.logging.fatal('Unexpected problem when creating list of current PrometheusAlerts')
        sys.exit(1)
    else:
        for sqlTable in sqlListOfTables:
            try:
                olderAlerts = sqlFunctions.SQL_getActiveAlertOlderThan(sqlTable,getSearchTime)
            except Exception as error:
                variables.logging.fatal('Unexpected problem when getting older alerts from prometheusAlertRules: %s' %sqlTable)
            else:
                if olderAlerts:
                    a = '%s' %sqlTable
                    listOfAlertsPerTable = add_values_in_dict(listOfAlertsPerTable,a,olderAlerts)
                else:
                    pass
        if listOfAlertsPerTable:
            for table in listOfAlertsPerTable:
                for alert in listOfAlertsPerTable[table]:
                    try:
                        numberOfThreads = sqlFunctions.SQL_getNumberOfThreads()
                    except Exception as error:
                        variables.logging.fatal('Unexpected problem when getting number of currenty running applicationThreads')
                        sys.exit(1)
                    else:
                        try:
                            prometheusAlertRecoveryExists = sqlFunctions.SQL_checkAlertResolved(alert)
                        except Exception as error:
                            variables.logging.fatal('Failed to check if prometheusAlert: %s from prometheusAlertRule: %s is already resolved.' %(alert,table))
                        else:
                            if prometheusAlertRecoveryExists == 1:
                                if int(numberOfThreads) >= int(variables.threadsThreshold):
                                    variables.logging.fatal('Cannot create new applicationThread to handle stale prometheusAlert: %s from prometheusAlertRule: %s. NumberOfThread exceeded' %(alert,table))
                                else:
                                    randomThreadID = random.randint(1,99999999999)
                                    try:
                                        threading.Thread(target=new_body_resolved.newBodyResolved, args=(randomThreadID,table,alert,"None"), daemon=True, name=randomThreadID).start()
                                    except Exception as error:
                                        variables.logging.error('Failed to start applicationThread: %s to handle stale prometheusAlert: %s from prometheusAlertRule: %s.' % (randomThreadID, alert, table))
                                    else:
                                        variables.logging.info('Succesfully started applicationThread: %s to handle stale prometheusAlert: %s from prometheusAlertRule: %s' %(randomThreadID, alert,table))                                
                            elif prometheusAlertRecoveryExists == 0:
                                variables.logging.info('Stale prometheusAlert: %s from prometheusAlertRule: %s is already scheduled' %(alert,table))
        else:
            variables.logging.info('Alert database is up to date')
