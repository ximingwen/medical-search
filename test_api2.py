import requests
import json


sample = {
  "algorithm": "Lingo",
  "language": "English",
  "documents": [
    { "title": "PDF Viewer on Windows" },
    { "title": "Firefox PDF plugin to view PDF in browser on Windows" },
    { "title": "Limit CPU usage for flash in Firefox?" }
  ]
}

r = requests.post('http://localhost:8985/service/cluster?indent', json=sample, headers={"Content-Type": "text/json"})
print(r.json())