'''
Created on 3.2.2014

@author: suontom1
'''
import message as m
import threading
import time
from logger_setup import LoggerBuilder
from Crypto.Random import _UserFriendlyRNG as rng
import json

from database import Database
import database

# Generated by rng.get_random_bytes(16).encode('hex')
REG_TOKENS = "reg_tokens.txt"
#SERVER_LOG = "/srv/http/serv_version1/server.log"
#SERVER_LOG = "server.log"
SERVER_LOG = None
#DB_LOG = "/srv/http/serv_version1/database.log"
#DB_LOG = "database.log"
DB_LOG = None

class ExpirationTimer(threading.Thread):
    
    def __init__(self, uname, expire_function, expiration_time):
        threading.Thread.__init__(self)
        self.daemon = True
        self.__uname = uname
        self.__ex = expire_function
        self.__et = expiration_time
        self.__start_time = time.time()
        self.__die = False
    
    def run(self):
        '''
        After expiration time user expiration function is called.
        Time is checked every second.
        '''
        time_passed = 0
        while time_passed < self.__et and not self.die:
             time.sleep(1)
             time_passed = time.time() - self.__start_time
        if time_passed > self.__et:
            self.__ex(self.__uname)

    def reset(self):
        self.__start_time = time.time()

    def die(self):
        self.__die = True

class Server(object):
   
    def __init__(self, logfile=SERVER_LOG, debug=True):
        self.__db = Database(debug=debug, logfile=DB_LOG)
        self.__authenticated_users = {}
        self.__timers = {}
        self.__logger = LoggerBuilder().build_logger("Server", logfile=logfile, debug=debug)
        self.__logger.info("The server been initialized.")

    def register(self, uname, h, token):
        if not self.__check_credentials(uname, h):
            return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        self.__logger.info("We are registering "+uname+".")
        creds = self.__db.get_user_credentials()
        if uname in creds:
            self.__logger.info("Registration for "+uname+" failed. Username already in use.")
            return m.Message(m.T_FAIL, {m.K_REASON:m.R_UNAME_TAKEN}, "Username already in use.")  
        f = open(REG_TOKENS, "r")
        tokens = f.read()
        write_back = ""
        success = False
        result = m.Message(m.T_FAIL, {m.K_REASON:m.R_INVALID_TOKEN}, "Invalid token.") 
        for t in tokens.split('\n'):
            if t == token and len(t) == 32: 
                self.__db.store_user_credentials(uname, h)
                result = m.Message(m.T_ACK, {}, "User "+uname+" registered successfully.") 
                success = True
                self.__logger.info("Registration for "+uname+" successful.")
            elif len(t) == 32:
                write_back += t+'\n'
            else:
                pass  
        f.close()
        if success == False:
            self.__logger.info("Registration for "+uname+" failed. Invalid token.")
        else:
            f = open(REG_TOKENS, "w")
            f.write(write_back) 
        return result
   
    def demo(self):
        self.__logger.info("We are requesting a demo session.")
        user = self.__db.generate_demo_user()
        if user == {}:
            self.__logger.info("We denied session. Demo user limit reached.")
            return m.Message(m.T_ERR, {m.K_REASON:m.R_LIMIT_REACHED}, "Demo user limit reached. Try again later.")

        else:
            uname = user[m.K_USER]
            self.__logger.info("We granted session "+uname+".")
            session_token = self.__generate_session_token()
            user[m.K_SID] = session_token
            self.__authenticated_users[uname] = session_token
            self.__logger.debug("We have added "+uname+ " into auth_users.")
            self.__set_reset_timer(uname)
            return m.Message(m.T_RESPONSE, user, "Demo session granted.")

    def authenticate(self, uname, h):
        self.__logger.info("We are authenticating user '"+uname+"': '"+h+"'...")
        creds = self.__db.get_user_credentials()
        if creds == {}:
            self.__logger.debug("Authentication failed. User "+uname+" not registered.")         
            return m.Message(m.T_FAIL, {m.K_REASON : m.R_EMPTY}, "User not registered.")
        self.__logger.debug("The credentials are: "+str(creds))            
        if uname in creds.keys():
            match = self.__match_safely(creds[uname], h)
            # Success if user is found and hash is correct.
            if match:
                session_token = self.__generate_session_token()
                self.__authenticated_users[uname] = session_token
                self.__logger.debug("We have added "+uname+ " into auth_users.")
                self.__set_reset_timer(uname)
                self.__logger.debug("Authenticated users: "+self.__authenticated_users.__str__())
                self.__logger.info(uname+"'s authentication successful.")
                return m.Message(m.T_RESPONSE, {m.K_SID : session_token}, "Authentication successful.")
            else:
                if uname in self.__authenticated_users.keys():
                    del self.__authenticated_users[uname]
                self.__logger.debug("Authentication failed. Invalid hash.")
                return m.Message(m.T_FAIL, {m.K_REASON : m.R_NOT_AUTH}, "authentication failed.")
        else:
            self.__logger.debug("failed. User "+uname+" not registered.")         
            return m.Message(m.T_FAIL, {m.K_REASON : m.R_NOT_AUTH}, "user not registered.")

    def logout(self, uname):
        if uname in self.__authenticated_users.keys():
            del self.__authenticated_users[uname]
            self.__logger.debug("We have removed "+uname+" from auth_users.")
        if uname in self.__timers.keys():
            self.__timers[uname].die()
            del self.__timers[uname]
            self.__logger.debug("We have removed "+uname+" from timers.")
        self.__logger.info("User "+uname+" logged out.")
        if uname.startswith('demo_'):
            self.__db.delete_user(uname)
            self.__logger.debug("We have deleted demouser "+uname+".")
        return m.Message(m.T_ACK, {}, "Bye.")
           
    def read_passwords(self, uname, sid):
        if self.__check_auth(uname, sid):
            pwd_dict = self.__db.read_passwords(uname)
            return m.Message(m.T_RESPONSE, pwd_dict, "Read successful.")
        else:       
            return m.Message(m.T_FAIL, {m.K_REASON : m.R_NOT_AUTH}, "Authentication required.") 
        
    def store_password(self, uname, sid, id, pwd):
        if self.__check_auth(uname, sid):
            result = self.__db.add_password(uname, identifier=id, pwd=pwd)
            if result == True:
                return m.Message(m.T_ACK, {}, "Storage successful.")
            else:
                raise Exception("Store password faced unexpected db response.")
        else:
            return m.Message(m.T_FAIL, {m.K_REASON : m.R_NOT_AUTH}, "Authentication required.") 

    def remove_password(self, uname, sid, id):
        if self.__check_auth(uname, sid):
            result = self.__db.delete_password(uname, identifier=id)
            if result == True:
                return m.Message(m.T_ACK, {}, "Removal successful.")
            else:
                raise Exception("Remove password faced unexpected db response.")
        else:
            return m.Message(m.T_FAIL, {m.K_REASON : m.R_NOT_AUTH}, "Authentication required.") 

    def respond(self, request):
        try:
            msg = self.__construct_response(request)
            # We might blacklist the client before return if neccessary.
            # TODO: Blacklist implementation
            # TODO: Login attempt counters for account locking
            return msg.toJson()
        except Exception as e:
            self.__logger.critical("We have crashed! Reason:\n"+e.__str__())

    def __construct_response(self, request):
        msg = m.construct_message(request)
        if msg:
            response = self.__exact_response(msg)
            return response
        else:
            return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")

    def __exact_response(self, msg):
        '''
        Sorts the requests to right handlers according to type.
        If the client has been tampered with, it is blacklisted.
        '''
        if msg.type == m.T_LOGIN:
            keys = msg.args.keys()
            if len(keys) == 2 and m.K_USER in keys and m.K_HASH in keys:
                return self.authenticate(uname=msg.args[m.K_USER], h=msg.args[m.K_HASH])
            elif len(keys) == 2 and m.K_USER in keys and m.K_SID in keys:
                self.__timer_reset(uname=msg.args[m.K_USER])
                self.__logger.debug("User "+msg.args[m.K_USER]+" still alive.")         
                return m.Message(m.T_ACK, {}, "We have refreshed your login.")
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        elif msg.type == m.T_GET:
            keys = msg.args.keys()
            if len(keys) == 2 and m.K_USER in keys and m.K_SID in keys:
                return self.read_passwords(msg.args[m.K_USER], msg.args[m.K_SID])
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        elif msg.type == m.T_PUT:
            keys = msg.args.keys()
            if len(keys) == 4 and m.K_USER in keys and m.K_SID in keys and m.K_ID in keys and m.K_PWD in keys:
                return self.store_password(msg.args[m.K_USER], msg.args[m.K_SID], id=msg.args[m.K_ID], pwd=msg.args[m.K_PWD])
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        elif msg.type == m.T_REMOVE:
            keys = msg.args.keys()
            args = msg.args
            if len(keys) == 3 and m.K_USER in keys and m.K_SID in keys and m.K_ID in keys:
                return self.remove_password(args[m.K_USER], args[m.K_SID], id=args[m.K_ID])
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        elif msg.type == m.T_LOGOUT:
            keys = msg.args.keys()
            args = msg.args
            if len(keys) == 1 and m.K_USER in keys:
                return self.logout(args[m.K_USER])
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        elif msg.type == m.T_REGISTER:
            keys = msg.args.keys()
            args = msg.args
            if len(keys) == 3 and m.K_USER in keys and m.K_HASH in keys and m.K_TOKEN in keys:
                return self.register(args[m.K_USER], args[m.K_HASH], args[m.K_TOKEN])
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        elif msg.type == m.T_DEMO:
            keys = msg.args.keys()
            if len(keys) == 0:
                return self.demo()
            else:
                return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")
        
        else:
            return m.Message(m.T_ERR, {m.K_REASON:m.R_BLACKLIST}, "Welcome to blacklist.")

    def __check_auth(self, uname, sid):
        auth_users = self.__authenticated_users
        if uname in auth_users and self.__match_safely(sid, auth_users[uname]):
            return True
        else:
            self.__logger.debug("Check auth failed. User "+uname+" not authenticated.")         
            return False

    def __match_safely(self, str1, str2):
        try:
            match = True
            if len(str1) != len(str2):
                return False 
            for i in range(len(str1)):
                if str1[i] != str2[i] :
                    match = False
            return match
        except Exception as e:
            self.__logger.debug("Exception caught in __match_safely:", e)                    
            return False 

    def __generate_session_token(self):
        secret = rng.get_random_bytes(50)
        return secret.encode('base64').replace('\n', '')

    def __expire_user(self, uname):
        if uname in self.__authenticated_users.keys():
            del self.__authenticated_users[uname] 
            del self.__timers[uname]
            self.__logger.debug("We have removed "+uname+" from timers and auth_users.")

    def __timer_reset(self, uname):
        self.__timers[uname].reset()

    def __set_reset_timer(self, uname, time=300):
        # Set a timer in seconds how long user's authentication stays valid.
        self.__logger.debug("We have added "+uname+" into timers.")
        self.__timers[uname] = ExpirationTimer(uname, self.__expire_user, time)
        self.__timers[uname].start()

    def __check_credentials(self, uname, h):
        if self.__is_valid_id(uname) and self.__is_valid_hash(h):
            return True
        else:
            return False
        

    def __is_valid_id(self, id):
        normal = False
        for letter in id:
            if not (64 < ord(str(letter)) < 91 or 96 < ord(str(letter)) < 123 or 47 < ord(str(letter)) < 58):
                return False
        if 3 < len(id) < 16:
            return True
        else:
            return False 

    def __is_valid_hash(self, h):
        if len(h) == 128:
            try:
                h.decode('hex')
                return True
            except:
                return False
        else:
            return False 
       

if __name__ == '__main__':
    s = Server(debug=True)
    response = s.authenticate("suonto", "suontos pwd hash")
    print response.toJson()
    
    
