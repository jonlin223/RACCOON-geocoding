from dotenv import load_dotenv
import json
from langchain_elasticsearch import ElasticsearchRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from operator import itemgetter
import os
import pandas as pd
import pycountry
from typing import List

from query import sorted_query20, country_query, country_query1, sorted_query1, base_query20, country_query_no_population

# SETTINGS

LARGER_CONTEXT = True
COUNTRY_RETRIEVAL = True
STATE_CONTEXT = True # Setting for state level context
GEONAMES_FEATURES = True # Setting to include geonames feature type in context
POPULATION_HEURISTIC = True
LLM_MODEL = "Gemini" # GPT or Gemini

text_field = "name"

class Location(BaseModel):
    location: str = Field(description="String value of the location as it appears in the article")
    infer_lat: float = Field(description="Latitude of the location")
    infer_lon: float = Field(description="Longitude of the location")
    infer_country: str = Field(description="ISO Alpha-2 country code of the location")

class Locations(BaseModel):
    __root__: List[Location]

def format_context(documents: list[Document]):
    formatted = []
    feature_codes = pd.read_csv("./datasets/GeoNames/featureCodes_en.txt", delimiter="\t", index_col="code").to_dict('index')

    for doc in documents:
        if GEONAMES_FEATURES:
            try:
                feature = feature_codes[doc.metadata['_source']['feature_code']]['name'].rstrip('(s)')
            except:
                feature = "location"
        else:
            feature = "location"

        try:
            formatted.append(f"'{doc.page_content}' is a {feature} in '{pycountry.countries.get(alpha_2=doc.metadata['_source']['country']).name}' with latitude {doc.metadata['_source']['latitude']} and longitude {doc.metadata['_source']['longitude']}")
        except:
            formatted.append(f"'{doc.page_content}' is a {feature} with latitude {doc.metadata['_source']['latitude']} and longitude {doc.metadata['_source']['longitude']}")
    # print(formatted)
    return formatted

def format_context_state(documents: list[Document]):
    formatted = []
    feature_codes = pd.read_csv("./datasets/GeoNames/featureCodes_en.txt", delimiter="\t", index_col="code").to_dict('index')
    admin1_dict = pd.read_csv("./datasets/GeoNames/admin1CodesASCII.txt", delimiter="\t", index_col="code").to_dict('index')

    for doc in documents:
        if GEONAMES_FEATURES:
            try:
                feature = feature_codes[doc.metadata['_source']['feature_code']]['name'].rstrip('(s)')
            except:
                feature = "location"
        else:
            feature = "location"

        try:
            admin1 = doc.metadata['_source']['admin1']
            country = doc.metadata['_source']['country']
            code = country.upper() + '.' + admin1
            admin1_name = admin1_dict[code]['name'] + ", "
        except:
            admin1_name = ""

        try:
            formatted.append(f"'{doc.page_content}' is a {feature} in '{admin1_name}{pycountry.countries.get(alpha_2=doc.metadata['_source']['country']).name}' with latitude {doc.metadata['_source']['latitude']} and longitude {doc.metadata['_source']['longitude']}")
        except:
            formatted.append(f"'{doc.page_content}' is a {feature} with latitude {doc.metadata['_source']['latitude']} and longitude {doc.metadata['_source']['longitude']}")
    # print(formatted)
    return formatted

def identify_locations(dataset, results_dir):
    load_dotenv()
    key = os.getenv('OPEN_AI_KEY')
    port = os.getenv('ELASTIC_PORT')

    if LLM_MODEL == "GPT":
        model = ChatOpenAI(model="gpt-4o-mini", api_key=key)
    elif LLM_MODEL == "Gemini":
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    output_parser = JsonOutputParser(pydantic_object=Location)

    if LARGER_CONTEXT:
        if not POPULATION_HEURISTIC:
            retriever_country = ElasticsearchRetriever.from_es_params(
                index_name="geonames_index",
                body_func=country_query_no_population,
                content_field=text_field,
                url=f"http://localhost:{port}"
            )
            retriever_no_country = ElasticsearchRetriever.from_es_params(
                index_name="geonames_index",
                body_func=base_query20,
                content_field=text_field,
                url=f"http://localhost:{port}"
            )
        else:
            retriever_country = ElasticsearchRetriever.from_es_params(
                index_name="geonames_index",
                body_func=country_query,
                content_field=text_field,
                url=f"http://localhost:{port}"
            )
            retriever_no_country = ElasticsearchRetriever.from_es_params(
                index_name="geonames_index",
                body_func=sorted_query20,
                content_field=text_field,
                url=f"http://localhost:{port}"
            )
    else:
        retriever_country = ElasticsearchRetriever.from_es_params(
            index_name="geonames_index",
            body_func=country_query1,
            content_field=text_field,
            url=f"http://localhost:{port}"
        )
        retriever_no_country = ElasticsearchRetriever.from_es_params(
            index_name="geonames_index",
            body_func=sorted_query1,
            content_field=text_field,
            url=f"http://localhost:{port}"
        )

    template = """
        Given the following location:
        {location}

        Infer the latitude, longitude and country of this location using the following article as context: {article}
        The country output should be represented as its ISO Alpha-2 country code.

        Retrieve the correct location from the following context. If none of the given locations are correct, infer location without this context: {context}

        Output should be formatted as a JSON with keys "location" ({location}), "infer_lat" (latitude of the location), "infer_lon" (longitude of the location), "infer_country" (country of the location).
    """

    prompt = PromptTemplate(template=template,
                            input_variables=["article", "location", "context"])

    if STATE_CONTEXT:
        chain_country = (
            {"article": itemgetter("article"), "location": itemgetter("location"), "context": {'search_query': itemgetter("location"), 'country_code': itemgetter("country_code")} | retriever_country | format_context_state}
            | prompt
            | model
            | output_parser
        )
        chain_no_country = (
            {"article": itemgetter("article"), "location": itemgetter("location"), "context": itemgetter("location") | retriever_no_country | format_context_state}
            | prompt
            | model
            | output_parser
        )
    else:
        chain_country = (
            {"article": itemgetter("article"), "location": itemgetter("location"), "context": {'search_query': itemgetter("location"), 'country_code': itemgetter("country_code")} | retriever_country | format_context}
            | prompt
            | model
            | output_parser
        )
        chain_no_country = (
            {"article": itemgetter("article"), "location": itemgetter("location"), "context": itemgetter("location") | retriever_no_country | format_context}
            | prompt
            | model
            | output_parser
        )

    inferred_countries = pd.read_csv(f"./datasets/{dataset}/inferred_countries.csv").groupby('file')[['location', 'infer_country']].apply(lambda g: list(map(tuple, g.values.tolist()))).to_dict()

    for i in range(0, 600):
        if not os.path.exists(f"./datasets/{dataset}/{i}.txt"):
            print(f"File {i} does not exist")
            continue

        with open(f"./datasets/{dataset}/{i}.txt") as f:
            article = f.read()
            try:
                locations = inferred_countries[i]
            except:
                continue
        
        results = []
        cache = {}
        for (location, country) in locations:
            if location not in cache:
                try:
                    if not COUNTRY_RETRIEVAL or pd.isna(country):
                        result = chain_no_country.invoke({"article": article, "location": location})
                    else:
                        result = chain_country.invoke({"article": article, "location": location, "country_code": country})
                    results.append(result)
                    cache[location] = {'infer_lat': result['infer_lat'], 'infer_lon': result['infer_lon'], 'infer_country': result['infer_country']}
                    print(f"Inferred location {location} in file {i}")
                except:
                    print(f"Failed to infer file {location} in file {i}")
            else:
                result = {'location': location, 'infer_lat': cache[location]['infer_lat'], 'infer_lon': cache[location]['infer_lon'], 'infer_country': cache[location]['infer_country']}
                results.append(result)
                print(f"Inferred location {location} in file {i} from cache")

        with open(f"./results_gemini/{results_dir}/{i}.json", "w") as wf:
            print(f"Inferred file {i}")
            wf.write(json.dumps(results, indent=4))
        
    

if __name__ == "__main__":

    (dataset, results_dir) = ("GeoVirus", "GV_Results_RAG_Gemini_Without_State")
    identify_locations(dataset, results_dir)
    (dataset, results_dir) = ("GeoWebNews", "GWN_Results_RAG_Gemini_Without_State")
    identify_locations(dataset, results_dir)
    (dataset, results_dir) = ("LGL", "LGL_Results_RAG_Gemini_Without_State")
    identify_locations(dataset, results_dir)
    
