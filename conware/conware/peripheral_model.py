# Native
import logging

# 3rd Party
import networkx

# Conware
from conware.models.simple_storage import SimpleStorageModel
from conware.peripheral_state import PeripheralModelState

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
        self.visited = set()
        self.wildcard_edges = {}

    def __eq__(self, other):
        """ determine if two peripherals are the same """
        return self.name == other.name and self.addresses == other.addresses

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
            # self.edge_tuples = networkx.get_edge_attributes(self.graph,
            #                                                "tuples")
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

        return self.graph[edge[0]][edge[1]]["tuples"]

    def _get_state(self, state_id):
        """ Return the state given the state/node id """
        # print("in _get_state, for state_id: " + str(state_id))
        return self.graph.nodes.data("state")[state_id]

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
                attributes[node] = {'state': state, 'label': "((%s)) %s" % (
                    str(node), state)}
            else:
                attributes[node] = {'state': state, 'label': "(%s) %s" % (
                    str(node), state)}

        networkx.set_node_attributes(self.graph, attributes)

    def _get_merge_constraints(self, state_id_1, state_id_2):
        """
        Will return a set of edges that must also be equal if the two states
        are equal or False

        An empty set means that the two states are fine to merge without any
        further checking

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
                "%s (%s) == %s (%s)" % (str(state_id_1), state1,
                                        str(state_id_2), state2))
            # Mark the nodes as equal
            self.equiv_states.append((state_id_1, state_id_2))
            # If these states are already accounted for, we don't need to
            # keep traversing
            self.equiv_states.append((state_id_1, state_id_2))
            if state_id_1 in self.visited and state_id_2 in self.visited:
                return merge_set

            # Marked the nodes as visited
            self.visited.add(state_id_1)
            self.visited.add(state_id_2)

            # Compress our existing nodes into equivalence classes to group
            # edges
            graph = networkx.Graph(self.equiv_states)
            equiv_classes = [tuple(c) for c in
                             networkx.connected_components(graph)]

            # Get all of the equivalent edges for our nodes (note that they
            # are in the same equivalence class)
            equiv_edges = set()
            for equiv_class in equiv_classes:
                if state_id_1 in equiv_class:
                    for state_id in equiv_class:
                        equiv_edges |= set(self.graph.out_edges(state_id))

            # Get the edges for each of these new nodes
            edges_1 = self.graph.out_edges(state_id_1)
            edges_2 = self.graph.out_edges(state_id_2)

            # Figure out any shared edges
            rtn = True
            for e2 in equiv_edges:
                e2_labels = self._get_edge_labels(e2)
                # Check all outgoing edges for node 1
                for e1 in edges_1:
                    e1_labels = self._get_edge_labels(e1)
                    # Do we have a duplicate edge (i.e., state transition)
                    if e1_labels & e2_labels:
                        merge_set.add((e1[1], e2[1]))

                # Check all outgoing edges for node 2
                for e1 in edges_2:
                    e1_labels = self._get_edge_labels(e1)
                    # Do we have a duplicate edge (i.e., state transition)
                    if e1_labels & e2_labels:
                        merge_set.add((e1[1], e2[1]))
            return merge_set
        else:
            logger.info(
                "%s and %s not mergable." % (str(state_id_1), str(state_id_2)))
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
            for n1 in networkx.dfs_preorder_nodes(self.graph,
                                                  self.start_state[0]):
                for n2 in networkx.dfs_preorder_nodes(self.graph,
                                                      n1):

                    logger.info("Comparing %s and %s" % (str(n1), str(n2)))
                    if n1 == n2:
                        continue

                    self.equiv_states = []
                    self.visited = set()

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
                        logger.info("Merging States: %s and %s" % (str(n1),
                                                                   str(n2)))
                        logger.debug("Equivalent nodes: %s" % self.equiv_states)
                        self._merge_states(self.equiv_states)
                        merged = True
                        break

                if merged:
                    break

        self._label_nodes()
        self._update_wildcard_edges()

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
        look in model, models per address, figure out which address reading
        from, read from that model (peripheral state stored)
        """

        # Assumption: We are in correct current state and expect read address to be there

        if address not in self.current_state[1].model_per_address:
            logger.error(
                "%s: Could not find model for read address (%s)" % (
                    self.name, hex(address)))
            return -1
        value = self.current_state[1].model_per_address[address].read()
        logger.debug("%s: Read from %s value: %s" % (self.name,
                                                     hex(address),
                                                     hex(value)))
        return value

    def _update_state(self, new_state, address, value):
        """

        :param new_state:
        :return:
        """
        self.current_state = (
            new_state, self.graph.nodes[new_state]["state"])

        # Write our value to the model (e.g., SimpleStorage)
        if address in self.current_state[1].model_per_address:
            self.current_state[1].model_per_address[address].write(
                address,
                value)
        else:
            logger.debug(
                "%s: Couldn't write address to model because address "
                "not "
                "found in model per address", self.name)
            for addr in self.current_state[1].model_per_address:
                self.current_state[1].model_per_address[addr].write(
                    address, value)

    def write(self, address, size, value):
        """
        write a value to the modeled peripheral (i.e., state transition)
        :param address:
        :param size:
        :param value:
        :return:
        1. look for edge (either a provided value, or wildcard edge)
        2. check if simple storage model in models per address
        3. BFS for valid edge
        4. If no edge found, pick edge with most instances of that address
        //ADD SimpleStorageModel to state if we have never seen write to address
        """

        logger.debug("%s: Writing to %s with value: %s" % (self.name,
                                                           hex(address),
                                                           hex(value)))
        current_state_id = self.current_state[0]
        out_edges = self.graph.edges(current_state_id)
        for edge in out_edges:
            edge_tuple = list(self.graph[edge[0]][edge[1]]['tuples'])

            if (address, value) in edge_tuple:
                self._update_state(edge[1], address, value)
                return True

            elif edge in self.wildcard_edges and address in \
                    self.wildcard_edges[edge]:
                logger.info("%s/%d Taking wildcard edge (%08X, %d)!" % (
                    self.name, self.current_state[0],
                    address, value))
                self._update_state(edge[1], address, value)
                return True

            # TODO: This check seems invalid, as there may still be a branch
            # elif edge_tuple[0][0] == address and edge_tuple[0][1] != value:
            #     logger.info(
            #         "found correct address but no matching value, check simple storage model")

        # couldnt find an edge, check if simple storage model
        if address in self.current_state[1].model_per_address:
            if (type(self.current_state[1].model_per_address[
                         address]) is SimpleStorageModel):
                # if it is a simple storage model then just write to the address
                self.current_state[1].model_per_address[address].write(value)
                logger.info(
                    "simple storage!, writing to address: " + str(address))
                return True

        logger.info("%s: Was not simple storage, starting BFS/Wildcard" % self.name)
        # otherwise start BFS
        target_edges = list(
            networkx.edge_bfs(self.graph, source=self.current_state[0]))

        for edge in target_edges:

            edge_tuple = list(self.graph[edge[0]][edge[1]]['tuples'])

            if ((address, value) in edge_tuple):
                self.current_state = (
                    edge[1], self.graph.nodes[edge[1]]["state"])
                if address in self.current_state[1].model_per_address:
                    self.current_state[1].model_per_address[address].write(
                        value)
                    logger.info("BFS Edge: " + str(edge) + " selected")
                return True
            elif (edge, address) in self.wildcard_edges:
                self.current_state = (
                    edge[1], self.graph.nodes[edge[1]]["state"])
                if address in self.current_state[1].model_per_address:
                    self.current_state[1].model_per_address[address].write(
                        value)
                    logger.info("Wildcard Edge: " + str(edge) + " selected")
                return True

        logger.info(
            "%s: No matching edge!, picking edge with most writes to target address" % self.name)
        # If we dont find value for address, look at all edges, with writes to that address, pick the one that has it the most times
        picked_edge = ((None, None), 0)  # (edge, addresscount)
        all_edges = self.graph.edges
        for edge in all_edges:
            addr_count = 0
            label = self._get_edge_labels(edge)
            for tuple in label:
                if tuple[0] == address:
                    addr_count += 1
            if addr_count > picked_edge[1]:
                picked_edge = (edge, addr_count)

        if picked_edge == ((None, None), 0):
            logger.error("%s: We could not find any state where this write was seen before (%s, %s)" % (self.name,
                                                                                                        hex(address),
                                                                                                        hex(value)))
            return False

        self.current_state = (
            picked_edge[0][1], self.graph.nodes[picked_edge[0][1]]["state"])
        logger.info("Picked edge: " + str(picked_edge[0]))
        if address in self.current_state[1].model_per_address:
            self.current_state[1].model_per_address[address].write(value)
        return True

        # This address has never been written to, do nothing
        logger.error("%s: We couldn't find a transition matching that address "
                     "and value: %s : %s" % (self.name, hex(address),
                                             str(value)))
        return False

    def _update_wildcard_edges(self, threshold=5):
        """
        Annotate any edges that have more than **threshold** writes to accept
        any value as a transition (i.e., a wildcard)
        :param threshold: Number of unique writes before we accept any
        transition

        :return:
        """
        self.wildcard_edges = {}
        all_edges = self.graph.edges
        for edge in all_edges:
            # Count how many times each address is used on this edge
            addresses = {}
            label = self._get_edge_labels(edge)
            for (address, value) in label:
                if address not in addresses:
                    addresses[address] = set()
                addresses[address].add((address, value))

            for address in addresses:
                if len(addresses[address]) > threshold:
                    logger.info("%s has a wildcard edge (count: %d)" %
                                (edge, len(addresses[address])))

                    # make sure no other outgoing edges use this address
                    has_other_edge = False
                    for e2 in self.graph.out_edges(edge[0]):
                        if e2 == edge or has_other_edge:
                            continue
                        label = self._get_edge_labels(e2)
                        for (a2, v2) in label:
                            if a2 == address:
                                has_other_edge = True
                                break
                    if has_other_edge:
                        continue

                    # Add to labels
                    edges = self.graph[edge[0]][edge[1]]["tuples"]
                    edges -= addresses[address]
                    edge_label = ", ".join(["(0x%08X, %d)" % x for x in edges])
                    self.graph[edge[0]][edge[1]]["label"] = edge_label + \
                                                            ", (%08X,*)" % address

                    # Should we mark this edge as a wildcard?
                    if edge not in self.wildcard_edges:
                        self.wildcard_edges[edge] = [address]
                    else:
                        self.wildcard_edges[edge].append(address)

    def append_states(self, append_str):
        """ append str to every node id """
        # Update our states
        for n in self.graph.nodes:
            state = self._get_state(n)
            state.state_id = str(n) + append_str
        # Update start state
        self.start_state = (str(self.start_state[0]) + append_str,
                            self.start_state[1])
        # Update nodes in the graph
        self.graph = networkx.relabel_nodes(self.graph,
                                            lambda x: str(x) + append_str)

    def merge(self, other_peripheral):
        """
        Merge the other peripheral into this peripheral

        :param other_peripheral:
        :return:
        """

        other_peripheral.append_states("_2")
        self._merge_map = {}
        if self._recursive_merge(self.start_state[0],
                                 other_peripheral.start_state[0],
                                 other_peripheral):
            # Rename our nodes to be equivalent
            other_peripheral.graph = networkx.relabel_nodes(
                other_peripheral.graph,
                self._merge_map)

            # Merge our graphs
            self.graph = networkx.compose(self.graph, other_peripheral.graph)

            # Merge the nodes and edges
            for merge_node in self._merge_map:
                state_id = self._merge_map[merge_node]

                # Merge the states
                state = self._get_state(state_id)
                state2 = other_peripheral._get_state(state_id)
                state.merge(state2)

                # add all edges
                edges2 = other_peripheral.graph.out_edges(state_id)
                for e2 in edges2:
                    e2_labels = other_peripheral._get_edge_labels(e2)
                    for (address, value) in e2_labels:
                        self._add_edge(e2[0], e2[1], address, value)
        else:
            logger.error("Failed to merge %s and %s" % (self, other_peripheral))

        # Update labels
        self._label_nodes()

        # Update any wildcard edges
        self._update_wildcard_edges()
        pass

    def _recursive_merge(self, state_id, state_id2, other_peripheral):
        """
        recursively merge every matching state from other into this peripheral

        :param state_id:
        :param state_id2:
        :param other_peripheral:
        :return: False if it fails
        """

        state = self._get_state(state_id)
        state2 = other_peripheral._get_state(state_id2)

        if state != state2:
            logger.error("%s != %s" % (state, state2))
            return False

        # Have we been here before?
        if state_id2 in self._merge_map:
            if self._merge_map[state_id2] == state_id:
                return True
            else:
                return False

        # state.merge(state2)
        self._merge_map[state_id2] = state_id

        edges = self.graph.out_edges(state_id)
        edges2 = other_peripheral.graph.out_edges(state_id2)

        rtn = True
        for e in edges:
            for e2 in edges2:
                e_labels = self._get_edge_labels(e)
                e2_labels = other_peripheral._get_edge_labels(e2)

                # Do they share common edges?
                if e_labels & e2_labels:
                    rtn &= self._recursive_merge(e[1], e2[1], other_peripheral)
                new_edges = e2_labels - e_labels

        return rtn
