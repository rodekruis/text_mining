import matplotlib.pyplot as plt
import matplotlib.pylab as plb
import seaborn as sns
import pandas as pd
import geopandas



# Set the styles for the plots
sns.set_style('whitegrid')
# For ease, print whole dataframe if called, comment out if not needed
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Read the data
disasters = pd.read_csv("../DataEnrichment/all_disasters.csv")


def fix_dates():
    """This function ensures that the dates from the all_disasters.csv file in this folder(!) all adhere to the same
    format and can be ordered based on their temporality."""
    # Create copy of the dataset in which we can store the disaster dates differently
    dd = disasters.copy()
    # Create column with entries being the first character of the date column
    dd['first_char'] = dd['date'].astype(str).str[0]
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    for index, row in dd.iterrows():
        if row['first_char'] in numbers:  # We are not yet dealing with months but a year is specified
            years = row['date'].split("-")
            year1 = int(years[0])  # The first year in which the disaster occurred
            year2 = int(years[1])  # The last year in which the disaster was still ongoing
            for i in range(year1, year2 + 1):
                # For every year we add all the months of that year as a month in which that disaster was happening
                row['date'] = "Jan " + str(i)
                dd = dd.append(row)
                row['date'] = "Feb " + str(i)
                dd = dd.append(row)
                row['date'] = "Mar " + str(i)
                dd = dd.append(row)
                row['date'] = "Apr " + str(i)
                dd = dd.append(row)
                row['date'] = "May " + str(i)
                dd = dd.append(row)
                row['date'] = "Jun " + str(i)
                dd = dd.append(row)
                row['date'] = "Jul " + str(i)
                dd = dd.append(row)
                row['date'] = "Aug " + str(i)
                dd = dd.append(row)
                row['date'] = "Sep " + str(i)
                dd = dd.append(row)
                row['date'] = "Oct " + str(i)
                dd = dd.append(row)
                row['date'] = "Nov " + str(i)
                dd = dd.append(row)
                row['date'] = "Dec " + str(i)
                dd = dd.append(row)

    dd = dd.drop(['first_char'], axis=1)  # Drop the extra column we created from our dataset
    dd = dd.reset_index()  # Reset the indexing

    # Below, we delete the rows that still contain the time period specified in years as we do not need these anymore
    dd['first_char'] = dd['date'].astype(str).str[0]
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    for index, row in dd.iterrows():
        if row['first_char'] in numbers:  # We are dealing with a time period
            dd = dd.drop([index])  # Drop this row

    # Below, we change the format of all the dates to a format that can be ordered based on time
    for index, row in dd.iterrows():
        full = row['date']
        if full[0:3] == "Jan":
            dd.at[index, 'date'] = "01" + full[4:8]
        elif full[0:3] == "Feb":
            dd.at[index, 'date'] = "02" + full[4:8]
        elif full[0:3] == "Mar":
            dd.at[index, 'date'] = "03" + full[4:8]
        elif full[0:3] == "Apr":
            dd.at[index, 'date'] = "04" + full[4:8]
        elif full[0:3] == "May":
            dd.at[index, 'date'] = "05" + full[4:8]
        elif full[0:3] == "Jun":
            dd.at[index, 'date'] = "06" + full[4:8]
        elif full[0:3] == "Jul":
            dd.at[index, 'date'] = "07" + full[4:8]
        elif full[0:3] == "Aug":
            dd.at[index, 'date'] = "08" + full[4:8]
        elif full[0:3] == "Sep":
            dd.at[index, 'date'] = "09" + full[4:8]
        elif full[0:3] == "Oct":
            dd.at[index, 'date'] = "10" + full[4:8]
        elif full[0:3] == "Nov":
            dd.at[index, 'date'] = "11" + full[4:8]
        elif full[0:3] == "Dec":
            dd.at[index, 'date'] = "12" + full[4:8]

    dd = dd.drop(['first_char'], axis=1)  # Drop the extra column we created from our dataset
    dd = dd.drop(['index'], axis=1)  # Drop the extra indices we created from our dataset

    return dd


def fix_years():
    """This function returns the dataframe with the date column as years."""
    # Create a list which already has the right entries for the dates, but still includes the month
    fixed = fix_dates()

    for index, row in fixed.iterrows():
        full = row['date']
        row['date'] = full[2:7]  # Only select the year

    return fixed


def disaster_type_per_country(d_type):
    """This function produces a count plot for the given disaster type, d_type, over all countries."""
    # Filter based on the given disaster type
    filtered = disasters[disasters.disaster_type == d_type].sort_values(['country'])

    plt.rc('figure', figsize=(15, 30))
    # Produce the plot and label it appropriately
    sns.countplot(data=filtered, y='country')
    plt.title('Occurrences of ' + d_type + ' for countries over all years')
    plt.xlabel('Number of ' + d_type + 's')
    plt.ylabel('Countries')
    # plt.savefig(d_type + '_per_country.png', bbox_inches='tight')  # Uncomment out if it is desired to save the image
    plt.show()


# Try it out
disaster_type_per_country('Drought')


def disasters_per_country():
    """This function produces a count plot for the disasters per country."""
    # Drop the columns which we do not need
    dropped = disasters.drop(['disaster_type'], axis=1)
    # Drop any duplicate rows as these are the same disaster (only a different type) and should not be counted twice
    dropped = dropped.drop_duplicates().sort_values(['country'])

    # Set the size of this plot as it should be quite long
    plt.rc('figure', figsize=(15, 35))
    # Produce the plot and label it appropriately
    sns.countplot(data=dropped, y='country')
    plt.title('Total number of occurrences of disasters for all countries over all years')
    plt.xlabel('Number of disasters')
    plt.ylabel('Countries')
    # plt.savefig('disasters_per_country.png', bbox_inches='tight') # Uncomment out if it is desired to save the image
    plt.show()


# Try it out
disasters_per_country()


def disasters_over_years():
    """This function produces a count plot for the number of disasters that are ongoing during every year."""
    # Set the dates to years
    fixed = fix_years()

    # Drop the columns which we do not need
    dropped = fixed.drop(['disaster_type'], axis=1).drop(['country'], axis=1)
    # Drop any duplicate rows as these are the same disaster (only a different type or in a different country)
    # and should not be counted twice
    dropped = dropped.drop_duplicates()
    # Group the data by their year and count how many disasters were going on in a certain year
    per_date = dropped.groupby(['date']).aggregate(n=('date', 'count'))

    # Set the size of this plot as it will be quite broad
    plt.rc('figure', figsize=(10, 5))
    # Produce the plot and label it appropriately
    sns.lineplot(data=per_date, x='date', y='n')
    plt.title('Time series of the total number of ongoing disasters over the years')
    plt.xlabel('Years')
    plb.xticks(rotation=45)
    plt.ylabel('Number of ongoing disasters')
    # plt.savefig('disasters_over_years.png', bbox_inches='tight')  # Uncomment out if it is desired to save the image
    plt.show()


# Try it out
disasters_over_years()


def disaster_types_over_years():
    """This function produces a count plot for the disaster types occurring over the years."""
    # Set the dates to years
    fixed = fix_years()
    # Drop the columns which we do not need
    dropped = fixed.drop(['country'], axis=1)
    # Drop any duplicate rows as these are the same disaster (only a different country) and should not be counted twice
    dropped = dropped.drop_duplicates().sort_values(['date'])

    # Set the size of this plot as it will be quite big
    plt.rc('figure', figsize=(16, 10))
    # Produce the plot and label it appropriately
    sns.histplot(data=dropped, x='date', hue='disaster_type', multiple='fill')
    plt.title('Proportions of the different disasters over the years')
    plt.xlabel('Years')
    plb.xticks(rotation=45)
    plt.ylabel('Percentage of disasters in the given year')
    # plt.savefig('disaster_types_over_years.png', bbox_inches='tight') # Uncomment out if it is desired to save the image
    plt.show()


# Try it out
disaster_types_over_years()


def plot_heat():
    """plots a geographical heatmap based on the disaster count per country"""
    """Inspired by https://melaniesoek0120.medium.com/data-visualization-how-to-plot-a-map-with-geopandas-in-python
    -73b10dcd4b4b """

    disaster_counts = pd.read_csv("../DataEnrichment/scraped_disaster_counts.csv")

    # 'naturalearth_lowres' is geopandas datasets so we can use it directly
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))

    # rename the columns so that we can merge world with disaster_counts
    world.columns = ['pop_est', 'continent', 'country', 'CODE', 'gdp_md_est', 'geometry']

    world = world.sort_values(by='country', ascending=False)

    # merge world and disaster counts
    merge = pd.merge(world, disaster_counts, on='country')

    # Optional: add raster for worldmap with seas instead of a white background
    # import rasterio.plot
    # raster = rasterio.open("World_map_data/NE1_50M_SR_W.tif")
    #
    # fig, ax = plt.subplots(figsize=(15, 15))
    # rasterio.plot.show(raster, ax=ax)

    # plot confirmed cases world map
    # merge.plot(ax=ax, column='count', scheme="quantiles", edgecolor="lightgrey",
    #            figsize=(25, 20),
    #            legend=True, cmap='Reds')  # coolwarm as alternative
    # plt.title('Disasters per country', fontsize=25)

    # Default simple heatmap plot
    #plot confirmed cases world map
    merge.plot(column='count', scheme="quantiles", edgecolor="lightgrey",
               figsize=(25, 20),
               legend=True, cmap='Reds')  # coolwarm as alternative
    plt.title('Disasters per country', fontsize=25)

    plt.show()


# Try it out
plot_heat()
