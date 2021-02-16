import unittest
import pandas as pd
from project.DataEnrichment.visualisation import fix_dates, fix_years

pd.set_option('display.max_rows', None)


class TestSuite(unittest.TestCase):

    def test_fix_dates(self):
        """This function checks whether a time period is actually transformed to months."""
        # Read the data
        disasters = pd.read_csv("../DataEnrichment/all_disasters.csv")

        # Get an entry of which we know the date was not correctly specified
        before = disasters[disasters.disaster_type == 'Drought']
        before = before[before.country == 'Guatemala']
        before = before[before.name == 'Guatemala: Food Insecurity 2012-2013']

        # Correct the data
        fixed = fix_dates()
        changed = fixed[fixed.disaster_type == 'Drought']
        changed = changed[changed.country == 'Guatemala']
        changed = changed[changed.name == 'Guatemala: Food Insecurity 2012-2013']

        return before.size * 24 == changed.size  # We know that for this specific instance it is split into 24 months

# Manual test of fix_dates():
# Additionally to automatically testing whether the period of years has been transformed to multiple rows for each
# month of those years, we also manually checked whether the right months were being entered into those rows.
# By printing out the whole frame for a disaster of which the date had been specified as a period, after transforming
# it, this was found to be the case.

    def test_fix_years(self):
        """This function tests whether the dates for the changed dataframe are all specified as years."""
        # Format the dates according to the function
        formatted = fix_years()

        for index, row in formatted.iterrows(): # For every disaster
            date = int(row['date']) # Get the year and transform it to an integer
            if not 0 < date < 2050: # Check if the year lies in a possible range
                return False

        return True

# Manuel test of disaster_type_per_country(d_type):
# The production of this plot has been tested by hand through running the function for different types of disasters.
# Presetting the size of the plot was not necessary in this case as the automatically set sizes looks quite nice
# already. The filtering has been checked by simply printing the head of the produced dataframe and checking whether
# only disasters of the specified type were added, which also was the case.

# Manuel test of disasters_per_country()::
# The production of this plot has been tested by hand through running the function. Presetting the size of the plot was
# necessary in this case as the plot turned out to be quite long, otherwise one could not read the country names.
# Again, the filtering has been checked by simply printing the head of the produced dataframe and checking whether
# only different disasters with different names for different countries were included (not simply of different types).
# Also, one could see that duplicates were indeed removed.

# Manuel test of disasters_over_years()::
# The production of this plot has been tested by hand through running the function. Presetting the size of the plot was
# necessary in this case as the plot turned out to be quite broad. For this purpose, the x-labels have been rotated as
# well. Again, the filtering has been checked by simply printing the head of the produced dataframe and checking whether
# only ongoing disasters with different names were counted for every year (not simply of different types or countries).
# Also, one could see that duplicates were indeed removed.

# Manual test of  disaster_types_over_years():
# The production of this plot has been tested by hand through running the function. Presetting the size of the plot was
# necessary in this case as the plot turned out to be quite broad again. For this purpose, the x-labels have been
# rotated as well. Again, the dropping of country specific observations filtering has been checked by simply printing
# the head of the produced dataframe and checking whether duplicates were indeed removed.

# Manually test def plot_heat()
# the objective of this function is to plot a geographical heatmap
# the disaster counts per country should be displayed upon a world map taken from geopandas
# we visually inspect missing countries, that can be due to a different naming between our
# scraped dataset and the world map dataset
# these inefficiencies are resolved as much as possible
# we run the code and see a geographical map with colors based on disaster count

if __name__ == "__main__":
    PATH = "project/DataEnrichment/visualisation.py"

    unittest.main()
