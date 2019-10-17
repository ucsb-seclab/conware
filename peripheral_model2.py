import logging
import random
import sys
import networkx
from peripheral_state2 import PeripheralModelState2

logger = logging.getLogger(__name__)


class PeripheralModel2:
    """
    This class represents an external peripheral
    """


    #Might want to mess around with this ID stuff to make merging easier
    global_nodeID = 0

    def __init__(self, addresses, name=None):
        self.all_states = []
        self.nodeID = 0
        self.graph = networkx.DiGraph()  # May want to use MultiDiGraph instead, allows parallel edges
        self.addresses = addresses
        self.name = name
        self.current_state = self.create_state(-1, "start", -1)
        self.start_state = self.current_state

    def update_node_id(self):
        self.nodeID += 1

    def create_state(self, address, operation, value):
        # create state attributes
        # state_id = PeripheralModel2.nodeID
        state_id = (self.nodeID, PeripheralModel2.global_nodeID)
        PeripheralModel2.global_nodeID += 1
        state = PeripheralModelState2(address, operation, value)
        attributes = {state_id: state.reads}
        # create state
        # check for state existance?
        if not self.graph.has_node(state_id):
            self.graph.add_node(state_id)

        networkx.set_node_attributes(self.graph, attributes)

        self.all_states.append(state)
        return state_id, state

    def train_read(self, address, value, pc, size, timestamp):
        """
        Assumes that we are in the correct current state
        """
        logger.info("got read %08X %08X" % (address, value))
        self.current_state[1].append_read(address, value, pc, size, timestamp)
        attributes = {self.current_state[0]: self.current_state[1].reads}
        networkx.set_node_attributes(self.graph, attributes)

    def train_write(self, address, value):
        self.update_node_id()
        new_state = self.create_state(address, "write", value)
        old_state = self.current_state
        self.current_state = new_state
        # self.graph.add_edge(self.current_state[0]-1, self.current_state[0], value=value)
        self.graph.add_edge(old_state[0], self.current_state[0], value=value)

    def train(self):
        for idx, state in enumerate(self.all_states):
            state.train()

    def reset(self):
        self.current_state = self.start_state

        for state in self.all_states:
            state.reset()



