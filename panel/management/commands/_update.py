import requests
from django.conf import settings

class Update:
    url = 'http://192.168.2.216:3000/api/project/1/tasks'
    url_user = 'http://192.168.2.216:3000/project/1/history?t='

    headers = {
            "Authorization": f"Bearer {settings.UPDATE_API_TOKEN}"
        }

    def start(name):
        data = {
            'template_id': 2,
            'message': f'AutoUp: {name}',
            'environment': f'{{"target":"{name}"}}',
            'project_id': 1
        }

        response = requests.post(settings.UPDATE_API_URL, headers=Update.headers, json=data, verify=False)
        
        id = response.json()['id']

        return f"{settings.UPDATE_DISPLAY_URL}{id}"


    def getStatus(link, bg):
        url = f"{settings.UPDATE_API_URL}/{link.split(settings.UPDATE_DISPLAY_URL)[-1]}"
        bg.stdout.write(bg.style.NOTICE(f" | Requesting {url}"))
        response = requests.get(url, headers=Update.headers, verify=False)

        status = response.json()['status']

        status = status.replace("waiting", "queued")
        status = status.replace("error", "failed")
        status = status.replace("success", "success")
        status = status.replace("running", "running")

        return status