import os
os.system('pip3 install -r requirements.txt')
import nltk
import stanza
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('wordnet')

stanza.download('en', processors='tokenize,mwt,pos,lemma,ner')
os.system('sh start_elasticsearch_server.sh')
