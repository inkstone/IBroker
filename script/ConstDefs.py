ibClientHeader = \
'''#ifndef IBCLIENT_HPP
#define IBCLIENT_HPP
#include <ctime>
#include <string>
#include <memory>
#include "Contract.h"
#include "EWrapper.h"
#include "EPosixClientSocketPlatform.h"
#include "EPosixClientSocket.h"

class IBClient : public EWrapper
{
public:
\tIBClient(): m_pClient(new EPosixClientSocket(this)), timeOutSecs(5){};
\t~IBClient(){};
'''

ibClientTail = \
'''

protected:
\tstd::shared_ptr<EPosixClientSocket> m_pClient;
\tlong timeOutSecs; 
};

#endif
'''

ibClientWrapperHeader = \
'''#ifndef IBCLIENT_WRAPPER_HPP
#define IBCLIENT_WRAPPER_HPP
#include "Contract.h"
#include "Execution.h"
#include "ScannerSubscription.h"
#include "OrderState.h"
#include "CommissionReport.h"
#include "IBClient.hpp"
#include <boost/python.hpp>
using namespace boost::python;

struct IBClientWrapper : public IBClient, wrapper<IBClient>
{

'''


ibClientWrapperTail = \
'''
};

#endif
'''

wrapperTemplate = \
'''
\t{3} {0}{1}{{
\t\tif (override {0} = this->get_override("{0}")) {{
\t\t\t{4}{2};{5}
\t\t}}
\t\t{4}IBClient::{2};
\t}}
\t{3} default_{0}{1} {{
\t\t{4}this->IBClient::{2};
\t}}
'''

ibrokerHead = \
'''#include <string>
#include "IBClientWrapper.hpp"

BOOST_PYTHON_MODULE(IBroker)
{
'''

ibrokerTail = \
'''
}
'''

# Some extra APIs need to be exposed.
extraAPI = []
    ## [{'return' : 'void',     'name' : 'onSend',     'paramList' : ['']}, \
    ##  {'return' : 'void',     'name' : 'onReceive',  'paramList' : ['']}, \
    ##  {'return' : 'void',     'name' : 'onError',    'paramList' : ['']}  \
    ## ]

# We need to export additional data structure for external usage.    
otherDataStructure = \
    [{'file' : 'Contract.h',                  'name' : ['Contract', 'ContractDetails'],   'type' : 'struct'},
     {'file' : 'Execution.h',                 'name' : ['Execution', 'ExecutionFilter'],  'type' : 'struct'},
     {'file' : 'Order.h',                     'name' : ['Order'],                         'type' : 'struct'},
     {'file' : 'OrderState.h',                'name' : ['OrderState'],                    'type' : 'struct'},
     {'file' : 'ScannerSubscription.h',       'name' : ['ScannerSubscription'],           'type' : 'struct'},
     {'file' : 'CommissionReport.h',          'name' : ['CommissionReport'],              'type' : 'struct'},
     {'file' : 'EWrapper.h',                  'name' : ['TickType'],                      'type' : 'enum'}
     ]

# These interfaces are defined in customized code in below.
customizedAPI = \
    [{'return' : 'void',     'name' : 'processMessages',     'paramList' : ['']}, \
     {'return' : 'void',     'name' : 'disconnect',          'paramList' : ['']}, \
     {'return' : 'void',     'name' : 'runStrategy',         'paramList' : ['']}, \
     {'return' : 'void',     'name' : 'setTimeOutSecs',      'paramList' : ['long t']}, \
     {'return' : 'long',     'name' : 'getTimeOutSecs',      'paramList' : ['']}, \
     {'return' : 'bool',     'name' : 'connect',             'paramList' : ['const std::string& host', 'unsigned int port', 'int clientId']}  \
    ]
  

# A customized code took and revised according to sample code provided by Interactive Broker.
customizedCode = \
'''
\tvirtual void processMessages()
\t{
\t\tfd_set readSet, writeSet, errorSet;
\t\tstruct timeval tval;
\t\ttval.tv_sec = timeOutSecs;
\t\ttval.tv_usec = 0;

\t\trunStrategy();
\t\tif( m_pClient->fd() >= 0 ) {
\t\t\tFD_ZERO( &readSet);
\t\t\terrorSet = writeSet = readSet;
\t\t\tFD_SET( m_pClient->fd(), &readSet);
\t\t\tif( !m_pClient->isOutBufferEmpty())
\t\t\t\tFD_SET( m_pClient->fd(), &writeSet);
\t\t\tFD_CLR( m_pClient->fd(), &errorSet);
\t\t\tint ret = select( m_pClient->fd() + 1, &readSet, &writeSet, &errorSet, &tval);
\t\t\tif( ret == 0) { // timeout
\t\t\t\treturn;
\t\t\t}
\t\t\tif( ret < 0) { // error
\t\t\t\tdisconnect();
\t\t\t\treturn;
\t\t\t}
\t\t\tif( m_pClient->fd() < 0)
\t\t\t\treturn;
\t\t\tif( FD_ISSET( m_pClient->fd(), &errorSet)) { // error on socket
\t\t\t\tm_pClient->onError();
\t\t\t}
\t\t\tif( m_pClient->fd() < 0)
\t\t\t\treturn;
\t\t\tif( FD_ISSET( m_pClient->fd(), &writeSet)) { // socket is ready for writing
\t\t\t\tm_pClient->onSend();
\t\t\t}
\t\t\tif( m_pClient->fd() < 0)
\t\t\t\treturn;
\t\t\tif( FD_ISSET( m_pClient->fd(), &readSet)) { // socket is ready for reading
\t\t\t\tm_pClient->onReceive();
\t\t\t}
\t\t}
\t}

\tvirtual void setTimeOutSecs(long t){timeOutSecs = t;}
\tvirtual long getTimeOutSecs() {return timeOutSecs;}

\tvirtual void runStrategy() {}

\tvirtual void disconnect()
\t{
\t\tm_pClient->eDisconnect();
\t}

\tvirtual bool connect(const std::string &host, unsigned int port, int clientId)
\t{
\t\t// trying to connect
\t\tstd::string address = host=="" ? "127.0.0.1" : host;
\t\treturn m_pClient->eConnect( host.c_str(), port, clientId);
\t}
'''
