import csv
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from operator import itemgetter
import os
import pandas as pd
from typing import List

class Location(BaseModel):
    location: str = Field(description="String value of the location")
    infer_country: str = Field(description="ISO Alpha-2 country code of the location")

class Locations(BaseModel):
    __root__: List[Location]

def infer_countries(dataset, output_loc):
    load_dotenv()
    key = os.getenv('OPEN_AI_KEY')

    model = ChatOpenAI(model="gpt-4o-mini", api_key=key)
    output_parser = JsonOutputParser(pydantic_object=Locations)

    template = """
        Given the following locations delimited by '|': {locations}

        Infer the country of each individual location using the following article as context: {article}
        The country output should be represented as its ISO Alpha-2 country code.
        If the location cannot be inferred to a country, it should be represented as null.

        Output should be formatted as a JSON with keys "location" (name of the location as provided), "infer_country" (country of the location).
    """

    prompt = PromptTemplate(template=template, input_variables=["article", "locations"])
    chain = (
        {"article": itemgetter("article"), "locations": itemgetter("locations")}
        | prompt
        | model
        | output_parser
    )

    with open(output_loc, "w") as wf:
        fieldnames = ["location", "infer_country", "file"]
        writer = csv.DictWriter(wf, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(0, 600):
            if not os.path.exists(f"./datasets/{dataset}/{i}.txt"):
                print(f"File {i} does not exist")
                continue

            with open(f"./datasets/{dataset}/{i}.txt") as f:
                article = f.read()
                locations = " | ".join(pd.read_csv(f"./datasets/{dataset}/{i}.csv")['location'].to_list())
            
                try:
                    locations = chain.invoke({"article": article, "locations": locations})
                    for location in locations:
                        row = {"location": location['location'], 'infer_country': location['infer_country'], "file": i}
                        writer.writerow(row)
                    print(f"Inferred file {i}")
                except:
                    try:
                        row = {"location": locations['location'], "infer_country": locations['infer_country'], "file": i}
                        writer.writerow(row)
                        print(f"Inferred file {i}")
                    except:
                        print(f"Failed to infer file {i}")

if __name__ == "__main__":
    # infer_countries("GeoVirus", "./datasets/GeoVirus/inferred_countries.csv")
    infer_countries("GeoWebNews", "./datasets/GeoWebNews/inferred_countries.csv")
    # infer_countries("LGL", "./datasets/LGL/inferred_countries.csv")