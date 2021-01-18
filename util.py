def build_snomed_hierarchy_four_layer_tree(cluster_map,model,snomed_codes,top_level,curs,p2c,c2p):
    
    print("calculate depth")
    G = nx.DiGraph()
    for top_code in top_level:
        add_snomed_node_for_DAG_graph(top_code,'snomed',G,curs,p2c)
    
    
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
    
    json.dump(children_dic, open(os.path.join("static","data","children_dic.json"), "w"))
    json.dump(parent_dic, open(os.path.join("static","data","parent_dic.json"), "w"))
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


# three-layer-tree
def build_snomed_hierarchy_three_layer_tree(snomed_codes,curs,p2c):
    
    node_dic={}
    for code in snomed_codes:
        concept=code2string(code,curs)
        top_concept=code2topconcept(code,curs)
        if concept !="":
            if top_concept not in node_dic:
                node_dic[top_concept]=[concept]
            elif concept not in node_dic[top_concept]:
                node_dic[top_concept].append(concept)

    snomed_hierarchy={'name':'snomed','children':[]}
    for key,value in node_dic.items():
        node_2thlayer=dict(name=key,children=[])
        snomed_hierarchy['children'].append(node_2thlayer)
        for each in value:
            node_3rdlayer=dict(name=each,children=[])
            node_2thlayer['children'].append(node_3rdlayer)

    json.dump(snomed_hierarchy, open(".\\static\\data\\snomed_hierarchy_three_layer_tree.json", "w"))


# first version four layer tree- seperate 
def build_snomed_hierarchy_four_layer_tree_no_name(snomed_codes,top_level,curs,p2c):
    #check the number of independent cluster:
    # find cluster
    cluster_dic={}
    model=snomed_embedding()
    node_dic={}
    for top_code in top_level:
        node_dic[top_code]=[]
        childrens=p2c[top_code]
        for children in childrens:
            get_all_the_children_concept(top_code,children,p2c,snomed_codes,node_dic)
    snomed_hierarchy={'name':'snomed','children':[]}

    for key, value in node_dic.items():
        top_concept=code2string(key,curs)
        X = np.zeros(shape=(1,200))
        snomed_vector={}
        label_list=[]
        for code in value:
            concept =code2string(code,curs)
            if concept !="" and code in model.keys():
                label_list.append(concept)
                X=np.concatenate((X,model[code].reshape(1,200)),axis=0) 
        
        X=np.delete(X,0,axis=0)
        if(len(X)!=0):
            cluster_num=int(len(value)/3)+1
            kmeans = KMeans(n_clusters=cluster_num, init='k-means++', max_iter=300, n_init=10, random_state=0)
            pred_y = kmeans.fit_predict(X)

            cluster_map = pd.DataFrame()
            cluster_map['concept_name'] = label_list
            cluster_map['cluster'] = kmeans.labels_
       
            node_2thlayer=dict(name=top_concept,children=[])
            snomed_hierarchy['children'].append(node_2thlayer)
            for i in range(cluster_num):
                node_3thlayer=dict(name="",children=[])
                node_2thlayer['children'].append(node_3thlayer)
                for each in cluster_map[cluster_map.cluster == i]['concept_name']:
                    node_4rdlayer=dict(name=each,children=[])
                    node_3thlayer['children'].append(node_4rdlayer)
            cluster_dic[top_concept]=cluster_map
    json.dump(snomed_hierarchy, open(".\\static\\data\\snomed_hierarchy_four_layer_tree.json", "w"))

    return cluster_dic


    # three-layer-tree
def build_snomed_hierarchy_three_layer_tree(snomed_codes,curs,p2c):
    
    node_dic={}
    for code in snomed_codes:
        concept=code2string(code,curs)
        top_concept=code2topconcept(code,curs)
        if concept !="":
            if top_concept not in node_dic:
                node_dic[top_concept]=[concept]
            elif concept not in node_dic[top_concept]:
                node_dic[top_concept].append(concept)

    snomed_hierarchy={'name':'snomed','children':[]}
    for key,value in node_dic.items():
        node_2thlayer=dict(name=key,children=[])
        snomed_hierarchy['children'].append(node_2thlayer)
        for each in value:
            node_3rdlayer=dict(name=each,children=[])
            node_2thlayer['children'].append(node_3rdlayer)

    json.dump(snomed_hierarchy, open(".\\static\\data\\snomed_hierarchy_three_layer_tree.json", "w"))

    # the original dag
def build_snomed_hierarchy_dag(snomed_codes,top_level,curs,p2c):
    
    edge={}
    tagged_nodes={}
    with open(".\\static\\data\\DAG\\dag.dot", "w") as file:
        file.write('digraph g {'+'\n')
        for top_code in top_level:
            add_snomed_node_for_dag(top_code,'snomed',file,curs,p2c,edge,snomed_codes,tagged_nodes)
        file.write('}')
    
    #json.dump(edge, open(".\\static\\data\\edge.json", "w"))

def build_snomed_hierarchy_tree(snomed_codes,top_level,curs,p2c):
    
    snomed_hierarchy={'name':'snomed','children':[]}
    for top_code in top_level:
        add_snomed_node(top_code,snomed_hierarchy,curs,p2c)

        
    json.dump(snomed_hierarchy, open(".\\static\\data\\snomed_hierarchy.json", "w"))


    def add_snomed_node_for_dag_three_layers(top_concept,node,file,curs,p2c,snomed_codes,node_dic):
    if node not in node_dic.keys():
        concept=code2string(node,curs)
        if concept !='':
            if node in snomed_codes:
                concept=code2string(node,curs)
                file.write(top_concept+'->'+concept+';\n')
                node_dic[node]=1

            if node in p2c.keys():
                childrens=p2c[node]
                for children in childrens:
                    add_snomed_node_for_dag_three_layers(top_concept,children,file,curs,p2c,snomed_codes,node_dic)


'''
three layer built using dot

def build_snomed_hierarchy_three_layer_dag(snomed_codes,top_level,curs,p2c):
    node_dic={}
    with open(".\\static\\data\\dag_three_layers.dot", "w") as file:
        file.write('digraph g {'+'\n')
        for top_code in top_level:
            concept=code2string(top_code,curs)
            file.write('snomed->'+concept+';\n')
            childrens=p2c[top_code]
            for children in childrens:
                add_snomed_node_for_dag_three_layers(concept,children,file,curs,p2c,snomed_codes,node_dic)

        file.write('}')

def add_snomed_node_for_dag_three_layers(top_concept,node,file,curs,p2c,snomed_codes,node_dic):
    if node not in node_dic.keys():
        concept=code2string(node,curs)
        if concept !='':
            if node in snomed_codes:
                concept=code2string(node,curs)
                file.write(top_concept+'->'+concept+';\n')
                node_dic[node]=1

            if node in p2c.keys():
                childrens=p2c[node]
                for children in childrens:
                    add_snomed_node_for_dag_three_layers(top_concept,children,file,curs,p2c,snomed_codes,node_dic)

#dag 0
def build_clinical_finding_cluster_dag(snomed_codes,cluster_dic,curs,p2c):
    edge={}
    tagged_nodes={}
    color=['red','blue','orange','green','yellow','gray']
    with open(".\\static\\data\\DAG\\dag_clinical_finding.dot", "w") as file:
        file.write('digraph g {'+'\n')
        add_snomed_node_for_dag_non_color('404684003','snomed',file,curs,p2c,edge,snomed_codes,tagged_nodes)
        #color cluster
        top_concept=code2string('404684003',curs)
        cluster_map=cluster_dic[top_concept]
        
        for each in cluster_map.itertuples():
            concept=each[1]
            cluster=each[2]
            file.write(concept+' [style=filled, fillcolor='+color[cluster]+'];\n')


        file.write('}')
# dag 1
def build_substance_pharmecutical_dag(snomed_codes,cluster_dic,curs,p2c):
    edge={}
    tagged_nodes={}
    color=['aliceblue','antiquewhite','cyan', 'aquamarine','springgreen' ,'turquoise','violet','yellow','yellowgreen','tomato','darkorange','darkorchid','maroon','darksalmon','darkseagreen','darkslateblue','darkslategray','green','greenyellow','skyblue','goldenrod','lightslategray','mediumblue','royalblue','red','mediumvioletred']
    with open(".\\static\\data\\DAG\\substance_pharmaceutical.dot", "w") as file:
        file.write('digraph g {'+'\n')
        for top_code in ['105590001','373873005']:
            add_snomed_node_for_dag_non_color(top_code,'snomed',file,curs,p2c,edge,snomed_codes,tagged_nodes)
       
        
        node_dic={}
        for top_code in ['105590001','373873005']:
            node_dic[top_code]=[]
            childrens=p2c[top_code]
            for children in childrens:
                get_all_the_children_concept(top_code,children,p2c,snomed_codes,node_dic)

        model=snomed_embedding()
        X = np.zeros(shape=(1,200))
        label_list=[]
        for key, value in node_dic.items():
            for code in value:
                concept =code2string(code,curs)
                if concept !="" and code in model.keys():
                    label_list.append(concept)
                    X=np.concatenate((X,model[code].reshape(1,200)),axis=0) 
        X=np.delete(X,0,axis=0)
        if(len(X)!=0):
            cluster_num=int(len(label_list)/3)+1
            kmeans = KMeans(n_clusters=cluster_num, init='k-means++', max_iter=300, n_init=10, random_state=0)
            pred_y = kmeans.fit_predict(X)

            cluster_map = pd.DataFrame()
            cluster_map['concept_name'] = label_list
            cluster_map['cluster'] = kmeans.labels_
            #color cluster
            
        for each in cluster_map.itertuples():
            concept=each[1]
            cluster=each[2]
            file.write(concept+' [style=filled, fillcolor='+color[cluster]+'];\n')


        file.write('}')
# dag 2
'''
def word2aui(word):
    #word2sui={}
    #for word in words:
        #better use API?
    f = open("MRCONSO.RRF",'rb')
    aui_index={}
    for line in f.readlines():
        line=str(line)
        content = re.compile("^b'(.*)'$", re.S)
        content=re.findall(content, line)
        if (content==[]):
            content = re.compile('^b\"(.*)\"$', re.S)
            content=re.findall(content, line)
        content=content[0].strip('\\n')
        content=content.split('|')
        string=content[14].lower()
        if re.search(word,string):
            aui_index[content[7]]={}
            aui_index[content[7]]['CUI']=content[0]
            aui_index[content[7]]['LAT']=content[1]
            aui_index[content[7]]['TS']=content[2]
            aui_index[content[7]]['LUI']=content[3]
            aui_index[content[7]]['STT']=content[4]
            aui_index[content[7]]['SUI']=content[5]
            aui_index[content[7]]['ISPREF']=content[6]
            aui_index[content[7]]['SAUI']=content[8]
            aui_index[content[7]]['SCUI']=content[9]
            aui_index[content[7]]['SDUI']=content[10]
            aui_index[content[7]]['SAB']=content[11]
            aui_index[content[7]]['TTY']=content[12]
            aui_index[content[7]]['CODE']=content[13]
            aui_index[content[7]]['STR']=content[14]
            aui_index[content[7]]['SRL']=content[15]
            aui_index[content[7]]['SUPPRESS']=content[16]
            aui_index[content[7]]['CVF']=content[17]
    return aui_index
    
def sui2cui(aui_index):
    sui2cui={}
    for item in aui_index.values():
        if item['SUI']+' '+item['STR'] not in sui2cui.keys():
            
            sui2cui[item['SUI']+' '+item['STR']]=[item['CUI']]
        else:
            sui2cui[item['SUI']+' '+item['STR']].append(item['CUI'])
    return sui2cui


 def add_node(node, parent ):

    # First create the new node and append it to its parent's children
    newNode = dict( node_id=node.id, children=[] )
    parent["children"].append( newNode )

    # Recursively add the current node's children
    if node.left: add_node( node.left, newNode )
    if node.right: add_node( node.right, newNode )

def label_tree( n ,id2name):
    # If the node is a leaf, then we have its name
    if len(n["children"]) == 0:
        n["name"] = id2name[n["node_id"]] 
    if len(n["children"])==1:
        label_tree(n["children"][0],id2name)
        n["name"] = ""
    if len(n["children"])==2:
        label_tree(n["children"][0],id2name)
        label_tree(n["children"][1],id2name)
        n["name"] = ""

    
    # If not, flatten all the leaves in the node's subtree
    #else:
    #    leafNames = reduce(lambda ls, c: ls + label_tree(c,id2name), n["children"], [])

    # Delete the node id since we don't need it anymore and
    # it makes for cleaner JSON
    del n["node_id"]

    # Labeling convention: "-"-separated leaf names
    #n["name"] = name = "-".join(sorted(map(str, leafNames)))
    
 def add_snomed_node_for_dag(node,parent,file,curs,p2c,edge_dic,snomed_codes,tagged_nodes):
    
    concept=code2string(node,curs)
    if concept !="":
        edge=parent+concept
        if edge not in edge_dic.keys():
            file.write(parent+'->'+concept+';\n')
            if node in snomed_codes and node not in tagged_nodes.keys():
                file.write(concept+' [style=filled, fillcolor=green];\n')
                tagged_nodes[node]=1
            edge_dic[edge]=1
            if node in p2c.keys():
                childrens=p2c[node]
                for children in childrens:
                    add_snomed_node_for_dag(children,concept,file,curs,p2c,edge_dic,snomed_codes,tagged_nodes)


                    def add_snomed_node(node,parent,curs,p2c):
    concept=code2string(node,curs)
    if concept !="" :
        newNode=dict(name=concept,children=[])
        parent["children"].append(newNode)
        if node in p2c.keys():
            childrens=p2c[node]
            for children in childrens:
                add_snomed_node(children,newNode,curs,p2c)

                def snomed_collocation(parsed_result,curs):
    '''
    word_frequency={}
    collocation_frequency={}
   
    for i in range(len(parsed_result['docs'])):
        for j in range(len(parsed_result['docs'][i]['code'])):
            cui_1=parsed_result['docs'][i]['code'][j]
            # calculate word frequency
            if (cui_1 not in word_frequency.keys()):
                word_frequency[cui_1]=1
            else:
                word_frequency[cui_1]+=1
            # calculate collocation frequency
            for cui_2 in parsed_result['docs'][i]['code'][j+1:]:
                if (cui_1,cui_2) in collocation_frequency.keys():
                    collocation_frequency[(cui_1,cui_2)]+=1
                elif (cui_2,cui_1) in collocation_frequency.keys():
                    collocation_frequency[(cui_2,cui_1)]+=1
                else:
                    collocation_frequency[(cui_1,cui_2)]=1
    #calculate PMI:
    PMI={}

    for key,value in collocation_frequency.items():
        print(key)
        '''
    model=snomed_embedding()
    label_list=[]
    lacked_label_list=[]
    matrix = np.zeros(shape=(1,200))
    snomed_vector={}
    snomed_codes=[]
   
    for i in range(len(parsed_result['docs'])):
        print("process {} documents".format(i))
      
        for snomed_code in parsed_result['docs'][i]['code']:
            concept=code2string(snomed_code,curs)
            if concept !="" :
                if snomed_code not in snomed_codes:
                    snomed_codes.append(snomed_code)

                if concept not in snomed_vector.keys():
                    if snomed_code in model.keys():
                        snomed_vector[concept]=model[snomed_code].reshape(1,200) 
                    elif snomed_code not in lacked_label_list:
                        lacked_label_list.append(snomed_code)

    for key,value in snomed_vector.items():
        label_list.append(key)
        matrix=np.concatenate((matrix,value),axis=0)

    matrix=np.delete(matrix,0,axis=0)
    clusters = linkage(matrix, 'single')
    #dendrogram(linked,orientation='top',labels=label_list,distance_sort='ascending', orientation = 'right')
   
    T = to_tree( clusters , rd=False )
    d3Dendro = dict(children=[], name="cui-code")
    add_node( T, d3Dendro ) 
    id2name = dict(zip(range(len(label_list)), label_list)) 

    label_tree( d3Dendro["children"][0], id2name)

    # Output to JSON
    json.dump(d3Dendro, open(".\\static\\data\\snomed_cluster.json", "w"), sort_keys=True, indent=4)

    return snomed_codes

    def cui_collocation(parsed_result):
    model=cui_embedding()
    label_list=[]
    lacked_label_list=[]
    matrix = np.zeros(shape=(1,500))
    API_KEY="35320203-e665-46d7-b21f-0c1fa1260f22"
    result=requests.post("https://utslogin.nlm.nih.gov/cas/v1/api-key",{'apikey':API_KEY}).text
    soup=Soup(result)
    TGT_KEY=soup.form['action']
    cui_vector={}
    for i in range(len(parsed_result['docs'])):
        print("process {} documents".format(i))
      
        for cui in parsed_result['docs'][i]['cui']:
            concept=cui2word(cui,TGT_KEY)
            if concept not in cui_vector.keys():
                if cui in model.index:
                    cui_vector[concept]=model.loc[cui].as_matrix().reshape(1,500) 
                elif cui not in lacked_label_list:
                    lacked_label_list.append(cui)

    for key,value in cui_vector.items():
        label_list.append(key)
        matrix=np.concatenate((matrix,value),axis=0)

    matrix=np.delete(matrix,0,axis=0)
    clusters = linkage(matrix, 'single')
    #dendrogram(linked,orientation='top',labels=label_list,distance_sort='ascending', orientation = 'right')
    T = to_tree( clusters , rd=False )
    d3Dendro = dict(children=[], name="cui-code")
    add_node( T, d3Dendro ) 
    id2name = dict(zip(range(len(label_list)), label_list)) 

    label_tree( d3Dendro["children"][0], id2name)

    # Output to JSON
    json.dump(d3Dendro, open(".\\static\\data\\d3-dendrogram.json", "w"), sort_keys=True, indent=4)



def snomed_collocation(parsed_result,curs):
    
    model=snomed_embedding()
    label_list=[]
    lacked_label_list=[]
    matrix = np.zeros(shape=(1,200))
    snomed_vector={}
    snomed_codes=[]
   
    for i in range(len(parsed_result['docs'])):
        print("process {} documents".format(i))
      
        for snomed_code in parsed_result['docs'][i]['code']:
            concept=code2string(snomed_code,curs)
            if concept !="" :
                if snomed_code not in snomed_codes:
                    snomed_codes.append(snomed_code)

                if concept not in snomed_vector.keys():
                    if snomed_code in model.keys():
                        snomed_vector[concept]=model[snomed_code].reshape(1,200) 
                    elif snomed_code not in lacked_label_list:
                        lacked_label_list.append(snomed_code)

    for key,value in snomed_vector.items():
        label_list.append(key)
        matrix=np.concatenate((matrix,value),axis=0)

    matrix=np.delete(matrix,0,axis=0)
    clusters = linkage(matrix, 'single')
    #dendrogram(linked,orientation='top',labels=label_list,distance_sort='ascending', orientation = 'right')
   
    T = to_tree( clusters , rd=False )
    d3Dendro = dict(children=[], name="cui-code")
    add_node( T, d3Dendro ) 
    id2name = dict(zip(range(len(label_list)), label_list)) 

    label_tree( d3Dendro["children"][0], id2name)

    # Output to JSON
    json.dump(d3Dendro, open(".\\static\\data\\snomed_cluster.json", "w"), sort_keys=True, indent=4)

    return snomed_codes

def get_all_the_children_concept(top_concept,node,p2c,snomed_codes,node_dic):
    if node not in node_dic[top_concept]:
        if node in snomed_codes:
            node_dic[top_concept].append(node)

        if node in p2c.keys():
            childrens=p2c[node]
            for children in childrens:
        
                get_all_the_children_concept(top_concept,children,p2c,snomed_codes,node_dic)

 # helper function for connecting umls:
def cui2word(cui,TGT_KEY):
    SERVIE_TICKET=requests.post(TGT_KEY,{'service':"http://umlsks.nlm.nih.gov"})
    url="https://uts-ws.nlm.nih.gov/rest/content/current/CUI/"+cui
    r = requests.get(url,{'ticket':SERVIE_TICKET})
    
    return r.json()["result"]["name"]


     path_c2p=os.path.join("visualization","static","data","c2p.json")
    path_p2c=os.path.join("visualization","static","data","p2c.json")
    if os.path.exist(path_c2p)==True and os.path.exist(path_p2c)==True :
        p2c=json.load(open(path_p2c,'rb'))
        c2p=json.load(open(path_c2p,'rb'))
    else:
        create_p2c_and_c2p(snomed_codes,top_level,p2c,c2p,curs)