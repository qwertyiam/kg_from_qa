import networkx as nx
import matplotlib.pyplot as plt
import pymongo
import numpy as np
from pylab import mpl

mpl.rcParams['font.sans-serif'] = ['FangSong'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.haodf
train = db.train
diseases = db.diseases
symptoms = db.symptoms
medicines = db.medicines
examinations = db.examinations

G = nx.DiGraph()
# 疾病名称更加需求修改
fd = diseases.find_one({'name': '甲状腺结节'})
f = lambda x: x[1]
disease_name = fd['name']
G.add_node(disease_name, color='tomato', size=4000)
examination = sorted(fd['examinations'].items(), key=f, reverse=True)
medicine = sorted(fd['medicines'].items(), key=f, reverse=True)
symptom = sorted(fd['symptoms'].items(), key=f, reverse=True)

for i, e in enumerate(examination):
    if i > 3:
        break
    G.add_node(e[0], color='seagreen', size=1000, weight=e[1])
    G.add_edge(disease_name, e[0])
    fe = examinations.find_one({'name': e[0]})
    d_list = sorted(fe['diseases'].items(), key=f, reverse=True)
    for k, d in enumerate(d_list):
        if d[0] == disease_name:
            k -= 1
        if k > 2:
            break
        G.add_node(d[0], color='tomato', size=2000)
        G.add_edge(d[0], e[0])

for i, m in enumerate(medicine):
    if i > 3:
        break
    G.add_node(m[0], color='navajowhite', size=1000, weight=m[1])
    G.add_edge(disease_name, m[0])
    fm = medicines.find_one({'name': m[0]})
    d_list = sorted(fm['diseases'].items(), key=f, reverse=True)
    for k, d in enumerate(d_list):
        if d[0] == disease_name:
            k -= 1
        if k > 2:
            break
        G.add_node(d[0], color='tomato', size=2000)
        G.add_edge(d[0], m[0])

for i, s in enumerate(symptom):
    if i > 3:
        break
    G.add_node(s[0], color='lightskyblue', size=1000, weight=s[1])
    G.add_edge(disease_name, s[0])
    fs = symptoms.find_one({'name': s[0]})
    d_list = sorted(fs['diseases'].items(), key=f, reverse=True)
    for k, d in enumerate(d_list):
        if d[0] == disease_name:
            k -= 1
        if k > 2:
            break
        G.add_node(d[0], color='tomato', size=2000)
        G.add_edge(d[0], s[0])

G.add_node(disease_name, color='tomato', size=4000)
ncolor = [G.nodes[v]['color'] for v in G]
nsize = [G.nodes[v]['size'] for v in G]
pos = nx.circular_layout(G, scale=2)
pos['甲状腺结节'] = np.array([0, 0])
plt.figure(1, figsize=(9, 9))
nx.draw(G, pos, with_labels=True, node_size=nsize, node_color=ncolor)
plt.show()
