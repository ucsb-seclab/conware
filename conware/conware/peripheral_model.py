import logging
import random
import sys
import networkx
import networkx.algorithms.isomorphism as iso
from .peripheral_state import PeripheralModelState
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
        self.graph = networkx.DiGraph()  # May want to use MultiDiGraph instead, allows parallel edges
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
        state = PeripheralModelState(address, operation, value, state_id)
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
        addresses = networkx.get_edge_attributes(self.graph, 'address')
        values = networkx.get_edge_attributes(self.graph, 'value')
        if edge in addresses:
            return (addresses[edge], values[edge])
        else:
            return None

    def _get_state_attributes(self, state_id):
        """ Return the state given the state/node id """
        return networkx.get_node_attributes(self.graph, 'state')[state_id]

    def optimize(self):
        """
        This function will optimize the state machine, merging equivalent
        states.
        :return:
        """
        merge_node_pairs = []

        #Pass 1
        #goes through every state and checks if there no reads
        #if so we add that state and the state before it to be merged
        #way to merge dynamically in this loop?
        for e in networkx.dfs_edges(self.graph, self.start_state[0]):
            state = self._get_state_attributes(e[1])

            num_addr_read = len(state.reads)
            if (num_addr_read == 0):
                node1 = self.graph.nodes[e[0]]
                node2 = self.graph.nodes[e[1]]
                merge_node_pairs.append((node1,node2))

        for merge_nodes in reversed(merge_node_pairs):
            print("Attempting merge of no read state: " + str(merge_nodes[1]["state"].state_id) + " with prev state: " + str(merge_nodes[0]["state"].state_id))
            self.no_reads_merge(merge_nodes[0], merge_nodes[1])


    def no_reads_merge(self, state1, state2):
        """
        Given state1 --> state2 where state 2 has 0 reads, merge state2 into state1
        :param state1:
        :param state2:
        :return:
        """
        to_node = None
        out_edge_attr = None
        if (len(state2["state"].reads) != 0):
            return False


        #check and save outgoing edges of state2
        out_edges = self.graph.out_edges(nbunch = state2["state"].state_id)
        for edge in out_edges:
            out_edge_attr = self._get_edge_lables(edge)
            to_node = edge[1]

        #make edge between state1 and state2 self loop of state2
        self_edge_attr = self._get_edge_lables((state1["state"].state_id, state2["state"].state_id))
        self.graph.add_edge(state1["state"].state_id, state1["state"].state_id, address=self_edge_attr[0], value=self_edge_attr[1])

        #merge state2 into state2
        #since state 2 has no reads we shouldnt actually have to do anything, just delete it
        self.graph.remove_node(state2["state"].state_id)

        #reconnect outgoing edge
        if (to_node):
            self.graph.add_edge(state1["state"].state_id, to_node, address=out_edge_attr[0], value=out_edge_attr[1])
        return True


