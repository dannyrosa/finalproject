# UMich SI 507 Final Project
This project was created as a final project for SI 507 at the University of Michigan's School of Information.

## Program Description
A 6-minute video of how the program runs can be found [here](https://www.loom.com/share/51bdd2026f304349955d5a374eef029c).

This interactive program combines USDA Economic Research Service (USDA ERS) and COVID-19 data. You will be able to see both state- and county-level COVID-19 data.

State-level COVID-19 data comes from scraping NPR's COVID-19 tracking webpage. The webpage is updated periodically and a timestamp is provided.

County-level COVID-19 data comes from the New York Times' GitHub repository. This data was downloaded as a CSV file on April 27th, with numbers current as of April 26th.
 
If you choose to see COVID-19 data for a specific state, then you will also be able to see a number of socioeconomic data harvested from USDA ERS data about that specific state.

The socioeconomic data are:
  - Population
  - Median Household Income
  - Unemployment Rate
  - Poverty Rate
  - College Completion Rate
  - High School Only Completion Rate

Both national and state COVID-19 data will be presented in bar and table form if you like. If you select a state, the socioeconomic data will print to your terminal and the COVID-19 data will launch in your browser.

## Instructions
To run this program, download the Python file "finalproj.py" and the folders "covid_data" and "socioeconomic_data". These should be placed within the same directory for the program to run properly. The program creates several JSON files and a SQL database, which have been provided for reference and you are able to download these as your wish.

To have the most updated COVID-19 data available, download  the "us-counties.csv" file from the [New York Time's GitHub Repository](https://github.com/nytimes/covid-19-data.git).

## Interactions
This program has a variety of command line prompts. Here is a breakdown of the interactive components:

INTERACTION 1
  - View webpage for specific socioeconomic data
  - “Next” proceeds to Interaction 2
  - Exit

INTERACTION 2
  - “Nation” to see state-level COVID-19 data
    - INTERACTION 2.5
      - If “nation”
        - View state-level COVID-19 data in visual form using Plotly bar graph and table
        - “Back” to begin Interaction 2 again
        - Exit
  - “State” proceeds to Interaction 3
  - “Back” to go to Interaction 1
  - Exit

INTERACTION 3
 - Select a state’s corresponding number for state-specific COVID-19 data
   - INTERACTION 3.5
     - If a state is select,
       - View socioeconomic data for a state and state-level COVID-19 data in visual form using Plotly bar graph and table
       - “Back” to begin Interaction 3 again
       - Exit
  - “Back” to go to Interaction 2
  - Exit

