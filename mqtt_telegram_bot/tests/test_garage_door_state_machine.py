import pytest
from mqtt_telegram_bot.garage_door_state_machine import GarageDoor


class TestGarageDoor(object):

    @pytest.fixture
    def garage_door(self):
        return GarageDoor()

    def test_initial_state(self, garage_door):
        assert garage_door.state == 'moving'

    def test_closed_to_moving(self, garage_door):
        # force closed state
        garage_door.to_closed()
        assert garage_door.state == 'closed'

        garage_door.lower_reed_one()
        assert garage_door.state == 'moving'

    def test_closed_to_closed(self, garage_door):
        # force closed state
        garage_door.to_closed()
        assert garage_door.state == 'closed'

        garage_door.upper_reed_one()
        assert garage_door.state == 'closed'

        garage_door.lower_reed_zero()
        assert garage_door.state == 'closed'

    def test_open_to_open(self, garage_door):
        # force open state
        garage_door.to_open()
        assert garage_door.state == 'open'

        garage_door.upper_reed_zero()
        assert garage_door.state == 'open'

        garage_door.lower_reed_one()
        assert garage_door.state == 'open'

    def test_open_to_moving(self, garage_door):
        # force open state
        garage_door.to_open()
        assert garage_door.state == 'open'

        garage_door.upper_reed_one()
        assert garage_door.state == 'moving'

    def test_moving_to_open(self, garage_door):
        assert garage_door.state == 'moving'

        garage_door.upper_reed_zero()
        assert garage_door.state == 'open'

    def test_moving_to_closed(self, garage_door):
        assert garage_door.state == 'moving'

        garage_door.lower_reed_zero()
        assert garage_door.state == 'closed'
