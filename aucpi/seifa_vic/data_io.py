import geopandas as gpd
import pandas as pd
from pathlib import Path
from aucpi.files import cached_download
from appdirs import user_cache_dir
from pathlib import Path
import zipfile
import os
import json
from getpass import getpass
from owslib.wfs import WebFeatureService

def get_cached_path(file_name):
	cache_dir= Path(user_cache_dir('aucpi'))
	cache_dir.mkdir(exist_ok=True, parents=True)
	return cache_dir/file_name

def get_data_links():
	out = dict(
		victoria_suburbs = 'https://data.gov.au/geoserver/vic-suburb-locality-boundaries-psma-administrative-boundaries/wfs?request=GetFeature&typeName=ckan_af33dd8c_0534_4e18_9245_fc64440f742e&outputFormat=json',
		victoria_councils = 'https://data.gov.au/geoserver/vic-local-government-areas-psma-administrative-boundaries/wfs?request=GetFeature&typeName=ckan_bdf92691_c6fe_42b9_a0e2_a4cd716fa811&outputFormat=json',
		seifa_suburb_2011= 'https://www.abs.gov.au/AUSSTATS/subscriber.nsf/log?openagent&2033.0.55.001%20ssc%20indexes.xls&2033.0.55.001&Data%20Cubes&F40D0630B245D5DCCA257B43000EA0F1&0&2011&05.04.2013&Latest',
		seifa_suburb_2016 = 'https://www.abs.gov.au/ausstats/subscriber.nsf/log?openagent&2033055001%20-%20ssc%20indexes.xls&2033.0.55.001&Data%20Cubes&863031D939DE8105CA25825D000F91D2&0&2016&27.03.2018&Latest',
		victorian_suburb_list = Path(__file__).parent/'metadata'/'victorian_locations.csv',
		state_suburb_codes_2011 = 'https://www.abs.gov.au/AUSSTATS/subscriber.nsf/log?openagent&1270055003_ssc_2011_aust_csv.zip&1270.0.55.003&Data%20Cubes&414A81A24C3049A8CA2578D40012D50C&0&July%202011&22.07.2011&Previous',
		seifa_2006_cd = 'https://www.abs.gov.au/AUSSTATS/subscriber.nsf/log?openagent&2033055001_%20seifa,%20census%20collection%20districts,%20data%20cube%20only,%202006.xls&2033.0.55.001&Data%20Cubes&6EFDD4FA99C28C4ECA2574170011668A&0&2006&26.03.2008&Latest',
		seifa_2006_cd_shapefile = 'https://www.abs.gov.au/AUSSTATS/subscriber.nsf/log?openagent&1259030002_cd06avic_shape.zip&1259.0.30.002&Data%20Cubes&D62E845F621FE8ACCA25795D002439BB&0&2006&06.12.2011&Previous',
		seifa_2001_aurin = 'aurin:datasource-AU_Govt_ABS-UoM_AURIN_DB_3_seifa_cd_2001',
		seifa_1996_aurin = 'aurin:datasource-AU_Govt_ABS-UoM_AURIN_DB_3_seifa_cd_1996',
		seifa_1991_aurin = 'aurin:datasource-AU_Govt_ABS-UoM_AURIN_DB_3_seifa_cd_1991',
		seifa_1986_aurin = 'aurin:datasource-AU_Govt_ABS-UoM_AURIN_DB_3_seifa_cd_1986',
	
		
	)

	return out

def download_dataset(dataset, suffix, links, should_unzip=False):
	local_path = get_cached_path(f"{dataset}.{suffix}")
	if should_unzip == True:
		new_path_name = Path(user_cache_dir('aucpi'))/f"{dataset}_unzipped"
		if  new_path_name.exists() == True:
			return new_path_name

	cached_download(links[dataset], local_path)
	if should_unzip == True:
		
		with zipfile.ZipFile(local_path, 'r') as zip_ref:
   			zip_ref.extractall(new_path_name)
		os.remove(local_path)
		return new_path_name
	else:
		return local_path
			
def load_gis_data(dataset = ' victoria_suburbs', **kwargs):
	links = get_data_links()
	local_path = download_dataset(dataset, 'geojson', links)
	
	return gpd.read_file(local_path, **kwargs)

def load_xls_data(dataset='seifa_suburb_2016', **kwargs):
	links = get_data_links()
	local_path = download_dataset(dataset, 'xls', links)

	return pd.read_excel(links[dataset], **kwargs)

def load_csv_data(dataset='victorian_suburb_list', zipped=False, **kwargs):
	links = get_data_links()
	if zipped == True: suffix = '.csv.zip'
	else: suffix = '.csv'
	local_path = download_dataset(dataset, suffix, links)
	return pd.read_csv(local_path, **kwargs)

def load_shapefile_data(dataset='seifa_2006_cd_shapefile'):
	links = get_data_links()
	local_path = download_dataset(dataset, '', links, should_unzip=True)
	shpfile_path = [x for x in local_path.iterdir() if 'shp' in x.name]
	return gpd.read_file(shpfile_path[0])


def make_aurin_config():
	
	username = input('please enter your aurin username: ')
	password = getpass('please enter your aurin password: ')
	out = {'username':username, 'password':password}

	path = get_cached_path('aurin_creds.json')

	with open(path, 'w') as file:
		json.dump(out, file)

def download_aurin_dataset(wfs_aurin, dataset, links):
	local_path = get_cached_path(dataset + '.geojson')
	if local_path.exists() == True:
		print(f'{dataset} already downloaded')
		return local_path
	response = wfs_aurin.getfeature(typename=links[dataset], bbox=(96.81,-43.75,159.11,-9.14), 
									srsname='urn:x-ogc:def:crs:EPSG:4283', outputFormat='json')
	
	with open(local_path,'w') as file: file.write(response.read().decode('UTF-8'))

	return local_path

def load_aurin_config():
	
	config_path = Path(__file__).parent.parent.parent/'config.ini'
	if config_path.exists() == False:
		return False
	else:
		print('loading credentials from config.ini')
		import configparser
		parser = configparser.ConfigParser()
		
		parser.read(str(config_path))
		
		username = parser['aurin']['username']
		password = parser['aurin']['password']
		return dict(username=username, password=password)

def load_aurin_data(dataset: str or list):
	links = get_data_links()
	
	if type(dataset) == str:
		dataset = [dataset]
	local_paths = [get_cached_path(f'{ds}.geojson') for ds in dataset ]
	all_downloaded = all([lp.exists() for lp in local_paths])
	if all_downloaded ==True:
		return [gpd.read_file(lp) for lp in local_paths]
	else:
		creds = load_aurin_config()
		if creds == False:
			path = get_cached_path('aurin_creds.json') 
			if path.exists() == False:
				make_aurin_config()
			with open(path, 'r') as file:
				creds = json.load(file)

		wfs_aurin = WebFeatureService('http://openapi.aurin.org.au/wfs', version='1.1.0',
									username=creds['username'], password = creds['password'])
		outs = []
		for d in dataset:
			outs.append(gpd.read_file(download_aurin_dataset(wfs_aurin, d, links)))
		return outs

def load_victorian_suburbs_metadata():
	links = get_data_links()
	return pd.read_csv(links['victorian_suburb_list'])