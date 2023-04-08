import calendar
import copy
import csv
import itertools
import math
import os
import pprint
import random
import sys
import time
from collections import deque
from datetime import *
from datetime import date
from datetime import datetime as dtt
from datetime import timedelta
from timeit import default_timer

import numpy as np
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from pandas import Timestamp
from pytz import timezone
from scipy.stats import norm

# import matplotlib.pyplot as plt


# import myiq

global today

today = dtt.today()




monthly_codes = {"F": ("January", 1), 'G': ('February', 2), "H": ('March', 3), "J": ('April', 4), "K": ('May', 5), "M": ('June', 6), "N": (
    'July', 7), "Q": ('August', 8), "U": ('September', 9), "V": ('October', 10), "X": ('November', 11), "Z": ('December', 12)}
monthly_codes_int = {1: ("F", "January"), 2: ('G', 'February'), 3: ("H", 'March'), 4: ("J", 'April'), 5: ("K", 'May'), 6: ("M", 'June'), 7: (
    "N", 'July'), 8: ("Q", 'August'), 9: ("U", 'September'), 10: ("V", 'October'), 11: ("X", 'November'), 12: ("Z", 'December')}

test_option = "XGV22C1300000"
test_option2 = 'SMXU22P2410000'


class option:
    def __init__(self, option_string, data=False, for_info=False, msg=False):
        self.debug_code = 4
        self.det_name = option_string
        self.msg = msg
        # print(self.det_name)
        self.option_info()
        # self.front_month_bool, self.front_month_string = self.get_front_month()
        # self.get_option_paths()
        self.mmcc = 0
        # if not for_info:
        # 	self.data = data
        # 	self.convert_response()
        # 	if self.is_new_data:
        # 		self.new_data()

    # def convert_response(self):
    # 	'''
    # 	converts response from api to a dataframe
    # 	must convert to datetimeindex and sortindex
    # 	'''
    # 	if self.data == False:
    # 		self.load_raw_test()
    # 	else:
    # 		#msg = myiq.get_ts_tickdata(self.det_name,1500,200)
    # 		if type(self.msg) != bool:
    # 			self.raw_new_df = myiq.convert_msg_to_raw(self.msg)
    # 			self.is_new_data = True
    # 		else:
    # 			self.is_new_data = False

    def find_starting_slice(self):
        '''
        Parameters
        ----------
        option : string <> 'SMXU22P2410000' "DX4V22C1100000"
                the option name

        Returns
        -------
        int
           searchs for first 2 connsecutive number in the option and returns
           the position, so it can slice the string and find the ticker
           return is -1 to account for month code, between year and ticker

        '''
        option = self.det_name
        # print("Option name = "+str(option))
        ll = list(option)
        for i in range(len(ll)):
            st = ll[i]+ll[i+1]
            if st.isnumeric():
                return i-1

    def option_info(self):
        global today
        ii = self.find_starting_slice()

        self.ticker = self.det_name[:ii]
        self.weekly = "DX" in self.ticker
        if self.weekly:
            self.weekly_dx = self.ticker[-1:]
        else:
            self.weekly_dx = "3"
        self.month_code = self.det_name[ii:ii+1]
        self.month_string = monthly_codes[self.month_code][0]
        self.year = self.det_name[ii+1:ii+3]
        self.option_type = self.det_name[ii+3:ii+4]
        self.strike = self.det_name[ii+4:-2]
        if self.option_type == "C":
            self.type = "Call"
        else:
            self.type = "Put"
        self.expiry = self.option_expiration()
        self.expiry_time = self.expiry+relativedelta(hours=14)
        self.days_left = (self.expiry - today).days
        # print("Ticker = ", self.ticker)
        # print("month_code = ", self.month_code)
        # print("month_string = ", self.month_string)
        # print("year = ", self.year)

        # print("option_type = ", self.option_type)
        # print("strike = ", self.strike)
        # print("days_till_expire = ", self.days_left)

    def option_expiration(self):
        '''
                Parameters
        ----------
        month : string or int
                dictionary key for monthly_codes
        year : TYPE
                DESCRIPTION.
        -------
        TYPE
                DESCRIPTION.
        '''
        if self.weekly:
            ty = self.make_list()
            month = monthly_codes[self.month_code][1]
            week = int(self.ticker[-1])-1
            return ty[month][week]
        else:
            the_year = 2000+int(self.year)
            if str(self.month_code).isnumeric():
                date_obj = dtt(the_year, self.month_code, 1)
            else:
                date_obj = dtt(the_year, monthly_codes[self.month_code][1], 1)
            day = 21 - (calendar.weekday(date_obj.year,
                        date_obj.month, 1) + 2) % 7
            # print(dtt(date_obj.year, date_obj.month, day))

            return dtt(date_obj.year, date_obj.month, day)

    def weekly_exp(self, mm, yy):
        month_start = dtt(yy, mm, 1)
        if month_start.weekday() == 4:
            m1 = month_start.date()
        else:
            m1 = month_start + timedelta((4-month_start.weekday()) % 7)

        m2 = m1+timedelta(days=7)
        m3 = m1+timedelta(days=14)
        m4 = m1+timedelta(days=21)
        m5 = m1+timedelta(days=28)


        return m1, m2, m3, m4, m5

    def make_list(self):
        TY = {}
        year = int(self.year)+2000
        for i in range(1, 13):
            m1, m2, m3, m4, m5 = self.weekly_exp(i, year)
            TY[i] = [m1, m2, m3, m4]
            if m5.month != i:
                m5 = 0
            TY[i].append(m5)

        return TY

    # def get_front_month(self):
    # 	global today
    # 	front_month_bool = False
    # 	#today = dtt.today()
    # 	day = 21 - (calendar.weekday(today.year, today.month, 1) + 2) % 7
    # 	if day <= today.day :
    # 		front_month = today.month+1

    # 	else:
    # 		front_month = today.month

    # 	if front_month == monthly_codes[self.month_code][1]:
    # 		front_month_bool = True
    # 	#print(front_month)
    # 	return front_month_bool, front_month

    # def get_option_paths(self):
    # 	self.path_main_dir = r'C:\Users\Admin\anaconda3\envs\phil\DDOI\opt_data\\'
    # 	if self.weekly:
    # 		self.path_opt = self.path_main_dir+self.year+"\\"+self.month_string+"\\"+self.option_type
    # 		self.path_raw_dir = self.path_main_dir+self.year+"\\"+self.month_string+"\\"+self.option_type+"\\"+self.weekly_dx+"\\"+"Raw"+"\\"
    # 		self.path_raw_file = self.path_raw_dir+self.det_name+".csv"
    # 	else:
    # 		self.path_opt = self.path_main_dir+self.year+"\\"+self.month_string+"\\"+self.option_type
    # 		self.path_raw_dir = self.path_main_dir+self.year+"\\"+self.month_string+"\\"+self.option_type+"\\"+"Raw"+"\\"
    # 		self.path_raw_file = self.path_raw_dir+self.det_name+".csv"
    # 	if not os.path.exists(self.path_opt):
    # 		os.makedirs(self.path_opt)
    # 	if not os.path.exists(self.path_raw_dir):
    # 		 os.makedirs(self.path_raw_dir)

    # 	self.path_processed_dir = self.path_raw_dir
    # 	self.path_processed_file = self.path_processed_dir+"\\"+self.det_name+"_processed.csv"
    # 	self.path_resampled_dir = self.path_opt
    # 	self.path_resampled_file = self.path_resampled_dir+"\\"+self.det_name+"_resampled.csv"

    # def load_raw_test(self):
    # 	dirr = 'C:\\Users\\Admin\\anaconda3\\envs\\phil\\DDOI\\opt\\'
    # 	main_db1 = pd.read_csv(dirr+self.det_name+".csv", names=['Time', 'Date', 'Price', 'Inc Vol', 'Bid',	'Ask', 'Volume', 'TickID',	'Info',	'Mkt Center'],skiprows=1)
    # 	#main_db1 = pd.read_csv(dirr+self.det_name+".csv", names=['Time', 'Date', 'Price', 'Inc Vol', 'Bid',	'Ask', 'Volume', 'B Size',	'A Size', 'TickID',	'Info',	'Mkt Center', 'Trade Conditions'],skiprows=1)
    # 	main_db2 = main_db1.copy()
    # 	main_db2['datetime'] = pd.to_datetime(main_db1['Date'] +' '+ main_db1['Time'])
    # 	self.raw_new_df = main_db2.set_index('datetime')
    # 	self.raw_new_df.index = pd.to_datetime(self.raw_new_df.index)

    # def debug(self):
    # 	self.raw_new_df = self.raw_old_df

    # def save_raw(self):
    # 	if not self.raw_old_bool:
    # 		print(self.raw_old_bool)
    # 		self.raw_df_updated = self.raw_new_df.copy()
    # 	self.raw_df_updated.sort_index(inplace=True)
    # 	self.raw_df_updated.to_csv(self.path_raw_file,header=True)
# 	def load_raw(self):
# 		if os.path.exists(self.path_raw_file):
# 			print(self.path_raw_file)
# 			self.raw_old_bool = True
# 			self.raw_old_df = pd.read_csv(self.path_raw_file,
# 							names=['datetime', 'Time', 'Date', 'Price', 'Inc Vol', 'Bid',	'Ask', 'Volume', 'TickID',	'Info',	'Mkt Center'],
# 							dtype = {'Time': 'str','Date': 'str','Price': 'float64','Inc Vol': 'float64',
# 									 'Bid': 'float64','Ask': 'float64', 'Volume': 'float64','TickID': 'str','Info': 'str','Mkt Center': 'str'},skiprows=1,index_col=0)
# # 					 names=['datetime', 'Time', 'Date', 'Price', 'Inc Vol', 'Bid',	'Ask', 'Volume', 'B Size',	'A Size', 'TickID',	'Info',	'Mkt Center', 'Trade Conditions'],skiprows=1,index_col='datetime')
# 			#print(self.raw_old_df)
# 			self.raw_old_df.index = pd.to_datetime(self.raw_old_df.index)
# 			print("loading old raw")
# 		else:
# 			self.raw_old_bool = False

# 	def save_processed(self):
# 		self.processed_df.to_csv(self.path_processed_file,header=True)
# 	def load_processed(self):
# 		if os.path.exists(self.path_processed_file):
# 			self.processed_df = pd.read_csv(self.path_processed_file
# 					 ,names=['datetime', 'Time', 'Date', 'Price', 'Inc Vol', 'Bid',	'Ask', 'Volume', 'TickID',	'Info',	'Mkt Center',
# 							 'Buy','Spread','MM_balance','Running_MM_Contracts_balance','cost_to_MM','Running_Cost sum'],
# 					 dtype = {'Time': 'str','Date': 'str','Price': 'float64','Inc Vol': 'float64',
# 								 'Bid': 'float64','Ask': 'float64', 'Volume': 'float64','TickID': 'str','Info': 'str','Mkt Center': 'str',
# 								 'Buy':"int",'Spread': 'float64','MM_balance':"int",'Running_MM_Contracts_balance':"int",'cost_to_MM': 'float64','Running_Cost sum': 'float64'
# 								 },skiprows=1,index_col=0)
# 		else:
# 			print("No processed file to load")

# 	def save_resample(self):
# 		self.resampled_df.to_csv(self.path_resampled_file,header=True)
# 	def load_resample(self):
# 		if os.path.exists(self.path_resampled_file):
# 			print("loading "+self.det_name)
# 			self.resampled_df = pd.read_csv(self.path_resampled_file
# 					 ,names=['datetime','Volume','MM_Contracts_added','Running_MM_Contracts_balance','cost_to_MM',"Running_Cost sum","Price Avg","Spread Avg"],
# 					 dtype = {'Volume': 'float64','MM_Contracts_added':"int",'Running_MM_Contracts_balance':"int",
# 			   'cost_to_MM': 'float64',"Running_Cost sum": 'float64',"Price Avg": 'float64',"Spread Avg": 'float64'},skiprows=1,index_col=0)
# 			self.resampled_df.index = pd.to_datetime(self.resampled_df.index)
# 		else:
# 			print("No resampled file to load")
# 			self.resampled_df = "None"

    # def new_data(self):
    # 	#print("Checking/loading old Raw "+self.det_name)
    # 	self.load_raw()
    # 	if self.raw_old_bool:
    # 		print("Old raw data, merging data "+self.det_name)
    # 		self.update_raw()
    # 	#print("Saving Raw "+self.det_name)
    # 	self.save_raw()
    # 	#print("Processing "+self.det_name)
    # 	self.process()
    #    # print("Saving Processing "+self.det_name)
    # 	self.save_processed()
    # 	#print("Resampling "+self.det_name)
    # 	self.create_new_resampled()
    # 	#print("saving resampled "+self.det_name)
    # 	self.save_resample()


# 	def update_raw(self):
# 		error_code = module_for_error+" ** "+"update_raw"
# 		_debug_print(error_code,1)
# 		try:
# 			self.raw_new_df = self.raw_new_df.astype({'Date': 'str','Volume': 'float64','Inc Vol': 'float64'})
# 			self.raw_df_updated = pd.concat([self.raw_old_df.dropna(), self.raw_new_df.dropna()]).drop_duplicates(keep='last')
# 			self.raw_df_updated = self.raw_df_updated[~self.raw_df_updated.index.duplicated(keep='last')]
# 			_debug_print(["self.raw_df_updated = "+str(self.raw_df_updated)],3)
# # 			df1 = pd.concat([self.raw_old_df.dropna(), self.raw_new_df.dropna()], axis=0, ignore_index=False)
# # 			df1['dt'] = df1.index
# # 			df = df1.drop_duplicates(subset='dt', keep='last')
# # 			#df = df1.index.drop_duplicates()
# # 			self.raw_df_updated = df.sort_index()
# # 			#return df.sort_index()


# 		except Exception as error:
# 			exc_type, exc_value, exc_tb = sys.exc_info()
# 			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
# 			print(error_code+' exception caught', exc_type,fname,exc_tb.tb_lineno)
# 			with open("except.txt", "a") as text_file:
# 				text_file.write('{} {} exception caught \n{} \n'.format(dtt.now(),error_code,str(error)))
# 				text_file.write('{}  exception type = {}  in file = {}  line Number = {} \n'.format(dtt.now(),exc_type,fname,exc_tb.tb_lineno))


# 	def process(self):
# 		#df_backup = df
# 		#df = df1.dropna()
# 		#self.processed_df = self.raw_df_updated[::-1].copy()
# 		self.processed_df = self.raw_df_updated.copy()
# 		self.processed_df['Buy'] = np.where(self.processed_df.Bid==self.processed_df.Price,1,-1)
# 		self.processed_df['Spread'] = abs(self.processed_df['Bid'].astype(float) - self.processed_df['Ask'].astype(float))
# 		self.processed_df['MM_balance'] = np.where(self.processed_df.Buy>0,self.processed_df['Inc Vol'],(self.processed_df['Inc Vol']*-1))
# 		self.processed_df['Running_MM_Contracts_balance'] = self.processed_df.MM_balance.cumsum()
# 		## calculate the cost or outstanding to MM
# 		self.processed_df['cost_to_MM'] = (self.processed_df['MM_balance']*self.processed_df['Price'])*-1
# 		self.processed_df['Running_Cost sum'] = self.processed_df.cost_to_MM.cumsum()
# 		self.count_diff()

# 	def count_diff(self):
# 		self.load_resample()
# 		if isinstance(self.resampled_df, pd.DataFrame) :
# 			old_amount = self.resampled_df['Running_MM_Contracts_balance'][-1]
# 			new_amount = self.processed_df['Running_MM_Contracts_balance'][-1]
# 			self.mmcc = int(new_amount)-int(old_amount)


# 	def create_new_resampled(self):
# 		df = self.processed_df
# 		df.index = pd.to_datetime(df.index)
# 		print(df)
# 		dflast=df.resample('1h').last()
# 		dfmulti=df.resample('1h').agg({'Price':np.mean,'Inc Vol':np.sum,'Volume':np.sum,'MM_balance':np.sum,'Spread':np.mean})
# 		HR = dflast
# 		del HR['Time']
# 		del HR['Date']
# 		del HR['Inc Vol']
# 		del HR['MM_balance']
# 		del HR['Spread']
# 		del HR['Bid']
# 		del HR['Ask']
# # 		del HR['Bid2']
# # 		del HR['Ask2']
# 		del HR['Buy']
# 		del HR['Price']

# 		#del HR['B Size']
# 		#del HR['A Size']
# 		del HR['TickID']
# 		del HR['Info']
# 		del HR['Mkt Center']

# 		HR["Price Avg"] = dfmulti['Price']
# 		HR["Spread Avg"] = dfmulti['Spread']
# 		HR["MM_Contracts_added"] = dfmulti['MM_balance']
# 		gr = HR.dropna()
# 		gr1 =  gr[['Volume','MM_Contracts_added','Running_MM_Contracts_balance','cost_to_MM','Running_Cost sum','Price Avg','Spread Avg']]

# 		self.resampled_df = gr1


# 	def transpose(self,combi):
# 		if self.front_month_bool:
# 			if self.type == "Call":
# 				for hour in self.resampled_df.index :
# 					combi.front_calls_df.at[hour,self.strike] = self.resampled_df.at[hour,"Running_MM_Contracts_balance"]
# 					#print("found call" +str(hour) + self.month_string +"strike = "+self.strike)

# 			if self.type == "Put":
# 				 for hour in self.resampled_df.index :
# 					 combi.front_puts_df.at[hour,self.strike] = self.resampled_df.at[hour,"Running_MM_Contracts_balance"]
# 					 #print("found put" +str(hour) + self.month_string +"strike = "+self.strike)

# 		if not self.front_month_bool:
# 			if self.type == "Call":
# 				for hour in self.resampled_df.index :
# 					combi.front_calls_df_two.at[hour,self.strike] = self.resampled_df.at[hour,"Running_MM_Contracts_balance"]
# 					#print("found call" +str(hour) + self.month_string +"strike = "+self.strike)
# 			if self.type == "Put":
# 				 for hour in self.resampled_df.index :
# 					 combi.front_puts_df_two.at[hour,self.strike] = self.resampled_df.at[hour,"Running_MM_Contracts_balance"]
# 					 #print("found put" +str(hour) + self.month_string +"strike = "+self.strike)
# 		return combi


# class weekly_exps():
# 	def __init__(self):
# 		self.TY,self.NY,self.dx_list = self.todays_dx_exps()
# 		print("Calcullated weekly exps")

# 	def weekly_exp(self,mm,yy):
# 		month_start = dtt(yy,mm,1)
# 		if month_start.weekday() == 4:
# 			m1 = month_start.date()
# 		else:
# 			m1 = month_start + timedelta( (4-month_start.weekday()) % 7 )

# 		m2 = m1+timedelta(days = 7)
# 		m3 = m1+timedelta(days = 14)
# 		m4 = m1+timedelta(days = 21)
# 		m5 = m1+timedelta(days = 28)

# 		return m1,m2,m3,m4,m5

# 	def make_list(self,today):
# 		TY = {}
# 		NY = {}
# 		for i in range(1,13):
# 			m1,m2,m3,m4,m5 = self.weekly_exp(i,today.year)
# 			TY[i]=[m1,m2,m3,m4]
# 			if m5.month != i:
# 				m5 = 0
# 			TY[i].append(m5)

# 			m1,m2,m3,m4,m5 = self.weekly_exp(i,today.year+1)
# 			NY[i]=[m1,m2,m3,m4]
# 			if m5.month != i:
# 				m5 = 0
# 			NY[i].append(m5)

# 		return TY,NY

# 	def todays_dx_exps(self):
# 		global today
# 		#global dx_list
# 		dx_list = [0,0,0,0,0]
# 		#today = dtt.today()
# 		TY,NY = self.make_list(today)

# 		this_fri = today + timedelta( (4-today.weekday()) % 7 )
# 		for i in range(len(TY[this_fri.month])):
# 			if TY[this_fri.month][i]:
# 				if TY[this_fri.month][i].date() == this_fri.date():
# 					this_fri_dx = i+1
# 					dx_list[i]=this_fri.date()

# 		## find and fill in DX dates until this friday
# 		for ii in range(len(dx_list)):
# 			if dx_list[ii] == 0:
# 				if this_fri.month == 12:
# 					dx_list[ii] = NY[1][ii].date()
# 				else:
# 					dx_list[ii] = TY[this_fri.month+1][ii].date()
# 			else:
# 				break
# 		## find and fill in DX dates after this friday
# 		for ii in range(len(dx_list)):
# 			if dx_list[ii] != 0:
# 				continue
# 			if TY[this_fri.month][ii] != 0:
# 				dx_list[ii] = TY[this_fri.month][ii].date()
# 			else:
# 				next_month = this_fri.month+1
# 				while True:
# 					if next_month <= 12:
# 						if TY[next_month][ii] != 0:
# 							dx_list[ii] = TY[next_month][ii].date()
# 							break
# 						next_month += 1
# 					else:
# 						if NY[next_month-12][ii] != 0:
# 							dx_list[ii] = NY[next_month-12][ii].date()
# 							break
# 						next_month += 1
# 		return TY,NY,dx_list


# def we():
# 	we =  weekly_exps()
# 	return we.TY, we.NY, we.dx_list


# parameters K is the strike so in the csv i sent you, the strike in the name is DX1H23C1575000_processed 15,750
# V is volatility, ill supply a 1 min timestamped csv with that price
# and S is price of the underlying, ill also provide a timestamped csv with that price
# needed function
# def option_delta2(flag, s, k, t, v, r=0.00):
#     '''
#     Parameters
#     ----------
#     flag : string
#             "C" for call or "P" for put
#     s : float
#             underlying price
#     k : float <> 100.00
#             Strike price of option
#     t : float <> 30/365
#             expirey of option in years
#     r : float <> 0.00
#             risk free rate
#     v : float <> 20%vol is .20
#             12 vol


#     option_delta("C", 97.65, 100.00, 30/365, 12, r=0.00)
#     Returns
#     -------
#     TYPE float
#             returns the delta of an option
#             0.27 is equal to 27 dollar units of the underlying
#             the return is used to calculate the delta hedge required to be neutral
#             IE 27*97.65 to be delta neutral .

#     '''
#     dl = (np.log(s/k)+(r+v*v/2)*t)/(v*np.sqrt(t))
#     if flag == "C":
#         return norm.cdf(dl)
#     else:
#         return norm.cdf(-dl)  # +signed put delta


# def delta2(flag, s, k, t, v, r=0.00):
#     d1 = (np.log(s/k)+(r+v*v/2)*t)/(v*np.sqrt(t))
#     s1 = s
#     if flag == "C":
#         d1 = norm.cdf(d1)
#     else:
#         d1 = norm.cdf(-d1)  # +signed put delta

#     d2 = (np.log((s+1)/k)+(r+v*v/2)*t)/(v*np.sqrt(t))
#     if flag == "C":
#         d2 = norm.cdf(d2)
#     else:
#         d2 = norm.cdf(-d2)

#     gg = d1*s1-d2*s1

#     gamma = (d1 - d2) / (s1 - s1+1)
#     # print("Delta1 = "+str(d1))
#     # print("Delta2 = "+str(d2))
#     # print("gamma = "+str(gamma))
#     # print("gg = "+str(gg))
#     return d1, gamma, gg


def create_new_resampled(processed_df, tf="5min"):
    df = processed_df
    df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)
    dflast = df.resample(tf).last()
    dfmulti = df.resample(tf).agg(
        {'Price': np.mean, 'Inc Vol': np.sum, 'Volume': np.sum, 'MM_balance': np.sum, 'Spread': np.mean})
    HR = dflast
    del HR['Time']
    del HR['Date']
    del HR['Inc Vol']
    del HR['MM_balance']
    del HR['Spread']
    del HR['Bid']
    del HR['Ask']
    # del HR['Bid2']
    # del HR['Ask2']
    del HR['Buy']
    del HR['Price']

    # del HR['B Size']
    # del HR['A Size']
    del HR['TickID']
    del HR['Info']
    del HR['Mkt Center']

    HR["Price Avg"] = dfmulti['Price']
    HR["Spread Avg"] = dfmulti['Spread']
    HR["MM_Contracts_added"] = dfmulti['MM_balance']
    gr = HR.dropna()
    gr1 = gr[['Volume', 'MM_Contracts_added', 'Running_MM_Contracts_balance',
              'cost_to_MM', 'Running_Cost sum', 'Price Avg', 'Spread Avg']]

    return gr1


def generate_blank_df(end_date, columns=None, frequency='5min', days_backwards=90):
    """
    Generate a blank pandas DataFrame with a datetime index in a specified format and additional columns.

    Parameters:
            end_date (datetime, required): A datetime to generate back from, EG  datetime.datetime(2023, 3, 31, 14, 0)
            columns (list, optional): A list of column names to add to the DataFrame. Default is ['col1'].
            frequency (str, optional): The frequency of the time intervals in the index. Default is '5min'.

    Returns:
            DataFrame: A blank pandas DataFrame with a datetime index and additional columns.
    """
    if columns is None:
        columns = ['col1']

    # Define the start and end dates for the index
    # end_date = datetime.datetime(2023, 3, 31, 14, 0)
    start_date = end_date - timedelta(days=days_backwards)

    # Create a date range with the specified frequency
    date_range = pd.date_range(end=end_date, start=start_date, freq=frequency)

    # Create a DataFrame with the date range as the index
    df = pd.DataFrame({'date_time': date_range})
    df.set_index('date_time', inplace=True)

    # Format the index as a string in the specified format
    df.index = df.index.strftime('%Y-%m-%d %H:%M:%S')
    df.index = df.index.astype('datetime64[ns]')
    # Add any additional columns with a value of None
    for col in columns:
        df[col] = None

    # Print the first few rows of the DataFrame and return it
    # print(df.head())
    return df


def fill_blank_df_with_data(blank_df, data_df):
    """
    Fill in a blank DataFrame with data from another DataFrame and forward fill down the DataFrame.

    Parameters:
        blank_df (DataFrame, required): A blank DataFrame generated by the generate_blank_df function.
        data_df (DataFrame, required): A DataFrame with data to fill in the blank DataFrame.

    Returns:
        DataFrame: A pandas DataFrame with the same index as the blank DataFrame and forward filled data from the data DataFrame.
    """
    # Select only the index values that are present in both DataFrames
    common_index = blank_df.index.intersection(data_df.index)

    # Fill in the common index values with the data
    blank_df.loc[common_index, :] = data_df.loc[common_index, :]

    # Forward fill down the DataFrame
    blank_df.fillna(method='ffill', inplace=True)

    return blank_df


def gen_and_fill(data_df, end_date):
    data_df.index = data_df.index.astype('datetime64[ns]')
    blank_df = generate_blank_df(
        end_date, columns=data_df.columns, frequency='5min')
    data_frame = fill_blank_df_with_data(blank_df, data_df)
    return data_frame


def prep_xg_fvs(FVS_csv_path, XG_csv_path, end_date):
    xg_df = pd.read_csv(XG_csv_path, names=['datetime', 'Date', 'Time', "Open", "High", "Low", 'Close', 'DayVol', 'Inc Vol', 'cond1'],
                        dtype={'Date': 'str', "DayVol": "float64", "Inc Vol": "float64"}, skiprows=1, index_col=0)
    fvs_df = pd.read_csv(FVS_csv_path, names=['datetime', 'Date', 'Time', "Open", "High", "Low", 'Close', 'DayVol', 'Inc Vol', 'cond1'],
                         dtype={'Date': 'str', "DayVol": "float64", "Inc Vol": "float64"}, skiprows=1, index_col=0)
    xg = gen_and_fill(xg_df, end_date)
    xg_prices = xg[['Close']]
    fvs = gen_and_fill(fvs_df, end_date)
    fvs_prices = fvs[['Close']]
    return xg_prices, fvs_prices


def delta3(end_date, df, xg_price_df, fvs_price_df):
    year_minutes = 365.25*24*60
    flag = "C"
    k = np.array([15000 for datte in df.index])
    r = np.array([0.0 for datte in df.index])
    s = xg_price_df['Close'].values
    v = fvs_price_df['Close'].values
    v = v/100
# t = np.array([(end_date - datte).days / 365.25 for datte in df.index])
    t = np.array([(end_date - datte).total_seconds() /
                 60 / year_minutes for datte in df.index])
    dl = np.array([(end_date - datte).days for datte in df.index])

    d1 = (np.log(s/k)+(r+v*v/2)*t)/(v*np.sqrt(t))
    if flag == "C":
        d1 = norm.cdf(d1)
    else:
        d1 = norm.cdf(-d1)  # +signed put delta

    d2 = (np.log((s+1)/k)+(r+v*v/2)*t)/(v*np.sqrt(t))
    if flag == "C":
        d2 = norm.cdf(d2)
    else:
        d2 = norm.cdf(-d2)  # +signed put delta

    gamma = (d1 - d2) / (s - s+1)
    gg = d1*s-d2*s
    delta2_values = pd.DataFrame({'Delta': d1, 'gamma': gamma, 'gg': gg, 'timeleft': t, 'datetime': df.index,
                                  "Days_left ": dl, "xg": xg_price_df["Close"], "FVS": fvs_price_df['Close']}, index=df.index)
    return delta2_values

# function to get all the folder names from the folder at a specified path
def getDirNames(rootdir):
    folderNames = []
    for file in os.listdir(rootdir):
        d = os.path.join(rootdir, file)
        if os.path.isdir(d):
            folderNames.append(file)
    return folderNames

# function to filter the _processed csv files from the folder
def filter_processed(path):
    file_list = []
    for (root, dirs, files) in os.walk(path, topdown=True):
        file_list.append(files)
    fff = list(itertools.chain(*file_list))
    res = []
    for f in fff:
        if "_processed" in f:
            res.append(f)
    return res


# path to the FVS and XG csv files
FVS_CSV_PATH = "./Data/FVS5min.csv"
XG_CSV_PATH = "./Data/XG5min.csv"
# the main function to calculate the delta given the path of the csv files and name of the files
def calculate_delta(file_path, file_name):
    option_df_processed = pd.read_csv(file_path)
    option_df_resampled = create_new_resampled(option_df_processed)
    option_name = file_name.split('_')[0]
    g = option(option_name, for_info=True)
    option_df = gen_and_fill(option_df_resampled, g.expiry_time)
    xg_prices, fvs_prices = prep_xg_fvs(
        FVS_CSV_PATH, XG_CSV_PATH, g.expiry_time)

    delta2_values = delta3(g.expiry_time, option_df, xg_prices, fvs_prices)
    delta2_values['Date'] = [d.date() for d in delta2_values['datetime']]
    delta2_values['Time'] = [d.time() for d in delta2_values['datetime']]
    df_concat = pd.concat([option_df, delta2_values], axis=1)
    df_concat[f"GEX_{g.option_type}"] = df_concat['Running_MM_Contracts_balance'] * df_concat['gg']
    df_concat['Strike'] = g.strike
    return df_concat



# method to get the calculated csv files, if not there, calculate them again
def get_calculated_csv_files(option_C_path, option_P_path, option_C_files, option_P_files):
    # try reading the calulated file, if not do the calculations
    try:
        calculated_C_data = pd.read_csv(
            option_C_path+"calculated_C_data.csv")
    except FileNotFoundError:
        calculated_C_data = pd.DataFrame()
        # calculations for option C files
        for option in option_C_files:
            rows_to_append = calculate_delta(option_C_path+option, option)
            calculated_C_data = pd.concat(
                [calculated_C_data, rows_to_append])

        calculated_C_data = calculated_C_data.reset_index(drop=True)
        calculated_C_data.to_csv(option_C_path+"calculated_C_data.csv")

    # try reading the calulated file, if not do the calculations
    try:
        calculated_P_data = pd.read_csv(
            option_P_path+"calculated_P_data.csv")
    except FileNotFoundError:
        calculated_P_data = pd.DataFrame()
        # calculations for option P files
        for option in option_P_files:
            rows_to_append = calculate_delta(option_P_path+option, option)
            calculated_P_data = pd.concat(
                [calculated_P_data, rows_to_append])
        calculated_P_data = calculated_P_data.reset_index(drop=True)
        calculated_P_data.to_csv(option_P_path+"calculated_P_data.csv")
    
    return calculated_C_data, calculated_P_data