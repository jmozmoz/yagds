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

    def __init__(self, out_function=print):
        machine = Machine(model=self, states=GarageDoor.states,
                          transitions=GarageDoor.transitions, initial='moving')
        self.send = out_function

    def door_open(self):
        self.send('door is now open')

    def door_closed(self):
        self.send('door is now closed')

    def start_moving(self):
        self.send('door started moving')

    def broken_door(self):
        self.send('HELP!!! Door is broken')
