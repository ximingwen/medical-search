# This is the main module

from query_builder import solr_query_builder
from document_searcher import solr_document_searcher
from text_parser import search_result_parser
from frequent_itemset import find_frequent_itemset
from frequent_itemset import calculate_tf_idf
from entity_analyzer import dag_builder
from entity_analyzer import cooccurence_analysis_from_pretrained_embedding
import globalvar as gl

def load_stopwords():
    stopword=set()
    with open('./stopwords.txt') as f:
      for word in f.readlines():
          word=word.strip('\n')
          stopword.add(word)
    return stopword

def load_df():
    tf={}
    with open ("./snomed_df.txt","r") as f:
      for word in f.readlines():
          word=word.strip('\n')
          pair=word.split('\t')
          tf[pair[0]]=pair[1]
    return tf

def main():
    
    
    info_focus_dict = {"event":[      
                          { 
                             "name":"nicotine",
                             "importance":"10"
                          },
                          {
                             "name":"tobacco",
                             "importance":"7"
                          },
                          {
                             "name":"pain",
                             "importance":"5"
                          },
                          {
                             "name":"opioid",
                             "importance":"3"
                          }
                       ]}
                       


	#info_focus_dict = {'concepts': [('migraine', 1.0),('pain',0)]}
    
    gl._init(load_stopwords(),"_stopwords")
    '''
    
    '''
	# step 1: build search string
   
   
    query_string,key_terms = solr_query_builder(info_focus_dict)

	# step 2: search solr index
    print("begin searching")
    results = solr_document_searcher(query_string, False)
    print("end")
    '''
    print("find frequent itemset")
    find_frequent_itemset(results)
    print("end")

    print("calculate_tf_idf")
    calculate_tf_idf(results,code2n)
    print("end")
    '''
    

	# step 3: parse search results
    print("begin parsing")
    concepts= search_result_parser(results, False,100)
    print("end")
  

    
    all_concepts = dict(sorted(concepts.items(), key = lambda x: len(x[1].pmids), reverse = True))
    frequent_concepts={}
    codes=[]
    for cui,concept in all_concepts.items():
        snomed_codes=list(concept.snomed_codes)[0]
        for code in snomed_codes:
            if code not in codes:
               codes.append(code)
            if len(codes)==30:
               break;
   
    gl._init(snomed_codes,"snomed_codes") 
          
 
    dag_builder()


if __name__ == '__main__':
	main() 
