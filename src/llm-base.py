# Function for base GPT model

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
import json
import os

class Location(BaseModel):
    location: str = Field(description="String value of the location as it appears in the article")
    infer_lat: float = Field(description="Latitude of the location")
    infer_lon: float = Field(description="Longitude of the location")
    infer_country: str = Field(description="ISO Alpha-2 country code of the location")

class Locations(BaseModel):
    __root__: List[Location]

model = ChatOpenAI(model="gpt-4o-mini")
output_parser = JsonOutputParser(pydantic_object=Locations)

template = """
    Given the following article:
    {article}

    Identify each individual location mention that appears in the article.
    Infer the latitude, longitude and country of each location mention.
    The country output should be represented as its ISO Alpha-2 country code.
    Address locations delimited by a ',' should be separated into their individual locations.
    You should include every and all location that appears in the article.
    Do not output locations that do not appear in the article.

    Output should be formatted as a JSON with keys "location" (string value of the location as it appears in the article), "infer_lat" (latitude of the location), "infer_lon" (longitude of the location), "infer_country" (country of the location).
    """
prompt = PromptTemplate(template=template,
                                 input_variables=["article"])

chain = (prompt | model | output_parser)

# (dataset, results_dir) = ("GeoWebNews", "GWN_Results_GPT")
# (dataset, results_dir) = ("GeoVirus", "GV_Results_GPT")
(dataset, results_dir) = ("LGL", "LGL_Results_GPT")

for i in range(0, 600):
    if not os.path.exists(f"./{dataset}/{i}.txt"):
        print(f"File {i} does not exist")
        continue
    try:
        with open(f"./{dataset}/{i}.txt") as f:
            article = f.read()
            result = chain.invoke({"article": article})
        with open(f"./Results/{results_dir}/{i}.json", "w") as wf:
            wf.write(json.dumps(result, indent=4))
        print(f"Inferred File {i}")
    except:
        with open("log.txt", "a") as log:
            log.write(f"{i}")
        print(f"Something failed on file {i}")
        