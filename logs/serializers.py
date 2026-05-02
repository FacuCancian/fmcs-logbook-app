from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Driver, LogDay, DutySegment


class DriverSerializer(serializers.ModelSerializer):
    """Driver serializer with basic info"""

    class Meta:
        model = Driver
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'driver_number', 'home_terminal', 'truck_license']
        read_only_fields = ['id']


class DutySegmentSerializer(serializers.ModelSerializer):
    """Activity segment serializer with HOS validation"""

    duration_hours = serializers.ReadOnlyField()

    class Meta:
        model = DutySegment
        fields = '__all__'
        read_only_fields = ['id']

    def validate_start_time(self, value):
        """Validate 15-minute increments"""
        if value.minute % 15 != 0:
            raise serializers.ValidationError(
                "Start time must be in 15-minute increments (00, 15, 30, 45)"
            )
        return value

    def validate_end_time(self, value):
        """Validate 15-minute increments"""
        if value.minute % 15 != 0:
            raise serializers.ValidationError(
                "End time must be in 15-minute increments (00, 15, 30, 45)"
            )
        return value

    def validate(self, data):
        """Main HOS validation logic"""

        # Get the log day
        log_day = data.get('log_day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        status = data.get('status')


        if not all([log_day, start_time, end_time, status]):
            return data


        existing_segments = DutySegment.objects.filter(
            log_day=log_day
        )


        if self.instance:
            existing_segments = existing_segments.exclude(id=self.instance.id)


        # RULE 1: 11-HOUR DRIVING LIMIT

        if status == 'D':

            current_driving = sum(
                seg.duration_hours for seg in existing_segments if seg.status == 'D'
            )

            # Calculate new segment duration
            new_duration = (end_time - start_time).total_seconds() / 3600

            # Check if exceeds 11 hours
            if current_driving + new_duration > 11:
                remaining = 11 - current_driving
                raise serializers.ValidationError(
                    f"11-hour driving limit exceeded. "
                    f"You have {current_driving:.1f} hours driven. "
                    f"Only {remaining:.1f} hours remaining."
                )


        # RULE 2: 14-HOUR DRIVING WINDOW

        if status == 'D':
            # Find first on-duty or driving of the day
            all_segments = list(existing_segments) + [self.instance] if self.instance else list(existing_segments)

            # Temporarily add current segment to find first work
            temp_segments = list(existing_segments)
            if self.instance:

                temp_segments = [s for s in temp_segments if s.id != self.instance.id]
            temp_segments.append(data)

            # Sort by start time
            temp_segments.sort(key=lambda x: x.get('start_time') if hasattr(x, 'get') else x.start_time)

            # Find first work segment (status not OFF or SB)
            first_work = None
            for seg in temp_segments:
                seg_status = seg.get('status') if hasattr(seg, 'get') else seg.status
                if seg_status in ['ON', 'D']:
                    first_work = seg
                    break

            if first_work:
                # Get start time of first work
                first_work_start = first_work.get('start_time') if hasattr(first_work, 'get') else first_work.start_time
                window_end = first_work_start + timedelta(hours=14)

                # Check if this driving segment ends after window
                if end_time > window_end:
                    raise serializers.ValidationError(
                        f"14-hour driving window ends at {window_end.strftime('%H:%M')}. "
                        f"Cannot drive after this time."
                    )

        # RULE 3: Validate no midnight crossing

        if start_time.date() != end_time.date():
            raise serializers.ValidationError(
                "Activity cannot cross midnight. Please split into two segments."
            )


        # RULE 4: Validate end_time > start_time

        if end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time."
            )

        return data


class LogDaySerializer(serializers.ModelSerializer):
    """Log day serializer with nested segments and HOS calculations"""

    segments = DutySegmentSerializer(many=True, read_only=True)
    total_driving_hours = serializers.ReadOnlyField()
    total_on_duty_hours = serializers.ReadOnlyField()

    class Meta:
        model = LogDay
        fields = '__all__'
        read_only_fields = ['id', 'total_driving_hours', 'total_on_duty_hours']

    def create(self, validated_data):
        """Create log day and auto-calculate totals"""
        log_day = super().create(validated_data)
        self.update_totals(log_day)
        return log_day

    def update(self, instance, validated_data):
        """Update log day and auto-calculate totals"""
        log_day = super().update(instance, validated_data)
        self.update_totals(log_day)
        return log_day

    def update_totals(self, log_day):
        """Recalculate total driving and on-duty hours for the day"""
        segments = log_day.segments.all()

        # Calculate total driving hours
        total_driving = sum(
            seg.duration_hours for seg in segments if seg.status == 'D'
        )

        # Calculate total on-duty hours (Driving + On-duty)
        total_on_duty = sum(
            seg.duration_hours for seg in segments if seg.status in ['D', 'ON']
        )

        # Update the log day
        log_day.total_driving_hours = round(total_driving, 2)
        log_day.total_on_duty_hours = round(total_on_duty, 2)
        log_day.save(update_fields=['total_driving_hours', 'total_on_duty_hours'])