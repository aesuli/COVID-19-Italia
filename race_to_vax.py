# COVID-19 data visualization
# Copyright (C) 2021 Andrea Esuli <andrea@esuli.it>
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
import os
import shutil
from io import BytesIO
from time import sleep

import ffmpeg as ffmpeg
import pandas as pd
from PIL import Image
from bokeh.io import webdriver
from bokeh.io.export import get_screenshot_as_png
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, NumeralTickFormatter, LegendItem, Legend
from bokeh.models.tools import HoverTool
from bokeh.palettes import Category10_10
from bokeh.plotting import figure
from bokeh.transform import dodge


def plot_day(time_ita_vax_data, day, i, total, row_count, driver):
    print(day)

    title_plot = figure(width=880, height=400, sizing_mode='scale_width')
    title_plot.axis.visible = False
    title_plot.grid.visible = False
    title_legend = Legend()
    title_legend.items.append(LegendItem(label='Percentuale vaccinati per'))
    title_legend.items.append(LegendItem(label='regione e fascia di età'))
    title_plot.add_layout(title_legend)
    title_plot.legend.location = 'top_left'
    title_legend.label_text_font_size = '24px'
    title_plot.toolbar.logo = None
    title_plot.toolbar_location = None

    legend_plot = figure(width=880, height=400, sizing_mode='scale_width')
    legend_plot.axis.visible = False
    legend_plot.grid.visible = False
    legend_plot.vbar(x=[0], top=[0], color=Category10_10[0], name='prima dose', legend_label='prima',
                     visible=False)
    legend_plot.vbar(x=[0], top=[0], color=Category10_10[1], name='seconda dose', legend_label='seconda',
                     visible=False)
    legend_plot.vbar(x=[0], top=[0], color=Category10_10[3], name='terza dose', legend_label='terza dose',
                     visible=False)
    legend_plot.legend.title_text_font_size = '20px'
    legend_plot.legend.label_text_font_size = '15px'
    legend_plot.legend.title = f'Giorno: {day}  #{i}/{total}'
    legend_plot.legend.location = 'top_left'
    legend_plot.legend.orientation = 'horizontal'
    legend_plot.toolbar.logo = None
    legend_plot.toolbar_location = None

    plots_perc = list()
    plots_perc.append([title_plot, legend_plot])
    for i, regione in enumerate(regioni_vax, 2):

        vax_by_age_dose = time_ita_vax_data[time_ita_vax_data['nome_area'] == regione].pivot_table(
            index='fascia_anagrafica',
            values=['prima_dose',
                    'seconda_dose',
                    'dose_addizionale_booster'],
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

        reg_plot_perc = figure(width=880, height=400, x_range=list(vax_by_age_dose_nation.index), y_range=(0, 100),
                               sizing_mode='scale_width')
        reg_plot_perc.tools.append(HoverTool(tooltips=[("Intervallo età", "@intervallo"),
                                                       ("Percentuale", "@$name%")]))
        ds_perc = ColumnDataSource()
        ds_perc.data['intervallo'] = vax_by_age_dose.index
        ds_perc.data['prima dose'] = vax_by_age_dose['prima_dose'] / reg_pop_by_range * 100
        ds_perc.data['seconda dose'] = vax_by_age_dose['seconda_dose'] / reg_pop_by_range * 100
        ds_perc.data['terza dose'] = (vax_by_age_dose['dose_addizionale_booster']) / reg_pop_by_range * 100

        reg_plot_perc.title.text = f'{regione}'

        reg_plot_perc.vbar(x=dodge('intervallo', -0.25, range=reg_plot_perc.x_range), width=0.2, source=ds_perc,
                           top='prima dose',
                           color=Category10_10[0], name='prima dose')
        reg_plot_perc.vbar(x=dodge('intervallo', 0.0, range=reg_plot_perc.x_range), width=0.2, source=ds_perc,
                           top='seconda dose',
                           color=Category10_10[1], name='seconda dose')
        reg_plot_perc.vbar(x=dodge('intervallo', 0.25, range=reg_plot_perc.x_range), width=0.2, source=ds_perc,
                           top='terza dose',
                           color=Category10_10[3], name='terza dose')
        reg_plot_perc.yaxis.formatter = NumeralTickFormatter(format='0')
        if i % row_count == 0:
            plots_perc.append(list())
        plots_perc[-1].append(reg_plot_perc)

    closing_plot = figure(width=880, height=400, sizing_mode='scale_width')
    closing_plot.axis.visible = False
    closing_plot.grid.visible = False
    closing_legend = Legend()
    closing_legend.items.append(LegendItem(label='Andrea Esuli'))
    closing_legend.items.append(LegendItem(label='http://esuli.it'))
    closing_plot.add_layout(closing_legend)
    closing_plot.legend.location = 'bottom_right'
    closing_legend.label_text_font_size = '14px'
    closing_plot.toolbar.logo = None
    closing_plot.toolbar_location = None

    plots_perc[-1].append(closing_plot)

    p = gridplot(plots_perc, toolbar_location=None, sizing_mode='scale_width')

    get_screenshot_as_png(p, driver=driver)
    sleep(2)
    return Image.open(BytesIO(driver.get_screenshot_as_png()))


if __name__ == '__main__':

    img_dir = './race'

    os.makedirs(img_dir, exist_ok=True)

    ita_vax_data = pd.read_csv(
        'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv')

    ita_pop = pd.read_csv('popolazione_italia_2020.csv')

    days = sorted(set(ita_vax_data['data_somministrazione']))

    print(len(days))

    vax_by_age_dose_nation = ita_vax_data.pivot_table(
        index='fascia_anagrafica',
        values=['prima_dose',
                'dose_addizionale_booster'],
        aggfunc='sum')

    row_count = 4

    regioni_vax = sorted(set(ita_vax_data['nome_area']))

    fps = 3
    driver = webdriver.create_firefox_webdriver()

    start_delay = 3 * fps
    end_delay = 10 * fps

    for i, day in enumerate(days):
        time_ita_vax_data = ita_vax_data[ita_vax_data['data_somministrazione'] <= day]

        plot_png = plot_day(time_ita_vax_data, day, i + 1, len(days), row_count, driver)

        if i == 0:
            for j in range(start_delay):
                filename = f'race/race_to_vax_{(i + j):03d}.png'
                plot_png.save(filename)
        else:
            filename = f'race/race_to_vax_{(start_delay + i - 1):03d}.png'
            plot_png.save(filename)
    for j in range(end_delay):
        filename = f'race/race_to_vax_{(start_delay + i - 1 + j):03d}.png'
        plot_png.save(filename)

    driver.close()

    ffmpeg.input(f'{img_dir}/race_to_vax_%03d.png', framerate=fps).output('race_to_vax.mp4').overwrite_output().run()

    shutil.rmtree(img_dir, ignore_errors=True)
