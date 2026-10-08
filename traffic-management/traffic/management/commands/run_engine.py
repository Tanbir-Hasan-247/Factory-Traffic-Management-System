from django.core.management.base import BaseCommand
from django.db import transaction

from traffic.models import (
    JunctionRecord,
    Vehicle,
    AuditLog,
    ControllerCommand,
    current_milli_time,
)

import time
import uuid

TIMING = {
    "GREEN_MIN": 10_000,
    "GREEN_MAX": 30_000,
    "YELLOW": 5_000,
    "ALL_RED": 2_000,
    "CONTROLLER_TIMEOUT": 15_000,
}

JUNCTION_CONFIGS = {
    "A": {
        "phases": {
            "NORTH_SOUTH": ["NORTH", "SOUTH"],
            "EAST_WEST": ["EAST", "WEST"],
        },
        "directions": [
            "NORTH",
            "SOUTH",
            "EAST",
            "WEST",
        ],
    },
    "B": {
        "phases": {
            "NORTH_SOUTH": ["NORTH", "SOUTH"],
            "EAST_ONLY": ["EAST"],
        },
        "directions": [
            "NORTH",
            "SOUTH",
            "EAST",
        ],
    },
    "C": {
        "phases": {
            "PHASE_1": ["NORTH"],
            "PHASE_2": ["SOUTH"],
            "PHASE_3": ["EAST"],
            "PHASE_4": ["WEST"],
        },
        "directions": [
            "NORTH",
            "SOUTH",
            "EAST",
            "WEST",
        ],
    },
}


class Command(BaseCommand):
    help = "Run factory traffic management engine"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=float,
            default=1.0,
            help="Traffic engine tick interval in seconds",
        )

    def handle(self, *args, **options):
        interval = options["interval"]

        self.ensure_junctions()

        self.stdout.write(self.style.SUCCESS("Traffic engine started..."))

        try:
            while True:
                self.tick()
                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nTraffic engine stopped."))

    def ensure_junctions(self):
        for junction_id, config in JUNCTION_CONFIGS.items():

            if JunctionRecord.objects.filter(pk=junction_id).exists():
                continue

            desired_signals = {direction: "RED" for direction in config["directions"]}

            actual_signals = {
                direction: "UNKNOWN" for direction in config["directions"]
            }

            JunctionRecord.objects.create(
                id=junction_id,
                mode="DEGRADED",
                current_phase="ALL_RED",
                transition_state="ALL_RED",
                transition_target_phase=None,
                desired_signals=desired_signals,
                actual_signals=actual_signals,
                controller_status="UNKNOWN",
                state_entered_at=current_milli_time(),
            )

            AuditLog.objects.create(
                junction_id=junction_id,
                event_type="JUNCTION_INITIALIZED",
                details={
                    "desired_signals": desired_signals,
                    "controller_status": "UNKNOWN",
                },
            )

    def tick(self):
        junction_ids = list(
            JunctionRecord.objects.values_list(
                "id",
                flat=True,
            )
        )

        for junction_id in junction_ids:

            try:
                with transaction.atomic():

                    junction = JunctionRecord.objects.select_for_update().get(
                        pk=junction_id
                    )

                    self.evaluate_junction(junction)

            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"Junction {junction_id} error: {exc}")
                )

    def get_queue_scores(self, junction):
        config = JUNCTION_CONFIGS.get(junction.id)

        if not config:
            return {}

        scores = {direction: 0.0 for direction in config["directions"]}

        now = current_milli_time()

        vehicles = Vehicle.objects.filter(junction_id=junction.id)

        for vehicle in vehicles:

            if vehicle.direction not in scores:
                continue

            wait_seconds = max(
                0,
                (now - vehicle.arrival_time) / 1000.0,
            )
            vehicle_score = 1 + vehicle.priority + (wait_seconds * 0.5)

            scores[vehicle.direction] += vehicle_score

        return scores

    def get_phase_scores(
        self,
        junction,
        config,
    ):
        direction_scores = self.get_queue_scores(junction)

        phase_scores = {}

        for phase, directions in config["phases"].items():
            phase_scores[phase] = sum(
                direction_scores.get(
                    direction,
                    0,
                )
                for direction in directions
            )

        return phase_scores

    def get_target_phase_for_direction(
        self,
        direction,
        config,
    ):
        for phase, directions in config["phases"].items():
            if direction in directions:
                return phase

        return None

    def has_significant_demand(
        self,
        junction,
        target_phase,
        phase_scores,
    ):
        current_score = phase_scores.get(
            junction.current_phase,
            0,
        )

        target_score = phase_scores.get(
            target_phase,
            0,
        )

        if current_score == 0 and target_score > 0:
            return True

        return target_score > (current_score * 1.2) + 2

    def choose_automatic_phase(
        self,
        junction,
        phase_scores,
        elapsed,
    ):
        if not phase_scores:
            return None

        positive_phases = [phase for phase, score in phase_scores.items() if score > 0]
        if not positive_phases:
            if junction.current_phase in phase_scores:
                return junction.current_phase

            return None
        if junction.current_phase not in phase_scores:
            return max(
                positive_phases,
                key=lambda phase: phase_scores[phase],
            )

        current_phase = junction.current_phase
        if elapsed >= TIMING["GREEN_MAX"]:

            waiting_other_phases = [
                phase for phase in positive_phases if phase != current_phase
            ]

            if waiting_other_phases:
                return max(
                    waiting_other_phases,
                    key=lambda phase: phase_scores[phase],
                )

        best_phase = max(
            positive_phases,
            key=lambda phase: phase_scores[phase],
        )

        if best_phase == current_phase:
            return current_phase
        if elapsed < TIMING["GREEN_MIN"]:
            return current_phase

        if self.has_significant_demand(
            junction,
            best_phase,
            phase_scores,
        ):
            return best_phase

        return current_phase

    def determine_target_phase(
        self,
        junction,
        config,
        phase_scores,
        elapsed,
    ):
        if junction.emergency_direction and junction.mode == "EMERGENCY":
            phase = self.get_target_phase_for_direction(
                junction.emergency_direction,
                config,
            )

            return phase, True
        if junction.manual_direction and junction.mode == "MANUAL":
            phase = self.get_target_phase_for_direction(
                junction.manual_direction,
                config,
            )

            return phase, True
        if junction.mode == "AUTOMATIC":

            phase = self.choose_automatic_phase(
                junction,
                phase_scores,
                elapsed,
            )

            return phase, False

        return None, False

    def get_green_directions(
        self,
        signals,
    ):
        return {direction for direction, state in signals.items() if state == "GREEN"}

    def is_safe_signal_map(
        self,
        signals,
        config,
    ):
        green_directions = self.get_green_directions(signals)

        if not green_directions:
            return True

        for directions in config["phases"].values():
            allowed = set(directions)

            if green_directions.issubset(allowed):
                return True

        return False

    def assert_transition_safe(
        self,
        next_state,
        phase,
        desired,
        config,
    ):
        green_directions = self.get_green_directions(desired)

        if next_state == "STABLE":

            if phase not in config["phases"]:
                raise ValueError(f"Unknown phase: {phase}")

            allowed_green = set(config["phases"][phase])

            if green_directions != allowed_green:
                raise ValueError(
                    "Safety violation: invalid " "GREEN directions for phase."
                )

        else:
            if green_directions:
                raise ValueError(
                    "Safety violation: GREEN " "signal outside STABLE state."
                )

        if not self.is_safe_signal_map(
            desired,
            config,
        ):
            raise ValueError("Safety violation: conflicting " "GREEN signals detected.")

    def create_controller_command(
        self,
        junction,
        target_signals,
        event_type="SIGNAL_STATE_REQUESTED",
    ):
        if junction.pending_command_id:
            raise ValueError(
                "Cannot create controller command " "while another command is pending."
            )

        command_id = f"cmd-{uuid.uuid4().hex[:12]}"

        ControllerCommand.objects.create(
            command_id=command_id,
            junction_id=junction.id,
            target_signals=target_signals,
            status="PENDING",
            created_at=current_milli_time(),
        )

        junction.desired_signals = target_signals

        junction.pending_command_id = command_id

        AuditLog.objects.create(
            junction_id=junction.id,
            event_type=event_type,
            details={
                "command_id": command_id,
                "target_signals": target_signals,
            },
        )

        return command_id

    def check_controller_timeout(
        self,
        junction,
        now,
    ):
        if not junction.pending_command_id:
            return False

        command = ControllerCommand.objects.filter(
            command_id=junction.pending_command_id,
            junction_id=junction.id,
        ).first()

        if not command:
            missing_id = junction.pending_command_id

            junction.pending_command_id = None
            junction.mode = "DEGRADED"
            junction.controller_status = "UNKNOWN"

            junction.save(
                update_fields=[
                    "pending_command_id",
                    "mode",
                    "controller_status",
                ]
            )

            AuditLog.objects.create(
                junction_id=junction.id,
                event_type="CONTROLLER_COMMAND_MISSING",
                details={
                    "command_id": missing_id,
                },
            )

            return True

        if command.status != "PENDING":
            return False

        age = now - command.created_at

        if age < TIMING["CONTROLLER_TIMEOUT"]:
            return False

        command.status = "TIMEOUT"
        command.save(update_fields=["status"])

        timed_out_id = command.command_id

        junction.pending_command_id = None
        junction.controller_status = "UNKNOWN"
        junction.mode = "DEGRADED"

        junction.save(
            update_fields=[
                "pending_command_id",
                "controller_status",
                "mode",
            ]
        )

        AuditLog.objects.create(
            junction_id=junction.id,
            event_type="CONTROLLER_TIMEOUT",
            details={
                "command_id": timed_out_id,
                "timeout_ms": TIMING["CONTROLLER_TIMEOUT"],
            },
        )

        return True

    def restore_operating_mode(
        self,
        junction,
    ):
        if junction.controller_status != "ONLINE":
            junction.mode = "DEGRADED"
            return

        if junction.emergency_direction:
            junction.mode = "EMERGENCY"

        elif junction.manual_direction:
            junction.mode = "MANUAL"

        else:
            junction.mode = "AUTOMATIC"

    def evaluate_junction(
        self,
        junction,
    ):
        config = JUNCTION_CONFIGS.get(junction.id)
        if not config:

            if junction.mode != "DEGRADED":
                junction.mode = "DEGRADED"
                junction.save(update_fields=["mode"])

                AuditLog.objects.create(
                    junction_id=junction.id,
                    event_type="CONFIGURATION_ERROR",
                    details={"error": "No junction configuration found."},
                )

            return

        now = current_milli_time()

        if self.check_controller_timeout(
            junction,
            now,
        ):
            return

        if junction.controller_status != "ONLINE":
            if junction.mode != "DEGRADED":
                junction.mode = "DEGRADED"

                junction.save(update_fields=["mode"])

            return

        if any(state == "UNKNOWN" for state in junction.actual_signals.values()):
            if junction.mode != "DEGRADED":
                junction.mode = "DEGRADED"

                junction.save(update_fields=["mode"])

            return

        if not self.is_safe_signal_map(
            junction.actual_signals,
            config,
        ):
            if junction.mode != "DEGRADED":

                junction.mode = "DEGRADED"

                junction.save(update_fields=["mode"])

                AuditLog.objects.create(
                    junction_id=junction.id,
                    event_type="UNSAFE_ACTUAL_STATE",
                    details={"actual_signals": junction.actual_signals},
                )

            return

        is_synced = junction.actual_signals == junction.desired_signals

        if not is_synced:

            if junction.pending_command_id:
                return
            if not self.is_safe_signal_map(
                junction.desired_signals,
                config,
            ):
                junction.mode = "DEGRADED"

                junction.save(update_fields=["mode"])

                AuditLog.objects.create(
                    junction_id=junction.id,
                    event_type="UNSAFE_DESIRED_STATE",
                    details={"desired_signals": junction.desired_signals},
                )

                return

            self.create_controller_command(
                junction,
                dict(junction.desired_signals),
                event_type="SYNC_RECOVERY",
            )

            junction.save(
                update_fields=[
                    "desired_signals",
                    "pending_command_id",
                ]
            )

            return

        if junction.mode == "DEGRADED":

            self.restore_operating_mode(junction)

            junction.save(update_fields=["mode"])

        elapsed = now - junction.state_entered_at

        phase_scores = self.get_phase_scores(
            junction,
            config,
        )

        target_phase, immediate = self.determine_target_phase(
            junction,
            config,
            phase_scores,
            elapsed,
        )

        if (
            immediate
            and target_phase
            and junction.transition_state in ["YELLOW", "ALL_RED"]
            and target_phase != junction.transition_target_phase
        ):
            old_target = junction.transition_target_phase

            junction.transition_target_phase = target_phase

            junction.save(update_fields=["transition_target_phase"])

            AuditLog.objects.create(
                junction_id=junction.id,
                event_type="TRANSITION_TARGET_CHANGED",
                details={
                    "previous_target": old_target,
                    "new_target": target_phase,
                },
            )

        if junction.transition_state == "STABLE":
            if not target_phase:
                return

            if target_phase == junction.current_phase:
                return

            should_switch = False
            if immediate:
                should_switch = True

            elif elapsed >= TIMING["GREEN_MAX"]:
                should_switch = True

            elif elapsed >= TIMING["GREEN_MIN"] and self.has_significant_demand(
                junction,
                target_phase,
                phase_scores,
            ):
                should_switch = True

            if should_switch:

                self.transition_to(
                    junction=junction,
                    next_state="YELLOW",
                    target_phase=target_phase,
                    config=config,
                )

            return

        if junction.transition_state == "YELLOW":
            if elapsed < TIMING["YELLOW"]:
                return

            self.transition_to(
                junction=junction,
                next_state="ALL_RED",
                target_phase=(junction.transition_target_phase),
                config=config,
            )

            return

        if junction.transition_state == "ALL_RED":
            if elapsed < TIMING["ALL_RED"]:
                return

            next_phase = junction.transition_target_phase
            if not next_phase:
                next_phase = target_phase
            if not next_phase:
                return

            self.transition_to(
                junction=junction,
                next_state="STABLE",
                target_phase=next_phase,
                config=config,
            )

            return
        junction.mode = "DEGRADED"

        junction.save(update_fields=["mode"])

        AuditLog.objects.create(
            junction_id=junction.id,
            event_type="INVALID_TRANSITION_STATE",
            details={"transition_state": junction.transition_state},
        )

    def transition_to(
        self,
        junction,
        next_state,
        target_phase,
        config,
    ):
        old_signals = dict(junction.desired_signals)

        old_phase = junction.current_phase

        desired = {direction: "RED" for direction in config["directions"]}

        if next_state == "STABLE":

            if not target_phase or target_phase not in config["phases"]:
                raise ValueError("Cannot enter STABLE without " "a valid target phase.")

            for direction in config["phases"][target_phase]:
                desired[direction] = "GREEN"

            new_phase = target_phase

        elif next_state == "YELLOW":

            if junction.current_phase not in config["phases"]:
                raise ValueError(
                    "Cannot enter YELLOW because " "current phase is invalid."
                )

            for direction in config["phases"][junction.current_phase]:
                desired[direction] = "YELLOW"

            new_phase = junction.current_phase

        elif next_state == "ALL_RED":
            new_phase = "ALL_RED"

        else:
            raise ValueError(f"Unknown transition state: " f"{next_state}")

        self.assert_transition_safe(
            next_state=next_state,
            phase=(target_phase if next_state == "STABLE" else new_phase),
            desired=desired,
            config=config,
        )

        junction.transition_state = next_state

        junction.current_phase = new_phase

        junction.state_entered_at = current_milli_time()

        if next_state == "YELLOW":

            junction.transition_target_phase = target_phase

        elif next_state == "ALL_RED":
            if target_phase:
                junction.transition_target_phase = target_phase

        elif next_state == "STABLE":

            junction.transition_target_phase = None

        command_id = self.create_controller_command(
            junction,
            desired,
        )

        junction.save(
            update_fields=[
                "transition_state",
                "current_phase",
                "transition_target_phase",
                "desired_signals",
                "pending_command_id",
                "state_entered_at",
            ]
        )

        AuditLog.objects.create(
            junction_id=junction.id,
            event_type="TRANSITION_STARTED",
            details={
                "previous_phase": old_phase,
                "new_phase": new_phase,
                "transition_state": next_state,
                "target_phase": target_phase,
                "previous_signals": old_signals,
                "desired_signals": desired,
                "command_id": command_id,
            },
        )
