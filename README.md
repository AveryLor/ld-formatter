# CSV to MoTeC `.ld` Log Converter

A tool that converts CSV log files into **MoTeC `.ld`** format.

- Parses CSV log files from AiM data systems
- Automatically detects and maps channels
- Outputs valid `.ld` logs compatible with MoTeC i2

Right now the csv parser is designed to parse logs from AiM data loggers, which include important metadata such as the sampling frequency for messages. If you have a csv that does not include this header, 
you can specify one using the --frequency flag. 

## Requirements
- I used Python 3.10 but you shouldnt have issues with any new version

## Usage
usage: main.py [-h] [--frequency FREQUENCY] [--output OUTPUT] log

Generates MoTeC .ld files using csv logs from an AiM data logger
positional arguments:
  log                   Path to logfile

options:
  -h, --help            show this help message and exit
  --frequency FREQUENCY
                        Sample rate for messages collected by the data logger
  --output OUTPUT       Name of output file, defaults to the same filename as 'log'


## Example
python3 main.py path/to/csv

Parsing CSV...

Converting to MoTeC log...

Saving MoTeC log...

Done!
