
import numpy as np

def parseDictFromFile(filepath):
    f = open(filepath, "r")
    t = f.readlines()
    f.close()

    t2 = t[0].split("nodes={[")
    t3 = t2[1].split("]} edges={[")
    t4 = t3[0].split("},{")

    t4[0] = (t4[0])[1:len(t4[0])]
    lastIndex = len(t4) - 1
    t4[lastIndex] = t4[lastIndex].replace("}}", "}")

    for i in range(len(t4)):
        t4[i] = t4[i].replace('options:{fixed:true},label:"', "")
        t4[i] = t4[i].replace('options:{fixed:false},label:"', "")
        t4[i] = t4[i].replace('",center:{x:', " ")
        t4[i] = t4[i].replace(',y:', " ")
        t4[i] = t4[i].replace('}', "")

    nodePosDict = dict()
    for entry in t4:
        data = entry.split(" ")
        label = data[0]
        x = float(data[1])
        y = float(data[2])
        nodePosDict[label] = np.array([x * 0.00005, -y * 0.01])

    return nodePosDict
