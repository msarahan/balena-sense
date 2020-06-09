#!/bin/sh

influx_plugin_version="7.0.0"
wget -O "/tmp/influx_plugin.zip" https://github.com/grafana/influxdb-flux-datasource/releases/download/v${influx_plugin_version}/grafana-influxdb-flux-datasource-${influx_plugin_version}.zip
unzip -d /usr/share/grafana/data/plugins "/tmp/influx_plugin.zip"