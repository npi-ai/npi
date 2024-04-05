from pydantic import Field
from npi.types import Parameter
from typing import Optional


class CreateEventParameter(Parameter):
    # calendar_id: str = Field(
    #     default='primary',
    #     description='The calendar\' ID'
    # )
    summary: str = Field(description='The title of this event')
    start_time: str = Field(
        description='The start time of this event. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T09:00:00-05:00. You should retrieve the user\'s timezone first.'
    )
    end_time: str = Field(
        description='The end time of this event. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-05:00. You should retrieve the user\'s timezone first.'
    )
    description: Optional[str] = Field(
        default=None,
        description='The description of this event. This property is used to store the details of this event'
    )


class RetrieveEventsParameter(Parameter):
    # calendar_id: str = Field(
    #     default='primary',
    #     description='The calendar\' ID'
    # )

    time_min: Optional[str] = Field(
        default=None,
        description='Lower bound (exclusive) for an event\'s end time to filter by. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-05:00. If `time_min` is set, `time_max` must be greater than `time_min`.'
    )

    time_max: Optional[str] = Field(
        default=None,
        description='Upper bound (exclusive) for an event\'s start time to filter by. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-05T10:00:00-05:00. If `time_max` is set, `time_min` must be smaller than `time_min`.'
    )
