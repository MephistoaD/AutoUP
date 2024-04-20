#!/usr/bin/env python3

import sys
import yaml
import json
from netbox import Netbox
from alertmanager import AlertManager
from pycron import *
from history import History
from semaphore import Semaphore
from html import Html

# Global variable to store parsed YAML content
CONFIG = None

def getConfig(file_path):
    global CONFIG
    try:
        # Open and read the YAML file
        with open(file_path, 'r') as file:
            CONFIG = yaml.safe_load(file)
            print(f"YAML content loaded from '{file_path}'")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")

def getInstances() -> list:
    instances = Netbox.getInstances(
            url=CONFIG['netbox']['url'],
            token=CONFIG['netbox']['token'],
            verify=CONFIG['netbox']['verify_certs']
        )

    alerts = AlertManager.getAlerts(
            url=CONFIG['alertmanager']['url'],
            verify=CONFIG['alertmanager']['verify_certs']
        )
    
    # add alerts to the instances list
    for instance in instances: instance.update(alerts.get(instance['name'], dict(triggers=[], inhibitors=[], trigger_severity=0)))
    
    # add list of instances depending on this one
    for instance in instances: instance['upgrade_before'] = [ item['name'] for item in instances if item['upgrade_after'] == instance['name'] ]

    factors = CONFIG['settings']['severity_factors']
    for instance in instances: instance.update(dict(
            # scores depending on the number of upgrades and the pool, penalized by the number of instances depending on it
            score=(instance['trigger_severity'] - len(instance['upgrade_before']))*factors[instance['pool']],
        ))
    for instance in instances: instance.update(dict(
            # parses and interprets the cron entry
            schedulable=isSchedulable(instance),
        ))

    instances_by_score = sorted(instances, key=lambda x: int(x['score']), reverse=True)
   
    return instances_by_score

def isSchedulable(instance):
    return is_now(instance['upgrade_schedule']) \
        and len(instance['inhibitors']) == 0 \
        and instance['score'] > 0

def previousRemainsRunning():
    history = History.getHistory(file_path=CONFIG['history']['file'])
    
    running_jobs = [ m for m in history if m['state'] not in ["SUCCESS", "ERROR"] ]

    for maintenance in running_jobs: 
        Semaphore.updateState(maintenance=maintenance, semaphore_config=CONFIG['semaphore'])
        History.writeMaintenance(maintenance=maintenance, file_path=CONFIG['history']['file'])

    running_jobs = [ m for m in history if m['state'] not in ["SUCCESS", "ERROR"] ]

    return len(running_jobs) > 0

def main():
    instances = getInstances()

    if CONFIG['settings']['debug']: print(json.dumps(instances, indent=2))

    # Is the last maintenance already finished?
    # store exit status
    if not previousRemainsRunning():


        # get the prioritized schedulable instance
        current_instance = next((instance for instance in instances if instance.get('schedulable')), None)

        if CONFIG['settings']['debug']: print(json.dumps(current_instance, indent=2))

        if CONFIG['settings']['trigger_jobs'] and current_instance:
            # schedule maintenance
            current_maintenance = Semaphore.triggerMaintenance(instance=current_instance, semaphore_config=CONFIG['semaphore'])

            if CONFIG['settings']['debug']: print(json.dumps(current_maintenance, indent=2))


            # write history
            History.writeMaintenance(maintenance=current_maintenance, file_path=CONFIG['history']['file'])


    # render html
    context = dict(
            instances=instances,
            history=History.getHistory(CONFIG['history']['file'])
        )
    Html.renderHtml(context=context, html_config=CONFIG['html'])
    
    


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    getConfig(file_path)

    # Example usage of CONFIG after loading
    if CONFIG:
        print("Parsed config correctly.")
        main()
