text_field = "name"
def sorted_query(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 10,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }

def sorted_query20(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 20,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }

def sorted_query1(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 1,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }

def base_query(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 10
    }

def sorted_query5(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 5,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }

def base_query5(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 5
    }

def base_query20(search_query: str):
    return {
        "query": {
            "match": {
                text_field: search_query,
            }
        },
        "size": 20
    }

def fuzzy_query(search_query: str):
    return {
        "query": {
            "match": {
                text_field: {
                    "query": search_query,
                    "fuzziness": "AUTO"
                }
            }
        },
        "size": 10,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }

def country_query(params):
    return {
        "query": {
            "bool": {
                'must': [
                    {"match": {
                        text_field: params['search_query'],
                    }}
                ],
                "filter": [
                    {"term": {"country": params['country_code'].upper()}}
                ]
            }
        },
        "size": 20,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }

def country_query_no_population(params):
    return {
        "query": {
            "bool": {
                'must': [
                    {"match": {
                        text_field: params['search_query'],
                    }}
                ],
                "filter": [
                    {"term": {"country": params['country_code'].upper()}}
                ]
            }
        },
        "size": 20
    }

def country_query1(params):
    return {
        "query": {
            "bool": {
                'must': [
                    {"match": {
                        text_field: params['search_query'],
                    }}
                ],
                "filter": [
                    {"term": {"country": params['country_code'].upper()}}
                ]
            }
        },
        "size": 1,
        "sort": [{
            "population": {
                "order": "desc"
            }
        }]
    }