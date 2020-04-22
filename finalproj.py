from bs4 import BeautifulSoup
from openpyxl import load_workbook
import requests
import json
import webbrowser
import csv
import sqlite3

CACHE_FILENAME = "covid_cache.json"
CACHE_DICT = {}
DB_NAME = "covid_usdaers.sqlite"

#########################################################
###                                                   ###
### CREATING DICTIONARY W/ 4 KEY:VALUE PAIRS FOR DATA ###
###                                                   ###
#########################################################
def build_county_url_dict():
    url = "https://www.ers.usda.gov/data-products/county-level-data-sets/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    make_request_with_cache(url, soup.prettify())

    section = soup.find("div", style="margin-left: 4em;")
    indiv = section.find("ul")

    link_texts = []
    for words in indiv.find_all("li"):
        link_texts.append(words.text.strip())
    link_urls = []
    for items in indiv.find_all("a"):
        link_urls.append(items['data-id'])
    
    data_dict = {}
    for i in range(len(link_texts)):
        data_dict[link_texts[i]] = f"https://data.ers.usda.gov/reports.aspx?ID={link_urls[i]}"

    return data_dict

def launch_dataset_webpage(dataset):
    return webbrowser.open(dataset)

#########################################################
###                                                   ###
### SCRAPING NPR CORONAVIRUS WEBPAGE                  ###
###                                                   ###
#########################################################
def npr_covid_data_dict():
    '''
    '''
    npr_url = "https://apps.npr.org/dailygraphics/graphics/coronavirus-d3-us-map-20200312/table.html?initialWidth=1238&childId=responsive-embed-coronavirus-d3-us-map-20200312-table&parentTitle=Coronavirus%20Map%20And%20Graphics%3A%20Track%20The%20Spread%20In%20The%20U.S.%20%3A%20Shots%20-%20Health%20News%20%3A%20NPR&parentUrl=https%3A%2F%2Fwww.npr.org%2Fsections%2Fhealth-shots%2F2020%2F03%2F16%2F816707182%2Fmap-tracking-the-spread-of-the-coronavirus-in-the-u-s"
    npr_response = requests.get(npr_url)
    npr_soup = BeautifulSoup(npr_response.text, 'html.parser')

    # make_request_with_cache(npr_url, npr_soup.prettify())

    covid_nums = {}

    names_list = []
    names = npr_soup.find_all("div", class_="cell cell-inner stateName")
    for n in names:
        names_list.append(n.text.strip())

    cases_list = []
    cases = npr_soup.find_all("div", class_="cell amt confirmed cell-inner")
    for c in cases:
        cases_list.append(clean_data(c.text.strip()))

    deaths_list = []
    deaths = npr_soup.find_all("div", class_="cell amt deaths cell-inner")
    for d in deaths:
        deaths_list.append(clean_data(d.text.strip()))

    for i in range(len(names_list)):
            covid_nums[names_list[i]] = {
                    'cases': cases_list[i],
                    'deaths': deaths_list[i]
                }
    
    return covid_nums

def build_usda_ers_dict(dict1, dict2, dict3, dict4, dict5, dict6):

    socioecon = {**dict1, **dict2, **dict3, **dict4, **dict5, **dict6}

    for key, value in socioecon.items():
        if key in dict1 and key in dict2 and key in dict3 and key in dict4 and key in dict5 and key in dict6:
            socioecon[key] = [
                value,
                dict1[key],
                dict2[key],
                dict3[key],
                dict4[key],
                dict5[key]
            ]
    
    socioecon2 = {}

    for k, items in socioecon.items():
        socioecon2[k] = {
            'Population': items[1]['Population'],
            'Median Household Income': items[0]['Median Household Income'],
            'Poverty Rate': items[2]['Poverty Rate'],
            'Unemployment Rate': items[5]['Unemployment Rate'],
            "Completed HS Only Rate": items[3]["Completed HS Only Rate"],
            "College Completion Rate": items[4]["College Completion Rate"],

        }

    return socioecon2

def build_socioecon_dict(names, data, key):
    socioecon = {}
    for i in range(len(names)):
        socioecon[names[i]] = {
            key: data[i]
        }
    
    return socioecon

def get_excel_data(workbook, sheet, cellrange):
    data = []

    wb = load_workbook(workbook)
    ws = wb[sheet]
    rows = ws[cellrange]

    for r in rows:
        for cells in r:
            data.append(cells.value)

    return data

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_county_covid_sql = "DROP TABLE IF EXISTS 'CovidCounty'"
    drop_state_covid_sql = "DROP TABLE IF EXISTS 'CovidState'"

    create_county_covid_sql = '''
        CREATE TABLE IF NOT EXISTS "CovidCounty" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Date" TEXT NOT NULL,
            "County" TEXT NOT NULL,
            "State" TEXT NOT NULL,
            "Fips" INTEGER NOT NULL,
            "Cases" INTEGER,
            "Deaths" INTEGER
        )
    '''

    create_state_covid_sql = '''
        CREATE TABLE IF NOT EXISTS "CovidState" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "State" TEXT NOT NULL,
            "Cases" INTEGER NOT NULL,
            "Deaths" INTEGER NOT NULL
        )
    '''

    cur.execute(drop_county_covid_sql)
    cur.execute(drop_state_covid_sql)
    cur.execute(create_county_covid_sql)
    cur.execute(create_state_covid_sql)

    conn.commit()
    conn.close()

def load_covid_data():
    data_header = []
    data_rows = []

    with open("covid_data/us-counties.csv", 'r') as csvfile:
        data = []
        csv_header = csv.reader(csvfile)
        for h in csv_header:
            data.append(h)
        data_header.extend(data[0])
        data_rows.extend(data[1:])

    insert_county_covid_sql = '''
        INSERT INTO CovidCounty
        VALUES (NULL, ?, ? , ?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for dr in data_rows:
        cur.execute(insert_county_covid_sql, [
            dr[0],
            dr[1],
            dr[2],
            dr[3],
            dr[4],
            dr[5]
        ])

    insert_state_covid_sql = '''
        INSERT INTO CovidState
        Values (NULL, ?, ?, ?)
    '''

    for k,v in npr_covid().items():
        cur.execute(insert_state_covid_sql, [
            k,
            v['cases'],
            v['deaths']
        ])

    conn.commit()
    conn.close()

def clean_data(data):
    data = data.replace(',','')
    return int(data)

def income_to_int(values):
    list_of_values = []

    for v in values: 
        v = v.replace("$",'')
        v = v.replace(',','')
        list_of_values.append(int(v))

    return list_of_values

def convert_to_percent(values):
    list_of_values = []
    
    for v in values:
        try:
            percent = float('{0:.2f}'.format((v * 100)))
            list_of_values.append(percent)
        except:
            list_of_values.append(v)
    
    return list_of_values

def write_to_json(filename, data):
    with open(filename, "w") as file_obj:
        json.dump(data, file_obj, indent=4)

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def make_request_with_cache(cache_key, cache_value):
    '''Check the cache for a saved result for this cache_key:cache_value
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    cache_key: string
        Various strings to be used as keys in CACHE_DICT
    cache_value: string
        Information to be saved as the value in CACHE_DICT
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if cache_key in CACHE_DICT.keys():
        print("Using cache")
        return CACHE_DICT[cache_key]
    else:
        print("Fetching")
        CACHE_DICT[cache_key] = cache_value
        save_cache(CACHE_DICT)
        return CACHE_DICT[cache_key]

if __name__ == "__main__":
    CACHE_DICT = open_cache()
    TEMP_LIST = []

    # create_database()
    # load_covid_data()

    # getting state socioeconomic data
    comp_coll_names = get_excel_data("socioeconomic_data/EducationReportCompColl.xlsx", "EducationReport", 'A6:A56')
    comp_coll_perc = get_excel_data("socioeconomic_data/EducationReportCompColl.xlsx", "EducationReport", 'F6:F56')

    comp_hs_only_names = get_excel_data("socioeconomic_data/EducationReportHSOnly.xlsx", "EducationReport", 'A6:A56')
    comp_hs_only = get_excel_data("socioeconomic_data/EducationReportHSOnly.xlsx", "EducationReport", 'F6:F56')

    pop_names = get_excel_data("socioeconomic_data/PopulationReport.xlsx", "PopulationReport", 'A6:A56')
    pop_num = get_excel_data("socioeconomic_data/PopulationReport.xlsx", "PopulationReport", 'E6:E56')

    poverty_names = get_excel_data("socioeconomic_data/PovertyReportPercent.xlsx", "PovertyReport", 'A7:A57')
    poverty_perc = get_excel_data("socioeconomic_data/PovertyReportPercent.xlsx", "PovertyReport", 'E7:E57')

    unemp_names = get_excel_data("socioeconomic_data/UnemploymentReportPercent.xlsx", "UnemploymentReport", 'B4:B54')
    unemp_perc = get_excel_data("socioeconomic_data/UnemploymentReportPercent.xlsx", "UnemploymentReport", 'K4:K54')

    med_income_names = get_excel_data("socioeconomic_data/UnemploymentReportPercent.xlsx", "UnemploymentReport", 'B4:B54')
    med_income = get_excel_data("socioeconomic_data/UnemploymentReportPercent.xlsx", "UnemploymentReport", 'L4:L54')

    # building state socioeconomic dictionaries
    comp_coll_dict = build_socioecon_dict(comp_coll_names, convert_to_percent(comp_coll_perc), "College Completion Rate")
    comp_hs_only_dict = build_socioecon_dict(comp_hs_only_names, convert_to_percent(comp_hs_only), "Completed HS Only Rate")
    poverty_dict = build_socioecon_dict(poverty_names, poverty_perc, "Poverty Rate")
    pop_dict = build_socioecon_dict(pop_names, pop_num, "Population")
    unemp_dict = build_socioecon_dict(unemp_names, unemp_perc, "Unemployment Rate")
    med_income_dict = build_socioecon_dict(med_income_names, income_to_int(med_income), "Median Household Income")
    
    usda_ers_data = build_usda_ers_dict(pop_dict, poverty_dict, comp_hs_only_dict, comp_coll_dict,unemp_dict, med_income_dict)

    write_to_json("USDA_ERS_Data.json", usda_ers_data)

    # write_to_json("US_Covid.json", npr_covid_data_dict())

    # print(f"\nHere are the datasets available for analysis.\n")

    # counter = 1
    # for k,v in build_county_url_dict().items():
    #     print(f"[{counter}] {k}")
    #     TEMP_LIST.append(v)
    #     counter += 1

    # while True:
        # webpage = input(f"\nChoose a number to launch the webpage for the respective dataset or 'exit':\n")
        # if webpage == "exit":
        #     exit()
        # else:
        #     webpage_num = int(webpage)
        #     if 0 < webpage_num <= 4:
        #         for i in range(len(TEMP_LIST)):
        #             launch_dataset_webpage(TEMP_LIST[webpage_num - 1])

    # while True:
        # covid_data = input(f"\nWould you like to see COVID-19 data for the United States? Enter 'yes' or 'exit'.\n")
        # if covid_data.lower() == "exit":
        #     exit()
        # elif covid_data.lower() == "yes":
        #     for k,v in npr_covid().items():
        #         print(f"{k}: cases - {v['cases']} | deaths - {v['deaths']}")