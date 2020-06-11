#!/bin/bash
set -x
/usr/src/app/api.sh &

#fn="/usr/src/app/provisioning/datasources/influxdb-datasource.yml"
#cp $fn.base $fn
#cat <<EOT >>$fn
#  defaultBucket: ${INFLUX_BUCKET:-""}
#  organization: ${INFLUX_ORG:-""}
#  orgId: ${INFLUX_ORG_ID:-"1"}
#  url: ${INFLUX_URL:-"http://influxdb:8086"}
#  type: ${INFLUX_PLUGIN_TYPE:-"influxdb"}
#EOT
#
#if [ -n "$INFLUX_TOKEN" ]; then
#  cat <<EOT >>$fn
#  secureJsonData:
#    token: ${INFLUX_TOKEN}
#EOT
#fi

if [ ! -z ${TIMEZONE+x} ]; then
  echo "${TIMEZONE}" > /etc/timezone
  dpkg-reconfigure tzdata
  # should be enough above... but let's do this too, just in case
  ln -sf /usr/share/zoneinfo/$TIMEZONE /etc/localtime
fi

exec grafana-server -homepath /usr/share/grafana
