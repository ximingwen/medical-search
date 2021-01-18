import jaydebeapi, os
import globalvar as gl
import math
import json

class treeNode:
    def __init__(self, nameValue, numOccur, parentNode,connection):
        self.name = nameValue
        self.count = numOccur
        self.nodeLink = None
        self.parent = parentNode
        self.children = {}
        self.curs=connection
 
    def inc(self, numOccur):
        self.count += numOccur
 
    def disp(self, ind=1):
        
        sql_str="select * from concept where concept.concept_code='"+str(self.name)+"'"
        self.curs.execute(sql_str)
        result = self.curs.fetchall()
        concept=str(self.name)
        if len(result)!=0:
            concept=result[0][1]
        
       
        #print ('  '*ind, self.name, ' ',concept,' ', self.count)
        for child in self.children.values():
            child.disp(ind+1)
    def todata(self,data):
        
        for child in self.children.values(): 
            data_node={}
        
            data_node["name"]=child.name+" ("+ str(child.count)+")" 
            data_node["children"]=[]
            data_node["count"]=child.count
            data.append(data_node)
            child.todata(data_node["children"])

        

def updateHeader(nodeToTest, targetNode):
    while nodeToTest.nodeLink != None:
        nodeToTest = nodeToTest.nodeLink
    nodeToTest.nodeLink = targetNode
def updateFPtree(items, inTree, headerTable, count,curs):
    if items[0] in inTree.children:
        # 判断items的第一个结点是否已作为子结点
        inTree.children[items[0]].inc(count)
    else:
        # 创建新的分支
        inTree.children[items[0]] = treeNode(items[0], count, inTree,curs)
        # 更新相应频繁项集的链表，往后添加
        if headerTable[items[0]][1] == None:
            headerTable[items[0]][1] = inTree.children[items[0]]
        else:
            updateHeader(headerTable[items[0]][1], inTree.children[items[0]])
    # 递归
    if len(items) > 1:
        updateFPtree(items[1:], inTree.children[items[0]], headerTable, count,curs)
 
def createFPtree(dataSet,curs, minSup=1):
    headerTable = {}
    
    new_dataSet={}
    for trans,count in dataSet.items():
        new_trans=set()
        for item in trans:
            sql_str="select * from concept where concept.concept_code='"+str(item)+"'"
            curs.execute(sql_str)
            result = curs.fetchall()
            concept=str(item)
            if len(result)!=0:
                concept=result[0][1]
            if concept not in new_trans:
                new_trans.add(concept)
                headerTable[concept] = headerTable.get(concept, 0) + count
        
        new_dataSet[frozenset(set(new_trans))]=count
    frequent_headerTable=headerTable.copy()
    for k in headerTable.keys():
        if headerTable[k] < minSup:
            del(frequent_headerTable[k]) # 删除不满足最小支持度的元素
    headerTable=frequent_headerTable
    freqItemSet = set(headerTable.keys()) # 满足最小支持度的频繁项集
    if len(freqItemSet) == 0:
        return None, None
    for k in headerTable:
        headerTable[k] = [headerTable[k], None] # element: [count, node]
 
    retTree = treeNode('Null Set', 5, None,curs)
    for tranSet, count in new_dataSet.items():
        # dataSet：[element, count]
        localD = {}
        for item in tranSet:
            if item in freqItemSet: # 过滤，只取该样本中满足最小支持度的频繁项
                localD[item] = headerTable[item][0] # element : count
                #print (item," ",headerTable[item][0])
        if len(localD) > 0:
            # 根据全局频数从大到小对单样本排序
            orderedItem = [v[0] for v in sorted(localD.items(), key=lambda p:p[1], reverse=True)]
            # 用过滤且排序后的样本更新树
            updateFPtree(orderedItem, retTree, headerTable, count,curs)
    return retTree, headerTable

# recursion
def ascendFPtree(leafNode, prefixPath):
    if leafNode.parent != None:
        prefixPath.append(leafNode.name)
        ascendFPtree(leafNode.parent, prefixPath)
# 条件模式基
def findPrefixPath(basePat, myHeaderTab):
    treeNode = myHeaderTab[basePat][1] # basePat在FP树中的第一个结点
    condPats = {}
    while treeNode != None:
        prefixPath = []
        ascendFPtree(treeNode, prefixPath) # prefixPath是倒过来的，从treeNode开始到根
        if len(prefixPath) > 1:
            condPats[frozenset(prefixPath[1:])] = treeNode.count # 关联treeNode的计数
        treeNode = treeNode.nodeLink # 下一个basePat结点
    return condPats
def mineFPtree(inTree, headerTable, minSup, preFix, freqItemList,condBases,curs):
    # 最开始的频繁项集是headerTable中的各元素
    bigL = [v[0] for v in sorted(headerTable.items(), key=lambda p:p[0])] # 根据频繁项的总频次排序
    for basePat in bigL: # 对每个频繁项
        newFreqSet = preFix.copy()
        newFreqSet.add(basePat)
        itemset_frequency=0
        for path in condBases:
            list_path=list(path)
            if basePat in list_path:
                itemset_frequency=itemset_frequency+condBases[path]

        newFreqSet_with_counts={
        "frequent_set":newFreqSet,
        "itemset_frequency":itemset_frequency
        }
        freqItemList.append(newFreqSet_with_counts)
        condPattBases = findPrefixPath(basePat, headerTable) # 当前频繁项集的条件模式基
        myCondTree, myHead = createFPtree(condPattBases, curs,minSup) # 构造当前频繁项的条件FP树
        
        if (myHead != None and len(preFix)<=1):
            # print 'conditional tree for: ', newFreqSet
            #myCondTree.disp(1)
            mineFPtree(myCondTree, myHead, minSup, newFreqSet, freqItemList,condPattBases,curs)
        


# 数据集
def createInitSet(search_result):
    retDict={}

    response = search_result['response']
    for i in range(len(response['docs'])):
        key = frozenset(response['docs'][i]['snomed_codes'])
        if key in retDict:
            retDict[key] += 1
        else:
            retDict[key] = 1
    return  retDict

def calculate_tf_idf(search_result,code2n):
    dsn_uid = "vaclabuser"
    dsn_pwd = "vaclab206"
    jdbc_driver_name = "org.postgresql.Driver"
    connection_string="jdbc:postgresql://sils-gotz.ad.unc.edu:8032/omop"
    conn = jaydebeapi.connect(jdbc_driver_name, connection_string, {'user': dsn_uid, 'password': dsn_pwd},jars='..\\jar\\postgresql-42.2.12.jar')
    curs = conn.cursor()

    code_frequency=search_result['facet_counts']['facet_fields']['snomed_codes']
    a=0
    code2tf_idf={}
    all_documents=29137784
    while (a <=len(code_frequency)/2):
        code=code_frequency[a]
        tf=math.log(code_frequency[a+1])
        sql_str="select * from concept where concept.concept_code='"+str(code)+"'"
        curs.execute(sql_str)
        result = curs.fetchall()
        concept=""
        if len(result)!=0:
            concept=result[0][1]
       
        idf=math.log(all_documents/int(code2n[code]))
        tf_idf=tf*idf
        code2tf_idf[code]={"value":tf_idf,
                           "concept":concept}
        a=a+2
    code2tf_idf={k: v for k, v in sorted(code2tf_idf.items(), key=lambda item: item[1]['value'],reverse=True)}
    gl._init(code2tf_idf,"tf_idf")

def turntodata( myFPtree):
    data=[]
    for child in myFPtree.children.values():
        data_node={}
        data_node["name"]=child.name+" ("+ str(child.count)+")" 
        data_node["children"]=[]
        data_node["count"]=child.count
        child.todata(data_node["children"])
        data.append(data_node)
    
    file = open('fp-tree.json','w',encoding='utf-8')
    json.dump(data,file,ensure_ascii=False)
    gl._init(data,"frequent_itemset")

def find_frequent_itemset(results):

    #build the connection
    
    dsn_uid = "vaclabuser"
    dsn_pwd = "vaclab206"
    jdbc_driver_name = "org.postgresql.Driver"
    connection_string="jdbc:postgresql://sils-gotz.ad.unc.edu:8032/omop"
    conn = jaydebeapi.connect(jdbc_driver_name, connection_string, {'user': dsn_uid, 'password': dsn_pwd},jars='..\\jar\\postgresql-42.2.12.jar')
    curs = conn.cursor()

    minSup = 1
    initSet = createInitSet(results)
    myFPtree, myHeaderTab = createFPtree(initSet,curs,minSup)
    #myFPtree.disp()
    myFreqList = []

    condPattBases={}
    for key,value  in myHeaderTab.items():
        condPattBases[frozenset(set([key]))]=value[0]
    '''
    
    mineFPtree(myFPtree, myHeaderTab, minSup, set([]), myFreqList,condPattBases,curs)
    
    for item in myFreqList:
        wordset=[]
        codeset=item["frequent_set"]
        frequency=item["itemset_frequency"]
        for code in codeset:
            sql_str="select * from concept where concept.concept_code='"+str(code)+"'"
            curs.execute(sql_str)
            result = curs.fetchall()
            concept=str(code)
            if len(result)!=0:
                concept=result[0][1]
            wordset.append(concept)
        print(wordset," ",frequency)
        print(codeset)


    
    data=[]
    code_for_layer_two=""
    for itemset in myFreqList:
        codeset=itemset["frequent_set"]
        frequency=itemset["itemset_frequency"]
        if len(codeset)==1:
            for code in codeset:             
                sql_str="select * from concept where concept.concept_code='"+str(code)+"'"
                curs.execute(sql_str)
                result = curs.fetchall()
                concept=str(code)
                if len(result)!=0:
                    concept=result[0][1]
                    node_concept=concept+" ("+ str(frequency)+") " +str(code)
                else:
                    node_concept=concept+" ("+ str(frequency)+")" 

                node_layer_one={"name":node_concept,"children":[]}
                data.append(node_layer_one)
        elif len(codeset)==2:
            for code_two in codeset:
                if (code_two!=code):
                    code_for_layer_two=code_two
                    sql_str="select * from concept where concept.concept_code='"+str(code_two)+"'"
                    curs.execute(sql_str)
                    result = curs.fetchall()
                    concept=str(code_two)
                    if len(result)!=0:
                        concept=result[0][1]
                        node_concept=concept+" ("+ str(frequency)+") " +str(code_two)
                    else:
                        node_concept=concept+" ("+ str(frequency)+")" 

                    node_layer_two={"name":node_concept,"children":[]}
                    node_layer_one["children"].append(node_layer_two)
        elif len(codeset)==3:
            for code_three in codeset:
                if (code_three!=code and code_three!=code_for_layer_two):
                    sql_str="select * from concept where concept.concept_code='"+str(code_three)+"'"
                    curs.execute(sql_str)
                    result = curs.fetchall()
                    concept=str(code_three)
                    if len(result)!=0:
                        concept=result[0][1]
                        node_concept=concept+" ("+ str(frequency)+") " +str(code_three)
                    else:
                        node_concept=concept+" ("+ str(frequency)+")" 

                    node_layer_three={"name":node_concept}
                    node_layer_two["children"].append(node_layer_three)


    
    '''         
    turntodata( myFPtree)
                





    