from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments


# accountID = "101-009-20438763-001"  # デモ    # ★★★
# access_token = '955c62ae4f76351d24369b3aae936b35-91f898f60f4dd3e02d4dd8e62754ac61'    # ★★★
# environment = "practice"  # デモ口座 本番は"live"
#
# api = API(access_token=access_token, environment="practice")
#
# params = {
#   "count": 5,
#   "granularity": "M5"
# }
# r = instruments.InstrumentsCandles(instrument="USD_JPY", params=params)
# res = api.request(r)

class test:
    def __init__(self, name):
        self.test = "a"
        self.name = name
        self.r()
        print("test")

    def r(self):
        self.i = "p"

    def p(self):
        print(self.name)
        print(self.i)


ins = test("i")
ins.p()
