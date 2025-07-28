import csv
import pandas as pd


class Channel(object):
    """Represents a singe channel of data."""

    def __init__(self, name, units, messages, data_type):
        self.name = str(name)
        self.units = str(units)
        self.messages = messages
        self.data_type = data_type


class CsvLog(object):
    """Class for intaking CSV log data"""

    def __init__(self, metadata, df):
        self.channels = []
        self.metadata = metadata
        self.frequency = None
        self.df: pd.DataFrame = df

    @classmethod
    def parse(cls, csv_file):
        """
        Parses the AiM csv log into a pandas DataFrame
        """
        metadata = {}
        data = []
        header = None
        units = None

        with open(csv_file, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                # skip empty rows
                if not any(cell.strip() for cell in row):
                    continue
                # reads the AiM csv metadata
                if len(row) == 2:
                    key, value = row[0], row[1]
                    metadata[key.strip('"')] = value.strip('"')
                else:
                    # found the header
                    header = row
                    # the next row contains unit data
                    units = next(reader)
                    break

            # all metadata has been read, now read the data
            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue
                data.append(row)

            # list of tuples [(name, unit), ...]
            columns = list(zip(header, units))

            # convert to numeric dataframe, dropping non-numeric columns
            df = pd.DataFrame(data, columns=columns)
            df = df.apply(pd.to_numeric, errors="coerce")
            df = df.dropna(axis=1)

            return cls(metadata, df)

    def create_channels(self):
        """Creates channels populated with messages from a DataFrame."""
        for col in self.df.columns:
            channel = Channel(col[0], col[1], list(self.df[col]), float)
            self.channels.append(channel)

    def get_frequency(self):
        if self.frequency is None:
            return None
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
