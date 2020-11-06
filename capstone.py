import folium
import pyproj
import numpy as np
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
    client_id = 'ULGA5LTQONIWZ5ULCDROWAYVYJ0ZOI0C35CLVMG12JJAKCFN' 
    client_secret = 'VMEKZXMMCBO3RWK0IFRKV5KXBABWQ1EQ3J2ACE53UAR5SVWC'
    
    #"Asian restaurant" category. 
    #Obtained from https://developer.foursquare.com/docs/build-with-foursquare/categories/
    venue_category = '4bf58dd8d48988d142941735'

    def __init__(self, latlon_coordinates, circle_diameter):
        self.latlon_coordinates = latlon_coordinates
        self.search_radius = np.sqrt(3)/2*circle_diameter

    def get_raw_requests(self):
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

    # def get_info(self):
    #     loaded = False
    #     try:
    #         restaurants = pd.read_csv('restaurants.csv')
    #         chinese_restaurants = pd.read_csv('restaurants.csv')
    #         location_restaurants = pd.read_csv('restaurants.csv')
    #         print('Restaurant data loaded from existing csv files.')
    #         loaded = True
    #     except:
         
    #         # restaurants, chinese_restaurants, location_restaurants = self.get_restaurants(self.latitudes, self.longitudes)    
    #         # # Let's persists this in local file system
            
    #         # with open('chinese_restaurants.csv', 'wb') as f:
    #         #     pickle.dump(chinese_restaurants, f)
    #         # with open('location_restaurants.csv', 'wb') as f:
    #         #     pickle.dump(location_restaurants, f)
        
    #     return restaurants, chinese_restaurants, location_restaurants
    
    def get_restaurants(self,lats, lons):
        restaurants = {}
        chinese_restaurants = {}
        location_restaurants = []

        print('Obtaining venues around candidate locations:', end='')
        for lat, lon in zip(lats, lons):
            #Using radius=350 to meke sure we have overlaps/full coverage so we don't miss any restaurant
            #(we're using dictionaries to remove any duplicates resulting from area overlaps)
            venues = self.get_venues_near_location(
                lat, 
                lon, 
                self.food_category, 
                self.foursquare_client_id, 
                self.foursquare_client_secret, 
                radius= self.radius, 
                limit=100
            )
            area_restaurants = []
            for venue in venues:
                venue_id = venue[0]
                venue_name = venue[1]
                venue_categories = venue[2]
                venue_latlon = venue[3]
                venue_address = venue[4]
                venue_distance = venue[5]
                is_res, is_italian = self.is_restaurant(venue_categories, specific_filter=self.chinese_restaurant_categories)
                if is_res:
                    x, y = Toronto.lonlat_to_xy(venue_latlon[1], venue_latlon[0])
                    restaurant = (venue_id, venue_name, venue_latlon[0], venue_latlon[1], venue_address, venue_distance, is_italian, x, y)
                    if venue_distance<=300:
                        area_restaurants.append(restaurant)
                    restaurants[venue_id] = restaurant
                    if is_italian:
                        chinese_restaurants[venue_id] = restaurant
            location_restaurants.append(area_restaurants)
            print(' .', end='')
        print(' done.')
        return restaurants, chinese_restaurants, location_restaurants

    def get_venues_near_location(self, lat, lon, category, client_id, client_secret, radius=500, limit=100):
        version = '20180724'
        url = f'https://api.foursquare.com/v2/venues/explore?'\
                                                f'client_id={client_id}'\
                                                f'&client_secret={client_secret}'\
                                                f'&v={version}'\
                                                f'&ll={lat},{lon}'\
                                                f'&categoryId={category}'\
                                                f'&radius={radius}'\
                                                f'&limit={limit}'
        try:
            results = requests.get(url).json()['response']['groups'][0]['items']
            venues = [(item['venue']['id'],
                    item['venue']['name'],
                    self.get_categories(item['venue']['categories']),
                    (item['venue']['location']['lat'], item['venue']['location']['lng']),
                    item['venue']['location']['distance']) for item in results]        
        except:
            venues = []
        return venues

    @staticmethod
    def is_restaurant(categories, specific_filter=None):
        restaurant_words = ['restaurant', 'diner', 'taverna', 'steakhouse']
        restaurant = False
        specific = False
        for c in categories:
            category_name = c[0].lower()
            category_id = c[1]
            for r in restaurant_words:
                if r in category_name:
                    restaurant = True
            if 'fast food' in category_name:
                restaurant = False
            if not(specific_filter is None) and (category_id in specific_filter):
                specific = True
                restaurant = True
        return restaurant, specific

    @staticmethod
    def get_categories(categories):
        return [(cat['name'], cat['id']) for cat in categories]

    def requestlist_to_dataframe(self, list):
        pass


class GetPostcodeWikiInfo:
    pass
# url = "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M"
# wiki_df = pd.read_html(requests.get(url).text)[0]
# wiki_df = wiki_df[wiki_df['Borough'] != 'Not assigned']
# coord_df = pd.read_csv('geospatial-coordinates.csv')
# wiki_df = wiki_df.merge(coord_df, how='left', on='Postal Code')
# wiki_df.head()




# import folium

# toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=11)
# toronto_map.choropleth(
#     geo_data='Toronto2.geojson',
#     fill_color='Yellow', 
#     line_color='Red',
#     fill_opacity=0.7, 
#     line_opacity=1,
#     reset=True
# )

# postcodes = folium.map.FeatureGroup()

# for lat, lng, in zip(wiki_df.Latitude, wiki_df.Longitude):
#     postcodes.add_child(
#         folium.features.CircleMarker(
#             [lat, lng],
#             radius=5, # define how big you want the circle markers to be
#             color='yellow',
#             fill=True,
#             fill_color='blue',
#             fill_opacity=0.6
#         )
#     )

# # add pop-up text to each marker on the map
# latitudes = list(wiki_df.Latitude)
# longitudes = list(wiki_df.Longitude)
# labels = list(wiki_df['Postal Code'])

# for lat, lng, label in zip(latitudes, longitudes, labels):
#     folium.Marker([lat, lng], popup=label).add_to(toronto_map)    
    
# # add incidents to map
# toronto_map.add_child(postcodes)


# def unpack_name_categories(row):
#     row = eval(row)
#     if len(row) == 0:
#         return np.NaN
#     else:
#         return row[0]['name'] 



# #creating a template for final results of SEARCH query 
# columns = ['VenueID', 'Venue', 'CategoryName', 'CategoryShortName', 'Address', 'PostCode', 'Longitude', 'Lattitude']
# restaurants_df = pd.DataFrame(columns=columns)



# #writing a function that extract needed keys and values from categories column 
# restaurants_df.VenueID = unprocessed_df.id
# restaurants_df.Venue = unprocessed_df.name
# restaurants_df.CategoryName = unprocessed_df.apply(lambda x: unpack_name_categories(x.categories), axis=1)
# restaurants_df.CategoryShortName = unprocessed_df.apply(lambda x: unpack_shortName_categories(x.categories), axis=1)
# restaurants_df.Address = unprocessed_df.apply(lambda x: unpack_address_location(x.location), axis=1)
# restaurants_df.PostCode = unprocessed_df.apply(lambda x: unpack_postcode_location(x.location), axis=1)
# restaurants_df.Longitude = unprocessed_df.apply(lambda x: unpack_lng_location(x.location), axis=1)
# restaurants_df.Lattitude = unprocessed_df.apply(lambda x: unpack_lat_location(x.location), axis=1)







    

