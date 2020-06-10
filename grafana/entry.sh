#!/bin/bash
set -x
/usr/src/app/api.sh &

fn="/usr/src/app/provisioning/datasources/influxdb-datasource.yml"
cp $fn.base $fn
cat <<EOT >>$fn
  defaultBucket: ${INFLUX_BUCKET:-""}
  organization: ${INFLUX_ORG:-""}
  url: ${INFLUX_URL:-"http://influxdb:8086"}
  type: ${INFLUX_PLUGIN_TYPE:-"influxdb"}
EOT

if [ -n "$INFLUX_TOKEN" ]; then
  cat <<EOT >>$fn
  secureJsonData:
    token: ${INFLUX_TOKEN}
EOT
fi

exec grafana-server -homepath /usr/share/grafana
