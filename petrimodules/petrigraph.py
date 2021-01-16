
class Node:
    def __init__(self, id, state, predcessorNode):
        self.id = id
        self.state = state
        self.predcessorNode = predcessorNode
        self.predcessors = self.setupAllPredcessorNodes()
        self.isChecked = False
        self.designationChar = "m"

    def getPredcessorNode(self):
        return self.predcessorNode

    def setupAllPredcessorNodes(self):
        if self.getPredcessorNode() is None:
            return []
        else:
            allNodes = list(self.getPredcessorNode().getAllPredcessorNodes())
            if self.getPredcessorNode() not in allNodes:
                allNodes.append(self.getPredcessorNode())
            return sorted(allNodes, key=lambda item: item.id, reverse=True)

    def getAllPredcessorNodes(self):
        return self.predcessors

    def getName(self):
        return f"{self.designationChar}{self.id}"

    def getAllPredcessorNames(self):
        allNames = []
        for node in self.getAllPredcessorNodes():
            allNames.insert(0, node.getName())
        return allNames

    def mergePredcessorNodesFrom(self, predNode):
        own = list(self.getAllPredcessorNodes())
        for node in predNode.getAllPredcessorNodes():
            if node not in own:
                own.append(node)
        if predNode not in own:
            own.append(predNode)
        self.predcessors = sorted(own, key=lambda item: item.id, reverse=True)

    def getGraphLabel(self):
        return f"{self.getName()}\n{self.state}\n({self.getAllPredcessorNames()})"

    def getGraphLabelCustomState(self, customstate):
        return f"{self.getName()}\n{customstate}\n({self.getAllPredcessorNames()})"

    def __str__(self):
        return f"{self.getName()} | {self.state} | ({self.getAllPredcessorNames()})"


class Graph:
    def __init__(self):
        self.nodeCount = 0
        self.nodes = []

    def addNode(self, state, predcessorNode=None):
        node = Node(self.nodeCount, state, predcessorNode)
        self.nodes.append(node)
        self.nodeCount += 1
        return node

    def hasNodeWithState(self, state):
        for node in self.nodes:
            if node.state == state:
                return True
        return False

    def getNodeWithState(self, state):
        for node in self.nodes:
            if node.state == state:
                return node
        return None

    def hasNodeWithName(self, name):
        for node in self.nodes:
            if node.getName() == name:
                return True
        return False

    def getNodeWithName(self, name):
        for node in self.nodes:
            if node.getName() == name:
                return node
        return None

    def buildNodeLabelDict(self):
        data = {}
        for node in self.nodes:
            data[node.getName()] = node.getGraphLabel()
        return data
