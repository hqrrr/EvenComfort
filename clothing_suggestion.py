from thermal_comfort import clo_prediction
from get_weather import th_outdoor_avg_today
from pythermalcomfort.models import pmv_ppd

"""
Total clothing insulation of typical ensembles.
Based on ASHRAE55:2017 - Table 5.2.2.2 A/B.
All clothing ensembles, except where otherwise indicated in parentheses, include shoes, socks,
and briefs or panties. All skirt/dress clothing ensembles include pantyhose and no additional socks.
"""
# Type A
clo_indoor_typical_ensembles_typeA = {
    "Walking shorts, short-sleeve shirt": 0.36,
    "Trousers, short-sleeve shirt, socks, shoes, underwear": 0.57,
    "Trousers, long-sleeve shirt": 0.61,
    "Sweat pants, long-sleeve sweatshirt": 0.74,
    "Sweat pants, long-sleeve sweatshirt, boots": 0.82,
    "Trousers, long-sleeve shirt plus suit jacket": 0.96,
    "Trousers, long-sleeve shirt plus long-sleeve sweater, t-shirt": 1.01,
    "Trousers, long-sleeve shirt plus suit jacket, vest, t-shirt": 1.14,
}

# Type B
clo_indoor_typical_ensembles_typeB = {
    "Walking shorts, short-sleeve shirt": 0.36,
    "Thin long-sleeve shirtdress": 0.41,
    "Knee-length skirt, short-sleeve shirt, sandals": 0.54,
    "Knee-length skirt, long-sleeve shirt, full slip": 0.67,
    "Sweat pants, long-sleeve sweatshirt": 0.74,
    "Sweat pants, long-sleeve sweatshirt, boots": 0.82,
    "Knee-length skirt, long-sleeve shirt, half slip, suit jacket": 1.04,
    "Knee-length skirt, long-sleeve shirt, half slip, long-sleeve sweater": 1.10,
}

"""
Typical thermal insulation values for individual outdoor garments.
Based on ISO 9920:2007 - Table B.1/B.2
"""
clo_outdoor_typical = {
    "No additional jacket needed": 0,
    "Vest": 0.17,
    "Light jacket": 0.249,
    "Jacket": 0.351,
    "Heavy jacket": 0.4,
    "Down jacket": 0.55,
    "Parka": 0.7,
    "Heavy Parka": 0.8,
    "Heavy Parka, thick socks and gloves": 1.0,
}


def clothing_suggestion(type="A") -> list:
    # predict clothing indoors based on outdoor temperature at 6 a.m.
    clo_indoor_predicted = clo_prediction()
    print("clo_indoor_predicted: ", clo_indoor_predicted)
    # find the closest insulation value of typical ensembles
    if type == "A":
        closest_ensembles_indoor, closest_clo_indoor = min(
            clo_indoor_typical_ensembles_typeA.items(),
            key=lambda x: abs(clo_indoor_predicted - x[1]),
        )
    else:
        closest_ensembles_indoor, closest_clo_indoor = min(
            clo_indoor_typical_ensembles_typeB.items(),
            key=lambda x: abs(clo_indoor_predicted - x[1]),
        )
    print("closest_ensembles_indoor: ", closest_ensembles_indoor)
    print("closest_clo_indoor: ", closest_clo_indoor)

    # For reference only, may not be accurate since Fanger's PMV/PPD model is primarily designed for indoor thermal environments.
    # Get today's average air temperature outdoors
    tout_avg_today, hout_avg_today = th_outdoor_avg_today()
    print(f"tout_avg_today: {tout_avg_today} °C")
    print(f"hout_avg_today: {hout_avg_today} %")
    # met for slow walking (2 km/h)
    met = 1.9
    # calculate PMV outdoors with suggested clothing ensembles indoors
    pmv_outdoor = pmv_ppd(tdb=tout_avg_today, tr=tout_avg_today, vr=0, rh=hout_avg_today, met=met, clo=closest_clo_indoor, limit_inputs=False)
    print(pmv_outdoor)

    # calculate extra clo needed to reach abs(PMV) <= 0.2 (category I in EN 16798-1)
    clo_extra = 0
    while abs(pmv_outdoor["pmv"]) > 0.2:
        clo_extra += 0.05
        clo = closest_clo_indoor + clo_extra
        # assume radiant temperature is equal to air temperature. The influence of sunlight is not taken into account.
        pmv_outdoor = pmv_ppd(tdb=tout_avg_today, tr=tout_avg_today, vr=0, rh=hout_avg_today, met=met,
                              clo=clo, limit_inputs=False)

    print("Extra clothing required for outdoor activities: ", clo_extra)
    closest_garment_outdoor, closest_clo_outdoor = min(
        clo_outdoor_typical.items(),
        key=lambda x: abs(clo_extra - x[1]),
    )
    print("closest_garment_outdoor: ", closest_garment_outdoor)
    print("closest_clo_outdoor: ", closest_clo_outdoor)

    return [closest_ensembles_indoor, closest_garment_outdoor, tout_avg_today, hout_avg_today]


if __name__ == "__main__":
    clothing_suggestion()
