
class Node:
    def __init__(self, id, state, predcessorNode):
        self.id = id
        self.state = state
        self.predcessorNode = predcessorNode
        self.predcessors = self.setupAllPredcessorNodes()
        self.isChecked = False

    def getPredcessorNode(self):
        return self.predcessorNode

    def setupAllPredcessorNodes(self):
        allNodes = []
        curNode = self.getPredcessorNode()
        while (curNode != None):
            allNodes.append(curNode)
            curNode = curNode.getPredcessorNode()
        return allNodes

    def getAllPredcessorNodes(self):
        return self.predcessors

    def getName(self):
        return f"m{self.id}"

    def getAllPredcessorNames(self):
        allNames = []
        for node in self.getAllPredcessorNodes():
            allNames.insert(0, node.getName())
        return allNames

    def getGraphLabel(self):
        return f"{self.getName()}\n{self.state}\n({self.getAllPredcessorNames()})"

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

    def buildNodeLabelDict(self):
        data = {}
        for node in self.nodes:
            data[node.getName()] = node.getGraphLabel()
        return data
