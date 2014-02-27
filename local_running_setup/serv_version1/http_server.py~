from twisted.web import http
from twisted.internet import reactor
from server import Server

class MyRequestHandler(http.Request):
    
    def process(self):
        print "kala"
        headers = self.requestHeaders
        header_dict = self.getAllHeaders()
        #self.write('%s\n'%("front-end-https" in header_dict.keys()))
        #self.write('%s\n'%(header_dict["x-real-ip"] == "83.201.213.197"))
        #self.write("%s\n"%header_dict["x-real-ip"])
        if self.method == "POST":    
            #self.write("method:\n")
            #self.write(self.method)
            #self.write("\nuri:\n")
            #self.write(self.uri)
            #self.write("\npath:\n")            
            #self.write(self.path)
            #self.write("\nargs:\n")
            #self.write(self.args)
            #print dir(self)
            if self.content:
                request = self.content.getvalue()
                self.write(serv.respond(request))
        else:
            self.write("<html>")
            self.write("This site is under construction.</br>At the moment I have nothing to show to you, sorry.")
            '''
            self.write(dict.__str__())
            self.write("<h1>Page %s<h1>"%self.path)
    

            if len(self.args)>0:
                self.write("<h2>Arguments:</h2>")
                for key,value in self.args.items():
                    self.write("<b>%s</b> : %s <br>"%(key,value))

            self.write("<h2>Request headers:</h2>")
            for key,value in headers.getAllRawHeaders():
                self.write("<b>%s</b> : %s <br>"%(key,value))
            '''
            self.write("<html>")
        

        self.finish()

class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp

if __name__ == '__main__':
    serv = Server()
    reactor.listenTCP(23450, MyHttpFactory())
    reactor.run()
