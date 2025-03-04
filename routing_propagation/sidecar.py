import argparse
from typing import Any
import asyncio
import json
from ndn import appv2, security
from inbound import InboundHandler
from outbound import OutboundHandler

app = appv2.NDNApp()
keychain = app.default_keychain()
config: dict[str, Any] = dict()


def load_arg_objects():
    parser = argparse.ArgumentParser(description="Process keychain and TPM paths")

    parser.add_argument('--config', type=str, required=True,
                        help='Path to routing_propagation.json')
    parser.add_argument('--keychain_path', type=str, required=True,
                        help='Path to the sqlite keychain database')
    parser.add_argument('--tpm_path', type=str, required=True,
                        help='Path to the TPM file')

    args = parser.parse_args()

    with open(args.config, 'r') as config_file:
        global config
        config = json.load(config_file)

    tpm = security.TpmFile(args.tpm_path)

    global keychain
    keychain = security.KeychainSqlite3(args.keychain_path, tpm)


async def main():
    inbound = InboundHandler(config, keychain)
    await app.register(config['sidecar_prefix'])
    app.attach_handler(config['sidecar_prefix'], inbound.on_inbound_interest)

    outbound = OutboundHandler(app, config, keychain)
    await outbound.outbound_main()


if __name__ == '__main__':
    app.run_forever(after_start=main())
