import logging
import random
import sys
import networkx
import networkx.algorithms.isomorphism as iso
from conware.peripheral_state import PeripheralModelState

import copy
logger = logging.getLogger(__name__)


class PeripheralModel:
    """
    This class represents an external peripheral
    """


    #Might want to mess around with this ID stuff to make merging easier
    global_nodeID = 0

    def __init__(self, addresses, name=None):
        self.all_states = []
        self.nodeID = 0
        self.graph = networkx.MultiDiGraph()  # May want to use MultiDiGraph instead, allows parallel edges
        self.addresses = addresses
        self.name = name
        self.current_state = self.create_state(-1, "start", -1)
        self.start_state = self.current_state

    def update_node_id(self):
        self.nodeID += 1

    def create_state(self, address, operation, value):
        # create state attributes
        state_id = self.nodeID
        #state_id = (self.nodeID, PeripheralModel.global_nodeID) turns out we dont need this pair if all of the peripherals are separate graphs
        PeripheralModel.global_nodeID += 1
        state = PeripheralModelState(address, operation, value)
        attributes = {state_id: {'state': state}}
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
        logger.debug("got read %08X %08X" % (address, value))
        self.current_state[1].append_read(address, value, pc, size, timestamp)
        # attributes = {self.current_state[0]: self.current_state[1].reads}
        # networkx.set_node_attributes(self.graph, attributes)

    def train_write(self, address, value):
        logger.info("got write %08X %08X" % (address, value))
        self.update_node_id()
        new_state = self.create_state(address, "write", value)
        old_state = self.current_state
        self.current_state = new_state
        # self.graph.add_edge(self.current_state[0]-1, self.current_state[0], value=value)
        self.graph.add_edge(old_state[0], self.current_state[0],
                            address=address, value=value)

    def train(self):
        for idx, state in enumerate(self.all_states):
            state.train()

    def reset(self):
        self.current_state = self.start_state

        for state in self.all_states:
            state.reset()
    def _get_edge_lables(self, edge):
        """
        Return the (address, value) pair associated with a state transition

        :param edge: Edge Label
        :return: (address, value)
        """
        addresses = networkx.get_edge_attributes(self.graph, 'address')
        values = networkx.get_edge_attributes(self.graph, 'value')
        if edge in addresses:
            return (addresses[edge], values[edge])
        else:
            return None

    def _get_state(self, state_id):
        """ Return the state given the state/node id """
        return networkx.get_node_attributes(self.graph, 'state')[state_id]

    def _merge_states(self, state_id_1, state_id_2):
        """
        merge state 2 into state 1
        :param state_id_1: ID of the state to keep
        :param state_id_2: ID of the state to merge into state 1
        :return: True if merge succeeded, False otherwise
        """

        self.equiv_states = []

        pass

    def _merge_recursive(self, state_id_1, state_id_2):
        """
        Recursive call to
        :param state_id_1:
        :param state_id_2:
        :return:
        """

    def optimize(self):
        """
        This function will optimize the state machine, merging equivalent
        states.
        :return:
        """
        for e in networkx.dfs_edges(self.graph, self.start_state[0]):
            print e
            state = self._get_state(e[1])
            print state
            print len(state.reads)
            print self._get_edge_lables(e)



