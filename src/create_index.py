import csv
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from langchain_core.documents import Document
from langchain_elasticsearch import ElasticsearchStore, BM25Strategy
import os
import pycountry

load_dotenv()
port = os.getenv("ELASTIC_PORT")

es_url = f"http://localhost:{port}"
es_client = Elasticsearch(hosts=[es_url])
index_name = "geonames_index"

# curl -XDELETE localhost:9618/geonames_index

def get_alt_names():
    with open("./datasets/GeoNames/alternateNames.txt") as f:
        reader = csv.reader(f, delimiter='\t')
        alt_names = {}

        for i, row in enumerate(reader):
            if row[2] == 'en' or row[2] =='abbr':
                if row[1] not in alt_names:
                    alt_names[row[1]] = [row[3]]
                else:
                    alt_names[row[1]].append(row[3])
    
    return alt_names


def create_index():
    """
    Create the index, define mapping in ElasticSearch
    """

    es_client.indices.create(
        index=index_name,
        mappings={
            "properties": {
                "name": {"type": "text"},
                "population": {"type": "long"},
                "country": {"type": "keyword"},
                "admin1": {"type": "text"},
                "latitude": {"type": "float"},
                "longitude": {"type": "float"},
                "feature_code": {"type": "text"}
            }
        }
    )

def index_data():
    load_dotenv()

    with open("./datasets/GeoNames/allCountries.txt") as f:
        reader = csv.reader(f, delimiter='\t')

        alt_names = get_alt_names()
    
        documents = []
        for i, row in enumerate(reader):

            if i % 100000 == 0:
                print(i)
            if i % 1000000 == 0 and i != 0:
                print("Adding 1000000 documents")
                bulk(es_client, documents)
                documents = []
                
            for alt in alt_names.get(row[0], []):
                if alt != row[1]:
                    document = {
                        "_op_type": "index",
                        "_index": index_name,
                        "name": alt,
                        "population": row[14],
                        "country": row[8],
                        "admin1": row[10],
                        "latitude": row[4],
                        "longitude": row[5],
                        "feature_code": row[6] + "." + row[7]
                    }
                    documents.append(document)

            # document = Document(page_content=f"{row[1]} {alternate_names_sentence} and is located at latitude {row[4]} longitude {row[5]}", metadata={'population': row[14], 'country': row[8]})
            document = {
                "_op_type": "index",
                "_index": index_name,
                "name": row[1],
                "population": row[14],
                "country": row[8],
                "admin1": row[10],
                "latitude": row[4],
                "longitude": row[5],
                "feature_code": row[6] + "." + row[7]
            }
            documents.append(document)
        
        print("Finishing indexing")
        bulk(es_client, documents)

if __name__ == "__main__":
    #get_alt_names()
    create_index()
    index_data()