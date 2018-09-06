from .io.soap_fewspi import pi
from .timeseries import FewsTimeSeries, FewsTimeSeriesCollection

__doc__ = """package for accessing fewspi service"""
__version__ = '0.5.9'

pi = pi()

if __name__ == '__main__':
    try:
        # for command line requests
        fire.Fire(pi)
        #pi = pi()
    except:
        # for jupyter notebooks
        #pi = pi()
        pass
