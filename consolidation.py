"""
Attempts to fill containers based upon the following conditions:

Logic:
    Grouping: (pick_up_location, deliver_to_location)
    Sorting: ready_date ascending
    Limits: total_volume < 70.0 & total_weight < 1500
    Conditions:
        1. All items must be within 7 days of earliest ready_date in container
        2. Containers must not exceed volume & weight limits

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
import pathlib

import pandas as pd
from collections import defaultdict

from container import Container, ConsolidationError, Item


class GeneratorError(Exception):
    pass


class ConsolidationGenerator:
    containers: list[Container]
    items: defaultdict
    sort_key: str
    sort_reverse: bool

    NULL_VALUES = ("", "nan", "Nan", "NaN", None, "null")

    VALID_SORT_KEYS = [
        "ready_date",
        "supplier",
        "total_volume",
        "total_weight",
    ]

    CSV_PATH = pathlib.Path("ConsolidationExample.csv").resolve()
    CSV_OUTPUT_PATH = "container_output.csv"

    def __init__(self, sort_key: str = None, as_csv: bool = False):
        self._determine_sorting(sort_key or "ready_date")  # ready_date ascending is default
        self.as_csv = as_csv

        self.containers = []
        self.query_results = []
        self.items = defaultdict(list)

    def run(self) -> list[Container]:
        self._query_data()
        self._group_results()

        for locations, items in self.items.items():
            if not items:
                continue

            self._consolidate(self._sorted_items(items), locations)

        if self.as_csv:
            self._generate_csv_output()

        return self.containers

    def _query_data(self):
        """Data being retrieved from csv example file, ideally would be queried from a db"""
        self.query_results = pd.read_csv(self.CSV_PATH).to_dict("records")

    def _group_results(self):
        for row in self.query_results:
            try:
                row_item = Item(**row)
            except TypeError as e:
                # missing data of some sort
                # future state should log these for tracking instead of printing
                print(e)
                continue

            self.items[row_item.key].append(row_item)

    def _consolidate(self, items: list, locations: tuple):
        containers = [Container(*locations, item=items.pop(0))]
        for item in items:
            new_container = Container(*locations, item=item)
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

    def _sorted_items(self, items: list) -> list:
        return sorted(items, key=lambda k: getattr(k, self.sort_key), reverse=self.sort_reverse)

    def _determine_sorting(self, key: str):
        if key[0] == "-":
            self.sort_key = key[1:]
            self.sort_reverse = True
        else:
            self.sort_key = key
            self.sort_reverse = False

        if self.sort_key not in self.VALID_SORT_KEYS:
            raise GeneratorError(f"Sort key {self.sort_key} must be one of {self.VALID_SORT_KEYS}")

    def _generate_csv_output(self):
        pd.DataFrame([c.final_dict for c in self.containers]).to_csv(self.CSV_OUTPUT_PATH, index=False)
