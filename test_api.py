import requests
import json
query_string = 'abstract:nicotine^1.0 OR title:nicotine^1.0 OR abstract:tobacco^1.0 OR title:tobacco^1.0 OR abstract:pain^1.0 OR title:pain^1.0 OR abstract:opioid^5.0 OR title:opioid^5.0'

# payload = {'q': query_string, 'start': '0', 'rows': '100',"facet.field":"snomed_codes","facet":"on"}
payload = {
    'event': [
        {
            'name': 'back',
            'importance': 5
        },
        {
            'name': 'pain',
            'importance': 10
        }
    ]
}
# json_object = json.dumps(payload, indent = 4)   
r = requests.post('http://10.4.80.108:8983/search/query', json=payload)
print(r.json())