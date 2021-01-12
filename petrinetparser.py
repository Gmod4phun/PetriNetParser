# PetriNetParser

# make sure you have 'numpy' installed as it is required for matrices
# https://numpy.org/install/
# cmd: pip install numpy

import numpy as np
import networkx as nx
from pyvis import network as pvnet

import xml.etree.ElementTree as et
import sys
import os.path

from petrimodules import petrigraph


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
        return self.isStatic


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
        places = list(net.getPlaces()) # deep copy
        for label in pattern.split(" "):
            try:
                newObjects.append(places.pop(places.index(net.getPlaceByLabel(label))))
            except ValueError:
                print("Invalid place label specified, not sorting!")
                return
        if len(self.getPlaces()) != len(newObjects):
            print("New place count does not match the old one, not sorting!")
        else:
            self.setPlaces(newObjects)

    def sortTransitionsByPattern(self, pattern):
        newObjects = []
        transitions = list(net.getTransitions()) # deep copy
        for label in pattern.split(" "):
            try:
                newObjects.append(transitions.pop(transitions.index(net.getTransitionByLabel(label))))
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

    def isState2GreaterThan1(self, state1, state2):
        # returns True if state2 is greater, otherwise returns False
        if state1 == state2:
            return False
        for i in range(len(state1)):
            if state1[i] > state2[i]:
                return False
        return True

    def runTransition(self, transition, graphState):
        transitionIndex = self.getTransitions().index(transition)
        incidenceColumn = self.incidenceMatrix[:, transitionIndex]

        newGraphState = list(graphState)
        for place in net.getPlaces():
            placeIndex = self.getPlaces().index(place)
            newGraphState[placeIndex] += int(incidenceColumn[placeIndex])
        return newGraphState

# program

file = ""

tArgs = sys.argv
if len(tArgs) == 2:
    file = tArgs[1]
else:
    input("Error: No input file provided. Press ENTER to exit...")
    sys.exit(0)

if os.path.exists(file) and os.path.isfile(file):
    print("Parsing file:", file)
    print()
else:
    input("Error: Can't load file. Press ENTER to exit...")
    sys.exit(0)

tree = et.parse(file)
root = tree.getroot()

# check if file is xml or pflow (pflow has data encapsulated in extra subnet block, otherwise it's identical to xml)
isPflowFormat = root.find("subnet") is not None

prefix = "subnet/" if isPflowFormat else ""

# filling the net with data
net = Net()

for type_tag in root.findall(prefix + "place"):
    id = type_tag.find('id').text
    label = type_tag.find('label').text
    tokens = int(type_tag.find('tokens').text)
    static = type_tag.find('static').text
    net.addPlace(Place(id, label, tokens, static))

for type_tag in root.findall(prefix + "transition"):
    id = type_tag.find('id').text
    label = type_tag.find('label').text
    net.addTransition(Transition(id, label))

for type_tag in root.findall(prefix + "arc"):
    id = type_tag.find('id').text
    sourceId = type_tag.find('sourceId').text
    destinationId = type_tag.find('destinationId').text
    multiplicity = type_tag.find('multiplicity').text
    net.addArc(Arc(id, sourceId, destinationId, multiplicity))


# sort places and transitions for proper matrix format
net.printCurrentPlaceOrder()
sortPatternPlaces = input("New place sort order (leave empty to sort alphabetically): ")
if sortPatternPlaces == "":
    print("Sorting places alphabetically")
    net.sortPlaces()
else:
    net.sortPlacesByPattern(sortPatternPlaces)
net.printCurrentPlaceOrder()

print()
net.printCurrentTransitionOrder()
sortPatternTransitions = input("New transition sort order (leave empty to sort alphabetically): ")
if sortPatternTransitions == "":
    print("Sorting transitions alphabetically")
    net.sortTransitions()
else:
    net.sortTransitionsByPattern(sortPatternTransitions)
net.printCurrentTransitionOrder()

# order recap
print("\nCurrent places/transitions order")
net.printCurrentPlaceOrder()
net.printCurrentTransitionOrder()

#  setup matrices
nRows = len(net.getPlaces())
nColumns = len(net.getTransitions())

inputMatrix = np.array([[0 for i in range(nColumns)] for j in range(nRows)])
outputMatrix = np.array([[0 for i in range(nColumns)] for j in range(nRows)])

# fill each matrix with the proper data
for arc in net.getArcs():
    sourceId = arc.getSourceId()
    destinationId = arc.getDestinationId()

    source = None
    destination = None

    if (net.getPlaceById(sourceId) is not None) and (net.getTransitionById(destinationId) is not None):
        source = net.getPlaceById(sourceId)
        destination = net.getTransitionById(destinationId)
    elif (net.getTransitionById(sourceId) is not None) and (net.getPlaceById(destinationId) is not None):
        source = net.getTransitionById(sourceId)
        destination = net.getPlaceById(destinationId)

    sourceIdInNetList = None
    destinationIdInNetList = None

    if type(source) == Place:
        sourceIdInNetList = net.getPlaces().index(source)
        destinationIdInNetList = net.getTransitions().index(destination)
        inputMatrix[sourceIdInNetList, destinationIdInNetList] = arc.getMultiplicity()

    if type(source) == Transition:
        sourceIdInNetList = net.getTransitions().index(source)
        destinationIdInNetList = net.getPlaces().index(destination)
        outputMatrix[destinationIdInNetList, sourceIdInNetList] = arc.getMultiplicity()

# calculate incidence matrix
incidenceMatrix = outputMatrix - inputMatrix

# print info
print("\nInput matrix I:")
print(inputMatrix)

print("\nOutput matrix O:")
print(outputMatrix)

print("\nIncidence matrix C = O - I:")
print(incidenceMatrix)

# set matrices attributes for the net itself
net.inputMatrix = inputMatrix
net.outputMatrix = outputMatrix
net.incidenceMatrix = incidenceMatrix


# build reachability graph
# add first node manually
G = nx.MultiDiGraph()
graph = petrigraph.Graph()
baseNode = graph.addNode(net.getGraphState())
G.add_node(baseNode.getName())

# add the rest automatically
isInfinite = False
while True:
    allChecked = True
    for curNode in graph.nodes:
        if not curNode.isChecked:
            allChecked = False
            break

    if allChecked or isInfinite:
        break

    for curNode in graph.nodes:
        if isInfinite:
            break
        if not curNode.isChecked:
            for trans in net.getTransitions():
                if net.isTransitionRunnableFromState(trans, curNode.state):
                    newState = net.runTransition(trans, curNode.state)

                    for cycleNode in graph.nodes:
                        if net.isState2GreaterThan1(cycleNode.state, newState):
                            isInfinite = True
                            break
                    if isInfinite:
                        break

                    newNode = None
                    if graph.hasNodeWithState(newState):
                        newNode = graph.getNodeWithState(newState)
                        newNode.mergePredcessorNodesFrom(curNode)
                    else:
                        newNode = graph.addNode(newState, curNode)
                        # G.add_node(newNode.getName())

                    G.add_edge(curNode.getName(), newNode.getName(), label=trans.getLabel())
            curNode.isChecked = True

if not isInfinite:
    print("\nPlotting Reachability Graph...")

    reachability_graph = pvnet.Network(directed=True, width="1900px", height="900px", heading="Reachability graph")
    for node in G.nodes():
        nodeData = graph.getNodeWithName(node)
        nodeName = nodeData.getName()
        nodeLabel = nodeData.getGraphLabel()
        nodeColor = "lightgreen" if nodeName == "m0" else None
        reachability_graph.add_node(nodeName, label=nodeLabel, shape="box", color=nodeColor, title=nodeName)

    edgeDict = dict()
    for edge in G.edges(data=True):
        edgeLabel = edge[2]["label"]
        entryName = edge[0] + " " + edge[1]
        if entryName not in edgeDict.keys():
            edgeDict[entryName] = edgeLabel
        else:
            edgeDict[entryName] = edgeDict[entryName] + ", " + edgeLabel

    for nodeData, edgeLabel in edgeDict.items():
        nodes = nodeData.split(" ")
        srcNode = nodes[0]
        dstNode = nodes[1]
        reachability_graph.add_edge(srcNode, dstNode, label=edgeLabel, color="black", title=edgeLabel)

    reachability_graph.set_options(getPyvisOptions())
    reachability_graph.save_graph("reachability_graph.html")
else:
    print("\nReachability graph is infinite, can't plot.")

input("\nFinished, press ENTER to exit...")
