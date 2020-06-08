#!/bin/sh

version="7.0.3"
influx_plugin_version="7.0.0"

outfile="/tmp/grafana.deb"
download_base="https://dl.grafana.com/oss/release/"
case $1 in
   rpi)  package_file="grafana-rpi_${version}_armhf.deb"
       ;;
   aarch64) package_file="grafana_${version}_arm64.deb"
       ;;
   *) package_file="grafana_${version}_armhf.deb"
esac
wget -O "${outfile}" "${download_base}${package_file}"

wget -O "/tmp/influx_plugin.zip" https://github.com/grafana/influxdb-flux-datasource/releases/download/v${influx_plugin_version}/grafana-influxdb-flux-datasource-${influx_plugin_version}.zip
unzip -d /usr/share/grafana/data/plugins "/tmp/influx_plugin.zip"