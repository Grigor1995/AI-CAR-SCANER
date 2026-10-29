"""Display conversions only. Domain and stored measurements remain canonical SI."""
import math


def convert(value:float,quantity:str,unit:str)->float:
    if not math.isfinite(value):raise ValueError('Finite engineering value required')
    linear={
        'speed':{'km/h':(1,0),'mph':(1/1.609344,0)},
        'distance':{'km':(1,0),'miles':(1/1.609344,0)},
        'temperature':{'C':(1,0),'F':(9/5,32)},
        'pressure':{'kPa':(1,0),'bar':(.01,0),'psi':(1/6.894757293168,0)},
        'torque':{'Nm':(1,0),'lb-ft':(.737562149277,0)},
        'power':{'kW':(1,0),'hp':(1/.745699871582,0)},
        'volume':{'L':(1,0),'US_gallons':(1/3.785411784,0)}}
    if quantity=='consumption':
        if value<=0:raise ValueError('Positive consumption required')
        if unit=='L/100km':return value
        if unit=='km/L':return 100/value
        if unit=='mpg_US':return 235.214583/value
        raise ValueError('Unsupported unit')
    try:scale,offset=linear[quantity][unit]
    except KeyError as error:raise ValueError('Unsupported quantity/unit') from error
    return value*scale+offset
