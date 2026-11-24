from transitions import Machine, State

class GarageDoor(object):
    states = [
        State(name='open'), #, on_enter=['door_open']),
        State(name='closed'), # on_enter=['door_closed']),
        State(name='moving'), # on_enter=['start_moving']),
        State(name='broken'), #on_enter=['broken_door'])
    ]

    transitions = [
        {'trigger': 'upper_reed_zero', 'source': ['moving'], 'dest': 'open',
         'after': 'door_open'
        },
        {'trigger': 'upper_reed_zero', 'source': ['open'], 'dest': 'open'},

        {'trigger': 'upper_reed_zero', 'source': ['closed', 'broken'], 'dest': 'broken',
         'after': 'broken_door'
        },
        {'trigger': 'lower_reed_zero', 'source': ['moving'], 'dest': 'closed',
         'after': 'door_closed'
        },
        {'trigger': 'lower_reed_zero', 'source': ['closed'], 'dest': 'closed'},
        {'trigger': 'lower_reed_zero', 'source': ['open', 'broken'], 'dest': 'broken',
         'after': 'broken_door'
        },
        {'trigger': 'upper_reed_one', 'source': ['open', 'broken'], 'dest': 'moving',
         'after': 'start_moving'
        },
        {'trigger': 'upper_reed_one', 'source': ['moving'], 'dest': 'moving'},
        {'trigger': 'upper_reed_one', 'source': ['closed'], 'dest': 'closed'},
        {'trigger': 'lower_reed_one', 'source': ['closed', 'broken'], 'dest': 'moving',
         'after': 'start_moving'
        },
        {'trigger': 'lower_reed_one', 'source': ['moving'], 'dest': 'moving'},
        {'trigger': 'lower_reed_one', 'source': ['open'], 'dest': 'open'},
    ]

    def __init__(self, out_function=print, state_function=None):
        """
        out_function: called with a human readable message on relevant
            state changes (e.g. sent to Telegram).
        state_function: optional, called with the new state name
            ('open', 'closed', 'moving', 'broken') whenever the state
            actually changes (e.g. published to a retained MQTT topic).
        """
        machine = Machine(model=self, states=GarageDoor.states,
                          transitions=GarageDoor.transitions, initial='moving',
                          after_state_change='_publish_state')
        self.send = out_function
        self.publish = state_function
        self.last_send = 1
        self._last_published = None

    def _publish_state(self):
        # after_state_change also fires on reflexive transitions
        # (e.g. open -> open); only publish real changes.
        if self.publish and self.state != self._last_published:
            self._last_published = self.state
            self.publish(self.state)

    def door_open(self):
        self.send('door is now open')
        self.last_send = 1

    def door_closed(self):
        self.send('door is now closed')
        self.last_send = 1

    def start_moving(self):
        self.send('door started moving')
        self.last_send = 1

    def broken_door(self):
        self.send('HELP!!! Door is broken')
