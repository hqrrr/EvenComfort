from serial_reader import microcontroller
from thermal_comfort import thermal_comfort_pmvppd, thermal_comfort_adaptive
from air_quality import iaq_co2
from clothing_suggestion import clothing_suggestion
import asyncio
import logging
from even_glasses.bluetooth_manager import GlassesManager
from even_glasses.commands import send_text
import time

# Hardware configuration
serial_port = "COM11"
baud_rate = 115200
sensors = ["BEM280", "SCD30"]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# some dummy data
temperature = -1
humidity = 99
pressure = 99
CO2 = 99


async def send_sensordata(manager):
    global temperature
    global humidity
    global pressure
    global CO2
    # init microcontroller
    mc = microcontroller(
        serial_port=serial_port,
        baud_rate=baud_rate,
        sensors=sensors,
    )
    while True:
        sensor_data = mc.get_data()
        if sensor_data:
            for i, data in enumerate(sensor_data["Data"]):
                # Bosch BME280
                if data["Sensor"] == "BME280":
                    temperature = sensor_data["Data"][i]["Value"]["Temperature"]
                    print(f"Temperature: {temperature} degC")
                    humidity = sensor_data["Data"][i]["Value"]["Humidity"]
                    print(f"Humidity: {humidity} %")
                    pressure = sensor_data["Data"][i]["Value"]["Pressure"]
                    print(f"Air pressure: {pressure} hPa")

                # Sensirion SCD30
                if data["Sensor"] == "SCD30":
                    CO2 = sensor_data["Data"][i]["Value"]["CO2"]
                    print(f"CO2: {CO2} ppm")

                else:
                    logger.error("Expected sensor not found in unpacked data")

            # 1) thermal comfort (Fanger's PMV/PPD model)
            pmvppd = thermal_comfort_pmvppd(tdb=temperature, rh=humidity)
            ## Predicted Mean Vote from –3 to +3 corresponding to the categories: cold, cool, slightly cool, neutral, slightly warm, warm, and hot.
            pmv = pmvppd["pmv"]
            print(f"PMV: {pmv} [-3 ~ +3]")
            ## Predicted Percentage of Dissatisfied (PPD) occupants in %
            ppd = pmvppd["ppd"]
            print(f"PMV: {ppd} [%]")
            ## Predicted clothing insulation value in clo
            clo_predicted = pmvppd["clo"]
            print(f"Predicted clothing: {clo_predicted} [clo]")

            # 2) thermal comfort (adaptive model)
            adaptive_results = thermal_comfort_adaptive(tdb=temperature)
            print("Adaptive thermal comfort results: ", adaptive_results)
            t_comfort_acceptable = adaptive_results[0]
            t_comfort_cat_i_low = adaptive_results[1]
            t_comfort = adaptive_results[2]
            t_comfort_cat_i_up = adaptive_results[3]

            # TODO: Translate the clo value into common and understandable clothing combinations.

            # Indoor Air Quality
            # change the standard if you prefer to use the standards or laws of another region
            # By default it uses European standard EN 16798-1:2019
            iaq_results = iaq_co2(CO2, standard="EN")
            print("IAQ results: ", iaq_results)

            if iaq_results["standard"] in ["LEHB", "SS", "DOSH"]:
                iaq = "Acceptable" if iaq_results["indices"][0] == 1 else "Unacceptable"
            elif iaq_results["standard"] == "HK":
                if iaq_results["indices"][0] == 1:
                    iaq = "Excellent"
                elif iaq_results["indices"][0] == 2:
                    iaq = "Good"
                else:
                    iaq = "Unacceptable"
            elif iaq_results["standard"] == "UBA":
                if iaq_results["indices"][0] == 1:
                    iaq = "Safe"
                elif iaq_results["indices"][0] == 2:
                    iaq = "Conspicuous"
                else:
                    iaq = "Unacceptable"
            else:
                # default: EN standard
                if iaq_results["indices"][0] == 1:
                    iaq = "Excellent"
                elif iaq_results["indices"][0] == 2:
                    iaq = "Good"
                elif iaq_results["indices"][0] == 3:
                    iaq = "Moderate"
                else:
                    iaq = "Bad"

            # TODO: Add support for other IEQ domains like noise, lighting, VOC etc.

            await send_text(
                manager=manager,
                text_message=f"Temperature: {temperature:.1f} °C | Humidity: {humidity:.0f} %\n"
                f"CO2: {CO2:.0f} ppm | Air Quality: {iaq}\n"
                f"PMV: {pmv:.2f}     | PPD: {ppd:.1f} %\n"
                f"Clothing Predicted: {clo_predicted:.2f} clo\n"
                f"Adaptive Comfort Temperature: {t_comfort:.1f} °C",
            )

        else:
            pass


async def send_suggestion(manager):
    # get suggested clothing ensembles indoors, extra clothing outdoors, today's average outdoor temperature and humidity
    (
        clothing_indoor,
        clothing_outdoor,
        tout_avg_today,
        hout_avg_today,
    ) = clothing_suggestion(type="A")

    await send_text(
        manager=manager,
        text_message=f"Today's average outdoor temperature: {tout_avg_today:.1f} °C\n"
        f"Today's average outdoor humidity: {hout_avg_today:.1f} %\n"
        f"Suggested indoor outfits: {clothing_indoor}\n"
        f"Suggested outdoor outfits: {clothing_outdoor}",
    )


async def main():
    # init even g1 glasses
    manager = GlassesManager(left_address=None, right_address=None)
    glasses_connected = await manager.scan_and_connect()
    await send_text(manager=manager, text_message="Hello, World!")

    if glasses_connected:
        try:
            await send_suggestion(manager)  # send clothing suggestions once, no microcontroller required
            # await send_sensordata(manager)  # send sensor data continuously when updated, comment this line if you don't have sensor data
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")

        finally:
            await manager.disconnect_all()
            logger.info("Glasses disconnected.")

    else:
        logger.error("Failed to connect to glasses.")


if __name__ == "__main__":
    asyncio.run(main())
