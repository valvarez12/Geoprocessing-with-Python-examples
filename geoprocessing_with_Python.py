#---------------- Listin 3.1 ----------------

# This script will print out the names, populations, and coordinates for the first
# 10 features in the dataset. 

import sys
from osgeo import ogr

fn = '/home/valvarez/Downloads/osgeopy/osgeopy-data/global/ne_50m_populated_places.shp'
ds = ogr.Open(fn, 0)
if ds is None:
	sys.exit('Could not open {0}.'.format(fn))
lyr = ds.GetLayer(0)
i = 0 
for feat in lyr:
	pt = feat.geometry()
	x = pt.GetX()
	y = pt.GetY()
	name = feat.GetField('NAME')
	pop = feat.GetField('POP_MAX')
	print name, pop, x, y
	i += 1
	if i == 10:
		break
del ds

# -----------------------------------------

# ------------- Listing 3.3 ---------------

# This script shows how to create a new shapefile that contains only the features
# corresponding to capital cities in the global populated splaces shapfile.

ds = ogr.Open('/home/valvarez/Downloads/osgeopy/osgeopy-data/global', 1)
if ds is None:
	sys.exit('Could not open folder.')
in_lyr = ds.GetLayer('ne_50m_populated_places')

if ds.GetLayer('capital_cities'):
	ds.DeleteLayer('capital_cities')
out_lyr = ds.CreateLayer('capital_cities', 
						 in_lyr.GetSpatialRef(),
						 ogr.wkbPoint)
						
out_lyr.CreateFields(in_lyr.schema)

out_defn = out_lyr.GetLayerDefn()
out_feat = ogr.Feature(out_defn)
for in_feat in in_lyr:
	if in_feat.GetField('FEATURECLA') == 'Admin-0 capital':
		geom = in_feat.geometry()
		out_feat.SetGeometry(geom)
		for i in range(in_feat.GetFieldCount()):
			value = in_feat.GetField(i)
			out_feat.SetField(i, value)
		out_lyr.CreateFeature(out_feat)
		
del ds

# ---------------------------------------

# ----------- Listing 4.2 ---------------

# this is a function that imports all of the layers from a data source 
# into a feature dataset within a file geodatabase, but note that this only works 
# if you have the FileGDB driver. This funciton does not work but still wrote it for practice.

# def layer_to_features_dataset(ds_name, gdb_fn, dataset_name):
# 	""" copy layers to a feature dataset in a file Geodatabase."""
# 	in_ds = ogr.Open(ds_name)
# 	if in_ds is None:
# 		raise Runtime Error('Could not open datasource')
# 	gdb_driver = ogr.GetDriverByName('FileGDB')
# 	if os.path.exists(gdb_fn):
# 		gdb_ds = gdb_driver.Open(gdb_fn, 1)
# 	else:
# 		gdb_ds = gdb_driver.CreateDataSource(gdb_fn)
# 	if gdb_ds is None:
# 		raise RuntimeError('Could not open file geodatabase')
# 	options = ['FEATURE_DATASET=' + dataset_name]
# 	for i in range(in_ds.GetLayerCount()):
# 		lyr = in_ds.GetLayer(i)
# 		lyr_name = lyr.GetName()
# 		print 'Copying ' + lyrt_name + '. . .'
# 		gdb_ds.CopyLayer(lyr, lyr_name, options)

# -------------------------------------

# --------- Listing 4.3 ---------------

# This listing contains a function to retrieve stream gauge data from a WFS and save it as GeoJSON;
# Contains a function to make the web map showing these stream gauges; 
# Contains a function to get a geometry so that the map afocuses on a single state instead of the whole country
# and a couple of helper functions to format data for the WFS request and the map.

import os 
import urllib
import folium

def get_bbox(geom):
	"""Return the bbox based on a geometry envelope."""
	return '{0}, {2}, {1}, {3}'.format(*geom.GetEnvelope())

def get_center(geom):
	"""return the center point of a geometry."""
	centroid = geom.Centroid()
	return [centroid.GetY(), centroid.GetX()]

def get_state_geom(state_name):
	"""Return the geometry for a state."""
	ds = ogr.Open('/home/valvarez/Downloads/osgeopy/osgeopy-data/osgeopy-data/US/states.geojson')
	if ds is None:
		raise RuntimeError(
			'Could not open the States dataset. Is the path correct?')
	lyr = ds.GetLayer()
	lyr.SetAttributeFilter('state = "{0}"'.format(state_name))
	feat = next(lyr)
	return feat.geometry().Clone()

def save_state_gauges(out_fn, bbox=None):
	"""Save stream gauge data to a geojson file."""
	url = 'http://gis.srh.noaa.gov/arcgis/services/ahps_gauges/' + 'MapServer/WFSServer'
	parms = {
		'version': '1.1.0',
		'typeNames': 'ahps_gauges:Observed_River_Stages',
		'srsName': 'urn:ogc:def:crs:EPSG:6.9:4326',
	}
	if bbox:
		parms['bbox'] = bbox
	try:
		request = 'WFS:{0}?{1}'.format(url, urllib.urlencode(parms))
	except:
		request = 'WFS:{0}?{1}'.format(url, urllib.parse.urlencode(parms))
	wfs_ds = ogr.Open(request)
	if wfs_ds is None:
		raise RuntimeError('Could not open WFS.')
	wfs_lyr = wfs_ds.GetLayer(0)
	
	driver = ogr.GetDriverByName('GeoJSON')
	if os.path.exists(out_fn):
		driver.DelteDataSource(out_fn)
	json_ds = driver.CreateDataSource(out_fn)
	json_ds.CopyLayer(wfs_lyr, '')
	
def make_map(state_name, json_fn, html_fn, **kwargs):
	"""Make a folium map."""
	geom = get_state_geom(state_name)
	save_state_gauges(json_fn, get_bbox(geom))
	fmap = folium.Map(location=get_center(geom), **kwargs)
	fmap.geo_json(geo_path=json_fn)
	fmap.create_map(path=html_fn)
	

os.chdir('/home/valvarez/Public/webmaps')
make_map('Oklahoma', 'ok.json', 'ok.html', zoom_start=7)

