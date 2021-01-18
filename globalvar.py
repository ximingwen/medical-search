
def _init(var,name):
    global _global_entity_list
    global _global_attributes
    global _global_snomed
    global _search_result
    global _stopwords
    global _frequent_itemset
    global _tf_idf
    if name=="entity_list":
        _global_entity_list = var
    if name=="attributes":
        _global_attributes=var
    if name=="snomed_codes":
        _global_snomed=var
    if name=="search_result":
        _search_result=var
    if name=="_stopwords":
        _stopwords=var
    if name=="frequent_itemset":
        _frequent_itemset=var
    if name=="tf_idf":
        _tf_idf=var

 
def get_value(var):
    if var=="attributes":
        return _global_attributes
    if var=="annotated_entities":
    	return _global_entity_list
    if var=="snomed_codes":
    	return _global_snomed
    if var=="search_result":
        return _search_result
    if var=="_stopwords":
        return _stopwords
    if var=="frequent_itemset":
        return _frequent_itemset
    if var=="tf_idf":
        return _tf_idf
