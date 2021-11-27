Introduction:
With this program we would like to implement a solution that can recognize entity mentions in web
pages and link them to entities in the Wikidata knowledge base. As an input, the program will receive
a WARC file which is a common archive format containing a collection of web pages. The output will
be a list of entities along with the IDs of the web pages and Wikidata entities. We coded the program
in Python, taking advantage of many libraries that are documented in requirements.txt; moreover we
made use of ElasticSearch and Trident which were already installed in the given Docker file.

Instructions to run the program:
1. Run setup.py to install all packages
2. In order to use ElasticSearch the vm.max_map_count should be increased to 262144
3. Run starter_code.py to run the program
