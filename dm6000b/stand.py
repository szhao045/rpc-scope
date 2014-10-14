# The MIT License (MIT)
#
# Copyright (c) 2014 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Erik Hvatum, Zach Pincus

from rpc_acquisition import message_device
from rpc_acquisition.dm6000b.microscopy_method_names import (MICROSCOPY_METHOD_NAMES, MICROSCOPY_METHOD_NAMES_TO_IDXS)

GET_ALL_METHODS = 70026
GET_ACT_METHOD = 70028
SET_ACT_METHOD = 70029

class Stand(message_device.LeicaAsyncDevice):
    def get_all_microscopy_methods(self):
        '''Returns a dict of microscopy method names to bool values indicating whether the associated
        microscopy method is available.'''
        method_mask = list(self.send_message(GET_ALL_METHODS, async=False, intent='get mask of available microscopy methods').response.strip())
        method_dict = {}
        # Note that the mask returned by the scope in response to GET_ALL_METHODS is reversed
        for method, is_available in zip(MICROSCOPY_METHOD_NAMES, list(reversed(method_mask))):
            method_dict[method] = bool(int(is_available))
        return method_dict

    def get_active_microscopy_method(self):
        method_idx = int(self.send_message(GET_ACT_METHOD, async=False, intent='get name of currently active microscopy method').response)
        return MICROSCOPY_METHOD_NAMES[method_idx]

    def set_active_microscopy_method(self, microscopy_method_name):
        if microscopy_method_name not in MICROSCOPY_METHOD_NAMES_TO_IDXS:
            raise KeyError('Value specified for microscopy method name must be one of {}.'.format([name for name, is_available in self.get_all_microscopy_methods().items() if is_available]))
        response = self.send_message(SET_ACT_METHOD, MICROSCOPY_METHOD_NAMES_TO_IDXS[microscopy_method_name], intent='switch microscopy methods')