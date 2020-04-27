from bs4 import BeautifulSoup
from openpyxl import load_workbook
import plotly.graph_objs as go
# from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import requests
import json
import webbrowser
import csv
import sqlite3
import time

CACHE_FILENAME = "covid_cache.json"
CACHE_DICT = {}
DB_NAME = "covid_usdaers.sqlite"

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

def npr_covid_data_dict():
    '''
    '''
    npr_url = "https://apps.npr.org/dailygraphics/graphics/coronavirus-d3-us-map-20200312/table.html?initialWidth=1238&childId=responsive-embed-coronavirus-d3-us-map-20200312-table&parentTitle=Coronavirus%20Map%20And%20Graphics%3A%20Track%20The%20Spread%20In%20The%20U.S.%20%3A%20Shots%20-%20Health%20News%20%3A%20NPR&parentUrl=https%3A%2F%2Fwww.npr.org%2Fsections%2Fhealth-shots%2F2020%2F03%2F16%2F816707182%2Fmap-tracking-the-spread-of-the-coronavirus-in-the-u-s"
    npr_response = requests.get(npr_url)
    npr_soup = BeautifulSoup(npr_response.text, 'html.parser')

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
                    'Cases': cases_list[i],
                    'Deaths': deaths_list[i]
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
    drop_states_usda_sql = "DROP TABLE IF EXISTS 'SocioeconomicStates'"
    drop_mi_usda_sql = "DROP TABLE IF EXISTS 'SocioecnomicMichigan'"

    create_county_covid_sql = '''
        CREATE TABLE IF NOT EXISTS "CovidCounty" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Date" TEXT NOT NULL,
            "County" TEXT NOT NULL,
            "StateName" TEXT NOT NULL,
            "Fips" INTEGER NOT NULL,
            "CountyCases" INTEGER,
            "CountyDeaths" INTEGER
        )
    '''

    create_state_covid_sql = '''
        CREATE TABLE IF NOT EXISTS "CovidState" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Name" TEXT NOT NULL,
            "StateCases" INTEGER NOT NULL,
            "StateDeaths" INTEGER NOT NULL
        )
    '''

    create_states_usda_sql = '''
        CREATE TABLE IF NOT EXISTS "SocioeconomicStates" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "StateName" TEXT NOT NULL,
            "StatePopulation" INTEGER NOT NULL,
            "StateMedianIncome" INTEGER NOT NULL,
            "StatePovertyRate" DECIMAL NOT NULL,
            "StateUnemploymentRate" DECIMAL NOT NULL,
            "StateCompHSOnlyRate" DECIMAL NOT NULL,
            "StateCompCollRate" DECIMAL NOT NULL
        )
    '''

    create_mi_usda_sql = '''
    CREATE TABLE IF NOT EXISTS "SocioeconomicMichigan" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "County" TEXT NOT NULL,
            "CountyPopulation" INTEGER NOT NULL,
            "CountyMedianIncome" INTEGER NOT NULL,
            "CountyPovertyRate" DECIMAL NOT NULL,
            "CountyUnemploymentRate" DECIMAL NOT NULL,
            "CountyCompHSOnlyRate" DECIMAL NOT NULL,
            "CountyCompCollRate" DECIMAL NOT NULL
        )
    '''

    cur.execute(drop_county_covid_sql)
    cur.execute(drop_state_covid_sql)
    cur.execute(drop_states_usda_sql)
    cur.execute(drop_mi_usda_sql)
    cur.execute(create_county_covid_sql)
    cur.execute(create_state_covid_sql)
    cur.execute(create_states_usda_sql)
    cur.execute(create_mi_usda_sql)

    conn.commit()
    conn.close()

def populate_database():
    data_header = []
    data_rows = []

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

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
        VALUES (NULL, ?, ?, ?)
    '''

    for k,v in npr_covid_data_dict().items():
        cur.execute(insert_state_covid_sql, [
            k,
            v['Cases'],
            v['Deaths']
        ])
    
    insert_state_ers_sql = '''
        INSERT INTO SocioeconomicStates
        VALUES (Null, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    with open("USDA_ERS_Data.json") as file_obj:
        for k, v in json.load(file_obj).items():
            cur.execute(insert_state_ers_sql, [
                k,
                v['Population'],
                v['Median Household Income'],
                v['Poverty Rate'],
                v['Unemployment Rate'],
                v['Completed HS Only Rate'],
                v['College Completion Rate']
            ])

    insert_mi_ers_sql = '''
        INSERT INTO SocioeconomicMichigan
        VALUES (Null, ?, ?, ?, ?, ?, ?, ?)
    '''
    with open("MI_USDA_ERS_Data.json") as file_obj:
        for k, v in json.load(file_obj).items():
            cur.execute(insert_mi_ers_sql, [
                k,
                v['Population'],
                v['Median Household Income'],
                v['Poverty Rate'],
                v['Unemployment Rate'],
                v['Completed HS Only Rate'],
                v['College Completion Rate']
            ])

    conn.commit()
    conn.close()

def clean_county_covid_data():
    data_header = []
    data_rows = []
    county_dict = {}

    with open("covid_data/us-counties.csv", 'r') as csvfile:
        data = []
        csv_header = csv.reader(csvfile)
        for h in csv_header:
            data.append(h)
        data_header.extend(data[0])
        data_rows.extend(data[1:])

    for dr in data_rows:
        if dr[2] not in county_dict:
            county_dict[dr[2]] = {
                dr[1]: {
                    "Cases": int(dr[4]),
                    "Deaths": int(dr[5])
                }
            }
        elif dr[2] in county_dict:
            county_dict[dr[2]].update(
            {
                dr[1]: {
                    "Cases": int(dr[4]),
                    "Deaths": int(dr[5])
                }
            }
            )

    return county_dict

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

def clean_excel_data():
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
    
    usda_ers_data = build_usda_ers_dict(pop_dict, poverty_dict, comp_hs_only_dict, comp_coll_dict, unemp_dict, med_income_dict)

    # getting michigan socioeconomic data
    mi_comp_coll_names = get_excel_data("socioeconomic_data/MIEducationReportCompColl.xlsx", "EducationReport", 'B5:B87')
    mi_comp_coll_perc = get_excel_data("socioeconomic_data/MIEducationReportCompColl.xlsx", "EducationReport", 'I5:I87')

    mi_comp_hs_only_names = get_excel_data("socioeconomic_data/MIEducationReportHSOnly.xlsx", "EducationReport", 'B5:B87')
    mi_comp_hs_only = get_excel_data("socioeconomic_data/MIEducationReportHSOnly.xlsx", "EducationReport", 'I5:I87')

    mi_pop_names = get_excel_data("socioeconomic_data/MIPopulationReport.xlsx", "PopulationReport", 'B5:B87')
    mi_pop_num = get_excel_data("socioeconomic_data/MIPopulationReport.xlsx", "PopulationReport", 'G5:G87')

    mi_poverty_names = get_excel_data("socioeconomic_data/MIPovertyReport.xlsx", "PovertyReport", 'D7:D89')
    mi_poverty_perc = get_excel_data("socioeconomic_data/MIPovertyReport.xlsx", "PovertyReport", 'G7:G89')

    mi_unemp_names = get_excel_data("socioeconomic_data/MIUnemploymentReport.xlsx", "UnemploymentReport", 'B4:B86')
    mi_unemp_perc = get_excel_data("socioeconomic_data/MIUnemploymentReport.xlsx", "UnemploymentReport", 'K4:K86')

    mi_med_income_names = get_excel_data("socioeconomic_data/MIUnemploymentReport.xlsx", "UnemploymentReport", 'B4:B86')
    mi_med_income = get_excel_data("socioeconomic_data/MIUnemploymentReport.xlsx", "UnemploymentReport", 'L4:L86')

    # cleaning michigan names
    mi_comp_coll_names_cleaned = []
    for counties in mi_comp_coll_names:
        split_counties = counties.split(',')
        mi_comp_coll_names_cleaned.append(split_counties[0])
    
    mi_comp_hs_only_names_cleaned = []
    for counties in mi_comp_hs_only_names:
        split_counties = counties.split(',')
        mi_comp_hs_only_names_cleaned.append(split_counties[0])

    mi_pop_names_cleaned = []
    for counties in mi_pop_names:
        split_counties = counties.replace('County','')
        mi_pop_names_cleaned.append(split_counties.strip())

    mi_unemp_names_cleaned = []
    for counties in mi_unemp_names:
        split_counties = counties.replace("County, MI", '')
        mi_unemp_names_cleaned.append(split_counties.strip())

    mi_med_income_names_cleaned = []
    for counties in mi_med_income_names:
        split_counties = counties.replace("County, MI", '')
        mi_med_income_names_cleaned.append(split_counties.strip())

    # building michigan socioeconomic dictionaries
    mi_comp_coll_dict = build_socioecon_dict(mi_comp_coll_names_cleaned, convert_to_percent(mi_comp_coll_perc), "College Completion Rate")
    mi_comp_hs_only_dict = build_socioecon_dict(mi_comp_hs_only_names_cleaned, convert_to_percent(mi_comp_hs_only), "Completed HS Only Rate")
    mi_poverty_dict = build_socioecon_dict(mi_poverty_names, mi_poverty_perc, "Poverty Rate")
    mi_pop_dict = build_socioecon_dict(mi_pop_names_cleaned, mi_pop_num, "Population")
    mi_unemp_dict = build_socioecon_dict(mi_unemp_names_cleaned, mi_unemp_perc, "Unemployment Rate")
    mi_med_income_dict = build_socioecon_dict(mi_med_income_names_cleaned, mi_med_income, "Median Household Income")

    mi_usda_ers_data = build_usda_ers_dict(mi_pop_dict, mi_poverty_dict, mi_comp_hs_only_dict, mi_comp_coll_dict, mi_unemp_dict, mi_med_income_dict)

    # writing data to json
    write_to_json("USDA_ERS_Data.json", usda_ers_data)
    write_to_json("MI_USDA_ERS_Data.json", mi_usda_ers_data)

def access_state_sql_database(state):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    query = f'''
        SELECT StateName, County, MAX(CountyCases), MAX(CountyDeaths)
        FROM CovidCounty
        WHERE StateName = "{state}"
        GROUP BY County
        ORDER BY MAX(CountyCases) DESC
    '''
    result = cur.execute(query).fetchall()
    conn.close()
    return result

def access_national_sql_database():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    query = '''
        SELECT Name, MAX(StateCases), MAX(StateDeaths), ss.StatePopulation, ss.StateMedianIncome, ss.StateUnemploymentRate, ss.StatePovertyRate, ss.StateCompCollRate, ss.StateCompHSOnlyRate
        FROM CovidState
            JOIN SocioeconomicStates as ss
            ON CovidState.Name = ss.StateName
        GROUP BY Name
        ORDER BY MAX(StateCases) DESC
    '''
    result = cur.execute(query).fetchall()
    conn.close()
    return result

def create_and_show_figures(user_input):
    if user_input == "nation":
        state_names = []
        state_cases = []
        state_deaths = []
        # state_pop = []
        # state_med_income = []
        # state_unemp = []
        # state_pov = []
        # state_coll_comp = []
        # state_comp_hs = []
        # table_data = []
        table_data = [["State", "Cases", "Deaths", "Population", "Median Income", "Unemployment Rate", "Poverty Rate", "College Completion Rate", "Completed High School Only Rate"]]
        for data in access_national_sql_database():
            table_data.append([data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]])
            state_names.append(data[0])
            state_cases.append(data[1])
            state_deaths.append(data[2])
            # state_pop.append(data[3])
            # state_med_income.append(data[4])
            # state_unemp.append(data[5])
            # state_pov.append(data[6])
            # state_coll_comp.append(data[7])
            # state_comp_hs.append(data[8])
        
        trace1 = go.Bar(name="Cases", x=state_names, y=state_cases, xaxis="x2", yaxis="y2")
        trace2 = go.Bar(name="Deaths", x=state_names, y=state_deaths, xaxis="x2", yaxis="y2")
    else:
        county_names = []
        county_cases = []
        county_deaths = []
        state_socio = []
        table_data = [['County', 'Cases', 'Deaths']]
        for data in access_state_sql_database(user_input.title()):
            table_data.append([data[1], data[2], data[3]])
            county_names.append(data[1])
            county_cases.append(data[2])
            county_deaths.append(data[3])

        for national_data in access_national_sql_database():
            if national_data[0] == user_input.title():
                state_socio.extend([national_data[0], national_data[3], national_data[4], national_data[5], national_data[6], national_data[7], national_data[8]])

        print(f"Here is socioeconomic data for {user_input.title()}:")
        time.sleep(1)
        print(f"Population: {state_socio[1]}")
        time.sleep(1)
        print(f"Median Household Income: {state_socio[2]}")
        time.sleep(1)
        print(f"Unemployment Rate: {state_socio[3]}")
        time.sleep(1)
        print(f"Poverty Rate: {state_socio[4]}")
        time.sleep(1)
        print(f"College Completion Rate: {state_socio[5]}")
        time.sleep(1)
        print(f"Completed High School Only Rate: {state_socio[6]}")

        trace1 = go.Bar(name="Cases", x=county_names, y=county_cases, xaxis="x2", yaxis="y2")
        trace2 = go.Bar(name="Deaths", x=county_names, y=county_deaths, xaxis="x2", yaxis="y2")
    
    table = ff.create_table(table_data)

    table.add_traces([trace1, trace2])

    table["layout"]["xaxis2"] = {}
    table["layout"]["yaxis2"] = {}

    table.layout.yaxis.update({"domain":[0, .45]})
    table.layout.yaxis2.update({"domain":[.6, 1]})

    table.layout.yaxis2.update({"anchor":"x2"})
    table.layout.xaxis2.update({"anchor":"y2"})
    table.layout.yaxis2.update({"title":"COVID-19"})

    table.layout.margin.update({"t":75, "l":50})

    if user_input == "nation":
        table.layout.update({"title":"National 2020 COVID-19 Numbers"})
    else:
        table.layout.update({"title":f"{user_input.title()} 2020 COVID-19 Numbers"})

    time.sleep(3)
    table.show()

if __name__ == "__main__":
    CACHE_DICT = open_cache()
    TEMP_LIST = []

    while True:
        data_to_view = input(f"\nYou can see COVID-19 data for the entire nation or a specific state. Enter 'nation', a state (including 'District of Columbia'), or 'exit':\n")
        if data_to_view == "exit":
            exit()
        else:
            create_and_show_figures(data_to_view)

    # clean_excel_data
    # create_database()
    # populate_database()
    # write_to_json("US_Covid.json", npr_covid_data_dict())
    # write_to_json("County_Covid.json", clean_county_covid_data())

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