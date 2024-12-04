import spacy
import csv

nlp = spacy.load("en_core_web_trf")

def get_title_length(file_num: int):
    with open(f"./Gold_Standard/{file_num}.txt") as f:
        title_length = len(f.readline())
        #print(title_length)
    
    return title_length


def label_file(file_num: int, title_line=True):

    # title_length = get_title_length(file_num)

    with open(f"./LGL/{file_num}.txt") as f:

        with open(f"./Results/LGL_Results/{file_num}.ner", "x") as wf:

            writer = csv.DictWriter(wf, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=['location', 'start', 'end'])
            writer.writeheader()

            text = f.read()
            doc = nlp(text)
            for ent in doc.ents:
                """ if (ent.label_ == "LOC" or ent.label_ == "GPE" or ent.label_ == "FAC") and ent.start_char >= title_length:
                    writer.writerow({"location": ent.text, "start": ent.start_char, "end": ent.end_char})
                    # print(ent.text, ent.start_char, ent.end_char, ent.label_) """
                if (ent.label_ == "LOC" or ent.label_ == "GPE" or ent.label_ == "FAC"):
                    writer.writerow({"location": ent.text, "start": ent.start_char, "end": ent.end_char})

import pandas
from geopy.geocoders import Nominatim
import csv

app = Nominatim(user_agent="thesis_geocoding")
fieldnames = ["location", "lat", "lon", "country", "infer_lat", "infer_lon", "infer_country"]

def geocode_result_file(gold_standard, results, writer):

    for result in results:
        for gs in gold_standard:
            if result['start'] == gs['start'] and result['end'] == gs['end']:
                try:
                    location = app.geocode(result['location'], addressdetails=True).raw
                    writer.writerow({"location": result['location'], "lat": gs['lat'], "lon": gs["long"], "country": gs["country"], "infer_lat": location['lat'], "infer_lon": location['lon'], "infer_country": location['address']['country_code']})
                    #print(result['location'], location)
                except:
                    print(result['location'])

if __name__ == "__main__":

    for i in range(0, 600):

        label_file(i)
        print(f"File {i} labelled")
    
    with open("./Results/LGL_Results/geocoding.csv", "a") as f:
        writer = csv.DictWriter(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(0, 600):
            try:
                gold_df = pandas.read_csv(f"LGL/{i}.csv", delimiter=",")
                results_df = pandas.read_csv(f"./Results/LGL_Results/{i}.ner", delimiter=",")

                gold_standard = gold_df.to_dict(orient='records')
                results = results_df.to_dict(orient='records')

                geocode_result_file(gold_standard, results, writer)
                print(f"Evaluated file {i}")
            except:
                print("Could not find some file")
