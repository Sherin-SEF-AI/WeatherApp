import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QListWidget, QComboBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage
from io import BytesIO
from PIL import Image

class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.last_lat = None
        self.last_lng = None

    def initUI(self):
        self.setWindowTitle('Advanced Weather Application')
        self.setGeometry(100, 100, 500, 600)

        # Main layout
        self.layout = QVBoxLayout()

        # Address input
        self.address_input = QLineEdit(self)
        self.address_input.setPlaceholderText('Enter Address')
        self.layout.addWidget(self.address_input)

        # Unit selector
        self.unit_selector = QComboBox(self)
        self.unit_selector.addItems(['Celsius', 'Fahrenheit'])
        self.layout.addWidget(self.unit_selector)

        # Search button
        self.search_button = QPushButton('Get Weather', self)
        self.search_button.clicked.connect(self.get_weather_for_address)
        self.layout.addWidget(self.search_button)

        # Result label for current weather
        self.result_label = QLabel('Weather information will be displayed here.', self)
        self.result_label.setWordWrap(True)
        self.layout.addWidget(self.result_label)

        # Icon label for weather condition
        self.icon_label = QLabel(self)
        self.layout.addWidget(self.icon_label)

        # Forecast label
        self.forecast_label = QLabel('7-Day Forecast:', self)
        self.forecast_label.setWordWrap(True)
        self.layout.addWidget(self.forecast_label)

        # Search history
        self.history_list = QListWidget(self)
        self.layout.addWidget(self.history_list)

        # Favorites list
        self.favorites_list = QListWidget(self)
        self.layout.addWidget(self.favorites_list)

        # Add to favorites button
        self.add_favorite_button = QPushButton('Add to Favorites', self)
        self.add_favorite_button.clicked.connect(self.add_to_favorites)
        self.layout.addWidget(self.add_favorite_button)

        # Save button
        self.save_button = QPushButton('Save Weather Info', self)
        self.save_button.clicked.connect(self.save_weather_info)
        self.layout.addWidget(self.save_button)

        # Set layout
        self.setLayout(self.layout)

        # Timer for auto-refresh (every 10 minutes)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_weather)
        self.timer.start(600000)  # 10 minutes in milliseconds

        # Connect favorite list click event
        self.favorites_list.itemClicked.connect(self.show_favorite_weather)

    def get_geolocation(self, address):
        url = "https://map-geocoding.p.rapidapi.com/json"
        querystring = {"address": address}
        headers = {
            "x-rapidapi-key": "2d7198105fmsha78df4c828aea6ep182ce4jsn6a513052a904",  # Replace with your actual RapidAPI key
            "x-rapidapi-host": "map-geocoding.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        if data and "results" in data and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            return None, None

    def get_weather(self, lat, lng):
        url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
        unit = "C" if self.unit_selector.currentText() == "Celsius" else "F"
        querystring = {"q": f"{lat},{lng}", "days": "7", "aqi": "no", "alerts": "no"}
        headers = {
            "x-rapidapi-key": "2d7198105fmsha78df4c828aea6ep182ce4jsn6a513052a904",  # Replace with your actual RapidAPI key
            "x-rapidapi-host": "weatherapi-com.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        return data if data else None

    def display_weather(self, data):
        if not data:
            QMessageBox.warning(self, "Error", "Failed to get weather data.")
            return
        
        location = data['location']['name']
        country = data['location']['country']
        current = data['current']
        temp = current['temp_c'] if self.unit_selector.currentText() == "Celsius" else current['temp_f']
        condition = current['condition']['text']
        humidity = current['humidity']
        wind_kph = current['wind_kph']
        wind_mph = current['wind_mph']
        icon_url = current['condition']['icon']

        weather_info = f"Weather in {location}, {country}:\n\n" \
                       f"Temperature: {temp}°{self.unit_selector.currentText()[0]}\n" \
                       f"Condition: {condition}\n" \
                       f"Humidity: {humidity}%\n" \
                       f"Wind Speed: {wind_kph} kph ({wind_mph} mph)"

        self.result_label.setText(weather_info)

        # Display weather icon
        response = requests.get(f"http:{icon_url}")
        image = Image.open(BytesIO(response.content))
        image = image.convert("RGBA")
        image_data = image.tobytes("raw", "RGBA")
        
        qimage = QImage(image_data, image.width, image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        self.icon_label.setPixmap(pixmap)

        # Display 7-Day forecast
        forecast_text = "7-Day Forecast:\n"
        for day in data['forecast']['forecastday']:
            date = day['date']
            condition = day['day']['condition']['text']
            max_temp = day['day']['maxtemp_c'] if self.unit_selector.currentText() == "Celsius" else day['day']['maxtemp_f']
            min_temp = day['day']['mintemp_c'] if self.unit_selector.currentText() == "Celsius" else day['day']['mintemp_f']
            forecast_text += f"{date}: {condition}, Max: {max_temp}°, Min: {min_temp}°\n"

        self.forecast_label.setText(forecast_text)

        # Update search history
        self.history_list.addItem(f"{location}, {country} - {temp}°{self.unit_selector.currentText()[0]}")

    def get_weather_for_address(self):
        address = self.address_input.text()
        if address:
            lat, lng = self.get_geolocation(address)
            if lat is not None and lng is not None:
                self.last_lat = lat
                self.last_lng = lng
                weather_data = self.get_weather(lat, lng)
                self.display_weather(weather_data)
            else:
                QMessageBox.warning(self, "Error", "Failed to get geolocation.")
        else:
            QMessageBox.warning(self, "Input Error", "Please enter an address.")

    def refresh_weather(self):
        if self.last_lat is not None and self.last_lng is not None:
            weather_data = self.get_weather(self.last_lat, self.last_lng)
            self.display_weather(weather_data)

    def add_to_favorites(self):
        current_location = self.result_label.text().splitlines()[0]
        if current_location and current_location not in [self.favorites_list.item(i).text() for i in range(self.favorites_list.count())]:
            self.favorites_list.addItem(current_location)
        else:
            QMessageBox.warning(self, "Error", "Location is already in favorites or no location selected.")

    def show_favorite_weather(self, item):
        address = item.text().split(" - ")[0]  # Extract the location name
        lat, lng = self.get_geolocation(address)
        if lat is not None and lng is not None:
            weather_data = self.get_weather(lat, lng)
            self.display_weather(weather_data)

    def save_weather_info(self):
        # Get the text from the result label and forecast label
        weather_info = self.result_label.text()
        forecast_info = self.forecast_label.text()

        # Combine both pieces of information
        full_info = f"{weather_info}\n\n{forecast_info}"

        # Open a file dialog to choose where to save the file
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Weather Info", "", "Text Files (*.txt);;All Files (*)", options=options)
        
        if file_name:
            try:
                with open(file_name, 'w') as file:
                    file.write(full_info)
                QMessageBox.information(self, "Success", f"Weather information saved to {file_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WeatherApp()
    ex.show()
    sys.exit(app.exec_())

