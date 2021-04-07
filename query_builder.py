# This module takes an information focus object and turn it into a Lucene/Solr
# query string

# below are a few tutorials
# https://lucene.apache.org/solr/guide/8_4/query-syntax-and-parsing.html
# https://lucene.apache.org/solr/guide/8_4/the-standard-query-parser.html
# http://yonik.com/solr/query-syntax/


# we need to perform query expansion at some point

# this is the main function



import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import globalvar as gl
import json
'''
from query_expansion import create_synonyms
from query_expansion import create_negtive_string
from query_expansion import create_positive_string
def solr_query_builder(info_focus_dict):
    query_parts = []
    key_terms=[]
    for concept in info_focus_dict['event']:
        # print (concept)
        term = concept['name']
        weight = float(concept['importance'])

        synonyms=create_synonyms(term)
        for syn in synonyms:
            key_terms.append(syn)
        key_terms.append(term)

        if (weight==0):
            neg_syn_string=create_negtive_string(term,synonyms)
            query_parts.append(neg_syn_string)
        else:
            pos_syn_string=create_positive_string(term,synonyms,weight)
            query_parts.append(pos_syn_string)
 
    query_string = ' AND '.join(query_parts)

    return query_string,set(key_terms)
'''
def load_stopwords():
    stopword=set()
    with open('./stopwords.txt') as f:
      for word in f.readlines():
          word=word.strip('\n')
          stopword.add(word)
    return stopword



def solr_query_builder(info_focus_dict):
    gl._init(load_stopwords(),"_stopwords")
    selfdefined_stopwords=gl.get_value("_stopwords")
    porter = PorterStemmer()
    '''
    with open('./stp.txt', 'w') as f:
        for w in selfdefined_stopwords:
            f.write(w)
            f.write('\n')
            
    with open('./foucs.json', 'w') as f:
        json.dump(info_focus_dict, f)   
        '''
    query_parts = []
    key_terms=[]
    pattern = re.compile(r'(?:\d|[a-zA-Z])\.\s([a-zA-Z].*)')
    query_dic={}
    for concept in info_focus_dict['event']:
        term = concept['name']
        weight = format(float(concept['importance']), '.2f')
        match=pattern.search(term)  
        if match:
            term=match.group(1)
        parts=term.split(",")
        for part in parts:
            minimals=part.split(" ")
            for minimal in minimals:
                add_to_query_dic(query_dic,minimal,weight,stopwords,selfdefined_stopwords)
    '''      
    with open('./query.json', 'w') as f:
        json.dump(query_dic, f)    
    '''     
    for key, value in query_dic.items():
        query_parts.append('abstract:'+key+ '^' + str(value))
        query_parts.append('title:' + key+ '^' + str(value))
        key_terms.append(term)
 
    query_string = ' '.join(query_parts)
    # print(query_string)

    return query_string,set(key_terms)


def add_to_query_dic( query_dic,term,weight,stopwords,self_defined_stopwords):
    term=term.lower().strip("[]()-")
    if term !="" and term not in stopwords.words('english') and term not in self_defined_stopwords :  
        if term not in query_dic:
            query_dic[term]=weight
        else:
            query_dic[term]=query_dic[term]+weight
# Unit test
if __name__ == '__main__':
    info_focus_dict = {
        "event": [
            {
                "name": "back",
                "importance": 5
            },
            {
                "name": "pain",
                "importance": 10
            }
        ]
    }
    
    query_string = solr_query_builder(info_focus_dict)
    print(query_string)