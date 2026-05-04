from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Driver, LogDay, DutySegment


class DriverSerializer(serializers.ModelSerializer):
    "Driver serializer with basic info"
    class Meta:
        model = Driver
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'driver_number', 'home_terminal', 'truck_license']
        read_only_fields = ['id']


class DutySegmentSerializer(serializers.ModelSerializer):
    "Activity segment serializer with HOS validation"

    duration_hours = serializers.ReadOnlyField()

    class Meta:
        model = DutySegment
        fields = '__all__'
        read_only_fields = ['id']

    def validate_start_time(self, value):
        "Validate 15-minute increments"
        if value.minute % 15 != 0:
            raise serializers.ValidationError(
                "Start time must be in 15-minute increments (00, 15, 30, 45)"
            )
        return value

    def validate_end_time(self, value):
        "15-minute increments"
        if value.minute % 15 != 0:
            raise serializers.ValidationError(
                "End time must be in 15-minute increments (00, 15, 30, 45)"
            )
        return value

    def validate(self, data):
        "Main HOS validation logic"
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

        if status == 'D':
            new_duration = (end_time - start_time).total_seconds() / 3600

            # RULE 1: 11-HOUR DRIVING LIMIT
            current_driving = sum(
                seg.duration_hours for seg in existing_segments if seg.status == 'D'
            )

            if current_driving + new_duration > 11:
                remaining = 11 - current_driving
                raise serializers.ValidationError(
                    f"11-hour driving limit exceeded. "
                    f"You have {current_driving:.1f} hours driven. "
                    f"Only {remaining:.1f} hours remaining."
                )

            # RULE 2: 14-HOUR DRIVING WINDOW
            temp_segments = []
            for seg in existing_segments:
                temp_segments.append({
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'status': seg.status,
                })

            temp_segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
            })

            temp_segments.sort(key=lambda x: x['start_time'])

            first_work_start = None
            for seg in temp_segments:
                if seg['status'] in ['ON', 'D']:
                    first_work_start = seg['start_time']
                    break

            if first_work_start:
                window_end = first_work_start + timedelta(hours=14)
                if end_time > window_end:
                    raise serializers.ValidationError(
                        f"14-hour driving window ends at {window_end.strftime('%H:%M')}. "
                        f"Cannot drive after this time."
                    )

            # RULE 3: 30-MINUTE REST BREAK
            temp_segments = []
            for seg in existing_segments:
                temp_segments.append({
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'status': seg.status,
                    'duration': seg.duration_hours
                })

            temp_segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'duration': new_duration
            })

            temp_segments.sort(key=lambda x: x['start_time'])

            cumulative_driving = 0

            for seg in temp_segments:
                if seg['status'] == 'D':
                    if cumulative_driving >= 8:
                        raise serializers.ValidationError(
                            "30-minute rest break required. "
                            "You have driven 8 cumulative hours without a 30-minute break. "
                            "Take 30 consecutive minutes off duty or sleeper berth before driving again."
                        )
                    cumulative_driving += seg['duration']
                elif seg['status'] in ['OFF', 'SB'] and seg['duration'] >= 0.5:
                    cumulative_driving = 0

            if cumulative_driving >= 8:
                raise serializers.ValidationError(
                    "30-minute rest break required. "
                    "You must take a 30-minute break after 8 cumulative driving hours."
                )

        # RULE 4: END TIME > START TIME
        if end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time."
            )

        # RULE 5: NO MIDNIGHT CROSSING
        if start_time.date() != end_time.date():
            raise serializers.ValidationError(
                "Activity cannot cross midnight. Please split into two segments."
            )


        # RULE 6: weekly

        driver = log_day.driver
        new_duration = (end_time - start_time).total_seconds() / 3600
        self._validate_weekly_limit(driver, log_day, start_time.date(), status, new_duration)

        return data
    def _validate_weekly_limit(self, driver, log_day, current_date, status, duration):
        "weekly on-duty limit"
        days_to_check = 7 if not driver.uses_70hour_8day else 8
        weekly_limit = 60 if not driver.uses_70hour_8day else 70

        start_date = current_date - timedelta(days=days_to_check - 1)

        log_days_in_window = LogDay.objects.filter(
            driver=driver,
            date__gte=start_date,
            date__lte=current_date
        )

        total_on_duty = 0

        for ld in log_days_in_window:
            if ld == log_day:
                # Current day: existing total + new segment (if on-duty)
                day_total = ld.total_on_duty_hours
                if status in ['D', 'ON']:
                    day_total += duration
                total_on_duty += day_total
            else:
                total_on_duty += ld.total_on_duty_hours

        if status in ['D', 'ON']:
            current_total = total_on_duty - duration

            if current_total >= weekly_limit:
                raise serializers.ValidationError(
                    f"Weekly limit of {weekly_limit} hours reached. "
                    f"Take a 34-hour restart."
                )

            if total_on_duty > weekly_limit:
                remaining = weekly_limit - current_total
                raise serializers.ValidationError(
                    f"Weekly limit exceeded. Only {remaining:.1f} hours remaining."
                )

class LogDaySerializer(serializers.ModelSerializer):
    "with nested segments and HOS calculations"
    segments = DutySegmentSerializer(many=True, read_only=True)
    total_driving_hours = serializers.ReadOnlyField()
    total_on_duty_hours = serializers.ReadOnlyField()

    class Meta:
        model = LogDay
        fields = '__all__'
        read_only_fields = ['id', 'total_driving_hours', 'total_on_duty_hours']

    def create(self, validated_data):
        log_day = super().create(validated_data)
        self.update_totals(log_day)
        return log_day

    def update(self, instance, validated_data):
        log_day = super().update(instance, validated_data)
        self.update_totals(log_day)
        return log_day

    def update_totals(self, log_day):
        segments = log_day.segments.all()

        total_driving = sum(
            seg.duration_hours for seg in segments if seg.status == 'D'
        )

        total_on_duty = sum(
            seg.duration_hours for seg in segments if seg.status in ['D', 'ON']
        )

        # Update the log day
        log_day.total_driving_hours = round(total_driving, 2)
        log_day.total_on_duty_hours = round(total_on_duty, 2)
        log_day.save(update_fields=['total_driving_hours', 'total_on_duty_hours'])