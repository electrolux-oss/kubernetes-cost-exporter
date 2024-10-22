#!/usr/bin/python
# -*- coding:utf-8 -*-
# Filename: exporter.py

import time
import requests
from prometheus_client import Gauge
import logging


class MetricExporter:
    def __init__(self, endpoint, aggregate, interval, name, extra_labels):
        self.endpoint = endpoint
        self.aggregate = aggregate
        self.interval = interval
        self.name = name
        self.extra_labels = extra_labels
        self.labels = set(aggregate)
        if extra_labels is not None:
            self.labels.update(extra_labels.keys())
        self.kubernetes_daily_cost_usd = Gauge(
            self.name, "Kubernetes daily cost in USD aggregated by %s" % ", ".join(self.aggregate), self.labels
        )

    def run_metrics_loop(self):
        while True:
            # every time we clear up all the existing labels before setting new ones
            self.kubernetes_daily_cost_usd.clear()
            self.fetch()
            time.sleep(self.interval)

    def fetch(self):
        api = (
            f"/allocation/summary?aggregate={','.join(self.aggregate)}&accumulate=true&chartType=costovertime&"
            "costUnit=cumulative&external=false&filter=&idle=true&idleByNode=false&includeSharedCostBreakdown=true&"
            "shareCost=0&shareIdle=true&shareLabels=&shareNamespaces=&shareSplit=weighted&shareTenancyCosts=true&"
            "window=today"
        )
        response = requests.get(self.endpoint + api)
        if response.status_code != 200 or response.json().get("code") != 200:
            logging.error(
                "error while fetching data from %s, status code %s, message %s!"
                % (api, response.status_code, response.text)
            )
        else:
            allocations = response.json()["data"]["sets"][0]["allocations"]
            for item in allocations:
                aggregation_labels = {}
                names = item.split("/")

                if len(names) != len(self.aggregate):
                    logging.warning(
                        "Record names from a response should map to aggregation labels, expected %s, got %s"
                        % (self.aggregate, names)
                    )
                    continue

                for i in range(len(self.aggregate)):
                    aggregation_labels[self.aggregate[i]] = names[i]

                if self.extra_labels:
                    self.kubernetes_daily_cost_usd.labels(**aggregation_labels, **self.extra_labels).set(
                        allocations[item]["totalCost"]
                    )
                else:
                    self.kubernetes_daily_cost_usd.labels(**aggregation_labels).set(allocations[item]["totalCost"])
            logging.info(f"cost metric {self.name} updated successfully")
