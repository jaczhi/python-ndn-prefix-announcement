#!/bin/bash

echo "Starting route monitor. Press Ctrl+C to stop."
echo "Checking routes every second..."

# Main loop
while true; do
  # Step 1: Get the route list
  routes=$(nfdc route list origin prefixann)

  # Only proceed if we found routes
  if [[ -n "$routes" ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Found routes with origin=prefixann"

    # Step 2: Parse output and remove routes
    echo "Removing existing routes..."
    while IFS= read -r line; do
      if [[ "$line" =~ prefix=([^ ]+)\ nexthop=([0-9]+)\ origin=prefixann ]]; then
        prefix="${BASH_REMATCH[1]}"
        nexthop="${BASH_REMATCH[2]}"

        echo "  Removing route: $prefix via nexthop $nexthop"
        nfdc route remove prefix "$prefix" nexthop "$nexthop" origin prefixann
      fi
    done <<< "$routes"

    # Step 3: Add new routes with modified parameters
    echo "Adding new routes with 'client' origin and 'capture' flag..."
    while IFS= read -r line; do
      if [[ "$line" =~ prefix=([^ ]+)\ nexthop=([0-9]+)\ origin=prefixann\ cost=([0-9]+) ]]; then
        prefix="${BASH_REMATCH[1]}"
        nexthop="${BASH_REMATCH[2]}"
        cost="${BASH_REMATCH[3]}"

        echo "  Adding route: $prefix via nexthop $nexthop with cost $cost"
        nfdc route add prefix "$prefix" nexthop "$nexthop" origin client cost "$cost" capture
      fi
    done <<< "$routes"

    echo "Route update completed."
  else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No routes with origin=prefixann found"
  fi

  # Wait for 1 second before the next iteration
  sleep 1
done
