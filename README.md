IBroker
=======

This work is to wrap Interactive Broker's (IB) into Python. The key benefit of this exercise is to make algorithmic trading development easier by leveraging powerful python packages such as numpy, scipy, pandas, and so on. Instead of rewriting everything in Python, we choose to wrap underlying C++ into a python loadable module. We believe this approach is less error-prone.

How to Build
============

Prerequisites are cmake and boost with python support installed on your system.

Linux
-----

As long as you have boost and cmake in place, you can run following

```shell
cmake -G "Unix Makefiles"   # It will generate necessary C++ code and corresponding Makefile
make                        # Only run it if previous cmake find your boost library successfully!
```

Mac OS
------

On Mac OS X, we recommend to install cmake, boost and boost-python via [Homebrew](http://brew.sh/). For example,

```shell
brew install boost           # General Boost Package
brew install boost-python    # General Boost Package doesn't have python support
brew install cmake           # CMake
```

After that, you use same command as on Linux to build the module. One tricky thing is that the output on Mac is .dylib while Python always looks for .so file. Therefore, you need to rename it or create a soft link (IBroker.so).

Windows
-------

Haven't tested on Windows yet. However, ``CMakeLists.txt`` does not depend on particular platform. So we believe following the same principle, building on Windows is not hard.

A Simple Tutorial
=================

Consider following simple code. What it does is requesting market data of exchange ratio between EUR and USD, and then displaying the tick prices accordingly. 

```python
#!/usr/bin/env python

import IBroker  # You need to link/copy IBroker.so to the same directory 
import sys


class MyClient(IBroker.IBClient) :                 #define a new client class. All client classes are recommended to derive from IBClient unless you have special need.  
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
    succeed = c.connect("", port, clientID)                 # you need to connect to the server before you do anything.
    if succeed : 
        while(1):
            c.processMessages()                             # put this function into infinit loop. A better way is to put it into a new thread.
    else :
        print("Fail to connect TWS")
```

The code is pretty straightforward:

1. Connect to local TWS terminal. If you fails here, please check your TWS settings. Sometimes, TWS disables API by default
2. Setup input for request market data accordingly and then call ``reqMktData``.
3. Inside callback API (error, tickPrice), corresponding information is printed out.


Drawback
========

This work was intent to wrap IB's C++ API automatically. Therefore, all customized C++ code is generated by python script. By this approach, we hope we can deal with any future changes on IB's C++ API. However, the latest released API from IB adds complicated data structures, which makes this approach difficult if not impossible. Therefore, the underlying C++ API we are currently using is slightly older than latest one.

The good news that old APIs still works:). However, we need to figure out a way to handle the latest version.
