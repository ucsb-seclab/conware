import logging
import random
import sys
import networkx
import networkx.algorithms.isomorphism as iso
from sets import Set
from pretender.models.simple_storage import SimpleStorageModel
from conware.peripheral_state import PeripheralModelState

import copy

logger = logging.getLogger(__name__)


class PeripheralModel:
    """
    This class represents an external peripheral
    """

    # Might want to mess around with this ID stuff to make merging easier
    global_nodeID = 0

    def __init__(self, addresses, name=None):
        self.all_states = []
        self.nodeID = 0
        self.graph = networkx.DiGraph()
        self.addresses = addresses
        self.name = name
        self.current_state = self.create_state(-1, "start", -1)
        self.start_state = self.current_state
        self.equiv_states = []

    def update_node_id(self):
        self.nodeID += 1
        return self.nodeID

    def create_state(self, address=None, operation=None, value=None,
                     state=None):
        # create state attributes
        new_state_id = self.update_node_id()
        # state_id = (self.nodeID, PeripheralModel.global_nodeID) turns out we dont need this pair if all of the peripherals are separate graphs
        # PeripheralModel.global_nodeID += 1
        if state is None:
            state = PeripheralModelState(address, operation, value,
                                         new_state_id)
        else:
            state.state_id = new_state_id

        attributes = {new_state_id: {'state': state}}

        # create state
        # check for state existence?
        if not self.graph.has_node(new_state_id):
            self.graph.add_node(new_state_id)

        networkx.set_node_attributes(self.graph, attributes)

        self.all_states.append(state)
        return new_state_id, state

    def train_read(self, address, value, pc, size, timestamp):
        """
        Assumes that we are in the correct current state
        """
        logger.debug("got read %08X %08X" % (address, value))
        self.current_state[1].append_read(address, value, pc, size, timestamp)

    def train_write(self, address, value):
        logger.info("got write %08X %08X" % (address, value))
        # self.update_node_id()
        new_state = self.create_state(address, "write", value)
        old_state = self.current_state
        self.current_state = new_state
        self._add_edge(old_state[0], self.current_state[0],
                       address=address, value=value)

    def train(self):
        for idx, state in enumerate(self.all_states):
            state.train()

    def reset(self):
        self.current_state = self.start_state

        for state in self.all_states:
            state.reset()

    def _add_edge(self, s1, s2, address=1, value=-1):
        """
        Add an edge with our annotations
        :param s2:
        :param address:
        :param value:
        :return:
        """
        if (s1, s2) in self.graph.edges:
            tuples = self._get_edge_labels((s1, s2))
            tuples |= set([(address, value)])
            networkx.set_edge_attributes(self.graph,
                                         {(s1, s2): {
                                             'tuples': tuples,
                                             'label': ", ".join(["(0x%08X,"
                                                                 "%d)"
                                                                 % x
                                                                 for x
                                                                 in tuples])}})
        else:
            self.graph.add_edge(s1, s2, tuples=set([(address, value)]),
                                label="(0x%08X,%d)" % (address, value))

    def _get_edge_labels(self, edge):
        """
        Return the (address, value) pair associated with a state transition

        :param edge: Edge Label
        :return: (address, value)
        """
        tuples = networkx.get_edge_attributes(self.graph, 'tuples')
        if edge in tuples:
            return tuples[edge]
        else:
            return None

    def _get_state(self, state_id):
        """ Return the state given the state/node id """
        return networkx.get_node_attributes(self.graph, 'state')[state_id]

    def _merge_states(self, equiv_states):
        """
        merge state 2 into state 1
        """
        graph = networkx.Graph(equiv_states)
        equiv_classes = [tuple(c) for c in networkx.connected_components(graph)]

        for equiv_set in equiv_classes:
            in_edges = set()
            out_edges = set()
            state = None
            for state_id in equiv_set:
                in_edges |= set(self.graph.in_edges(state_id))
                out_edges |= set(self.graph.out_edges(state_id))
                if state is None:
                    state = self._get_state(state_id)
                else:
                    state.merge(self._get_state(state_id))

            # Create a new state
            new_state_id, new_state = self.create_state(state=state)

            # Update all of our inbound edges
            for e in in_edges:
                tuples = self._get_edge_labels(e)
                if e[0] not in equiv_set:
                    for (address, value) in tuples:
                        self._add_edge(e[0], new_state_id,
                                       address=address, value=value)
                else:
                    # Self reference
                    logger.debug("Adding self reference for %d" % new_state_id)
                    for (address, value) in tuples:
                        self._add_edge(new_state_id, new_state_id,
                                       address=address, value=value)
                self.graph.remove_edge(*e)

            # Update our outbound edges
            out_edges = out_edges.difference(in_edges)
            for e in out_edges:
                tuples = self._get_edge_labels(e)
                if e[1] not in equiv_set:
                    for (address, value) in tuples:
                        self._add_edge(new_state_id, e[1],
                                       address=address, value=value)
                else:
                    # Self reference
                    logger.info("Adding self reference for %d" % new_state_id)
                    for (address, value) in tuples:
                        self._add_edge(new_state_id, new_state_id,
                                       address=address, value=value)
                self.graph.remove_edge(*e)

            # Remove all of our old states
            for state_id in equiv_set:
                self.graph.remove_node(state_id)
                if state_id == self.start_state[0]:
                    self.start_state = (new_state_id, new_state)

    def _label_nodes(self):
        """ Add labels to all of our nodes """
        attributes = {}
        for node in self.graph.nodes:
            state = self._get_state(node)
            if node == self.start_state[0]:
                attributes[node] = {'state': state, 'label': "((%d)) %s" % (
                    node, state)}
            else:
                attributes[node] = {'state': state, 'label': "(%d) %s" % (
                    node, state)}

        networkx.set_node_attributes(self.graph, attributes)

    def _get_merge_constraints(self, state_id_1, state_id_2):
        """
        Recursive call to
        :param state_id_1:
        :param state_id_2:
        :return:
        """
        merge_set = set()
        if state_id_1 == state_id_2:
            return merge_set

        state1 = self._get_state(state_id_1)
        state2 = self._get_state(state_id_2)
        if state1 == state2:
            logger.debug(
                "%d (%s) == %d (%s)" % (state_id_1, state1, state_id_2, state2))
            # If these states are already accounted for, we don't need to
            # keep traversing
            for equiv_tuple in self.equiv_states:
                if state_id_1 in equiv_tuple and \
                        state_id_2 in equiv_tuple:
                    self.equiv_states.append((state_id_1, state_id_2))
                    return merge_set
            self.equiv_states.append((state_id_1, state_id_2))

            # Compress our existing nodes into equivalence classes to group
            # edges
            graph = networkx.Graph(self.equiv_states)
            equiv_classes = [tuple(c) for c in
                             networkx.connected_components(graph)]

            equiv_edges = set()
            for equiv_class in equiv_classes:
                if state_id_1 in equiv_class:
                    for state_id in equiv_class:
                        equiv_edges |= set(self.graph.out_edges(state_id))

            edges_1 = self.graph.out_edges(state_id_1)
            edges_2 = self.graph.out_edges(state_id_2)

            rtn = True
            # Check all outgoing edges for node 1
            for e1 in edges_1:
                for e2 in equiv_edges:
                    e1_labels = self._get_edge_labels(e1)
                    e2_labels = self._get_edge_labels(e2)
                    # Do we have a duplicate edge (i.e., state transition)
                    if e1_labels & e2_labels:
                        merge_set.add((e1[1], e2[1]))

            # Check all outgoing edges for node 2
            for e1 in edges_2:
                for e2 in equiv_edges:
                    e1_labels = self._get_edge_labels(e1)
                    e2_labels = self._get_edge_labels(e2)
                    # Do we have a duplicate edge (i.e., state transition)
                    if e1_labels & e2_labels:
                        merge_set.add((e1[1], e2[1]))

            return merge_set
        else:
            return False

    def optimize2(self):
        """
        This function will optimize the state machine, merging equivalent
        states.
        :return:
        """
        merged = True
        while merged:
            merged = False
            visted = set()
            for n1 in networkx.dfs_preorder_nodes(self.graph,
                                                  self.start_state[0]):
                for n2 in networkx.dfs_preorder_nodes(self.graph,
                                                      n1):

                    logger.info("Comparing %d and %d" % (n1, n2))
                    if n1 == n2:
                        continue

                    self.equiv_states = []

                    merge_set = self._get_merge_constraints(n1, n2)
                    if merge_set is False:
                        continue

                    # Ensure that all shared outgoing edges are also mergable
                    mergable = True
                    while len(merge_set) != 0:
                        x, y = merge_set.pop()

                        set2 = self._get_merge_constraints(x, y)
                        if set2 is False:
                            mergable = False
                            break
                        else:
                            merge_set = merge_set.union(set2)

                    # Did everything check out?
                    if mergable:
                        logger.info("Merging States: %d and %d" % (n1, n2))
                        logger.debug("Equivalent nodes: %s" % self.equiv_states)
                        self._merge_states(self.equiv_states)
                        merged = True
                        break

                if merged:
                    break

        self._label_nodes()

    def _get_state_attributes(self, state_id):
        """ Return the state given the state/node id """
        return networkx.get_node_attributes(self.graph, 'state')[state_id]

    def no_reads_merge(self, state1, state2):
        """
        Given state1 --> state2 where state 2 has 0 reads, merge state2 into state1
        :param state1:
        :param state2:
        :return:
        """
        to_node = None
        out_edge_attr = None
        if len(state2["state"].reads) != 0:
            return False

        # check and save outgoing edges of state2
        out_edges = self.graph.out_edges(nbunch=state2["state"].state_id)
        for edge in out_edges:
            out_edge_attr = self._get_edge_labels(edge)
            to_node = edge[1]

        # make edge between state1 and state2 self loop of state2
        self_edge_attr = self._get_edge_labels(
            (state1["state"].state_id, state2["state"].state_id))
        self.graph.add_edge(state1["state"].state_id, state1["state"].state_id,
                            address=self_edge_attr[0], value=self_edge_attr[
                1])

        # merge state2 into state2
        # since state 2 has no reads we shouldnt actually have to do anything, just delete it
        self.graph.remove_node(state2["state"].state_id)

        # reconnect outgoing edge
        if to_node:
            self.graph.add_edge(state1["state"].state_id, to_node,
                                address=out_edge_attr[0],
                                value=out_edge_attr[1])
        return True

    def read(self, address, size):
        """
        Read a value from the modeled peripheral
        :param address:
        :param size:
        :return:
        look in model, models per address, figur out which address reading from, read from that model (peripheral state stored)
        """

        # Assumption: We are in correct current state and expect read address to be there
        # uart = False
        # if (self.name == 'UART'):
        #     uart = True
        #     logger.info("UART reading from address: " + str(hex(address)))

        if (address not in self.current_state[1].model_per_address):
            # if (uart):
            #     logger.info("Couldnt find model for read address")
            return -1

        # if (uart):
        #     logger.info("Found read: " + str(
        #         hex(self.current_state[1].model_per_address[address].read())))
        return self.current_state[1].model_per_address[address].read()

    def write(self, address, size, value):
        """
        write a value to the modeled peripheral (i.e., state transition)
        :param address:
        :param size:
        :param value:
        :return:
        1. look for edge
        2. check if simple storage model in models per address
        3. BFS for valid edge
        """
        uart = False
        # logger.info("current peripheral: " + str(self.name))
        # logger.info("current state: " + str(self.current_state[0]))
        # logger.info("Attempting to write address: " + hex(address) + " Value: " + str(value))
        if (self.name == 'UART'):
            uart = True
            logger.info("UART")
            logger.info("Attempting to write address: " + str(
                address) + " Value: " + str(value))

        if (uart):
            if (value == 79):
                logger.info("Ascii value 79 found: O")
            if (value == 78):
                logger.info("Ascii value 78 found: N")
            if (value == 13):
                logger.info("Ascii value 13 found: CARRIAGE RETURN")
            if (value == 10):
                logger.info("Ascii value 10 found: LINE FEED")
            if (value == 2):
                logger.info("Ascii value 2 found: START OF TEXT")
            if (value == 102):
                logger.info("Ascii value 102 found: f")
            if (value == 111):
                logger.info("Ascii value 111 found: o")

        current_state_id = self.current_state[0]
        out_edges = self.graph.edges(current_state_id)
        # print("out edges from current state: ", out_edges)
        for edge in out_edges:
            edge_tuple = list(self.graph[edge[0]][edge[1]]['tuples'])

            if ((address, value) in edge_tuple):
                self.current_state = (
                edge[1], self.graph.nodes[edge[1]]["state"])
                if (uart):
                    logger.info(
                        "Found correct edge transition, updating current state to: ")
                    logger.info(str(self.current_state))

                # Write our value to the model (e.g., SimpleStorage)
                if address in self.current_state[1].model_per_address:
                    self.current_state[1].model_per_address[address].write(
                        value)
                else:
                    if (uart):
                        logger.info(
                            "Couldnt write address to model because address not found in model per address")
                return True

            elif (edge_tuple[0][0] == address and edge_tuple[0][1] != value):
                if (uart):
                    logger.info(
                        "Found correct write address but incorrect value")

        # couldnt find an edge, check if simple storage model
        if (address in self.current_state[1].model_per_address):
            if (uart):
                logger.info(
                    "We couldnt find a connecting edge, checking if SimpleStorage")
            if (type(self.current_state[1].model_per_address[
                         address]) is SimpleStorageModel):
                if (uart):
                    logger.info("SimpleStorage!! Writing")
                # if it is a simple storage model then just write to the address
                self.current_state[1].model_per_address[address].write(value)
                return True

        # otherwise start BFS
        target_edges = list(
            networkx.bfs_edges(self.graph, source=self.current_state[0]))
        if (uart):
            logger.info("Starting BFS with target edges: " + str(target_edges))
        for edge in target_edges:

            edge_tuple = list(self.graph[edge[0]][edge[1]]['tuples'])

            if (uart):
                logger.info("BFS edge being considered: " + str(
                    edge) + "; with addr, val: " + str(edge_tuple))

            if ((address, value) in edge_tuple):
                if (uart):
                    logger.info(
                        "Found good edge in BFS, transitioning to state: " + str(
                            edge[1]))
                self.current_state = (
                edge[1], self.graph.nodes[edge[1]]["state"])
                if address in self.current_state[1].model_per_address:
                    self.current_state[1].model_per_address[address].write(
                        value)
                return True

        logger.error("%s: We couldn't find a transition matching that address "
                     "and value: %s : %s" % (self.name, hex(address),
                                             str(value)))
        return False
