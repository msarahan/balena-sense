#!/bin/sh

influx_plugin_version="7.0.0"
wget -O "/tmp/influx_plugin.zip" https://github.com/msarahan/influxdb-flux-datasource/archive/master.zip
#wget -O "/tmp/influx_plugin.zip" https://github.com/grafana/influxdb-flux-datasource/releases/download/v${influx_plugin_version}/grafana-influxdb-flux-datasource-${influx_plugin_version}.zip
mkdir -p /usr/share/grafana/data/plugins
unzip -d /usr/share/grafana/data/plugins "/tmp/influx_plugin.zip"