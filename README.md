# AI Sustainability Dashboard

## Overview
The **AI Sustainability Dashboard** is an interactive platform that leverages Artificial Intelligence to promote sustainability by analyzing real-time data on pollution, energy consumption, and carbon emissions. It offers actionable insights and recommendations to help individuals and organizations reduce their environmental impact.



## Features
- **Real-Time Pollution Monitoring**: Track air quality data for any location.
- **Behavioral Analysis**: Analyze activities like shopping and commuting to estimate carbon footprints.
- **Forecasting Trends**: Predict pollution and energy trends using machine learning.
- **High-Emission Zone Clustering**: Identify zones with high pollution levels.
- **Interactive Visualizations**: Dynamic graphs and maps for data exploration.
- **EV Charging Station Locator**: Find nearby charging stations for electric vehicles.

## Deployment
The dashboard is live and accessible at: [AI Sustainability Dashboard](https://aisustainabilitydashboard.streamlit.app/)

## Installation
Follow these steps to set up the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/stanleymay20/ai_sustainability_dashboard.git
   ```

2. Navigate to the project directory:
   ```bash
   cd ai_sustainability_dashboard
   ```

3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the app locally:
   ```bash
   streamlit run sustainability_dashboard.py
   ```

## API Integration
The dashboard integrates the following APIs:
- **OpenWeatherMap**: For air quality data.
- **AQICN**: For real-time AQI data.
- **Carbon Interface**: For vehicle carbon emissions.
- **ElectricityMap**: For electricity grid carbon intensity.

## Key Technologies
- **Python**
- **Streamlit**: Interactive UI
- **Plotly**: Data visualization
- **Folium**: Geospatial mapping
- **Machine Learning**: For forecasting and clustering

## Usage
1. Launch the app locally or visit the deployment URL.
2. Enter a city or location details to get pollution data.
3. Explore predictions and recommendations to reduce your environmental footprint.

## Contributions
Contributions are welcome! Follow these steps:
1. Fork the repository.
2. Create a new branch (`feature/new-feature`).
3. Commit your changes.
4. Push the branch and open a pull request.

## License
This project is licensed under the [MIT License](LICENSE).

## Author
Developed by **Stanley Osei-Wusu**. Reach out for feedback or collaboration opportunities!

## References
- [OpenWeatherMap API Documentation](https://openweathermap.org/api)
- [AQICN API Documentation](https://aqicn.org/api/)
- [Carbon Interface API Documentation](https://www.carboninterface.com/docs)
- [ElectricityMap API Documentation](https://electricitymap.org/api)
