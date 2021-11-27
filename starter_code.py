import csv
import json
import stanza
import numpy as np

from NLP import NE_obtainer
from entity_linking import levenshteinDistanceDP, score, list_selector, trident_matcher
from elasticsearch import Elasticsearch, RequestError

# These functions need to be here or else Elasticsearch will not work
def search(query):
    """
    Function for ElasticSearch query
    
    Parameters
    ----------
    query : String that you want to give as an input for your ElasticSearch query

    Returns
    -------
    id_labels : A dictionary that contains Wikidata entity IDs (URL) and 
    their labels as the result of the ElasticSearch query

    """
    e = Elasticsearch()
    p = { "query" : { "query_string" : { "query" : query }}}
    response = e.search(index="wikidata_en", body=json.dumps(p), request_timeout=120, size=60)
    id_labels = {}
    if response:
        for hit in response['hits']['hits']:
            try:
                label = hit['_source']['schema_name']
            except KeyError:
                label = "None"
            id = hit['_id']
            id_labels.setdefault(id, set()).add(label)
    return id_labels

def EC_obtainer(NE):
    """
    Function that takes in the named entities from the function NE_obtainer (NLP.py)
    and based on those gives back a list of Wikidata entity candidates

    Parameters
    ----------
    NE : Named entity (string) that was extracted from the WARC file during the NLP part

    Returns
    -------
    entity_candidate_list  : A list that contains the entity candidates 
    (Wikidata labels and entity IDs) that are obtained from Wikidata using ElasticSearch

    """
    entity_canditate_list=[]
    for i in range(len(NE)):
        for j in range(len(NE[i])):
            if j % 2 ==0:

                if __name__ == '__main__':
                    import sys
                    try:
                        _, QUERY = sys.argv
                    except Exception as e:
                        #print(NE[i])
                        QUERY = NE[i][j]
                        #print(QUERY)
                    try:
                        search(QUERY).items()
                    except RequestError:
                        break
                    for entity, labels in search(QUERY).items():
                        entity_canditate_list.append({"labels": labels,
                                                      "entity": entity})
    return entity_canditate_list

# Get the list of Named Entities from the WARC file
WARC_file = "data/sample_new.warc.gz" # Change this to the warc file you want to use
# Set up the NLP pipeline from stanza
nlp = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,ner')
max_NE = 10000 # Limit the number of NEs that can be recognized to make the program run faster
NE_list = NE_obtainer(WARC_file,max_NE,nlp)
print(str(len(NE_list))+" Entities found")

# Obtain a list of wikidata articles for every Named Entity and put them in a
# dict in the list of Named Entities
print("Performing ElasticSearch...")
for i in NE_list:
    i.append(EC_obtainer(i))

print("Levenshtein distance will be calculated")

distance_list = []
for i in NE_list:
    for j in i[2]:
        label = ""
        for k in j['labels']:
            label = label+str(k)
        j['distance'] = levenshteinDistanceDP(i[1][0],label)
    distance_list.append([i[0],i[1],sorted(i[2], key=lambda k: k['distance'])])

# Set up the variables for the trident filter
KBPATH='assets/wikidata-20200203-truthy-uri-tridentdb'

# Load in the lists for each label
NORP_list = np.genfromtxt("label_entities/NORP.txt",dtype="str")
PRODUCT_list = np.genfromtxt("label_entities/PRODUCT.txt",dtype="str")
PERSON_list = np.genfromtxt("label_entities/PERSON.txt",dtype="str")
GPE_list = np.genfromtxt("label_entities/GPE.txt",dtype="str")
LANGUAGE_list = np.genfromtxt("label_entities/LANGUAGE.txt",dtype="str")
ORG_list = np.genfromtxt("label_entities/ORG.txt",dtype="str")

# Create the list dictionary
match_lists = {"NORP_list": NORP_list,
              "PRODUCT_list": PRODUCT_list,
              "PERSON_list": PERSON_list,
              "GPE_list": GPE_list,
              "LANGUAGE_list": LANGUAGE_list,
              "ORG_list": ORG_list}

newnew_list = []

print("Wikidata Entities obtained, Trident filtering will start now")
for i in distance_list:
    print("Filtering: "+str(i[1]))
    new_NE = trident_matcher(i,list_selector(i,match_lists),KBPATH)
    if len(new_NE[2]) != 0:
        newnew_list.append(new_NE)

print("Candidates will be scored")
final_list = score(newnew_list)
print("Results have been obtained")
results = []
for i in final_list:
    results.append(i[0]+" "+i[1][0]+" "+i[2][0]['entity'])
    np.savetxt("results.txt",results, fmt='%s')
    
with open('predictions.tsv', 'wt') as tsvfile:
    writer = csv.writer(tsvfile, delimiter='\t')
    for i in final_list:
        print(i[0],i[1][0],i[2][0]['entity'])
        writer.writerow([i[0],i[1][0],i[2][0]['entity']])