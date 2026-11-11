"""LabMeasurement смарт-келісімшартының Python-дағы моделі (нұсқа 22).

S2 (increaseBy), S3 (decreaseBy), V2 (getScaled)
STEP = 6; MIN_VALUE = 6; FACTOR = 3; INIT = 102
"""


class LabMeasurement:
    STEP = 6
    MIN_VALUE = 6
    FACTOR = 3

    def __init__(self, initial: int, deployer: str = "owner"):
        self.owner = deployer
        self.current_value = initial
        self.update_count = 0
        self.events = []  # (by, oldValue, newValue)

    def _only_owner(self, sender: str) -> None:
        if sender != self.owner:
            raise ValueError("Only owner")

    def get_value(self) -> int:
        return self.current_value

    def increase_by(self, x: int, sender: str) -> None:
        self._only_owner(sender)
        if not x <= self.STEP:
            raise ValueError("Step too large")
        self.events.append((sender, self.current_value, self.current_value + x))
        self.current_value += x
        self.update_count += 1

    def decrease_by(self, x: int, sender: str) -> None:
        self._only_owner(sender)
        if not self.current_value >= x + self.MIN_VALUE:
            raise ValueError("Below minimum")
        self.events.append((sender, self.current_value, self.current_value - x))
        self.current_value -= x
        self.update_count += 1

    def get_scaled(self) -> int:
        return self.current_value * self.FACTOR


def expect_revert(label, func, *args):
    try:
        func(*args)
    except ValueError as e:
        print(f"{label}: revert -> {e}")
    else:
        print(f"{label}: ҚАТЕ - revert болмады!")


if __name__ == "__main__":
    OWNER, OTHER = "owner", "other"
    c = LabMeasurement(102, OWNER)
    print(f"Deploy: getValue() = {c.get_value()}")

    # 4-қадам: сценарий
    c.increase_by(6, OWNER)
    print(f"increaseBy(6): currentValue = {c.current_value}, updateCount = {c.update_count}")
    c.decrease_by(4, OWNER)
    print(f"decreaseBy(4): currentValue = {c.current_value}, updateCount = {c.update_count}")
    print(f"getScaled() = {c.get_scaled()}")

    # 5-қадам: revert тесттері
    expect_revert("increaseBy(STEP + 1 = 7)", c.increase_by, c.STEP + 1, OWNER)
    expect_revert("decreaseBy(currentValue)", c.decrease_by, c.current_value, OWNER)
    expect_revert("increaseBy(1) басқа аккаунттан", c.increase_by, 1, OTHER)

    # 6-қадам: оқиғалар
    for i, (by, old, new) in enumerate(c.events, 1):
        print(f"ValueChanged #{i}: by={by}, oldValue={old}, newValue={new}")

    # state revert кезінде өзгермегенін тексеру
    assert (c.current_value, c.update_count) == (104, 2)
    assert c.get_scaled() == 312