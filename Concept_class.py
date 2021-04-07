class Concept_global(object):
    def __init__(self):
        self.cui = ''             # cui of this concept
        self.mentions = set()     # string mentions in documents 
        self.pmids = set()        # pmid array, where this concept is mentioned
       
    
    def __init__(self, cui, mention, pmid):
        self.cui = cui
        self.mentions = set([mention])
        self.pmids = set([pmid])
    
    def to_json(self):
        json_out = {
            'mentions': list(self.mentions),
            'pmids': list(self.pmids)
        }
        return json_out
      
# def concept2dic(concepts,json):
#     for cui,concept in concepts.items():
#         json[cui]={}
#         json[cui]['mentions']=list(concept.mentions)
#         json[cui]['pmids']=list(concept.pmids)
      
#     return json

class Concept_cluster(object):
    def __init__(self):
        self.cui = ''             # cui of this concept
        self.mentions = set()     # string mentions in documents 
        self.pmids = set()        # pmid array, where this concept is mentioned
        self.net_count = 0
        self.score = 0
       
    
    def __init__(self, cui, mention, pmid, net_count):
        self.cui = cui
        self.mentions = set([mention])
        self.pmids = set([pmid])
        self.net_count = net_count

    
    def to_json(self):
        json_out = {
            'mentions': list(self.mentions),
            'pmids': list(self.pmids),
            'net_count': self.net_count,
            'score': self.score
        }
        return json_out