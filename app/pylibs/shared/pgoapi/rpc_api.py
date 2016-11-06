"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

from __future__ import absolute_import

import os
import re
import time
import base64
import random
import logging
import requests
import subprocess
import six
import binascii
import ctypes

from google.protobuf import message

from importlib import import_module

from pgoapi.protobuf_to_dict import protobuf_to_dict
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException, ServerSideRequestThrottlingException, ServerSideAccessForbiddenException, UnexpectedResponseException, AuthTokenExpiredException, ServerApiEndpointRedirectException
from pgoapi.utilities import to_camel_case, get_time, get_format_time_diff, Rand48, long_to_bytes, f2i, \
    HashGenerator

from . import protos
from POGOProtos.Networking.Envelopes.RequestEnvelope_pb2 import RequestEnvelope
from POGOProtos.Networking.Envelopes.ResponseEnvelope_pb2 import ResponseEnvelope
from POGOProtos.Networking.Requests.RequestType_pb2 import RequestType
from POGOProtos.Networking.Envelopes.SignalAgglomUpdates_pb2 import SignalAgglomUpdates
from POGOProtos.Networking.Platform.Requests.SendEncryptedSignatureRequest_pb2 import SendEncryptedSignatureRequest


class RpcApi:

    RPC_ID = 0
    START_TIME = 0

    def __init__(self, auth_provider, device_info):

        self.log = logging.getLogger(__name__)

        self._auth_provider = auth_provider

        # mystical unknown6 - resolved by PokemonGoDev
        self._signal_agglom_gen = False
        self._signature_lib = None
        self._hash_engine = None

        if RpcApi.START_TIME == 0:
            RpcApi.START_TIME = get_time(ms=True)

        # data fields for SignalAgglom
        self.session_hash = os.urandom(16)
        self.token2 = random.randint(1,59)
        self.course = random.uniform(0, 360)

        self.device_info = device_info

    def activate_signature(self, signature_lib_path, hash_lib_path):
        try:
            self._signal_agglom_gen = True
            self._signature_lib = ctypes.cdll.LoadLibrary(signature_lib_path)
            self._hash_engine = HashGenerator(hash_lib_path)
        except:
            raise

    def get_rpc_id(self):
        if RpcApi.RPC_ID==0 :  #Startup
            RpcApi.RPC_ID=1
            if self.device_info is not None  and  \
               self.device_info.get('device_brand','Apple')!='Apple':
                rand=0x53B77E48
            else:
                rand=0x000041A7
        else:
            rand=random.randint(0,2**31)
        RpcApi.RPC_ID += 1
        cnt= RpcApi.RPC_ID
        reqid= ((rand| ((cnt&0xFFFFFFFF)>>31))<<32)|cnt
        self.log.debug("Incremented RPC Request ID: %s", reqid)

        return reqid

    def decode_raw(self, raw):
        output = error = None
        try:
            process = subprocess.Popen(['protoc', '--decode_raw'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            output, error = process.communicate(raw)
        except:
            output = "Couldn't find protoc in your environment OR other issue..."

        return output

    def get_class(self, cls):
        module_, class_ = cls.rsplit('.', 1)
        class_ = getattr(import_module(module_), class_)
        return class_

    def _make_rpc(self, endpoint, request_proto_plain):
        self.log.debug('Execution of RPC')

        request_proto_serialized = request_proto_plain.SerializeToString()
        #print binascii.hexlify(request_proto_serialized)
        try:
            http_response = self._session.post(endpoint, data=request_proto_serialized, timeout=30)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise ServerBusyOrOfflineException(e)

        return http_response

    def request(self, endpoint, subrequests, player_position):

        if not self._auth_provider or self._auth_provider.is_login() is False:
            raise NotLoggedInException()

        request_proto = self._build_main_request(subrequests, player_position)
        response = self._make_rpc(endpoint, request_proto)

        response_dict = self._parse_main_response(response, subrequests)

        self.check_authentication(response_dict)

        # some response validations
        if isinstance(response_dict, dict):
            status_code = response_dict.get('status_code', None)
            if status_code == 102:
                raise AuthTokenExpiredException()
            elif status_code == 52:
                raise ServerSideRequestThrottlingException("Request throttled by server... slow down man")
            elif status_code == 53:
                api_url = response_dict.get('api_url', None)
                if api_url is not None:
                    exception = ServerApiEndpointRedirectException()
                    exception.set_redirected_endpoint(api_url)
                    raise exception
                else:
                    raise UnexpectedResponseException()

        return response_dict

    def check_authentication(self, response_dict):
        if isinstance(response_dict, dict) and ('auth_ticket' in response_dict) and \
           ('expire_timestamp_ms' in response_dict['auth_ticket']) and \
           (self._auth_provider.is_new_ticket(response_dict['auth_ticket']['expire_timestamp_ms'])):

            had_ticket = self._auth_provider.has_ticket()

            auth_ticket = response_dict['auth_ticket']
            self._auth_provider.set_ticket(
                [auth_ticket['expire_timestamp_ms'], base64.standard_b64decode(auth_ticket['start']), base64.standard_b64decode(auth_ticket['end'])])

            now_ms = get_time(ms=True)
            h, m, s = get_format_time_diff(now_ms, auth_ticket['expire_timestamp_ms'], True)

            if had_ticket:
                self.log.debug('Replacing old Session Ticket with new one valid for %02d:%02d:%02d hours (%s < %s)', h, m, s, now_ms, auth_ticket['expire_timestamp_ms'])
            else:
                self.log.debug('Received Session Ticket valid for %02d:%02d:%02d hours (%s < %s)', h, m, s, now_ms, auth_ticket['expire_timestamp_ms'])

    def _build_main_request(self, subrequests, player_position=None):
        self.log.debug('Generating main RPC request...')

        request = RequestEnvelope()
        request.status_code = 2
        request.request_id = self.get_rpc_id()
        request.accuracy = random.choice((5, 5, 5, 5, 10, 10, 10, 30, 30, 50, 65, random.uniform(66,80)))

        if player_position:
            request.latitude, request.longitude, altitude = player_position

        # generate sub requests before SignalAgglomUpdates generation
        request = self._build_sub_requests(request, subrequests)

        ticket = self._auth_provider.get_ticket()
        if ticket:
            self.log.debug('Found Session Ticket - using this instead of oauth token')
            request.auth_ticket.expire_timestamp_ms, request.auth_ticket.start, request.auth_ticket.end = ticket
            ticket_serialized = request.auth_ticket.SerializeToString()

        else:
            self.log.debug('No Session Ticket found - using OAUTH Access Token')
            request.auth_info.provider = self._auth_provider.get_name()
            request.auth_info.token.contents = self._auth_provider.get_access_token()
            request.auth_info.token.unknown2 = self.token2
            ticket_serialized = request.auth_info.SerializeToString()  #Sig uses this when no auth_ticket available

        if self._signal_agglom_gen:
            sig = SignalAgglomUpdates()

            sig.location_hash_by_token_seed = self._hash_engine.generate_location_hash_by_seed(ticket_serialized, request.latitude, request.longitude, request.accuracy)
            sig.location_hash = self._hash_engine.generate_location_hash(request.latitude, request.longitude, request.accuracy)

            for req in request.requests:
                hash = self._hash_engine.generate_request_hash(ticket_serialized, req.SerializeToString())
                sig.request_hashes.append(hash)

            sig.field22 = self.session_hash
            sig.epoch_timestamp_ms = get_time(ms=True)
            sig.timestamp_ms_since_start = get_time(ms=True) - RpcApi.START_TIME
            if sig.timestamp_ms_since_start < 5000:
                sig.timestamp_ms_since_start = random.randint(5000, 8000)

            loc = sig.location_updates.add()
            sen = sig.sensor_updates.add()

            sen.timestamp = random.randint(sig.timestamp_ms_since_start - 5000, sig.timestamp_ms_since_start - 100)
            loc.timestamp_ms = random.randint(sig.timestamp_ms_since_start - 30000, sig.timestamp_ms_since_start - 1000)

            loc.name = random.choice(('network', 'network', 'network', 'network', 'fused'))
            loc.latitude = request.latitude
            loc.longitude = request.longitude

            if not altitude:
                loc.altitude = random.triangular(300, 400, 350)
            else:
                loc.altitude = altitude

            if random.random() > .95:
                # no reading for roughly 1 in 20 updates
                loc.device_course = -1
                loc.device_speed = -1
            else:
                self.course = random.triangular(0, 360, self.course)
                loc.device_course = self.course
                loc.device_speed = random.triangular(0.2, 4.25, 1)

            loc.provider_status = 3
            loc.location_type = 1
            if request.accuracy >= 65:
                loc.vertical_accuracy = random.triangular(35, 100, 65)
                loc.horizontal_accuracy = random.choice((request.accuracy, 65, 65, random.uniform(66,80), 200))
            else:
                if request.accuracy > 10:
                    loc.vertical_accuracy = random.choice((24, 32, 48, 48, 64, 64, 96, 128))
                else:
                    loc.vertical_accuracy = random.choice((3, 4, 6, 6, 8, 12, 24))
                loc.horizontal_accuracy = request.accuracy

            sen.acceleration_x = random.triangular(-3, 1, 0)
            sen.acceleration_y = random.triangular(-2, 3, 0)
            sen.acceleration_z = random.triangular(-4, 2, 0)
            sen.magnetic_field_x = random.triangular(-50, 50, 0)
            sen.magnetic_field_y = random.triangular(-60, 50, -5)
            sen.magnetic_field_z = random.triangular(-60, 40, -30)
            sen.magnetic_field_accuracy = random.choice((-1, 1, 1, 2, 2, 2, 2))
            sen.attitude_pitch = random.triangular(-1.5, 1.5, 0.2)
            sen.attitude_yaw = random.uniform(-3, 3)
            sen.attitude_roll = random.triangular(-2.8, 2.5, 0.25)
            sen.rotation_rate_x = random.triangular(-6, 4, 0)
            sen.rotation_rate_y = random.triangular(-5.5, 5, 0)
            sen.rotation_rate_z = random.triangular(-5, 3, 0)
            sen.gravity_x = random.triangular(-1, 1, 0.15)
            sen.gravity_y = random.triangular(-1, 1, -.2)
            sen.gravity_z = random.triangular(-1, .7, -0.8)
            sen.status = 3

            sig.field25 = ctypes.c_uint64(-8408506833887075802).value

            if self.device_info:
                for key in self.device_info:
                    setattr(sig.device_info, key, self.device_info[key])
                if self.device_info['device_brand'] == 'Apple':
                    sig.ios_device_info.bool5 = True
            else:
                sig.ios_device_info.bool5 = True

            signal_agglom_proto = sig.SerializeToString()

            sig_request = SendEncryptedSignatureRequest()
            sig_request.encrypted_signature = self._generate_signature(signal_agglom_proto, sig.timestamp_ms_since_start)
            plat = request.platform_requests.add()
            plat.type = 6
            plat.request_message = sig_request.SerializeToString()

        request.ms_since_last_locationfix = int(random.triangular(300, 30000, 10000))

        self.log.debug('Generated protobuf request: \n\r%s', request)

        return request

    def _generate_signature(self, signature_plain, iv):
        self._signature_lib.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
        self._signature_lib.restype = ctypes.c_int
        rounded_size = len(signature_plain) + (256 - (len(signature_plain) % 256));
        total_size = rounded_size + 5;
        output = ctypes.POINTER(ctypes.c_ubyte * total_size)()
        #print binascii.hexlify(signature_plain)
        output_size = self._signature_lib.encrypt(signature_plain, len(signature_plain), iv, ctypes.byref(output))
        #print binascii.hexlify(output.contents)
        signature = b''.join(list(map(lambda x: six.int2byte(x), output.contents)))
        return signature

    def _build_sub_requests(self, mainrequest, subrequest_list):
        self.log.debug('Generating sub RPC requests...')

        for entry in subrequest_list:
            if isinstance(entry, dict):

                entry_id = list(entry.items())[0][0]
                entry_content = entry[entry_id]

                entry_name = RequestType.Name(entry_id)

                proto_name = to_camel_case(entry_name.lower()) + 'Message'
                proto_classname = 'POGOProtos.Networking.Requests.Messages.' + proto_name + '_pb2.' + proto_name
                subrequest_extension = self.get_class(proto_classname)()

                self.log.debug("Subrequest class: %s", proto_classname)

                for (key, value) in entry_content.items():
                    if isinstance(value, list):
                        self.log.debug("Found list: %s - trying as repeated", key)
                        for i in value:
                            try:
                                self.log.debug("%s -> %s", key, i)
                                r = getattr(subrequest_extension, key)
                                r.append(i)
                            except Exception as e:
                                self.log.warning('Argument %s with value %s unknown inside %s (Exception: %s)', key, i, proto_name, e)
                    elif isinstance(value, dict):
                        for k in value.keys():
                            try:
                                r = getattr(subrequest_extension, key)
                                setattr(r, k, value[k])
                            except Exception as e:
                                self.log.warning('Argument %s with value %s unknown inside %s (Exception: %s)', key, str(value), proto_name, e)
                    else:
                        try:
                            setattr(subrequest_extension, key, value)
                        except Exception as e:
                            try:
                                self.log.debug("%s -> %s", key, value)
                                r = getattr(subrequest_extension, key)
                                r.append(value)
                            except Exception as e:
                                self.log.warning('Argument %s with value %s unknown inside %s (Exception: %s)', key, value, proto_name, e)

                subrequest = mainrequest.requests.add()
                subrequest.request_type = entry_id
                subrequest.request_message = subrequest_extension.SerializeToString()

            elif isinstance(entry, int):
                subrequest = mainrequest.requests.add()
                subrequest.request_type = entry
            else:
                raise Exception('Unknown value in request list')

        return mainrequest

    def _parse_main_response(self, response_raw, subrequests):
        self.log.debug('Parsing main RPC response...')

        if response_raw.status_code == 403:
            raise ServerSideAccessForbiddenException("Seems your IP Address is banned or something else went badly wrong...")
        elif response_raw.status_code == 502:
            raise ServerBusyOrOfflineException("502: Bad Gateway")
        elif response_raw.status_code != 200:
            error = 'Unexpected HTTP server response - needs 200 got {}'.format(response_raw.status_code)
            self.log.warning(error)
            self.log.debug('HTTP output: \n%s', response_raw.content.decode('utf-8'))
            raise UnexpectedResponseException(error)

        if response_raw.content is None:
            self.log.warning('Empty server response!')
            return False

        response_proto = ResponseEnvelope()
        try:
            response_proto.ParseFromString(response_raw.content)
        except message.DecodeError as e:
            self.log.warning('Could not parse response: %s', e)
            return False

        self.log.debug('Protobuf structure of rpc response:\n\r%s', response_proto)
        try:
            self.log.debug('Decode raw over protoc (protoc has to be in your PATH):\n\r%s', self.decode_raw(response_raw.content).decode('utf-8'))
        except:
            self.log.debug('Error during protoc parsing - ignored.')

        response_proto_dict = protobuf_to_dict(response_proto)
        response_proto_dict = self._parse_sub_responses(response_proto, subrequests, response_proto_dict)

        return response_proto_dict

    def _parse_sub_responses(self, response_proto, subrequests_list, response_proto_dict):
        self.log.debug('Parsing sub RPC responses...')
        response_proto_dict['responses'] = {}

        if response_proto_dict.get('status_code', 1) == 53:
            exception = ServerApiEndpointRedirectException()
            exception.set_redirected_endpoint(response_proto_dict['api_url'])
            raise exception

        if 'returns' in response_proto_dict:
            del response_proto_dict['returns']

        list_len = len(subrequests_list)-1
        i = 0
        for subresponse in response_proto.returns:
            if i > list_len:
                self.log.info("Error - something strange happend...")

            request_entry = subrequests_list[i]
            if isinstance(request_entry, int):
                entry_id = request_entry
            else:
                entry_id = list(request_entry.items())[0][0]

            entry_name = RequestType.Name(entry_id)
            proto_name = to_camel_case(entry_name.lower()) + 'Response'
            proto_classname = 'POGOProtos.Networking.Responses.' + proto_name + '_pb2.' + proto_name

            self.log.debug("Parsing class: %s", proto_classname)

            subresponse_return = None
            try:
                subresponse_extension = self.get_class(proto_classname)()
            except Exception as e:
                subresponse_extension = None
                error = 'Protobuf definition for {} not found'.format(proto_classname)
                subresponse_return = error
                self.log.debug(error)

            if subresponse_extension:
                try:
                    subresponse_extension.ParseFromString(subresponse)
                    subresponse_return = protobuf_to_dict(subresponse_extension)
                except:
                    error = "Protobuf definition for {} seems not to match".format(proto_classname)
                    subresponse_return = error
                    self.log.debug(error)

            response_proto_dict['responses'][entry_name] = subresponse_return
            i += 1

        return response_proto_dict
