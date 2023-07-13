#!/usr/bin/python
# -*- coding:utf-8 -*-
# Filename: main.py

import argparse
from app.exporter import MetricExporter
from prometheus_client import start_http_server
import logging


class key_value_arg(argparse.Action):
    def __call__(self, parser, namespace,
                 values, option_string=None):
        setattr(namespace, self.dest, dict())

        for kvpair in values:
            assert len(kvpair.split("=")) == 2

            key, value = kvpair.split("=")
            getattr(namespace, self.dest)[key] = value


def get_args():
    parser = argparse.ArgumentParser(
        description="Kubernetes Cost Exporter, exposing Kubernetes cost data as Prometheus metrics.")
    parser.add_argument("-p", "--port", default=9090, type=int,
                        help="Exporter's port (default: 9090)")
    parser.add_argument("-i", "--interval", default=60, type=int,
                        help="Update interval in seconds (default: 60)")
    parser.add_argument("-e", "--endpoint", default="http://kubecost-cost-analyzer.monitoring.svc:9003",
                        help="Kubecost service endpoint (default: http://kubecost-cost-analyzer.monitoring.svc:9003)")
    parser.add_argument("-a", "--aggregate", default="namespace",
                        help="Aggregation level, e.g., namespace, cluster")
    parser.add_argument("-l", "--label", nargs="*", action=key_value_arg,
                        help="Additional labels that need to be added to the metric, \
                            may be used several times, e.g., --label project=foo environment=dev")
    args = parser.parse_args()

    return args


def main(args):
    app_metrics = MetricExporter(
        endpoint=args.endpoint,
        aggregate=args.aggregate,
        interval=args.interval,
        extra_labels=args.label
    )
    start_http_server(args.port)
    app_metrics.run_metrics_loop()


if __name__ == "__main__":
    logger_format = "%(asctime)-15s %(levelname)-8s %(message)s"
    logging.basicConfig(level=logging.INFO, format=logger_format)
    args = get_args()
    main(args)
