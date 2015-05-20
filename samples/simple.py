#!/usr/bin/env python

import IBroker  # You need to link/copy IBroker.so to the same directory 
import sys


class MyClient(IBroker.IBClient) :                             #  define a new client class. All client classes are recommended to derive from IBClient unless you have special need.  
    def setup(self):
        self.state = "initial"

    def connect(self, ip, port, ID):
        if ip == '' :
            ip = "127.0.0.1"
        return self.eConnect(ip, port, ID);

    def error(self, ID, errorCode, errorString) :
        print("ID%d (%d) : %s" % (ID, errorCode, errorString))

    def tickPrice(self, TickerId, tickType, price, canAutoExecute):
        '''
        This function will be called once price changes automatically
        '''
        print("TicketId='%d'" % TickerId)
        print("TicketType='%s'" % tickType)
        print("price='%f'" % price)
        print("canAutoExecute='%d'" % canAutoExecute)

    def runStrategy(self) :
        '''
        This should be your trading strategy's main entry. It will be called at the beginning of processMessages()
        '''
        if self.state == "initial":
            contract = IBroker.Contract()
            contract.symbol = 'EUR'
            contract.secType = "CASH"
            contract.exchange = "IDEALPRO"
            contract.primaryExchange = "IDEALPRO"
            contract.currency = 'USD'
            #contract.symbol = "TSLA"
            #contract.secType = "STK"
            #contract.exchange = "SMART"
            #contract.primaryExchange = "NASDAQ"
            self.reqMktData(888, contract, '221', False)    # Once it called, market data will flow-in and corresponding events will be tricked automatically. 
            self.state = "datareqed"                        # change the state so that you won't request the same data again. 


if __name__ == '__main__' :
    port = int(sys.argv[1])
    if len(sys.argv[1:]) > 1 :
        clientID = int(sys.argv[2])
    else :
        clientID = 0

    c = MyClient()                                          # create a client object
    c.setup();                                              # additional setup. It's optional.
    succeed = c.connect("", port, clientID)                           # you need to connect to the server before you do anything.
    if succeed : 
        while(1):
            c.processMessages()                                 # put this function into infinit loop. A better way is to put it into a new thread.
    else :
        print("Fail to connect TWS")


