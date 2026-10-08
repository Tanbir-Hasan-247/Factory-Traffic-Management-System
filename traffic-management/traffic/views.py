from rest_framework import viewsets, status

from rest_framework.decorators import action

from rest_framework.response import Response

from django.db import IntegrityError

from .models import JunctionRecord, ControllerCommand

from .serializers import (
    JunctionRecordSerializer,
    AuditLogSerializer,
    ManualCommandSerializer,
    SensorEventSerializer,
    ControllerEventSerializer,
    ControllerCommandSerializer,
)

from .services import TrafficService


class JunctionViewSet(viewsets.ModelViewSet):

    queryset = JunctionRecord.objects.all()

    serializer_class = JunctionRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "status":
            queryset = queryset.prefetch_related("vehicles")
        return queryset

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):

        junction = self.get_object()

        queues = TrafficService.get_queue_map(junction)

        pending_command = None

        if junction.pending_command_id:

            command = ControllerCommand.objects.filter(
                command_id=junction.pending_command_id
            ).first()

            if command:
                pending_command = ControllerCommandSerializer(command).data

        return Response(
            {
                "junction_id": junction.id,
                "mode": junction.mode,
                "phase": junction.current_phase,
                "transition_state": junction.transition_state,
                "controller_status": junction.controller_status,
                "sensor_status": junction.sensor_status,
                "desired_signals": junction.desired_signals,
                "actual_signals": junction.actual_signals,
                "queues": queues,
                "pending_command": pending_command,
            }
        )

    @action(detail=True, methods=["post"])
    def commands(self, request, pk=None):

        serializer = ManualCommandSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        command = serializer.validated_data["command"]

        direction = serializer.validated_data.get("direction")

        TrafficService.process_manual_command(
            junction_id=pk, command=command, direction=direction
        )

        return Response({"status": "Accepted"}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):

        junction = self.get_object()

        logs = junction.audit_logs.all()[:50]

        serializer = AuditLogSerializer(logs, many=True)

        return Response(serializer.data)


class SensorEventViewSet(viewsets.ViewSet):

    def create(self, request):

        serializer = SensorEventSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:

            result = TrafficService.process_sensor_event(serializer.validated_data)

        except IntegrityError:

            return Response(
                {"status": "Accepted (Duplicate)"}, status=status.HTTP_202_ACCEPTED
            )

        if result.get("duplicate"):

            return Response(
                {"status": "Accepted (Duplicate)"}, status=status.HTTP_202_ACCEPTED
            )

        return Response({"status": "Accepted"}, status=status.HTTP_202_ACCEPTED)


class ControllerEventViewSet(viewsets.ViewSet):

    def create(self, request):

        serializer = ControllerEventSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        result = TrafficService.process_controller_event(serializer.validated_data)

        if result.get("duplicate_ack"):

            return Response(
                {"status": "Accepted (Duplicate ACK)"}, status=status.HTTP_202_ACCEPTED
            )

        if result.get("stale_ack"):

            return Response(
                {"status": "Ignored stale ACK"}, status=status.HTTP_202_ACCEPTED
            )

        return Response(result, status=status.HTTP_202_ACCEPTED)


class ControllerCommandViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = (
        ControllerCommand.objects.select_related("junction")
        .all()
        .order_by("-created_at")
    )

    serializer_class = ControllerCommandSerializer
