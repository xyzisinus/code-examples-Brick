import requests, json

import sys
sys.path.append('..')
from creds import buildingDepotCreds

# Short demon to show how to connect with BD CentralService,
# create a TagType and retrieve it.

# basic config: BD CS url, client id/key (read from <bd_cs_url>/central/oauth_gen)
bd_cs_url = 'http://localhost:81/'
client_id = buildingDepotCreds['client_id']
client_key = buildingDepotCreds['client_key']

# Get access token and make request header
api_url = bd_cs_url + "oauth/access_token/client_id=" + client_id + "/client_secret=" + client_key
token = requests.get(api_url).json()["access_token"]
header = {"Authorization": "bearer " + token, 'content-type':'application/json'}

# Add a TagType
api_url = bd_cs_url + "api/tagtype"
data = { "data":
         {"name": "building",
          "description": "building"
         }
       }
payload = json.dumps(data)
result = requests.post(api_url, headers = header, data = payload).json()
assert result['success']

# Retrieve it
api_url = bd_cs_url + "api/tagtype/building"
result = requests.get(api_url, headers = header).json()
assert result['success'] and result['name'] == 'building' and result['description'] == 'building'
