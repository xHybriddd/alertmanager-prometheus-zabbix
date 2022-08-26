from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from time import sleep
from datetime import datetime
import sched, time
import json
import random
import os
import sys
import logging
import threading
    # Files & Functions
import variables
import rule_manager_file
import scheduler_file
from functions import sql as sqlFunctions
from functions import zabbix as zabbixFunctions
    # Thread bodies
import new_body_firing
import new_body_resolved

app = Flask(__name__)
Bootstrap(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
@app.route("/alerts", methods=["POST"])
def resp():
    failed = 0
    warning = 0
    content = request.json

    prometheusAlertRule = content['groupLabels']['alertname']
    try:
        prometheusAlertRuleExists = sqlFunctions.SQL_checkTableExists("alertDatabase", prometheusAlertRule)
    except Exception() as error:
        variables.logging.fatal("Unexpected error when checking if requested prometheusAlertRule: %s exists in SQL" %prometheusAlertRule)
        return "Unexpected error when checking if requested prometheusAlertRule exists in SQL", 502
    else:
        if prometheusAlertRuleExists == 0:
            for prometheusAlert in content['alerts']:
                prometheusAlert_id = prometheusAlert['fingerprint']

                if prometheusAlert['status'] == "firing":
                    try:
                        prometheusAlertExists = sqlFunctions.SQL_checkRowExists("alertDatabase", prometheusAlertRule, prometheusAlert_id)
                    except Exception as error:
                        variables.logging.error('Unexpected problem happened when checking if prometheusAlert: %s from prometheusAlertRule: %s exists in alertDatabase. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                        failed += 1
                        continue
                    else:
                        if prometheusAlertExists == 0:
                            # Alert exists
                            # 1 - Alert status must be in state COMPLETED
                            # 2 - Alert couldnt be in resolvedThreads in threadDatabase
                            #    - Update timestemp
                            #    - Sent values
                            try:
                                alertStatus = sqlFunctions.SQL_getAlertStatus(prometheusAlertRule, prometheusAlert_id)
                            except Exception as error:
                                variables.logging.error('Failed to check status of prometheusAlert: %s from prometheusAlertRule: %s in database. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                failed += 1
                                continue
                            else:
                                if alertStatus == "COMPLETED":
                                    try:
                                        prometheusAlertRecoveryExists = sqlFunctions.SQL_checkAlertResolved(prometheusAlert_id)
                                    except Exception as error:
                                        variables.logging.error('Failed to check if prometheusAlert: %s from prometheusAlertRule: %s is already resolved. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                        failed += 1
                                        continue
                                    else:
                                        if prometheusAlertRecoveryExists == 1:
                                            try:
                                                prometheusAlert_currentTime = time.time()
                                                sqlFunctions.SQL_updateAlertTime(prometheusAlertRule,prometheusAlert_id,prometheusAlert_currentTime)
                                            except Exception as error:
                                                variables.logging.error('Failed to update timestemp for prometheusAlert: %s from prometheusAlertRule: %s. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                                failed += 1
                                                continue
                                            else:
                                                try:
                                                    listAlerts = sqlFunctions.SQL_getListOfAlets(prometheusAlertRule)
                                                    zabbixFunctions.sendAlert(prometheusAlertRule,listAlerts)
                                                except Exception as error:
                                                    variables.logging.error('Failed to send values to already existed prometheusAlert: %s from prometheusAlertRule: %s. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                                    failed += 1
                                                    continue
                                                else:
                                                    variables.logging.info('Succesfully sended values to already existed prometheusAlert: %s from prometheusAlertRule: %s' %(prometheusAlert_id,prometheusAlertRule))                   
                                        elif prometheusAlertRecoveryExists == 0:
                                            variables.logging.warning('Firing prometheusAlert: %s from prometheusAlertRule: %s is already scheduled as recovered. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                            warning += 1
                                            continue
                                else:
                                    variables.logging.warning('Firing prometheusAlert (already existed): %s from prometheusAlertRule: %s is in state: %s. Expected state "COMPLETED". Continue with next one..' %(prometheusAlert_id,prometheusAlertRule,alertStatus))
                                    warning += 1
                                    continue
                        elif prometheusAlertExists == 1:
                            # Alert doesnt exists
                            prometheusAlert_name = prometheusAlert['annotations']['zabbix_trigger_name']
                            if not prometheusAlert_name:
                                variables.logging.error('New prometheusAlert: %s from prometheusAlertRule: %s cannot be created. Annotation "zabbix_trigger_name" is empty' %(prometheusAlert_id,prometheusAlertRule))
                                failed += 1
                                continue
                            else:
                                prometheusAlert_severity = prometheusAlert['annotations']['zabbix_trigger_severity']
                                if not prometheusAlert_severity:
                                    variables.logging.error('New prometheusAlert: %s from prometheusAlertRule: %s cannot be created. Annotation "zabbix_trigger_severity" is empty' %(prometheusAlert_id,prometheusAlertRule))
                                    failed += 1
                                    continue
                                else:
                                    if (prometheusAlert_severity != 'disaster' and prometheusAlert_severity != 'high' and prometheusAlert_severity != 'average' and prometheusAlert_severity != 'warning' and prometheusAlert_severity != 'information'):
                                        variables.logging.error('New prometheusAlert: %s from prometheusAlertRule: %s cannot be created. Annotation "zabbix_trigger_severity" does not containe required values' %(prometheusAlert_id,prometheusAlertRule))
                                        failed += 1
                                        continue
                                    else:
                                        prometheusAlert_importance = prometheusAlert['annotations']['zabbix_trigger_importance']
                                        if not prometheusAlert_importance:
                                            variables.logging.error('New prometheusAlert: %s from prometheusAlertRule: %s cannot be created. Annotation "zabbix_trigger_importance" is empty' %(prometheusAlert_id,prometheusAlertRule))
                                            failed += 1
                                            continue
                                        else:
                                            prometheusAlert_description = prometheusAlert['annotations']['summary']
                                            if not prometheusAlert_description:
                                                variables.logging.error('New prometheusAlert: %s from prometheusAlertRule: %s cannot be created. Annotation "summary" is empty' %(prometheusAlert_id,prometheusAlertRule))
                                                failed += 1
                                                continue
                                            else:
                                                prometheusAlert_currentTime = time.time()
                                                try:
                                                    numberOfThreads = sqlFunctions.SQL_getNumberOfThreads()
                                                except Exception as error:
                                                    variables.logging.error('Failed to start applicationThread to handle new firing prometheusAlert: %s from prometheusAlertRule: %s' %(prometheusAlert_id,prometheusAlertRule))
                                                    failed += 1
                                                    continue
                                                else:
                                                    if int(numberOfThreads) >= int(variables.threadsThreshold):
                                                        variables.logging.error('Failed to start applicationThread to handle new firing prometheusAlert: %s from prometheusAlertRule: %s. NumberOfThread exceeded.' %(prometheusAlert_id,prometheusAlertRule))
                                                        failed += 1
                                                        continue
                                                    else:
                                                        try:
                                                            randomThreadID = random.randint(1,99999999999)
                                                            threading.Thread(target=new_body_firing.newBodyFiring, args=(randomThreadID,prometheusAlertRule,prometheusAlert_id,prometheusAlert_name,prometheusAlert_description,prometheusAlert_severity,prometheusAlert_importance,"None"), daemon=True, name=randomThreadID).start()
                                                        except Exception as error:
                                                            variables.logging.error('Failed to start applicationThread: %s to handle new firing prometheusAlert: %s from prometheusAlertRule: %s' %(randomThreadID,prometheusAlert_id,prometheusAlertRule))
                                                            failed += 1
                                                            continue
                                                        else:
                                                            variables.logging.info('Succesfully started applicationThread: %s to handle new firing prometheusAlert: %s from prometheusAlertRule: %s' %(randomThreadID,prometheusAlert_id,prometheusAlertRule))
                elif prometheusAlert['status'] == "resolved":
                    # 1 - Alert status must be in state COMPLETED
                    # 2 - Alert couldnt be in resolvedThreads in threadDatabase
                    try:
                        alertStatus = sqlFunctions.SQL_getAlertStatus(prometheusAlertRule, prometheusAlert_id)
                    except Exception as error:
                        variables.logging.error('Failed to check status of prometheusAlert: %s from prometheusAlertRule: %s in database. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                        failed += 1
                        continue
                    else:
                        if alertStatus == "COMPLETED":
                            try:
                                prometheusAlertRecoveryExists = sqlFunctions.SQL_checkAlertResolved(prometheusAlert_id)
                            except Exception as error:
                                variables.logging.error('Failed to check if prometheusAlert: %s from prometheusAlertRule: %s is already resolved. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                failed += 1
                                continue
                            else:
                                if prometheusAlertRecoveryExists == 1:
                                    try:
                                        numberOfThreads = sqlFunctions.SQL_getNumberOfThreads()
                                    except Exception as error:
                                        variables.logging.error('Failed to start applicationThread to handle resolved prometheusAlert: %s from prometheusAlertRule: %s. NumberOfThread exceeded.' %(prometheusAlert_id,prometheusAlertRule))
                                        failed += 1
                                        continue
                                    else:
                                        if int(numberOfThreads) >= int(variables.threadsThreshold):
                                            variables.logging.error('Failed to start applicationThread to handle resolved prometheusAlert: %s from prometheusAlertRule: %s. NumberOfThread exceeded.' %(prometheusAlert_id,prometheusAlertRule))
                                            failed += 1
                                            continue
                                        else:
                                            try:
                                                randomThreadID = random.randint(1,99999999999)
                                                threading.Thread(target=new_body_resolved.newBodyResolved, args=(randomThreadID,prometheusAlertRule,prometheusAlert_id,"None"), daemon=True, name=randomThreadID).start()
                                            except Exception as error:
                                                variables.logging.error('Failed to start applicationThread: %s to handle resolved prometheusAlert: %s from prometheusAlertRule: %s' %(randomThreadID,prometheusAlert_id,prometheusAlertRule))
                                                failed += 1
                                                continue
                                            else:
                                                variables.logging.info('Succesfully started applicationThread: %s to handle resolved prometheusAlert: %s from prometheusAlertRule: %s' %(randomThreadID,prometheusAlert_id,prometheusAlertRule))
                                elif prometheusAlertRecoveryExists == 0:
                                    variables.logging.warning('Resolved prometheusAlert: %s from prometheusAlertRule: %s is already scheduled as recovered. Continue with next one..' %(prometheusAlert_id,prometheusAlertRule))
                                    warning += 1
                                    continue
                        elif alertStatus == "None":
                            variables.logging.warning('Resolved prometheusAlert: %s from prometheusAlertRule: %s does not exist in database' %(prometheusAlert_id,prometheusAlertRule))
                            warning += 1
                            continue
                        else:
                            variables.logging.warning('Resolved prometheusAlert: %s from prometheusAlertRule: %s is in state: %s. Expected state "COMPLETED". Continue with next one..' %(prometheusAlert_id,prometheusAlertRule,alertStatus))
                            warning += 1
                            continue
            if failed == 0:
                return "Nothing failed", 200
            else:
                return "Something failed", 502
        elif prometheusAlertRuleExists == 1:
            variables.logging.warning("prometheusAlertRule: %s doesn't exists yet in database. Need to wait for reload database.." %prometheusAlertRule)
            return "PrometheusAlertRule %s doesn't exists yet in database. Need to wait for reload database.." %prometheusAlertRule, 200


@app.route("/healthz", methods=["GET"])
def healthz():
    lot = threading.enumerate()
    handler = False
    for t in lot:
        if t.name == "scheduler":
            handler = True
        else:
            pass
    
    if handler:
        return jsonify(
          scheduler="healthy",
          server="healthy"
      ),200
    else:
        return jsonify(
          scheduler="failed",
          server="healthy"
        ),500

# Applicatation deleteing menu
# |----------------------------------|

# Main 
@app.route('/menu')
def menu():
    return render_template('index.html')

# Show all firingThread
@app.route('/select_firing_thread')
def select_firing_thread():
    try:
        threads = sqlFunctions.SQL_MENU_getListOfThreads("firingThreads")
    except Exception as error:
        message = f"Failed to get list of application firingThreads. Please, try it again later.."
        return render_template('error.html', pageheading="Internal server error (500)", error=message),500
    else:
        return render_template('select_firing_thread.html', threads=threads)

# Show all resolvedThreads
@app.route('/select_resolved_thread')
def select_resolved_thread():
    try:  
        threads = sqlFunctions.SQL_MENU_getListOfThreads("resolvedThreads")
    except Exception as error:
        message = f"Failed to get list of application resolvedThreads. Please, try it again later.."
        return render_template('error.html', pageheading="Internal server error (500)", error=message),500
    else:
        return render_template('select_resolved_thread.html', threads=threads)

# Show all PrometheusAlertRules
@app.route('/select_prometheus_rule')
def select_prometheus_rule():
    try:
        rules = sqlFunctions.SQL_getListOfAlertsRule()
    except Exception as error:
        message = f"Failed to get list of PrometheusRules. Please, try it again later.."
        return render_template('error.html', pageheading="Internal server error (500)", error=message),500
    else:
        return render_template('list_of_prometheus_rule.html', rows=rules)

# Show all PrometheusAlerts from selected PrometheusAlertRule
@app.route('/select_prometheus_alert/<rule>')
def select_prometheus_alert(rule):
    try:
        alerts = sqlFunctions.SQL_MENU_getListOfAlerts(rule)
    except Exception as error:
        message = f"Failed to get list of PrometheusAlerts. Please, try it again later.."
        return render_template('error.html', pageheading="Internal server error (500)", error=message),500
    else:  
        return render_template('select_prometheus_alert.html', alerts=alerts, rule=rule)

# Confirmation form for deleting required thread (firing or resolved)
@app.route('/delete_threads/<table>', methods=['POST'])
def delete_threads(table):
    if table == 'firingThreads':
        try:
            threadInfo = sqlFunctions.SQL_getThreadInformation(table,request.form['id'])
        except Exception as error:
            message = f"Failed to get inforamations about required thread. Please, try it again later.."
            return render_template('error.html', pageheading="Internal server error (500)", error=message),500
        else:
            return render_template('delete_firing_threads.html', thread=threadInfo)

    elif table == 'resolvedThreads':
        try:
            threadInfo = sqlFunctions.SQL_getThreadInformation(table,request.form['id'])
        except Exception as error:
            message = f"Failed to get inforamations about required thread. Please, try it again later.."
            return render_template('error.html', pageheading="Internal server error (500)", error=message),500
        else: 
            return render_template('delete_resolved_threads.html', thread=threadInfo)

# Confirmation form for deleting required PrometheusAlert from required PrometheusAlertRue
@app.route('/delete_prometheus_alert/<table>', methods=['POST'])
def delete_prometheus_alert(table):
    try:
        alertInfo = sqlFunctions.SQL_MENU_getAlertInfo(table,request.form['id'])
    except Exception as error:
        message = f"Failed to get inforamations about required PrometheusAlert. Please, try it again later.."
        return render_template('error.html', pageheading="Internal server error (500)", error=message),500
    else:       
        return render_template('delete_prometheus_alert.html', alert=alertInfo, table=table)

# FINAL DELETE required thread (firing or resolved)
@app.route('/delete_threads_result/<table>,<id>', methods=['POST'])
def delete_threads_result(table,id):
    if table == 'firingThreads':
        try:
            sqlFunctions.SQL_deleteThread(id,table)
        except Exception as error:
            message = f"Firing Application thread has NOT been successfully deleted from internal database. Please, try again later.."
            return render_template('delete_threads_result.html', message=message, table=table)
        else:
            message = f"Firing Application thread has been successfully deleted from internal database"
            return render_template('delete_threads_result.html', message=message, table=table)

    elif table == 'resolvedThreads':
        try:
            sqlFunctions.SQL_deleteThread(id,table)
        except Exception as error:
            message = f"Resolved Application thread has NOT been successfully deleted from internal database. Please, try again later.."
            return render_template('delete_threads_result.html', message=message, table=table)
        else:
            message = f"Resolved Application thread has been successfully deleted from internal database"
            return render_template('delete_threads_result.html', message=message, table=table)

# FINAL DELETE required PrometheusAlert from required PrometheusAlertRue
@app.route('/delete_prometheus_alert_result/<table>,<id>', methods=['POST'])
def delete_prometheus_alert_result(table,id):
    try:
        sqlFunctions.SQL_deleteAlert(table,id)
    except Exception as error:
        message = f"PrometheusAlert has NOT been successfully deleted from internal database. Please, try again later.."
        return render_template('delete_prometheus_alert_result.html', message=message, table=table)
    else:
        message = f"PrometheusAlert has been successfully deleted from internal database"
        return render_template('delete_prometheus_alert_result.html', message=message, table=table)
# |----------------------------------|

if __name__ == '__main__':
    variables.logging.info('- - LOGGER......%s' %variables.logLevel)
    variables.logging.info('- - ZabbixApiUrl......%s' %variables.zabbixApiUrl)
    variables.logging.info('- - ZabbixUrl......%s' %variables.zabbixUrl)
    variables.logging.info('- - ZabbixHost......%s' %variables.zabbixHost)
    variables.logging.info('- - ZabbixUsername......%s' %variables.zabbixUsername)
    variables.logging.info('- - ZabbixPassword......X-X-X-X')
    variables.logging.info('- - PrometheusUrl......%s' %variables.prometheusUrl)
    variables.logging.info('- - AlertDatabase......%s' %variables.alertDatabase)
    variables.logging.info('- - ThreadDatbase......%s' %variables.threadDatabase)
    variables.logging.info('- - MaximumThreads......%s' %variables.threadsThreshold)
    variables.logging.info('- - RemoveAlertAfter......%ss' %variables.itemCleanThreshold)
    variables.logging.info('- - ReloadRulesAfter......%ss' %variables.appReloader)
    variables.logging.info('')

    # Init of pod (create required thread tables)
    try:
        sqlFunctions.SQL_createThreadTable()
    except Exception as error:
        variables.logging.fatal('Failed to create required tables in threadDatabase..')
        sys.exit(1)
    
    # Finish all remaning thread in database
    variables.logging.info('Starting with initialization of whole pod..')
    scheduler_file.consumeRemaningThreads()
    variables.logging.info('==================================================')
    variables.logging.info('')
    variables.logging.info('        Intialization of Zabbix & SQL')
    variables.logging.info('')

    # Sync PrometheusAlertRues
    rule_manager_file.prometheusAlertRuleManager()
    variables.logging.info('')
    variables.logging.info('==================================================')
    variables.logging.info('')
    variables.logging.info('Whole pod is succesfully initializated...')
    variables.logging.info('Starting process "scheduler"...')
    
    # Start of Scheduler
    try:
        threading.Thread(target=scheduler_file.scheduler, daemon=True, name="scheduler").start()
    except Exception as error:
        variables.logging.fatal('Failed to start process "scheduler"')
        sys.exit(1)
    else:
        # Start HTTP Server
        variables.logging.info('Starting HTTP Server...')
        app.run(host='0.0.0.0', port=5000)