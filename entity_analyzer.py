import requests
import json
from bs4 import BeautifulSoup  as Soup
#import gensim.downloader as api
import numpy as np
import pandas as pd
from functools import reduce
from scipy.cluster.hierarchy import dendrogram, linkage,to_tree
from sklearn.cluster import KMeans
import jaydebeapi, os
import globalvar as gl
#from graphviz import Digraph
import re
import networkx as nx


  
   


def dag_builder():
     #build the connection
    dsn_uid = "vaclabuser"
    dsn_pwd = "vaclab206"
    jdbc_driver_name = "org.postgresql.Driver"
    connection_string="jdbc:postgresql://sils-gotz.ad.unc.edu:8032/omop"
    conn = jaydebeapi.connect(jdbc_driver_name, connection_string, {'user': dsn_uid, 'password': dsn_pwd},jars='..\\jar\\postgresql-42.2.12.jar')
    curs = conn.cursor()
   

    # build p2c
    top_level=[]
    p2c={}
    c2p={}
   
    snomed_codes=gl.get_value("snomed_codes")
    print("create dictionary")
    create_p2c_and_c2p(snomed_codes,top_level,p2c,c2p,curs)
    draw_dag_from_snomed_code(snomed_codes,top_level,curs,p2c)
 

def k_means_clustering(snomed_codes,model,curs):
    model=snomed_embedding()
    X = np.zeros(shape=(1,200))
    label_list=[]
    code_list=[]
   
    for code in snomed_codes:
        concept =code2string(code,curs)
        if concept !="" and code in model.keys():
            label_list.append(concept)
            code_list.append(code)
            X=np.concatenate((X,model[code].reshape(1,200)),axis=0) 
    
    X=np.delete(X,0,axis=0)
    if(len(X)!=0):
        cluster_num=min(int(len(snomed_codes)/5)+1,6)
        print('cluster num: ', cluster_num)
        kmeans = KMeans(n_clusters=cluster_num, init='k-means++', max_iter=300, n_init=10, random_state=0)
        result = kmeans.fit(X)

        cluster_map = pd.DataFrame()
        cluster_map['concept_code'] = code_list
        cluster_map['concept_name'] = label_list
        cluster_map['cluster'] = kmeans.labels_

    return cluster_map

def draw_dag_from_cluster_result(cluster_map,top_level,curs,p2c):
   
   
    color=['aliceblue','antiquewhite','cyan', 'aquamarine','springgreen' ,'turquoise','violet','yellow','yellowgreen','tomato','darkorange','darkorchid','maroon','darksalmon','darkseagreen','darkslateblue','darkslategray','green','greenyellow','skyblue','goldenrod','lightslategray','mediumblue','royalblue','red','mediumvioletred']
    edge={}
    tagged_nodes={}

    with open(os.path.join("static","data","DAG","dag.dot"), "w") as file:
        file.write('digraph g {'+'\n')
        for top_code in top_level:
            add_snomed_node_for_dag_non_color(top_code,'snomed',file,curs,p2c,edge,tagged_nodes)
        
        for each in cluster_map.itertuples():
            code=each[1]
            cluster=each[3]
            file.write(code+' [ style=filled, fillcolor='+color[cluster]+'];\n')



        file.write('}')


def draw_dag_from_snomed_code(snomed_codes,top_level,curs,p2c):
   
   
    color=['aliceblue','antiquewhite','cyan', 'aquamarine','springgreen' ,'turquoise','violet','yellow','yellowgreen','tomato','darkorange','darkorchid','maroon','darksalmon','darkseagreen','darkslateblue','darkslategray','green','greenyellow','skyblue','goldenrod','lightslategray','mediumblue','royalblue','red','mediumvioletred']
    edge={}
    tagged_nodes={}

    with open(os.path.join("static","data","DAG","new.dot"), "w") as file:
        file.write('digraph g {'+'\n')
        for top_code in top_level:
            add_snomed_node_for_dag_non_color(top_code,'snomed',file,curs,p2c,edge,tagged_nodes)
        
        for name in snomed_codes:
            
            file.write(name+" [ style=filled, fillcolor=\"aliceblue\"];\n")



        file.write('}')




def cut_nodes(cluster_map,snomed_codes,top_level,curs,p2c,c2p):
    
    print("cut nodes")
    # cut nodes:
    children_dic={}
    parent_dic={}
    cluster_num=min(int(len(snomed_codes)/7)+1,6)
    new_cluster_num=list(range(0,cluster_num))
    for i in range(cluster_num):
        cluster=cluster_map[cluster_map['cluster']==i]['concept_code'].tolist()
        redundant_concept=[]
        if len(cluster)==1:
            new_cluster_num.remove(i)
            redundant_concept.append(cluster[0])
            continue

        children_dic[i]={}
        for code in cluster:
            if code in p2c:
                children_dic[i][code]=[]
                childrens=p2c[code]
                for children in childrens:
                    get_all_the_children(code,children,p2c,children_dic[i])

        #get redundant concepts
        new_cluster=cluster
        for key,value in children_dic[i].items():
            cluster=new_cluster
            for each in cluster:
                if each in value:
                    redundant_concept.append(key)
                    new_cluster.remove(key)
                    break

            if len(new_cluster)==1:
                redundant_concept.append(new_cluster[0])
                new_cluster_num.remove(i)
                break

        #delete them:
        
        for concept in redundant_concept:
            cluster_map=cluster_map.drop(cluster_map[cluster_map.concept_code==concept].index)

        #get all the parents

        parent_dic[i]={}
        cluster=cluster_map[cluster_map['cluster']==i]['concept_code']

        for code in cluster:
            parent_dic[i][code]=[]
            parents=c2p[code]
            for parent in parents:
                get_all_the_parent(code,parent,c2p,parent_dic[i])
  
    return new_cluster_num,parent_dic,cluster_map


def build_snomed_hierarchy_four_layer_tree(cluster_map,curs,top_level,p2c,new_cluster_num,parent_dic):

    G = nx.DiGraph()
    for top_code in top_level:
        add_snomed_node_for_DAG_graph(top_code,'snomed',G,curs,p2c)
    
    #build the graph:
    snomed_hierarchy={'name':'snomed','children':[]}
    
    print("name tag and build the tree")
    for i in new_cluster_num:
        # judge whether have common parents:
        cluster=cluster_map[cluster_map['cluster']==i]['concept_code'].tolist()
        parent_name=check_common_parents(cluster,parent_dic[i],curs,G)

        if parent_name=="":
             # four layer:
            dic={}
            top_concept=[]
            for code in cluster:
                tc=code2topconcept(code,curs)
                if tc not in dic:
                    dic[tc]=[code]
                    top_concept.append(tc)
                else:
                    dic[tc].append(code)
            
           
            node_2thlayer=dict(name="&".join(top_concept),children=[])
            snomed_hierarchy['children'].append(node_2thlayer)
            
                    
            for key,value in dic.items():
                # check names of this layer:
                parent_name=key
                if len(value)>=2:
                    name=check_common_parents(value,parent_dic[i],curs,G)
                    if name!="":
                        parent_name=name
                else:
                    parent_name=code2string(value[0],curs)
                node_3thlayer=dict(name=parent_name,children=[])
                node_2thlayer['children'].append(node_3thlayer)
                for children in value:
                    node_4thlayer=dict(name=code2string(children,curs),children=[])
                    node_3thlayer['children'].append(node_4thlayer)
        else:
            # three layer
           

            node_2thlayer=dict(name=parent_name,children=[])
            snomed_hierarchy['children'].append(node_2thlayer)
            for concept in cluster_map[cluster_map['cluster']==i]['concept_name']:
                node_3thlayer=dict(name=concept,children=[])
                node_2thlayer['children'].append(node_3thlayer)    

    json.dump(snomed_hierarchy, open(os.path.join("static","data","snomed_hierarchy_four_layer_tree.json"), "w"))




#helper funtions for builiding trees and dags
def check_common_parents(cluster,parent_dic,curs,G):
   
    common_parent=parent_dic[cluster[0]]
    parent_name=""
    for code in cluster[1:]:
        parent_cluster=parent_dic[code]
        discard_parent=[]
        for parent in common_parent:
            if parent not in parent_cluster:
                discard_parent.append(parent)
        for each in discard_parent:
            common_parent.remove(each)
        if len(common_parent)==0:
            break
            
    if len(common_parent)==1:
    
    #get the deepest parent:
        parent_name=code2string(common_parent[0],curs)

    elif len(common_parent)>1:
        parent_name=code2string(common_parent[0],curs)
        if parent_name in G.node:
            depth=G.node[parent_name]['depth']
        else:
            depth=0
        for each in common_parent[1:]:
            name=code2string(each,curs)
            if name in G.node:
                new_depth=G.node[name]['depth']
                if new_depth>depth:
                    parent_name=name
                    depth=new_depth
    return parent_name

def create_p2c_and_c2p(snomed_codes,top_level,p2c,c2p,curs):
    for code in snomed_codes:
        find_parent(p2c,c2p,code,curs,top_level)
    #build_json_file:
    json.dump(p2c, open(os.path.join("static","data","p2c.json"), "w"))
    json.dump(c2p, open(os.path.join("static","data","c2p.json"),"w"))


def get_all_the_children(concept,node,p2c,node_dic):
    if node not in node_dic[concept]:
        node_dic[concept].append(node)

        if node in p2c.keys():
            childrens=p2c[node]
            for children in childrens:
                
                get_all_the_children(concept,children,p2c,node_dic)

def get_all_the_parent(concept,node,c2p,node_dic):
    if node not in node_dic[concept]:
        node_dic[concept].append(node)

        if node in c2p.keys():
            parents=c2p[node]
            for parent in parents:
        
                get_all_the_parent(concept,parent,c2p,node_dic)


def get_all_the_children_concept(top_concept,node,p2c,snomed_codes,node_dic):
    if node not in node_dic[top_concept]:
        if node in snomed_codes:
            node_dic[top_concept].append(node)

        if node in p2c.keys():
            childrens=p2c[node]
            for children in childrens:
        
                get_all_the_children_concept(top_concept,children,p2c,snomed_codes,node_dic)


def code2string(code,curs):
    sql_str="select * from concept where concept.concept_code='"+str(code)+"'"
    curs.execute(sql_str)
    result = curs.fetchall()
    if len(result)!=0:
        concept=result[0][1]
        if re.search('/',concept) or re.search('-',concept) or re.search('\'',concept) or re.search(',',concept):
            concept=concept.replace('/','_or_')
            concept=concept.replace('-','_')
            concept=concept.replace('\'','')
            concept=concept.replace(',','_')
        concept=concept.replace(' ','_')
        return concept
    else:
        return ""

def code2topconcept(code,curs):
    sql_str="select * from concept where concept.concept_code='"+code+"'"
    curs.execute(sql_str)
    result = curs.fetchall()
    if len(result)!=0:
        concept=result[0][4]
        if re.search('/',concept) or re.search('-',concept) or re.search('\'',concept) or re.search(',',concept):
            concept=concept.replace('/','_or_')
            concept=concept.replace('-','_')
            concept=concept.replace('\'','')
            concept=concept.replace(',','_')
            concept=concept.replace(' ','_')
            concept=concept.replace(' ','_')
        return concept

def find_parent(p2c,c2p,code,curs,top_level):
    sql_str="select * from concept c1 join concept_relationship cr on c1.concept_id=cr.concept_id_1 join concept c2 on c2.concept_id=cr.concept_id_2 where c1.concept_code='"+code+"' and c1.vocabulary_id='SNOMED' and cr.relationship_id='Is a'"
    curs.execute(sql_str)
    result = curs.fetchall()
    if len(result)!=0:
        for parent in result:
            if parent[-4] in ["123037004","404684003", "243796009","308916002","272379006","363787002","410607006","373873005","78621006","260787004","362981000", "363787002", "48176007","370115009","71388002","105590001","900000000000441003"]:
                if parent[-4] not in top_level:
                    top_level.append(parent[-4])
            
            if parent[-4]!='138875005': 
                if parent[-4] not in p2c.keys():
                    p2c[parent[-4]]=[code]
                elif code not in p2c[parent[-4]]:
                    p2c[parent[-4]].append(code)

                
                if code not in c2p:
                    c2p[code]=[parent[-4]]
                elif parent[-4] not in c2p[code]:
                    c2p[code].append(parent[-4])
                find_parent(p2c,c2p,parent[-4],curs,top_level)






def add_snomed_node_for_dag_non_color(node,parent,file,curs,p2c,edge_dic,tagged_nodes):
    
    children_concept=code2string(node,curs)
    if node not in tagged_nodes:
        file.write(node+'[label="'+children_concept+'"];\n')
        tagged_nodes[node]=1
    if children_concept !="":
        edge=parent+node
        if edge not in edge_dic.keys():
            file.write(parent+'->'+node+';\n')
            edge_dic[edge]=1
            if node in p2c.keys():
                childrens=p2c[node]
                for children in childrens:
                    add_snomed_node_for_dag_non_color(children,node,file,curs,p2c,edge_dic,tagged_nodes)




# helper function for nx graph:
def add_snomed_node_for_DAG_graph(node,parent,G,curs,p2c):
    concept=code2string(node,curs)
    if concept !="":
        if concept not in G.node:
            G.add_edge(parent,concept)
            G.node[concept]['depth']=nx.dijkstra_path_length(G,'snomed', concept)
            if node in p2c.keys():
                childrens=p2c[node]
                for children in childrens:
                    add_snomed_node_for_DAG_graph(children,concept,G,curs,p2c)
        else:
            G.add_edge(parent,concept)
            current_distance=nx.dijkstra_path_length(G,'snomed', concept)
            if G.node[concept]['depth']>current_distance:
                G.node[concept]['depth']=current_distance
                if node in p2c.keys():
                    childrens=p2c[node]
                    for children in childrens:
                        add_snomed_node_for_DAG_graph(children,concept,G,curs,p2c)



 


 # embedding building fuctions   
def cui_embedding():

    embeddings_dict=pd.read_csv(os.path.join("word-embedding","cui2vec_pretrained.csv"),index_col=[0])
    return embeddings_dict

def snomed_embedding():
    embeddings_dict={}
    with open(os.path.join("word-embedding","SNOMEDCT_isa.txt.emb_dims_200.nthreads_1.txt"), 'r', encoding="utf-8") as f:
        for line in f:
            values = line.split()
            word = values[0]
            vector = np.asarray(values[1:], "float32")
            embeddings_dict[word] = vector

    return embeddings_dict

def cooccurence_analysis_from_pretrained_embedding(concepts):
    doc2con = {}
    set_word=[]
    concept2id={}
    cui2word={}
    i=0
    model=snomed_embedding()
    X = np.zeros(shape=(1,200))
    
    for c in concepts.values():
        if list(c.mentions)[0] not in set_word:
            snomed_codes=list(c.snomed_codes)
            for snomed_code in snomed_codes:
                if snomed_code in model.keys():
                    X=np.concatenate((X,model[snomed_code].reshape(1,200)),axis=0) 

                    for pmid in c.pmids:
                        if pmid not in doc2con:
                            doc2con[pmid] = [c.cui]
                        else:
                            doc2con[pmid].append(c.cui)

                    set_word.append(list(c.mentions)[0])
                    cui2word[c.cui]=list(c.mentions)[0]
                    break
        
    X=np.delete(X,0,axis=0)
    if(len(X)!=0):
        cluster_num=int(len(set_word)/7)+1
        print('cluster num: ', cluster_num)
        kmeans = KMeans(n_clusters=cluster_num, init='k-means++', max_iter=800, n_init=10, random_state=0)
        clustering_result = kmeans.fit(X)
         # l2c: label to concepts
        l2c = {}
        for i, label in enumerate(clustering_result.labels_):
            if label not in l2c:
                l2c[label] = []
            l2c[label].append(set_word[i])
    
    reordered_set_word=[]
    i=1
   

    for label,words in l2c.items():      
        reordered_set_word=reordered_set_word+words
        for word in words:
            concept2id[word]=i
            i+=1
     

        
               
    # count co-occurrences
    cooc = {}
    for docid, cons in doc2con.items():
        for i in range(len(cons)):
            for j in range(i + 1, len(cons)):
                if cons[i] != cons[j]:
                    pair = tuple(sorted( (cons[i], cons[j]) ))
                    if pair not in cooc:
                        cooc[pair] = 1
                    else:
                        cooc[pair] += 1
    vab=len(set_word)
    matrix = [[0 for j in range(vab+1)] for i in range(vab+1)]  # 初始化矩阵
    matrix[0][1:] = np.array(reordered_set_word)
    matrix = list(map(list, zip(*matrix)))
    matrix[0][1:] = np.array(reordered_set_word)  # 赋值矩阵的第一行与第一列
    

    for pair, count in cooc.items():
        c1, c2 = pair
        n1=concept2id[cui2word[c1]]
        n2=concept2id[cui2word[c2]]
        matrix[n2][n1]=count
        matrix[n1][n2]=count
    
    data = pd.DataFrame(matrix)



    data.to_csv('coccurence_order_by_contextual_embedding.csv', index=0, columns=None, encoding='utf_8_sig')

def cooccurence_analysis_from_clustering_each_row(concepts):
    doc2con = {}
    set_word=[]
    concept2id={}
    cui2word={}
    i=0
    model=snomed_embedding()
    
    for c in concepts.values():
        if list(c.mentions)[0] not in set_word:
            snomed_codes=list(c.snomed_codes)
            for snomed_code in snomed_codes:
                if snomed_code in model.keys():
                    for pmid in c.pmids:
                        if pmid not in doc2con:
                            doc2con[pmid] = [c.cui]
                        else:
                            doc2con[pmid].append(c.cui)

                    set_word.append(list(c.mentions)[0])
                    cui2word[c.cui]=list(c.mentions)[0]
                    break
               
    # count co-occurrences
    cooc = {}
    for docid, cons in doc2con.items():
        for i in range(len(cons)):
            for j in range(i + 1, len(cons)):
                if cons[i] != cons[j]:
                    pair = tuple(sorted( (cons[i], cons[j]) ))
                    if pair not in cooc:
                        cooc[pair] = 1
                    else:
                        cooc[pair] += 1
     

    vab=len(set_word)
    matrix = [[0 for j in range(vab+1)] for i in range(vab+1)]  # 初始化矩阵
    matrix[0][1:] = np.array(set_word)
    matrix = list(map(list, zip(*matrix)))
    matrix[0][1:] = np.array(set_word)  # 赋值矩阵的第一行与第一列
    

    i=1
    for word in set_word:
        concept2id[word]=i
        i+=1
    


    for pair, count in cooc.items():
        c1, c2 = pair
        n1=concept2id[cui2word[c1]]
        n2=concept2id[cui2word[c2]]
        matrix[n2][n1]=count
        matrix[n1][n2]=count
  
    cluster_num=int(len(set_word)/4)
    kmeans = KMeans(n_clusters=cluster_num, init='k-means++', max_iter=800, n_init=10, random_state=0)
    X = np.zeros(shape=(1,vab))
    for i in range(len(matrix)-1): 
        X=np.concatenate((X,np.array(matrix[i+1][1:]).reshape(1,vab)),axis=0) 
    X=np.delete(X,0,axis=0)

    clustering_result = kmeans.fit(X)
     # l2c: label to concepts
    l2c = {}
    for i, label in enumerate(clustering_result.labels_):
        if label not in l2c:
            l2c[label] = []
        l2c[label].append(set_word[i])
    
    reordered_set_word=[]
    i=1
    for label,words in l2c.items():
        reordered_set_word=reordered_set_word+words
        for word in words:
            concept2id[word]=i
            i+=1

    matrix = [['' for j in range(vab+1)] for i in range(vab+1)]  # 初始化矩阵
    matrix[0][1:] = np.array(reordered_set_word)
    matrix = list(map(list, zip(*matrix)))
    matrix[0][1:] = np.array(reordered_set_word)  # 赋值矩阵的第一行与第一列
    
    for pair, count in cooc.items():
        c1, c2 = pair
        n1=concept2id[cui2word[c1]]
        n2=concept2id[cui2word[c2]]
        matrix[n2][n1]=count
        matrix[n1][n2]=count
    
    data = pd.DataFrame(matrix)



    data.to_csv('coccurence.csv', index=0, columns=None, encoding='utf_8_sig')
    edge=vab+1
    # concept for each document
    matrix2 = [['' for j in range(edge)] for i in range(101)]
    matrix2[0][1:] = np.array(reordered_set_word)
    num=1
    global_occur={}
    for docid, cons in doc2con.items():
        matrix2[num][0]=docid
        occur={}
        for con in cons:
            if con not in occur:
                occur[con] = 1
            else:
                occur[con] += 1
            for concept, count in occur.items():
                matrix2[num][concept2id[cui2word[concept]]]=count
        num+=1

        for con in cons:
            if con not in global_occur:
                global_occur[con] = 1
            else:
                global_occur[con] += 1
    # concept and frequency 
    matrix3 = [['' for j in range(2)] for i in range(len(reordered_set_word)+1)]
    matrix3[0][:]=["concepts","frequency"]
    num=1
   
    for concept, count in global_occur.items():
        matrix3[num][0]=cui2word[concept]
        matrix3[num][1]=count
        num+=1
    
   

    data2 = pd.DataFrame(matrix2)
    data2.to_csv('data_2.csv', index=0, columns=None, encoding='utf_8_sig')    

    data3 = pd.DataFrame(matrix3)
    data3.to_csv('data_3.csv', index=0, columns=None, encoding='utf_8_sig')    

    with open("cluster result","w") as f:
        for label,words in l2c.items():
            f.write("clulster num: "+str(label)+'\n')
            for word in words:
                f.write(word+"\n")
            f.write("\n")

