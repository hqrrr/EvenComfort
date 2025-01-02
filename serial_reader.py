import serial
import serial.tools.list_ports
import json
from csv import writer
from datetime import datetime
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class microcontroller():
    def __init__(self, serial_port: str, baud_rate: int, number_of_sensor: int, filename: str = "test", save: bool = False):
        self.mc = serial.Serial(serial_port, baud_rate, timeout=1)
        self.number_of_sensor = number_of_sensor
        self.filename = filename
        self.save = save

    def get_data(self):
        """
        read data from serial port in json format / save data as csv (optional, if save is True)
        -------------------------
        data structure example:
            {
              "Device": "ieq_epaper_v",
              "Time": 11847,
              "Location": "office",
              "Data": [
                {
                  "Sensor": "BME280",
                  "Value": {
                    "Temperature": 0,
                    "Humidity": 0,
                    "Pressure": 0,
                    "Approx. Altitude": 0
                  }
                },
                {
                  "Sensor": "SCD30",
                  "Value": {
                    "Temperature": 22.54,
                    "Humidity": 42.45,
                    "CO2": 1568.18
                  }
                }
              ]
            }
        """

        # read serial data
        value_read = self.mc.readline()  # type bytes

        logger.debug("---check----")
        logger.debug(value_read)
        logger.debug(len(value_read))
        logger.debug("-------")

        value_read_dict = {}

        if len(value_read) < 80:
            pass
        else:
            value_read_deco = value_read.decode("utf-8").strip()
            value_read_dict = json.loads(value_read_deco)

            # update time
            now = datetime.now()
            new_row = [now]

            for i in range(0, self.number_of_sensor):
                if value_read_dict["Data"][i]["Sensor"] == "BME280":
                    new_row.append(value_read_dict["Data"][i]["Sensor"])
                    new_row.append(value_read_dict["Data"][i]["Value"]["Temperature"])
                    new_row.append(value_read_dict["Data"][i]["Value"]["Humidity"])
                    new_row.append(value_read_dict["Data"][i]["Value"]["Pressure"])
                elif value_read_dict["Data"][i]["Sensor"] == "SCD30":
                    new_row.append(value_read_dict["Data"][i]["Sensor"])
                    new_row.append(value_read_dict["Data"][i]["Value"]["Temperature"])
                    new_row.append(value_read_dict["Data"][i]["Value"]["Humidity"])
                    new_row.append(value_read_dict["Data"][i]["Value"]["CO2"])
                else:
                    raise Exception("Sensor type unknow!")

            logger.info(new_row)

            if self.save is True:
                try:
                    append_list_as_row(f"{self.filename}.csv", new_row)
                    logger.debug(f"{self.filename}: data saved!")
                except:
                    logger.error("Saving data failed, try next time again...")

        return value_read_dict


def append_list_as_row(file_name: str, list_of_elem: list):
    # Open file in append mode
    with open(file_name, "a+", newline="") as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)

