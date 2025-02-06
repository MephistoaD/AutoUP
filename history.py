import yaml
import jsonschema
from jsonschema import validate

"""
---
history: list(maintenance)
"""

class History(object):
    
    # Define the expected schema
    SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["id", "instance", "maintenance_url", "scheduled_at", "state", "target"],
            "properties": {
                "id": {"type": "integer"},
                "instance": {
                    "type": "object",
                    "required": [
                        "name", "nb_url", "pool", "role", "schedulable", "score",
                        "status", "trigger_severity", "triggers", "upgrade_after",
                        "upgrade_before", "upgrade_schedule",
#                        "vmid"
                    ],
                    "properties": {
                        "name": {"type": "string"},
                        "nb_url": {"type": "string", "format": "uri"},
                        "pool": {"type": "string"},
                        "role": {"type": "string"},
                        "schedulable": {"type": "boolean"},
                        "score": {"type": "integer"},
                        "status": {"type": "string"},
                        "trigger_severity": {"type": "integer"},
                        "triggers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["count", "name", "origin", "title"],
                                "properties": {
                                    "count": {"type": "string"},
                                    "name": {"type": "string"},
                                    "origin": {"type": "string"},
                                    "title": {"type": "string"}
                                }
                            }
                        },
                        "upgrade_after": {"type": ["string", "null"]},
                        "upgrade_before": {"type": "array"},
                        "upgrade_schedule": {"type": "string"},
#                        "vmid": {"type": "integer"},
                    }
                },
                "maintenance_url": {"type": "string"},
                "scheduled_at": {"type": "string"},
                "state": {"type": "string"},
                "target": {"type": "string"},
            }
        }
    }

    def writeMaintenance(file_path, maintenance, retention):
        history = History.getHistory(file_path=file_path)

        history = [item for item in history if item.get('id') != maintenance.get('id')]
        history.append(maintenance)

        history = sorted(history, key=lambda x: x['scheduled_at'], reverse=True)

        # slice the last elements
        history = history[0:retention]

        with open(file_path, 'w') as file:
            yaml.dump(history, file, default_flow_style=False)
        print(f"SUCCESS: Written history to {file_path} successfully")


    def getHistory(file_path) -> list:
        try:
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
                print(f"YAML content loaded from '{file_path}'")

            if not isinstance(data, list):
                print("Error: Expected a list of entries in the YAML file.")
                return

            valid_entries = []
            for entry in data:
                try:
                    validate(instance=entry, schema=History.SCHEMA["items"])
                    valid_entries.append(entry)
                except jsonschema.exceptions.ValidationError as e:
                    print(f"Removing invalid entry: {entry.get('id', 'Unknown ID')}, reason: {e.message}")

            if not valid_entries:
                print("No valid entries found in the YAML file.")
                return

        except yaml.YAMLError as e:
            print(f"YAML Parsing Error: {e}")
        
        return valid_entries
