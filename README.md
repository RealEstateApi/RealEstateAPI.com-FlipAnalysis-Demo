# RealEstateAPI.com-FlipAnalysis-Demo

## 2023 Flip Indicator Analysis Demo
In this demo we leverage RealEstateAPI.com's Property Search API to find the top 10 states with the highest count of SFR/MFR properties sold in 2023 where the prior owner held the property for 6 to 12 months. This table is then weighted by the size of the state in terms of total properties and sales. This data point may be a good indicator to begin the process of identifying flipped properties.

Use this project as a starting point to analyze hot markets, identify trends, and gain market insights. Keep in mind that this is a high level analysis focusing on only one of many indicators used to identify flips. You should not make financial decisions based on this demo and you should explore the data further to gain deeper insights.

## How to run this demo
1. Make sure you have python installed:
```
python3 --version
```

or, depending on your environment:

```
python --version
```
2. Clone the repo and create a virtual environment in the root of the project folder:
```
python3 -m venv .venv
```
or, depending on your python version
```
python -m venv .venv
```
3. Activate your virtual environment
```
source .venv/bin/activate
``` 
4. Install requirements (see requirements.txt)
```
 pip install -r requirements.txt
```
5. Paste your RealEstateAPI.com API key into app.py, line 9
```
api_key = "YOUR-API-KEY"
```
6. Run the project with this command:
```
streamlit run app.py
```
7. You can see the Streamlit app running at:
```
http://localhost:8501
```

8. When you're done, to deactivate the virtual environment, run deactivate from your terminal
```
deactivate
```

## Notes
***WARNING:*** Uncommenting and running the code from line 245-248 consumes a significant amount of API credits. This code retrieves all propert search results for the top 3 states to map their coordinates which uses 1 credit per record. 

Everything elase uses  { count: true } to get counts of records matching the queries. This does not consume API credits.
