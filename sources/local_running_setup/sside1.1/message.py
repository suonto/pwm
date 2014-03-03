import json

# Message types
T_ACK = "ACK"
T_FAIL = "FAIL"
T_ERR = "ERR"
T_LOGIN = "LOGIN"
T_LOGOUT = "LOGOUT"
T_RESPONSE = "RESPONSE"
T_GET = "GET"
T_PUT = "PUT"
T_REMOVE = "REMOVE"
T_REGISTER = "REGISTER"
T_DEMO = "DEMO"

# Possible keys in msg.args dictionary
K_USER = "USER"
K_HASH = "HASH"
K_SID = "SID"
K_ID = "ID"
K_PWD = "PWD"
K_REASON = "REASON"
K_STATUS_CODE  = "STATUS CODE"
K_TOKEN = "TOKEN"
K_DEMO_PASS = "DEMO PASSWORD"

# Failure and error reasons
R_BLACKLIST = "BLACKLIST"
R_EMPTY = "EMPTY"
R_NOT_AUTH = "NOT AUTHENTICATED"
R_NO_CONN = "NO CONNECTION"
R_SERV_ERR = "SERVER ERROR"
R_INVALID_TOKEN = "INVALID TOKEN"
R_UNAME_TAKEN = "USERNAME TAKEN"
R_LIMIT_REACHED = "DEMO USER LIMIT REACHED"

VALID_TYPES = [T_ACK, T_ERR, T_RESPONSE]

class Message(object):
    
    def __init__(self, type, args, payload):
        self.type = type
        self.args = args
        self.pay = payload

    def toJson(self):
        return json.dumps({"TYPE":self.type, "ARGS":self.args, "PAYLOAD":self.pay})

def construct_message(jsn):
    pyobj = dict(json.loads(jsn))
    keys = pyobj.keys()
    if len(keys)==3 and "TYPE" in keys and "ARGS" in keys and "PAYLOAD" in keys:
        msg = Message(type=str(pyobj["TYPE"]), args=pyobj["ARGS"], payload=str(pyobj["PAYLOAD"]))
        args = {}
        for key in msg.args.keys():
            args[str(key)] = str(msg.args[key])
            del msg.args[key]
        msg.args = args
        return msg
    else:
        return None

if __name__ == '__main__':
    msg = Message("KALA", {"nakki", "vene"}, "maukasta")
    nahka = msg.toJson()
    print nahka
    print type({"nakki":"vene"})
