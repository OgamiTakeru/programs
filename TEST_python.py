from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments


accountID = "101-009-20438763-001"  # デモ    # ★★★
access_token = '955c62ae4f76351d24369b3aae936b35-91f898f60f4dd3e02d4dd8e62754ac61'    # ★★★
environment = "practice"  # デモ口座 本番は"live"

api = API(access_token=access_token, environment="practice")

params = {
  "count": 5,
  "granularity": "M5"
}
r = instruments.InstrumentsCandles(instrument="USD_JPY", params=params)
res = api.request(r)

# print(res)
print(res['instrument'])
print(res['candles'])
for i in range(len(res['candles'])):
    print(res['candles'][i])
