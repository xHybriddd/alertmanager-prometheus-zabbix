# Alertmanager (Prometheus) to Zabbix
Application to forward Prometheus alerts from Alertmanager to Zabbix with dynamic trigger name and severity.

App is creating Zabbix triggers when Prometheus alert is firing with rendered labels values.

Application uses a sqlite3 database with storage in /databases/ folder (could be a PVC of Kubernetes)

---

## Todo

- Describe (How to deploy, how to use it, how to configure etc)
- Add Kubernetes manifests examples
