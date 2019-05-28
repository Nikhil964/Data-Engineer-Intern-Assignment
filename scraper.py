#Importing relevant libraries to access website's HTML and extract information
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import re


#Function that accepts a url and uses BeautifulSoup library to get the HTML for a webpage.
def getHTMLContent(link):
    html = urlopen(link)
    soup = BeautifulSoup(html, 'html.parser')
    return soup

cities_html = getHTMLContent('https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population')
cities_table = [cities_html.find_all(name='table',class_='wikitable sortable')[0]][0]

#Function to get additional data of each city (Land Area, Water Area, Elevation, City Website)
def getAdditionalDetails(url):
    city_page = getHTMLContent('https://en.wikipedia.org' + url)  # Appending initial weblink
    table = city_page.find('table', {'class': 'infobox geography vcard'})
    additional_details = []
    read_content = False
    for tr in table.find_all('tr'):
        # Iterating through all the rows of the table and getting useful info such as "Land Area", "Water Area", "Elevation", "City Website"
        if tr.get('class')==['mergedtoprow']:
            try:
                heading = tr.find('th').get_text().strip('\n')
                if heading[0:4]=='Area':
                    read_content=True
                elif heading[0:9]=='Elevation':
                    additional_details.append(tr.find('td').get_text())
                elif heading[0:7]=='Website':
                    additional_details.append(tr.find('a').get('href'))
        
            except Exception as error:
                pass

        elif tr.get('class')==['mergedrow'] and read_content:
            
            if tr.find('th').get_text()=='\xa0•\xa0Land':
                additional_details.append(tr.find('td').get_text())
            
            elif tr.find('th').get_text()=='\xa0•\xa0Water':
                additional_details.append(tr.find('td').get_text())
                read_content=False

    return additional_details


#Creating the dataset
data_content = []
rows = cities_table.find_all('tr')
# Moving through each row of cities list and compiling data.
for row in rows:
    cells = row.find_all('td')
    if len(cells) > 1:
        print("Getting information of the city:",cells[1].get_text())
        city_link = cells[1].find('a')
        city_info = [cell.text.strip('\n') for cell in cells]
        additional_details = getAdditionalDetails(city_link.get('href'))
        if (len(additional_details) == 4):
            city_info += additional_details
            data_content.append(city_info)


#Converting Dataset to pandas dataframe
dataset = pd.DataFrame(data_content)

# Defining column headings and removing unnecessary columns
headers = rows[0].find_all('th')
headers = [header.get_text().strip('\n') for header in headers]
headers += ['Area_Land','Area_Water','Elevation', 'City_Official_Site']

drop_columns = [6,8]
dataset.drop(drop_columns,axis=1,inplace=True)

dataset.columns = headers

drop_columns1=['2018rank','2016 land area','2016 population density','Location']
dataset.drop(drop_columns1,axis=1,inplace=True)

# Removing unnecessary characters and unifying data into common formatt (cleaning data)

# Replacing the headings with useful names
dataset.rename(columns={'State[c]': 'State'}, inplace = True)
dataset.rename(columns={'2018estimate': "2018_Population_Estimate"},inplace = True)
dataset.rename(columns={'2010Census': "2010_Population_Census"},inplace = True)
dataset.rename(columns={'Change': "Percentage_of_Population_Change"},inplace = True)
dataset.rename(columns={'Area_Land': "Land_Area(sq mi)"},inplace = True)
dataset.rename(columns={'Area_Water': "Water_Area(sq mi)"},inplace = True)
dataset.rename(columns={'City_Official_Site': "City_WebSite"},inplace = True)
dataset.rename(columns={'Elevation': "Elevation(ft)"},inplace = True)


#Removing paranthesis, square brackets and content inside them
for column in dataset.columns:
    dataset[column] = dataset[column].str.replace(r"\(.*\)", "")
    dataset[column] = dataset[column].str.replace(r"\[.*\]", "")

#Stripping the percentage (%) sign in column 5
dataset['Percentage_of_Population_Change'] = dataset['Percentage_of_Population_Change'].str.strip('%')

# In the 'Elevation' column information is present in two units 'ft' and 'm'. Converting everthing to 'ft'
dataset['Elevation(ft)'] = dataset['Elevation(ft)'].str.replace(',', '')
for x in range(len(dataset['Elevation(ft)'])):
    elevation = dataset.iloc[x]['Elevation(ft)']
    if ('\xa0m' in elevation):
        elevation = elevation.split("-")[0]
        elevation = re.sub(r'[^0-9.]+', '', elevation)
        elevation = round(float(elevation) * 3.281, 2)
    else:
        elevation = elevation.split("-")[0].split("-")[0].split("–")[0].split('to')[0]
        elevation = re.sub(r'[^0-9.]+', '', elevation)
        elevation = round(float(elevation), 2)
    dataset.iloc[x]['Elevation(ft)'] = elevation

# In the 'Land Area' column information is present in two units 'sq mi' and 'km2'. Converting everthing to 'sq mi' and rounding the value to two decimal points
dataset['Land_Area(sq mi)'] = dataset['Land_Area(sq mi)'].str.replace(',', '')
for x in range(len(dataset['Land_Area(sq mi)'])):
    area = dataset.iloc[x]['Land_Area(sq mi)']
    if ('sq\xa0mi' in area):
        area = area.split("\xa0")[0]
        area = re.sub(r'[^0-9.]+', '', area)
        area = round(float(area), 2)
    else:
        area = area.split("\xa0")[0]
        area = re.sub(r'[^0-9.]+', '', area)
        area = round(float(area) / 2.58999, 2)
    dataset.iloc[x]['Land_Area(sq mi)'] = area


# In the 'Water Area' column information is present in two units 'sq mi' and 'km2'. Converting everthing to 'sq mi' and rounding the value to two decimal points
dataset['Water_Area(sq mi)'] = dataset['Water_Area(sq mi)'].str.replace(',', '')
for x in range(len(dataset['Water_Area(sq mi)'])):
    area = dataset.iloc[x]['Water_Area(sq mi)']
    if ('sq\xa0mi' in area):
        area = area.split("\xa0")[0]
        area = re.sub(r'[^0-9.]+', '', area)
        area = round(float(area), 2)
    else:
        area = area.split("\xa0")[0]
        area = re.sub(r'[^0-9.]+', '', area)
        area = round(float(area) / 2.5899, 2)
    dataset.iloc[x]['Water_Area(sq mi)'] = area

# Converting population columns (3,4) to integers
dataset['2018_Population_Estimate'] = dataset['2018_Population_Estimate'].str.replace(',', '')
for x in range(len(dataset['2018_Population_Estimate'])):
    population = int(dataset.iloc[x]['2018_Population_Estimate'])
    dataset.iloc[x]['2018_Population_Estimate'] = population

dataset['2010_Population_Census'] = dataset['2010_Population_Census'].str.replace(',', '')
for x in range(len(dataset['2010_Population_Census'])):
    population = int(dataset.iloc[x]['2010_Population_Census'])
    dataset.iloc[x]['2010_Population_Census'] = population

# Storing transformed data to finalDataset.csv file
dataset.to_csv('finalDataset.csv',index=False)


