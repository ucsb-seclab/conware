# Native
import logging
import threading

# 3rd Party
import networkx

# Conware
from conware.models.simple_storage import SimpleStorageModel
from conware.peripheral_state import PeripheralModelState

conware_rlock = threading.RLock()

logger = logging.getLogger(__name__)


class PeripheralModel:
    """
    This class represents an external peripheral
    """

    # Might want to mess around with this ID stuff to make merging easier
    global_nodeID = 0

    def __init__(self, addresses, name=None):
        self.pending_interrupts = {}
        self.all_states = []
        self.nodeID = 0
        self.graph = networkx.DiGraph()
        self.addresses = addresses
        self.name = name
        self.node_states = {}
        self.current_state = self.create_state(operation=
                                               "start")
        self.start_state = self.current_state
        self.equiv_states = []
        self.visited = []
        self.wildcard_edges = {}
        self.merge_count = 1

        self.stats = {'reads': [],
                      'writes': [],
                      'interrupts': [],
                      'wildcard': 0,
                      'bfs': 0,
                      'long_jump': 0,
                      'failed': 0}

    def __str__(self):
        """ Return a nice readable string """
        return "%s: %s" % (self.name, self.current_state)

    def __repr__(self):
        return self.__str__()

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
        self.node_states[new_state_id] = state

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

    def train_interrupt(self, irq_num, timestamp):
        """
        Make sure all observed interrupts are logged appropriately
        :param irq_num:
        :param timestamp:
        :return:
        """
        logger.info("got interrupt %d", irq_num)
        self.current_state[1].append_interrupt(irq_num)

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
        # return self.node_states[state_id]
        return self.graph.nodes[state_id]["state"]

    def _merge_states(self, equiv_states, skip_check=False):
        """
            Given a list of tuples of equivalent states, this find their equivalence classes, and make a single node for
             each equivalence class.

             Since our equality is non-transitive, we first do a check to make sure all of the merges will succeed.
             This can be skipped with the `skip_check` argument

        """
        graph = networkx.Graph(equiv_states)
        equiv_classes = [tuple(c) for c in networkx.connected_components(graph)]

        # First, we need to make sure that every node is truly equal to every other node.
        # Since we permit merging of states with no overlapping reads, our equality is not transitive
        # the case where A = B and B = C but A merge B != C is possible
        # e.g., A:[read 0:Storage], B:[read 1:Pattern], C:[read 0:Storage]
        if not skip_check:
            for equiv_set in equiv_classes:
                for state_id1 in equiv_set:
                    for state_id2 in equiv_set:
                        state1 = self._get_state(state_id1)
                        state2 = self._get_state(state_id2)
                        if state1 != state2:
                            logger.warning("Lack of transitivity in equality bit us, aborting merge")
                            logger.warning("%s != %s" % (state1, state2))
                            return False

        # Merge all of the equivalent nodes
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
                    if not state.merge(self._get_state(state_id)):
                        import traceback
                        traceback.print_exc()
                        logger.exception("A merge failed!  This should impossible!")

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
                    logger.info("%s: Adding self reference for %d" % (self.name, new_state_id))
                    for (address, value) in tuples:
                        self._add_edge(new_state_id, new_state_id,
                                       address=address, value=value)
                self.graph.remove_edge(*e)

            # Remove all of our old states
            for state_id in equiv_set:
                self.graph.remove_node(state_id)
                if state_id == self.start_state[0]:
                    self.start_state = (new_state_id, new_state)
        return True

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
            # if state_id_1 in self.visited and state_id_2 in self.visited:
            if set([state_id_1, state_id_2]) in self.visited:
                return merge_set

            # Marked the nodes as visited
            self.visited.append(set([state_id_1, state_id_2]))
            # self.visited.add(state_id_1)
            # self.visited.add(state_id_2)

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
            for e2 in equiv_edges:
                e2_labels = self._get_edge_labels(e2)
                # Check all outgoing edges for node 1
                for e1 in edges_1:
                    e1_labels = self._get_edge_labels(e1)
                    # Do we have a duplicate edge (i.e., state transition)
                    if e1_labels & e2_labels:
                        # Only add if they haven't already been visited
                        # if e1[1] not in self.visited and e2[1] not in self.visited:
                        if set([e1[1], e2[1]]) not in self.visited:
                            if (e2[1], e1[1]) not in merge_set:
                                merge_set.add((e1[1], e2[1]))

                # Check all outgoing edges for node 2
                for e1 in edges_2:
                    e1_labels = self._get_edge_labels(e1)
                    # Do we have a duplicate edge (i.e., state transition)
                    if e1_labels & e2_labels:
                        if (e2[1], e1[1]) not in merge_set:
                            merge_set.add((e1[1], e2[1]))
            return merge_set
        else:
            logger.debug(
                "%s and %s not mergable." % (str(state_id_1), str(state_id_2)))
            return False

    def optimize2(self):
        """
        This function will optimize the state machine, merging equivalent
        states.
        :return:
        """

        # First get rid of all of empty nodes (i.e., no reads were observed) by just merging them into the next
        # non-empty node
        last_node = None
        empty_merges = []
        for n in networkx.dfs_preorder_nodes(self.graph,
                                             self.start_state[0]):
            # Check if our last_visited node was empty
            if last_node is not None:
                state_last = self._get_state(last_node)
                if state_last.is_empty():
                    empty_merges.append((last_node, n))
                    logger.debug("Merged an empty state")
            last_node = n
        self._merge_states(empty_merges, skip_check=True)

        # TODO: Do better caching with equivalence classes?
        checked = set()
        merged = True
        while merged:
            merged = False

            # TODO: Figure out a more efficient way to do this, potentially with some caching of equivalence classes?
            for n1 in networkx.dfs_preorder_nodes(self.graph,
                                                  self.start_state[0]):
                for n2 in networkx.dfs_preorder_nodes(self.graph,
                                                      n1):

                    if (n1, n2) in checked or (n2, n1) in checked:
                        continue

                    logger.info("%s: Comparing %s and %s" % (self.name, str(n1), str(n2)))
                    if n1 == n2:
                        continue

                    self.equiv_states = []
                    self.visited = []

                    # Get a set of all of the nodes that must also be equal
                    merge_set = self._get_merge_constraints(n1, n2)
                    checked.add((n1, n2))

                    # These two nodes are not even equal to start with, no reason to attempt a merge
                    if merge_set is False:
                        continue

                    # Ensure that all shared outgoing edges are also mergable
                    mergable = True
                    checked2 = set()  # Cache so we don't keep re-checking the same values
                    while len(merge_set) != 0:
                        x, y = merge_set.pop()
                        logger.debug("\t* Comparing %s and %s" % (str(x), str(y)))

                        if (x, y) in checked2 or (y, x) in checked2:
                            continue

                        set2 = self._get_merge_constraints(x, y)
                        checked2.add((x, y))
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
                        if self._merge_states(self.equiv_states):
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
                            address=self_edge_attr[0], value=self_edge_attr[1])

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
        self.stats['reads'].append(address)

        if address not in self.current_state[1].model_per_address:
            logger.debug("%s: starting BFS search for read (0x%08X" % (self.name, address))
            # otherwise start BFS
            target_edges = list(
                networkx.edge_bfs(self.graph, source=self.current_state[0]))

            found = False
            for edge in target_edges:

                state = self._get_state(edge[1])
                logger.debug("%s: Checking node %s: %s" % (self.name, str(edge[1]), state))
                if address in state.model_per_address:
                    logger.debug(
                        "%s: BFS selected %s: %s" % (self.name, str(edge), str(self.graph.nodes[edge[1]]["state"])))
                    self.stats['bfs'] += 1
                    self.current_state = (
                        edge[1], self.graph.nodes[edge[1]]["state"])
                    self._queue_interrupts(self.current_state[1].interrupts)
                    found = True
                    break

            logger.warn(
                "%s: No matching states!  Finding an node that has this address (0x%08X)" % (self.name, address))
            # BFS failed, let's just find a node anywhere!
            for n in self.graph.nodes:
                state = self._get_state(n)
                logger.debug("%s: Checking node %s: %s" % (self.name, str(n), state))
                if address in state.model_per_address:
                    logger.debug(
                        "%s: Long jump selected %s: %s" % (self.name, str(n), str(self.graph.nodes[n]["state"])))
                    self.stats['long_jump'] += 1
                    self.current_state = (
                        n, self.graph.nodes[n]["state"])
                    self._queue_interrupts(self.current_state[1].interrupts)
                    found = True

            if not found:
                logger.error(
                    "%s: Could not find model for read address (%s)" % (
                        self.name, hex(address)))
                self.stats['failed'] += 1
                return 0

        value = self.current_state[1].model_per_address[address].read()
        logger.debug("%s: Read from %s value: %s" % (self.name,
                                                     hex(address),
                                                     hex(value)))
        return value

    def _update_state(self, new_state, address, value):
        """
        Update our the current state that we are in and queue any interrupts
        :param new_state:
        :return:
        """
        self.current_state = (
            new_state, self.graph.nodes[new_state]["state"])
        self._queue_interrupts(self.current_state[1].interrupts)

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

    def _queue_interrupts(self, interrupt_dict):
        """
        Queue our interrupt to be fired when `get_interrupts` is triggered
        :param irq_num: 
        :return: 
        """
        with conware_rlock:
            for irq_num in interrupt_dict:
                if irq_num not in self.pending_interrupts:
                    self.pending_interrupts[irq_num] = interrupt_dict[irq_num]
                else:
                    self.pending_interrupts[irq_num] += interrupt_dict[irq_num]

    def get_interrupts(self):
        """
        After every write we need to check and see if we have any interrupts to fire
        :return: a dictionary of interrupt numbers with their counts { irq_num: count }
        """
        with conware_rlock:
            # Store our interrupts and reset the queue
            tmp_interrupts = self.pending_interrupts
            self.pending_interrupts = {}

            if len(tmp_interrupts) > 0:
                self.stats['interrupts'].append(tmp_interrupts)
            return tmp_interrupts

            # if len(self.current_state[1].interrupts) > 0:
            #     self.stats['interrupts'].append(self.current_state[1].interrupts)
            # return self.current_state[1].interrupts

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
        self.stats['writes'].append((address, value))

        current_state_id = self.current_state[0]
        out_edges = self.graph.edges(current_state_id)
        for edge in out_edges:
            edge_tuple = list(self.graph[edge[0]][edge[1]]['tuples'])

            if (address, value) in edge_tuple:

                self._update_state(edge[1], address, value)
                return True

            elif edge in self.wildcard_edges and address in \
                    self.wildcard_edges[edge]:
                logger.debug("%s/%d Taking wildcard edge (%08X, %d)!" % (
                    self.name, self.current_state[0],
                    address, value))
                self.stats['wildcard'] += 1
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
                self.current_state[1].model_per_address[address].write(address, value)
                logger.info(
                    "simple storage!, writing to address: " + str(address))
                return True

        logger.debug("%s: Was not simple storage, starting BFS/Wildcard (0x%08X, %X)" % (self.name, address, value))
        # otherwise start BFS
        target_edges = list(
            networkx.edge_bfs(self.graph, source=self.current_state[0]))

        for edge in target_edges:

            edge_tuple = list(self.graph[edge[0]][edge[1]]['tuples'])

            logger.debug("%s: Checking tuple (%s,%s): %s" % (self.name, str(edge[0]), str(edge[1]), edge_tuple))
            if (address, value) in edge_tuple:
                self._update_state(edge[1], address, value)
                # self.current_state = (
                #     edge[1], self.graph.nodes[edge[1]]["state"])
                # if address in self.current_state[1].model_per_address:
                #     self.current_state[1].model_per_address[address].write(
                #         value)
                logger.debug(
                    "%s: BFS selected %s: %s" % (self.name, str(edge), str(self.graph.nodes[edge[1]]["state"])))
                self.stats['bfs'] += 1
                return True
            elif (edge, address) in self.wildcard_edges:
                self._update_state(edge[1], address, value)
                # self.current_state = (
                #     edge[1], self.graph.nodes[edge[1]]["state"])
                # if address in self.current_state[1].model_per_address:
                #     self.current_state[1].model_per_address[address].write(
                #         value)
                logger.debug("%s: Wildcard selected %s: %s" % (self.name, str(edge),
                                                               str(self.graph.nodes[edge[1]]["state"])))
                self.stats['bfs'] += 1
                self.stats['wildcard'] += 1
                return True

        logger.warn(
            "%s: No matching edge!, picking edge with most writes to target address" % self.name)
        # If we dont find value for address, look at all edges, with writes to that address, pick the one that has it
        # the most times
        picked_edge = ((None, None), 0)  # (edge, addresscount)
        all_edges = self.graph.edges
        for edge in all_edges:
            address_count = 0
            label = self._get_edge_labels(edge)
            for label_tuple in label:
                if label_tuple[0] == address:
                    address_count += 1
            if address_count > picked_edge[1]:
                picked_edge = (edge, address_count)

        if picked_edge == ((None, None), 0):
            logger.error("%s: We could not find any state where this write was seen before (%s, %s)" % (self.name,
                                                                                                        hex(address),
                                                                                                        hex(value)))
            # TODO: Do something smarter, create a new state on the fly?
            self.stats['failed'] += 1
            return True

        self.stats['long_jump'] += 1
        self._update_state(picked_edge[0][1], address, value)

        # self.current_state = (
        #     picked_edge[0][1], self.graph.nodes[picked_edge[0][1]]["state"])
        # logger.info("Picked edge: " + str(picked_edge[0]))
        # if address in self.current_state[1].model_per_address:
        #     self.current_state[1].model_per_address[address].write(address, value)
        return True

        # This address has never been written to, do nothing
        # TODO: Do something smarter, Create a new state on the fly?
        logger.error("%s: We couldn't find a transition matching that address "
                     "and value: %s : %s" % (self.name, hex(address),
                                             str(value)))
        return True

    def _update_wildcard_edges(self, threshold=3):
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
        new_states = {}
        # Update our states
        for n in self.graph.nodes:
            state = self._get_state(n)
            state.state_id = str(n) + append_str

            # Update our state mapping
            self.node_states[state.state_id] = state
            new_states[state.state_id] = state

        # Update start state
        self.start_state = (str(self.start_state[0]) + append_str,
                            self.start_state[1])
        # Update nodes in the graph
        self.graph = networkx.relabel_nodes(self.graph,
                                            lambda x: str(x) + append_str)

        return new_states

    def merge(self, other_peripheral):
        """
        Merge the other peripheral into this peripheral

        :param other_peripheral:
        :return:
        """

        # Make sure our keys for the nodes do not overlap
        # TODO: Change this support more than 2 model merges
        suffix = "_%d" % self.merge_count
        self.merge_count += 1
        other_states = other_peripheral.append_states(suffix)
        self.node_states.update(other_states)

        # create a new empty start state

        self._merge_map = {}
        if self._recursive_merge(self.start_state[0],
                                 other_peripheral.start_state[0], other_peripheral):
            # Rename our nodes to be equivalent
            other_peripheral.graph = networkx.relabel_nodes(
                other_peripheral.graph,
                self._merge_map)

            # Merge our graphs
            # Ref: https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.operators.binary.compose.html
            self.graph = networkx.compose(other_peripheral.graph, self.graph)

            # Merge the nodes and edges
            for merge_node in self._merge_map:
                state_id = self._merge_map[merge_node]

                # Merge the states
                state = self._get_state(state_id)
                state2 = other_peripheral._get_state(state_id)
                logger.info("Merged %s and %s" % (state_id, merge_node))
                state.merge(state2)

                # add all edges
                edges2 = other_peripheral.graph.out_edges(state_id)
                for e2 in edges2:
                    e2_labels = other_peripheral._get_edge_labels(e2)
                    for (address, value) in e2_labels:
                        self._add_edge(e2[0], e2[1], address, value)
        else:
            logger.error("Failed to merge %s and %s" % (self, other_peripheral))
            return False

        # Update labels
        self._label_nodes()

        # Update any wildcard edges
        self._update_wildcard_edges()
        return True

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
                # TODO: Why is this variable set?  Is this an error that we don't use it?

        # If we got to this point, we at least merged the two initial nodes
        return True
