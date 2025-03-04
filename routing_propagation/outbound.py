import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext, pass_all
from ndn.encoding import BinaryStr, FormalName, Component, Name, MetaInfo, make_data, parse_data
from ndn.security import NullSigner
from ndn.security import Keychain
from ndn.app_support import security_v2
from nfdc_route_shim import add_route, list_routes, RouteProperties

import sys
sys.path.append('..')
from prefix_announce_lib import create_announcement_object


class OutboundHandler:
    def __init__(self, app: NDNApp, config: dict[str, Any], keychain: Keychain):
        self._app = app
        self._config = config
        self._keychain = keychain

        self._processed: dict[str, datetime] = dict()

    @staticmethod
    def _is_later(time1, time2, margin_seconds=1):
        margin = timedelta(seconds = margin_seconds)
        return time1 > (time2 + margin)

    async def outbound_main(self):
        routes = list_routes("prefixann")

        for route in routes:
            new_expiry = datetime.now() + timedelta(seconds=route.expires)
            if (route.prefix not in self._processed or
                    self._is_later(new_expiry, self._processed[route.prefix])):
                await self.propagate(route)
                self._processed[route.prefix] = new_expiry

        await asyncio.sleep(30)
        task = asyncio.create_task(self.outbound_main())

    async def propagate(self, route: RouteProperties):
        announce_name = route.prefix
        for neighbor in self._config['neighbors']:
            if not any([Name.is_prefix(Name.from_str(p), announce_name) for p in neighbor['outbound']]):
                continue

            interest_signer = self._keychain.get_signer(self._config['sidecar_signer'])
            pa_signer = self._keychain.get_signer(neighbor['outbound_signer'])

            pa_obj = create_announcement_object(announce_name, pa_signer, route.expires)

            # TODO: validate interest response
            await self._app.express(neighbor['outbound_sidecar_prefix'] + [Component.from_str(str(uuid.uuid4()))],
                                    pass_all,
                                    pa_obj,
                                    interest_signer)  # We don't need to observe the result of a notification
