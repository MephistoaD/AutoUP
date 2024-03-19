from django.core.management.base import BaseCommand, CommandError
from panel.models import *
from django.conf import settings
from datetime import timedelta

import json
import requests

class Command(BaseCommand):
    help = 'Runs the background logic'

    def add_arguments(self, parser):
        #parser.add_argument('poll_id', nargs='+', type=int)
        pass

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting background tasks..."))
        
        maintenances = Maintenance.objects.filter(endsAt=None).values()

        for maintenance in maintenances:
            maintenance = Maintenance.getJson(maintenance)
            maintenance_obj = Maintenance.objects.get(id=maintenance['id'])
            print(maintenance_obj)
            self.stdout.write(self.style.NOTICE(f"Processing maintenance {maintenance['id']}:"))

            if maintenance['status'] == "BLOCKED":
                active_inhibitor_exists = not any(inhibitor.get('active') for inhibitor in maintenance['inhibitors']) and len(maintenance['inhibitors']) != 0
                if len(maintenance['triggers']) == 0:
                    self.stdout.write(self.style.NOTICE(f" | Maintenance has no triggers."))
                    self.stdout.write(self.style.NOTICE(f" | ignoring."))
                elif active_inhibitor_exists:
                    self.stdout.write(self.style.NOTICE(f" | Maintenance blocked by inhibitor(s)."))
                    self.stdout.write(self.style.NOTICE(f" | ignoring."))
                else:
                    self.stdout.write(self.style.NOTICE(f" | Starting triggered maintenance..."))
                    instance = Instance.objects.filter(id=maintenance['instance_id']).values()[0]

                    maintenance_obj.job = Update.start(name=instance['name'])
                    maintenance_obj.status = Maintenance.MaintenanceStatus.QUEUED
                    maintenance_obj.startsAt = timezone.now()
                    maintenance_obj.save()
                    self.stdout.write(self.style.NOTICE(f" | Started maintenance at {maintenance_obj.job}"))
                    

            elif maintenance['status'] in ["QUEUED","RUNNING"]:

                print(json.dumps(maintenance, indent=4))

                self.stdout.write(self.style.NOTICE(f" | Maintenance found {'QUEUED' if maintenance['status'] == 'QE' else 'RUNNING'}"))

                stateMapping = dict(
                    queued=Maintenance.MaintenanceStatus.QUEUED,
                    running=Maintenance.MaintenanceStatus.RUNNING,
                    success=Maintenance.MaintenanceStatus.SUCCESS,
                    failed=Maintenance.MaintenanceStatus.FAILED
                )
                status = Update.getStatus(maintenance_obj.job, self)
                maintenance_obj.status = stateMapping[status]
                
                maintenance_ended = (maintenance_obj.status == Maintenance.MaintenanceStatus.SUCCESS or
                                    maintenance_obj.status == Maintenance.MaintenanceStatus.FAILED)

                if (maintenance_ended):
                    maintenance_obj.endsAt = timezone.now()
                
                # happens last to ensure all related tasks are done properly
                maintenance_obj.save()
                self.stdout.write(self.style.NOTICE(f" | Updated maintenance {maintenance_obj.job} to status {maintenance_obj.status.label}"))

                if (maintenance_ended):
                    self.cooldown(
                            instance=maintenance_obj.instance,
                            status=status,
                        )

                
    def cooldown(self, instance, status):
        STATUS = status.upper()
        COOLDOWN_HOURS = settings.COOLDOWN_HOURS[STATUS]

        self.stdout.write(self.style.NOTICE(f" | Creating cooldown of {COOLDOWN_HOURS} hours ({STATUS})..."))

        data = dict(
                alertName = f"Cooldown after maintenance ({STATUS} -> {COOLDOWN_HOURS}h)",
                alertTitle = "Created after maintenance",
                instance = instance,
                startsAt = timezone.now(),
                endsAt = timezone.now() + timedelta(hours=COOLDOWN_HOURS),
                fingerprint = "",
            )

        data['handledInMaintenance'] = Maintenance.getOrCreateCurrentForInstance(data['instance'])

        self.stdout.write(self.style.NOTICE(f" | Storing cooldown..."))
        MaintenanceInhibitor.updateOrCreate(data)
        self.stdout.write(self.style.NOTICE(f" | Cooldown stored."))

        pass

# def perform(self):
#         instance = Instance.objects.filter(id=self.instance.id).values()[0]
#         self.jobId = Update.start(name=instance['name'])
#         self.status = Maintenance.MaintenanceStatus.QUEUED
#         self.startsAt = datetime.now()
#         self.save()

#     def updateState(self):
#         stateMapping = dict(
#             queued=Maintenance.MaintenanceStatus.QUEUED,
#             running=Maintenance.MaintenanceStatus.RUNNING,
#             success=Maintenance.MaintenanceStatus.SUCCESS,
#             failed=Maintenance.MaintenanceStatus.FAILED
#         )
#         status = Update.getStatus(self.jobId)
#         self.status = stateMapping[status]
        
#         if (self.status == Maintenance.MaintenanceStatus.SUCCESS or
#             self.status == Maintenance.MaintenanceStatus.FAILED):
#             self.endsAt = datetime.now()
        
#         self.save()


