import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
from fbprophet import Prophet
import pytz
import datetime as dt
from datetime import datetime, timedelta
import sqlite3 as sql

"""#Reading the Excel Sheet"""

df = pd.concat(pd.read_excel("incident.xlsx", sheet_name=None), ignore_index=True)


df.Created = pd.to_datetime(df.Created, unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')


df["Priority"] = df['Priority'].str.extract('(\d+)').astype(int)


"""## Create DataFrame with Required Columns"""

dataset = pd.DataFrame()
#dataset['DateTime'] = df['Created']
dataset['Date'] = pd.to_datetime(df['Created']).dt.date
dataset['Time'] = pd.to_datetime(df['Created']).dt.hour
dataset['Priority'] = np.where(df['Priority']>2, 'P34', 'P12')
dataset["Assignment group"] = df["Assignment group"]


"""## Count the Number of Incidents"""

dataset = dataset.groupby(['Date', 'Time',	'Priority', 'Assignment group']).size().reset_index().rename(columns={0:'Count'})


"""##Convert Date Column to DateTime column based upon Time Shift"""

dataset["Date"] = pd.DataFrame(pd.to_datetime(dataset.Date))
for i in tqdm(range(0, len(dataset.Date))):
  dataset.Date[i] = dataset.Date[i].replace(hour=dataset.Time[i], minute=0, second=0)


#t = dataset.groupby('Assignment group').size().reset_index()

"""# Get All Grps"""

grps = dataset["Assignment group"].unique()

"""#Dataset Creation"""

def create_data(t_dataset, gr, pr_type):
  rng = pd.date_range(start=t_dataset.Date[0], end=t_dataset.Date[len(t_dataset.Date)-1], freq='1H')
  temp_year = pd.DataFrame({ 'ds': rng})
  temp_year["y"] = np.zeros(len(temp_year.ds))
  temp_dataset = pd.DataFrame(t_dataset.loc[t_dataset['Assignment group'] == gr])
  if pr_type == 0:
    temp_dataset = temp_dataset.loc[temp_dataset['Priority'] == "P12"]
  else:
    temp_dataset = temp_dataset.loc[temp_dataset['Priority'] == "P34"]
  temp_dataset = temp_dataset.reset_index(drop=True)
  #temp_dataset = temp_dataset.drop(['Time'], axis=1)
  temp_year['y'] = temp_year['ds'].map(temp_dataset.set_index('Date')['Count']).fillna(0)
  return temp_year

"""#Prediction"""

def fb_model(X_train):
  model=Prophet(yearly_seasonality=True,changepoint_prior_scale=0.1, n_changepoints=100, seasonality_prior_scale=10)
  model.fit(X_train)
  return model

bins = [-1, 5, 13, 21, np.inf]
names = ['C', 'A', 'B', 'C']

master_dict = {}

"""#For Loop"""

st = pd.to_datetime("today") - timedelta(days=pd.to_datetime("today").weekday())
st = st.replace(hour=6, minute=0, second=0, microsecond=0)
en = st +  timedelta(days=7)
en = en.replace(hour=5)
range1 = pd.date_range(start=st, end= en, freq='1H')
future = pd.DataFrame({ 'ds': range1})

for i in tqdm(range(0, len(grps))):
  grp_df = pd.DataFrame()
  for j in range(0, 2):
    temp_year = create_data(pd.DataFrame(dataset), grps[i], j)
    model = fb_model(pd.DataFrame(temp_year))
    X_pred = model.predict(future)

    temp_data = pd.DataFrame()
    temp_data["DateTime"] = X_pred.ds
    temp_data['Shift'] = pd.cut(pd.to_datetime(X_pred['ds']).dt.hour, bins, labels=names, ordered=False)
    temp_data["Date"] = pd.to_datetime(X_pred['ds']).dt.date
    temp_data["Incidents_Expected"] = X_pred["yhat"].apply(np.round)

    if j == 0:
      temp_data.insert(0, "Priority", "Priority 1&2")
      temp_data["Incidents_Expected"] = X_pred["yhat"].round(decimals=4)
    else:
      temp_data.insert(0, "Priority", "Priority 3&4")
      temp_data["Incidents_Expected"] = X_pred["yhat"].apply(np.round)
    temp_data.insert(0, "Assignment_Group", grps[i])
    grp_df = grp_df.append(temp_data, ignore_index=True)
  master_dict[grps[i]] = pd.DataFrame(grp_df)

for i in tqdm(range(0, len(grps))):
  master_dict[grps[i]].insert(4, "StartDate", master_dict[grps[i]]["Date"])
#  master_dict[grps[i]]["StartDate"] = master_dict[grps[i]]["Date"]
  for j in range(0, len(master_dict[grps[i]]["StartDate"])):
    if master_dict[grps[i]]["DateTime"][j].hour < 6:
      master_dict[grps[i]]["StartDate"][j] -= timedelta(days=1)


yourdf = pd.concat(master_dict,axis=0,ignore_index=True)
conn = sql.connect('Predictions.db')
yourdf.to_sql('Predictions', conn, if_exists='replace')
