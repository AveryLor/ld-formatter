"""Parser for MoTec ld files. Code created through reverse engineering the data format."""

import struct
import numpy as np


class ldData(object):
    """Container for parsed data of an ld file. Allows reading and writing."""

    def __init__(self, head, channs):
        self.head = head
        self.channs = channs

    def write(self, f):
        """Write an ld file containing the current header information and channel data"""
        # convert the data using scale/shift etc before writing the data
        conv_data = (
            lambda c: ((c._data / c.mul) - c.shift) * c.scale / pow(10.0, -c.dec)
        )

        with open(f, "wb") as f_:
            self.head.write(f_, len(self.channs))
            f_.seek(self.channs[0].meta_ptr)
            for i, ch in enumerate(self.channs):
                ch.write(f_, i)
            for ch in self.channs:
                f_.write(conv_data(ch).astype(ch.dtype))


class ldEvent(object):
    fmt = "<64s64s1024sH"

    def __init__(self, name, session, comment, venue_ptr, venue):
        self.name, self.session, self.comment, self.venue_ptr, self.venue = (
            name,
            session,
            comment,
            venue_ptr,
            venue,
        )

    def write(self, f):
        f.write(
            struct.pack(
                ldEvent.fmt,
                self.name.encode(),
                self.session.encode(),
                self.comment.encode(),
                self.venue_ptr,
            )
        )

        if self.venue_ptr > 0:
            f.seek(self.venue_ptr)
            self.venue.write(f)


class ldVenue(object):
    fmt = "<64s1034xH"

    def __init__(self, name, vehicle_ptr, vehicle):
        self.name, self.vehicle_ptr, self.vehicle = name, vehicle_ptr, vehicle

    def write(self, f):
        f.write(struct.pack(ldVenue.fmt, self.name.encode(), self.vehicle_ptr))
        if self.vehicle_ptr > 0:
            f.seek(self.vehicle_ptr)
            self.vehicle.write(f)


class ldVehicle(object):
    fmt = "<64s128xI32s32s"

    def __init__(self, id, weight, type, comment):
        self.id, self.weight, self.type, self.comment = id, weight, type, comment

    def write(self, f):
        f.write(
            struct.pack(
                ldVehicle.fmt,
                self.id.encode(),
                self.weight,
                self.type.encode(),
                self.comment.encode(),
            )
        )


class ldHead(object):
    fmt = "<" + (
        "I4x"  # ldmarker
        "II"  # chann_meta_ptr chann_data_ptr
        "20x"  # ??
        "I"  # event_ptr
        "24x"  # ??
        "HHH"  # unknown static (?) numbers
        "I"  # device serial
        "8s"  # device type
        "H"  # device version
        "H"  # unknown static (?) number
        "I"  # num_channs
        "4x"  # ??
        "16s"  # date
        "16x"  # ??
        "16s"  # time
        "16x"  # ??
        "64s"  # driver
        "64s"  # vehicleid
        "64x"  # ??
        "64s"  # venue
        "64x"  # ??
        "1024x"  # ??
        "I"  # enable "pro logging" (some magic number?)
        "66x"  # ??
        "64s"  # short comment
        "126x"  # ??
    )

    def __init__(
        self,
        meta_ptr,
        data_ptr,
        event_ptr,
        event,
        driver,
        vehicleid,
        venue,
        datetime,
        short_comment,
    ):
        (
            self.meta_ptr,
            self.data_ptr,
            self.event_ptr,
            self.event,
            self.driver,
            self.vehicleid,
            self.venue,
            self.datetime,
            self.short_comment,
        ) = (
            meta_ptr,
            data_ptr,
            event_ptr,
            event,
            driver,
            vehicleid,
            venue,
            datetime,
            short_comment,
        )

    def write(self, f, n):
        f.write(
            struct.pack(
                ldHead.fmt,
                0x40,
                self.meta_ptr,
                self.data_ptr,
                self.event_ptr,
                1,
                0x4240,
                0xF,
                0x1F44,
                "ADL".encode(),
                420,
                0xADB0,
                n,
                self.datetime.date().strftime("%d/%m/%Y").encode(),
                self.datetime.time().strftime("%H:%M:%S").encode(),
                self.driver.encode(),
                self.vehicleid.encode(),
                self.venue.encode(),
                0xC81A4,
                self.short_comment.encode(),
            )
        )
        if self.event_ptr > 0:
            f.seek(self.event_ptr)
            self.event.write(f)


class ldChan(object):
    """Channel (meta) data

    Parses and stores the channel meta data of a channel in a ld file.
    Needs the pointer to the channel meta block in the ld file.
    The actual data is read on demand using the 'data' property.
    """

    fmt = "<" + (
        "IIII"  # prev_addr next_addr data_ptr n_data
        "H"  # some counter?
        "HHH"  # datatype datatype rec_freq
        "hhhh"  # shift mul scale dec_places
        "32s"  # name
        "8s"  # short name
        "12s"  # unit
        "40x"  # ? (40 bytes for ACC, 32 bytes for acti)
    )

    def __init__(
        self,
        _f,
        meta_ptr,
        prev_meta_ptr,
        next_meta_ptr,
        data_ptr,
        data_len,
        dtype,
        freq,
        shift,
        mul,
        scale,
        dec,
        name,
        short_name,
        unit,
    ):

        self._f = _f
        self.meta_ptr = meta_ptr
        self._data = None

        (
            self.prev_meta_ptr,
            self.next_meta_ptr,
            self.data_ptr,
            self.data_len,
            self.dtype,
            self.freq,
            self.shift,
            self.mul,
            self.scale,
            self.dec,
            self.name,
            self.short_name,
            self.unit,
        ) = (
            prev_meta_ptr,
            next_meta_ptr,
            data_ptr,
            data_len,
            dtype,
            freq,
            shift,
            mul,
            scale,
            dec,
            name,
            short_name,
            unit,
        )

    def write(self, f, n):
        if self.dtype == np.float16 or self.dtype == np.float32:
            dtype_a = 0x07
            dtype = {np.float16: 2, np.float32: 4}[self.dtype]
        else:
            dtype_a = 0x05 if self.dtype == np.int32 else 0x03
            dtype = {np.int16: 2, np.int32: 4}[self.dtype]

        f.write(
            struct.pack(
                ldChan.fmt,
                self.prev_meta_ptr,
                self.next_meta_ptr,
                self.data_ptr,
                self.data_len,
                0x2EE1 + n,
                dtype_a,
                dtype,
                self.freq,
                self.shift,
                self.mul,
                self.scale,
                self.dec,
                self.name.encode(),
                self.short_name.encode(),
                self.unit.encode(),
            )
        )
