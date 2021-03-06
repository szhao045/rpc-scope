# This code is licensed under the MIT License (see LICENSE file for details)

import contextlib

class StateStackDevice:
    def __init__(self):
        self._state_stack = []

    def _set_state(self, properties_and_values):
        """Set a number of device properties at once, in the order specified"""
        for p, v in properties_and_values:
            getattr(self, 'set_'+p)(v)

    @staticmethod
    def _order(state, weights):
        if len(state) == 0 or weights is None:
            return state.items()
        # sort by weight, with implicit value of zero for non-listed items
        properties, values = zip(*sorted(state.items(), key=lambda p_v: weights.get(p_v[0], 0)))
        return zip(properties, values)

    def  _update_push_states(self, state, old_state):
        for k in list(state.keys()):
            if old_state[k] == state[k]:
                state.pop(k)
                old_state.pop(k)

    def _get_push_weights(self, state):
        return None

    def _get_pop_weights(self, state):
        return None

    def push_state(self, **state):
        """Set a number of device parameters at once using keyword arguments, while
        saving the old values of those parameters. pop_state() will restore those
        previous values. push_state/pop_state pairs can be nested arbitrarily.
        """
        old_state = {p: getattr(self, 'get_'+p)() for p, v in state.items()}
        self._update_push_states(state, old_state)
        if old_state:
            properties_and_values = self._order(state, self._get_push_weights(state))
            self._set_state(properties_and_values)
        self._state_stack.append(old_state)

    def pop_state(self):
        """Restore the most recent set of device parameters changed by a push_state()
        call.
        """
        old_state = self._state_stack.pop()
        if old_state:
            properties_and_values = self._order(old_state, self._get_pop_weights(old_state))
            self._set_state(properties_and_values)

    @contextlib.contextmanager
    def in_state(self, **state):
        """Context manager to set a number of device parameters at once using
        keyword arguments. The old values of those parameters will be restored
        upon exiting the with-block."""
        self.push_state(**state)
        try:
            yield
        finally:
            self.pop_state()
