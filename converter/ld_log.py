import numpy as np
import struct
from converter.ldparser import ldVehicle, ldVenue, ldEvent, ldHead, ldChan, ldData
from converter.csv_log import CsvLog, Channel
import datetime

# Pointers to locations in the file where data sections should be written. These have been
# determined from inspecting some MoTeC .ld files, and were consistent across all files.
VEHICLE_PTR = 1762
VENUE_PTR = 5078
EVENT_PTR = 8180
HEADER_PTR = 11336
CHANNEL_HEADER_SIZE = struct.calcsize(ldChan.fmt)


class LdLog(object):
    """Handles generating a MoTeC .ld file from a CsvLog object."""

    def __init__(self, ld_header, frequency):
        self.ld_header: ldHead = ld_header
        self.ld_channels: list[ldChan] = []
        self.frequency = frequency

    @classmethod
    def initialize(cls, csv_log: CsvLog):
        """Initializes all the meta data for the motec log. This must be called before adding any channel data."""
        metadata: dict = csv_log.metadata

        vehicle_id = ""
        vehicle_weight = 0
        vehicle_type = ""
        vehicle_comment = ""
        venue_name = ""
        event_name = ""
        event_session = ""
        long_comment = ""
        driver = ""
        date = datetime.datetime.now()
        short_comment = ""

        frequency = csv_log.get_frequency()
        if frequency is None:
            try:
                frequency = metadata["Sample Rate"]
            except KeyError:
                print("WARNING: log frequency not specified. Using 20hz default.")
                frequency = 20

        ld_vehicle = ldVehicle(
            vehicle_id, vehicle_weight, vehicle_type, vehicle_comment
        )
        ld_venue = ldVenue(venue_name, VEHICLE_PTR, ld_vehicle)
        ld_event = ldEvent(event_name, event_session, long_comment, VENUE_PTR, ld_venue)
        ld_header = ldHead(
            HEADER_PTR,
            HEADER_PTR,
            EVENT_PTR,
            ld_event,
            driver,
            vehicle_id,
            venue_name,
            date,
            short_comment,
        )
        return cls(ld_header, frequency)

    def add_channel(self, log_channel: Channel):
        """Adds a single channel of data to the motec log.

        log_channel: data_log.Channel
        """
        # Advance the header data pointer
        self.ld_header.data_ptr += CHANNEL_HEADER_SIZE

        # Advance the data pointers of all previous channels
        for ld_channel in self.ld_channels:
            ld_channel.data_ptr += CHANNEL_HEADER_SIZE

        # Determine our file pointers
        if self.ld_channels:
            meta_ptr = self.ld_channels[-1].next_meta_ptr
            prev_meta_ptr = self.ld_channels[-1].meta_ptr
            data_ptr = self.ld_channels[-1].data_ptr + self.ld_channels[-1]._data.nbytes
        else:
            # First channel needs the previous pointer zero'd out
            meta_ptr = HEADER_PTR
            prev_meta_ptr = 0
            data_ptr = self.ld_header.data_ptr
        next_meta_ptr = meta_ptr + CHANNEL_HEADER_SIZE

        # Channel specs
        data_len = len(log_channel.messages)
        data_type = np.float32 if log_channel.data_type is float else np.int32
        freq = self.frequency
        shift = 0
        multiplier = 1
        scale = 1

        # Decimal places must be hard coded to zero, the ldparser library doesn't properly
        # handle non zero values, consequently all channels will have zero decimal places
        # decimals = log_channel.decimals
        decimals = 0

        ld_channel = ldChan(
            None,
            meta_ptr,
            prev_meta_ptr,
            next_meta_ptr,
            data_ptr,
            data_len,
            data_type,
            freq,
            shift,
            multiplier,
            scale,
            decimals,
            log_channel.name,
            "",
            log_channel.units,
        )

        # Add in the channel data
        ld_channel._data = np.array(log_channel.messages, data_type)

        # Add the ld channel and advance the file pointers
        self.ld_channels.append(ld_channel)

    def add_all_channels(self, csv_log: CsvLog):
        """Adds all channels from a DataLog to the motec log.

        data_log: data_log.DataLog
        """
        channels = csv_log.channels
        for channel in channels:
            self.add_channel(channel)

    def write(self, filename):
        """Writes the motec log data to disc."""
        ld_data = ldData(self.ld_header, self.ld_channels)
        # Need to zero out the final channel pointer
        ld_data.channs[-1].next_meta_ptr = 0
        ld_data.write(filename)
