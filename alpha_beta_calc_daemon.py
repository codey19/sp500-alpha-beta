#!/usr/bin/env python3
from datetime import datetime, timedelta, date

import yfinance as yf
import pandas as pd
from pandas import DataFrame
import numpy as np

import firebase_admin
from firebase_admin import db
import json


PATH_TO_PRIVATE_KEY='/home/csheng/redvest/sp500-ab-firebase-adminsdk-5bo38-00138df82d.json'
FIREBASE_URL='https://sp500-ab-default-rtdb.firebaseio.com/'

def get_finance_data(ticker, end_date, window_size):
    start_date = end_date + timedelta(days=-window_size)
    my_data = yf.download(ticker,  start=start_date,  end=end_date)
    sp_data = yf.download("^GSPC", start=start_date,  end=end_date)
    return my_data, sp_data

def init_file_db():
    cred_obj = firebase_admin.credentials.Certificate(PATH_TO_PRIVATE_KEY)
    default_app = firebase_admin.initialize_app(cred_obj, {'databaseURL':FIREBASE_URL})

def save_fire_db(end_date, alpha, beta):
    ref = db.reference("/")
    ab_record = {"End_Date": end_date.strftime("%b %d, %Y"), "Alpha": alpha, "Beta": beta}
    ref.push().set(ab_record)

def get_next_date():
    ref = db.reference("/")
    #query = ref.order_by_child('End_Date').limit_to_last(1)
    result = ref.get()
    if result:
        for key, value in result.items():
            last_date = datetime.strptime(value['End_Date'], "%b %d, %Y")
        last_date += timedelta(days=1)
        today = datetime.today()
        if last_date >= today:
            return today
        return last_date
    else:
        return datetime.strptime("Nov 1, 2024","%b %d, %Y")

if __name__ == "__main__":
    init_file_db()
    end_date = get_next_date()
    my_data, sp_data = get_finance_data("MSFT", end_date, 7)

    my_prices = my_data['Adj Close']
    sp_prices = sp_data['Adj Close']
    my_returns = my_prices.pct_change().dropna()
    sp_returns = sp_prices.pct_change().dropna()
    aligned_data = pd.concat([my_returns, sp_returns], axis=1, keys=['Stock', 'Market']).dropna()
    my_returns = aligned_data['Stock']
    sp_returns = aligned_data['Market']
    print(f"my_returns: {my_returns}")
    print(f"sp_returns: {sp_returns}")

    mean_my_return = 0
    for i in range(len(my_returns)):
        mean_my_return += my_returns.iloc[i,0]
    mean_my_return /= (len(my_returns) - 1)

    mean_sp_return = 0
    for i in range(len(sp_returns)):
        mean_sp_return += sp_returns.iloc[i,0]
    mean_sp_return /= (len(sp_returns) - 1)

    my_deviations = my_returns - mean_my_return
    sp_deviations = sp_returns - mean_sp_return
    print(f"my_deviations: {my_deviations}")
    print(f"sp_deviations: {sp_deviations}")

    covariance = 0;
    for i in range(len(my_deviations)):
        covariance += my_deviations.iloc[i, 0] * sp_deviations.iloc[i, 0]
    covariance /= (len(my_returns) - 1)

    sp_variance = 0;
    for i in range(len(sp_deviations)):
        sp_variance += sp_deviations.iloc[i, 0] ** 2
    sp_variance /= (len(my_returns) - 1)

    print(f"covariance: {covariance}")
    print(f"sp_variance: {sp_variance}")

    beta = covariance / sp_variance
    alpha = mean_my_return - beta * mean_sp_return

    print(f"Beta: {beta}")
    print(f"Alpha: {alpha}")

    save_fire_db(end_date, alpha, beta)
