import streamlit as st
import requests
import pandas as pd
import json
import os

last_sale_date_min = "2023-01-01"
last_sale_date_max = "2023-12-31"
api_key = "YOUR-API-KEY-HERE"

state_codes = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming'
}

def property_search(params):
    # API endpoint and parameters
    url = "https://api.realestateapi.com/v2/PropertySearch"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "x-user-id": "flip-analysis-demo"
    }
    
    # Making the API request
    print(f"Querying Property Search with: {params}")
    
    response = requests.post(url, json=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if params.get('count'):
            return data.get('resultCount')
        else:
            return data
    else:
        st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return []
    
def get_state_level_data():
    state_df = pd.DataFrame(list(state_codes.items()), columns=['State Code', 'State Name'])

    # Get a count of SFR/MFR properties in each state
    query = {
        "count": True,
        "or": [
            {"property_type": "SFR"},
            {"property_type": "MFR"}
        ]
    }

    state_df['SFR/MFR Count'] = state_df['State Code'].apply(lambda state: property_search({**query, "state": state}))


    # Get a count of SFR/MFR properties that were sold in each state
    query = {
        "count": True,
        "last_sale_date_max": last_sale_date_max,
        "last_sale_date_min": last_sale_date_min,
        "or": [
            {"property_type": "SFR"},
            {"property_type": "MFR"}
        ]
    }

    state_df['Properties Sold'] = state_df['State Code'].apply(lambda state: property_search({**query, "state": state}))


    # Get a count of SFR/MFR properties sold that were owned by the previous owner for 6-12 months
    query = {
        "count": True,
        "last_sale_date_min": last_sale_date_min,
        "last_sale_date_max": last_sale_date_max,
        "prior_owner_months_owned_min": 6,
        "prior_owner_months_owned_max": 12,
        "or": [
            {"property_type": "SFR"},
            {"property_type": "MFR"}
        ]
    }

    state_df['Flip Indicator Count'] = state_df['State Code'].apply(lambda state: property_search({**query, "state": state}))


    # Calculate weights for each state based on total properties sold and flip indicator count
    state_df['Properties Sold Ratio'] = state_df['State Code'].apply(lambda state: state_df.loc[state_df['State Code'] == state, 'Properties Sold'].values[0] / state_df.loc[state_df['State Code'] == state, 'SFR/MFR Count'].values[0])
    state_df['Prior Owner Mos. Owned Ratio'] = state_df['State Code'].apply(lambda state: state_df.loc[state_df['State Code'] == state, 'Flip Indicator Count'].values[0] / state_df.loc[state_df['State Code'] == state, 'Properties Sold'].values[0])
    state_df['Score'] = state_df['State Code'].apply(lambda state: (state_df.loc[state_df['State Code'] == state, 'Properties Sold Ratio'].values[0] + state_df.loc[state_df['State Code'] == state, 'Prior Owner Mos. Owned Ratio'].values[0]) / 2)


    # Format the dataframe
    state_df = state_df.drop(columns=['Properties Sold Ratio', 'Prior Owner Mos. Owned Ratio'])
    state_df = state_df.sort_values(by='Score', ascending=False)
    state_df = state_df.reset_index(drop=True)
    state_df = state_df.head(10)

    return state_df

def map_data(state):

    if state is None:
        st.error("Please enter a state code for the map data")
        return

    if state not in state_codes:
        st.error("Invalid state code")
        return
    
    all_properties = []
    state_data_file = f"data/{state}_data.json"
    
    if os.path.exists(state_data_file):
        with open(state_data_file, 'r') as file:
            all_properties = json.load(file)
    else:
        query = {
            "size": 250,
            "state": state,
            "last_sale_date_min": last_sale_date_min,
            "last_sale_date_max": last_sale_date_max,
            "prior_owner_months_owned_min": 6,
            "prior_owner_months_owned_max": 12,
            "or": [
                {"property_type": "SFR"},
                {"property_type": "MFR"}
            ]
        }

        data = property_search(query)
        for d in data['data']:
            all_properties.append(d)

        result_index = 0
        while len(all_properties) < data['resultCount']:
            query['resultIndex'] = result_index
            response = property_search(query)
            if response:
                for d in response['data']:
                    all_properties.append(d)
                result_index += response['recordCount']
            else:
                break
    
    coordinates = []
    for property in all_properties:
        if 'lastSaleAmount' not in property or 'latitude' not in property or 'longitude' not in property:
            # Skip this record if any of the required keys are missing
            continue
        
        if property['latitude'] is None or property['longitude'] is None:
            continue
        else:
            if property['lastSaleAmount'] is not None and property['priorSaleAmount'] is not None:
                if property['lastSaleAmount'] > property['priorSaleAmount']:
                    coordinates.append({
                        "latitude": property['latitude'],
                        "longitude": property['longitude'],
                        "name": property['id']
                    })

    # Display the map
    st.map(coordinates, color="#7B2CBF")
    
    if not os.path.exists(state_data_file):
        with open(state_data_file, 'w') as file:
            json.dump(all_properties, file)

def main():

    # Title and description
    st.title("Flip Indicator Analysis")
    st.header("Powered by RealEstateAPI.com")

    # Get state level data
    state_level_df = get_state_level_data()
    
    st.subheader("State Level Analysis")

    state_df_description = f'''
    The table below shows the top 10 states with the highest count of 
    SFR/MFR properties sold between {last_sale_date_min} and {last_sale_date_max} where the 
    prior owner held the property for 6 to 12 months. This data point may be 
    a good indicator to begin the process of identifying flipped properties.
    
    Use this project as a starting point to analyze hot markets, identify trends,
    and gain market insights. Keep in mind that this is a high level analysis 
    focusing on only one of many indicators used to identify flips. You should 
    not make financial decisions based on this demo and you should explore 
    the data further to gain deeper insights.
    '''

    # Write state level data to Streamlit
    st.text(state_df_description)
    st.write(state_level_df)

    # WARNING: Uncommenting the code below will use up your API credits!
    # Everything above these lines uses { count: true } to get the data
    # which does not consume API credits. The code below will consume a
    # significant amount of API credits:

    # top_states = state_level_df['State Code'].head(3).tolist()
    # for state in top_states:
    #     st.subheader(f"Map Data for {state_codes[state]}")
    #     map_data(state)

if __name__ == "__main__":
    main()
