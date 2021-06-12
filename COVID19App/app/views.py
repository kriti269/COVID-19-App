from django.shortcuts import render
from django.views import generic
from urllib import request as urlrequest
import pandas
import seaborn
import matplotlib.pyplot
from datetime import datetime
import matplotlib.dates as dates
from matplotlib.font_manager import FontProperties
from io import StringIO


class GetGraphs(generic.TemplateView):
    template_name = "graphs.html"

    def displayGraphs(request):
        # get covid19 data from api
        covid_data = GetGraphs.getAllData()
        context = {}
        # set heatmap and linchart context values as svg image data
        context['heatmap'] = GetGraphs.getHeatMap(covid_data).getvalue()
        context['linechart'] = GetGraphs.getLineChart(covid_data).getvalue()
        return render(request, 'graphs.html', context)

    @staticmethod
    def getHeatMap(data):
        # fetch all list of Active cases for all PHUs
        dict_new = {}
        for items in data:
            if items["PHU_NAME"] is not None:
                if items["PHU_NAME"] not in dict_new :
                    dict_new[items["PHU_NAME"]] = []
                dict_new[items["PHU_NAME"]].append(items["ACTIVE_CASES"])

        # create dataframe with filtered data
        dataframe = pandas.DataFrame.from_dict(dict_new, orient='index')
        dataframe = dataframe.T

        # create figure instance
        matplotlib.pyplot.figure(figsize=(20, 10))
        # calculate correlation and plot heatmap
        heatmap = seaborn.heatmap(dataframe.corr())
        heatmap.set_title('Correlation Heatmap')

        # save figure as svg in StringIO object
        image = StringIO()
        matplotlib.pyplot.savefig(image, dpi=300, format='svg')
        return image

    @staticmethod
    def getLineChart(data):
        # fetch active cases and dates for all PHUs
        dict_new = {}
        for items in data:
            if items["PHU_NAME"] not in dict_new:
                dict_new[items["PHU_NAME"]] = {"DATES": [], "ACTIVE_CASES": []}

            date = items["FILE_DATE"]
            if date not in dict_new[items["PHU_NAME"]]["DATES"]:
                dict_new[items["PHU_NAME"]]["DATES"].append(date)
                dict_new[items["PHU_NAME"]]["ACTIVE_CASES"].append(items["ACTIVE_CASES"])

        # create figure instance and define labels
        matplotlib.pyplot.figure(figsize=(20, 10))
        matplotlib.pyplot.gca().xaxis.set_major_formatter(dates.DateFormatter('%Y-%m-%d'))
        matplotlib.pyplot.gca().xaxis.set_major_locator(dates.DayLocator(interval=15))
        matplotlib.pyplot.ylabel("Number of Active Cases")
        matplotlib.pyplot.xlabel("Time")
        matplotlib.pyplot.xticks(rotation=45)

        # convert dates from string to datetime format and sort the lists of date and active cases for PHUs
        for item in dict_new:
            date = list(dict_new[item]["DATES"])
            date_list = [datetime.fromisoformat(x).date() for x in date]
            dates_new = dates.date2num(date_list)
            xs, ys = zip(*sorted(zip(dates_new, list(dict_new[item]["ACTIVE_CASES"]))))
            matplotlib.pyplot.plot_date(xs, ys, '-', label=item)

        # set up legends for identifying PHUs
        fontp = FontProperties()
        fontp.set_size('small')
        matplotlib.pyplot.legend(title='Counties', bbox_to_anchor=(1, 1), loc='upper left', prop=fontp)

        # save figure as svg in StringIO object
        image = StringIO()
        matplotlib.pyplot.savefig(image, dpi=300, format='svg')
        return image

    @staticmethod
    def getAllData():
        # fetch entire dataset using apis with offset
        offset = 0
        data = []
        while True:
            url = "https://data.ontario.ca/api/3/action/datastore_search?resource_id=d1bfe1ad-6575-4352-8302-09ca81f7ddfc&offset=" + str(
                offset)
            response = urlrequest.urlopen(url)
            new_data = pandas.read_json(response.read())['result']['records']
            offset += 100
            if len(new_data) == 0:
                break
            data += new_data
        return data


