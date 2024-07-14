from datetime import datetime, timedelta


class ConsolidationError(Exception):
    pass


class Container:
    MAX_VOLUME: float = 70.0
    MAX_WEIGHT: float = 1500.0
    READY_DATE_WINDOW: int = 7  # days

    def __init__(self, pick_up_location: str, deliver_to_location: str, item: dict):
        self.pick_up_location = pick_up_location
        self.deliver_to_location = deliver_to_location
        self.item = item

        self.total_volume = self.item["total_volume"]
        self.total_weight = self.item["total_weight"]
        self.supplier = self.item["supplier"]
        self.ready_date = item["ready_date"]

        self.container_items = [self.item]

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

