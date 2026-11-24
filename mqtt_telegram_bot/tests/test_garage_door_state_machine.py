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

    def test_open_to_cbroken(self, garage_door):
        # force open state
        garage_door.to_open()
        assert garage_door.state == 'open'

        garage_door.lower_reed_zero()
        assert garage_door.state == 'broken'

    def test_closed_to_cbroken(self, garage_door):
        # force open state
        garage_door.to_closed()
        assert garage_door.state == 'closed'

        garage_door.upper_reed_zero()
        assert garage_door.state == 'broken'


class TestGarageDoorStatePublishing(object):

    @pytest.fixture
    def published(self):
        return []

    @pytest.fixture
    def garage_door(self, published):
        return GarageDoor(out_function=lambda m: None,
                          state_function=published.append)

    def test_no_publish_without_change(self, garage_door, published):
        assert garage_door.state == 'moving'
        assert published == []

    def test_moving_to_open(self, garage_door, published):
        garage_door.upper_reed_zero()
        assert published == ['open']

    def test_open_moving_closed(self, garage_door, published):
        garage_door.to_open()
        garage_door.upper_reed_one()
        garage_door.lower_reed_zero()
        assert published == ['open', 'moving', 'closed']

    def test_broken(self, garage_door, published):
        garage_door.to_open()
        garage_door.lower_reed_zero()
        assert published == ['open', 'broken']

    def test_reflexive_transition_not_republished(self, garage_door, published):
        garage_door.to_open()
        garage_door.upper_reed_zero()
        garage_door.lower_reed_one()
        assert published == ['open']

    def test_manual_correction_publishes(self, garage_door, published):
        garage_door.to_closed()
        garage_door.to_open()
        assert published == ['closed', 'open']

    def test_without_state_function(self):
        garage_door = GarageDoor(out_function=lambda m: None)
        garage_door.upper_reed_zero()
        assert garage_door.state == 'open'
