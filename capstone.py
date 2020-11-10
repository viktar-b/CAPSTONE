import folium
import pyproj
import numpy as np
import pandas as pd 
import requests
import pickle

class Toronto: 

    circle_diameter = None
    latlon_list_for_circles = None  
    
    def __init__(self, top_right, top_left, bot_left, bot_right):
        self.top_left = top_left
        self.top_right = top_right 
        self.bot_left = bot_left
        self.bot_right = bot_right
        
    
    def display_toronto_map(self, zoom_start=11, display_boundaries=True):
        boundaries = [  
            self.top_right, 
            self.top_left, 
            self.bot_left, 
            self.bot_right,
            self.top_right 
        ]
        toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=zoom_start)
        if display_boundaries:
            toronto_map.choropleth(
                geo_data='Toronto2.geojson',
                fill_color='Yellow', 
                line_color='Red',
                fill_opacity=0.9, 
                line_opacity=0.1,
                reset=True
            )
        folium.PolyLine(boundaries, color="red", weight=2.5, opacity=1).add_to(toronto_map)
        return toronto_map

    def display_circles(self, latlon_data, zoom_start=10):
        toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=zoom_start)
        for lat, lon in latlon_data:
            folium.Circle([lat, lon], radius= self.circle_diameter/2, color='blue', fill=False).add_to(toronto_map)
        return toronto_map

    
    def display_toronto_postcode(self):
        pass

    def get_latlon_data(self):
        xy_filtered = self.get_xy_data()
        latlon_data = [self.xy_to_latlon(x,y) for x, y in xy_filtered]
        self.latlon_list_for_circles = latlon_data
        return latlon_data

    @staticmethod
    def lonlat_to_xy(lat, lon):
        proj = pyproj.Proj("+proj=utm +zone=17N, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
        xy = proj(lon, lat)
        return xy

    @staticmethod
    def xy_to_latlon(x, y):
        proj = pyproj.Proj("+proj=utm +zone=17N, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
        lon, lat = proj(x, y, inverse=True)
        return lat, lon
    
    #reassess this method
    def get_xy_data(self):
        x_1, y_1 = self.lonlat_to_xy(*self.top_left)
        x_2, y_2 = self.lonlat_to_xy(*self.top_right)
        x_3, y_3 = self.lonlat_to_xy(*self.bot_left)
        x_4, y_4 = self.lonlat_to_xy(*self.bot_right)

        max_horizontal_distance = np.sqrt((y_1-y_2)**2 + (x_1 - x_2)**2)
        max_vertical_distance = np.sqrt((y_1-y_3)**2 + (x_1 - x_3)**2)

        top_horizontal_gradient = np.divide( y_2 - y_1, x_2 - x_1)
        vertical_line_gradient = -top_horizontal_gradient

        horizontal_add_x = (self.circle_diameter**2/(1+top_horizontal_gradient**2))**0.5
        horizontal_add_y = top_horizontal_gradient*horizontal_add_x
        
        distance__from_hor_line = np.sqrt(3)/2*self.circle_diameter

        vertical_add_y = (distance__from_hor_line**2/(1+vertical_line_gradient**2))**0.5
        vertical_add_x = vertical_line_gradient*vertical_add_y

        vertical_number_of_elements = int(max_vertical_distance//(distance__from_hor_line))
        horizontal_number_of_elements = int(max_horizontal_distance//self.circle_diameter)
        
        xy_coord = []
        for i in range(vertical_number_of_elements):
            if i%2==0:
                x, y = x_1-i*vertical_add_x , y_1-i*vertical_add_y
                for j in range(horizontal_number_of_elements):
                    xy_coord.append((x + j*horizontal_add_x, y + j*horizontal_add_y))
            if i%2!=0:
                x, y = x_1-i*vertical_add_x+horizontal_add_x/2, y_1-i*vertical_add_y+horizontal_add_y/2
                for j in range(horizontal_number_of_elements):
                    xy_coord.append((x + j*horizontal_add_x, y + j*horizontal_add_y))

        bot_line_gradient = np.divide( y_4 - y_3, x_4 - x_3)
        bot_horizontal_bias = y_4 - bot_line_gradient*x_4 

        xy_filtered = []
        for x_map, y_map in xy_coord:
            y_line = x_map*bot_line_gradient+bot_horizontal_bias
            if y_line < y_map: 
                xy_filtered.append((x_map, y_map))
        
        return xy_filtered


class FoursquareSearch:

    version = '20201102'
    limit = 100
    # client_id = '' 
    # client_secret = ''
    
    #"Asian restaurant" category. 
    #Obtained from https://developer.foursquare.com/docs/build-with-foursquare/categories/
    venue_category = '4bf58dd8d48988d142941735'

    def __init__(self, latlon_coordinates, circle_diameter):
        self.latlon_coordinates = latlon_coordinates
        self.search_radius = np.sqrt(3)/2*circle_diameter

    def get_explore_requests(self):
        go_not = input(f"Number of circles is {len(self.latlon_coordinates)} "
                        f"and radius is {int(self.search_radius)}. Print 'go' to procceed")
        if go_not.lower() == 'go':
            list_of_requests = []
            with open(f"radius_{int(self.search_radius)}.txt", "wb") as file:  
                for lat, lon in self.latlon_coordinates:
                    url = f'https://api.foursquare.com/v2/venues/explore?'\
                                                f'client_id={self.client_id}'\
                                                f'&client_secret={self.client_secret}'\
                                                f'&v={self.version}'\
                                                f'&ll={lat},{lon}'\
                                                f'&categoryId={self.venue_category}'\
                                                f'&radius={self.search_radius}'\
                                                f'&limit={self.limit}'

                    list_of_requests.append(requests.get(url).json())
                pickle.dump(list_of_requests, file)
                print("Done")
        else:
            return print('Request was terminated')
    
    @classmethod
    def get_price_tier(self, list_of_venueID):
        go_not = input(f"Number of venues is {len(list_of_venueID)}. Print 'go' to request information.")
        if go_not.lower() == 'go':
            list_of_request = []
            for venue_id in list_of_venueID:
                url = f"https://api.foursquare.com/v2/venues/{venue_id}?"\
                                        f"client_id={self.client_id}"\
                                        f"&client_secret={self.client_secret}"\
                                        f"&v={self.version}"

                list_of_request.append(requests.get(url).json())
            
            with open("a5_venues.txt", "wb") as file:
                pickle.dump(list_of_request, file)

    

    @staticmethod
    def requests_to_dataframe(list_of_requests):
        columns = ['venueID', 'venue_name', 'category_name', 'categoryID', 'address', 'postcode', 'latitude', 'longitude', 'price_tier']
        restaurants_df = pd.DataFrame(columns=columns)

        restaurants_df.venueID = [x['response']['groups'][0]['items'][0]['venue']['id'] for x in list_of_requests]
        restaurants_df.venue_name = [x['response']['groups'][0]['items'][0]['venue']['name'] for x in list_of_requests]
        restaurants_df.category_name = [x['response']['groups'][0]['items'][0]['venue']['categories'][0]['name'] for x in list_of_requests]
        restaurants_df.categoryID = [x['response']['groups'][0]['items'][0]['venue']['categories'][0]['id'] for x in list_of_requests]
        restaurants_df.address = ["".join(x['response']['groups'][0]['items'][0]['venue']['location']['formattedAddress']) \
                                        for x in list_of_requests]
        restaurants_df.latitude = [x['response']['groups'][0]['items'][0]['venue']['location']['lat'] for x in list_of_requests]
        restaurants_df.longitude = [x['response']['groups'][0]['items'][0]['venue']['location']['lng'] for x in list_of_requests]

        list_postcodes = []
        for x in list_of_requests: 
            try:
                list_postcodes.append(x['response']['groups'][0]['items'][0]['venue']['location']['postalCode'])
            except:
                list_postcodes.append(np.NaN)

        restaurants_df.postcode = list_postcodes
        restaurants_df = restaurants_df.drop_duplicates(subset='venueID')
        restaurants_df = restaurants_df.reset_index(drop=True)
        return restaurants_df
