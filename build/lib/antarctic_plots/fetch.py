import pooch
import pandas as pd
from pyproj import Transformer
import xarray as xr
import pygmt

def imagery():
    """
    Antarctic imagery from LIMA: https://lima.usgs.gov/fullcontinent.php
    will replace with belowonce figured out login issue with pooch
     MODIS Mosaic of Antarctica: https://doi.org/10.5067/68TBT0CGJSOJ
    Assessed from https://daacdata.apps.nsidc.org/pub/DATASETS/nsidc0730_MEASURES_MOA2014_v01/geotiff/
    """
    img = pooch.retrieve(
        # url="https://daacdata.apps.nsidc.org/pub/DATASETS/nsidc0730_MEASURES_MOA2014_v01/geotiff/moa750_2014_hp1_v01.tif",
        url='https://lima.usgs.gov/tiff_90pct.zip',
        processor=pooch.Unzip(),
        known_hash=None,)[0]
    return img

def groundingline():
    """
    Antarctic groundingline shape file, from https://doi.pangaea.de/10.1594/PANGAEA.819147
    Supplement to Depoorter et al. 2013: https://doi.org/10.1038/nature12567
    """
    groundingline = pooch.retrieve(
        url="https://doi.pangaea.de/10013/epic.42133.d001",
        known_hash=None,
        processor=pooch.Unzip(),)[3]
    return groundingline

def basement(plot=False, info=False):
    """
    Offshore and sub-Ross Ice Shelf basement topography.
    from Tankersley et al. 2022: https://onlinelibrary.wiley.com/doi/10.1029/2021GL097371
    offshore data from Lindeque et al. 2016: https://doi.org/10.1002/2016GC006401
    """
    path = pooch.retrieve(
        url="https://download.pangaea.de/dataset/941238/files/Ross_Embayment_basement_filt.nc",
        known_hash=None,
        )
    grd = xr.load_dataarray(path)
    if plot==True:
        grd.plot(robust=True)
    if info==True:
        print(pygmt.grdinfo(grd))
    return grd

def bedmap2(layer, plot=False, info=False):
    """
    bedmap2 data, from https://doi.org/10.5194/tc-7-375-2013.
    layer is one of following strings: 
        thickness, bed, surface, geoid2wgs
    """
    bedmap2 = pooch.retrieve(
        url="https://secure.antarctica.ac.uk/data/bedmap2/bedmap2_tiff.zip",
        known_hash=None,
        processor=pooch.Unzip(),)
    if layer=='thickness':
        path=bedmap2[11]
    if layer=='bed':
        path=bedmap2[29]
    if layer=='surface':
        path=bedmap2[39]
    if layer=='geoid2wgs':
        path=bedmap2[26]

    grd = xr.load_dataarray(path)
    grd = grd.squeeze()

    if layer=='surface':
        grd = grd.fillna(0)

    if plot==True:
        grd.plot(robust=True)
    if info==True:
        print(pygmt.grdinfo(grd))
    return grd

def deepbedmap(plot=False, info=False, region=None, spacing=10e3):
    """
    DeepBedMap, from Leong and Horgan, 2020: https://doi.org/10.5194/tc-14-3687-2020
    Accessed from https://zenodo.org/record/4054246#.Ysy344RByp0
    """
    if region==None:
        region=(-2700000, 2800000, -2200000, 2300000)

    path = pooch.retrieve(
        url="https://zenodo.org/record/4054246/files/deepbedmap_dem.tif?download=1",
        known_hash=None,
        progressbar=True,)

    grd = pygmt.grdfilter(
        grid=path,
        filter=f'g{spacing}',
        spacing=spacing,
        region=region,
        distance='0',
        nans='r',
        verbose='q')
    # grd = xr.load_dataarray(path)

    if plot==True:
        grd.plot(robust=True)
    if info==True:
        print(pygmt.grdinfo(grd))
    return grd

def gravity(type, plot=False, info=False, region=None, spacing=5e3):
    """
    Preliminary compilation of Antarctica gravity and gravity gradient data.
    Updates on 2016 AntGG compilation.
    Accessed from https://ftp.space.dtu.dk/pub/RF/4D-ANTARCTICA/.
    type is either 'FA' or 'BA', for free-air and bouguer anomalies, respectively.
    """
    if region==None:
        region=(-3330000, 3330000, -3330000, 3330000)

    gravity = pooch.retrieve(
        url="https://ftp.space.dtu.dk/pub/RF/4D-ANTARCTICA/ant4d_gravity.zip",
        known_hash=None,
        processor=pooch.Unzip(),)[5]

    df = pd.read_csv(gravity, delim_whitespace=True, 
                            skiprows=3, names=['id', 'lat', 'lon', 'FA', 'Err', 'DG', 'BA'])

    transformer = Transformer.from_crs("epsg:4326", "epsg:3031")
    df['x'], df['y'] = transformer.transform(df.lat.tolist(), df.lon.tolist())
    df = pygmt.blockmedian(df[["x", "y", type]], 
                            spacing=spacing, 
                            region=region,
                            verbose='q')
    grd = pygmt.surface(data=df[['x','y',type]], 
                                spacing=spacing, 
                                region=region,
                                M='2c',
                                verbose='q')
    if plot==True:
        grd.plot(robust=True)
    if info==True:
        print(pygmt.grdinfo(grd))
    return grd

def magnetics(plot=False, info=False, region=None, spacing=5e3):
    """
    ADMAP-2001 magnetic anomaly compilation of Antarctica.
    https://admap.kongju.ac.kr/databases.html
    Update to use ADMAP2 once non-Geosoft specific file versions are released
    ADMAP2 magnetic anomaly compilation of Antarctica.
    Accessed from https://doi.pangaea.de/10.1594/PANGAEA.892722?format=html#download
    """
    if region==None:
        region=(-3330000, 3330000, -3330000, 3330000)
    # for download .gdb abridged files
    # files = pooch.retrieve(
    #     url="https://hs.pangaea.de/mag/airborne/Antarctica/ADMAP2A.zip",
    #     known_hash=None,
    #     processor=pooch.Unzip(),
    #     progressbar=True)

    file = pooch.retrieve(
            url="https://admap.kongju.ac.kr/admapdata/ant_new.zip",
            known_hash=None,
            processor=pooch.Unzip(),
            progressbar=True)[0]

    df = pd.read_csv(file, delim_whitespace=True, header=None, 
            names=['lat', 'lon', 'nT']
            )
    transformer = Transformer.from_crs("epsg:4326", "epsg:3031")
    df['x'], df['y'] = transformer.transform(df.lat.tolist(), df.lon.tolist())

    df = pygmt.blockmedian(df[["x", "y", 'nT']], 
                            spacing=spacing, 
                            region=region,
                            verbose='q')
    grd = pygmt.surface(data=df[['x','y','nT']], 
                            spacing=spacing, 
                            region=region,
                            M='2c',
                            verbose='q') 

    if plot==True:
        grd.plot(robust=True)
    if info==True:
        print(pygmt.grdinfo(grd))
    return grd

# def geothermal(plot=False, info=False):
#     """
#     Mean geothermal heat flow from various models.
#     From Burton-Johnson et al. 2020: Review article: Geothermal heat flow in Antarctica: current and future directions
#     """
#     path = pooch.retrieve(
#         url="https://doi.org/10.5194/tc-14-3843-2020-supplement",
#         known_hash=None,
#         processor=pooch.Unzip(
#             extract_dir='Burton_Johnson_2020',),)
#     file = [p for p in path if p.endswith('Mean.tif')][0]
#     grd = xr.load_dataarray(file)
#     grd = grd.squeeze()

#     if plot==True:
#         grd.plot(robust=True)
#     if info==True:
#         print(pygmt.grdinfo(grd))
#     return grd