from bs4 import BeautifulSoup
import requests
import json
import secrets
import webbrowser

CACHE_FILENAME = "covid_cache.json"
CACHE_DICT = {}

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

#########################################################
###                                                   ###
### CREATING DICTIONARY W/ 4 KEY:VALUE PAIRS FOR DATA ###
###                                                   ###
#########################################################
def launch_dataset_webpage(dataset):
    return webbrowser.open(dataset)

###########################################################
###                                                     ###
### COLLECTING DATA FROM ONE SPECIFIC PAGE (POPULATION) ###
### *** having trouble here                             ###
###########################################################
pop_url = "https://data.ers.usda.gov/reports.aspx?ID=17829"
pop_response = requests.get(pop_url)
pop_soup = BeautifulSoup(pop_response.text, "html.parser")
# print(pop_soup.prettify())



pop_data_table = pop_soup.find("a", title="Excel")
pop_data_table = pop_soup.find("table", class_="P89563b08bc53465683c0bb7d1b5395f0_1_r10")
# print(f"\n\n\n\n")
# print(pop_data_table)

# for items in pop_data_table:
#     print(f"\n\n\n\n\n{items}")

#########################################################
###                                                   ###
### SCRAPING NPR CORONAVIRUS WEBPAGE                  ###
###                                                   ###
#########################################################
def npr_covid():
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

def write_to_json(filename, data):
    with open(filename, "w") as file_obj:
        json.dump(data, file_obj, indent=4)

def clean_data(data):
    try:
        return int(data)
    except:
        data = data.replace(',','')
        return int(data)

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

    print(f"\nHere are the datasets available for analysis.\n")

    counter = 1
    for k,v in build_county_url_dict().items():
        print(f"[{counter}] {k}")
        TEMP_LIST.append(v)
        counter += 1
    
    write_to_json("US_Covid.json", npr_covid())

    # while True:
        # webpage = input(f"\nChoose a number to launch the webpage for the respective dataset or 'exit':\n")
        # if webpage == "exit":
        #     exit()
        # else:
        #     webpage_num = int(webpage)
        #     if 0 < webpage_num <= 4:
        #         for i in range(len(TEMP_LIST)):
        #             launch_dataset_webpage(TEMP_LIST[webpage_num - 1])

    while True:
        covid_data = input(f"\nWould you like to see COVID-19 data for the United States? Enter 'yes' or 'exit'.\n")
        if covid_data.lower() == "exit":
            exit()
        elif covid_data.lower() == "yes":
            for k,v in npr_covid().items():
                print(f"{k}: cases - {v['cases']} | deaths - {v['deaths']}")