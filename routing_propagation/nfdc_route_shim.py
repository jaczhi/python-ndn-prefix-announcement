from ndn import types, encoding
import subprocess
import re
from typing import Optional


class RouteProperties:
    prefix: encoding.Name
    next_hop: int | str
    origin: str
    cost: int
    child_inherit: bool
    capture: bool
    expires: int


def list_routes(origin: Optional[str] = None) -> list[RouteProperties]:
    command = ["nfdc", "route", "list"] + (
        [] if origin is None else ["origin", origin]
    )

    command_result = subprocess.run(command, capture_output=True, text=True)

    routes = []

    def parse_timestamp(ts):
        match = re.match(r'^\d+', ts)
        if match:
            return int(match.group(0)) * 1_000
        return -1

    for route_str in command_result.stdout.split('\n'):
        properties_split = list(filter(lambda p: p.strip() and p.find('=') != -1,
                                       route_str.strip().split(' ')))
        properties = dict([
            tuple(p.strip().split('=', 1)) for p in properties_split
        ])

        route = RouteProperties()

        route.prefix = encoding.Name.from_str(properties['prefix'])
        route.next_hop = int(properties['nexthop']) if properties['nexthop'].isdigit() else properties['nexthop']
        route.origin = properties['origin']
        route.cost = int(properties['cost'])

        route.child_inherit = route_str.find('child-inherit') != -1
        route.capture = route_str.find('capture') != -1

        route.expires = parse_timestamp(properties['expires'])

        routes.append(route)

    return routes


def add_route(route: RouteProperties) -> None:
    command = ["nfdc", "route", "add"]
    command += ["prefix", route.prefix]
    command += ["nexthop", str(route.next_hop)]
    command += ["origin", route.origin]
    command += ["cost", str(route.cost)]
    command += ["no-inherit"] if not route.child_inherit else []
    command += ["capture"] if route.capture else []
    command += ["expires", str(route.expires)] if route.expires > 0 else []

    subprocess.run(command, capture_output=True)
