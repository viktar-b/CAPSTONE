import folium 


def show_toronto_map(topright, topleft, bottomleft, bottomrigth):

    boundaries = [  
        topright, 
        topleft,
        bottomleft,
        bottomrigth,
        topright
    ]

    toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=10)
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

def print_this():
    return 'qwe'

