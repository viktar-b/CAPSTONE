import folium 
import pyproj
import numpy as np

class TorontoCircles: 

    circle_diameter = None

    def __init__(self, top_right, top_left, bot_left, bot_right):

        self.top_right = top_right 
        self.top_left = top_left
        self.bot_left = bot_left
        self.bot_right = bot_right
        
        self.x_1, self.y_1 = self.lonlat_to_xy(*top_left)
        self.x_2, self.y_2 = self.lonlat_to_xy(*top_right)
        self.x_3, self.y_3 = self.lonlat_to_xy(*bot_left)
        self.x_4, self.y_4 = self.lonlat_to_xy(*bot_right)

        self.max_horizontal_distance = np.sqrt((self.y_1-self.y_2)**2 + (self.x_1 - self.x_2)**2)
        self.max_vertical_distance = np.sqrt((self.y_1-self.y_3)**2 + (self.x_1 - self.x_3)**2)

        self.top_horizontal_gradient = np.divide( self.y_2 - self.y_1, self.x_2 - self.x_1)
        self.top_horizontal_bias = self.y_1 - self.top_horizontal_gradient*self.x_1 

        self.vertical_line_gradient = -self.top_horizontal_gradient
        self.vertical_line_bias = self.y_1 + self.top_horizontal_gradient*self.x_1 
    
    def create_toronto_map(self):

        boundaries = [  
            self.top_right, 
            self.top_left, 
            self.bot_left, 
            self.bot_right,
            self.top_right 
        ]

        toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=11)
        
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

    def display_circles(self):
        
        toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=10)

        latlon_data = self.get_latlon_data()
        for lat, lon in latlon_data:
            folium.Circle([lat, lon], radius= self.circle_diameter/2, color='blue', fill=False).add_to(toronto_map)
        
        return toronto_map

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

        horizontal_add_x = (self.circle_diameter**2/(1+self.top_horizontal_gradient**2))**0.5
        horizontal_add_y = self.top_horizontal_gradient*horizontal_add_x
        distance__from_hor_line = np.sqrt(3)/2*self.circle_diameter

        vertical_add_y = (distance__from_hor_line**2/(1+self.vertical_line_gradient**2))**0.5
        vertical_add_x = self.vertical_line_gradient*vertical_add_y

        vertical_number_of_elements = int(self.max_vertical_distance//(distance__from_hor_line*2))
        horizontal_number_of_elements = int(self.max_horizontal_distance//self.circle_diameter)
        
        xy_coord = []
        for i in range(vertical_number_of_elements):
            if i%2==0:
                x, y = self.x_1-i*vertical_add_x , self.y_1-i*vertical_add_y
                for j in range(horizontal_number_of_elements):
                    xy_coord.append((x + j*horizontal_add_x, y + j*horizontal_add_y))
            if i%2!=0:
                x, y = self.x_1-i*vertical_add_x+horizontal_add_x/2, self.y_1-i*vertical_add_y+horizontal_add_y/2
                for j in range(horizontal_number_of_elements):
                    xy_coord.append((x + j*horizontal_add_x, y + j*horizontal_add_y))

        print(len(xy_coord))
        bot_line_gradient = np.divide( self.y_4 - self.y_3, self.x_4 - self.x_3)
        bot_horizontal_bias = self.y_4 - bot_line_gradient*self.x_4 

        xy_filtered = []
        for x_map, y_map in xy_coord:
            y_line = x_map*bot_line_gradient+bot_horizontal_bias
            if y_line < y_map: 
                xy_filtered.append((x_map, y_map))
        
        return xy_filtered

    def get_latlon_data(self):
        xy_filtered = self.get_xy_data()
        latlon_data = [self.xy_to_latlon(x,y) for x, y in xy_filtered]
        return latlon_data

 

    

