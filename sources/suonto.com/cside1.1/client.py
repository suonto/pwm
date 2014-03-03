'''
Created on 8.2.2014

@author: suonto
'''
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import _UserFriendlyRNG as rng
import scrypt
import random
import message as m
import json
import requests
import time
import os

HOST = "54.194.255.244"
PORT = 443
RSA_LEN = 4096

hdrs = {
		"Accept-Language" : 'en-US,en;q=0.5',
		"Accept-Encoding" : 'gzip, deflate',
		"Connection" : 'close',
		"Accept" : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		"Host" : 'suonto.com',
                "Content-Type" : "application/json"
                
	   }

S_NOT_AUTH, S_AUTH = xrange(2)

#TODO: Registration

class Client(object):

    def __init__(self, uname, passphrase):
        self.__uname = uname
        self.__pp = passphrase
        self.__sid = None
        self.__state = S_NOT_AUTH
        self.__priv = None
        random.seed()

    def get_username(self):
        return self.__uname

    def set_credentials(self, uname, pp):
        self.__uname = uname
        self.__pp = pp

    def import_rsa(self, filename=""):
        if filename == "":
            filename = self.__uname+".pem"
        try:
            f = open(filename,'r')
            priv = RSA.importKey(f.read(), passphrase=self.__pp)
            f.close()
        except IOError:
            priv = RSA.generate(RSA_LEN)
            self.__export_rsa(priv)
        return priv 

    def __export_rsa(self, priv, filename=""):
        '''
        The keys are only exported if they are generated for the first time.
        Afterwards there is no need for export, since the keys remain the same.
        Using priv arg instead of self.__priv to enable calling from import_rsa.
        '''
        if filename == "":
            filename = self.__uname+".pem"
        f = open(filename,'w')
        f.write(priv.exportKey('PEM', passphrase=self.__pp))
        f.close()

    def encrypt_rsa(self, message):
        return self.__pkcs1.encrypt(message).encode("hex")
    
    def decrypt_rsa(self, ctext):
        return self.__pkcs1.decrypt(ctext.decode('hex'))

    def hex_hash(self, data):
        # As salt using username concatenated with it's legth.
        h1 = scrypt.hash(data, self.__uname+str(len(self.__uname)))
        return h1.encode('hex')

    def register(self, uname, passphrase, reg_token):
        self.__uname = uname
        msg = m.Message(m.T_REGISTER, {m.K_USER : uname, m.K_HASH : self.hex_hash(passphrase), m.K_TOKEN:reg_token}, "User "+uname+" requesting registration.")
        self.__uname = None
        response = self.__request(msg)
        response = self.__sort_response(response, "Register") 
        return response

    def demo(self):
        msg = m.Message(m.T_DEMO, {}, "User requesting a demo session.")
        response = self.__request(msg)
        response = self.__sort_response(response, "Demo") 
        return response

    def demo_settings(self, sid):
        self.__priv = self.import_rsa() 
        self.__pkcs1 = PKCS1_OAEP.new(self.__priv)  
        self.__sid = sid
        self.__state = S_AUTH

    def try_login(self, uname, passphrase):
        self.__uname = uname
        msg = m.Message(m.T_LOGIN, {m.K_USER : uname, m.K_HASH : self.hex_hash(passphrase)}, "User "+uname+" requesting authentication.")
        self.__uname = None
        response = self.__request(msg)
        response = self.__sort_response(response, "Try login") 
        return response
       
    def login(self):
        #msg = m.Message(m.T_LOGIN, {m.K_USER : self.__uname, m.K_HASH : self.hex_hash(self.__pp)}, "User "+self.__uname+" requesting authentication.")
        msg = m.Message(m.T_LOGIN, {m.K_USER : self.__uname, m.K_HASH : self.hex_hash(self.__pp)}, "User "+self.__uname+" requesting authentication.")
        response = self.__request(msg)
        if response.type == m.T_RESPONSE:
            self.__priv = self.import_rsa() 
            self.__pkcs1 = PKCS1_OAEP.new(self.__priv)  
            self.__sid = response.args[m.K_SID]
            self.__state = S_AUTH
        else:
            self.__sid = None
            self.__state = S_NOT_AUTH
        return response

    def logout(self):
        msg = msg = m.Message(m.T_LOGOUT, {m.K_USER : self.__uname}, "User "+self.__uname+" leaving.")
        caller = "Logout"
        response = self.__make_request(msg, caller)
        if self.__uname.startswith('demo_'): 
            try:
                os.remove(self.__uname+".pem")
            except:
                pass
        return response
            
    def get_passwords(self):
        msg = m.Message(m.T_GET, {m.K_USER : self.__uname, m.K_SID : self.__sid}, "Requesting passwords.")
        caller = "Get passwords"
        response = self.__make_request(msg, caller)
        return response

    def store_password(self, id, pwd):
        crypted = self.encrypt_rsa(pwd)
        msg = m.Message(m.T_PUT, {m.K_USER:self.__uname, m.K_SID:self.__sid, m.K_ID:id, m.K_PWD:crypted}, "Requesting storage.")
        caller = "Store password"    
        response = self.__make_request(msg, caller)
        return response
            
    def remove_password(self, id):
        msg = m.Message(m.T_REMOVE, {m.K_USER:self.__uname, m.K_SID:self.__sid, m.K_ID:id}, "Requesting removal.")    
        caller = "Remove password"
        response = self.__make_request(msg, caller)
        return response

    def stay_logged(self):
        msg = m.Message(m.T_LOGIN, {m.K_USER:self.__uname, m.K_SID:self.__sid}, "User "+self.__uname+"requesting to stay logged in.")    
        caller = "Stay logged"
        response = self.__make_request(msg, caller)
        return response
     
    def __make_request(self, msg, caller):
        if self.__state == S_AUTH :
            response = self.__request(msg)
            response = self.__sort_response(response, caller)    
        else:
            response = m.Message(m.T_ERR, {}, "Authentication required.") 
        return response

    def __request(self, request):
        try:
            #print "sending:", request.type, request.args
            r = requests.post('https://suonto.com/', headers=hdrs, data=request.toJson())
            if r.status_code == 502:
                return m.Message(m.T_ERR, {m.K_REASON : m.R_SERV_ERR}, "Server error.")                
            #print "we got back:\nStatus Code:", str(r.status_code), "\n", r.text
            #print "request history:", r.history
            msg = m.construct_message(r.text)
            #print msg, msg.args
            if msg:
                return msg
            else:
                return m.Message(m.T_ERR, {m.K_REASON : m.R_SERV_ERR, m.K_STATUS_CODE : r.status_code}, "invalid message from server.")
        except ValueError, e:
            return m.Message(m.T_ERR, {m.K_REASON : m.R_SERV_ERR}, "Error. Invalid message from server.")
        except requests.ConnectionError, e:
            return m.Message(m.T_ERR, {m.K_REASON : m.R_NO_CONN}, "Error: No connection to the server.")
        except Exception as inst:
            # TODO: Generate a bug report
            return m.Message(m.T_ERR, {m.K_REASON : m.R_SERV_ERR}, "Unclassified exception caught in __request():\nType: "+str(type(inst))+"\nArgs: "+str(inst))

    def __sort_response(self, response, caller):
        keys = response.args.keys()
        if response.type == m.T_ACK:
            pass
        elif response.type == m.T_RESPONSE:
            pass
        elif response.type == m.T_FAIL:
            if m.K_REASON in keys and response.args[m.K_REASON] == m.R_NOT_AUTH:
                self.__sid = None 
                self.__state = S_NOT_AUTH
            elif m.K_REASON in keys and (response.args[m.K_REASON] == m.R_UNAME_TAKEN or response.args[m.K_REASON] == m.R_INVALID_TOKEN) or response.args[m.K_REASON] == m.R_EMPTY:
                pass                 
            else:
                raise Exception(caller+' got unclassified failure from the server.')
        elif response.type == m.T_ERR and m.K_REASON in keys:
            # In case of error we can just return the response generated by self.__request
            pass
        else:
            raise Exception(caller+' got unexpected response from the server.')
        return response
    
def main():
    pass
    '''
    client = Client("suonto", "nahkanakki")
    h1 = scrypt.hash('password', 'random salt')
    h2 = scrypt.hash('password', 'random salt')
    print h1
    print h2
    auth_result = client.login()
    print auth_result.pay
    read_result = client.get_passwords()
    print read_result.pay
    store_result = client.store_password("facebook", "nahkakala")
    print store_result.pay
    read_result = client.get_passwords()
    print [(key, client.decrypt_rsa(read_result.args[key])) for key in read_result.args.keys()] 
    remove_result = client.remove_password("facebook")
    print remove_result.pay
    read_result = client.get_passwords()
    print read_result.pay
    logout_result = client.logout()
    print logout_result.pay
    '''

if __name__ == '__main__':
    main()
