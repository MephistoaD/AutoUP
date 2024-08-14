import requests
import json

class Netbox(object):

    def getInstances(url, token, verify=True):
        # Define API endpoints for devices and virtual machines
        devices_url = f'{url}/api/dcim/devices/'
        vms_url = f'{url}/api/virtualization/virtual-machines/'

        result = []

        raw = Netbox.getRaw(devices_url, token, verify=verify)
        for instance in raw:
            upgrade_after = instance['custom_fields']['upgrade_after']
            if upgrade_after:
                upgrade_after = upgrade_after['name']
            result.append(dict(
                    name=instance['name'], # unique id
                    nb_url=instance['url'],
                    role=instance['device_role']['name'],
                    status=instance['status']['label'],
                    upgrade_schedule=instance['custom_fields']['upgrade_schedule'],
                    pool=instance['custom_fields']['pool'],
                    upgrade_after=upgrade_after,
                ))

        raw = Netbox.getRaw(vms_url, token, verify=verify)
        for instance in raw:
            upgrade_after = instance['custom_fields']['upgrade_after']
            if upgrade_after:
                upgrade_after = upgrade_after['name']
            result.append(dict(
                    name=instance['name'], # unique id
                    nb_url=instance['url'],
                    role=instance['role']['name'],
                    status=instance['status']['label'],
                    upgrade_schedule=instance['custom_fields']['upgrade_schedule'],
                    pool=instance['custom_fields']['pool'],
                    vmid=instance['custom_fields']['vmid'],
                    upgrade_after=upgrade_after,
                ))
            
        return result

    def getRaw(url, token, verify=True):
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        }

        try:
            # Make GET request to retrieve devices
            instance_response = requests.get(url, headers=headers, verify=verify)
            instance_data = instance_response.json()

            # Process and return the instances data
            instances = instance_data['results'] if 'results' in instance_data else []

            return instances

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from NetBox API: {e}")
            return []
