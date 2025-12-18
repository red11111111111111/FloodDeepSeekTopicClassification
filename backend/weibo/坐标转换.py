import http.client

conn = http.client.HTTPSConnection("restapi.amap.com")
payload = ''
headers = {}
conn.request("GET", "/v3/geocode/geo?address=%e6%96%b0%e4%b9%a1%e5%ad%94%e5%ba%84%e6%9d%91&Key=6f5894aff371b20019c78c2789dd5323", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))