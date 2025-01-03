from serial_reader import microcontroller
from thermal_comfort import thermal_comfort_pmvppd, thermal_comfort_adaptive
import asyncio
import logging
from even_glasses.bluetooth_manager import GlassesManager
from even_glasses.commands import send_text

# Hardware configuration
serial_port = "COM11"
baud_rate = 115200
sensors = ["BEM280", "SCD30"]


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
            sensors=sensors,
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

                        else:
                            logger.error("Expected sensor not found in unpacked data")
                            # some dummy data
                            temperature = 22
                            humidity = 50
                            pressure = 1000
                            CO2 = 400

                    # 1) thermal comfort (Fanger's PMV/PPD model)
                    pmvppd = thermal_comfort_pmvppd(tdb=temperature, rh=50)
                    ## Predicted Mean Vote from –3 to +3 corresponding to the categories: cold, cool, slightly cool, neutral, slightly warm, warm, and hot.
                    pmv = pmvppd["pmv"]
                    logger.info(f"PMV: {pmv} [-3 ~ +3]")
                    ## Predicted Percentage of Dissatisfied (PPD) occupants in %
                    ppd = pmvppd["ppd"]
                    logger.info(f"PMV: {ppd} [%]")
                    ## Predicted clothing insulation value in clo
                    clo_predicted = pmvppd["clo"]
                    logger.info(f"Predicted clothing: {clo_predicted} [clo]")

                    # 2) thermal comfort (adaptive model)
                    adaptive_results = thermal_comfort_adaptive(tdb=temperature)


                    # TODO: Translate the clo value into common and understandable clothing combinations.

                    # TODO: IAQ

                    # TODO: Add support for other IEQ domains like noise, lighting, VOC etc.

                    # TODO: send sensor data to even g1
                    # await send_text(manager=manager, text_message="Hello World!")

                else:
                    logger.error("No sensor data!")
                    await send_text(manager=manager, text_message="No sensor data!")


        except KeyboardInterrupt:
            logger.info("Interrupted by user.")

        finally:
            await manager.disconnect_all()
            logger.info("Glasses disconnected.")

    else:
        logger.error("Failed to connect to glasses.")


if __name__ == "__main__":
    asyncio.run(main())
