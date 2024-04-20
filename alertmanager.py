import requests, json

class AlertManager(object):


    def getAlerts(url, verify=True):
        raw = AlertManager.getRaw(url, verify=verify)

        result = {}
        for instance in raw:
            if instance['receiver']['name'] == "autoup":
                data = dict(
                        triggers=[],
                        inhibitors=[],
                    )
                

                for alert in instance['alerts']:
                    count = alert['annotations']['count'] if 'count' in alert['annotations'] else "-1"
                    data[f'{alert["labels"]["autoup"]}s'].append(dict(
                            name=alert['labels']['alertname'],
                            title=alert['annotations']['title'],
                            origin=alert['labels'].get('origin'),
                            count=count,
                        ))
                    
                data['trigger_severity'] = sum(int(trigger['count']) for trigger in data['triggers'])
        
                result[instance['labels']['instance']] = data
        return result

    def getRaw(url, verify=True):
        try:
            response = requests.get(f"{url}/api/v2/alerts/groups", verify=verify)
            response.raise_for_status()  # Raise an HTTPError for bad status codes
            alerts = response.json()  # Assuming the response is JSON
            return alerts
        except requests.exceptions.RequestException as e:
            print(f"Error fetching alerts from {url}: {e}")
            return None
