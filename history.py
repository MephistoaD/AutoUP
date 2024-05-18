import yaml, os

"""
---
history: list(maintenance)
"""

class History(object):

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
        result = []
        try:
            # Open and read the YAML file
            with open(file_path, 'r') as file:
                result = yaml.safe_load(file)
                print(f"YAML content loaded from '{file_path}'")
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
        
        return result
    
