#!/usr/bin/env python3
import json
import urllib.request
import time

time.sleep(3)  # Wait for backend to reload

url = 'http://localhost:8000'
creds = {'username':'dr.mehta','password':'Doctor#1'}
req = urllib.request.Request(url+'/login', data=json.dumps(creds).encode(), headers={'Content-Type':'application/json'})

try:
    with urllib.request.urlopen(req) as r:
        body = r.read().decode()
        token = json.loads(body)['token']
        req2 = urllib.request.Request(url+'/chat', data=json.dumps({'question':'Give the brief details about code of conduct'}).encode(), headers={'Content-Type':'application/json','Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req2) as r2:
            resp = json.loads(r2.read().decode())
            print('✅ CHAT 200 OK')
            print('ANSWER:', resp.get('answer', '')[:250])
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}')
    body = e.read().decode()
    print(body[:400])
except Exception as e:
    print(f'ERR: {type(e).__name__}: {e}')
