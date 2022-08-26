import logging
import os
import sys

# Setup Logger of application (For container app)

logLevel = os.getenv('LOG_LEVEL')

if logLevel == "DEBUG":
  logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(threadName)s: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
  )
else:
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(threadName)s: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
  )

if 'ZABBIX_SERVER' in os.environ:
  zabbixUrl =  os.getenv('ZABBIX_SERVER')
else:
  logging.fatal('Missing required variable "ZABBIX_SERVER"')
  sys.exit(1)
if 'ZABBIX_API_URL' in os.environ:
  zabbixApiUrl =  os.getenv('ZABBIX_API_URL')
else:
  logging.fatal('Missing required variable "ZABBIX_API_URL"')
  sys.exit(1)
if 'ZABBIX_HOST' in os.environ:
  zabbixHost =  os.getenv('ZABBIX_HOST')
else:
  logging.fatal('Missing required variable "ZABBIX_HOST"')
  sys.exit(1)
if 'ZABBIX_USERNAME' in os.environ:
  zabbixUsername =  os.getenv('ZABBIX_USERNAME')
else:
  logging.fatal('Missing required variable "ZABBIX_USERNAME"')
  sys.exit(1)
if 'ZABBIX_PASSWORD' in os.environ:
  zabbixPassowrd =  os.getenv('ZABBIX_PASSWORD')
else:
  logging.fatal('Missing required variable "ZABBIX_PASSWORD"')
  sys.exit(1)
if 'PROMETHEUS_URL' in os.environ:
  prometheusUrl =  os.getenv('PROMETHEUS_URL')
else:
  logging.fatal('Missing required variable "PROMETHEUS_URL"')
  sys.exit(1)
if 'THREADS_THRESHOLD' in os.environ:
  threadsThreshold =  os.getenv('THREADS_THRESHOLD')
else:
  logging.info('Optional variable "THREADS_THRESHOLD" is not set up. Using default value: 20')
  threadsThreshold =  20
if 'ALERT_LIFE_THRESHOLD' in os.environ:
  itemCleanThreshold =  os.getenv('ALERT_LIFE_THRESHOLD')
else:
  logging.info('Optional variable "ALERT_LIFE_THRESHOLD" is not set up. Using default value: 1800s')
  itemCleanThreshold =  1800
if 'DATABASE_RELOAD' in os.environ:
  appReloader =  os.getenv('DATABASE_RELOAD')
else:
  logging.info('Optional variable "DATABASE_RELOAD" is not set up. Using default value: 60s')
  appReloader =  60


alertDatabase = "/databases/prometheusAlerts.db"
threadDatabase = "/databases/serverThreads.db"
