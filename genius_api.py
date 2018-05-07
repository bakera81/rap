import yaml
import requests
import urllib2
from sanction import Client
# import urllib.parse

with open('genius_credentials.yml', 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

query = 'Rick Ross'
querystring = requests.utils.requote_uri('http://api.genius.com/search/' + query)

c = Client(token_endpoint="https://api.genius.com/oauth/authorize",
           resource_endpoint=querystring,
           # redirect_uri="https://anthonywbaker.com",
           client_id=config['client_id'],
           client_secret=config['client_secret'])

scope = 'me'
c.auth_uri(scope)


# querystring='https://api.genius.com/songs/378195'

r = requests.get(
    querystring,
    params={'access_token': config['client_access_token']},
    headers={'user-agent': '', 'Authorization': 'Bearer ' + config['client_access_token']})


auth_url = 'https://api.genius.com/oauth/authorize/?'
r = requests.get('https://api.genius.com/oauth/authorize',
                 params={
                    'client_id': config['client_id'],
                    'redirect_uri': 'https://anthonywbaker.com',
                    'scope': 'me',
                    'state': 'true',
                    'response_type': 'token'
                 })
r.url

auth_url = 'https://api.genius.com/oauth/authorize/?'
query_params = urllib.parse.urlencode({
       'client_id': config['client_id'],
       'redirect_uri': 'https://anthonywbaker.com',
       'scope': 'me',
       'state': 'true',
       'response_type': 'token'
    })

query_params = 'client_id=' + config['client_id']
query_params += '&redirect_uri=https://anthonywbaker.com'
query_params += '&scope=me'
query_params += '&state=true'
query_params += '&response_type=token'
auth_url = auth_url + query_params

# The challenge is that you need to open a browser, click, then grab the access token from the query parametersself.
# To automate this, we'll need selenium.
# The alternative is to scrape it directly...

with open('auth_page.html', 'w') as f:
    f.write(r.text)

# The token only works once. You need to dynamically get the token using requests.
