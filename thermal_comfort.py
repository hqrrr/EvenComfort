from pythermalcomfort.models import pmv_ppd, clo_tout
from pythermalcomfort.models.adaptive_en import adaptive_en
from pythermalcomfort.utilities import (
    v_relative,
    clo_dynamic,
    running_mean_outdoor_temperature,
)
from get_weather import t_outdoor_6am, t_outdoor_avg_past7days
from datetime import datetime


updated = None
last_update_date = None
tout_6am = None


def clo_prediction() -> float:
    """
    Predict clothing today based on outdoor air temperature at 06:00 a.m.
    No need to manually enter your current clothing insulation value.
    The outdoor air temperature is updated only once a day.

    Returns
    -------
    clo_prediction: float
        predicted clothing insulation value [clo]
    """
    global updated
    global last_update_date
    global tout_6am

    if updated is True:
        time_difference = datetime.now() - last_update_date
        # if last update was more than one day ago, set updated status to False
        if time_difference.days >= 1:
            updated = False

    else:
        tout_6am = t_outdoor_6am()
        # refresh update status
        last_update_date = datetime.now()
        updated = True

    clo_predicted = clo_tout(tout_6am)

    return clo_predicted


def thermal_comfort_pmvppd(tdb, rh, tr=None, v=0, met=1.2) -> dict:
    """
    Returns 1) Predicted Mean Vote (PMV) from –3 to +3 corresponding to the categories:
    cold, cool, slightly cool, neutral, slightly warm, warm, and hot.
    2) Predicted Percentage of Dissatisfied (PPD) occupants in %.

    Parameters
    ----------
    tdb: float, int
        dry bulb air temperature in [°C] measured by air temperature sensor
    rh: float, int
        relative humidity in [%] measured by humidity sensor
    tr: float, int, optional
        mean radiant temperature in [°C] measuremd by globe thermometer.
        If radiant temperature not given, assume it's equal to the dry bulb air temperature.
    v: float, int, optional
        air speed indoors in [m/s].
        If air speed not given, assume it's equal to 0.
    met: float, int, optional
        metabolic rate in [met]. Defaults to 1.2 met (for seated office work regarding ISO 7730)

    Returns
    -------
    Returns PMV (-3 ~ +3), PPD (%) and predicted clothing (clo) in a dict

    Notes
    -----
    Because the Fanger model is a group model rather than an individual model,
    it is impossible for the PPD to reach 0%, i.e. for everyone to be satisfied with the current indoor environment.

    Examples
    --------
    >>> from thermal_comfort import thermal_comfort_pmvppd
    >>> print(thermal_comfort_pmvppd(tdb=20,rh=50)) # 20 degreeC and 50% humidity
    """
    # if radiant temperature not given, assume it's equal to the dry bulb air temperature.
    if tr is None:
        tr = tdb

    # calculate relative air speed
    v_r = v_relative(v=v, met=met)

    # predict clothing based on outdoor temperature at 6 a.m.
    clo = clo_prediction()
    # calculate dynamic clothing
    clo_d = clo_dynamic(clo=clo, met=met)
    results = pmv_ppd(tdb=tdb, tr=tr, vr=v_r, rh=rh, met=met, clo=clo_d)
    # add predicted clo in results for daily clothing suggestion
    results["clo"] = clo

    return results


def thermal_comfort_adaptive(tdb, tr=None, v=0) -> list:
    """
    Returns results based on adaptive thermal comfort model (EN 16798-1:2019):
    1) Acceptability of the current indoor thermal conditions (comply with comfort category I)
    2) Calculated ideal comfort temperature at that specific running mean temperature in [°C]
    3) lower & upper limits of acceptable indoor temperature range in [°C] (category I in EN 16798-1:2019)

    Parameters
    ----------
    tdb: float, int
        dry bulb air temperature in [°C] measured by air temperature sensor
    tr: float, int, optional
        mean radiant temperature in [°C] measuremd by globe thermometer.
        If radiant temperature not given, assume it's equal to the dry bulb air temperature.
    v: float, int, optional
        air speed indoors in [m/s].
        If air speed not given, assume it's equal to 0.

    Returns
    -------
    t_comfort_acceptable: bool
        if current indoor temperature acceptable, True or False
    t_comfort_cat_i_low: float
        lower limit of acceptable indoor temperature range in [°C] (category I in EN 16798-1:2019)
    t_comfort: float
        calculated ideal comfort temperature at that specific running mean temperature in [°C]
    t_comfort_cat_i_up: float
        upper limit of acceptable indoor temperature range in [°C] (category I in EN 16798-1:2019)
    """
    # if radiant temperature not given, assume it's equal to the dry bulb air temperature.
    if tr is None:
        tr = tdb

    # calculate running mean temperature
    tout_avg_past7days_ls = t_outdoor_avg_past7days()
    t_runningmean = running_mean_outdoor_temperature(tout_avg_past7days_ls, alpha=0.8)

    # Adaptive thermal comfort model based on EN 16798-1:2019
    results = adaptive_en(tdb, tr, t_runningmean, v, limit_inputs=False)
    # if current indoor temperature acceptable
    t_comfort_acceptable = bool(results["acceptability_cat_i"])
    # lower limit of acceptable range (category I in EN 16798-1:2019)
    t_comfort_cat_i_low = float(results["tmp_cmf_cat_i_low"])
    # calculated ideal comfort temperature
    t_comfort = float(results["tmp_cmf"])
    # upper limit of acceptable range (category I in EN 16798-1:2019)
    t_comfort_cat_i_up = float(results["tmp_cmf_cat_i_up"])

    return [t_comfort_acceptable, t_comfort_cat_i_low, t_comfort, t_comfort_cat_i_up]


if __name__ == "__main__":
    a = thermal_comfort_adaptive(18)
    print(a)
