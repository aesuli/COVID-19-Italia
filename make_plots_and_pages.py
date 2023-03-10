# COVID-19 data visualization
# Copyright (C) 2020 Andrea Esuli <andrea@esuli.it>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import datetime
import os
import re
import sys

import numpy as np
import pandas as pd
from bokeh.io import save
from bokeh.layouts import gridplot, layout
from bokeh.models import ColumnDataSource, NumeralTickFormatter, DatetimeTickFormatter, DataRange1d, Legend, LegendItem, \
    Column
from bokeh.models.tools import HoverTool
from bokeh.palettes import Category10_10, Category20_20
from bokeh.plotting import figure, output_file
from bokeh.transform import dodge

os.makedirs('./plots', exist_ok=True)
os.makedirs('./pages', exist_ok=True)

update = datetime.datetime.now()

root = '/COVID-19-Italia/'


def include(outputfile, filename, count=1):
    print('{% raw %}', file=outputfile)
    print(
        f'<iframe src="{root}{filename}" width="100%" sandbox="allow-same-origin allow-scripts" height="{int(320 * count + 20)}" scrolling="no" seamless="seamless" frameborder="0"></iframe>',
        file=outputfile)
    print('{% endraw %}', file=outputfile)
    print('', file=outputfile)
    print(
        f'[Mostra a schermo intero]({root}{filename})',
        file=outputfile)
    print('', file=outputfile)


footer = f'''
---

Ultimo aggiornamento: {update}

Fonte dati COVID-19 mondo: [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19) - [DASHBOARD](https://gisanddata.maps.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6)

Fonte dati COVID-19 Italia: [Presidenza del Consiglio dei Ministri - Dipartimento della Protezione Civile](https://github.com/pcm-dpc/COVID-19) - [DASHBOARD](http://opendatadpc.maps.arcgis.com/apps/opsdashboard/index.html#/b0c68bce2cce478eaac82fe38d4138b1)

Fonte dati Vaccinazione Italia: [Developers Italia - Commissario straordinario per l'emergenza Covid-19](https://github.com/italia/covid19-opendata-vaccini) - [DASHBOARD](https://www.governo.it/it/cscovid19/report-vaccini/)

Fonte dati età popolazione Italia: [ISTAT](http://dati.istat.it//Index.aspx?QueryId=49876)

[**Simulatore di quarantena**](https://aesuli.github.io/lockdownsimulator/index_it.html) - [**Lockdown simulator**](https://aesuli.github.io/lockdownsimulator/index.html)


[Home sito](https://aesuli.github.io/COVID-19-Italia/)

[Github repo](https://github.com/aesuli/COVID-19-Italia)

Licenza codice: [GPL-v3](https://www.gnu.org/licenses/gpl-3.0.txt)

Licenza grafici: [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.en)
'''


def plot_compare_countries(df, outputfile, plot_top=10, logplot=False, dataname='N/A', daily=False):
    print('\t', dataname)
    counts = df.groupby('Country/Region').sum()[df.columns[4:]].T
    to_plot = list(counts.T[df.columns[-1]].sort_values(ascending=False).head(plot_top).index)
    args = list()
    if daily:
        args.append('daily')
        counts[1:] -= counts.values[:-1]
        counts[counts < 0] = 0
        counts = counts.rolling(7, win_type='boxcar').mean()
    else:
        args.append('cumulative')
    if logplot:
        counts = np.log10(counts[to_plot] + 1)
        args.append('log10')
    filename = f'plots/world_{dataname}_{"_".join(args)}.html'

    include(outputfile, filename)

    output_file(filename)
    p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
               y_range=DataRange1d(only_visible=True))
    p.tools.append(HoverTool(tooltips=[("Country", "@country"),
                                       ('Date', '@date{%F}'),
                                       ("Value", "@value")],
                             formatters={'@date': 'datetime'}))
    legend = Legend()
    legend.click_policy = 'hide'
    for i, nation in enumerate(to_plot):
        ds = ColumnDataSource()
        ds.data['value'] = counts[nation]
        ds.data['date'] = pd.to_datetime(counts.index)
        ds.data['country'] = [nation] * len(ds.data['date'])
        e1 = p.line(source=ds, x='date', y='value', name=nation, color=Category20_20[i], line_width=2)
        e2 = p.circle(source=ds, x='date', y='value', color=Category20_20[i])
        legend.items.append(LegendItem(label=nation, renderers=[e1, e2]))

    if 'daily' in args:
        args.remove('daily')
        args.append('daily (7-day avg)')
    p.title.text = f'World {dataname} ({", ".join(args)})'
    p.add_layout(legend, 'right')
    p.yaxis.formatter = NumeralTickFormatter(format='0')
    p.xaxis.formatter = DatetimeTickFormatter()
    p.xaxis.ticker.desired_num_ticks = 20

    save(p)


if sys.argv[-1] != 'i':
    print('world')

    plot_top = 20

    with open('pages/world.md', mode='wt', encoding='utf-8') as worldfile:
        world_data = dict()
        world_data['confirmed'] = pd.read_csv(
            'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
        world_data['dead'] = pd.read_csv(
            'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')

        print('<a name="main"></a>', file=worldfile)
        print(f'# Visualizzazione dei dati giornalieri su COVID-19: Mondo - [Dati Italia]({root})', file=worldfile)

        print('Ogni visualizzazione include le dieci nazioni con il valore dell\'ultimo rilevamento più alto.',
              file=worldfile)

        print(' * [Casi totali](#cumul)', file=worldfile)
        print(' * [Casi del giorno](#daily)', file=worldfile)
        print('', file=worldfile)
        print('---', file=worldfile)
        print('', file=worldfile)
        print('<a name="cumul"></a>', file=worldfile)
        print('## Casi totali', file=worldfile)

        for dataname in world_data:
            plot_compare_countries(world_data[dataname], worldfile, plot_top=plot_top, dataname=dataname)

        print('[Indietro](#main)', file=worldfile)
        print('', file=worldfile)
        print('---', file=worldfile)
        print('', file=worldfile)
        print('<a name="daily"></a>', file=worldfile)
        print('## Casi del giorno', file=worldfile)

        for dataname in world_data:
            plot_compare_countries(world_data[dataname], worldfile, plot_top=plot_top, dataname=dataname, daily=True)

        print('[Indietro](#main)', file=worldfile)

        print(footer, file=worldfile)

if sys.argv[-1] != 'w':
    print('italia')

    ita_reg_data = pd.read_csv(
        'https://github.com/pcm-dpc/COVID-19/raw/master/dati-regioni/dpc-covid19-ita-regioni.csv')
    ita_prov_data = pd.read_csv(
        'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province.csv')

    ita_vax_data = pd.read_csv(
        'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv')

    ita_vax_data_consegne = pd.read_csv(
        'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/consegne-vaccini-latest.csv')

    ita_pop = pd.read_csv('popolazione_italia_2020.csv')

    ita_reg_data['data'] = ita_reg_data['data'].apply(lambda x: x[:10])
    ita_prov_data['data'] = ita_prov_data['data'].apply(lambda x: x[:10])

    regioni = sorted(set(ita_reg_data['denominazione_regione']))

    linestyles = list()
    for i in range(len(set(ita_reg_data['denominazione_regione']))):
        if i < 10:
            linestyles.append('-')
        elif i < 20:
            linestyles.append('--')
        else:
            linestyles.append('+-')

    with open('index.md', mode='wt', encoding='utf-8') as italiafile:
        etichette = ['terapia_intensiva', 'totale_ospedalizzati', 'isolamento_domiciliare',
                     'totale_positivi', 'nuovi_positivi', 'dimessi_guariti', 'deceduti',
                     'totale_casi', 'tamponi']

        print('<a name="main"></a>', file=italiafile)
        print('# Visualizzazione dei dati giornalieri su COVID-19: Italia - [Dati Mondo](/pages/world.md)',
              file=italiafile)

        print(' * [Malati/Guariti/Decessi](#cumul)', file=italiafile)
        print(' * [Vaccinazioni](#vax)', file=italiafile)
        print(' * [Tamponi](#postam)', file=italiafile)
        print(' * [Link a pagine delle Regioni e Province](#province)', file=italiafile)
        print(' * [Altri dati di confronto tra regioni](#regioni)', file=italiafile)
        print('', file=italiafile)
        print('---', file=italiafile)
        print('', file=italiafile)

        print('<a name="cumul"></a>', file=italiafile)
        print('## Malati/Guariti/Decessi', file=italiafile)

        values = ['terapia_intensiva', 'ricoverati_con_sintomi', 'isolamento_domiciliare', 'dimessi_guariti',
                  'deceduti', 'nuovi_positivi', 'tamponi']
        values_to_plot = ['terapia_intensiva', 'ricoverati_con_sintomi', 'isolamento_domiciliare', 'dimessi_guariti',
                          'deceduti']
        to_positive = ['terapia_intensiva', 'ricoverati_con_sintomi', 'isolamento_domiciliare']
        to_negative = ['deceduti', 'dimessi_guariti']

        filename = f'plots/Italia.html'
        include(italiafile, filename, 2)
        print('[Indietro](#main)', file=italiafile)
        output_file(filename)
        p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                   y_range=DataRange1d(only_visible=True))
        p.tools.append(HoverTool(tooltips=[("Tipo", "$name"),
                                           ('Data', '@date{%F}'),
                                           ("Valore", "@$name")],
                                 formatters={'@date': 'datetime'}))

        cumul = ita_reg_data.pivot_table(index=['data'],
                                         values=values,
                                         aggfunc='sum')
        for to_neg in to_negative:
            cumul[to_neg] = -cumul[to_neg]

        legend = Legend()
        legend.click_policy = 'hide'
        ds = ColumnDataSource()
        ds.data['date'] = pd.to_datetime(cumul.index)
        for value in values:
            ds.data[value] = cumul[value]
        e1s = p.varea_stack(stackers=to_positive, x='date', color=Category10_10[:len(to_positive)],
                            source=ds)
        e2s = p.vline_stack(stackers=to_positive, x='date', color=Category10_10[:len(to_positive)],
                            source=ds)
        for l, e1, e2 in zip(to_positive, e1s, e2s):
            legend.items.append(LegendItem(label=l, renderers=[e1, e2]))
        legend.items.reverse()
        e1s = p.varea_stack(stackers=to_negative, x='date',
                            color=Category10_10[len(to_positive):][:len(to_negative)], source=ds)
        e2s = p.vline_stack(stackers=to_negative, x='date',
                            color=Category10_10[len(to_positive):][:len(to_negative)], source=ds)
        for l, e1, e2 in zip(to_negative, e1s, e2s):
            legend.items.append(LegendItem(label=l, renderers=[e1, e2]))
        p.title.text = f'Ripartizione casi in Italia (cumulativo)'
        p.add_layout(legend, 'right')
        p.yaxis.formatter = NumeralTickFormatter(format='0')
        p.xaxis.formatter = DatetimeTickFormatter()
        p.xaxis.ticker.desired_num_ticks = 20

        p2 = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                    y_range=DataRange1d(only_visible=True))
        p2.tools.append(HoverTool(tooltips=[("Tipo", "$name"),
                                            ('Data', '@date{%F}'),
                                            ("Valore", "@$name")],
                                  formatters={'@date': 'datetime'}))

        daily = cumul[1:] - cumul.values[:-1]
        daily[daily[to_positive] < 0] = 0
        daily[daily[to_negative] > 0] = 0
        daily = daily.rolling(7, win_type='boxcar', min_periods=1).mean()

        legend = Legend()
        ds = ColumnDataSource()
        ds.data['date'] = pd.to_datetime(daily.index)
        for value in values:
            ds.data[value] = daily[value]
        cumul[cumul['nuovi_positivi'] < 0] = 0
        ds.data['nuovi_positivi'] = cumul['nuovi_positivi'][1:].rolling(7, win_type='boxcar').mean()
        e1 = p2.vbar(top='nuovi_positivi', x='date', source=ds, width=datetime.timedelta(days=1) * .8,
                     color=Category10_10[len(to_positive) + len(to_negative):][3], name='nuovi_positivi')
        legend_entry = LegendItem(label='nuovi_positivi', renderers=[e1])
        e1s = p2.vbar_stack(stackers=to_positive, width=datetime.timedelta(days=1) * .8, x='date',
                            color=Category10_10[:len(to_positive)], source=ds)
        for l, e1 in zip(to_positive, e1s):
            legend.items.append(LegendItem(label=l, renderers=[e1]))
        legend.items.reverse()
        legend.items.insert(0, legend_entry)
        e1s = p2.vbar_stack(stackers=to_negative, width=datetime.timedelta(days=1) * .8, x='date',
                            color=Category10_10[len(to_positive):][:len(to_negative)], source=ds)
        for l, e1 in zip(to_negative, e1s):
            legend.items.append(LegendItem(label=l, renderers=[e1]))
        p2.title.text = f'Ripartizione casi in Italia (giornaliero, media 7 giorni)'
        legend.click_policy = 'hide'
        p2.add_layout(legend, 'right')
        p2.yaxis.formatter = NumeralTickFormatter(format='0')
        p2.xaxis.formatter = DatetimeTickFormatter()
        p2.xaxis.ticker.desired_num_ticks = 20

        p = gridplot([[p], [p2]], sizing_mode='scale_width', toolbar_location="right")
        # p = Column(children=[p, p2], sizing_mode='scale_width')

        save(p)

        print('<a name="vax"></a>', file=italiafile)
        print('## Vaccinazioni', file=italiafile)

        filename = f'plots/Italia_vax.html'
        include(italiafile, filename, 4)
        print('[Indietro](#main)', file=italiafile)
        output_file(filename)
        p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                   y_range=DataRange1d(only_visible=True))
        p.tools.append(HoverTool(tooltips=[("Tipo", "$name"),
                                           ('Data', '@date{%F}'),
                                           ("Valore", "@$name")],
                                 formatters={'@date': 'datetime'}))

        vax_values = ['d1', 'd2', 'dpi', 'db1', 'db2']
        daily = ita_vax_data.pivot_table(index=['data'],
                                         values=vax_values,
                                         aggfunc='sum')
        daily_consegne = ita_vax_data_consegne.pivot_table(index=['data_consegna'],
                                                           values=['numero_dosi'],
                                                           aggfunc='sum')
        daily = daily.merge(daily_consegne, how='left', left_index=True, right_index=True)
        daily.fillna(0, inplace=True)
        cumul = daily.cumsum()
        ds = ColumnDataSource()
        ds.data['date'] = pd.to_datetime(cumul.index)
        ds.data['prima_dose'] = cumul['d1']+cumul['dpi']
        ds.data['seconda_dose'] = cumul['d2']
        ds.data['booster'] = cumul['db1']
        ds.data['booster 2'] = cumul['db2']
        ds.data['numero_dosi'] = cumul['numero_dosi']

        p.varea_stack(stackers=['prima_dose', 'seconda_dose', 'booster', 'booster 2'], x='date',
                      color=[Category10_10[c] for c in [0, 1, 3, 4]],
                      source=ds, legend_label=['dose 1', 'dose 2', 'booster 1', 'booster 2'])
        p.vline_stack(stackers=['prima_dose', 'seconda_dose', 'booster', 'booster 2'], x='date',
                      color=[Category10_10[c] for c in [0, 1, 3, 4]],
                      source=ds, legend_label=['dose 1', 'dose 2', 'booster 1', 'booster 2'])
        p.vline_stack(x='date', color='black', stackers=['numero_dosi'], source=ds,
                      legend_label='dosi disponibili')
        p.legend.location = 'top_left'
        p.title.text = f'Vaccinazioni in Italia (cumulativo)'
        p.yaxis.formatter = NumeralTickFormatter(format='0')
        p.xaxis.formatter = DatetimeTickFormatter()
        p.xaxis.ticker.desired_num_ticks = 20

        p2 = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                    y_range=DataRange1d(only_visible=True))
        p2.tools.append(HoverTool(tooltips=[("Tipo", "$name"),
                                            ('Data', '@date{%F}'),
                                            ("Valore", "@$name")],
                                  formatters={'@date': 'datetime'}))

        ds = ColumnDataSource()
        ds.data['date'] = pd.to_datetime(daily.index)
        ds.data['prima_dose'] = daily['d1']+daily['dpi']
        ds.data['seconda_dose'] = daily['d2']
        ds.data['booster'] = daily['db1']
        ds.data['booster 2'] = daily['db2']
        p2.vbar_stack(stackers=['prima_dose', 'seconda_dose', 'booster', 'booster 2'], width=datetime.timedelta(days=1) * .8,
                      x='date',
                      color=[Category10_10[c] for c in [0, 1, 3, 4]], source=ds,
                      legend_label=['dose 1', 'dose 2', 'booster 1', 'booster 2'])
        p2.legend.location = 'top_left'
        p2.title.text = f'Vaccinazioni in Italia (giornaliero)'
        p2.yaxis.formatter = NumeralTickFormatter(format='0')
        p2.xaxis.formatter = DatetimeTickFormatter()
        p2.xaxis.ticker.desired_num_ticks = 20

        vax_by_age_dose = ita_vax_data.pivot_table(index='eta',
                                                   values=vax_values,
                                                   aggfunc='sum')

        ita_pop_by_range = list()
        for interval in vax_by_age_dose.index:
            if len(interval) == 5:
                begin = int(interval[:2])
                end = int(interval[-2:])
            else:
                begin = int(interval[:2])
                end = begin + 1000
            ita_pop_by_range.append(ita_pop[(begin <= ita_pop['età']) & (ita_pop['età'] <= end)]['value'].sum())

        p3 = figure(width=880, height=300, x_range=list(vax_by_age_dose.index), sizing_mode='scale_width')
        p3.tools.append(HoverTool(tooltips=[("Intervallo età", "@intervallo"),
                                            ("Valore", "@$name")]))

        ds = ColumnDataSource()
        ds.data['intervallo'] = vax_by_age_dose.index
        ds.data['popolazione'] = ita_pop_by_range
        ds.data['prima dose'] = vax_by_age_dose['d1']+vax_by_age_dose['dpi']
        ds.data['seconda dose'] = vax_by_age_dose['d2']
        ds.data['booster'] = vax_by_age_dose['db1']
        ds.data['booster 2'] = vax_by_age_dose['db2']

        p3.title.text = 'Numero dosi effettuate per intervalli di età'

        p3.vbar(x=dodge('intervallo', 0, range=p3.x_range), width=0.8, source=ds, top='popolazione',
                color=Category10_10[2], name='popolazione', legend_label='popolazione')
        p3.vbar(x=dodge('intervallo', -0.3, range=p3.x_range), width=0.15, source=ds, top='prima dose',
                color=Category10_10[0], name='prima dose', legend_label='dose 1')
        p3.vbar(x=dodge('intervallo', -0.1, range=p3.x_range), width=0.15, source=ds, top='seconda dose',
                color=Category10_10[1], name='seconda dose', legend_label='dose 2')
        p3.vbar(x=dodge('intervallo', 0.1, range=p3.x_range), width=0.15, source=ds, top='booster',
                color=Category10_10[3], name='booster', legend_label='booster 1')
        p3.vbar(x=dodge('intervallo', 0.3, range=p3.x_range), width=0.15, source=ds, top='booster 2',
                color=Category10_10[4], name='booster 2', legend_label='booster 2')
        p3.yaxis.formatter = NumeralTickFormatter(format='0')

        p4 = figure(width=880, height=300, x_range=list(vax_by_age_dose.index), y_range=(0, 100),
                    sizing_mode='scale_width')
        p4.tools.append(HoverTool(tooltips=[("Intervallo età", "@intervallo"),
                                            ("Valore", "@$name%")]))

        ds_perc = ColumnDataSource()
        ds_perc.data['intervallo'] = vax_by_age_dose.index
        ds_perc.data['prima dose'] = (vax_by_age_dose['d1']+vax_by_age_dose['dpi']) / ita_pop_by_range * 100
        ds_perc.data['seconda dose'] = vax_by_age_dose['d2'] / ita_pop_by_range * 100
        ds_perc.data['booster'] = vax_by_age_dose['db1'] / ita_pop_by_range * 100
        ds_perc.data['booster 2'] = vax_by_age_dose['db2'] / ita_pop_by_range * 100

        p4.title.text = 'Percentuali dosi effettuate rispetto alla popolazione negli intervalli di età'

        p4.vbar(x=dodge('intervallo', -0.3, range=p4.x_range), width=0.15, source=ds_perc, top='prima dose',
                color=Category10_10[0], name='prima dose', legend_label='dose 1')
        p4.vbar(x=dodge('intervallo', -0.1, range=p4.x_range), width=0.15, source=ds_perc, top='seconda dose',
                color=Category10_10[1], name='seconda dose', legend_label='dose 2')
        p4.vbar(x=dodge('intervallo', 0.1, range=p4.x_range), width=0.15, source=ds_perc, top='booster',
                color=Category10_10[3], name='booster', legend_label='booster 1')
        p4.vbar(x=dodge('intervallo', 0.3, range=p4.x_range), width=0.15, source=ds_perc, top='booster 2',
                color=Category10_10[4], name='booster', legend_label='booster 2')
        p4.yaxis.formatter = NumeralTickFormatter(format='0')
        p4.legend.location = 'top_left'

        p = gridplot([[p], [p2], [p3], [p4]], sizing_mode='scale_width', toolbar_location="right")
#        p = Column(children=[p, p2, p3, p4], sizing_mode='scale_width')

        save(p)

        filename = f'plots/regioni_vax.html'
        output_file(filename)
        print('<h3>Numero dosi per regioni e fascia di età</h3>',
              file=italiafile)
        include(italiafile, filename, 3.4)
        print('[Indietro](#main)', file=italiafile)

        plots = list()
        legend_plot = figure(width=400, height=80, sizing_mode='fixed')
        legend_plot.axis.visible = False
        legend_plot.grid.visible = False
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[2], name='popolazione', legend_label='popolazione',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[0], name='prima dose', legend_label='dose 1',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[1], name='seconda dose', legend_label='dose 2',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[3], name='booster', legend_label='booster 1',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[4], name='booster 2', legend_label='booster 2',
                         visible=False)
        legend_plot.legend.location = 'top_left'
        legend_plot.legend.orientation = 'horizontal'
        legend_plot.toolbar.logo = None
        legend_plot.toolbar_location = None

        row_count = 3
        regioni_vax = sorted(set(ita_vax_data['reg']))
        for i, regione in enumerate(regioni_vax):

            vax_by_age_dose = ita_vax_data[ita_vax_data['reg'] == regione].pivot_table(index='eta',
                                                                                             values=vax_values,
                                                                                             aggfunc='sum')

            reg_pop_by_range = list()
            for interval in vax_by_age_dose.index:
                if len(interval) == 5:
                    begin = int(interval[:2])
                    end = int(interval[-2:])
                else:
                    begin = int(interval[:2])
                    end = begin + 1000
                reg_pop_by_range.append(
                    ita_pop[(begin <= ita_pop['età']) & (ita_pop['età'] <= end) & (ita_pop['regione'] == regione)][
                        'value'].sum())

            reg_plot = figure(width=880, height=400, x_range=list(vax_by_age_dose.index), sizing_mode='scale_width')
            reg_plot.tools.append(HoverTool(tooltips=[("Intervallo età", "@intervallo"),
                                                      ("Valore", "@$name")]))

            ds = ColumnDataSource()
            ds.data['intervallo'] = vax_by_age_dose.index
            ds.data['popolazione'] = reg_pop_by_range
            ds.data['prima dose'] = vax_by_age_dose['d1'] + vax_by_age_dose['dpi']
            ds.data['seconda dose'] = vax_by_age_dose['d2']
            ds.data['booster'] = vax_by_age_dose['db1']
            ds.data['booster 2'] = vax_by_age_dose['db2']

            reg_plot.title.text = f'{regione}'

            reg_plot.vbar(x=dodge('intervallo', 0, range=reg_plot.x_range), width=0.8, source=ds, top='popolazione',
                          color=Category10_10[2], name='popolazione')
            reg_plot.vbar(x=dodge('intervallo', -0.3, range=reg_plot.x_range), width=0.15, source=ds,
                          top='prima dose', color=Category10_10[0], name='prima dose')
            reg_plot.vbar(x=dodge('intervallo', -0.1, range=reg_plot.x_range), width=0.15, source=ds,
                          top='seconda dose', color=Category10_10[1], name='seconda dose')
            reg_plot.vbar(x=dodge('intervallo', 0.1, range=reg_plot.x_range), width=0.15, source=ds,
                          top='booster', color=Category10_10[3], name='booster')
            reg_plot.vbar(x=dodge('intervallo', 0.3, range=reg_plot.x_range), width=0.15, source=ds,
                          top='booster 2', color=Category10_10[4], name='booster 2')
            reg_plot.yaxis.formatter = NumeralTickFormatter(format='0')
            if i % row_count == 0:
                plots.append(list())
            plots[-1].append(reg_plot)

        p = layout(legend_plot, gridplot(plots, toolbar_location="right"), sizing_mode='scale_width')
        save(p)

        filename = f'plots/regioni_vax_perc.html'
        output_file(filename)
        print('<h3>Percentuale vaccinazioni per regioni e fascia di età</h3>', file=italiafile)
        print(
            '<iframe width="560" height="315" src="https://www.youtube.com/embed/7ub3ixdsJRg" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
            file=italiafile)

        include(italiafile, filename, 3.4)
        print('[Indietro](#main)', file=italiafile)
        legend_plot = figure(width=400, height=80, sizing_mode='fixed')
        legend_plot.axis.visible = False
        legend_plot.grid.visible = False
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[0], name='prima dose', legend_label='dose 1',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[1], name='seconda dose', legend_label='dose 2',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[3], name='booster', legend_label='booster 1',
                         visible=False)
        legend_plot.vbar(x=[0], top=[0], color=Category10_10[4], name='booster 2', legend_label='booster 2',
                         visible=False)
        legend_plot.legend.location = 'top_left'
        legend_plot.legend.orientation = 'horizontal'
        legend_plot.toolbar.logo = None
        legend_plot.toolbar_location = None

        plots_perc = list()
        for i, regione in enumerate(regioni_vax):

            vax_by_age_dose = ita_vax_data[ita_vax_data['reg'] == regione].pivot_table(index='eta',
                                                                                             values=vax_values,
                                                                                             aggfunc='sum')

            reg_pop_by_range = list()
            for interval in vax_by_age_dose.index:
                if len(interval) == 5:
                    begin = int(interval[:2])
                    end = int(interval[-2:])
                else:
                    begin = int(interval[:2])
                    end = begin + 1000
                reg_pop_by_range.append(
                    ita_pop[(begin <= ita_pop['età']) & (ita_pop['età'] <= end) & (ita_pop['regione'] == regione)][
                        'value'].sum())

            reg_plot_perc = figure(width=880, height=400, x_range=list(vax_by_age_dose.index), y_range=(0, 100),
                                   sizing_mode='scale_width')
            reg_plot_perc.tools.append(HoverTool(tooltips=[("Intervallo età", "@intervallo"),
                                                           ("Percentuale", "@$name%")]))
            ds_perc = ColumnDataSource()
            ds_perc.data['intervallo'] = vax_by_age_dose.index
            ds_perc.data['prima dose'] = (vax_by_age_dose['d1'] + vax_by_age_dose['dpi']) / reg_pop_by_range * 100
            ds_perc.data['seconda dose'] = vax_by_age_dose['d2'] / reg_pop_by_range * 100
            ds_perc.data['booster'] = vax_by_age_dose['db1'] / reg_pop_by_range * 100
            ds_perc.data['booster 2'] = vax_by_age_dose['db2'] / reg_pop_by_range * 100

            reg_plot_perc.title.text = f'{regione}'

            reg_plot_perc.vbar(x=dodge('intervallo', -0.3, range=reg_plot_perc.x_range), width=0.15, source=ds_perc,
                               top='prima dose',
                               color=Category10_10[0], name='prima dose')
            reg_plot_perc.vbar(x=dodge('intervallo', -0.1, range=reg_plot_perc.x_range), width=0.15, source=ds_perc,
                               top='seconda dose',
                               color=Category10_10[1], name='seconda dose')
            reg_plot_perc.vbar(x=dodge('intervallo', 0.1, range=reg_plot_perc.x_range), width=0.15, source=ds_perc,
                               top='booster',
                               color=Category10_10[3], name='booster')
            reg_plot_perc.vbar(x=dodge('intervallo', 0.3, range=reg_plot_perc.x_range), width=0.15, source=ds_perc,
                               top='booster 2',
                               color=Category10_10[4], name='booster 2')
            reg_plot_perc.yaxis.formatter = NumeralTickFormatter(format='0')
            if i % row_count == 0:
                plots_perc.append(list())
            plots_perc[-1].append(reg_plot_perc)

        p = layout(legend_plot, gridplot(plots_perc, toolbar_location="right"), sizing_mode='scale_width')
        save(p)

        print('<a name="postam"></a>', file=italiafile)
        print('## Tamponi', file=italiafile)

        filename = f'plots/Italia_postam.html'
        include(italiafile, filename, 2)
        print('[Indietro](#main)', file=italiafile)
        output_file(filename)
        p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                   y_range=DataRange1d(only_visible=True))
        p.tools.append(HoverTool(tooltips=[('Date', '@date{%F}'),
                                           ("Value", "@value")],
                                 formatters={'@date': 'datetime'}))
        cumul = ita_reg_data.pivot_table(values=['tamponi', 'nuovi_positivi'], index=['data'], aggfunc='sum')
        daily_tam = cumul['tamponi'][1:] - cumul['tamponi'].values[:-1]
        daily_tam[daily_tam < 0] = 0
        rapporto = cumul['nuovi_positivi'][1:] / daily_tam

        ds = ColumnDataSource()
        ds.data['value'] = rapporto.values
        ds.data['date'] = pd.to_datetime(rapporto.index)
        p.line(source=ds, x='date', y='value', name="Rapporto posiviti/tamponi", color=Category10_10[0], line_width=2,
               legend_label="Rapporto posiviti/tamponi")
        p.circle(source=ds, x='date', y='value', color=Category10_10[0], legend_label="Rapporto posiviti/tamponi")

        p.title.text = f'Rappoto giornaliero nuovi positivi/tamponi'
        p.legend.location = 'top_left'
        p.yaxis.formatter = NumeralTickFormatter(format='0.00')
        p.xaxis.formatter = DatetimeTickFormatter()
        p.xaxis.ticker.desired_num_ticks = 20

        p2 = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                    y_range=DataRange1d(only_visible=True))
        p2.tools.append(HoverTool(tooltips=[('Date', '@date{%F}'),
                                            ("Value", "@value")],
                                  formatters={'@date': 'datetime'}))

        ds = ColumnDataSource()
        ds.data['value'] = daily_tam.values
        ds.data['date'] = pd.to_datetime(daily_tam.index)
        p2.vbar(source=ds, x='date', top='value', name="Tamponi giornaliero", color=Category10_10[0],
                width=datetime.timedelta(days=1) * .8, legend_label="Tamponi giornaliero")

        p2.title.text = f'Tamponi giornaliero'
        p2.legend.location = 'top_left'
        p2.yaxis.formatter = NumeralTickFormatter(format='0.00')
        p2.xaxis.formatter = DatetimeTickFormatter()
        p2.xaxis.ticker.desired_num_ticks = 20

        p = gridplot([[p], [p2]], sizing_mode='scale_width', toolbar_location="right")

        save(p)

        print('', file=italiafile)
        print('---', file=italiafile)
        print('', file=italiafile)

        print('<a name="province"></a>', file=italiafile)
        print('## Link a pagine delle Regioni e Province', file=italiafile)
        for regione in regioni:
            print(f' * [{regione}](/pages/{regione.replace(" ", "_")}.md)', file=italiafile)
        print('', file=italiafile)
        print('[Indietro](#main)', file=italiafile)

        print('', file=italiafile)
        print('---', file=italiafile)
        print('', file=italiafile)
        print('<a name="regioni"></a>', file=italiafile)
        print('## Altri dati di confronto tra regioni', file=italiafile)

        filename = f'plots/regioni.html'
        include(italiafile, filename, len(etichette))
        print('[Indietro](#main)', file=italiafile)
        output_file(filename)
        regplots = list()
        for etichetta in etichette:

            print(etichetta)

            cumul = ita_reg_data.pivot_table(index=['data'], values=etichetta, columns=['denominazione_regione'],
                                             aggfunc='sum')

            legend = Legend()
            legend.click_policy = 'hide'
            p = figure(width=880, height=300, x_axis_type='datetime',
                       y_range=DataRange1d(only_visible=True))
            p.tools.append(HoverTool(tooltips=[("Regione", "@regione"),
                                               ('Data', '@date{%F}'),
                                               ("Valore", "@value")],
                                     formatters={'@date': 'datetime'}))
            for i, regione in enumerate(regioni):
                ds = ColumnDataSource()
                ds.data['value'] = cumul[regione]
                ds.data['date'] = pd.to_datetime(cumul.index)
                ds.data['regione'] = [regione] * len(ds.data['date'])
                e1 = p.line(source=ds, x='date', y='value', name=regione, color=Category10_10[i % 10], line_width=2)
                if i < 10:
                    e2 = p.circle(source=ds, x='date', y='value', color=Category10_10[i % 10])
                elif i < 20:
                    e2 = p.triangle(source=ds, x='date', y='value', color=Category10_10[i % 10])
                legend.items.append(LegendItem(label=regione, renderers=[e1, e2]))

            p.title.text = f'{etichetta.capitalize().replace("_", " ")} per regione'
            p.add_layout(legend, 'right')
            p.yaxis.formatter = NumeralTickFormatter(format='0')
            p.xaxis.formatter = DatetimeTickFormatter()
            p.xaxis.ticker.desired_num_ticks = 20
            p.legend.label_height = 15
            p.legend.glyph_height = 15
            p.legend.spacing = 0

            regplots.append([p])

        p = gridplot(regplots, sizing_mode='scale_width', toolbar_location="right")
        save(p)

        print(footer, file=italiafile)

        for regione in regioni:
            print('\t', regione)

            with open(f'pages/{regione.replace(" ", "_")}.md', mode='wt', encoding='utf-8') as regionefile:

                print('<a name="main"></a>', file=regionefile)
                print(f'# Ripartizione casi in {regione} - [Indietro]({root})', file=regionefile)

                print('[Cumulativo](#cumul) - [Giornaliero](#daily) - [Tamponi](#tam)', file=regionefile)

                print('<a name="cumul"></a>', file=regionefile)
                print('### Cumulativo', file=regionefile)

                filename = f'plots/{regione.replace(" ", "_")}.html'
                include(regionefile, filename)
                print('[Indietro](#main)', file=regionefile)
                output_file(filename)
                p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                           y_range=DataRange1d(only_visible=True))
                p.tools.append(HoverTool(tooltips=[("Tipo", "$name"),
                                                   ('Data', '@date{%F}'),
                                                   ("Valore", "@$name")],
                                         formatters={'@date': 'datetime'}))

                cumul = ita_reg_data[ita_reg_data['denominazione_regione'] == regione].pivot_table(index=['data'],
                                                                                                   values=values,
                                                                                                   aggfunc='sum')
                tamp = cumul['tamponi'][1:] - cumul['tamponi'].values[:-1]

                for to_neg in to_negative:
                    cumul[to_neg] = -cumul[to_neg]

                legend = Legend()
                legend.click_policy = 'hide'
                ds = ColumnDataSource()
                ds.data['date'] = pd.to_datetime(cumul.index)
                for value in values:
                    ds.data[value] = cumul[value]
                e1s = p.varea_stack(stackers=to_positive, x='date',
                                    color=Category10_10[:len(to_positive)], source=ds)
                e2s = p.vline_stack(stackers=to_positive, x='date',
                                    color=Category10_10[:len(to_positive)], source=ds)
                for l, e1, e2 in zip(to_positive, e1s, e2s):
                    legend.items.append(LegendItem(label=l, renderers=[e1, e2]))
                legend.items.reverse()
                e1s = p.varea_stack(stackers=to_negative, x='date',
                                    color=Category10_10[len(to_positive):][:len(to_negative)], source=ds)
                e2s = p.vline_stack(stackers=to_negative, x='date',
                                    color=Category10_10[len(to_positive):][:len(to_negative)], source=ds)
                for l, e1, e2 in zip(to_negative, e1s, e2s):
                    legend.items.append(LegendItem(label=l, renderers=[e1, e2]))
                p.title.text = f'Ripartizione casi in {regione} (cumulativo)'
                p.add_layout(legend, 'right')
                p.yaxis.formatter = NumeralTickFormatter(format='0')
                p.xaxis.formatter = DatetimeTickFormatter()
                p.xaxis.ticker.desired_num_ticks = 20

                save(p)

                print('<a name="daily"></a>', file=regionefile)
                print('### Giornaliero', file=regionefile)

                filename = f'plots/{regione.replace(" ", "_")}_daily.html'
                include(regionefile, filename)
                print('[Indietro](#main)', file=regionefile)
                output_file(filename)
                p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                           y_range=DataRange1d(only_visible=True))
                p.tools.append(HoverTool(tooltips=[("Tipo", "$name"),
                                                   ('Data', '@date{%F}'),
                                                   ("Valore", "@$name")],
                                         formatters={'@date': 'datetime'}))

                daily = cumul[1:] - cumul.values[:-1]
                daily[daily[to_positive] < 0] = 0
                daily[daily[to_negative] > 0] = 0
                daily = daily.rolling(7, win_type='boxcar').mean()

                legend = Legend()
                ds = ColumnDataSource()
                ds.data['date'] = pd.to_datetime(daily.index)
                for value in values:
                    ds.data[value] = daily[value]
                cumul[cumul['nuovi_positivi'] < 0] = 0
                ds.data['nuovi_positivi'] = cumul['nuovi_positivi'][1:].rolling(7, win_type='boxcar').mean()
                e1 = p.vbar(top='nuovi_positivi', x='date', source=ds, width=datetime.timedelta(days=1) * .8,
                            color=Category10_10[len(to_positive) + len(to_negative):][3], name='nuovi_positivi')
                legend_entry = LegendItem(label='nuovi_positivi', renderers=[e1])
                e1s = p.vbar_stack(stackers=to_positive, width=datetime.timedelta(days=1) * .8,
                                   x='date', color=Category10_10[:len(to_positive)], source=ds)
                for l, e1 in zip(to_positive, e1s):
                    legend.items.append(LegendItem(label=l, renderers=[e1]))
                legend.items.reverse()
                legend.items.insert(0, legend_entry)
                e1s = p.vbar_stack(stackers=to_negative, width=datetime.timedelta(days=1) * .8,
                                   x='date', color=Category10_10[len(to_positive):][:len(to_negative)], source=ds)
                for l, e1 in zip(to_negative, e1s):
                    legend.items.append(LegendItem(label=l, renderers=[e1]))
                legend.click_policy = 'hide'
                p.add_layout(legend, 'right')
                p.title.text = f'Ripartizione casi in {regione} (giornaliero, media 7 giorni)'
                p.yaxis.formatter = NumeralTickFormatter(format='0')
                p.xaxis.formatter = DatetimeTickFormatter()
                p.xaxis.ticker.desired_num_ticks = 20

                save(p)

                print('<a name="tam"></a>', file=regionefile)
                print('### Tamponi giornaliero', file=regionefile)

                filename = f'plots/{regione.replace(" ", "_")}_tam.html'
                include(regionefile, filename)
                print('[Indietro](#main)', file=regionefile)
                output_file(filename)
                p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                           y_range=DataRange1d(only_visible=True))
                p.tools.append(HoverTool(tooltips=[('Date', '@date{%F}'),
                                                   ("Value", "@value")],
                                         formatters={'@date': 'datetime'}))

                ds = ColumnDataSource()
                ds.data['value'] = tamp.values
                ds.data['date'] = pd.to_datetime(tamp.index)
                p.vbar(source=ds, x='date', top='value', name="Tamponi giornaliero", color=Category10_10[0],
                       width=datetime.timedelta(days=1) * .8, legend_label="Tamponi giornaliero")

                p.title.text = f'Tamponi giornaliero in {regione}'
                p.legend.location = 'top_left'
                p.yaxis.formatter = NumeralTickFormatter(format='0.00')
                p.xaxis.formatter = DatetimeTickFormatter()
                p.xaxis.ticker.desired_num_ticks = 20

                save(p)

                print('', file=regionefile)
                print('---', file=regionefile)
                print('', file=regionefile)
                print('<a name="prov"></a>', file=regionefile)
                print('# Casi totali per provincia', file=regionefile)
                print('[Indietro](#main)', file=regionefile)
                print('', file=regionefile)

                province = [provincia for provincia in sorted(
                    set(ita_prov_data[ita_prov_data['denominazione_regione'] == regione]['denominazione_provincia'])) if
                            provincia != 'In fase di definizione'
                            and provincia != 'Fuori Regione / Provincia Autonoma'
                            and provincia != 'In fase di definizione/aggiornamento'
                            and provincia != 'fuori Regione/P.A.']

                labels = [re.sub(r"\W", "_", provincia) for provincia in province]

                links = [f'[{provincia}](#{label})' for provincia, label in zip(province, labels)]
                print('Cumulativo: ', ' - '.join(links), file=regionefile)
                print('', file=regionefile)

                links = [f'[{provincia}](#{label}_daily)' for provincia, label in zip(province, labels)]
                print('Giornaliero: ', ' - '.join(links), file=regionefile)
                print('', file=regionefile)

                for provincia, label in zip(province, labels):
                    filename = f'plots/{regione.replace(" ", "_")}_{label}.html'
                    print('', file=regionefile)
                    print(f'---', file=regionefile)
                    print('', file=regionefile)
                    print(f'<a name="{label}"></a>', file=regionefile)
                    print(f'## Totale casi a {provincia} - {regione}', file=regionefile)
                    include(regionefile, filename)
                    print('[Indietro](#prov)', file=regionefile)

                for provincia, label in zip(province, labels):
                    filename = f'plots/{regione.replace(" ", "_")}_{label}_daily.html'
                    print('', file=regionefile)
                    print(f'---', file=regionefile)
                    print('', file=regionefile)
                    print(f'<a name="{label}_daily"></a>', file=regionefile)
                    print(f'## Casi giornalieri a {provincia} - {regione}', file=regionefile)
                    include(regionefile, filename)
                    print('[Indietro](#prov)', file=regionefile)

                    print('\t\t', provincia)

                    filename = f'plots/{regione.replace(" ", "_")}_{label}.html'

                    output_file(filename)
                    p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                               y_range=DataRange1d(only_visible=True))
                    p.tools.append(HoverTool(tooltips=[('Data', '@date{%F}'),
                                                       ("Valore", "@value")],
                                             formatters={'@date': 'datetime'}))

                    cumul = ita_prov_data[ita_prov_data['denominazione_provincia'] == provincia].pivot_table(
                        index=['data'],
                        values='totale_casi',
                        aggfunc='sum')
                    ds = ColumnDataSource()
                    ds.data['value'] = cumul['totale_casi'].values
                    ds.data['date'] = pd.to_datetime(cumul.index)
                    p.line(source=ds, x='date', y='value', name=f'Totale casi a {provincia} - {regione}',
                           color=Category10_10[0],
                           line_width=2, legend_label=f'Totale casi a {provincia} - {regione}')
                    p.circle(source=ds, x='date', y='value', color=Category10_10[0],
                             legend_label=f'Totale casi a {provincia} - {regione}')

                    p.title.text = f'Totale casi a {provincia} - {regione}'
                    p.legend.location = 'top_left'
                    p.yaxis.formatter = NumeralTickFormatter(format='0')
                    p.xaxis.formatter = DatetimeTickFormatter()
                    p.xaxis.ticker.desired_num_ticks = 20

                    save(p)

                    filename = f'plots/{regione.replace(" ", "_")}_{label}_daily.html'

                    daily = cumul[1:] - cumul.values[:-1]
                    daily[daily < 0] = 0
                    daily = daily.rolling(7, win_type='boxcar').mean()

                    output_file(filename)
                    p = figure(width=880, height=300, x_axis_type='datetime', sizing_mode='scale_width',
                               y_range=DataRange1d(only_visible=True))
                    p.tools.append(HoverTool(tooltips=[('Date', '@date{%F}'),
                                                       ("Value", "@value")],
                                             formatters={'@date': 'datetime'}))

                    ds = ColumnDataSource()
                    ds.data['value'] = daily.values
                    ds.data['date'] = pd.to_datetime(daily.index)
                    p.vbar(source=ds, x='date', top='value',
                           name=f'Casi giornalieri a {provincia} - {regione} (media 7 giorni)',
                           color=Category10_10[0],
                           width=datetime.timedelta(days=1) * .8,
                           legend_label=f'Casi giornalieri a {provincia} - {regione} (media 7 giorni)')

                    p.title.text = f'Casi giornalieri a {provincia} - {regione} (media 7 giorni)'
                    p.legend.location = 'top_left'
                    p.yaxis.formatter = NumeralTickFormatter(format='0')
                    p.xaxis.formatter = DatetimeTickFormatter()
                    p.xaxis.ticker.desired_num_ticks = 20

                    save(p)

                print(footer, file=regionefile)
