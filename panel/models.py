from django.db import models
from django.utils.translation import gettext_lazy
import json
from .management.commands._update import Update
from django.utils import timezone
from datetime import datetime

# Create your models here.
class Instance(models.Model):
    name = models.CharField(max_length=255)

    def getOrCreate(name):
        try:
            existing = Instance.objects.get(name=name)
        except:
            instance = Instance(
                    name=name
                )
            instance.save()
            existing = Instance.objects.get(name=name)
        return existing
    
    def getJson(instance) -> dict:
        data = dict(instance)

        maintenances_qs = Maintenance.objects.filter(instance=instance['id']).order_by('-createdAt').values()

        maintenances = []
        for maintenance in maintenances_qs:
            maintenances.append(Maintenance.getJson(maintenance))

        current = maintenances[0]
        maintenances.remove(current)

        data['maintenances'] = dict(
            current=current,
            history=maintenances,
        )

        return data
        

class Maintenance(models.Model):
    class MaintenanceStatus(models.TextChoices):
        BLOCKED = "BL", gettext_lazy("BLOCKED")
        QUEUED = "QE", gettext_lazy("QUEUED")
        RUNNING = "RU", gettext_lazy("RUNNING")
        SUCCESS = "OK", gettext_lazy("SUCCESS")
        FAILED = "FA", gettext_lazy("FAILED")

# {"id":138,"template_id":2,"project_id":1,"status":"waiting","debug":false,"dry_run":false,"diff":false,"playbook":"","environment":"{\"target\":\"cloud-test\"}","limit":"","user_id":2,"created":"2024-03-03T22:12:20.077087121+01:00","start":null,"end":null,"message":"-\u003e 28.0.3","commit_hash":null,"commit_message":"","build_task_id":null,"version":null,"arguments":null}
    
    instance = models.ForeignKey(
            Instance,
            on_delete=models.CASCADE
        )
    createdAt = models.DateTimeField(auto_now_add=True)
    startsAt = models.DateTimeField(null=True)
    endsAt = models.DateTimeField(null=True)
    job = models.CharField(max_length=255) # Link to the semaphore job
    status = models.CharField(
            max_length=2,
            choices=MaintenanceStatus.choices,
            default=MaintenanceStatus.BLOCKED,
        )
    
    def getOrCreateCurrentForInstance(instance):
        try:
            existing = Maintenance.objects.get(instance=instance, endsAt=None)
        except:
            maintenance = Maintenance(
                instance=instance,
            )
            maintenance.save()
            existing = Maintenance.objects.get(instance=instance, endsAt=None)
            pass
        return existing
    
    def getJson(maintenance) -> dict:
        data = dict(maintenance)

        triggers = MaintenanceTrigger.getJson(maintenance)
        inhibitors = MaintenanceInhibitor.getJson(maintenance)

        data['triggers'] = triggers
        data['inhibitors'] = inhibitors

        data['createdAt'] = data['createdAt'].strftime("%Y/%m/%d, %H:%M") if len(triggers) > 0 else "Not required yet"
        data['startsAt'] = "Not started yet" if data['startsAt'] is None else data['startsAt'].strftime("%Y/%m/%d, %H:%M")
        data['endsAt'] = "Not ended yet" if data['endsAt'] is None else data['endsAt'].strftime("%Y/%m/%d, %H:%M")
        data['status'] = str(Maintenance.MaintenanceStatus(maintenance['status']).label)

        return data
  

class MaintenanceTrigger(models.Model):
    alertName = models.CharField(max_length=255)
    alertTitle = models.CharField(max_length=255)
    origin = models.CharField(max_length=255)
    instance = models.ForeignKey(
            Instance,
            on_delete=models.CASCADE
        )
    startsAt = models.DateTimeField(auto_now_add=True)
    endsAt = models.DateTimeField(null=True)
    fingerprint = models.CharField(max_length=255)
    handledInMaintenance = models.ForeignKey(
            Maintenance,
            on_delete=models.CASCADE
        )
    
    def updateOrCreate(data):
        maintenance = data['handledInMaintenance']
        trigger = MaintenanceTrigger(**data)
        try:
            existing = MaintenanceTrigger.objects.get(fingerprint=data['fingerprint'], handledInMaintenance=maintenance)
            print(f"found existing MaintenanceTrigger {data['alertName']}")
            trigger.id = existing.id
        except:
            print(f"creating new MaintenanceTrigger {data['alertName']}")
        trigger.save()

    def getJson(maintenance) -> list:
        triggers = list(MaintenanceTrigger.objects.filter(handledInMaintenance=maintenance['id']).order_by('alertName').values())

        for trigger in triggers:
            trigger['startsAt'] = trigger['startsAt'].strftime("%Y/%m/%d, %H:%M")
            trigger['endsAt'] = trigger['endsAt'].strftime("%Y/%m/%d, %H:%M")

        return triggers

  
class MaintenanceInhibitor(models.Model):
    alertName = models.CharField(max_length=255)
    alertTitle = models.CharField(max_length=255)
    instance = models.ForeignKey(
            Instance,
            on_delete=models.CASCADE
        )
    startsAt = models.DateTimeField(auto_now_add=True)
    endsAt = models.DateTimeField(null=True)
    fingerprint = models.CharField(max_length=255)
    handledInMaintenance = models.ForeignKey(
            Maintenance,
            on_delete=models.CASCADE
        )
    
    def updateOrCreate(data):
        trigger = MaintenanceInhibitor(**data)
        try:
            existing = MaintenanceInhibitor.objects.get(fingerprint=data['fingerprint'], handledInMaintenance=data['handledInMaintenance'])
            print(f"found existing MaintenanceInhibitor {data['alertName']}")
            trigger.id = existing.id
        except:
            print(f"creating new MaintenanceInhibitor {data['alertName']}")
        trigger.save()

    def getJson(maintenance) -> list:
        inhibitors = list(MaintenanceInhibitor.objects.filter(handledInMaintenance=maintenance['id']).order_by('alertName').values())

        for inhibitor in inhibitors:
            inhibitor['startsAt'] = inhibitor['startsAt'].strftime("%Y/%m/%d, %H:%M")
            end = inhibitor['endsAt'].strftime("%Y/%m/%d, %H:%M")
            active = (end == "1/01/01, 00:00" or inhibitor['endsAt'] > timezone.now())
            inhibitor['active'] = active
            inhibitor['endsAt'] = "still active" if inhibitor['active'] else end

        return inhibitors