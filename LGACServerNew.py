#!/usr/bin/python3
import sys
import os

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)

from gevent import monkey
monkey.patch_all()

import msgpack
from gevent.queue import Queue
from gevent.pool import Group
from gevent.server import StreamServer
import argparse
from msgpack import Unpacker
import time
import signal
from logging.handlers import RotatingFileHandler
import logging
import wideq
import math
import enum


parser = argparse.ArgumentParser()
parser.add_argument('--acDevNum', type=str, help='AC Device Number', default='put here dev num')
parser.add_argument('--token', type=str, help='Refresh Token', default='put here token')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=22233)
args = parser.parse_args()

send = Queue()
receive = Queue()
sockets = {}

#### LOGGING

# fh = RotatingFileHandler(os.path.join(os.path.dirname(__file__), '.', 'log/server.log'), maxBytes=1024 * 1024, backupCount=5)
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(logging.Formatter("%(asctime)s [%(process)s]:%(levelname)s:%(name)-10s| %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))

s = logging.StreamHandler(sys.stdout)
s.setLevel(logging.DEBUG)
s.setFormatter(logging.Formatter("server: %(message)s"))

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
# logger.addHandler(fh)
logger.addHandler(s)

#### ./LOGGING

### for run as service
def signal_handler(signum=None, frame=None):
    time.sleep(10)
    sys.exit(0)
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
    signal.signal(sig, signal_handler)
### ./for run as service


def socket_incoming_connection(socket, address):

    logger.debug('connected %s', address)

    sockets[address] = socket

    unpacker = Unpacker(encoding='utf-8')
    while True:
        data = socket.recv(4096)

        if not data:
            logger.debug('closed connection %s', address)
            break

        unpacker.feed(data)

        for msg in unpacker:
            receive.put(InMsg(msg, address))
            logger.debug('got socket msg: %s', msg)

    sockets.pop(address)


def socket_msg_sender(sockets, q):
    while True:
        msg = q.get()
        if isinstance(msg, OutMsg) and msg.to in sockets:
            sockets[msg.to].sendall(msgpack.packb(msg, use_bin_type=True))
            logger.debug('send reply %s', msg.to)



def ac_commands_handler(acDevNum, token, q):
    client = wideq.Client.from_token(token)
    device=client.get_device(acDevNum)
    if device.type != wideq.DeviceType.AC:
        logger.debug('This is not an AC device.')
        return
    ac = wideq.ACDevice(client, device)
    connRefresh=0
    try:
        ac.monitor_start()
        while True:
            msg = q.get()
            try:
                cmd = msg.pop(0)
                if hasattr(ACCommand, cmd):
                    connRefresh +=1
                    result = getattr(ACCommand, cmd)(ac, *msg)
                    if 'exception' in result:
                        if result['exception'] == 'no response':
                            print('Client refreshing')
                            client.refresh()
                            ac.monitor_start()
                    if connRefresh > 10:
                        print('Monitor restart')
                        ac.monitor_stop()
                        client.refresh()
                        ac.monitor_start()
                        connRefresh=0
                else:
                    result = {'exception': 'command [%s] not found' % cmd} 
            except (Exception) as e:
                result = {'exception': 'python-LGAC: %s' % e}
                continue
            finally:
                result.update({'cmd': cmd})
                logger.debug('ac result %s', result)
                send.put(OutMsg(result, msg.to))
    except KeyboardInterrupt:
        pass
    finally:
        ac.monitor_stop()
        print('AC connection STOP')

class ACCommand(object):

    @classmethod
    def status(cls, ac):
        try:
            state = ac.poll()
        except wideq.NotLoggedInError:
            return {
                'exception': 'no response'
            }
        if state:
            return {
                'state' : '{1}'.format(state,'on' if state.is_on else 'off'),
                'mode' : '{0.mode.name}'.format(state,'on' if state.is_on else 'off'),
                'temp_actual' : '{0.temp_cur_c}'.format(state,'on' if state.is_on else 'off'),
                'temp_setpoint' : '{0.temp_cfg_c}'.format(state,'on' if state.is_on else 'off'),
                'wind_strength': state.data['WindStrength'],
                'air_ionizer': state.data['AirClean']
            }
        return {'code':'None Response'}
        
    @classmethod
    def set_Temp(cls, ac, level):
        return {'code': ac.set_celsius(level)}
    
    @classmethod
    def turn_AC(cls, ac, state):
        return {'code': ac.set_on(state == 'on')}
    
    @classmethod
    def turn_Ionizer(cls, ac, state):
        return {'code': ac.set_ionizer(state == 'on')}
    
    @classmethod    
    def set_Mode(cls, ac, modeName):
        mode = wideq.ACMode[modeName]
        return {'code': ac.set_mode(mode)}
    
    @classmethod
    def set_Wind(cls, ac, levelName):
        name = wideq.ACWst[levelName]
        return {'code': ac.set_wind(name)}
    
    @classmethod 
    def check_Filter(cls, ac):
        fstatus = ac.get_filter_state()
        usedTime=float(fstatus['UseTime'])
        period=float(fstatus['ChangePeriod'])
        return {'filter_percentage_state': math.ceil((period-usedTime)/period*100)}



class InMsg(list):
    def __init__(self, data, to, **kwargs):
        super(InMsg, self).__init__(**kwargs)
        self.extend(data)
        self.to = to


class OutMsg(dict):
    def __init__(self, data, to, **kwargs):
        super(OutMsg, self).__init__(**kwargs)
        self.update(data)
        self.to = to


if __name__ == '__main__':

    server = StreamServer((args.host, args.port), socket_incoming_connection)
    logger.debug('Starting server on %s %s' % (args.host, args.port))

    services = Group()
    services.spawn(server.serve_forever)
    services.spawn(ac_commands_handler, args.acDevNum, args.token, receive)
    services.spawn(socket_msg_sender, sockets, send)
    services.join()

