from pyzabbix import ZabbixAPI, ZabbixAPIException, ZabbixMetric, ZabbixSender
import sys
import time
import json
# Files
import variables

def zabbixLogin():
    try:
        zabbix = ZabbixAPI(url=variables.zabbixApiUrl, user=variables.zabbixUsername, password=variables.zabbixPassowrd)
    except:
        return 2
    else:
        return zabbix

def createTrigger(nameOfItem, triggerID, nameOfTrigger, triggerDescription, triggerSeverity, triggerImportance):
    if "disaster" in triggerSeverity:
        severity = 5
    elif "high" in triggerSeverity:
        severity = 4
    elif "average" in triggerSeverity:
        severity = 3
    elif "warning" in triggerSeverity:
        severity = 2
    elif "information" in triggerSeverity:
        severity = 1
    
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:
            if nameOfItem == "Watchdog":
                trigger = zabbixConnection.trigger.create(
                    expression='nodata(/%s/%s,600s)=1'%(variables.zabbixHost,nameOfItem),
                    description=nameOfTrigger,
                    comments=triggerDescription,
                    priority=severity,
                    url=nameOfItem,
                    tags=[
                        {
                            "tag": triggerID,
                            "value": ""
                        },
                        {
                            "tag": "importance",
                            "value": triggerImportance
                        }

                    ]
                )
            else:
                trigger = zabbixConnection.trigger.create(
                    expression='find(/%s/%s,,,"%s")=1'%(variables.zabbixHost,nameOfItem,triggerID),
                    description=nameOfTrigger,
                    comments=triggerDescription,
                    priority=severity,
                    url=nameOfItem,
                    tags=[
                        {
                            "tag": triggerID,
                            "value": ""
                        },
                        {
                            "tag": "importance",
                            "value": triggerImportance
                        }
                    ]
                )
        except ZabbixAPIException as e:
            raise Exception()
        else:
            return 0

def getTriggerById(triggerId):
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        return 2
    else:
        try:
            trigger = zabbixConnection.trigger.get(tags=[{"tag": triggerId}],host=variables.zabbixHost,output=['triggerid'])
        except ZabbixAPIException as e:
            return 1
        else:
            if trigger:
                return trigger
            else:
                return 1

def getTriggerStatus(triggerId):
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:
            trigger = zabbixConnection.trigger.get(tags=[{"tag": triggerId}],host=variables.zabbixHost,output=['value'])
        except ZabbixAPIException as e:
            raise Exception()
        else:
            if trigger:
                a = str(trigger)
                b = a.replace("\'", "\"")
                test = json.loads(b)
                if test[0]['value'] == 0:
                    return 0
                elif test[0]['value'] == 1:
                    raise Exception()

def getListOfItems():
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:    
            items = zabbixConnection.item.get(host=variables.zabbixHost)
        except ZabbixAPIException as e:
            raise Exception()
        else:
            return items


def getItemId(nameOfItem):
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        return 2
    else:
        try:    
            item = zabbixConnection.item.get(search={"key_":nameOfItem}, host=variables.zabbixHost)
        except ZabbixAPIException as e:
            variables.logging.error('[zabbix]: Failed to get item from host: %s' %variables.zabbixHost)
            return 1
        else:
            if item:
                return item
            else:
                return 1


def sendAlert(nameOfItem, values):
    packet = [
        ZabbixMetric(variables.zabbixHost, nameOfItem, values)
    ]
    zabbix_server = ZabbixSender(variables.zabbixUrl)
    try:
        out = zabbix_server.send(packet)
    except Exception as e:
        raise Exception()
    else:
        xd = str(out)
        test = json.loads(xd)
        if test['processed'] == 1:
            return 0
        elif test['processed'] == 0:
            raise Exception()

def getHostnameId():
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:
            hosts = zabbixConnection.host.get(filter={"host": variables.zabbixHost})
        except ZabbixAPIException as e:
            raise Exception()
        else:
            if hosts:
                return(hosts[0]["hostid"])
            else:
                raise Exception()

def createMultipleItems(value):
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:
            item = zabbixConnection.item.create(*value)
        except ZabbixAPIException as e:
            raise Exception()
        else:
            if item:
                return 0
            else:
                raise Exception()

def deleteItem(nameOfItem):
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:
            item = getItemId(nameOfItem)
            if item == 1 or item == 2:
                raise Exception()
            else:
                zabbixConnection.item.delete(
                    item[0]["itemid"]
                )
        except ZabbixAPIException as e:
            raise Exception()
        else:
            return 0

def deleteTrigger(triggerId):
    zabbixConnection = zabbixLogin()
    if zabbixConnection == 2:
        raise Exception()
    else:
        try:
            trigger = getTriggerById(triggerId)
            if trigger == 1 or trigger == 2:
                raise Exception()
            else:
                zabbixConnection.trigger.delete(
                    trigger[0]["triggerid"]
                )
        except ZabbixAPIException as e:
            raise Exception()
        else:
            return 0
