from ndn.appv2 import NDNApp
from ndn.encoding import Component, MetaInfo, Name, NonStrictName, Signer, TlvModel, UintField, make_data
from ndn.transport.nfd_registerer import NfdRegister
from ndn.transport.prefix_registerer import PrefixRegisterer
from ndn import utils, security, types
from ndn.app_support import nfd_mgmt
from .prefix_announce_lib import create_announcement_object
import asyncio
import random


async def announce_prefix(app: NDNApp, name: NonStrictName, interest_signer: Signer, pa_signer: Signer,
                          expiration: int = 24 * 3600_000) -> bool:
    """
    Announce a prefix (unofficial method written as an extension to python-ndn)

    Parameter usage similar to register_prefix.

    Expiration should be in milliseconds(?)

    See https://redmine.named-data.net/projects/nfd/wiki/PrefixAnnouncement/
    """

    # the official way to fix any and all race conditions
    await asyncio.sleep(random.random())

    name = Name.normalize(name)
    registerer_base: PrefixRegisterer = app.registerer
    if not isinstance(registerer_base, NfdRegister):
        raise TypeError('The prefix registerer associated with the app is not an NFD Registerer')

    registerer: NfdRegister = registerer_base

    async def pass_all(_name, _sig, _context):
        return types.ValidResult.PASS

    async with registerer._prefix_register_semaphore:
        for _ in range(10):
            now = utils.timestamp()
            if now > registerer._last_command_timestamp:
                registerer._last_command_timestamp = now
                break
            await asyncio.sleep(0.001)
        try:
            ann_obj = create_announcement_object(name, pa_signer, expiration)

            _, reply, _ = await app.express(
                name='/localhop/nfd/rib/announce',
                app_param=ann_obj, signer=interest_signer,
                validator=pass_all,
                lifetime=1000)
            ret = nfd_mgmt.parse_response(reply)
            if ret['status_code'] != 200:
                print(f'Announcement for {Name.to_str(name)} failed: {ret["status_code"]} {ret["status_text"]}', flush=True)
                return False
            else:
                print(f'Announcement for {Name.to_str(name)} succeeded: {ret["status_code"]} {ret["status_text"]}', flush=True)
                return True
        except (types.InterestNack, types.InterestTimeout, types.InterestCanceled, types.ValidationFailure) as e:
            print(f'Announcement for {Name.to_str(name)} failed: {e.__class__.__name__}', flush=True)
            return False
