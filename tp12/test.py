from geopy.geocoders import GoogleV3

# 使用你的 Google API Key
api_key = 'AIzaSyCnbw-OeDr5P5qsEtokjbX1QwCJulnFkgE'
geolocator = GoogleV3(api_key=api_key)

def test_geocode_address(address):
    try:
        location = geolocator.geocode(address)
        if location:
            print(f"Address: {address}")
            print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
        else:
            print(f"Address: {address} could not be geocoded.")
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")

# 测试示例地址
test_geocode_address('Flinders Street Station, Melbourne, Australia')
test_geocode_address('Melbourne Central, Melbourne, Australia')
