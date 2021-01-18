# Medical Search

This project is a pipeline as follows:

(query object) -> [Lucene query writer] -> (Solr search URL string, Solr API) 
-> [search document] -> (document list, ctakes API) -> [entity extractor] 
-> (annotated document list)

Modules we need:

1.  Lucene query writer
2.  search document
3.  entity extractor

## Start Locally:

###### 1. download necessary library and file:

1. library

download scipy, jaydebeapi

2. word embedding

download the csv file from :https://figshare.com/s/00d69861786cd0156d81 (1 GB)

make a folder word-embedding under /visualization

so the path looks like visualization/word-embedding/cui2vec_pretrained.csv

3. GraphViz (only needed if to build new dags) 

download from :https://graphviz.gitlab.io/download/
unzip and add bin path to environment variable

###### 2. to start this script

1. run the code

cd  visualization

python manage.py runserver 0.0.0.0:8000 --noreload

the result will display at localhost:8000

2. build new dag (don't need if only want to check existing pngs get from dot)

cd .\medical-search\visualization\static\data\DAG

open cmd and input: dot -Tpng filename.dot -o filename.png 

## Check Result:

###### 1. Different Results:

1. hierarchical clustering result of snomed:
http://localhost:8000/collocation_snomed/

related function: entitiy_analyzer.py:k_means_clustering, draw_dag_from clustering result

2. snomed hierarchy as a tree:
http://localhost:8000/snomed_hierarchy/

related function: entitiy_analyzer.py:k_means_clustering, draw_dag_from clustering result

3. the three layer cluster tree:
http://localhost:8000/snomed_three_layer_tree/

related function: entitiy_analyzer.py: build_snomed_hierarchy_four_layer_tree

4. the four layer cluster tree:
http://localhost:8000/snomed_four_layer_tree/

related function: entitiy_analyzer.py: build_snomed_hierarchy_three_layer_tree

5. FP tree
related function: frequent_itemset.py

6. Co-occurence Analysis
related function: frequent_itemset.py:cooccurence_analysis_from_pretrained_embedding, cooccurence_analysis_from_clustering_each_row (co-occurence for each concept as a vector)

###### 2. DAG:
location:
.\medical-search\visualization\static\data\DAG

## Start the RESTful API

. /opt/tools/anaconda3/etc/profile.d/conda.sh

conda activate base

python start_api.py
