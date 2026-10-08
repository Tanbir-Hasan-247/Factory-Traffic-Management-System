import datetime

from rest_framework import serializers

from .models import JunctionRecord, Vehicle, ProcessedEvent, ControllerCommand, AuditLog

VALID_DIRECTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}

VEHICLE_TYPES = {"EMERGENCY", "TRUCK", "FORKLIFT", "EMPLOYEE_VEHICLE"}


class JunctionRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = JunctionRecord
        fields = "__all__"


class VehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vehicle
        fields = "__all__"


class ProcessedEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProcessedEvent
        fields = "__all__"


class ControllerCommandSerializer(serializers.ModelSerializer):

    class Meta:
        model = ControllerCommand
        fields = "__all__"


class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog
        fields = "__all__"


class ManualCommandSerializer(serializers.Serializer):

    command = serializers.ChoiceField(
        choices=["MANUAL_GREEN_REQUEST", "RETURN_TO_AUTOMATIC"]
    )

    direction = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        command = attrs.get("command")
        direction = attrs.get("direction")

        if command == "MANUAL_GREEN_REQUEST":
            if direction not in VALID_DIRECTIONS:
                raise serializers.ValidationError(
                    {"direction": "Valid direction is required."}
                )

        return attrs


class SensorEventSerializer(serializers.Serializer):

    event_id = serializers.CharField()
    junction_id = serializers.CharField()

    event_type = serializers.ChoiceField(
        choices=[
            "VEHICLE_ARRIVED",
            "VEHICLE_CLEARED",
            "SENSOR_OFFLINE",
            "SENSOR_ONLINE",
        ]
    )

    vehicle_id = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    vehicle_type = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    direction = serializers.CharField()

    sequence_no = serializers.IntegerField(required=False, allow_null=True)

    timestamp = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    sensor_timestamp = serializers.IntegerField(required=False, allow_null=True)

    def validate_direction(self, value):
        if value not in VALID_DIRECTIONS:
            raise serializers.ValidationError(
                "Direction must be NORTH, SOUTH, EAST or WEST."
            )

        return value

    def validate(self, attrs):
        event_type = attrs.get("event_type")
        vehicle_id = attrs.get("vehicle_id")
        vehicle_type = attrs.get("vehicle_type")

        if event_type == "VEHICLE_ARRIVED":

            if not vehicle_id:
                raise serializers.ValidationError(
                    {"vehicle_id": "vehicle_id is required."}
                )

            if vehicle_type not in VEHICLE_TYPES:
                raise serializers.ValidationError(
                    {"vehicle_type": "Invalid vehicle type."}
                )

        elif event_type == "VEHICLE_CLEARED":

            if not vehicle_id:
                raise serializers.ValidationError(
                    {"vehicle_id": "vehicle_id is required."}
                )

        timestamp = attrs.pop("timestamp", None)

        if timestamp:

            try:
                dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

                attrs["sensor_timestamp"] = int(dt.timestamp() * 1000)

            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    {"timestamp": "Invalid ISO timestamp."}
                )

        return attrs


class ControllerEventSerializer(serializers.Serializer):

    junction_id = serializers.CharField()

    status = serializers.ChoiceField(choices=["ACK", "OFFLINE", "ONLINE"])

    command_id = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    actual_signals = serializers.JSONField(required=False)

    def validate(self, attrs):

        status_value = attrs.get("status")

        if status_value == "ACK":

            if not attrs.get("command_id"):
                raise serializers.ValidationError(
                    {"command_id": "command_id is required for ACK."}
                )

        if status_value == "ONLINE":

            if not attrs.get("actual_signals"):
                raise serializers.ValidationError(
                    {"actual_signals": "Full actual signal state is required."}
                )

        return attrs
