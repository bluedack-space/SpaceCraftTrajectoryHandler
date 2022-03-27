import requests

class SpaceCraftTrajectoryHandler():

    @staticmethod
    def getTLE(CATNR=None,withOutputFile=False,fnameTextTLE=None):
        response = requests.get('https://celestrak.com/satcat/tle.php?CATNR='+str(CATNR), verify=False)
        #print(response.status_code)
        print(response.text) 
        tle = response.text

        if withOutputFile and fnameTextTLE!=None:
            f = open('raise2.txt', 'w')
            f.write(tle)
            f.close()
        elif withOutputFile==False:
            return tle

    @staticmethod
    def getSpaceCraftByTLE(fnameTextTLE=None,ScName=None):
        from skyfield.api import load
        satellites = load.tle(fnameTextTLE)
        SC         = satellites[ScName]
        return SC

    @staticmethod
    def propageteTrajectory(SC,dt0,timeDelta,nmax,withOutputExcel=False,fnameExcel=None):
        from skyfield.api import load
        ts        = load.timescale() 

        resultSet = []
        for n in range(nmax):
            if n==0:
                dt_c            = dt0
            else:
                dt_c            = dt_c + timeDelta

            t0                  = ts.utc(dt_c.year, dt_c.month, dt_c.day, dt_c.hour, dt_c.minute)
            geocentric          = SC.at(t0)  
            llh                 = geocentric.subpoint()

            #x_eci, y_eci, z_eci = geocentric.position.km

            latitude_deg        = llh.latitude.degrees
            longitude_deg       = llh.longitude.degrees
            altitude_km         = llh.elevation.km

            import pymap3d as pm
            x_ecef,y_ecef,z_ecef = pm.geodetic2ecef(latitude_deg, longitude_deg, altitude_km*1000.0)

            result = [ str(dt_c), x_ecef*0.001, y_ecef*0.001, z_ecef*0.001, latitude_deg, longitude_deg, altitude_km ]

            resultSet.append(result)

        if withOutputExcel and fnameExcel!=None:
            import pandas as pd
            df = pd.DataFrame(resultSet)
            df.columns = ["Time","X-ECEF[km]","Y-ECEF[km]","Z-ECEF[km]","Latitude[deg]","Longitude[km]","Altitude[km]"]
            df.to_excel(fnameExcel,sheet_name="trajectory", index=False)

        return resultSet

if __name__ == '__main__':

    fnameTextTLE = "iss.txt"
    ScName       = "ISS (ZARYA)"
    CATNR        = 25544
    fnameExcel  = "./traj.xlsx"

    import datetime
    #dt = datetime.datetime(2022, 3, 26, 20, 0, 0, 0)
    dt = datetime.datetime.now()

    SpaceCraftTrajectoryHandler.getTLE(CATNR=CATNR,withOutputFile=True,fnameTextTLE=fnameTextTLE)

    SC            = SpaceCraftTrajectoryHandler.getSpaceCraftByTLE(fnameTextTLE=fnameTextTLE,ScName=ScName)

    dt_minutes    = 3
    total_minutes = 180
    nmax          = int(total_minutes/dt_minutes)

    resultSet     = SpaceCraftTrajectoryHandler.propageteTrajectory(SC=SC,dt0=dt,timeDelta=datetime.timedelta(minutes=dt_minutes),nmax=nmax,withOutputExcel=True,fnameExcel=fnameExcel)

    from PandasHandler import *
    from TrajectoryPlotter import *

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots( rows=1, cols=1, specs=[[{"type":"scatter3d"}]] )

    rowEath  = 1
    colEarth = 1

    TrajectoryPlotter.displayEarth(fig,row=rowEath,col=colEarth)

    filePathExcel_Data = 'traj.xlsx'
    dfSet_Data         = PandasHandler.readAllSheets_Excel(filePathExcel_Data)
    sheetNames         = PandasHandler.getSheetNames_Excel(filePathExcel_Data)
    index              = sheetNames.index('trajectory')
    df_Data            = dfSet_Data[index]

    fig.add_trace( go.Scatter3d( x=df_Data["X-ECEF[km]"], y=df_Data["Y-ECEF[km]"], z=df_Data["Z-ECEF[km]"], mode='lines', marker=dict(size=2, color='red'), line=dict(color='fuchsia',width=5), name="Trajectory"), row=rowEath, col=colEarth)

    fig.show()
    fig.write_html("resultAsPlotly.html")
