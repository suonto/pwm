'''
Created on 15.8.2013

@author: suonto
'''
import sqlite3
import message as m
from Crypto.Cipher import AES
from Crypto.Random import _UserFriendlyRNG as rng
import logging
from logger_setup import LoggerBuilder
import atexit
import os

# Key for symmetric database encryption.
# Symmetric encryption is not really even necessary.
# DB_KEY = 'a3040e0afdb2a4f08d263e55f589f5e5c98fc7ea718c925fd8d8f9ec20bb5309'.decode('hex')
DB_KEY = open("db_key").read().rstrip('\n').decode('hex')
CREDENTIALS = "CREDENTIALS"
UPDATED = "UPDATED"
ADDED = "ADDED"

class Database(object):

    def __init__(self, logfile=None, debug=False):
        self.__conns = {} # username:connection
        self.__logger = LoggerBuilder().build_logger("Database", logfile=logfile, debug=debug)
        self.__logger.info("The database has been initialized.")
        self.__demos = {}
        atexit.register(self.__confirm_demo_user_deletion)
    
    def __confirm_demo_user_deletion(self):
        for uname in self.__demos.keys():
            self.delete_user(uname)
        
    def __get_db_conn(self, uname):
        '''
        Returns an open connection object to the parameter user's database.
        If the connection is not open, it will be opened and returned.
        '''
        self.__logger.debug("We are opening connection to db "+uname+".")
        if not uname in self.__conns.keys():
            conn = sqlite3.connect(uname)
            self.__conns[uname] = conn
            return conn
        else:
            return self.__conns[uname]
    
    def __close_db_conn(self, uname):
        '''
        Closes the connection (if open) to parameter users database.
        '''
        try:
            self.__logger.debug("We are closing connection to db "+uname+".")
            self.__conns[uname].close()
            del self.__conns[uname]
        except Exception as e:
            self.__logger.error("We caught an exception in close_conn:\nType: "+str(type(e))+"\nArgs: "+e.__str__())

    def __pad_data(self, data):
        while len(data)%16 != 0:
            data = data+" "
        return data

    def store_user_credentials(self, uname, password_hash_hex):
        '''
        Stores a user's credential info for authentication purposes. 
        '''
        conn = self.__get_db_conn(CREDENTIALS)
        cursor = conn.cursor() 
        added = False
        updated = False
        #Create the table for credentials if it doesn't already exist.
        cursor.execute("create table if not exists "+CREDENTIALS+" (username text, password text)")
        #Insert into credentials table if user was not already there.
        if not cursor.execute("select * from "+CREDENTIALS+" where username=?", (uname,)).fetchone():
            cursor.execute("insert into "+CREDENTIALS+" values (?,?)", (uname, password_hash_hex,))
            conn.commit()
            added = True   
            self.__logger.info("We have successfully registered "+uname+".")
        else:
            cursor.execute("update "+CREDENTIALS+" set password=? where username=?", (password_hash_hex, uname,))
            conn.commit()
            updated = True 
            self.__logger.info("We have updated "+uname+"'s password in credentials library.")
        self.__close_db_conn(CREDENTIALS)
        if added:
            return ADDED
        elif updated:
            return UPDATED
        else:
            raise Exception('Store user credentials neither updated or added anything.')

    def get_user_credentials(self):
        conn = self.__get_db_conn(CREDENTIALS)
        # We are avoiding any complications in opening and closing the connection.
        result = self.__get_user_credentials(conn)
        self.__close_db_conn(CREDENTIALS)
        return result

    def __get_user_credentials(self, conn):
        '''
        Reads user credentials and returns them in a dictionary.
        '''
        cursor = conn.cursor()
        exists = cursor.execute("select name from sqlite_master where type='table' and name='"+CREDENTIALS+"'").fetchall()
        if len(exists) == 0:
            self.__logger.info("We don't have any registered users. Returning {}.")
            return {}    
        credentials = cursor.execute("select * from "+CREDENTIALS).fetchall()    
        dict_format = {}
        for tuple in credentials:
            dict_format[str(tuple[0])] = str(tuple[1])
        credentials = dict_format
        self.__logger.info("We are reading credentials.")
        self.__logger.debug("Credentials: "+str(credentials))
        return credentials

    def add_password(self, uname, identifier, pwd):
        '''
        Stores a password in the users database.
        Opens a connection to the db if neccessary.
        '''
        iv = rng.get_random_bytes(16)
        ec = AES.new(DB_KEY, AES.MODE_CBC, iv)
        #Encrypting the password for storage
        pwd = ec.encrypt(self.__pad_data(pwd)).encode('hex')
        conn = self.__get_db_conn(uname)
        cursor = conn.cursor()
        added = False
        #Create the table for the user if it doesn't already exist.
        cursor.execute("create table if not exists sites (id text, iv text, password text)")
        #Insert into db if identifier is not already there.
        if not cursor.execute("select * from sites where id=?", (identifier.encode('hex'),)).fetchone():
            #IV and ID encoded in hex for storage.
            self.__logger.debug("We are adding a new password "+identifier+" for user "+uname+".")
            cursor.execute("insert into sites values (?,?,?)",(identifier.encode('hex'), iv.encode('hex'), pwd,))
        # Else update pwd value.
        else:
            cursor.execute("update sites set iv=? ,password=? where id=?", (iv.encode('hex'), pwd, identifier.encode('hex'),))
            self.__logger.debug("We have updated "+uname+"'s password "+identifier+".")
        conn.commit()
        added = True   
        self.__close_db_conn(uname)
        return added

    def read_passwords(self, uname):
        '''
        Reads all the passwords of the parameter user and returns them in a list.
        '''
        conn = self.__get_db_conn(uname)
        # We are avoiding any complications in opening and closing the connection.
        result = self.__read_passwords(conn, uname)
        self.__close_db_conn(uname)
        return result

    def __read_passwords(self, conn, uname):        
        self.__logger.info("We are reading passwords for "+uname+".")
        cursor = conn.cursor()
        exists = cursor.execute("select name from sqlite_master where type='table' and name='sites'").fetchall()
        if len(exists) == 0:
            self.__logger.info("We have no passwords for "+uname+" Returning {}.")
            return {} 
        passwords = cursor.execute("select * from sites").fetchall()
        self.__logger.info("Read for "+uname+" successful.")
        self.__logger.debug("Passwords:")
        result = {}
        for line in passwords:
            iv_hex = str(line[1])
            id_hex = line[0]
            dc = AES.new(DB_KEY, AES.MODE_CBC, iv_hex.decode('hex'))
            password = dc.decrypt(line[2].decode('hex')).rstrip(' ')
            self.__logger.debug([id_hex.decode('hex'), iv_hex, password])
            result[id_hex.decode('hex')] = password 
        return result
            
    def delete_password(self, uname, identifier):
        self.__logger.info("We are trying to delete "+uname+"'s password "+identifier+".")
        conn = self.__get_db_conn(uname)
        cursor= conn.cursor()
        removed = False
        exists = cursor.execute("select name from sqlite_master where type='table' and name='sites'").fetchall()
        if len(exists) == 0:
            self.__logger.info("We have no passwords for "+uname+". Returning False.")
            return False
        if cursor.execute("select * from sites where id=?", (identifier.encode('hex'),)).fetchone():
            cursor.execute("delete from sites where id=?", (identifier.encode('hex'),))
            conn.commit()
            removed = True
            self.__logger.info("We are deleting user "+uname+"'s password "+identifier)
            #If table is empty after removal, it is dropped.
            if not cursor.execute("select * from sites").fetchone():
                cursor.execute("drop table sites")
                conn.commit()
                self.__logger.debug("We are deleting user "+uname+"'s empty table sites.")
        self.__close_db_conn(uname)
        return removed

    def delete_user(self, uname):
        self.__logger.info("We are deleting user "+uname+".")
        conn = self.__get_db_conn(uname)
        cursor= conn.cursor()
        cursor.execute("drop table if exists sites")
        self.__logger.debug("We are dropping table sites if it exists.")
        conn.commit()
        try:
            os.remove(uname)
        except:
            pass
        self.__close_db_conn(uname)
        conn = self.__get_db_conn(CREDENTIALS)
        cursor= conn.cursor()
        removed = False
        exists = cursor.execute("select name from sqlite_master where type='table' and name='"+CREDENTIALS+"'").fetchall()
        if len(exists) == 0:
            self.__logger.info("We don't have any registered users. Returning False.")
            return False  
        if cursor.execute("select * from "+CREDENTIALS+" where username=?", (uname,)).fetchone():
            cursor.execute("delete from "+CREDENTIALS+" where username=?", (uname,))
            conn.commit()
            removed = True
            self.__logger.info("We have deleted user "+uname+".")
            #If table is empty after removal, it is dropped.
            if not cursor.execute("select * from "+CREDENTIALS).fetchone():
                cursor.execute("drop table "+CREDENTIALS)
                conn.commit()
                self.__logger.debug("We are deleting empty table "+CREDENTIALS+".")
        else:
            self.__logger.debug("We didn't delete "+uname+", he's gone already.")
        self.__close_db_conn(CREDENTIALS)
        return removed

    def generate_demo_user(self):
        if len(self.__demos.keys()) > 10:
            return None
        demo = {}
        dname = "demo_"+str(len(self.__demos.keys())) 
        dpass = rng.get_random_bytes(20).encode('hex')
        demo[m.K_USER] = dname 
        demo[m.K_DEMO_PASS] = dpass
        self.__demos[dname] = dpass
        return demo
 

if __name__ == '__main__':
    db = Database(debug=True)
    #print rng.get_random_bytes(32).encode('hex')
    #f = open("db_password")
    #pwd = f.read()
    #print [pwd.rstrip('\n').decode('hex')]
    #db.add_password("suonto", "facebook", "kakkakala")
    #db.read_passwords("suonto")
    #db.delete_password("suonto", "facebook")
    #db.store_user_credentials("suonto", "b86dda2ddb35f8bb836f84a17bf4f523f0d3501ddcddf656676b25cea7788ba8")
    #db.get_user_credentials()
    #db.delete_user(uname)



        
    
    
