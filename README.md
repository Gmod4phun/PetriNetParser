# PetriNetParser
 A program to compute various Petri Net related things

Requires **NumPy**: https://github.com/numpy/numpy - https://numpy.org/install/

*Requires the following Python packages*
-

- **numpy**
- **networkx**
- **matplotlib**

Usage
-

- Drag n' drop a **.xml** or **.pflow** file containing a petri net written in the **PetriFlow** language onto petrinetparser.py
- Let the program sort places/transitions automatically (use empty pattern) or provide a pattern (case sensitive)(such as IN p1 p2 p3 p4 OUT, or t1 t2 t3 t4 etc.)

*Current features*
-

- Calculates the Input, Output and Incidence matrices
- Calculates the Reachability Graph (if possible)
