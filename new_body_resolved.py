#
#         Created new thread with firing body
#           Stage 1 - insert self informations in to threadDatabase
#           Stage 2 - update status of alertDatabase
#           Stage 3 - insert values to Zabbix
#           Stage 4 - warit until ZabbixTrigger goes RESOLVED
#           Stage 5 - delete zabbixTrigger
#           Stage 6 - delete alert from alertDatabase
#           Stage 7 - delete self informations from threadDatabase
#

from time import sleep
from datetime import datetime
import time
import sys
import logging
import random
    # Files
import variables
from functions import sql as sqlFunctions
from functions import zabbix as zabbixFunctions

def newBodyResolved(threadId, prometheusAlertRule, prometheusAlertId, lastStage):
    runContinue = False
    
    variables.logging.info('At your service..')
    if lastStage == "None":
        runContinue = True
        # Stage 1
        try: 
            sqlFunctions.SQL_createResolvedThread("resolvedThreads", threadId, "STAGE 1", prometheusAlertRule, prometheusAlertId)
        except Exception as error:
            variables.logging.fatal('Unexpected problem happened when creating myself in to threadDatabase. (prometheusAlert: %s, prometheusAlertRule: %s). Exiting :-(' %(prometheusAlertId, prometheusAlertRule))
            #(#TODO - ZabbixWarning)
            sys.exit(1)

    if lastStage == "None" or lastStage == "STAGE 1" or runContinue is True:
        runContinue = True
        # Stage 2
        while True:
            try:
                sqlFunctions.SQL_updateAlertStatus(prometheusAlertRule, prometheusAlertId, "EPILOG")
            except Exception as error:
                sleepTime = random.randint(1,10)
                variables.logging.error('Failed update prometheusAlert: %s from prometheusAlertRule: %s status to "EPILOG" in alertDatabase.Trying again after: %ss' %(prometheusAlertId, prometheusAlertRule, sleepTime))
                sleep(sleepTime)
            else:
                try:
                    sqlFunctions.SQL_updateThreadStatus(threadId,"resolvedThreads","STAGE 2")
                except Exception as error:
                    variables.logging.error('Failed to update status to state "STAGE 2"' %threadId)
                break

    if lastStage == "None" or lastStage == "STAGE 2" or runContinue is True:
        runContinue = True
        # Stage 3
        while True:
            try:
                listAlerts = sqlFunctions.SQL_getListOfAlets(prometheusAlertRule)
                zabbixFunctions.sendAlert(prometheusAlertRule,listAlerts)
            except Exception as error:
                sleepTime = random.randint(1,10)
                variables.logging.error('Failed to send values to ZabbixTrigger for prometheusAlert: %s from prometheusAlertRule: %s. Trying again after: %ss' %(prometheusAlertId, prometheusAlertRule, sleepTime))
                sleep(sleepTime)
            else:
                try:
                    zabbixFunctions.getTriggerStatus(prometheusAlertId)
                except Exception as error:
                    variables.logging.error('Not getting resolved ZabbixTrigger for prometheusAlert: %s from prometheusAlertRule: %s. Try again after: %ss' %(prometheusAlertId, prometheusAlertRule, sleepTime))
                    sleep(sleepTime)
                else:
                    sleep(4)
                    try:
                        sqlFunctions.SQL_updateThreadStatus(threadId,"resolvedThreads","STAGE 3")
                    except Exception as error:
                        variables.logging.error('Failed to update status to state "STAGE 3"' %threadId)
                    break

    if lastStage == "None" or lastStage == "STAGE 3" or runContinue is True:
        runContinue = True
        # Stage 4
        while True:
            try:
                zabbixFunctions.deleteTrigger(prometheusAlertId)
            except Exception as error:
                sleepTime = random.randint(1,10)
                variables.logging.error('Failed to delete resolved ZabbixTrigger for prometheusAlert: %s from prometheusAlertRule: %s. Try again after: %ss' %(prometheusAlertId, prometheusAlertRule, sleepTime))
                sleep(sleepTime)
            else:
                try:
                    sqlFunctions.SQL_updateThreadStatus(threadId,"resolvedThreads","STAGE 4")
                except Exception as error:
                    variables.logging.error('Failed to update status to state "STAGE 4"' %threadId)
                break

    if lastStage == "None" or lastStage == "STAGE 4" or runContinue is True:
        runContinue = True
        # Stage 5
        while True:
            try:
                sqlFunctions.SQL_deleteAlert(prometheusAlertRule, prometheusAlertId)
            except Exception as error:
                sleepTime = random.randint(1,10)
                variables.logging.error('Unexpected problem happened when deleting prometheusAlert: %s from prometheusAlertRule: %s from alertDatabase. Trying again after: %ss' %(prometheusAlertId, prometheusAlertRule, sleepTime))
                sleep(sleepTime)
            else:
                try:
                    sqlFunctions.SQL_updateThreadStatus(threadId,"resolvedThreads","STAGE 5")
                except Exception as error:
                    variables.logging.error('Failed to update status to state "STAGE 5"' %threadId)
                break
    
    if lastStage == "None" or lastStage == "STAGE 5" or runContinue is True:
        runContinue = True
        # Stage 5
        while True:
            try:
                sqlFunctions.SQL_deleteThread(threadId, "resolvedThreads")
            except Exception as error:
                sleepTime = random.randint(1,10)
                variables.logging.error('Unexpected problem happened when deleting myself from threadDatabase. Trying again after: %ss' %sleepTime)
                sleep(sleepTime)
            else:
                variables.logging.info('Goodbye..')
                break
