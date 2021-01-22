# PetriNetParser
A Python program to compute various Petri Net related things

#### Requires the following Python packages to be installed
- **numpy**
- **networkx**
- **pyvis**

#### You can use an online Petri Net editor such as [this one](https://builder.interes.group/modeler)

#### Program Usage
- The Places and Transitions in the saved Petri Net file **MUST** have names, otherwise the program might work incorrectly
- Drag n' drop a **.xml** or **.pflow** file containing a petri net written in the **PetriFlow** language onto **petrinetparser.py**
- Set screen resolution (for proper HTML graph size)
- Let the program either sort places/transitions automatically (use empty pattern) or provide a pattern (case sensitive)(such as IN p1 p2 p3 p4 OUT, or t1 t2 t3 t4 etc.)

#### Current features
- Input, Output and Incidence matrices - prints matrix info to the console
- Presets and Postsets for Transitions - prints info to the console
- Reachability Graph (if possible) - saves graph into  ***reachability_graph.html***
- Reachability Graph for Workflow nets (if possible) - saves graph into ***workflow_reachability_graph.html***
- Coverability Tree - saves graph into ***coverability_tree.html***
- Coverability Graph - saves graph into ***coverability_graph.html***
