from typing import Any, Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.encoding import BinaryStr, FormalName, Component, Name, MetaInfo, make_data, parse_data
from ndn.security import NullSigner
from ndn.security import Keychain
from ndn.app_support import security_v2
from nfdc_route_shim import add_route, RouteProperties

import sys
sys.path.append('..')
from prefix_announce_lib import parse_announcement


class InboundHandler:
    def __init__(self, config: dict[str, Any], keychain: Keychain):
        self._config = config
        self._keychain = keychain

    def on_inbound_interest(self, name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc,
                            context: PktContext) -> None:
        nack_data = make_data(name + [Component.from_str('nack')], MetaInfo(), bytes(),
                              self._keychain.get_signer(self._config['sidecar_signer']))
        ok_data = make_data(name, MetaInfo(), bytes(),
                            self._keychain.get_signer(self._config['sidecar_signer']))

        if not app_param:
            reply(nack_data)
            return

        announce_name, exp, sigs = parse_announcement(app_param)

        key_locator_name = sigs.signature_info.key_locator.name
        if not any([n['key'] == Name.to_str(key_locator_name) for n in self._config['neighbors']]):
            reply(nack_data)
            return

        # TODO: check signature

        neighbor = next(n for n in self._config['neighbors'] if n['key'] == Name.to_str(key_locator_name))

        # Check inbound rules
        if not any([Name.is_prefix(Name.from_str(p), announce_name) for p in neighbor['inbound']]):
            reply(nack_data)
            return

        # Find face and add locally
        route = RouteProperties()
        route.prefix = announce_name
        route.next_hop = neighbor['face']
        route.origin = "prefixann"
        route.cost = 2048
        route.child_inherit = True
        route.capture = False
        route.expires = exp

        add_route(route)

        reply(ok_data)
