#!/usr/bin/python
# -*- coding:utf-8 -*-
# Filename: exporter.py

import time
import requests
from prometheus_client import Gauge
import logging


class MetricExporter:
    def __init__(self, endpoint, aggregate, interval, extra_labels):
        self.endpoint = endpoint
        self.aggregate = aggregate
        self.interval = interval
        self.extra_labels = extra_labels
        self.labels = set([aggregate])
        if extra_labels is not None:
            self.labels.update(extra_labels.keys())
        self.kubernetes_daily_cost_usd = Gauge(
            "kubernetes_daily_cost_usd", "Kubernetes daily cost in USD aggregated by %s" % self.aggregate, self.labels)

    def run_metrics_loop(self):
        while True:
            self.fetch()
            time.sleep(self.interval)

    def fetch(self):
        api = (f"/allocation/view?aggregate={self.aggregate}&window=today&shareIdle=true&idle=true&"
               "idleByNode=false&shareTenancyCosts=true&shareNamespaces=&shareCost=NaN&"
               "shareSplit=weighted&chartType=costovertime&costUnit=cumulative&step=")
        response = requests.get(self.endpoint + api)
        if (response.status_code != 200 or response.json().get("code") != 200):
            logging.error("error while fetching data from %s, status code %s, message %s!" % (
                api, response.status_code, response.text))
        items = response.json()["data"]["items"]["items"]
        for item in items:
            if self.extra_labels:
                self.kubernetes_daily_cost_usd.labels(
                    **{self.aggregate: item["name"]}, **self.extra_labels).set(item["totalCost"])
            else:
                self.kubernetes_daily_cost_usd.labels(
                    **{self.aggregate: item["name"]}).set(item["totalCost"])
