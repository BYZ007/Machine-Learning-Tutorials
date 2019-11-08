from PyQt5 import QtWidgets,uic
import matplotlib.pyplot as plt
import sys
from PyQt5.QtCore import QAbstractTableModel, Qt, QStringListModel
import pandas as pd
import numpy as np
import seaborn as sns
import traceback
from PyQt5.QtWidgets import QCompleter
from datetime import timedelta
import ExtrusionCalculations as ext 
import os

app = QtWidgets.QApplication([])
window = uic.loadUi(r"C:\Users\zhang\Extrusion_app_V1.ui")
window.show()

def time_to_date(time):
    return str(time)[:10]

WO = pd.read_csv(r"C:\Users\zhang\DataFrameMain.csv")
WO['Production Date'] = pd.to_datetime(WO['Production Date'])
featuresWO = ['Machine','Order','Product Code','SerialNbr','Operator','Resins','Recipe','Paper Code']
for f in featuresWO:
    WO[f] = WO[f].astype(str)

NWO = pd.read_csv(r"C:\Users\zhang\DataFrameMod.csv")
featuresNWO =  ['Machine','Order','Product Code','Operator','Resins','Paper Code','Construction']
for f in featuresNWO:
    NWO[f] = NWO[f].astype(str)

def get_PC_list(model):
    model.setStringList(NWO['Product Code'].unique().tolist())
def get_paper_list(model):
    model.setStringList(NWO['Paper Code'].unique().tolist())
def get_Cons_list(model):
    model.setStringList(NWO['Construction'].unique().tolist())
def get_order_list(model):
    model.setStringList(NWO['Order'].unique().tolist())

PCcompleter = QCompleter()
PaperCompleter = QCompleter()
ConsCompleter = QCompleter()
OrderCompleter = QCompleter()
PCcompleter.setCaseSensitivity(False)
PaperCompleter.setCaseSensitivity(False)
ConsCompleter.setCaseSensitivity(False)
modelPC = QStringListModel()
modelPaper = QStringListModel()
modelCons = QStringListModel()
modelOrder = QStringListModel()
get_PC_list(modelPC)
get_paper_list(modelPaper)
get_Cons_list(modelCons)
get_order_list(modelOrder)
PCcompleter.setModel(modelPC)
PaperCompleter.setModel(modelPaper)
ConsCompleter.setModel(modelCons)
OrderCompleter.setModel(modelOrder)
window.GS_PCinput.setCompleter(PCcompleter)
window.ProductCodeKDE.setCompleter(PCcompleter)
window.GS_ConsInput.setCompleter(ConsCompleter)
window.GS_PCodeInput.setCompleter(PaperCompleter)
window.PaperCodeKDE.setCompleter(PaperCompleter)
window.KDECons.setCompleter(ConsCompleter)
window.GS_woinput.setCompleter(OrderCompleter)
window.ExtByRoll.setCompleter(OrderCompleter)

class pandasModel(QAbstractTableModel):   
    def __init__(self,data):
        super().__init__()
        self._data = data
    
    def rowCount(self, parent = None):
        return self._data.shape[0]
    
    def columnCount(self, parent = None):
        return self._data.shape[1]
    
    def data(self,index,role = Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(),index.column()])
        return None

    def headerData(self,col,orientation,role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None
# Extrusion Data/Plotting Page
window.ExtByRoll.setEnabled(False)

def ext_search_parameters():
    if window.ExtByRollCheck.isChecked():
        window.ExtByRoll.setEnabled(True)
        window.StartTime.setEnabled(False)
        window.EndTime.setEnabled(False)
        window.Machine_select.setEnabled(False)
        window.Web_width_input.setEnabled(False)

    else:
        window.ExtByRoll.setEnabled(False)
        window.StartTime.setEnabled(True)
        window.EndTime.setEnabled(True)
        window.Machine_select.setEnabled(True)
        window.Web_width_input.setEnabled(True)

def get_data_user_ext():
    try:
        if window.ExtByRollCheck.isChecked():
            Roll = window.ExtByRoll.text()
            DF = WO.loc[WO['Order']== (str(Roll))]
            web_width = float(DF['Web Width'].iloc[0])
            machine_number = DF['Machine'].iloc[0]
            start_time = (DF['Production Date'].min()-timedelta(hours=3)).strftime('%Y-%m-%d %H:%M') +':00'
            end_time = DF['Production Date'].max().strftime('%Y-%m-%d %H:%M') +':00'
                
        else:
            web_width = float(window.Web_width_input.text())
            machine_number = window.Machine_select.currentText()
            start_time = window.StartTime.dateTime().toString('yyyy-MM-dd hh:mm') +':00'
            end_time = window.EndTime.dateTime().toString('yyyy-MM-dd hh:mm') +':00'

        return ([start_time,end_time,machine_number,web_width])
    except Exception:
        window.Comments.setText(traceback.format_exc())


def gsm_plot():
    try:
        data = get_data_user_ext()
        plt.figure(figsize=(15,15), dpi =100)
        if data[2]!='151':
            gsm = ext.gsm_calc(data)
            gsm = ext.gsm_convert(gsm)
            hoppers = ['4.5 Total gsm','2.5 Total gsm','Total gsm']
            for i in range(0,len(hoppers)):
                plt.plot(gsm.Time, gsm[hoppers[i]],label = hoppers[i])
        else:
            gsm = ext.gsm_calc_151(data)
            gsm = ext.gsm_convert_151(gsm)
            plt.plot(gsm.Time, gsm['Total gsm'])

        plt.subplots_adjust(bottom=0.15, left = 0.07, right = 1, top = 0.96)
        plt.legend(loc=(0.91,0.91),fontsize = 8)
        plt.xlim(left =0)
        plt.xlabel('Time')
        plt.ylabel('gsm')
        plt.xticks(np.arange(0,len(gsm.Time),6),gsm.Time[0::6],rotation = 'vertical',fontsize = 8)
        plt.title('GSM Plot '+data[2]+'  ' +data[0]+'--'+data[1])
        plt.show()
        model = pandasModel(gsm)
        window.gsm_table.setModel(model)
        window.gsm_table.show()
        window.gsm_table.resizeColumnsToContents()
    except Exception:
        window.Comments.setText(traceback.format_exc())


def recipe_plot():
    try:
        data = get_data_user_ext()
        plt.figure(figsize=(15,10))
        if data[2] != '151':
            recipe = ext.recipe_calc(data)
            hoppers = ['4.5 HopperA resin %',
                    '4.5 HopperB resin %',
                    '4.5 HopperC resin %',
                    '2.5 HopperA resin %',
                    '2.5 HopperB resin %',
                    '2.5 HopperC resin %']
            for i in range(0,len(hoppers)):
                plt.plot(recipe.Time, recipe[hoppers[i]],label = hoppers[i])
        else:
            recipe = ext.recipe_calc_151(data)
            hoppers = ['4.5 HopperA resin %',
                    '4.5 HopperB resin %',
                    '4.5 HopperC resin %']
            for i in range(0,len(hoppers)):
                plt.plot(recipe.Time, recipe[hoppers[i]],label = hoppers[i])
        plt.subplots_adjust(bottom=0.15, left = 0.07, right = 0.95, top = 0.96)
        plt.xlim(left = 0,right = recipe.Time.max())
        plt.xlabel('Time')
        plt.ylabel('percentage')
        plt.yticks(np.arange(0,100,step = 5))
        plt.xticks(np.arange(0,len(recipe.Time),6),recipe.Time[0::6],rotation = 'vertical',fontsize = 8)
        plt.legend(loc=(0.91,0.87),fontsize = 8)
        plt.title('Recipe plot '+data[2]+'  ' +data[0]+'-'+data[1])
        plt.show()
        model = pandasModel(recipe)
        window.gsm_table.setModel(model)
        window.gsm_table.show()
        window.gsm_table.resizeColumnsToContents()
    except Exception:
        window.Comments.setText(traceback.format_exc())

window.ExtByRollCheck.stateChanged.connect(ext_search_parameters)

window.PlotGSMB.clicked.connect(gsm_plot)
window.PlotRecipeB.clicked.connect(recipe_plot)

# General Search Page
def get_GSCriteria():
    CList = []
    for item in window.CriteriaList.selectedItems():
        CList.append(item.text()[3::])
    return(CList)

def get_resinlist():
    RList = []
    for item in window.GS_ResinList.selectedItems():
        RList.append(item.text())
    return RList

window.GS_MachineSelect.setEnabled(False)
window.GS_ResinList.setEnabled(False)
window.GS_OperatorSelect.setEnabled(False)
window.GS_PCinput.setEnabled(False)
window.GS_woinput.setEnabled(False)
window.PDstart.setEnabled(False)
window.PDend.setEnabled(False)
window.ColSelectList.setEnabled(False)
window.GroupByList.setEnabled(False)
window.GS_PCodeInput.setEnabled(False)
window.GS_ConsInput.setEnabled(False)
window.GS_GroupSelect.setEnabled(False)

def colselect():
    if window.CS_check.isChecked():
        window.ColSelectList.setEnabled(True)
    else: 
        window.ColSelectList.setEnabled(False)
def groupby_check():
    if window.Sort_check.isChecked():
        window.GroupByList.setEnabled(True)
    else:
        window.GroupByList.setEnabled(False)

window.Sort_check.stateChanged.connect(groupby_check)
window.CS_check.stateChanged.connect(colselect)

def selection_boxes():
    Ostate = {'Machine':False,'Resin':False,'Operator':False,'Production Date':False,'Product Code':False,'Construction':False,'Paper Code':False,'Product Group':False}
    state = Ostate
    items = get_GSCriteria()
    if ('Order' in items) == True:
        window.GS_woinput.setEnabled(True)
        state = Ostate
    else: 
        for item in items:
            state[item] = True
        window.GS_woinput.setEnabled(False)
    window.GS_MachineSelect.setEnabled(state['Machine'])
    window.GS_OperatorSelect.setEnabled(state['Operator'])
    window.PDstart.setEnabled(state['Production Date'])
    window.PDend.setEnabled(state['Production Date'])
    window.GS_PCinput.setEnabled(state['Product Code'])
    window.GS_ResinList.setEnabled(state['Resin'])
    window.GS_PCodeInput.setEnabled(state['Paper Code'])
    window.GS_ConsInput.setEnabled(state['Construction'])
    window.GS_GroupSelect.setEnabled(state['Product Group'])

def selected():
    items = get_GSCriteria()
    if ('Order' in items) == True:
        return (['Order'])
    else:
        selections = []
        if ('Production Date' in items) ==True:
            selections.append('Production Date')
            items.remove('Production Date')
        for item in items:
            selections.append(item)
        if ('Resin' in items) == True:
            selections.remove('Resin')
            selections.append('Resin')
        return (selections)

def search_data(selection):
    GS_data = []
    if selection[0]=='Production Date':
        GS_data.append([window.PDstart.date().toString('yyyy-MM-dd'),window.PDend.date().toString('yyyy-MM-dd')])
    for item in selection:
        if item == 'Machine':
            GS_data.append(window.GS_MachineSelect.currentText())
        elif item == 'Operator':
            GS_data.append(window.GS_OperatorSelect.currentText())
        elif item == 'Product Code':
            GS_data.append(window.GS_PCinput.text().upper())
        elif item == 'Order':
            GS_data.append(window.GS_woinput.text())
        elif item == 'Construction':
            GS_data.append(window.GS_ConsInput.text())
        elif item == 'Product Group':
            GS_data.append(window.GS_GroupSelect.currentText())
        elif item == 'Paper Code':
            GS_data.append(window.GS_PCodeInput.text())
    if selection[-1] == 'Resin':
        GS_data.append(get_resinlist())
    return(GS_data)

def search():
    try:
        df = WO.copy()
        selection = selected()
        if len(selection) ==0:
            window.Comments.setText('Please Make a Selection')
            return None
        else:
            GS_data = search_data(selection)
            if selection[0]== 'Production Date':
                df = df[(df['Production Date']>= GS_data[0][0]) & (df['Production Date']<= GS_data[0][1])]
                del selection[0]
                del GS_data[0]

            if ('Resin' in selection) ==True:
                if window.ResinExcludeCheck.isChecked():
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df.drop(df.loc[df['check']==1].index)
                        df = df.drop(columns = ['check'])

                else:
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df[df['check']==1]
                        df = df.drop(columns = ['check'])
                        
                del selection[-1]
                del GS_data[-1]

            for i in range(0,len(GS_data)):
                df = df[df[selection[i]].str[0:len(GS_data[i])]== GS_data[i]]

            items = []
            if window.CS_check.isChecked():
                for item in window.ColSelectList.selectedItems():
                    items.append(item.text())
                if ('Historical Productivity' in items) == True:
                    items.remove('Historical Productivity')
                    items.append('Max Kg/Hr')
                    items.append('Min Kg/Hr')
                    items.append('Average Kg/Hr')
            Features = ['Paper Code','Paper Code 2','Paper Type','Poly Basis','Paper Basis','Resins','Recipe','OP Run Time','Setup Time','Maintenance Down Time','Total Production','Efficiency','SerialNbr','Max Kg/Hr','Min Kg/Hr','Average Kg/Hr','Web Width','Web Width 2','Coating GSM','Total Down Time','Over Coating','Product Group','Line Speed']
            droplist = list(set(Features) - set(items))
            df = df.drop(columns = droplist)

            if window.Sort_check.isChecked():
                s = window.GroupByList.currentText()
                df = df.sort_values(s)

            model = pandasModel(df)
            window.SearchTable.setModel(model)
            window.SearchTable.show()
            window.SearchTable.resizeColumnsToContents()
    except Exception:
        window.Comments.setText(traceback.format_exc())

# Build a Graph Tab
window.X_AxisBar.setEnabled(False)
window.X_AxisLine.setEnabled(False)
window.HueList.setEnabled(False)
window.YList.setEnabled(False)
window.PeroidSelect.setEnabled(False)
window.OperatorKDEList.setEnabled(False)
window.ProductCodeKDE.setEnabled(False)
window.PKDE_select.setEnabled(False)
window.KDECons.setEnabled(False)
window.PaperCodeKDE.setEnabled(False)
window.KDE_ResinList.setEnabled(False)
window.ValuesCheck.setEnabled(False)
window.KDEPgroup.setEnabled(False)

def parameters_active():
    try:
        plot_type = window.PlotTypeList.currentItem().text()
        if plot_type == 'Bar':
            window.X_AxisBar.setEnabled(True)
            window.YList.setEnabled(True)
            window.X_AxisLine.setEnabled(False)
            window.OperatorKDEList.setEnabled(False)
            window.peroidCheck.setEnabled(True)
            window.HueCheck.setEnabled(True)
            window.ProductCodeKDE.setEnabled(False)
            window.PKDE_select.setEnabled(False)
            window.KDECons.setEnabled(False)
            window.PaperCodeKDE.setEnabled(False)
            window.KDE_ResinList.setEnabled(False)
            window.ValuesCheck.setEnabled(True)
            window.KDEPgroup.setEnabled(False)

        elif plot_type == 'Operator KDE':
            window.OperatorKDEList.setEnabled(True)
            window.X_AxisBar.setEnabled(False)
            window.X_AxisLine.setEnabled(False)
            window.YList.setEnabled(True)
            window.HueCheck.setEnabled(False)
            window.peroidCheck.setEnabled(False)
            window.ProductCodeKDE.setEnabled(False)
            window.PKDE_select.setEnabled(False)
            window.KDECons.setEnabled(False)
            window.PaperCodeKDE.setEnabled(False)
            window.KDE_ResinList.setEnabled(False)
            window.ValuesCheck.setEnabled(False)
            window.KDEPgroup.setEnabled(False)

        elif plot_type == 'Line':
            window.OperatorKDEList.setEnabled(False)
            window.X_AxisLine.setEnabled(True)
            window.YList.setEnabled(True)
            window.X_AxisBar.setEnabled(False)
            window.peroidCheck.setEnabled(True)
            window.HueCheck.setEnabled(True)
            window.ProductCodeKDE.setEnabled(False)
            window.PKDE_select.setEnabled(False)
            window.KDECons.setEnabled(False)
            window.PaperCodeKDE.setEnabled(False)
            window.KDE_ResinList.setEnabled(False)
            window.ValuesCheck.setEnabled(False)
            window.KDEPgroup.setEnabled(False)

        elif plot_type == 'Product KDE':
            window.OperatorKDEList.setEnabled(False)
            window.YList.setEnabled(True)
            window.X_AxisBar.setEnabled(False)
            window.X_AxisLine.setEnabled(False)
            window.HueCheck.setEnabled(False)
            window.peroidCheck.setEnabled(False)
            window.PKDE_select.setEnabled(True)
            window.ValuesCheck.setEnabled(False)
            Ostate = {'Product Code':False,'Resins':False,'Paper Code':False,'Construction':False,'Product Group':False}
            for item in window.PKDE_select.selectedItems():
                Ostate[item.text()] = True
            window.ProductCodeKDE.setEnabled(Ostate['Product Code'])
            window.KDECons.setEnabled(Ostate['Construction'])
            window.PaperCodeKDE.setEnabled(Ostate['Paper Code'])
            window.KDE_ResinList.setEnabled(Ostate['Resins'])
            window.KDEPgroup.setEnabled(Ostate['Product Group'])

        else:
            window.X_AxisBar.setEnabled(False)
            window.X_AxisLine.setEnabled(False)
            window.YList.setEnabled(False)
            window.OperatorKDEList.setEnabled(False)
            window.HueCheck.setEnabled(False)
            window.peroidCheck.setEnabled(False)
            window.ProductCodeKDE.setEnabled(False)
            window.PKDE_select.setEnabled(False)
            window.KDECons.setEnabled(False)
            window.PaperCodeKDE.setEnabled(False)
            window.KDE_ResinList.setEnabled(False)
            window.ValuesCheck.setEnabled(False)
            window.KDEPgroup.setEnabled(False)

        if window.HueCheck.isChecked():
            window.HueList.setEnabled(True)
        else: 
            window.HueList.setEnabled(False)

        if window.peroidCheck.isChecked():
            window.PeroidSelect.setEnabled(True)
            window.X_AxisBar.setEnabled(False)
            window.X_AxisLine.setEnabled(False)
            window.YList.setEnabled(True)
            window.OperatorKDEList.setEnabled(False)
            window.PKDE_select.setEnabled(False)
            window.KDECons.setEnabled(False)
            window.PaperCodeKDE.setEnabled(False)
            window.KDE_ResinList.setEnabled(False)
            window.KDEPgroup.setEnabled(False)

        else:
            window.PeroidSelect.setEnabled(False)
            
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

def mean(series):
    return series.mean()
def monthly(time):
    return str(time)[:7]

def to_hours(time):
    return time/pd.Timedelta(hours=1)

def Build_a_graph():
    try:
        df = NWO.copy()
        selection = selected()
        if len(selection) ==0:
            window.Comments.setText('Please Make a Selection')
            return None
        else:
            GS_data = search_data(selection)
            if selection[0]== 'Production Date':
                df = df[(df['Production Date']>= GS_data[0][0]) & (df['Production Date']<= GS_data[0][1])]
                del selection[0]
                del GS_data[0]

            if ('Resin' in selection) ==True:
                if window.ResinExcludeCheck.isChecked():
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df.drop(df.loc[df['check']==1].index)
                        df = df.drop(columns = ['check'])

                else:
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df[df['check']==1]
                        df = df.drop(columns = ['check'])
                        
                del selection[-1]
                del GS_data[-1]

            for i in range(0,len(GS_data)):
                df = df[df[selection[i]].str[0:len(GS_data[i])]== GS_data[i]]

            plot_type = window.PlotTypeList.currentItem().text()
            sns.set_style("whitegrid")
                
            if plot_type == 'Bar':
                x = window.X_AxisBar.currentItem().text()
            elif plot_type =='Line':
                x = window.X_AxisLine.currentItem().text()

            y = window.YList.currentItem().text()

            hue = None
            if window.HueCheck.isChecked():           
                hue = window.HueList.currentItem().text()
                if y == 'Run Time':
                    df = pd.DataFrame(df.groupby([x,hue], sort = False)['Run Time'].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)

                elif (y in ['Efficiency','Kg/Hr','Over Coating','Line Speed','Total Down Time','Estimated Line Speed'])== True:
                    total_time = dict(df.groupby([x,hue], sort = False)['Run Time'].sum())
                    def div_totalT(df):
                        T = total_time[(df[x],df[hue])]
                        return (df['Run Time']/T)
                    df['Run Time'] = df.apply(div_totalT, axis = 1)
                    df[y] = df[y].multiply(df['Run Time'])
                    df = pd.DataFrame(df.groupby([x,hue], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)
                elif y =='Average Order Size':
                    y='Qty'
                    df = pd.DataFrame(df.groupby(['Order',x],sort = False)['Qty'].sum()).reset_index()
                    df = pd.DataFrame(df.groupby([x],sort = False)['Qty'].mean()).reset_index()

                else:
                    df = pd.DataFrame(df.groupby([x,hue], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)

            else:
                if (y in ['Efficiency','Kg/Hr','Over Coating','Line Speed','Total Down Time','Estimated Line Speed'])== True:
                    total_time = dict(df.groupby([x], sort = False)['Run Time'].sum())
                    def div_totalT(df):
                        T = total_time[df[x]]
                        return (df['Run Time']/T)
                    df['Run Time'] = df.apply(div_totalT,axis = 1)
                    df[y] = df[y].multiply(df['Run Time'])
                    df = pd.DataFrame(df.groupby([x], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)
                
                elif y =='Average Order Size':
                    y = 'Qty'
                    df = pd.DataFrame(df.groupby(['Order',x],sort = False)['Qty'].sum()).reset_index()
                    df = pd.DataFrame(df.groupby([x],sort = False)['Qty'].mean()).reset_index()

                elif y =='Run Time':
                    df = pd.DataFrame(df.groupby(x, sort = False)['Run Time'].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)

                else:
                    df = pd.DataFrame(df.groupby(x, sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)

            if plot_type == 'Bar':
                palette=("Paired")
                P=sns.barplot(x,y,hue = hue, data = df,ci=None,palette = palette)
                if window.ValuesCheck.isChecked():
                    for i in range(0,len(P.patches)):
                        P.annotate("%.2f" % P.patches[i].get_height(), (P.patches[i].get_x() + P.patches[i].get_width() / 2., P.patches[i].get_height()),ha='center', va='center', fontsize=8, color='black', xytext=(0, 10),textcoords='offset points')
                plt.legend(loc=(1,0.4),fontsize = 8)

            elif plot_type == 'Line':
                sns.lmplot(x,y, hue = hue, data = df,ci=0.9, fit_reg = True, x_bins = 20,order = 1)
                plt.xlim(left = 0)

            R = '1'
            for i in range(0,len(str(int(df[y].max())))-1):
                R+='0'

            plt.subplots_adjust(bottom=0.15, left = 0.05, right = 0.9, top = 0.95)
            plt.ylim(top = df[y].max()+(int(R)/10))
            plt.yticks(np.arange(0,df[y].max()+(int(R)/10),step = (int(R)/10)), fontsize = 8)
            plt.ylabel(y, fontsize = 8)
            plt.xlabel(x, fontsize = 8)
            plt.title (y + ' Graph By '+x, fontsize = 14)
            plt.xticks(rotation = 'vertical',fontsize = 8)
            plt.show()
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

def peroid_plots():
    try:
        df = NWO.copy()
        selection = selected()
        if len(selection) ==0:
            window.Comments.setText('Please Make a Selection')
            return None
        else:
            GS_data = search_data(selection)
            if selection[0]== 'Production Date':
                df = df[(df['Production Date']>= GS_data[0][0]) & (df['Production Date']<= GS_data[0][1])]
                del selection[0]
                del GS_data[0]

            if ('Resin' in selection) ==True:
                if window.ResinExcludeCheck.isChecked():
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df.drop(df.loc[df['check']==1].index)
                        df = df.drop(columns = ['check'])

                else:
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df[df['check']==1]
                        df = df.drop(columns = ['check'])
                        
                del selection[-1]
                del GS_data[-1]

            for i in range(0,len(GS_data)):
                df = df[df[selection[i]].str[0:len(GS_data[i])]== GS_data[i]]

            peroid = window.PeroidSelect.currentText()
            plot_type = window.PlotTypeList.currentItem().text()
            sns.set(style='whitegrid')
            y = window.YList.currentItem().text()
            plt.subplots_adjust(bottom=0.15, left = 0.05, right = 0.9, top = 0.95)

            hue = None
            if peroid == 'Monthly':
                df['Production Date'] = df['Production Date'].apply(monthly)
                    
            if window.HueCheck.isChecked():
                hue = window.HueList.currentItem().text()
                total_time = df.groupby(['Production Date',hue], sort = False)['Run Time'].sum()    
                if y == 'Run Time':
                    df = total_time.reset_index()
                    df = df.drop(df.loc[df[y]==0].index)
                elif (y in ['Efficiency','Kg/Hr','Over Coating','Line Speed','Total Down Time','Estimated Line Speed'])== True:
                    total_time = dict(total_time)
                    def div_totalT(df):
                        T = total_time[(df['Production Date'],df[hue])]
                        return (df['Run Time']/T)
                    df['Run Time'] = df.apply(div_totalT, axis = 1)
                    df[y] = df[y].multiply(df['Run Time'])
                    df = pd.DataFrame(df.groupby(['Production Date',hue], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)
                elif y =='Average Order Size':
                    y = 'Qty'
                    df = pd.DataFrame(df.groupby(['Order','Production Date'],sort = False)['Qty'].sum()).reset_index()
                    df = pd.DataFrame(df.groupby(['Production Date'],sort = False)['Qty'].mean()).reset_index()
                else:
                    df = pd.DataFrame(df.groupby(['Production Date',hue], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)
                palette=("Paired")
            else:
                total_time = df.groupby(['Production Date'], sort = False)['Run Time'].sum()    
                if y == 'Run Time':
                    df = total_time.reset_index()
                    df = df.drop(df.loc[df[y]==0].index)

                elif (y in ['Efficiency','Kg/Hr','Over Coating','Line Speed','Total Down Time','Estimated Line Speed'])== True:
                    total_time = dict(total_time)
                    def div_totalT(df):
                        T = total_time[df['Production Date']]
                        return (df['Run Time']/T)
                    df['Run Time'] = df.apply(div_totalT, axis = 1)
                    df[y] = df[y].multiply(df['Run Time'])
                    df = pd.DataFrame(df.groupby(['Production Date'], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)
                elif y =='Average Order Size':
                    y = 'Qty'
                    df = pd.DataFrame(df.groupby(['Order','Production Date'],sort = False)['Qty'].sum()).reset_index()
                    df = pd.DataFrame(df.groupby(['Production Date'],sort = False)['Qty'].mean()).reset_index()
                else:
                    df = pd.DataFrame(df.groupby(['Production Date'], sort = False)[y].sum()).reset_index()
                    df = df.drop(df.loc[df[y]==0].index)

                palette=sns.cubehelix_palette(12)
            df = df.sort_values(by=['Production Date'],ascending=True)
            if plot_type == 'Bar':
                P = sns.barplot('Production Date',y,data = df,hue = hue,ci=None,palette=palette)
                if window.ValuesCheck.isChecked():
                    for p in P.patches:
                        P.annotate("%.2f" % p.get_height(), (p.get_x() + p.get_width() / 2., p.get_height()),ha='center', va='center', fontsize=8, color='black', xytext=(0,10),textcoords='offset points')
                plt.legend(loc=(1,0.4),fontsize = 8)

            else:
                P=sns.lineplot('Production Date',y,data = df,hue = hue,ci=None,palette=palette)
                plt.xlim(left = 0)

            R = '1'
            for i in range(0,len(str(int(df[y].max())))-1):
                R+='0'
            plt.yticks(np.arange(0,df[y].max()+(int(R)/10),step = (int(R)/10)), fontsize = 8)
            plt.ylabel(y, fontsize = 8)
            plt.xlabel('By '+peroid,fontsize = 8)
            plt.title(peroid +' '+ y, fontsize = 14)
            plt.xticks(rotation = 'vertical', fontsize = 8)
            plt.show()
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

def Preport():
    try:
        df = WO.copy()
        selection = selected()
        if len(selection) == 0:
            return None
        else:
            GS_data = search_data(selection)
            if selection[0]== 'Production Date':
                window.FilePath.setText(window.GS_MachineSelect.currentText()+'_'+str(GS_data[0][0])+'_to_'+str(GS_data[0][1]))
                df = df[(df['Production Date']>= GS_data[0][0]) & (df['Production Date']<= GS_data[0][1])]
                del selection[0]
                del GS_data[0]

            if ('Resin' in selection) ==True:
                if window.ResinExcludeCheck.isChecked():
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df.drop(df.loc[df['check']==1].index)
                        df = df.drop(columns = ['check'])

                else:
                    for r in GS_data[-1]:
                        df['check'] = df['Resins'].apply(lambda x: 1 if (r in x)==True else 0)
                        df = df[df['check']==1]
                        df = df.drop(columns = ['check'])
                        
                del selection[-1]
                del GS_data[-1]


            for i in range(0,len(GS_data)):
                df = df[df[selection[i]]== GS_data[i]]
        try:
            n = int(window.ReportCriteria.text())
            df = df.drop(df[df['Total Production']<n].index)
        except:
            pass

        df['Production Date']=df['Production Date'].apply(lambda x: str(x)[:10])

        Rparam = window.ReportParameter.currentText()
        Range = window.ReportRange.currentText()
        dfr = pd.DataFrame(df.groupby(['Order','Product Code'], sort = False)[Rparam,'Run Time'].mean()).reset_index()
        dfr = dfr.dropna(axis = 0)
        dfr['Check'] = dfr.apply(lambda x: 1 if ('T' in list(x['Product Code'][10::])) == True else 0, axis = 1)
        dfr = dfr.loc[dfr['Check']==0]
        dfr = dfr.drop(columns = ['Check'])

        comments_dict = {0:window.Comments1,1:window.Comments2,2:window.Comments3,3:window.Comments4,
        4:window.Comments5,5:window.Comments6,6:window.Comments7,7:window.Comments8,8:window.Comments9,9:window.Comments10}
        month = window.FilePath.text()
        print(month)
        parameter = window.ReportParameter.currentText()
        if parameter =='Kg/Hr':
            parameter = 'Kgs'

        file_exists = True
        try:
            path = r'C:\Users\zhang\Documents\{}.txt'.format(month)
            file = open(path,'r')

            comment = []
            for line in file.readlines():
                comment.append(line)
        except:
            file_exists = False
        print(path)
        totalTime = dict(dfr.groupby(['Order'], sort = False)['Run Time'].sum())
        def div_totalT(dfr):
            T = totalTime[dfr['Order']]
            return dfr['Run Time']/T
        dfr['Run Time'] = dfr.apply(div_totalT,axis = 1)
        dfr[Rparam] = dfr[Rparam].multiply(dfr['Run Time'])
        dfr = pd.DataFrame(dfr.groupby(['Order'], sort = False)[Rparam].sum()).reset_index()         
        dfr = dfr.sort_values(Rparam, ascending = 1)
        dfr = dfr.iloc[0:int(Range[7::]),0].tolist()

        if not file_exists:
            for i in range(int(Range[7:])):
                comments_dict[i].setText(dfr[i]+': ')
                
        df1 = df.loc[df['Order']==dfr[0]]
        df1['Production Date'] = str(df[df['Order']==dfr[0]]['Production Date'].tolist()[0])[:10]
        df1 = df1.groupby(['Order','Product Code','Production Date'])['Kg/Hr','Average Kg/Hr',
            'Efficiency','Line Speed','Run Time','Total Production'].mean().reset_index()
        if file_exists:
            try:
                comments_dict[0].setText(comment[0])
            except Exception:
                window.Graph_Comments.setText(traceback.format_exc())                
        for i in range(1,len(dfr)):
            df2 = df.loc[df['Order']==dfr[i]]
            df2['Production Date'] = str(df[df['Order']==dfr[i]]['Production Date'].tolist()[0])[:10]
            df2 = df2.groupby(['Order','Product Code','Production Date'])['Kg/Hr','Average Kg/Hr',
            'Efficiency','Line Speed','Run Time','Total Production'].mean().reset_index()
            df1 = pd.concat([df1,df2],axis = 0)
            if file_exists:
                try:
                    comments_dict[i].setText(comment[i])
                except Exception:
                    window.Graph_Comments.setText(traceback.format_exc())

        df1['Average Kg/Hr']=df1['Average Kg/Hr'].apply(lambda x: round(x,2))
        model = pandasModel(df1)
        window.ReportTable.setModel(model)
        window.ReportTable.show()
        window.ReportTable.resizeColumnsToContents()


        return df1
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

def saveReport():
    try:
        comments_dict = {0:window.Comments1,1:window.Comments2,2:window.Comments3,3:window.Comments4,
        4:window.Comments5,5:window.Comments6,6:window.Comments7,7:window.Comments8,8:window.Comments9,9:window.Comments10}
        month = window.FilePath.text()
        path = month+'.txt'
        Rfile = open(path,'w+')
        for i in range(10):
            Rfile.write(comments_dict[i].toPlainText())
            Rfile.write('\n')
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

window.ReportSave.clicked.connect(saveReport)

def operator_kde():
    try:
        operators = []
        plt.figure(figsize=(15,10), dpi =100)
        plt.subplots_adjust(bottom=0.1, left = 0.05, right = 0.94, top = 0.95)
        for item in window.OperatorKDEList.selectedItems():
            operators.append(item.text())
        y = window.YList.currentItem().text()

        for x in operators:
            df = WO[WO['Operator']==x]
            if (y in ['Efficiency','Kg/Hr','Line Speed','Total Down Time','Estimated Line Speed'])== True:
                df = pd.DataFrame(df.groupby(['Order'], sort = False)[y].mean())
            elif y =='Setup Time':
                df = df.drop(df.loc[df['Setup Time']==0].index)
                df = pd.DataFrame(df.groupby(['Order'], sort = False)[y].mean())
            elif y == 'Run Time':
                df = pd.DataFrame(df.groupby(['Order'], sort = False)['OP Run Time'].mean())
                df = df.rename(columns = {'OP Run Time':'Run Time'})
            else:
                df = pd.DataFrame(df.groupby(['Order'], sort = False)[y].sum())
            sns.kdeplot(df[y],label = x,clip=(0, df[y].max()))
        plt.xlim(left = 0)
        plt.xlabel(y +' KDE',fontsize = 12)
        plt.show()
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

def product_kde():
    try:
        KDE = []
        df = WO.copy()
        for item in window.PKDE_select.selectedItems():
            KDE.append(item.text())
        if ('Product Code' in KDE) ==True:
            df = df[df['Product Code']==window.ProductCodeKDE.text()]
        else:
            if ('Resins' in KDE) == True:
                for item in window.KDE_ResinList.selectedItems():                   
                    df['check'] = df['Resins'].apply(lambda x: 1 if (item.text() in x)==True else 0)
                    df = df[df['check']==1]
                df = df.drop(columns = ['check'])
            if ('Paper Code' in KDE)==True:
                df = df[df['Paper Code']==window.PaperCodeKDE.text()]
            if ('Construction' in KDE)==True:
                df = df[df['Construction']==window.KDECons.text()]
            if ('Product Group' in KDE)==True:
                df = df[df['Product Group']==window.KDEPgroup.currentText()]
        plt.subplots_adjust(bottom=0.1, left = 0.05, right = 0.94, top = 0.95)
        y = window.YList.currentItem().text()
        if len(df['Order'].unique())<=3:
            window.Graph_Comments.setText('Sample Size is too small, graph may not be representitive')
        if y =='Setup Time':
            df = df.drop(df.loc[df['Setup Time']==0].index)
        elif y == 'Qty':
            df = pd.DataFrame(df.groupby('Order',sort = False)[y].sum())
        elif (y in ['Efficiency','Kg/Hr', 'Run Time','Total Down Time','Over Coating','Estimated Line Speed'])==True:
            df = pd.DataFrame(df.groupby('Order',sort = False)[y].mean())

        sns.kdeplot(df[y],shade = True,clip=(0, df[y].max()))
        plt.xlim(left = 0)
        plt.xlabel(y +' KDE',fontsize = 12)
        plt.show()
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())

window.CriteriaList.itemSelectionChanged.connect(selection_boxes)
window.GS_SearchB.clicked.connect(search)
window.HueCheck.stateChanged.connect(parameters_active)
window.PKDE_select.itemSelectionChanged.connect(parameters_active)
window.peroidCheck.stateChanged.connect(parameters_active)
window.PlotTypeList.itemSelectionChanged.connect(parameters_active)
window.ReportB.clicked.connect(Preport)

def report_plot():
    try:
        DF_Report = Preport()
        df = pd.DataFrame(DF_Report.groupby('Product Code',sort = False)['Kg/Hr','Run Time','Total Production','Efficiency'].mean())
        df['Kg/Hr'] = df['Kg/Hr']/1000
        df['Total Production'] = df['Total Production']/1000
        df['Efficiency'] = df['Efficiency']/100
        df = df.rename(columns = {'Total Production': 'Total Production (1000 kgs)','Kg/Hr':'Kg/Hr (1000 Kgs)','Run Time':'Run Time (Hrs)'})
        P = df.plot(kind = 'bar')
        for p in P.patches:
            P.annotate("%.2f" % p.get_height(), (p.get_x() + p.get_width() / 2., p.get_height()),ha='center', va='center', fontsize=8, color='black', xytext=(0,10),textcoords='offset points')
        plt.subplots_adjust(bottom=0.15, left = 0.05, right = 0.96, top = 0.95)
        plt.show()
    except Exception:
        window.Graph_Comments.setText(traceback.format_exc())
window.ReportPlotB.clicked.connect(report_plot)

def build():
    if window.peroidCheck.isChecked():
        peroid_plots()
    elif window.PlotTypeList.currentItem().text() == 'Operator KDE':
        operator_kde()
    elif window.PlotTypeList.currentItem().text() == 'Product KDE':
        product_kde()
    else:
        Build_a_graph()

window.BuildGraphB.clicked.connect(build)

app.exec_()