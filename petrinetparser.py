# PetriNetParser

# you should have pip installed by default with Python, if not, use google
# then, make sure you have the 'numpy', 'networkx' and 'pyvis' packages installed as they are required
# cmd: pip install numpy; pip install networkx; pip install pyvis


# default packages
import xml.etree.ElementTree as et
import sys
import os.path


# custom packages
try:
    import numpy as np
    import networkx as nx
    from pyvis import network as pvnet
except ModuleNotFoundError as err:
    print("One or more packages could not be loaded.")
    print("List of all required packages: numpy, networkx, pyvis")
    input("Press ENTER to exit...")
    sys.exit(-1)

from petrimodules import petrigraph


# global stuff
CONST_OMEGA_CHAR = "ω"
NODECOLOR_FIRST = "#7FFF8C"
NODECOLOR_GENERIC = "#8CCFFF"
NODECOLOR_LAST = "#FFC97F"


# functions
def getPyvisOptions():
    opts = '''
        var options = {
          "physics": {
            "enabled": false
          },
          "interaction": {
            "dragNodes": true,
            "hideEdgesOnDrag": false,
            "hideNodesOnDrag": false
        },
        "edges": {
            "smooth": {
                "enabled": true,
                "type": "continuous"
            }
        }
        }
    '''
    return opts


def calcGraphResolution():
    # screen resolution (for html graph size)
    scrw_in = input("Your screen width (leave empty for default 1920): ")
    scrh_in = input("Your screen height (leave empty for default 1080): ")
    SCR_W = 1920 if scrw_in == "" else int(scrw_in)
    SCR_H = 1080 if scrh_in == "" else int(scrh_in)
    print(f"Screen resolution: {SCR_W}x{SCR_H}\n")
    return SCR_W * 0.9875, SCR_H * 0.82


# classes
class Place:
    def __init__(self, id, label, tokens=0, static=False):
        self.id = id
        self.label = label
        self.tokens = tokens
        self.static = static

    def getId(self):
        return self.id

    def getLabel(self):
        return self.label

    def getTokens(self):
        return self.tokens

    def isStatic(self):
        return self.static


class Transition:
    def __init__(self, id, label):
        self.id = id
        self.label = label

    def getId(self):
        return self.id

    def getLabel(self):
        return self.label


class Arc:
    def __init__(self, id, sourceId, destinationId, multiplicity=1):
        self.id = id
        self.sourceId = sourceId
        self.destinationId = destinationId
        self.multiplicity = multiplicity
        self.source = None
        self.destination = None

    def getId(self):
        return self.id

    def getSourceId(self):
        return self.sourceId

    def getDestinationId(self):
        return self.destinationId

    def getMultiplicity(self):
        return self.multiplicity


class Net:
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
        self.inputMatrix = None
        self.outputMatrix = None
        self.incidenceMatrix = None

    def addPlace(self, place):
        self.places.append(place)

    def addTransition(self, transition):
        self.transitions.append(transition)

    def setPlaces(self, places):
        self.places = places

    def setTransitions(self, transitions):
        self.transitions = transitions

    def addArc(self, arc):
        self.arcs.append(arc)

    def getPlaces(self):
        return self.places

    def getTransitions(self):
        return self.transitions

    def getArcs(self):
        return self.arcs

    def getPlaceById(self, id):
        for obj in self.getPlaces():
            if obj.getId() == id:
                return obj
        return None

    def getTransitionById(self, id):
        for obj in self.getTransitions():
            if obj.getId() == id:
                return obj
        return None

    def getPlaceByLabel(self, label):
        for obj in self.getPlaces():
            if obj.getLabel() == label:
                return obj
        return None

    def getTransitionByLabel(self, label):
        for obj in self.getTransitions():
            if obj.getLabel() == label:
                return obj
        return None

    def sortObjectsByLabel(self, arr):
        n = len(arr)
        for i in range(n - 1):
            for j in range(0, n - i - 1):
                if arr[j].getLabel() > arr[j + 1].getLabel():
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]

    # def sortObjectsByLabel(self, arr):
    #     arr = sorted(arr, key=lambda item: item.getLabel(), reverse=True)

    def sortPlacesByPattern(self, pattern):
        newObjects = []
        places = list(self.getPlaces()) # deep copy
        for label in pattern.split(" "):
            try:
                newObjects.append(places.pop(places.index(self.getPlaceByLabel(label))))
            except ValueError:
                print("Invalid place label specified, not sorting!")
                return
        if len(self.getPlaces()) != len(newObjects):
            print("New place count does not match the old one, not sorting!")
        else:
            self.setPlaces(newObjects)

    def sortTransitionsByPattern(self, pattern):
        newObjects = []
        transitions = list(self.getTransitions()) # deep copy
        for label in pattern.split(" "):
            try:
                newObjects.append(transitions.pop(transitions.index(self.getTransitionByLabel(label))))
            except ValueError:
                print("Invalid transition label specified, not sorting!")
                return
        if len(self.getTransitions()) != len(newObjects):
            print("New transition count does not match the old one, not sorting!")
        else:
            self.setTransitions(newObjects)

    def sortPlaces(self):
        self.sortObjectsByLabel(self.places)

    def sortTransitions(self):
        self.sortObjectsByLabel(self.transitions)

    def printOrderedPlacesTransitions(self):
        print("   ", end="")
        for transition in self.getTransitions():
            print(transition.getLabel(), end=" ")
        print()
        for place in self.getPlaces():
            print(place.getLabel())

    def printCurrentPlaceOrder(self):
        print("Current place order: ", end="")
        for place in self.getPlaces():
            print(place.getLabel(), end=" ")
        print()

    def printCurrentTransitionOrder(self):
        print("Current transition order: ", end="")
        for transition in self.getTransitions():
            print(transition.getLabel(), end=" ")
        print()

    def getGraphState(self):
        graphState = []
        for p in self.getPlaces():
            graphState.append(p.getTokens())
        return graphState

    def isTransitionRunnableFromState(self, transition, graphState):
        transitionIndex = self.getTransitions().index(transition)
        inputColumn = self.inputMatrix[:, transitionIndex]
        curGraphState = graphState

        isRunnable = True
        for i in range(len(curGraphState)):
            available = int(curGraphState[i])
            required = int(inputColumn[i])
            if available < required:
                isRunnable = False
                break
        return isRunnable

    def isTransitionRunnableFromState_Omega(self, transition, graphState):
        transitionIndex = self.getTransitions().index(transition)
        inputColumn = self.inputMatrix[:, transitionIndex]
        curGraphState = graphState

        isRunnable = True
        for i in range(len(curGraphState)):
            available_char = curGraphState[i]
            required = int(inputColumn[i])

            # only check runnability if it isnt omega, if its omega it counts as always runnable
            if available_char != CONST_OMEGA_CHAR:
                available = int(curGraphState[i])
                if available < required:
                    isRunnable = False
                    break
        return isRunnable

    def isState2GreaterThan1(self, state1, state2):
        # returns True if state2 is greater, otherwise returns False
        if state1 == state2:
            return False
        for i in range(len(state1)):
            if state1[i] > state2[i]:
                return False
        return True

    def isState2GreaterThan1_Omega(self, state1, state2):
        # returns True if state2 is greater, otherwise returns False
        if state1 == state2:
            return False
        for i in range(len(state1)):
            s1 = state1[i]
            s2 = state2[i]
            # if they are not omegas, do regular check
            # if s1 is omega and s2 is not, s1 has to be greater
            # otherwise s2 has to be greater
            if s1 != CONST_OMEGA_CHAR and s2 != CONST_OMEGA_CHAR and s1 > s2:
                return False
            if s1 == CONST_OMEGA_CHAR and s2 != CONST_OMEGA_CHAR:
                return False
        return True

    def transformState2ToOmega(self, state1, state2):
        for i in range(len(state1)):
            s1 = state1[i]
            s2 = state2[i]

            if s1 != CONST_OMEGA_CHAR and s2 != CONST_OMEGA_CHAR and s2 > s1:
                state2[i] = CONST_OMEGA_CHAR
        return state2

    def runTransition(self, transition, graphState):
        transitionIndex = self.getTransitions().index(transition)
        incidenceColumn = self.incidenceMatrix[:, transitionIndex]

        newGraphState = list(graphState)
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            newGraphState[placeIndex] += int(incidenceColumn[placeIndex])
        return newGraphState

    def runTransition_Omega(self, transition, graphState):
        transitionIndex = self.getTransitions().index(transition)
        incidenceColumn = self.incidenceMatrix[:, transitionIndex]

        newGraphState = list(graphState)
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            # only change tokens if we arent omega
            if newGraphState[placeIndex] != CONST_OMEGA_CHAR:
                newGraphState[placeIndex] += int(incidenceColumn[placeIndex])
        return newGraphState

    def getWorkflowStateFromState(self, state):
        newState = []
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            if not place.isStatic():
                tokens = state[placeIndex]
                finalTokens = "" if tokens == 1 else str(tokens)
                text = f"{finalTokens}{place.getLabel()}"
                if tokens > 0:
                    newState.append(text)
        return " + ".join(newState)

    def createEdgeDictFromGraph(self, graph):
        edgeDict = dict()
        for edge in graph.edges(data=True):
            edgeLabel = edge[2]["label"]
            entryName = edge[0] + " " + edge[1]
            if entryName not in edgeDict.keys():
                edgeDict[entryName] = edgeLabel
            else:
                edgeDict[entryName] = edgeDict[entryName] + ", " + edgeLabel
        return edgeDict

    def updateMultiEdgesForPyvisgraph(self, graph):
        edgeDict = dict()
        for edge in graph.get_edges():
            edgeLabel = edge["label"]
            entryName = edge["from"] + " " + edge["to"]
            if entryName not in edgeDict.keys():
                edgeDict[entryName] = edgeLabel
            else:
                edgeDict[entryName] = edgeDict[entryName] + ", " + edgeLabel
        # delete old edges, add new ones
        graph.edges = []
        for key, value in edgeDict.items():
            nodeData = key.split(" ")
            nodeFrom = nodeData[0]
            nodeTo = nodeData[1]
            edgeLabel = value
            graph.add_edge(nodeFrom, nodeTo, label=edgeLabel, color="black", title=edgeLabel)

    def printTransitionPreset(self, transition):
        transitionIndex = self.getTransitions().index(transition)
        inputColumn = self.inputMatrix[:, transitionIndex]

        placeList = []
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            if inputColumn[placeIndex] > 0:
                placeList.append(place.getLabel())
        print("•", transition.getLabel(), end=" = {", sep="")
        print(", ".join(placeList), end="}\n")

    def printTransitionPostset(self, transition):
        transitionIndex = self.getTransitions().index(transition)
        inputColumn = self.outputMatrix[:, transitionIndex]

        placeList = []
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            if inputColumn[placeIndex] > 0:
                placeList.append(place.getLabel())
        print(transition.getLabel(), "•", end=" = {", sep="")
        print(", ".join(placeList), end="}\n")

    def printAllTransitionsPresets(self):
        print("\nTransitions presets:")
        for t in self.getTransitions():
            self.printTransitionPreset(t)

    def printAllTransitionsPostsets(self):
        print("\nTransitions postsets:")
        for t in self.getTransitions():
            self.printTransitionPostset(t)

    def getLeafNodesFromGraph(self, graph):
        nodesWithoutSuccessors = []
        for node in graph.nodes():
            successorCount = 0
            for _ in graph.successors(node):
                successorCount += 1
            if successorCount == 0:
                nodesWithoutSuccessors.append(node)
        return nodesWithoutSuccessors

    def getGraphStatesOccurenceCount(self, graph, petrigraph):
        nodeStates = dict()
        for node in graph.nodes():
            nodeData = petrigraph.getNodeWithName(node)
            nodeState = str(nodeData.state)
            if nodeState not in nodeStates:
                nodeStates[nodeState] = 1
            else:
                nodeStates[nodeState] += 1
        return nodeStates


# program

file = ""

tArgs = sys.argv
if len(tArgs) == 2:
    file = tArgs[1]
else:
    input("Error: No input file provided. Press ENTER to exit...")
    sys.exit(-1)

if os.path.exists(file) and os.path.isfile(file):
    print("Parsing file:", file)
    print()
else:
    input("Error: Can't load file. Press ENTER to exit...")
    sys.exit(-1)

PYVISGRAPH_W, PYVISGRAPH_H = calcGraphResolution()

tree = et.parse(file)
root = tree.getroot()

# check if file is xml or pflow (pflow has data encapsulated in extra subnet block, otherwise it's identical to xml)
isPflowFormat = root.find("subnet") is not None

prefix = "subnet/" if isPflowFormat else ""

# filling the net with data
petri_net = Net()

for type_tag in root.findall(prefix + "place"):
    id = type_tag.find('id').text
    label = type_tag.find('label').text
    tokens = int(type_tag.find('tokens').text)
    static = True if type_tag.find('static').text == "true" else False
    petri_net.addPlace(Place(id, label, tokens, static))

for type_tag in root.findall(prefix + "transition"):
    id = type_tag.find('id').text
    label = type_tag.find('label').text
    petri_net.addTransition(Transition(id, label))

for type_tag in root.findall(prefix + "arc"):
    id = type_tag.find('id').text
    sourceId = type_tag.find('sourceId').text
    destinationId = type_tag.find('destinationId').text
    multiplicity = type_tag.find('multiplicity').text
    petri_net.addArc(Arc(id, sourceId, destinationId, multiplicity))


# sort places and transitions for proper matrix format
petri_net.printCurrentPlaceOrder()
sortPatternPlaces = input("New place sort order (leave empty to sort alphabetically): ")
if sortPatternPlaces == "":
    print("Sorting places alphabetically")
    petri_net.sortPlaces()
else:
    petri_net.sortPlacesByPattern(sortPatternPlaces)
petri_net.printCurrentPlaceOrder()

print()
petri_net.printCurrentTransitionOrder()
sortPatternTransitions = input("New transition sort order (leave empty to sort alphabetically): ")
if sortPatternTransitions == "":
    print("Sorting transitions alphabetically")
    petri_net.sortTransitions()
else:
    petri_net.sortTransitionsByPattern(sortPatternTransitions)
petri_net.printCurrentTransitionOrder()

# order recap
print("\nCurrent places/transitions order")
petri_net.printCurrentPlaceOrder()
petri_net.printCurrentTransitionOrder()

#  setup matrices
nRows = len(petri_net.getPlaces())
nColumns = len(petri_net.getTransitions())

inputMatrix = np.array([[0 for i in range(nColumns)] for j in range(nRows)])
outputMatrix = np.array([[0 for i in range(nColumns)] for j in range(nRows)])

# fill each matrix with the proper data
for arc in petri_net.getArcs():
    sourceId = arc.getSourceId()
    destinationId = arc.getDestinationId()

    source = None
    destination = None

    if (petri_net.getPlaceById(sourceId) is not None) and (petri_net.getTransitionById(destinationId) is not None):
        source = petri_net.getPlaceById(sourceId)
        destination = petri_net.getTransitionById(destinationId)
    elif (petri_net.getTransitionById(sourceId) is not None) and (petri_net.getPlaceById(destinationId) is not None):
        source = petri_net.getTransitionById(sourceId)
        destination = petri_net.getPlaceById(destinationId)

    sourceIdInNetList = None
    destinationIdInNetList = None

    if type(source) == Place:
        sourceIdInNetList = petri_net.getPlaces().index(source)
        destinationIdInNetList = petri_net.getTransitions().index(destination)
        inputMatrix[sourceIdInNetList, destinationIdInNetList] = arc.getMultiplicity()

    if type(source) == Transition:
        sourceIdInNetList = petri_net.getTransitions().index(source)
        destinationIdInNetList = petri_net.getPlaces().index(destination)
        outputMatrix[destinationIdInNetList, sourceIdInNetList] = arc.getMultiplicity()

# calculate incidence matrix
incidenceMatrix = outputMatrix - inputMatrix

# set matrices attributes for the net itself
petri_net.inputMatrix = inputMatrix
petri_net.outputMatrix = outputMatrix
petri_net.incidenceMatrix = incidenceMatrix

# print info
print("\nInput matrix I:")
print(petri_net.inputMatrix)

print("\nOutput matrix O:")
print(petri_net.outputMatrix)

print("\nIncidence matrix C = O - I:")
print(petri_net.incidenceMatrix)

# transition presets/postsets
petri_net.printAllTransitionsPresets()
petri_net.printAllTransitionsPostsets()

# REACHABILITY GRAPH
# build reachability graph
reach_nxgraph = nx.MultiDiGraph()
reach_petrigraph = petrigraph.Graph()

# add first node manually
baseNode = reach_petrigraph.addNode(petri_net.getGraphState())
reach_nxgraph.add_node(baseNode.getName())

# variable to check whether or not the reachability graph is infinite
isInfinite = False
while True:
    allChecked = True
    for curNode in reach_petrigraph.nodes:
        if not curNode.isChecked:
            allChecked = False
            break

    # if all nodes are checked or graph is infinite, stop
    if allChecked or isInfinite:
        break

    for curNode in reach_petrigraph.nodes:
        if isInfinite:
            break
        if not curNode.isChecked:
            for trans in petri_net.getTransitions():
                if petri_net.isTransitionRunnableFromState(trans, curNode.state):
                    newState = petri_net.runTransition(trans, curNode.state)

                    curNodePredcessors = (curNode.getAllPredcessorNames() + [curNode.getName()])
                    for cycleNode in reach_petrigraph.nodes:
                        # only check predcessors
                        if cycleNode.getName() in curNodePredcessors:
                            if petri_net.isState2GreaterThan1(cycleNode.state, newState):
                                isInfinite = True
                                break
                    if isInfinite:
                        break

                    newNode = None
                    if reach_petrigraph.hasNodeWithState(newState):
                        newNode = reach_petrigraph.getNodeWithState(newState)
                        if newNode != curNode:
                            newNode.mergePredcessorNodesFrom(curNode)
                    else:
                        newNode = reach_petrigraph.addNode(newState, curNode)

                    reach_nxgraph.add_edge(curNode.getName(), newNode.getName(), label=trans.getLabel())
            curNode.isChecked = True


# if the graph is infinite, we cant create it, otherwise we can
if not isInfinite:
    print("\nPlotting Reachability Graphs...")

    reach_pyvisgraph = pvnet.Network(directed=True, width=PYVISGRAPH_W, height=PYVISGRAPH_H, heading="Reachability graph")
    reach_pyvisgraph_workflow = pvnet.Network(directed=True, width=PYVISGRAPH_W, height=PYVISGRAPH_H, heading="Reachability graph (Workflow)")
    for node in reach_nxgraph.nodes():
        nodeData = reach_petrigraph.getNodeWithName(node)
        nodeName = nodeData.getName()
        nodeLabel = nodeData.getGraphLabel()
        nodeColor = NODECOLOR_FIRST if node == list(reach_nxgraph.nodes())[0] else NODECOLOR_GENERIC
        nodeColor = NODECOLOR_LAST if node == list(reach_nxgraph.nodes())[-1] else nodeColor
        reach_pyvisgraph.add_node(nodeName, label=nodeLabel, shape="box", color=nodeColor, title=nodeName)
        # label for workflow graph (place names (but no static places), and no predcessors to reduce visual clutter)
        # predcessors are still available upon mouse hover over node
        nodeLabelWorkflow = nodeData.getGraphLabelCustom(petri_net.getWorkflowStateFromState(nodeData.state), "")
        nodeTitleWorkflow = "Predcessors: " + " ".join(nodeData.getAllPredcessorNames())
        reach_pyvisgraph_workflow.add_node(nodeName, label=nodeLabelWorkflow, shape="box", color=nodeColor, title=nodeTitleWorkflow)

    for nodeData, edgeLabel in petri_net.createEdgeDictFromGraph(reach_nxgraph).items():
        nodes = nodeData.split(" ")
        reach_pyvisgraph.add_edge(nodes[0], nodes[1], label=edgeLabel, color="black", title=edgeLabel)
        reach_pyvisgraph_workflow.add_edge(nodes[0], nodes[1], label=edgeLabel, color="black", title=edgeLabel)

    filename_reachgraph = "reachability_graph.html"
    print(f"Saving the result to '{filename_reachgraph}'")
    reach_pyvisgraph.set_options(getPyvisOptions())
    reach_pyvisgraph.save_graph(filename_reachgraph)

    filename_reachgraph_workflow = "workflow_reachability_graph.html"
    print(f"Saving the result to '{filename_reachgraph_workflow}'")
    reach_pyvisgraph_workflow.set_options(getPyvisOptions())
    reach_pyvisgraph_workflow.save_graph(filename_reachgraph_workflow)
else:
    print("\nReachability graph is infinite, can't plot.")

''' --------------------------------------------------------------
------------------------------------------------------------------
------------------------------------------------------------------
------------------------------------------------------------------
------------------------------------------------------------------
-------------------------------------------------------------- '''

# COVERABILITY TREE (old one, needed for coverability graph) (refactor this some day :P)
# build coverability tree (old)
cover_nxtree_old = nx.MultiDiGraph()
cover_petritree_old = petrigraph.Graph()

# add first node manually
baseNode = cover_petritree_old.addNode(petri_net.getGraphState())
baseNode.designationChar = "v"
cover_nxtree_old.add_node(baseNode.getName())

while True:
    allChecked = True
    for curNode in cover_petritree_old.nodes:
        if not curNode.isChecked:
            allChecked = False
            break

    # if all nodes are checked, stop
    if allChecked:
        break

    for curNode in cover_petritree_old.nodes:
        if not curNode.isChecked:
            for trans in petri_net.getTransitions():
                if petri_net.isTransitionRunnableFromState_Omega(trans, curNode.state):
                    newState = petri_net.runTransition_Omega(trans, curNode.state)

                    curNodePredcessors = (curNode.getAllPredcessorNames() + [curNode.getName()])
                    for cycleNode in cover_petritree_old.nodes:
                        # only check predcessors
                        if cycleNode.getName() in curNodePredcessors:
                            if petri_net.isState2GreaterThan1_Omega(cycleNode.state, newState):
                                newState = petri_net.transformState2ToOmega(cycleNode.state, newState)
                                break

                    newNode = None
                    if cover_petritree_old.hasNodeWithState(newState):
                        newNode = cover_petritree_old.addNode(newState, curNode)
                        newNode.isChecked = True
                    else:
                        newNode = cover_petritree_old.addNode(newState, curNode)

                    newNode.designationChar = "v"

                    cover_nxtree_old.add_edge(curNode.getName(), newNode.getName(), label=trans.getLabel())
            curNode.isChecked = True


# new coverability tree

# COVERABILITY TREE (new, good)
# build coverability tree
cover_nxtree = nx.MultiDiGraph()
cover_petritree = petrigraph.Graph()

# add first node manually
baseNode = cover_petritree.addNode(petri_net.getGraphState())
baseNode.designationChar = "v"
cover_nxtree.add_node(baseNode.getName())

while True:
    allChecked = True
    for curNode in cover_petritree.nodes:
        if not curNode.isChecked:
            allChecked = False
            break

    # if all nodes are checked, stop
    if allChecked:
        break

    for curNode in cover_petritree.nodes:
        if not curNode.isChecked:
            for trans in petri_net.getTransitions():
                if petri_net.isTransitionRunnableFromState_Omega(trans, curNode.state):
                    newState = petri_net.runTransition_Omega(trans, curNode.state)

                    curNodePredcessors = (curNode.getAllPredcessorNames() + [curNode.getName()])
                    for cycleNode in cover_petritree.nodes:
                        # only check predcessors
                        if cycleNode.getName() in curNodePredcessors:
                            # print(f"Node {curNode.getName()} with state {curNode.state}, transition {trans.getLabel()}, comparing new state {newState} with cyclestate {cycleNode.state}")
                            if petri_net.isState2GreaterThan1_Omega(cycleNode.state, newState):
                                newState = petri_net.transformState2ToOmega(cycleNode.state, newState)
                                # print(f"New state is greater, transforming to {newState}")
                                break

                    newNode = cover_petritree.addNode(newState, curNode)
                    newNode.designationChar = "v"

                    newNodePredcessors = newNode.getAllPredcessorNames()
                    for cycleNode in cover_petritree.nodes:
                        if cycleNode.getName() in newNodePredcessors:
                            if cycleNode.state == newNode.state:
                                newNode.isChecked = True
                                break

                    cover_nxtree.add_edge(curNode.getName(), newNode.getName(), label=trans.getLabel())
            curNode.isChecked = True


print("\nPlotting Coverability Tree...")
cover_pyvistree = pvnet.Network(directed=True, width=PYVISGRAPH_W, height=PYVISGRAPH_H, heading="Coverability tree")
for node in cover_nxtree.nodes():
    nodeData = cover_petritree.getNodeWithName(node)
    nodeName = nodeData.getName()
    nodeLabel = nodeData.getGraphLabel()
    nodeColor = NODECOLOR_FIRST if node == list(cover_nxtree.nodes())[0] else NODECOLOR_GENERIC
    nodeColor = NODECOLOR_LAST if node == list(cover_nxtree.nodes())[-1] else nodeColor
    cover_pyvistree.add_node(nodeName, label=nodeLabel, shape="box", color=nodeColor, title=nodeName)

for nodeData, edgeLabel in petri_net.createEdgeDictFromGraph(cover_nxtree).items():
    nodes = nodeData.split(" ")
    cover_pyvistree.add_edge(nodes[0], nodes[1], label=edgeLabel, color="black", title=edgeLabel)

filename_covertree = "coverability_tree.html"
print(f"Saving the result to '{filename_covertree}'")
cover_pyvistree.set_options(getPyvisOptions())
cover_pyvistree.save_graph(filename_covertree)


# COVERABILITY GRAPH
print("\nPlotting Coverability Graph...")
cover_pyvisgraph = pvnet.Network(directed=True, width=PYVISGRAPH_W, height=PYVISGRAPH_H, heading="Coverability graph")
for node in cover_nxtree_old.nodes():
    nodeData = cover_petritree_old.getNodeWithName(node)
    nodeName = nodeData.getName()
    nodeLabel = nodeData.getGraphLabel()
    nodeColor = NODECOLOR_FIRST if node == list(cover_nxtree_old.nodes())[0] else NODECOLOR_GENERIC
    nodeColor = NODECOLOR_LAST if node == list(cover_nxtree_old.nodes())[-1] else nodeColor
    cover_pyvisgraph.add_node(nodeName, label=nodeLabel, shape="box", color=nodeColor, title=nodeName)

for nodeData, edgeLabel in petri_net.createEdgeDictFromGraph(cover_nxtree_old).items():
    nodes = nodeData.split(" ")
    cover_pyvisgraph.add_edge(nodes[0], nodes[1], label=edgeLabel, color="black", title=edgeLabel)

# edit old coverability tree to make coverability graph
nodeStates = petri_net.getGraphStatesOccurenceCount(cover_nxtree_old, cover_petritree_old)
nodeMergeDict = dict()
for node in reversed(petri_net.getLeafNodesFromGraph(cover_nxtree_old)):
    nodeData = cover_petritree_old.getNodeWithName(node)
    nodeState = str(nodeData.state)
    # if there is more than 1 node with this state, we will merge them
    if nodeState in nodeStates.keys() and nodeStates[nodeState] > 1:
        # take this node and find the first node in graph with the same state
        for cycleNode in cover_nxtree_old.nodes():
            cycleNodeData = cover_petritree_old.getNodeWithName(cycleNode)
            cycleNodeState = str(cycleNodeData.state)
            # if we found a node with same state, but only if it isn't the same node (aka don't merge to itself)
            # if it's the same node, break and move on without doing anything
            if cycleNodeState == nodeState and cycleNode == node:
                break
            if cycleNodeState == nodeState:
                nodeMergeDict[node] = cycleNode
                break

# reroute the edges from old nodes to new nodes
nodesToRemove = []
for oldNode, newNode in nodeMergeDict.items():
    for edge in cover_pyvisgraph.get_edges():
        nodeTo = edge["to"]
        if oldNode == nodeTo:
            edge["to"] = newNode
            nodesToRemove.append(nodeTo)

# remove the old nodes
newNodes = []
for node in cover_pyvisgraph.nodes:
    if node["id"] not in nodesToRemove:
        nodeLabel = node["label"].split("\n")[1]
        nodeLabel = "\n"+nodeLabel+"\n"
        node["label"] = nodeLabel
        node["title"] = nodeLabel
        newNodes.append(node)
cover_pyvisgraph.nodes = newNodes

petri_net.updateMultiEdgesForPyvisgraph(cover_pyvisgraph)

filename_covergraph = "coverability_graph.html"
print(f"Saving the result to '{filename_covergraph}'")
cover_pyvisgraph.set_options(getPyvisOptions())
cover_pyvisgraph.save_graph(filename_covergraph)

input("\nFinished, press ENTER to exit...")
