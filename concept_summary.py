import numpy as np
import nltk
import string
from nltk.tokenize import sent_tokenize
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import json

def generate_summary(query, docids, concept, all_docs, num_sentence, snomed=True):
    stemmer = PorterStemmer()
    docids.sort()
    # print(docids)
    docids = docids[:min(100, len(docids))]
    all_title_cand, all_abs_cand = extract_sent_candids(docids, concept, all_docs, snomed)
    all_title_text = [cand['sent'] for cand in all_title_cand]
    all_abs_text = [cand['sent'] for cand in all_abs_cand]
    all_text = [query] + all_title_text + all_abs_text
    all_cand = all_title_cand + all_abs_cand
    raw_text = []
    for t in all_text:
        words = word_tokenize(t)
        words = [w for w in words if w not in string.punctuation]
        words = [stemmer.stem(w) for w in words]
        raw_text.append(' '.join(words))
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(raw_text)
    # print(len(vectorizer.vocabulary_))
    query = X[0, :].reshape((1, -1))
    cand = X[1:, :]
    sim = cosine_similarity(query, cand)
    # print(sim.shape)
    sim_mat = -np.ones((len(all_cand), len(all_cand)), dtype=np.float)
    for i in range(len(all_cand)):
        sim_mat[i, i] = sim[0, i]
    l = 0.5
    selected_sentence = []
    while len(selected_sentence) < num_sentence:
        new_sent_id = select_sentence(cand, selected_sentence, sim_mat, l)
        selected_sentence.append(new_sent_id)
    summary = []
    for sent_id in selected_sentence:
        summary.append(all_cand[sent_id])
    # print(summary)
    return summary

def select_sentence(cand, selected_sentence, sim_mat, l):
    best_sent = 0
    best_score = np.NINF
    if len(selected_sentence) == 0:
        for i in range(sim_mat.shape[0]):
            score = sim_mat[i, i]
            if score > best_score:
                best_score = score
                best_sent = i
        return best_sent
    else:
        sim_list = cosine_similarity(cand[selected_sentence[-1], :].reshape(1, -1), cand)
        sim_mat[selected_sentence[-1], :] = sim_list        
        for i in range(sim_mat.shape[0]):
            if i in selected_sentence:
                continue
            query_sim = sim_mat[i, i]
            sim = []
            for c in selected_sentence:
                sim.append(sim_mat[c, i])
                assert sim_mat[c, i]!=-1
            max_sim = np.amax(sim)
            score = l * query_sim - (1 - l) * max_sim
            if score > best_score:
                best_score = score
                best_sent = i
                # print(i, best_score)
        return best_sent

def extract_sent_candids(docids, concept, all_docs, snomed):
    all_title_cand = []
    all_abs_cand = []
    for i, docid in enumerate(docids):
        doc = all_docs[docid]
        title = doc['title'][0]
        title_sent = split_and_span(title)
        if snomed:
            title_cand = find_candidates(title_sent, concept, doc['title_spans'])
        else:
            title_cand = find_candidates(title_sent, concept, doc['title_phrase_spans'])
        all_title_cand += title_cand
        abstract = doc['abstract'][0]
        abstract_sent = abstract_split(abstract, json.loads(doc['abstract_sen']))
        # if i < 2:
        #     print(abstract_sent)
        if snomed:
            abstract_cand = find_candidates(abstract_sent, concept, doc['abstract_spans'])
        else:
            abstract_cand = find_candidates(abstract_sent, concept, doc['abstract_phrase_spans'])
        all_abs_cand += abstract_cand
    return all_title_cand, all_abs_cand

def split_and_span(content):
    words = np.array(content.split())
    sents = sent_tokenize(content)
    sent_list = []
    pos = 0
    for i, s in enumerate(sents):
        s_words = s.split()
        span = [pos, pos + len(s_words)-1]
        pos = pos + len(s_words)
        sent_list.append({"sent": s, "span": span, "pos": i, "c_span": []})
    return sent_list

def abstract_split(abstract, abstract_sen):
    abstract_tokens = abstract.split(" ")
    sent_list = []
    for i in range(len(abstract_sen) - 1):
        start = abstract_sen[i]
        end = abstract_sen[i+1]
        sentence = abstract_tokens[start:end]
        sent_list.append({"sent": " ".join(sentence), "span": [start, end-1], "pos": i, "c_span": []})
    return sent_list


def find_candidates(sent_list, target_concept_id, concepts_spans):
    # find target concept's spans
    target_spans = []
    for span in concepts_spans:
        if target_concept_id in span['cui_list']:
            target_spans.append(span['span'])
    
    # find the sentences that the targets spans exist
    sent_cands = []
    for span in target_spans:
        for sent in sent_list:
            if (span[0] >= sent['span'][0]) and (span[1] <= sent['span'][1]):
                sent['c_span'].append([span[0]-sent['span'][0], span[1]-sent['span'][0]])
                break
    for sent in sent_list:
        if len(sent['c_span']) > 0:
            sent_cands.append(sent)
    return sent_cands

# content = "The recent outbreak of coronavirus disease (COVID-19) globally threatens the public health. COVID-19 is a pneumonia caused by severe acute respiratory syndrome coronavirus 2 (SARS-CoV-2), previously known as the 2019 novel coronavirus (2019-nCoV). Typical symptoms of COVID-19 include fever, cough and fatigue. As a novel disease, there are still many unsolved questions regarding COVID-19. Nevertheless, genetic analysis has demonstrated that the virus is strongly associated with certain SARS-like coronavirus originated from bats. The COVID-19 outbreak started in a seafood wholesale market in Wuhan, China, but the exact origin of the virus is still highly debatable. Since there is currently no registered antiviral drug for the disease, symptomatic treatments have been applied routinely to manage COVID-19 cases. However, various drugs and vaccines have been currently under research. This review aims to consolidate and discuss the likely origins and genetic features of SARS-CoV-2 as well as the recent clinical findings and potential effective treatments of COVID-19. Keywords: COVID-19; SARS-CoV-2; 2019-nCoV; SARS; coronavirus."    
# t1 = time.time()
# split_and_span(content)
# t2 = time.time()
# print(t2 -t1)