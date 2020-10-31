import folium

def show_toronto_area(): 
    top_right = (43.857698, -79.169111)
    top_left = (43.750724, -79.640452)
    bottom_left = (43.577857, -79.541984)
    bottom_right = (43.749704, -79.111260)
    toronto_map = folium.Map(location=[43.7, -79.4], zoom_start=11)

