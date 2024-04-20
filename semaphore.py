import requests, json
from datetime import datetime


class Semaphore(object):

    def triggerMaintenance(instance, semaphore_config): 
        target = []
        if instance['upgrade_after']:
            target.append(instance['upgrade_after'])
        target.append(instance['name'])
        target = json.dumps(target)
        
        post_body = {
            'template_id': semaphore_config['template_id'],
            "message": f"AutoUp: {target}",
            "environment": "{\"target\":\"" + target.replace("\"", "\'") + "\"}",
            "project_id": semaphore_config['project_id']
        }
        
        data = Semaphore.post(
                url=f"{semaphore_config['url']}/api/project/{semaphore_config['project_id']}/tasks",
                bearer_token=semaphore_config['token'],
                body=post_body
            )

        print(f"Scheduled maintenance for targets {target} with id {data['id']}")

        maintenance = dict(
            id=data['id'],
            target=target,
            instance=instance,
            scheduled_at=datetime.now().strftime("%Y/%m/%d %H:%M"),
            maintenance_url=f"{semaphore_config['url']}/project/{semaphore_config['project_id']}/history?t={data['id']}",
            state="RUNNING",
        )
        return maintenance

    def updateState(maintenance, semaphore_config): 
        
        data = Semaphore.get(
                url=f"{semaphore_config['url']}/api/project/{semaphore_config['project_id']}/tasks/{maintenance['id']}",
                bearer_token=semaphore_config['token'],
            )

        maintenance['state'] = data['status'].upper()

        return maintenance

    def get(url, bearer_token):
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None

    def post(url, bearer_token, body):
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None
