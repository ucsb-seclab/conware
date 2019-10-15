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

    nodeID = 0

    def __init__(self, addresses, name=None):
        self.graph = networkx.DiGraph()  # May want to use MultiDiGraph instead, allows parallel edges
        self.addresses = addresses
        self.name = name
        self.current_state = self.create_state(-1, "start", 0)


    def update_node_id(self):
        PeripheralModel2.nodeID += 1

    def create_state(self, address, operation, value):
        #create state attributes
        state_id = PeripheralModel2.nodeID
        state = PeripheralModelState2(address, operation, value)
        attributes = {state_id: state.reads}
        #create state
        # check for state existance?
        if not self.graph.has_node(state_id):
            self.graph.add_node(state_id)

        networkx.set_node_attributes(self.graph, attributes)
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
        self.current_state = new_state
        self.graph.add_edge(self.current_state[0]-1, self.current_state[0])

        ###TODO####
        ##Add Edge between two states###
        ##State moving from will always be the state the edge comes from###