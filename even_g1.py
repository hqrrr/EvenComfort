from serial_reader import microcontroller
import asyncio
import logging
from even_glasses.bluetooth_manager import GlassesManager
from even_glasses.commands import send_text


serial_port = "COM11"
baud_rate = 115200
number_of_sensor = 2


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # init even g1 glasses
    manager = GlassesManager(left_address=None, right_address=None)
    glasses_connected = await manager.scan_and_connect()
    await send_text(manager=manager, text_message="Hello, World!")

    if glasses_connected:
        # init microcontroller
        mc = microcontroller(
            serial_port=serial_port,
            baud_rate=baud_rate,
            number_of_sensor=number_of_sensor,
        )
        try:
            while True:
                sensor_data = mc.get_data()
                if sensor_data:
                    for i, data in enumerate(sensor_data["Data"]):
                        # Bosch BME280
                        if data["Sensor"] == "BME280":
                            temperature = sensor_data["Data"][i]["Value"]["Temperature"]
                            logger.info(f"Temperature: {temperature} degC")
                            humidity = sensor_data["Data"][i]["Value"]["Humidity"]
                            logger.info(f"Humidity: {humidity} %")
                            pressure = sensor_data["Data"][i]["Value"]["Pressure"]
                            logger.info(f"Air pressure: {pressure} hPa")

                        # Sensirion SCD30
                        if data["Sensor"] == "SCD30":
                            CO2 = sensor_data["Data"][i]["Value"]["CO2"]
                            logger.info(f"CO2: {CO2} ppm")

                # TODO: send sensor data to even g1
                # await send_text(manager=manager, text_message="Hello World!")

                # TODO: add thermal comfort evaluation

        except KeyboardInterrupt:
            logger.info("Interrupted by user.")

        finally:
            await manager.disconnect_all()
            logger.info("Glasses disconnected.")

    else:
        logger.error("Failed to connect to glasses.")


if __name__ == "__main__":
    asyncio.run(main())
