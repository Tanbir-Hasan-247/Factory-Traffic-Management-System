from django.db import models
import time


def current_milli_time():
    return int(time.time() * 1000)


def default_desired_signals():
    return {"NORTH": "RED", "SOUTH": "RED", "EAST": "RED", "WEST": "RED"}


def default_actual_signals():
    return {
        "NORTH": "UNKNOWN",
        "SOUTH": "UNKNOWN",
        "EAST": "UNKNOWN",
        "WEST": "UNKNOWN",
    }


class JunctionRecord(models.Model):
    MODE_CHOICES = [
        ("AUTOMATIC", "Automatic"),
        ("MANUAL", "Manual"),
        ("EMERGENCY", "Emergency"),
        ("DEGRADED", "Degraded"),
    ]

    PHASE_CHOICES = [
        ("NORTH_SOUTH", "North South"),
        ("EAST_WEST", "East West"),
        ("ALL_RED", "All Red"),
    ]

    CONTROLLER_STATUS_CHOICES = [
        ("UNKNOWN", "Unknown"),
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
    ]

    id = models.CharField(max_length=50, primary_key=True)

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="AUTOMATIC")

    current_phase = models.CharField(
        max_length=50, choices=PHASE_CHOICES, default="ALL_RED"
    )

    transition_state = models.CharField(max_length=20, default="STABLE")

    transition_target_phase = models.CharField(max_length=50, null=True, blank=True)

    state_entered_at = models.BigIntegerField(default=current_milli_time)

    manual_direction = models.CharField(max_length=20, null=True, blank=True)

    emergency_direction = models.CharField(max_length=20, null=True, blank=True)

    desired_signals = models.JSONField(default=default_desired_signals)

    actual_signals = models.JSONField(default=default_actual_signals)

    pending_command_id = models.CharField(max_length=100, null=True, blank=True)

    controller_status = models.CharField(
        max_length=20, choices=CONTROLLER_STATUS_CHOICES, default="UNKNOWN"
    )

    last_controller_ack = models.BigIntegerField(null=True, blank=True)

    sensor_status = models.JSONField(default=dict)

    def __str__(self):
        return f"Junction {self.id}"


class Vehicle(models.Model):
    vehicle_id = models.CharField(max_length=100, primary_key=True)

    junction = models.ForeignKey(
        JunctionRecord,
        on_delete=models.CASCADE,
        related_name="vehicles",
        db_column="junction_id",
    )

    direction = models.CharField(max_length=20)

    vehicle_type = models.CharField(max_length=50)

    priority = models.IntegerField(default=1)

    arrival_time = models.BigIntegerField(default=current_milli_time)

    def __str__(self):
        return self.vehicle_id


class ProcessedEvent(models.Model):
    event_id = models.CharField(max_length=100, primary_key=True)

    junction = models.ForeignKey(
        JunctionRecord,
        on_delete=models.CASCADE,
        related_name="processed_events",
        db_column="junction_id",
    )

    sequence_no = models.IntegerField(null=True, blank=True)

    sensor_timestamp = models.BigIntegerField(null=True, blank=True)

    event_type = models.CharField(max_length=50)

    received_at = models.BigIntegerField(default=current_milli_time)

    def __str__(self):
        return self.event_id


class ControllerCommand(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACKED", "Acknowledged"),
        ("FAILED", "Failed"),
        ("TIMEOUT", "Timeout"),
        ("STALE", "Stale"),
    ]

    command_id = models.CharField(max_length=100, primary_key=True)

    junction = models.ForeignKey(
        JunctionRecord,
        on_delete=models.CASCADE,
        related_name="controller_commands",
        db_column="junction_id",
    )

    target_signals = models.JSONField(default=dict)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    created_at = models.BigIntegerField(default=current_milli_time)

    acknowledged_at = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.command_id


class AuditLog(models.Model):
    junction = models.ForeignKey(
        JunctionRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        db_column="junction_id",
    )

    event_type = models.CharField(max_length=50)

    details = models.JSONField(default=dict)

    timestamp = models.BigIntegerField(default=current_milli_time)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.junction_id} - {self.event_type}"
