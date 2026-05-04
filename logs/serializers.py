from rest_framework import serializers
from datetime import timedelta
from .models import Driver, LogDay, DutySegment


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'driver_number', 'home_terminal', 'truck_license']
        read_only_fields = ['id']


class DutySegmentSerializer(serializers.ModelSerializer):
    duration_hours = serializers.ReadOnlyField()

    class Meta:
        model = DutySegment
        fields = '__all__'
        read_only_fields = ['id']

    def validate_start_time(self, value):
        if value.minute % 15 != 0:
            raise serializers.ValidationError(
                "Start time must be in 15-minute increments (00, 15, 30, 45)"
            )
        return value

    def validate_end_time(self, value):
        if value.minute % 15 != 0:
            raise serializers.ValidationError(
                "End time must be in 15-minute increments (00, 15, 30, 45)"
            )
        return value

    def validate(self, data):
        log_day = data.get('log_day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        status = data.get('status')

        if not all([log_day, start_time, end_time, status]):
            return data

        # RULE 0: end > start
        if end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time.")

        # RULE 1: no midnight crossing
        if start_time.date() != end_time.date():
            if status in ['D', 'ON']:
                raise serializers.ValidationError(
                    "Driving and On-duty cannot cross midnight. Please split into two segments."
                )

        # Base queryset - todos los segmentos del día excepto el actual si es edición
        existing_segments = DutySegment.objects.filter(log_day=log_day)
        if self.instance:
            existing_segments = existing_segments.exclude(id=self.instance.id)

        # RULE 2: no overlapping segments
        for seg in existing_segments:
            if start_time < seg.end_time and end_time > seg.start_time:
                raise serializers.ValidationError(
                    f"Time conflict with existing segment: "
                    f"{seg.start_time.strftime('%H:%M')} - {seg.end_time.strftime('%H:%M')} "
                    f"({seg.get_status_display()})"
                )

        # RULE 3: 11-hour driving limit
        if status == 'D':
            current_driving = sum(
                seg.duration_hours for seg in existing_segments if seg.status == 'D'
            )
            new_duration = (end_time - start_time).total_seconds() / 3600

            if current_driving + new_duration > 11:
                remaining = 11 - current_driving
                raise serializers.ValidationError(
                    f"11-hour driving limit exceeded. "
                    f"Driven today: {current_driving:.1f}h. "
                    f"Remaining: {remaining:.1f}h."
                )

        # RULE 4: 14-hour driving window
        if status == 'D':
            temp_segments = list(existing_segments)
            temp_segments.append(data)
            temp_segments.sort(
                key=lambda x: x.get('start_time') if isinstance(x, dict) else x.start_time
            )

            first_work = None
            for seg in temp_segments:
                seg_status = seg.get('status') if isinstance(seg, dict) else seg.status
                if seg_status in ['ON', 'D']:
                    first_work = seg
                    break

            if first_work:
                first_work_start = (
                    first_work.get('start_time') if isinstance(first_work, dict)
                    else first_work.start_time
                )
                window_end = first_work_start + timedelta(hours=14)
                if end_time > window_end:
                    raise serializers.ValidationError(
                        f"14-hour driving window ends at {window_end.strftime('%H:%M')}. "
                        f"Cannot drive after this time."
                    )

        return data


class LogDaySerializer(serializers.ModelSerializer):
    segments = DutySegmentSerializer(many=True, read_only=True)
    total_driving_hours = serializers.ReadOnlyField()
    total_on_duty_hours = serializers.ReadOnlyField()

    class Meta:
        model = LogDay
        fields = '__all__'
        read_only_fields = ['id', 'total_driving_hours', 'total_on_duty_hours']

    def create(self, validated_data):
        log_day = super().create(validated_data)
        self._update_totals(log_day)
        return log_day

    def update(self, instance, validated_data):
        log_day = super().update(instance, validated_data)
        self._update_totals(log_day)
        return log_day

    def _update_totals(self, log_day):
        segments = log_day.segments.all()
        log_day.total_driving_hours = round(
            sum(s.duration_hours for s in segments if s.status == 'D'), 2
        )
        log_day.total_on_duty_hours = round(
            sum(s.duration_hours for s in segments if s.status in ['D', 'ON']), 2
        )
        log_day.save(update_fields=['total_driving_hours', 'total_on_duty_hours'])