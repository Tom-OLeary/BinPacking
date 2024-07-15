from copy import deepcopy
from dataclasses import dataclass, fields
from datetime import date, datetime, timedelta
from typing import Union


class ConsolidationError(Exception):
    pass


@dataclass
class Item:
    pickup_location: str
    deliver_to_location: str
    supplier: str
    total_volume: float
    total_weight: float
    ready_date: Union[date, datetime, str]

    def __post_init__(self):
        """Data validation"""
        for f in fields(self):
            # handle Nan/None string values
            if f.type not in (str, datetime, date):
                continue

            _value = getattr(self, f.name) or ""
            if isinstance(_value, float):
                _value = ""

            if not _value:
                setattr(self, f.name, _value)

        validation_errors = []
        if not self.pickup_location:
            validation_errors.append(f"Pickup location: {self.pickup_location} cannot be empty")

        if not self.deliver_to_location:
            validation_errors.append(f"Deliver to location: {self.deliver_to_location} cannot be empty")

        if not self.ready_date:
            validation_errors.append(f"Ready date: {self.ready_date} cannot be empty")

        if validation_errors:
            raise TypeError(f"Item validation_errors {validation_errors}")

        self.total_volume = self.total_volume or 0.0
        self.total_weight = self.total_weight or 0.0

        self.ready_date = datetime.strptime(self.ready_date, "%m/%d/%Y")

    @property
    def key(self) -> tuple:
        return self.pickup_location, self.deliver_to_location


class Container:
    MAX_VOLUME: float = 70.0
    MAX_WEIGHT: float = 1500.0
    READY_DATE_WINDOW: int = 7  # days

    def __init__(self, pick_up_location: str, deliver_to_location: str, item: Item):
        self.pick_up_location = pick_up_location
        self.deliver_to_location = deliver_to_location
        self.item = item

        self.total_volume = self.item.total_volume
        self.total_weight = self.item.total_weight
        self.supplier = self.item.supplier
        self.ready_date = self.item.ready_date

        self.container_items = [self.item.__dict__]

    def __iadd__(self, other):
        if (
            self._fails_volume(other.total_volume) or
            self._fails_weight(other.total_weight) or
            not self._fits_window(other.ready_date)
        ):
            raise ConsolidationError()

        self.total_volume += other.total_volume
        self.total_weight += other.total_weight
        self.container_items.extend(other.container_items)

    @property
    def final_dict(self) -> dict:
        _data = deepcopy(self.__dict__)
        _data.pop("item")
        return _data

    def _fails_volume(self, other_volume: float) -> bool:
        if not self.MAX_VOLUME:
            return False

        return self.total_volume + other_volume > self.MAX_VOLUME

    def _fails_weight(self, other_weight: float) -> bool:
        if not self.MAX_WEIGHT:
            return False

        return self.total_weight + other_weight > self.MAX_WEIGHT

    def _fits_window(self, other_ready_date: datetime) -> bool:
        before_window = self.ready_date - timedelta(days=self.READY_DATE_WINDOW)
        after_window = self.ready_date + timedelta(days=self.READY_DATE_WINDOW)
        return before_window <= other_ready_date <= after_window

