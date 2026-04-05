#!/usr/bin/env python3

import requests
import sys
import logging
import os
import re

API = "https://api.hetzner.cloud/v1"
HEADERS = {}

def get_zone_id(domain):
    zones = requests.get(f"{API}/zones", headers=HEADERS).json()
    
    for zone in zones["zones"]:
        if domain.endswith(zone["name"]):
            return zone["id"]
    
    logging.error(f"Could not find zone for {domain}")

    return None


def add_record(domain, name, value):
    zone_id = get_zone_id(domain)

    if not zone_id:
        sys.exit(1)

    data = {
        "name": name,
        "type": "TXT",
        "ttl": 180,
        "records": [
            {
                "value": f"\"{value}\""
            }
        ]
    }

    response = requests.post(f"{API}/zones/{zone_id}/rrsets", headers=HEADERS, json=data).json()
    
    error = response.get("error")
    if error:
        logging.error("%s %s %s", error["code"], error["message"], error["details"])


def remove_record(domain, name, value):
    zone_id = get_zone_id(domain)

    if not zone_id:
        return

    get_response = requests.get(f"{API}/zones/{zone_id}/rrsets/{name}/TXT", headers=HEADERS).json()

    error = get_response.get("error")
    if error:
        logging.info(f"Unable to find rrset {name} ({error['message']}), in which case there is nothing to remove")
        sys.exit(1)

    rrset = get_response.get("rrset")
    if not rrset:
        logging.error(f"rrset does not seem to be the first object in the result.")
        sys.exit(1)

    for record in rrset["records"]:
        if value in record["value"]:
            # since we now know that the rrset value exists, we'll remove it
            data = {
                "records": [
                    {
                        "value": f"\"{value}\""
                    }
                ]
            }
            remove_response = requests.post(f"{API}/zones/{zone_id}/rrsets/{name}/TXT/actions/remove_records", headers=HEADERS, json=data).json()
            if "error" in remove_response:
                error = remove_response.get("error")
                logging.error(f"Error trying to remove {value} record from {name}: {error['code']} {error['message']}")

            break


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

""" 
TrueNAS ACME DNS Authenticator for Hetzner
 Args:
    action (str): either "set" or "unset", the former adds the DNS entry whereas the latter removes it.
    domain (str): The domain name of the zone of which we want to add/remove DNS entries
    name (str): The name value for the TXT DNS entry
    value (str): The value for the TXT DNS entry
"""
if __name__ == "__main__":
    # this script expects 4 additional arguments from truenas (which totals to 5 including the script path)
    num_args = len(sys.argv)
    if num_args <= 4:
        logging.error(f"Total number of arguments passed does not meet expectations {num_args}/5")
        sys.exit(1)

    # map command-line arguments to variables
    action = sys.argv[1]
    # With hetzner, we only care about the top level domain for dns-01 challenges
    # Do note, this regex will **NOT** work with country-code top-level domains such as "co.uk"
    domain = re.search(r"([A-Za-z0-9][A-Za-z0-9\-]{0,62}[A-Za-z0-9]\.)*(?P<SLD>[A-Za-z0-9][A-Za-z0-9\-]{0,62}[A-Za-z0-9]\.[A-Za-z]+)", sys.argv[2]).group("SLD")
    # TrueNAS gives the entry name to us in the format of "_acme-challenge.domain.com", 
    # But hetzner expects only _acme-challenge as it appends .domain.com automatically when adding the DNS entry
    # Basically take everything up until the second level domain
    name = sys.argv[3][0:sys.argv[3].find(domain)-1]
    value = sys.argv[4]

    logging.info(f"Starting script with args:\n\tAction: {action}\n\tDomain: {domain}\n\tName: {name}\n\tValue: {value}")

    # get API key from environment variables
    api_key : str = None
    if num_args >= 6:
        api_key = sys.argv[5]

    if api_key == None:
        api_key = os.getenv("HETZNER_CLOUD_API_KEY")
        if api_key == None:
            logging.error("No hetzner cloud API key was provided, either add it as an environment variable or configure it in the bash script.")
            sys.exit(1)       
    
    if len(api_key) != 64:
        logging.error("Hetzner cloud API key is of invalid size, please check your API key")
        sys.exit(1)

    HEADERS = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if action == "set":
        add_record(domain, name, value)
    elif action == "unset":
        remove_record(domain, name, value)

