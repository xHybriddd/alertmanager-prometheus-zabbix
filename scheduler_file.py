from time import sleep
from datetime import datetime
import sched, time
import json
import random
import os
import sys
import threading
    # Files & Functions
import variables
import rule_manager_file
from functions import sql as sqlFunctions
from functions import zabbix as zabbixFunctions
    # Thread bodies
import new_body_firing
import new_body_resolved

def scheduler():
    while True:
        sleep(variables.appReloader)
        variables.logging.info('Scheduling reload of SQL Databases..')
        try:
            threading.Thread(target=rule_manager_file.prometheusAlertRuleManager, daemon=True, name="PrometheusAlertRule-Sync").start()
        except Exception as error:
            variables.logging.fatal('Failed to start applicationThread (PrometheusAlertRule-Sync) to handle synchronization of PrometheusAlertRules')
        else:
            try:
                threading.Thread(target=rule_manager_file.prometheusAlertManager, daemon=True, name="PrometheusAlert-Cleaner").start()
            except Exception as error:
                variables.logging.fatal('Failed to start applicationThread (PrometheusAlert-Cleaner) to handle stale PrometheusAlerts')


def consumeRemaningThreads():
    # Firing threads now
    variables.logging.info('==================================================')
    variables.logging.info('        Consume remain thread from database')
    variables.logging.info('')
    variables.logging.info('firingThreads - Started')
    try:
        listOfThreadIds = sqlFunctions.SQL_getListOfThreads("firingThreads")
    except Exception as error:
        variables.logging.fatal('firingThreads - Failed to get list of threads from database')
        sys.exit(1)
    else:
        if listOfThreadIds:
            for thread in listOfThreadIds:
                try:
                    thread_info = sqlFunctions.SQL_getThreadInformation("firingThreads",thread)
                except Exception as error:
                    variables.logging.fatal('firingThreads - Failed to get information about remaining threads')
                    sys.exit(1)
                else:
                    print(thread_info)
                    thread_Id = thread_info[0]
                    thread_Status = thread_info[1]
                    prometheusAlert_Rule = thread_info[2]
                    prometheusAlert_Id = thread_info[3]
                    prometheusAlert_Name = thread_info[4]
                    prometheusAlert_Description = thread_info[5]
                    prometheusAlert_Severity = thread_info[6]
                    prometheusAlert_Importance = thread_info[7]

                    # This might not be a best way. Try and check. Maybe (#PŘEPIŠ POKUD PROBLÉM)
                    variables.logging.info('firingThreads - Starting applicationThread: %s to finish (PrometheusAlert: %s, PrometheusAlertRule: %s)' %(thread_Id,prometheusAlert_Id,prometheusAlert_Rule))
                    try:
                        new_body_firing.newBodyFiring(thread_Id,prometheusAlert_Rule,prometheusAlert_Id,prometheusAlert_Name,prometheusAlert_Description,prometheusAlert_Severity,prometheusAlert_Importance,thread_Status)
                    except Exception as error:
                        variables.logging.fatal('firingThreads - Unexpected problem with applicationThread: %s to finish (PrometheusAlert: %s, PrometheusAlertRule: %s)' %(thread_Id,prometheusAlert_Id,prometheusAlert_Rule))
                    else:
                        variables.logging.info('firingThreads - applicationThread: %s is successfully completed' %thread_Id)
        else:
            variables.logging.info('firingThreads - There is no threads that should be consumed')
    variables.logging.info('firingThreads - Finished')
    variables.logging.info('')
    # Resolved threads now
    variables.logging.info('resolvedThreads - Started')
    try:
        listOfThreadIds = sqlFunctions.SQL_getListOfThreads("resolvedThreads")
    except Exception as error:
        variables.logging.fatal('resolvedThreads - Failed to get list of threads from database')
        sys.exit(1)
    else:
        if listOfThreadIds:
            for thread in listOfThreadIds:
                try:
                    thread_info = sqlFunctions.SQL_getThreadInformation("resolvedThreads", thread)
                except Exception as error:
                    variables.logging.fatal('resolvedThreads - Failed to get information about remaining threads')
                    sys.exit(1)
                else:
                    thread_Id = thread_info[0]
                    thread_Status = thread_info[1]
                    prometheusAlert_Rule = thread_info[2]
                    prometheusAlert_Id = thread_info[3]

                    # This might not be a best way. Try and check. Maybe (#PŘEPIŠ POKUD PROBLÉM)
                    variables.logging.info('resolvedThreads - Starting applicationThread: %s to finish (PrometheusAlert: %s, PrometheusAlertRule: %s)' %(thread_Id,prometheusAlert_Id,prometheusAlert_Rule))
                    try:
                        new_body_resolved.newBodyResolved(thread_Id,prometheusAlert_Rule,prometheusAlert_Id,thread_Status)
                    except Exception as error:
                        variables.logging.fatal('resolvedThreads - Unexpected problem with applicationThread: %s to finish (PrometheusAlert: %s, PrometheusAlertRule: %s)' %(thread_Id,prometheusAlert_Id,prometheusAlert_Rule))
                    else:
                        variables.logging.info('resolvedThreads - applicationThread: %s is successfully completed' %thread_Id)
        else:
            variables.logging.info('resolvedThreads - There is no threads that should be consumed')
    variables.logging.info('resolvedThreads - Finished')
    variables.logging.info('')
    variables.logging.info('==================================================')
if __name__ == '__main__':
    consumeRemaningThreads()
