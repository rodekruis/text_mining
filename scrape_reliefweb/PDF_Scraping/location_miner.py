import geograpy


def find_cities(filename, country):
    """This function mines the summary from the disaster webpage and returns the mentioned cities of the country
    that was hit by the disaster"""

    places = geograpy.get_geoPlace_context(filename)  # get geo data

    return places.country_cities.get(country)  # return the cities from the country of the dictionary
