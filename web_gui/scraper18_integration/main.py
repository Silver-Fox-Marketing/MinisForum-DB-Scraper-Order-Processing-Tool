from scrapers.joemachensnissan import *
from scrapers.joemachenscdjr import *
from scrapers.joemachenshyundai import *
from scrapers.kiaofcolumbia import *
from scrapers.porschestlouis import *
from scrapers.auffenberghyundai import *
from scrapers.hondafrontenac import *
from scrapers.bommaritocadillac import *
from scrapers.pappastoyota import *
from scrapers.twincitytoyota import *
from scrapers.serrahondaofallon import *
from scrapers.southcountyautos import *
from scrapers.glendalechryslerjeep import *
from scrapers.davesinclairlincolnsouth import *
from scrapers.suntrupkiasouth import *
from scrapers.columbiabmw import *
from scrapers.rustydrewingcadillac import *
from scrapers.rustydrewingchevroletbuickgmc import *
from scrapers.pundmannford import *
from scrapers.stehouwerauto import *
from scrapers.bmwofweststlouis import *
from scrapers.bommaritowestcounty import *
from scrapers.hwkia import *
from scrapers.wcvolvocars import *
from scrapers.joemachenstoyota import *
from scrapers.suntruphyundaisouth import *
from scrapers.landroverranchomirage import *
from scrapers.jaguarranchomirage import *
from scrapers.indigoautogroup import *
from scrapers.miniofstlouis import *
from scrapers.suntrupfordkirkwood import *
from scrapers.thoroughbredford import *
from scrapers.spiritlexus import *
from scrapers.frankletahonda import *
from scrapers.columbiahonda import *
from scrapers.davesinclairlincolnstpeters import *
from scrapers.weberchev import *
from scrapers.suntrupbuickgmc import *
from scrapers.suntrupfordwest import *

from scrapers.helper_class import *

helper = Helper()

sites_data = helper.reading_csv('./input_data/config.csv')
data_folder = helper.checking_folder_existence('./output_data/')
data_folder = helper.checking_folder_existence(data_folder + str(datetime.datetime.now()).split()[0] + '/')
log_folder = helper.checking_folder_existence(f'{data_folder}/log/')

output_file = f'{data_folder}complete_data.csv'

sites_processed_file = f'{log_folder}sites_processed.json'
sites_processed_data = helper.json_exist_data(sites_processed_file)

for index, site_data in enumerate(sites_data[1:]):

	site_name = site_data[0]
	to_scrap = site_data[1].lower()

	if to_scrap != 'yes':
		continue

	print(index, ' / ', len(sites_data), ' : ', site_name, ' : ', to_scrap)

	if site_name not in sites_processed_data:

		if site_name == 'joemachensnissan.com':
			JOEMACHENSNISSAN(data_folder, output_file).start_scraping_joemachensnissan()

		elif site_name == 'joemachenscdjr.com':
			JOEMACHENSCDJR(data_folder, output_file).start_scraping_joemachenscdjr()

		elif site_name == 'joemachenshyundai.com':
			JOEMACHENSHYUNDAI(data_folder, output_file).start_scraping_joemachenshyundai()

		elif site_name == 'kiaofcolumbia.com':
			KIAOFCOLUMBIA(data_folder, output_file).start_scraping_kiaofcolumbia()

		elif site_name == 'porschestlouis.com':
			PORSCHESTLOUIS(data_folder, output_file).start_scraping_porschestlouis()

		elif site_name == 'auffenberghyundai.com':
			AUFFENBERGHYUNDAI(data_folder, output_file).start_scraping_auffenberghyundai()

		elif site_name == 'hondafrontenac.com':
			HONDAFRONTENAC(data_folder, output_file).start_scraping_hondafrontenac()

		elif site_name == 'bommaritocadillac.com':
			BOMMARITOCADILLAC(data_folder, output_file).start_scraping_bommaritocadillac()

		elif site_name == 'pappastoyota.com':
			PAPPASTOYOTA(data_folder, output_file).start_scraping_pappastoyota()

		elif site_name == 'twincitytoyota.com':
			TWINCITYTOYOTA(data_folder, output_file).start_scraping_twincitytoyota()

		elif site_name == 'serrahondaofallon.com':
			SERRAHONDAOFALLON(data_folder, output_file).start_scraping_serrahondaofallon()

		elif site_name == 'southcountyautos.com':
			SOUTHCOUNTYAUTOS(data_folder, output_file).start_scraping_southcountyautos()

		elif site_name == 'glendalechryslerjeep.net':
			GLENDALECHRYSLERJEEP(data_folder, output_file).start_scraping_glendalechryslerjeep()

		elif site_name == 'davesinclairlincolnsouth.com':
			DAVESINCLAIRLINCOLNSOUTH(data_folder, output_file).start_scraping_davesinclairlincolnsouth()

		elif site_name == 'suntrupkiasouth.com':
			SUNTRUPKIASOUTH(data_folder, output_file).start_scraping_suntrupkiasouth()

		elif site_name == 'columbiabmw.com':
			COLUMBIABMW(data_folder, output_file).start_scraping_columbiabmw()

		elif site_name == 'rustydrewingcadillac.com':
			RUSTYDREWINGCADILLAC(data_folder, output_file).start_scraping_rustydrewingcadillac()

		elif site_name == 'rustydrewingchevroletbuickgmc.com':
			RUSTYDREWINGCHEVROLETBUICKGMC(data_folder, output_file).start_scraping_rustydrewingchevroletbuickgmc()

		elif site_name == 'pundmannford.com':
			PUNDMANNFORD(data_folder, output_file).start_scraping_pundmannford()

		elif site_name == 'stehouwerauto.com':
			STEHOUWERAUTO(data_folder, output_file).start_scraping_stehouwerauto()

		elif site_name == 'bmwofweststlouis.com':
			BMWOFWESTSTLOUIS(data_folder, output_file).start_scraping_bmwofweststlouis()

		elif site_name == 'bommaritowestcounty.com':
			BOMMARITOWESTCOUNTY(data_folder, output_file).start_scraping_bommaritowestcounty()

		elif site_name == 'hwkia.com':
			HWKIA(data_folder, output_file).start_scraping_hwkia()

		elif site_name == 'wcvolvocars.com':
			WCVOLVOCARS(data_folder, output_file).start_scraping_wcvolvocars()

		elif site_name == 'joemachenstoyota.com':
			JOEMACHENSTOYOTA(data_folder, output_file).start_scraping_joemachenstoyota()

		elif site_name == 'suntruphyundaisouth.com':
			SUNTRUPHYUNDAISOUTH(data_folder, output_file).start_scraping_suntruphyundaisouth()

		elif site_name == 'landroverranchomirage.com':
			LANDROVERRANCHOMIRAGE(data_folder, output_file).start_scraping_landroverranchomirage()

		elif site_name == 'jaguarranchomirage.com':
			JAGUARRANCHOMIRAGE(data_folder, output_file).start_scraping_jaguarranchomirage()

		elif site_name == 'indigoautogroup.com':
			INDIGOAUTOGROUP(data_folder, output_file).start_scraping_indigoautogroup()

		elif site_name == 'miniofstlouis.com':
			MINIOFSTLOUIS(data_folder, output_file).start_scraping_miniofstlouis()

		elif site_name == 'suntrupfordkirkwood.com':
			SUNTRUPFORDKIRKWOOD(data_folder, output_file).start_scraping_suntrupfordkirkwood()

		elif site_name == 'thoroughbredford.com':
			THOROUGHBREDFORD(data_folder, output_file).start_scraping_thoroughbredford()

		elif site_name == 'spiritlexus.com':
			SPIRITLEXUS(data_folder, output_file).start_scraping_spiritlexus()

		elif site_name == 'frankletahonda.com':
			FRANKLETAHONDA(data_folder, output_file).start_scraping_frankletahonda()

		elif site_name == 'columbiahonda.com':
			COLUMBIAHONDA(data_folder, output_file).start_scraping_columbiahonda()

		elif site_name == 'davesinclairlincolnstpeters.com':
			DAVESINCLAIRLINCOLNSTPETERS(data_folder, output_file).start_scraping_davesinclairlincolnstpeters()

		elif site_name == 'weberchev.com':
			WEBERCHEV(data_folder, output_file).start_scraping_weberchev()

		elif site_name == 'suntrupbuickgmc.com':
			SUNTRUPBUICKGMC(data_folder, output_file).start_scraping_suntrupbuickgmc()

		elif site_name == 'suntrupfordwest.com':
			SUNTRUPFORDWEST(data_folder, output_file).start_scraping_suntrupfordwest()

				
		sites_processed_data.append(site_name)
		helper.write_json_file(sites_processed_data, sites_processed_file)

	else:
		print('Site Already processed...')

	print('-'*50)
	print()