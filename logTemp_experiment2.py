"""
A script for recording heating and cooling curves

"""

if __name__ == "__main__":
    import time
    import datetime
    import pigpio
    import DHT22
    import pandas as pd
    from math import floor

    # Set pins
    heater_pin = 27
    fan_pin = 17


    # find information on box config
    df_config = pd.read_csv('config.csv')

    # Intervals of about 2 seconds or less will eventually hang the DHT22.
    INTERVAL = df_config["TempLogInterval_sec"]
    window = df_config["TempDisplayWindow_sec"]
    maxSamples = floor(window/INTERVAL) #the number of rows of data to be held in short term storage

    df_s = pd.read_csv('tempData_shortTerm.csv')
    numSamples = df_s.shape[0] #number of rows of data already stored in short term storage

    #controls
    #tempSetPoint = df_config['TempSetPoint'].values[0]
    #tempSetPointList = [26,28,30,32,34]
    i = 0
    tempSetPoint = 26 #tempSetPointList[i]
    margin = 0.2

    #pi_fan = pigpio.pi()
   # pi_heater = pigpio.pi()



    pi = pigpio.pi()
    s = DHT22.sensor(pi, 24)
    r = 0
    next_reading = time.time()

    pi.set_mode(fan_pin, pigpio.OUTPUT)
    pi.set_mode(heater_pin, pigpio.OUTPUT)

    #initialize fan and heater off
    pi.write(fan_pin, 0)
    pi.write(heater_pin, 0)
    HeaterStatus = "OFF"
    FanStatus =  "OFF"


    try:
        while True:
            timeStamp = datetime.datetime.now().isoformat()
            r += 1
            s.trigger()
            time.sleep(0.2)
            next_reading += INTERVAL
            time.sleep(next_reading-time.time()) # Overall INTERVAL second polling.
            vals = {"Time":timeStamp,
                    "TemperatureC":s.temperature(),
                    "Humidity": s.humidity(),
                    "HeaterStatus": HeaterStatus,
                    "HumidifierStatus": "OFF",
                    "FanStatus": FanStatus
                    }
            print(vals)
            if (numSamples < maxSamples):
                df_s = df_s.append(vals, ignore_index=True)
                df_s.to_csv('tempData_shortTerm.csv', index=False)
                numSamples = numSamples + 1
            else:
                df_s = df_s.iloc[1:]
                df_s = df_s.append(vals, ignore_index=True)
                df_s.to_csv('tempData_shortTerm.csv', index=False)
            if (vals["TemperatureC"] < tempSetPoint-margin and (HeaterStatus == "OFF")):
                pi.write(heater_pin, 1)
                HeaterStatus = "ON"
                #pi.write(fan_pin, 0)
                #FanStatus = "OFF"
            elif (vals["TemperatureC"] > tempSetPoint+margin and (HeaterStatus == "ON")):
                pi.write(heater_pin, 0)
                HeaterStatus = "OFF"
                #pi.write(fan_pin, 1)
                #FanStatus = "ON"
            if r % 1200 == 0: # every hour
                if r == 1200 * 1:
                    tempSetPoint = 28
                elif r == 1200 * 2:
                    tempSetPoint = 30
                elif r == 1200 * 3:
                    tempSetPoint = 32
                elif r == 1200 * 4:
                    tempSetPoint = 34
                elif r == 1200 * 5:
                    tempSetPoint = 34
                elif r == 1200 * 6:
                    tempSetPoint = 26
    finally:
        pi.write(heater_pin, 0)
        pi.write(fan_pin, 0)
        s.cancel()
        pi.stop()