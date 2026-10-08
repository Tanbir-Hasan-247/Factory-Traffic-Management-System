import uuid

from django.db import transaction
from rest_framework.exceptions import ValidationError, NotFound

from .models import (
    JunctionRecord,
    Vehicle,
    ProcessedEvent,
    ControllerCommand,
    AuditLog,
    current_milli_time,
)

PRIORITIES = {"EMERGENCY": 1000, "TRUCK": 10, "FORKLIFT": 5, "EMPLOYEE_VEHICLE": 1}

VALID_DIRECTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}


class TrafficService:

    @staticmethod
    def get_queue_map(junction_or_id):
        queue_map = {"NORTH": 0, "SOUTH": 0, "EAST": 0, "WEST": 0}

        if isinstance(junction_or_id, JunctionRecord):
            for vehicle in junction_or_id.vehicles.all():
                direction = vehicle.direction
                if direction in queue_map:
                    queue_map[direction] += 1
        else:
            vehicles = Vehicle.objects.filter(junction_id=junction_or_id).values(
                "direction"
            )
            for vehicle in vehicles:
                direction = vehicle["direction"]
                if direction in queue_map:
                    queue_map[direction] += 1

        return queue_map

    @staticmethod
    def restore_mode(junction):

        if junction.controller_status != "ONLINE":
            junction.mode = "DEGRADED"

        elif junction.emergency_direction:
            junction.mode = "EMERGENCY"

        elif junction.manual_direction:
            junction.mode = "MANUAL"

        else:
            junction.mode = "AUTOMATIC"

    @staticmethod
    def process_manual_command(junction_id, command, direction=None):

        with transaction.atomic():

            try:
                junction = JunctionRecord.objects.select_for_update().get(
                    pk=junction_id
                )

            except JunctionRecord.DoesNotExist:
                raise NotFound("Junction not found.")

            if command == "MANUAL_GREEN_REQUEST":

                junction.manual_direction = direction

                if junction.controller_status != "ONLINE":
                    junction.mode = "DEGRADED"

                elif junction.mode != "EMERGENCY":
                    junction.mode = "MANUAL"

                junction.save()

                AuditLog.objects.create(
                    junction_id=junction_id,
                    event_type="MANUAL_OVERRIDE",
                    details={"direction": direction},
                )

            elif command == "RETURN_TO_AUTOMATIC":

                junction.manual_direction = None

                TrafficService.restore_mode(junction)

                junction.save()

                AuditLog.objects.create(
                    junction_id=junction_id,
                    event_type="RETURN_TO_AUTOMATIC",
                    details={},
                )

            return junction

    @staticmethod
    def process_sensor_event(data):

        event_id = data["event_id"]
        junction_id = data["junction_id"]
        event_type = data["event_type"]

        vehicle_id = data.get("vehicle_id")
        vehicle_type = data.get("vehicle_type")
        direction = data["direction"]

        sequence_no = data.get("sequence_no")
        sensor_timestamp = data.get("sensor_timestamp")

        with transaction.atomic():

            try:
                junction = JunctionRecord.objects.select_for_update().get(
                    pk=junction_id
                )

            except JunctionRecord.DoesNotExist:
                raise NotFound(f"Junction {junction_id} not found.")
            if ProcessedEvent.objects.filter(event_id=event_id).exists():

                return {"duplicate": True}
            if sequence_no is not None:

                last_event = (
                    ProcessedEvent.objects.filter(
                        junction_id=junction_id, sequence_no__isnull=False
                    )
                    .order_by("-sequence_no")
                    .first()
                )

                if (
                    last_event is not None
                    and last_event.sequence_no is not None
                    and sequence_no <= last_event.sequence_no
                ):
                    raise ValidationError(
                        {"sequence_no": "Stale/out-of-order sequence number."}
                    )

            if event_type == "VEHICLE_ARRIVED":

                vehicle, created = Vehicle.objects.get_or_create(
                    vehicle_id=vehicle_id,
                    defaults={
                        "junction_id": junction_id,
                        "direction": direction,
                        "vehicle_type": vehicle_type,
                        "priority": PRIORITIES[vehicle_type],
                    },
                )

                if not created:
                    raise ValidationError(
                        {"vehicle_id": "Vehicle is already active in a queue."}
                    )

                AuditLog.objects.create(
                    junction_id=junction_id,
                    event_type="VEHICLE_ARRIVED",
                    details={
                        "vehicle_id": vehicle_id,
                        "vehicle_type": vehicle_type,
                        "direction": direction,
                    },
                )

                if vehicle_type == "EMERGENCY":

                    oldest_emergency = (
                        Vehicle.objects.filter(
                            junction_id=junction_id, vehicle_type="EMERGENCY"
                        )
                        .order_by("arrival_time")
                        .first()
                    )

                    if oldest_emergency:
                        junction.emergency_direction = oldest_emergency.direction

                    TrafficService.restore_mode(junction)

                    junction.save()

                    AuditLog.objects.create(
                        junction_id=junction_id,
                        event_type="EMERGENCY_DETECTED",
                        details={"direction": direction, "vehicle_id": vehicle_id},
                    )

            elif event_type == "VEHICLE_CLEARED":

                if junction.actual_signals.get(direction) != "GREEN":
                    raise ValidationError(
                        {
                            "error": f"Cannot clear vehicle from {direction} while signal is RED."
                        }
                    )

                if vehicle_id == "OLDEST":

                    vehicle = (
                        Vehicle.objects.filter(
                            junction_id=junction_id, direction=direction
                        )
                        .order_by("arrival_time")
                        .first()
                    )

                    if not vehicle:
                        raise ValidationError(
                            {"vehicle_id": "No vehicle available to clear."}
                        )

                else:

                    try:
                        vehicle = Vehicle.objects.get(
                            vehicle_id=vehicle_id, junction_id=junction_id
                        )

                    except Vehicle.DoesNotExist:
                        raise ValidationError(
                            {"vehicle_id": "Vehicle not found at this junction."}
                        )

                cleared_vehicle_id = vehicle.vehicle_id

                vehicle.delete()

                AuditLog.objects.create(
                    junction_id=junction_id,
                    event_type="VEHICLE_CLEARED",
                    details={"vehicle_id": cleared_vehicle_id, "direction": direction},
                )

                remaining_emergency = (
                    Vehicle.objects.filter(
                        junction_id=junction_id, vehicle_type="EMERGENCY"
                    )
                    .order_by("arrival_time")
                    .first()
                )

                if remaining_emergency:
                    junction.emergency_direction = remaining_emergency.direction

                else:
                    junction.emergency_direction = None

                TrafficService.restore_mode(junction)

                junction.save()

            elif event_type in ["SENSOR_OFFLINE", "SENSOR_ONLINE"]:

                sensor_status = dict(junction.sensor_status)

                if event_type == "SENSOR_OFFLINE":
                    sensor_status[direction] = "OFFLINE"

                else:
                    sensor_status[direction] = "ONLINE"

                junction.sensor_status = sensor_status

                junction.save()

                AuditLog.objects.create(
                    junction_id=junction_id,
                    event_type=event_type,
                    details={"direction": direction},
                )

            ProcessedEvent.objects.create(
                event_id=event_id,
                junction_id=junction_id,
                sequence_no=sequence_no,
                sensor_timestamp=sensor_timestamp,
                event_type=event_type,
            )

            return {"duplicate": False}

    @staticmethod
    def process_controller_event(data):

        junction_id = data["junction_id"]
        status_value = data["status"]

        command_id = data.get("command_id")
        actual_signals = data.get("actual_signals")

        with transaction.atomic():

            try:
                junction = JunctionRecord.objects.select_for_update().get(
                    pk=junction_id
                )

            except JunctionRecord.DoesNotExist:
                raise NotFound("Junction not found.")

            if status_value == "OFFLINE":

                junction.controller_status = "OFFLINE"
                junction.mode = "DEGRADED"

                if junction.pending_command_id:

                    ControllerCommand.objects.filter(
                        command_id=junction.pending_command_id, status="PENDING"
                    ).update(status="FAILED")

                    junction.pending_command_id = None

                junction.save()

                AuditLog.objects.create(
                    junction_id=junction_id, event_type="CONTROLLER_OFFLINE", details={}
                )

                return {"status": "Controller offline"}

            if status_value == "ONLINE":

                junction.controller_status = "ONLINE"
                junction.actual_signals = actual_signals
                junction.last_controller_ack = current_milli_time()

                if junction.actual_signals == junction.desired_signals:
                    TrafficService.restore_mode(junction)

                else:
                    junction.mode = "DEGRADED"

                junction.save()

                AuditLog.objects.create(
                    junction_id=junction_id,
                    event_type="CONTROLLER_ONLINE",
                    details={"actual_signals": actual_signals},
                )

                return {"status": "Controller online"}

            try:
                command = ControllerCommand.objects.get(
                    command_id=command_id, junction_id=junction_id
                )

            except ControllerCommand.DoesNotExist:
                raise ValidationError(
                    {"command_id": "Unknown command or junction mismatch."}
                )

            if command.status == "ACKED":

                return {"duplicate_ack": True}

            if junction.pending_command_id != command_id:

                command.status = "STALE"
                command.save()

                return {"stale_ack": True}

            old_synced = junction.actual_signals == junction.desired_signals

            command.status = "ACKED"
            command.acknowledged_at = current_milli_time()
            command.save()

            junction.actual_signals = command.target_signals

            junction.controller_status = "ONLINE"

            junction.last_controller_ack = current_milli_time()

            junction.pending_command_id = None

            new_synced = junction.actual_signals == junction.desired_signals

            if junction.mode == "DEGRADED" and new_synced:
                TrafficService.restore_mode(junction)

            if not old_synced and new_synced:
                junction.state_entered_at = current_milli_time()

            junction.save()

            AuditLog.objects.create(
                junction_id=junction_id,
                event_type="CONTROLLER_ACK",
                details={"command_id": command_id},
            )

            return {"status": "ACK processed"}

    @staticmethod
    def create_controller_command(junction, target_signals):

        command_id = f"cmd-{uuid.uuid4().hex[:12]}"

        command = ControllerCommand.objects.create(
            command_id=command_id,
            junction=junction,
            target_signals=target_signals,
            status="PENDING",
        )

        junction.desired_signals = target_signals

        junction.pending_command_id = command_id

        junction.save(update_fields=["desired_signals", "pending_command_id"])

        AuditLog.objects.create(
            junction=junction,
            event_type="SIGNAL_STATE_REQUESTED",
            details={"command_id": command_id, "target_signals": target_signals},
        )

        return command
