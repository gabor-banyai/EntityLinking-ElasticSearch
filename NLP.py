from bs4 import BeautifulSoup
from warcio.archiveiterator import ArchiveIterator
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.parse.corenlp import CoreNLPParser
from nltk.stem import WordNetLemmatizer 
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.tree import Tree 
from nltk import ne_chunk, pos_tag

st = CoreNLPParser()
lemmatizer = WordNetLemmatizer()

def NE_stanford(text,nlp):
    """
    Function that takes in text and returns a list of NEs

    Parameters
    ----------
    text : string of text that we want to analyze
    nlp : NLP pipeline for stanza

    Returns
    -------
    NE_list: List of NEs

    """
    text.replace("\n","")
    sentences = sent_tokenize(text)
    # create list of instances that we do not want
    instance_list = ["DATE","ORDINAL","CARDINAL","MONEY","TIME","WORK_OF_ART","LAW","PERCENT","QUANTITY","MISC","EVENT"]
    NE_list = []
    for sent in sentences:
        doc = nlp(sent)
        tokens = [[token.text, token.ner] for sent in doc.sentences for token in sent.tokens]
        current_NER = ""
        NER_mode = False
        for i in tokens:
            if i[1][0] == "B":
                NER_mode = True
            if NER_mode == True:
                current_NER = current_NER+" "+i[0]
            if i[1][0] == "E":
                NER_mode = False
                if i[1][2:] not in instance_list:
                    NE_list.append([current_NER.strip(),i[1][2:]])
                current_NER = ""
            if i[1][0] == "S":
                if i[1][2:] not in instance_list:
                    NE_list.append([i[0],i[1][2:]])
    
    print("Found NEs: "+str(NE_list))
    return(NE_list)

def NE_obtainer(WARC_file,limit,nlp):
    """
    Function that retrieves al NEs from a WARC file
    Parameters
    ----------
    WARC_file : WARC with the webpages you want to use.
    Limit : A limit on the number of NEs, used to make testing faster
    NLP : the NLP pipeline used for the stanford NER

    Returns
    -------
    NE_list : A list of NEs with the given WARC-id of the page that it came from.

    """
    NE_list = []
    with open(WARC_file, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'warcinfo':
                print(record.raw_stream.read())
            elif record.rec_type == 'response':
                if record.http_headers.get_header('Content-Type') == 'text/html':
                    print(record.rec_headers.get_header('WARC-Target-URI'))
                    WARC_ID = record.rec_headers.get_header('WARC-Record-ID')
                    print(WARC_ID) # Print the WARC_id for testing
                    page = record.content_stream().read()
                    soup = BeautifulSoup(page,'html.parser')
                    #current_NE_list = get_continuous_chunks(soup.get_text())
                    current_NE_list = NE_stanford(soup.get_text(),nlp)
                    for item in current_NE_list:
                        if item not in NE_list:                        
                            NE_list.append([WARC_ID,item])
                    if len(NE_list)>limit:
                        return NE_list
    return NE_list

def get_continuous_chunks(text):
    """
    (NOT USED ANYMORE)
    Parameters
    ----------
    text : Text that you want to split into chunks

    Returns
    -------
    continuous_chunk : A list with the chunks and the tags

    """
    stop_words = set(stopwords.words('english'))
    sentences = sent_tokenize(text)
    continuous_chunk = []
    for sent in sentences:
        tokenized_text = word_tokenize(sent)
        filtered = [w for w in tokenized_text if not w in stop_words]
        tagged = pos_tag(filtered)
        lemmatized_text = lemmatize_text(tagged)
        chunked = ne_chunk(pos_tag(word_tokenize(lemmatized_text)))
        #print(chunked)
        current_chunk = []
        for i in chunked:
            if type(i) == Tree:
                current_chunk.append(" ".join([token for token, pos in i.leaves()]))
            if current_chunk:
               named_entity = " ".join(current_chunk)
               if named_entity not in continuous_chunk:
                       continuous_chunk.append([named_entity,i.label()])
                       current_chunk = []
            else:
                continue
    return continuous_chunk 

"""
FUNCTIONS BELOW ARE NO LONGER USED, BUT INCLUDED TO SHOW HOW THE MANUALLY CREATED
FUNCTIONS WORK
"""
def get_wordnet_pos(treebank_tag):
    """
    Function that takes in a tag from the function pos_tag() and gives back a version
    that can be used for lemmatization. (NOT USED ANYMORE)
    Parameters 
    ----------
    treebank_tag : The tag that you want to transform so that it can be lemmatized

    Returns
    -------
    the proper tag.
    """
    
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None
    
def lemmatize_text(pos_text):
    """
    Function that lemmatizes a given text (NOT USED ANYMORE)

    Parameters
    ----------
    pos_text : A string with POS tag

    Returns
    -------
    TYPE
        string that has been lemmatized

    """
    wn_tagged = map(lambda x: (x[0], get_wordnet_pos(x[1])), pos_text)
    res_words = []
    for word, tag in wn_tagged:
        if tag is None:                        
            res_words.append(word)
        else:
            res_words.append(lemmatizer.lemmatize(word, tag))
    return " ".join(res_words)

