import trident
import json
import requests
import numpy as np
from bs4 import BeautifulSoup

def levenshteinDistanceDP(token1, token2):
    """
    Calculates the levenshteindistance between two strings of unequal length

    Parameters
    ----------
    token1 : String 1, usually used as the entity as found in the text
    token2 : String 2, usually used as the label of an entity from wikidata

    Returns
    -------
    TYPE
        Float, measuring the distance between the two

    """
    distances = np.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2
        
    a = 0
    b = 0
    c = 0
    
    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if (token1[t1-1] == token2[t2-1]):
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]
                
                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    #printDistances(distances, len(token1), len(token2))
    return distances[len(token1)][len(token2)]

def list_selector(NE,match_lists):
    """
    This function takes in the Named Entity and determines what list must be
    used in order to match the instances of the entity canditates

    Parameters
    ----------
    NE : Named Entity
    match_lists : dictionary of lists with instances for certain categories

    Returns
    -------
    match_list : the proper list

    """
    if NE[1][1] == "NORP":
        match_list = match_lists['NORP_list']
    elif NE[1][1] == "PRODUCT":
        match_list = match_lists['PRODUCT_list']
    elif NE[1][1] == "PERSON":
        match_list = match_lists['PERSON_list']
    elif NE[1][1] == "GPE":
        match_list = match_lists['GPE_list']
    elif NE[1][1] == "LANGUAGE":
        match_list = match_lists['LANGUAGE_list']
    elif NE[1][1] == "ORG":
        match_list = match_lists['ORG_list']
    else:
        match_list = []
    return match_list

def trident_matcher(NE,match_list,KBPATH):
    """
    This function takes in a NE a matchlist and the KBPATH to match the right
    candidate entities with the NE. It does this by checking if the candidates
    belong to the same group (match_list) of the NE

    Parameters
    ----------
    NE : Named Entity
    match_list : list with wikidata entities
    KBPATH : Path for trident

    Returns
    -------
    new_NE : NE, but has only the matching candidate entities

    """
    new_NE = [NE[0],NE[1],[]]
    max_length = 20 # How many candidates should be evaluated using trident?
    for i in NE[2][0:max_length]:
        #print(i) # Print statement to check which candidates are being evaluated
        accepted = False
        entity = i['entity']
        start = entity.rfind('/') + 1
        end = entity.rfind('>')
        #if entity[start:end] != filter:#delete disambiguation pages
        item = entity[start:end]
        #item = i['entity'].strip("https://wikidata.org/entity/")
             #Retrieve all data in "instance of" property (P31) from all entities from elasticsearch
        query_instance="PREFIX wde: <http://www.wikidata.org/entity/> "\
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> "\
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select ?s WHERE {{wde:{} wdp:P31 ?s. }}".format(item)
        query_subclass="PREFIX wde: <http://www.wikidata.org/entity/> "\
                    "PREFIX wdp: <http://www.wikidata.org/prop/direct/> "\
                    "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
                    "select ?s WHERE {{wde:{} wdp:P279 ?s. }}".format(item)
        
        # Load the KB
        db = trident.Db(KBPATH)
        results_instance = db.sparql(query_instance)
        results_subclass = db.sparql(query_subclass)
        json_results_instance = json.loads(results_instance)
        json_results_subclass = json.loads(results_subclass)
        
        
        variables_instance = json_results_instance["head"]["vars"]
        variables_subclass = json_results_subclass["head"]["vars"]
        
        results_instance = json_results_instance["results"]
        for b in results_instance["bindings"]:
            line = ""
            for var in variables_instance:
                line += var + ": " + b[var]["value"] + " "
            instance = line.strip("s: ")
            if instance in match_list:
                #print("It's a match") Uncomment for more detailed results
                accepted = True
                break
        
        results_subclass = json_results_subclass["results"]
        for b in results_subclass["bindings"]:
            line = ""
            for var in variables_subclass:
                line += var + ": " + b[var]["value"] + " "
            instance = line.strip("s: ")
            if instance in match_list:
                #print("It's a match") # Uncomment for more detailed results
                accepted = True
                break
        
        if accepted == True:
            #print("This instance is accepted") # Uncomment for more detailed results
            new_NE[2].append(i)
        #if accepted == False: # Uncomment for more detailed results
            #print("This instance was rejected") # Uncomment for more detailed resutls
    return new_NE

def score(NE_list):
    """
    Calculates the score of all candidate entities in NE_list by calculating the
    number of times that the Named Entity is present in the wikidata webpage and divides
    that number by the length of the webpage to give the score.

    Parameters
    ----------
    NE_list : A list with the NEs and possible candidates for the NE in it.

    Returns
    -------
    new_list : A list with the NEs and possible candidates for the NE in it, with
    a score that is used to sort all the candidates.

    """
    new_list = []    
    for i in NE_list:
        entity_labels = []
        # Only use the top 10 results, which have the smallest distance between
        # The NE and the candidate
        print("Candidates for: "+i[1][0]+" are being scored")
        length = 5
        if length > len(i[2]):
            length = len(i[2])
        for j in range(length):
            #first retrieve the page
            NE_name = i[1][0]
            entity = i[2][j]['entity']
            URL = entity.strip('<http')
            URL = URL.strip('>')
            URL = "https"+URL
            URL = URL.replace("entity","wiki")
            page = requests.get(URL)
            soup = BeautifulSoup(page.content,'html.parser')
            # Calculate the score by counting the presence of the NE and dividing by length
            text = soup.get_text()
            score = 100*text.count(NE_name)/len(text)
            i[2][j]['score'] = score
            entity_labels.append(i[2][j])
        # Sort the new list by the score
        new_list.append([i[0],i[1],sorted(entity_labels,key=lambda k: k['score'], reverse=True)]) 
    return new_list
