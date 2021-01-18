from nltk.corpus import wordnet
import re
'''
def create_synonyms(term):
    synonyms = []
    if(re.search(' ',term)):
        term=term.replace(' ','_')
    syn=wordnet.synsets(term)
    for syn in wordnet.synsets(term):
        for l in syn.lemmas():
            synonyms.append(l.name())
    synonyms=set(synonyms) 
    if (len(synonyms)>0):
        synonyms.remove(term)     
    return synonyms



def create_positive_string(term,synonyms,weight):
    syn_parts=[]
    # process synonyms
    for syn in synonyms:
        # phrases
        if (re.search('_',syn)):
            syn='"'+syn.replace('_',' ')+'"'
            syn_parts.append('abstract:'+'('+ syn + '~' +'2'+')' + '^' + str(weight))
            syn_parts.append('title:' +'('+ syn+ '~' + '2'+')'+ '^' + str(weight))
        # single word 
        else:
            syn_parts.append( 'abstract:' + syn + '^' + str(weight) )
            syn_parts.append( 'title:' + syn + '^' + str(weight) )
    # process the term itself
    if(re.search(' ',term)):
        syn_parts.append('abstract:'+'('+ term + '~' +'2'+')' + '^' + str(weight))
        syn_parts.append('title:' +'('+ term+ '~' + '2'+')'+ '^' + str(weight))
    else:
        syn_parts.append( 'abstract:' + term + '^' + str(weight) )
        syn_parts.append( 'title:' + term + '^' + str(weight) )
    #create the string
    syn_string = ' OR '.join(syn_parts)
    syn_string="("+syn_string+")"
    return syn_string

def create_negtive_string(term,synonyms):
    syn_parts=[]
    # process synonyms
    for syn in synonyms:
        # phrases
        if (re.search('_',syn)):
            syn='"'+syn.replace('_',' ')+'"'
            syn_parts.append('abstract:'+ syn + '~' +'2' )
            syn_parts.append('title:' + syn+ '~' + '2')
        # single word 
        else:
            syn_parts.append( 'abstract:' + syn   )
            syn_parts.append( 'title:' + syn )
    # process the term itself
    if (re.search(' ',term)):
        syn_parts.append('abstract:'+ term + '~' +'2')
        syn_parts.append('title:' + term+ '~' + '2')
    else:
        syn_parts.append( 'abstract:' + term  )
        syn_parts.append( 'title:' + term )
    #create the string
    syn_string = ' OR '.join(syn_parts)
    syn_string="-("+syn_string+")"
    return syn_string

    '''
