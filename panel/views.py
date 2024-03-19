from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.db.models import Q
import json


def index(request):
    instances_qs = Instance.objects.all().order_by('name').values()

    instances = []
    for instance in instances_qs:
        instances.append(Instance.getJson(instance))
    
    template = loader.get_template('index.html')
    context = {
        'instances': instances,
    }

    print(json.dumps(context, indent=4))
    return HttpResponse(template.render(context, request))

def details(request, id):
    instance = Instance.objects.filter(id=id).values()[0]
    instance = Instance.getJson(instance)
    
    print(json.dumps(instance, indent=4))

    template = loader.get_template('details.html')
    context = {
        'instance': instance,
    }
    print(json.dumps(context, indent=4))
    return HttpResponse(template.render(context, request))

@require_POST
@csrf_exempt
def webhooks_alertmanager(request):
    print("webhook triggered")
    body = json.loads(request.body)
    print(json.dumps(body, indent=4))

    status = 200
    message = "Data received."

    for alert in body['alerts']:
        print(f"processing {alert['labels']['alertname']}...")
        try:
            alertType = alert['labels']['autoup']
            data = dict(
                    alertName = alert['labels']['alertname'],
                    alertTitle = alert['annotations']['title'],
                    instance = alert['labels']['instance'],
                    startsAt = alert['startsAt'],
                    endsAt = alert['endsAt'],
                    fingerprint = alert['fingerprint'],
                )
        except Exception as e:
            print(f"Exception: {e}")
            status = 500
            message = "Invalid upload"
            return HttpResponse(message, status=status)

        print(json.dumps(data, indent=4))

        data['instance'] = Instance.getOrCreate(name=data['instance'])

        data['handledInMaintenance'] = Maintenance.getOrCreateCurrentForInstance(data['instance'])
        if data['handledInMaintenance'].status == Maintenance.MaintenanceStatus.BLOCKED:
            if alertType == "trigger":
                print("store trigger")
                data['origin'] = alert['labels']['origin']
                MaintenanceTrigger.updateOrCreate(data)
                
            elif alertType == "inhibitor":
                print("store inhibitor")
                MaintenanceInhibitor.updateOrCreate(data)
            else:
                print(f"Invalid value for label autoup: {alertType}")
        else:
            print(f"Skipping {data['handledInMaintenance'].status.label} maintenance")

    return HttpResponse(message, status=status)