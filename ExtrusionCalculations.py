import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def truncate(series):
    series = series[:-3]
    return series

def get_data(start,end,machine):
    file = machine+' Blender Data1.csv'
    raw_data = pd.read_csv(file,low_memory=False)
    raw_data.Time = pd.to_datetime(raw_data.Time)
    blender_data = raw_data[(raw_data.Time>=start) & (raw_data.Time<= end)]
    if machine != '151':
        col_names = ['Time','4.5 HopperA','4.5 HopperB','4.5 HopperC','2.5 HopperA','2.5 HopperB','2.5 HopperC','LineSpeed','ExtruderASpeed','ExtruderBSpeed']
        col_dict = dict(zip(blender_data.columns.values.tolist(),col_names))
        blender_data = blender_data.rename(columns = col_dict)
    else:
        col_names = ['Time','HopperA','HopperB','HopperC','ExtruderSpeed','LineSpeed']
        col_dict = dict(zip(blender_data.columns.values.tolist(),col_names))
        blender_data = blender_data.rename(columns = col_dict)
    return blender_data

def gsm_calc(parameters):
    width = parameters[3]
    data = get_data(parameters[0],parameters[1],parameters[2])
    gsm = data.iloc[:,1:7].diff(axis = 0)/5/width*1000
    gsm['LineSpeed']=data['LineSpeed'].replace(0,5)
    gsm.iloc[:,:6] = gsm.iloc[:,:6].div(gsm.LineSpeed, axis = 0)
    gsm = gsm.dropna(axis = 0)
    col_names = gsm.columns.values.tolist()
    for i in range(0,6):
        col_names[i]+= ' gsm'
    col_dict = dict(zip(gsm.columns.values.tolist(),col_names))
    gsm = gsm.rename(columns = col_dict)
    gsm['4.5 Total gsm'] = gsm.iloc[:,0:3].sum(axis = 1)
    gsm['2.5 Total gsm'] = gsm.iloc[:,3:6].sum(axis = 1)
    gsm['4.5 Total gsm'] = gsm['4.5 Total gsm'].apply(lambda x: 0 if x<0 else x)
    gsm['2.5 Total gsm'] = gsm['2.5 Total gsm'].apply(lambda x: 0 if x<0 else x)
    gsm['Total gsm'] = gsm['4.5 Total gsm']+gsm['2.5 Total gsm']
    gsm['Time'] = data.Time.astype(str).str[5:16]
    return gsm

def gsm_calc_151(parameters):
    width = parameters[3]
    data = get_data(parameters[0],parameters[1],parameters[2])
    gsm = data.iloc[:,1:4].diff(axis = 0)/5/width*1000
    gsm['LineSpeed']=data['LineSpeed']
    gsm.iloc[:,:3] = gsm.iloc[:,:3].div(gsm.LineSpeed, axis = 0)
    gsm = gsm.dropna(axis = 0)
    col_names = gsm.columns.values.tolist()
    for i in range(0,3):
        col_names[i]+= ' gsm'
    col_dict = dict(zip(gsm.columns.values.tolist(),col_names))
    gsm = gsm.rename(columns = col_dict)
    gsm['Total gsm'] = gsm.iloc[:,0:3].sum(axis = 1)
    gsm['Total gsm'] = gsm['Total gsm'].apply(lambda x: 0 if x<0 else x)
    gsm['Time'] = data.Time.astype(str).str[5:16]
    return gsm

def time_value(t):
    hour = int(t[:2])
    minute = int(t[3:])
    return hour*60+minute

def recipe_calc(parameters):
    gsm = gsm_calc(parameters)
    r1 = round(gsm.iloc[:,0:3].div(gsm['4.5 Total gsm'], axis = 0)*100,2)
    r2 = round(gsm.iloc[:,3:6].div(gsm['2.5 Total gsm'], axis = 0)*100,2)
    recipe = pd.concat([r1,r2], axis = 1)
    col_names = gsm.columns.values.tolist()[:-3]
    for i in range(0,len(gsm.columns.values)-3):
        col_names[i] = col_names[i].replace('gsm','resin %')
    col_dict = dict(zip(gsm.columns.values.tolist(),col_names))
    recipe = recipe.rename(columns = col_dict)
    recipe['Time'] = gsm.Time
    return recipe

def recipe_calc_151(parameters):
    gsm = gsm_calc(parameters)
    recipe = round(gsm.iloc[:,0:3].div(gsm['Total gsm'], axis = 0)*100,2)
    col_names = gsm.columns.values.tolist()[:3]
    for i in range(0,3):
        col_names[i] = col_names[i].replace('gsm','resin %')
    col_dict = dict(zip(gsm.columns.values.tolist(),col_names))
    recipe = recipe.rename(columns = col_dict)
    recipe['Time'] = gsm.Time
    return recipe


def gsm_convert(gsm):
    mask = (gsm['LineSpeed'] <=50)
    gsm.loc[mask,['4.5 Total gsm','2.5 Total gsm','Total gsm']] = 0
    mask2 = (gsm['Total gsm']>= gsm['Total gsm'].mean()+20)
    gsm.loc[mask2,['4.5 Total gsm','2.5 Total gsm','Total gsm']] = 0
    return gsm

def gsm_convert_151(gsm):
    mask = (gsm['LineSpeed'] <=50)
    gsm.loc[mask,['Total gsm']] = 0
    return gsm
