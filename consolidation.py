"""
Attempts to fill containers based upon the following conditions:

Logic:
    Grouping: (pick_up_location, deliver_to_location)
    Sorting: ready_date ascending
    Limits: total_volume < 70.0 & total_weight < 1500
    Conditions:
        1. All items must be within 7 days of earliest ready_date in container
        2. Items in container should ideally have the same 'supplier', but not required

Response:
    1. Generates csv if as_csv is True
    2. Otherwise, returns list[dict] of containers

Example Item:
    {
        "pick_up_location": "pickup A",
        "deliver_to_location": "deliver A",
        "total_volume": 15.0,
        "total_weight": 200.0,
        "supplier": "Supplier 1",
        "ready_date": "2021-01-01",
    }
"""
from collections import defaultdict
from typing import Union

from container import Container, ConsolidationError


class ConsolidationGenerator:
    containers: list
    items: defaultdict

    NULL_VALUES = ("", "nan", "Nan", "NaN", None, "null")

    def __init__(self, as_csv: bool = False):
        self.as_csv = as_csv

        self.containers = []
        self.query_results = []
        self.items = defaultdict(list)

    def run(self) -> list[dict]:
        self._query_data()
        self._group_results()

        return self.containers

    def _query_data(self):
        self.query_results = []

    def _group_results(self):
        for row in self.query_results:
            if not row.get("ready_date"):
                continue

            pickup = row.get("pick_up_location")
            deliver_to = row.get("deliver_to_location")

            key = (pickup, deliver_to)
            if any(isinstance(k, float) for k in key):
                # NaN values
                continue
            elif any(k in self.NULL_VALUES for k in key):
                continue

            self.items[key].append(row)

    def _consolidate(self, items: list, locations: tuple):
        containers = [Container(*locations, item=items.pop(0))]
        for item in items:
            new_container = Container(*locations, item=item)
            containers = self._sorted_containers(containers, new_container)
            for container in containers:
                try:
                    container += new_container
                except ConsolidationError:
                    continue
                else:
                    break
            else:
                containers.append(new_container)
        
        self.containers.extend(containers)

    @staticmethod
    def _sorted_containers(current_containers: list, new_container: Container) -> list:
        pass