# coding: utf-8

# In[1]:

################################
#### Author: Mattijn van Hoek ##
####  While working for HKV   ##
################################
from __future__ import print_function

import gzip
import io
from datetime import datetime, timedelta
import collections

import geopandas as gpd
import pandas as pd
import pytz
from shapely.geometry import Point
from zeep import Client, Settings

from ..utils.untangle import parse_raw  # import untangle
from ..utils.wsdl_helper import query
from ..utils.pi_helper import pi_series
from ..utils.simplenamespace import *
from ..timeseries import FewsTimeSeries, FewsTimeSeriesCollection

#import urllib.parse
try:
    import urllib.parse
except ImportError:
    import urlparse
import fire
    
class pi(object):
    """create pi object that can interact with fewspi service
    """

    def __init__(self):
        """
        """
        pass

    class errors(object):
        """
        error class with different errors to provide for fewsPi
        """

        def nosetClient(self):
            """
            error to show that the client is unknown
            """
            raise AttributeError(
                'client unknown. did you set it .setClient()?')

    class utils(object):
        @staticmethod
        def addFilter(self, child):
            setattr(self.Filters, child['id'].replace(".", "_"), {'id': child['id'],
                                                                  'name': child.name.cdata,
                                                                  'description': child.description.cdata})

        @staticmethod
        def event_client_datetime(event, tz_server, tz_client='Europe/Amsterdam'):
            """
            Get datetime object in client time of an XML Element named event with attributes date and time
            input:
            event     : XML Element named event [eg: obj.TimeSeries.series.event[0]]
            tz_server : datetime abbreviation of the server timezone [eg: 'Etc/GMT']
            tz_client : datetime abbreviation of the client timezone [eg: 'Europe/Amsterdam']

            return
            event_client_time : an datetime object of the event in client timezome

            """
            # convert XML element date string to integer list
            event_server_date = list(
                map(int, event['date'].split('-')))  # -> [yyyy, MM, dd]
            event_server_time = list(
                map(int, event['time'].split(':')))  # -> [HH, mm, ss]

            # define server time
            server_time = datetime(event_server_date[0], event_server_date[1], event_server_date[2],
                                   event_server_time[0], event_server_time[1], event_server_time[2],
                                   tzinfo=pytz.timezone(tz_server))
            client_timezone = pytz.timezone(tz_client)

            # returns datetime in the new timezone
            event_client_time = server_time.astimezone(client_timezone)

            return event_client_time

        @staticmethod
        def gzip_str(string_):
            """
            write string to gzip compressed bytes object
            """
            out = io.BytesIO()

            with gzip.GzipFile(fileobj=out, mode='w') as fo:
                fo.write(string_.encode())

            bytes_obj = out.getvalue()
            return bytes_obj

        @staticmethod
        def gunzip_bytes_obj(bytes_obj):
            """
            read string from gzip compressed bytes object
            """
            in_ = io.BytesIO()
            in_.write(bytes_obj)
            in_.seek(0)
            with gzip.GzipFile(fileobj=in_, mode='rb') as fo:
                gunzipped_bytes_obj = fo.read()

            return gunzipped_bytes_obj.decode()

    def setClient(self, wsdl):
        """
        set soap client using a wsdl URL

        Parameters
        ----------
        wsdl: str
            provide a URL string to a fewsPi wsdl service
            (eg. 'http://www.oms-waddenzee.nl:8081/FewsPiService/fewspiservice?wsdl' or
            'http://localhost:8101/FewsPiService?wsdl')
        """
        settings = Settings(xml_huge_tree=True)
        self.client = Client(wsdl=wsdl, settings=settings)
        
    def setQueryParameters(self, prefill_defaults=True):
        return query(prefill_defaults)
    
    def setPiTimeSeries(self, prefill_defaults=True):
        return pi_series(prefill_defaults)
        
    def getTimeZoneId(self):
        """
        get the servers TimeZoneId

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for filters
        #fewsPi.getTimeZoneId = types.SimpleNamespace()

        getTimeZoneId_response = self.client.service.getTimeZoneId()
        # if not hasattr(self,'getTimeZoneId'):
        setattr(self, 'TimeZoneId', getTimeZoneId_response)
        return self.TimeZoneId

    def getFilters(self):
        """
        get the filters known at the pi service, nested filters will be 'unnested'

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for filters

        self.Filters = types.SimpleNamespace()

        getFilters_response = self.client.service.getFilters()
        getFilters_json = parse_raw(getFilters_response)
        #setattr(self.Filters, 'asJSON', getFilters_json)

        # iterate over the filters and set in pi object
        for piFilter in getFilters_json.filters.filter:
            if hasattr(piFilter, 'child'):
                for child in piFilter.child:
                    if hasattr(child, 'child'):
                        for child in child.child:
                            if hasattr(child, 'child'):
                                for child in child.child:
                                    self.utils.addFilter(self, child)
                            self.utils.addFilter(self, child)
                    self.utils.addFilter(self, child)
            self.utils.addFilter(self, piFilter)
        return self.Filters

    def runTask(self, startTime, endTime, workflowId, userId=None, coldStateId=None, scenarioId=None, piParametersXml=None, timeZero=None, clientId=None, piVersion='1.22', description=None):
        """
        get the workflows known at the pi service

        Parameters
        ----------
        clientId: str
        workflowId: str
        startTime: datetime
        timeZero: str,
        endTime: datetime,
        coldStateId: str,
        scenarioId: str,
        coldstateId: str,
        piParametersXml: xml object
        userId: str
        description: str      
        useColdState: boolean    
        piVersion: str
            described the version of XML that is returned from the pi service
            (defaults to 1.22 as current version only can read version 1.22)
        piXmlContent: xml object 

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for task
        self.Task = types.SimpleNamespace()

        try:
            # for embedded FewsPi services
            runTask_response = self.client.service.runTask(
                in0=startTime,
                in1=endTime,
                in2=workflowId,
                in3=clientId,
                in4=timeZero,
                in5=coldStateId,
                in6=scenarioId,
                in7=piParametersXml,
                in8=userId,
                in9=description
            )
        except TypeError:
            # for tomcat FewsPi services
            runTask_response = self.client.service.runTask(
                startTime=startTime,
                endTime=endTime,
                workflowId=workflowId,
                clientId=clientId,
                timeZero=timeZero,
                coldStateId=coldStateId,
                scenarioId=scenarioId,
                piParametersXml=piParametersXml,
                userId=userId,
                description=description
            )

        #runTask_json = parse_raw(runTask_response)
        setattr(self, 'Task',
                {'id': runTask_response}
                )

        return self.Task
        
    def getTaskRunStatus(self, taskId, maxWaitMillis=1000):
        """
        get the parameters known at the pi service given a certain filterId

        Parameters
        ----------
        taskId: str
            provide a taskId 
        maxWaitMillis: int
            maximum allowed waiting time

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """    
        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for task
        self.TaskRunStatus = types.SimpleNamespace()

        try:
            # for embedded FewsPi services
            getTaskRunStatus_response = self.client.service.getTaskRunStatus(
                in0=taskId,
                in1=maxWaitMillis
            )
        except TypeError:
            # for tomcat FewsPi services
            getTaskRunStatus_response = self.client.service.getTaskRunStatus(
                taskId=taskId,
                maxWaitMillis=maxWaitMillis
            )

        if getTaskRunStatus_response == 'C':
            getTaskRunStatus_response = 'completed'
        if getTaskRunStatus_response == 'R':
            getTaskRunStatus_response = 'running'
        if getTaskRunStatus_response == 'P':
            getTaskRunStatus_response = 'pending'        
        
        #runTask_json = parse_raw(runTask_response)
        setattr(self, 'TaskRunStatus',
                {'status': getTaskRunStatus_response}
                )

        return self.TaskRunStatus    
    
    def getParameters(self, filterId='', piVersion='1.22', clientId=''):
        """
        get the parameters known at the pi service given a certain filterId

        Parameters
        ----------
        filterId: st'
            provide a filterId (if not known, try pi.getFilters() first)
        piVersion: str
            described the version of XML that is returned from the pi service
            (defaults to 1.22 as current version only can read version 1.22)
        clientId: str
            clientId of the pi service (defaults to '', not sure if it is really necessary)

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for parameters
        self.Parameters = types.SimpleNamespace()

        try:
            # for embedded FewsPi services
            getParameters_response = self.client.service.getParameters(
                in0=clientId,
                in1=filterId,
                in2=piVersion
            )
        except TypeError:
            # for tomcat FewsPi services
            getParameters_response = self.client.service.getParameters(
                clientId=clientId,
                filterId=filterId,
                piVersion=piVersion
            )

        getParameters_json = parse_raw(getParameters_response)

        # iterate over the filters and set in pi object
        for piParameter in getParameters_json.timeseriesparameters.parameter:
            setattr(self.Parameters, piParameter['id'].replace(".", "_"),
                    {'id': piParameter['id'],
                     'name': piParameter.name.cdata,
                     'parameterType': piParameter.parameterType.cdata,
                     'unit': piParameter.unit.cdata,
                     'displayUnit': piParameter.displayUnit.cdata,
                     'usesDatum': piParameter.usesDatum.cdata})
        return self.Parameters
    
    def getWorkflows(self, piVersion='1.22', clientId=''):
        """
        get the workflows known at the pi service

        Parameters
        ----------
        piVersion: str
            described the version of XML that is returned from the pi service
            (defaults to 1.22 as current version only can read version 1.22)

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for parameters
        self.Workflows = types.SimpleNamespace()

        try:
            # for embedded FewsPi services
            getWorkflows_response = self.client.service.getWorkflows(
                in0=piVersion
            )
        except TypeError:
            # for tomcat FewsPi services
            getWorkflows_response = self.client.service.getWorkflows(
                piVersion=piVersion
            )

        getWorkflows_json = parse_raw(getWorkflows_response)
        
        # iterate over the workflows and set in pi object
        for piWorkflow in getWorkflows_json.workflows.workflow:
            setattr(self.Workflows, piWorkflow['id'].replace(".", "_"),
                    {'id': piWorkflow['id'],
                     'name': piWorkflow.name.cdata,
                     'description': piWorkflow.description.cdata})
        return self.Workflows

    def getLocations(self, filterId='', piVersion='1.22', clientId='', setFormat='geojson'):
        """
        get the locations known at the pi service given a certain filterId

        Parameters
        ----------
        filterId: str
            provide a filterId (if not known, try pi.getFilters() first)
        piVersion: str
            described the version of XML that is returned from the pi service
            (defaults to 1.22 as current version only can read version 1.22)
        clientId: str
            clientId of the pi service (defaults to '', not sure if it is really necessary)
        setFormat: str
            choose the format to return, currently supports 'geojson', 'gdf' en 'dict'
            'geojson' returns GeoJSON formatted output
            'gdf' returns a GeoDataFrame
            'dict' returns a dictionary of locations

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for locations
        self.Locations = types.SimpleNamespace()

        try:
            # for embedded FewsPi services
            getLocations_response = self.client.service.getLocations(
                in0=clientId,
                in1=filterId,
                in2=piVersion
            )
        except TypeError:
            # for embedded FewsPi services
            getLocations_response = self.client.service.getLocations(
                clientId=clientId,
                filterId=filterId,
                piVersion=piVersion
            )

        getLocations_json = parse_raw(getLocations_response)
        setattr(self.Locations, 'geoDatum',
                getLocations_json.Locations.geoDatum.cdata)

        # iterate over the filters and set in pi object
        for piLocations in getLocations_json.Locations.location:
            # check if location starts with a digit, if so prepend with an 'L'
            if piLocations['locationId'][:1].isdigit():
                locId = "L{0}".format(
                    piLocations['locationId']).replace(".", "_")
            else:
                locId = piLocations['locationId'].replace(".", "_")

            # set attributes of object with location items
            setattr(self.Locations, locId,
                    {'locationId': piLocations['locationId'],
                     'shortName': piLocations.shortName.cdata,
                     'lat': piLocations.lat.cdata,
                     'lon': piLocations.lon.cdata,
                     'x': piLocations.x.cdata,
                     'y': piLocations.y.cdata
                     })

        # CREATE dataframe of location rows dictionary
        df = pd.DataFrame(vars(self.Locations)).T
        df = df.loc[df.index != "geoDatum"]
        df[['lon', 'lat']] = df[['lon', 'lat']].apply(
            pd.to_numeric, errors='coerce')

        # CONVERT to geodataframe using latlon for geometry
        geometry = [Point(xy) for xy in zip(df.lon, df.lat)]
        df = df.drop(['lon', 'lat'], axis=1)
        crs = {'init': 'epsg:4326'}
        gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

        setattr(self.Locations, 'asGeoDataFrame', gdf)
        setattr(self.Locations, 'asGeoJSON', gdf.to_json())

        if setFormat == 'geojson':
            return self.Locations.asGeoJSON
        if setFormat == 'gdf':
            return self.Locations.asGeoDataFrame
        if setFormat == 'dict':
            return self.Locations

    def getTimeSeriesForFilter2(self, filterId, parameterIds, locationIds, startTime, endTime,convertDatum=True, useDisplayUnits=False, piVersion='1.22', clientId=None, ensembleId=None, timeZero='', clientTimeZone='Europe/Amsterdam', setFormat='gzip'):
        """
        This function is deprecated, use getTimeSeries instead. 
        Get the timeseries known at the pi service given a certain filter, parameter(s), location(s)

        Parameters
        ----------
        filterId: str
            provide a filterId (if not known, try pi.getFilters() first)
        parameterIds: str, array of str
            provide the parameter of interest, also (should) accept an array with parameters if multiple are required
        locationIds: str, array of str
            provide the location of interest, also (should) accept an array with locations if multiple are required
        startTime: datetime object
            provide the start time from which you want to extract time series, should be datetime object
            (eg. pd.Timestamp('2018-1-18 23:00', tz='Etc/GMT')) # offset is in seconds
        endTime: datetime object
            provide the end time from which you want to extract time series, should be datetime object. Currently should
            provide tzinfo as well, otherwise timeZero cannot be computed
            (eg. pd.Timestamp('2018-1-18 23:00', tz='Etc/GMT')) # offset is in seconds
        convertDatum: boolean
            Option to convert values from relative to location height to absolute values (True). If False values remain relative. (default is True)
        useDisplayUnits: boolean
            Option to export values using display units (True) instead of database units (False) (boolean, default is False)
        piVersion: str
            described the version of XML that is returned from the pi service
            (defaults to 1.22 as current version only can read version 1.22)
        clientId: str
            clientId of the pi service (defaults to None, not sure if it is really necessary)
        ensembleId: str
            ensembleId (defaults to None)
        timeZero: datetime object
            Forecast time zero. (will default be same as endTime)
        clientTimeZone: str
            set the timezone of the output data, accepts timezones known by pytz module (defaults to 'Europe/Amsterdam')
        setFormat: str
            choose the format to return, currently supports 'geojson', 'gdf' en 'dict'
            'json' returns JSON formatted output
            'df' returns a DataFrame
            'gzip' returns a Gzip compresed JSON string

        all the results of get*** functions are also written back in the class object without 'get'
        (eg result of pi.getTimeZoneId() is stored in pi.TimeZoneId)
        """

        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for Timeseries
        self.TimeSeries = types.SimpleNamespace()

        # set TimeZoneId
        self.getTimeZoneId()

        if startTime.tzinfo is None or startTime.tzinfo.utcoffset(startTime) is None:
            startTime.replace(tzinfo=pytz.UTC)
            local_tz = pytz.timezone(clientTimeZone)
            startTime = local_tz.localize(startTime)
        if endTime.tzinfo is None or endTime.tzinfo.utcoffset(endTime) is None:
            endTime.replace(tzinfo=pytz.UTC)
            local_tz = pytz.timezone(clientTimeZone)
            endTime = local_tz.localize(endTime)

        # no real idea what to do with timeZero
        try:
            timeZero = endTime.astimezone(pytz.utc)
        except ValueError:
            timeZero = endTime

        try:
            # for embedded FewsPi services
            getTimeSeries_response = self.client.service.getTimeSeriesForFilter2(
                in0=clientId,
                in1=startTime,
                in2=timeZero,
                in3=endTime,
                in4=filterId,
                in5=locationIds,
                in6=parameterIds,
                in7=convertDatum,
                in8=useDisplayUnits,
                in9=piVersion
            )
        except TypeError:
            getTimeSeries_response = self.client.service.getTimeSeriesForFilter2(
                clientId=clientId,
                startTime=startTime,
                timeZero=timeZero,
                endTime=endTime,
                filterId=filterId,
                locationIds=locationIds,
                parameterIds=parameterIds,
                convertDatum=convertDatum,
                useDisplayUnits=useDisplayUnits,
                ensembleId=ensembleId,
                piVersion=piVersion
            )

        getTimeSeries_json = parse_raw(getTimeSeries_response)

        timeZoneValue = int(
            float(getTimeSeries_json.TimeSeries.timeZone.cdata))
        if timeZoneValue >= 0:
            timeZone = "Etc/GMT+" + str(timeZoneValue)
        else:
            timeZone = "Etc/GMT-" + str(timeZoneValue)

        # empty dictionary to fill with dictionary format of each row
        # method adopted to avoid appending to pandas dataframe
        event_attributes = ['value', 'flag']
        rows_ts_dict = {}
        rows_latlon_list = []

        # start iteration
        for series in getTimeSeries_json.TimeSeries.series:
            # initiate empty lists
            moduleInstanceId = []
            locationId = []

            stationName = []
            parameterId = []
            units = []

            event_datetimes = []
            event_values = []
            event_flags = []

            # collect metadata
            # GET moduleInstanceId
            try:
                moduleInstanceId.append(series.header.moduleInstanceId.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET locationId
            try:
                locationId.append(series.header.locationId.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET lat
            try:
                lat = float(series.header.lat.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET lon
            try:
                lon = float(series.header.lon.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET stationNames
            try:
                stationName.append(series.header.stationName.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET parameterId
            try:
                parameterId.append(series.header.parameterId.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET units
            try:
                units.append(series.header.units.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET data values
            for event in series.event:
                event_datetimes.append(self.utils.event_client_datetime(
                    event, tz_server=timeZone, tz_client=clientTimeZone))
                event_values.append(float(event['value']))
                event_flags.append(int(event['flag']))

            # PUT timeseries info into row dictionary
            dataValuesFlags = [event_values, event_flags]
            multiColumns = pd.MultiIndex.from_product([moduleInstanceId, parameterId, units, locationId, stationName, event_attributes],
                                                      names=['moduleInstanceIds', 'parameterIds', 'units', 'locationIds', 'stationName', 'event_attributes'])
            df_ts_dict = pd.DataFrame(
                dataValuesFlags, index=multiColumns, columns=event_datetimes).T.to_dict()

            # PUT timeseries row in dictionary of rows
            rows_ts_dict.update(df_ts_dict)

        #     # PUT latlon/location info into row dictionary
        #     df_latlon_dict = pd.DataFrame([{'stationName':stationName[0],'lat':lat,'lon':lon}]).to_dict(orient='split')
        #     print (df_latlon_dict)

            # PUT latlon/location row in dictionary of rows
            rows_latlon_list.append(
                {'stationName': stationName[0], 'Lat': lat, 'Lon': lon})

        # CREATE dataframe of timeseries rows dictionary
        df_timeseries = pd.DataFrame(rows_ts_dict)

        # reset the multiIndex and create a stacked DataFrame and convert to row-oriented JSON object
        df_timeseries = df_timeseries.stack([0, 1, 2, 3, 4]).rename_axis(
            ['date', 'moduleId', 'parameterId', 'units', 'locationId', 'stationName'])

        # prepare settings for database ingestion
        entry = parameterId[0]+'|'+locationId[0]+'|'+units[0]

        setattr(self.TimeSeries, 'asDataFrame', df_timeseries)
        setattr(self.TimeSeries, 'asJSON', df_timeseries.reset_index().to_json(
            orient='records', date_format='iso'))
        setattr(self.TimeSeries, 'asGzip',
                self.utils.gzip_str(self.TimeSeries.asJSON))

        if setFormat == 'json':
            return self.TimeSeries.asJSON, entry
        elif setFormat == 'df':
            return self.TimeSeries.asDataFrame, entry
        elif setFormat == 'gzip':
            #json_timeseries = df_timeseries.reset_index().to_json(orient='records', date_format='iso')
            # self.utils.gzip_str(json_timeseries), entry
            return self.TimeSeries.asGzip, entry

    def getTimeSeries(self, queryParameters, setFormat='gzip', print_response=False):
        """
        get the timeseries known at the pi service given dict of query parameters

        Parameters
        ----------
        queryParameters: dict
            soap request parameters, use function setQueryParameters to set the dictioary
        setFormat: str
            choose the format to return, currently supports 'geojson', 'gdf' en 'dict'
                'json' returns JSON formatted output
                'df' returns a DataFrame
                'gzip' returns a Gzip compresed JSON string
        print_response: boolean
            if True, prints the xml return
        """

        
        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for Timeseries
        self.TimeSeries = types.SimpleNamespace()
        
        # set TimeZoneId
        self.getTimeZoneId()       
        
        # check if input is a queryParameters is class and not dictionary
        if not isinstance(queryParameters, collections.Mapping):
            # if so try extract the query
            queryParameters = queryParameters.query

        # for embedded FewsPi services
        getTimeSeries_response = self.client.service.getTimeSeries(
            queryParameters)
        if print_response == True:
            print(getTimeSeries_response)

        getTimeSeries_json = parse_raw(getTimeSeries_response)

        # empty dictionary to fill with dictionary format of each row
        # method adopted to avoid appending to pandas dataframe
        event_attributes = ['value', 'flag']
        rows_ts_dict = {}
        rows_latlon_list = []

        timeZoneValue = int(
            float(getTimeSeries_json.TimeSeries.timeZone.cdata))
        # Etc/GMT* follows POSIX standard, including counter-intuitive sign change: see https://stackoverflow.com/q/51542167/2459096
        if timeZoneValue >= 0:
            timeZone = "Etc/GMT-" + str(timeZoneValue)
        else:
            timeZone = "Etc/GMT+" + str(timeZoneValue)

        # start iteration
        for series in getTimeSeries_json.TimeSeries.series:
            # initiate empty lists
            moduleInstanceId = []
            qualifierId = []
            locationId = []

            stationName = []
            parameterId = []
            units = []

            event_datetimes = []
            event_values = []
            event_flags = []

            # collect metadata
            # GET qualifierId
            try:
                qualifierId.append(series.header.qualifierId.cdata)
            except AttributeError as e:
                qualifierId.append('')
                print('warning:', e)

            # GET moduleInstanceId
            try:
                moduleInstanceId.append(series.header.moduleInstanceId.cdata)
            except AttributeError as e:
                moduleInstanceId.append('')
                print('warning:', e)

            # GET locationId
            try:
                locationId.append(series.header.locationId.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET lat
            try:
                lat = float(series.header.lat.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET lon
            try:
                lon = float(series.header.lon.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET stationNames
            try:
                stationName.append(series.header.stationName.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET parameterId
            try:
                parameterId.append(series.header.parameterId.cdata)
            except AttributeError as e:
                print('warning:', e)

            # GET units
            try:
                units.append(series.header.units.cdata)
            except AttributeError as e:
                print('warning:', e)

            if hasattr(series, 'event'):
                # GET data values
                for event in series.event:
                    event_datetimes.append(self.utils.event_client_datetime(
                        event, tz_server=timeZone, tz_client=queryParameters['clientTimeZone']))
                    event_values.append(float(event['value']))
                    event_flags.append(int(event['flag']))

            # PUT timeseries info into row dictionary
            dataValuesFlags = [event_values, event_flags]
            multiColumns = pd.MultiIndex.from_product([moduleInstanceId, qualifierId,
                                                       parameterId, units,
                                                       locationId, stationName, event_attributes],
                                                      names=['moduleInstanceIds', 'qualifierIds',
                                                             'parameterIds', 'units',
                                                             'locationIds', 'stationName', 'event_attributes'])
            df_ts_dict = pd.DataFrame(
                dataValuesFlags, index=multiColumns, columns=event_datetimes).T.to_dict()

            # PUT timeseries row in dictionary of rows
            rows_ts_dict.update(df_ts_dict)

            # PUT latlon/location row in dictionary of rows
            rows_latlon_list.append(
                {'stationName': stationName[0], 'Lat': lat, 'Lon': lon})

        # CREATE dataframe of timeseries rows dictionary
        df_timeseries = pd.DataFrame(rows_ts_dict)

        # reset the multiIndex and create a stacked DataFrame and convert to row-oriented JSON object
        df_timeseries = df_timeseries.stack([0, 1, 2, 3, 4, 5]).rename_axis(
            ['date', 'moduleInstanceId', 'qualifierId', 'parameterId', 'units', 'locationId', 'stationName'])

        # prepare settings for database ingestion
        entry = moduleInstanceId[0]+'|'+qualifierId[0] + \
            '|'+parameterId[0]+'|'+locationId[0]+'|'+units[0]

        setattr(self.TimeSeries, 'asDataFrame', df_timeseries)
        setattr(self.TimeSeries, 'asJSON', df_timeseries.reset_index().to_json(
            orient='records', date_format='iso'))
        setattr(self.TimeSeries, 'asGzip',
                self.utils.gzip_str(self.TimeSeries.asJSON))

        if setFormat == 'json':
            return self.TimeSeries.asJSON, entry
        elif setFormat == 'df':
            return self.TimeSeries.asDataFrame, entry
        elif setFormat == 'gzip':
            # self.utils.gzip_str(json_timeseries), entry
            return self.TimeSeries.asGzip, entry


    def getFewsTimeSeries(self, queryParameters, print_response=False):
        """
        Get timeseries from the pi service given a dict of query parameters. 
        Return FewsTimeSeriesCollection object

        Parameters
        ----------
        queryParameters: dict
            soap request parameters, use function setQueryParameters to set the dictioary

        print_response: boolean
            if True, prints the xml return


        Returns
        -------
        obj: FewsTimeSeriesCollection
            object containing timeseries data

        """

        
        if not hasattr(self, 'client'):
            self.errors.nosetClient()

        # set new empty attribute in object for Timeseries
        self.TimeSeries = types.SimpleNamespace()
        
        # set TimeZoneId
        self.getTimeZoneId()       
        
        # check if input is a queryParameters is class and not dictionary
        if not isinstance(queryParameters, collections.Mapping):
            # if so try extract the query
            queryParameters = queryParameters.query

        # for embedded FewsPi services
        getTimeSeries_response = self.client.service.getTimeSeries(queryParameters)
        if print_response == True:
            print(getTimeSeries_response)

        pi_timeseries = FewsTimeSeriesCollection.from_pi_xml(io.StringIO(getTimeSeries_response))
        
        return pi_timeseries

    def getAvailableTimeZones(self):
        """
        get the list of available time zones
        """
        return pytz.all_timezones



