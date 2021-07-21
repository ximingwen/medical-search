import nltk
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import string

def process_highlight(doc, target_clusters):
    stop_words = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    existing_title_span = doc['title_spans']
    existing_abstract_span = doc['abstract_spans']
    abstarct = doc['abstract'][0].lower().split(" ")
    abstract_words = []
    for aw in abstarct:
        aw = aw.translate(str.maketrans('', '', string.punctuation))
        abstract_words.append(stemmer.stem(aw.strip()))
    # print(abstract_words)
    title = doc['title'][0].lower().split(" ")
    title_words = []
    for tw in title:
        tw = tw.translate(str.maketrans('', '', string.punctuation))
        title_words.append(stemmer.stem(tw.strip()))
    for tc in target_clusters:
        label_words = []
        for label_string in tc['labels']:
            ls = label_string.lower().translate(str.maketrans('', '', string.punctuation))
            # print(label_string)
            label_words += word_tokenize(ls)
        filter_words = []
        for w in label_words:
            # print(w)
            if w not in stop_words:
                filter_words.append(stemmer.stem(w))
        # print(filter_words)
        add_new_span(existing_title_span, filter_words, title_words, tc['color'])
        add_new_span(existing_abstract_span, filter_words, abstract_words, tc['color'])
    doc['title_spans'] = existing_title_span
    doc['abstract_spans'] = existing_abstract_span
    return doc

def add_new_span(existing_span, filter_words, text_words, color):
    text_words = np.array(text_words)
    for w in filter_words:
        idxs = np.where(text_words==w)[0]
        if len(idxs) > 0:
            for idx in idxs:
                idx = int(idx)
                for i, span in enumerate(existing_span):
                    # can be inserted before the first existing span
                    if (i==0) and (idx < span['span'][0]):
                        existing_span.insert(0, {'span':[idx, idx], 'color': color})
                        break
                    elif (i > 0) and (idx < span['span'][0]):
                        if idx > existing_span[i-1]['span'][1]:
                            existing_span.insert(i, {'span':[idx, idx], 'color': color})
                        else:
                            existing_span[i-1]['color'] = color
                        break
                    # can be inserted after the last span
                    elif (i==(len(existing_span)-1)):
                        if idx > span['span'][1]:
                            existing_span.insert(i+1, {'span':[idx, idx], 'color': color})
                        elif idx == span['span'][1]:
                            span['color'] = color
                        break
    # print(existing_span)

            


