import os
import io
import sys
import base64
import requests
import pandas as pd
import geopandas
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO
from dotenv import load_dotenv
from src.utils.main_utils import read_yaml_file
from src.logger import logging
from src.exception import MyException
from typing import List

# Bounding box for India and its states
COUNTRY_BBOX = {
    "india": "68.0,6.0,97.0,36.0"
}

INDIA_STATE_BBOX = {
    "up": [77.1, 23.5, 84.5, 31.5],
    "mp": [74.0, 21.0, 82.0, 26.0],
    "maharashtra": [72.5, 17.0, 80.0, 22.0],
    "bihar": [83.0, 24.0, 88.0, 27.5],
    "rajasthan": [69.0, 23.3, 78.0, 30.1],
    "karnataka": [74.0, 11.5, 78.5, 18.5],
    "tamil_nadu": [76.0, 8.0, 80.3, 13.5],
    "gujarat": [68.0, 20.0, 74.0, 24.0],
    "west_bengal": [85.0, 21.5, 89.9, 27.1],
    "assam": [89.4, 24.0, 96.0, 28.2],
    "odisha": [81.0, 17.5, 87.5, 22.5],
    "jharkhand": [83.0, 22.0, 87.0, 25.0],
    "punjab": [73.5, 29.5, 76.9, 32.3],
    "haryana": [74.0, 27.5, 77.5, 30.9],
    "kerala": [74.0, 8.0, 77.5, 12.5],
    "telangana": [77.0, 15.5, 81.0, 19.0],
    "andhra_pradesh": [77.0, 13.0, 84.0, 19.0],
    "chhattisgarh": [80.0, 17.5, 84.5, 24.0],
    "himachal_pradesh": [75.8, 30.3, 79.5, 33.3],
    "uttarakhand": [77.5, 28.8, 81.0, 31.3],
    "nagaland": [93.3, 25.0, 95.3, 27.0],
    "manipur": [93.0, 23.8, 94.8, 25.8],
    "mizoram": [92.5, 21.5, 93.5, 24.5],
    "tripura": [91.0, 22.5, 92.0, 24.0],
    "sikkim": [88.0, 27.0, 88.9, 28.0],
    "arunachal_pradesh": [91.2, 26.9, 97.1, 29.5],
    "goa": [73.6, 15.0, 74.2, 15.7],
    "chandigarh": [76.8, 30.7, 76.9, 30.8],
    "delhi": [77.1, 28.4, 77.3, 28.9],
    "puducherry": [79.7, 11.9, 79.9, 12.0],
    "ladakh": [76.0, 32.0, 80.0, 37.0],
    "jammu_kashmir": [72.6, 32.0, 75.0, 36.0],
    "meghalaya": [90.0, 25.0, 92.0, 26.5],
}

class Analyser:
    def __init__(self):
        load_dotenv()
        self.MAP_KEY = os.getenv("MAP_KEY")
        if not self.MAP_KEY:
            raise ValueError("MAP_KEY not found in .env file")
        self.state_bbox_dict = INDIA_STATE_BBOX

    async def init_config(self, country: str = "india"):
        try:
            config_path = "src/configuration/region.yaml"
            if os.path.exists(config_path):
                config = await read_yaml_file(file_path=config_path)
                # Handle nested structure: {country: {state: bbox}}
                if country in config:
                    self.state_bbox_dict = config[country]
                else:
                    self.state_bbox_dict = config
        except Exception as e:
            logging.error(f"Error loading config: {e}")

    async def assign_state_to_fires(self, data: pd.DataFrame):
        data["state"] = "unknown"
        for state, bbox in self.state_bbox_dict.items():
            # Handle string bbox like "77,23,84,31"
            if isinstance(bbox, str):
                bbox = [float(x.strip()) for x in bbox.split(",")]
            
            if len(bbox) != 4:
                logging.warning(f"Invalid bbox for state {state}: {bbox}")
                continue

            min_lon, min_lat, max_lon, max_lat = bbox
            mask = (
                (data.longitude >= min_lon) &
                (data.longitude <= max_lon) &
                (data.latitude >= min_lat) &
                (data.latitude <= max_lat)
            )
            data.loc[mask, "state"] = state
        return data

    async def fetch_firms_country_data(self, country: str, source="VIIRS_SNPP_NRT", day_range=3):
        country = country.lower()
        if country not in COUNTRY_BBOX:
            raise ValueError(f"Bounding box not found for country: {country}")

        area = COUNTRY_BBOX[country]
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{self.MAP_KEY}/{source}/{area}/{day_range}"
        
        logging.info(f"Fetching FIRMS data for {country} from: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise ConnectionError(f"Error: {response.status_code} - {response.text}")

        df = pd.read_csv(StringIO(response.text))
        required_cols = ["latitude", "longitude", "acq_date", "acq_time", "confidence"]
        # Ensure only required columns are kept if they exist
        existing_cols = [c for c in required_cols if c in df.columns]
        df = df[existing_cols]
        return df

    def _get_plot_base64(self):
        """Helper to convert the current matplotlib plot to a base64 string."""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return img_str

    async def analyse(self, country: str = "india")->List[str]:
        """
        Performs analysis on fire data for a given country and returns a list of base64-encoded plot strings.
        """
        try:
            # 1. Fetch Data
            df = await self.fetch_firms_country_data(country)
            
            # 2. Assign States
            df = await self.assign_state_to_fires(df)
            
            plots_base64 = []

            # 3. Visualization 1: Count of Fires by State and Confidence
            # Ensure we have state and confidence
            if 'state' in df.columns and 'confidence' in df.columns:
                p = df.groupby(['state', 'confidence']).size().reset_index(name='count')
                plt.figure(figsize=(15, 6))
                sns.barplot(data=p, x='state', y='count', hue='confidence')
                plt.xticks(rotation=45)
                plt.title(f"Fire Intensity Distribution by State ({country.capitalize()})")
                plots_base64.append(self._get_plot_base64())

            # 4. Visualization 2: Top 5 States with Most Fire Activity
            if 'state' in df.columns and not df.empty:
                state_counts = df['state'].value_counts().head(5)
                if not state_counts.empty:
                    plt.figure(figsize=(10, 6))
                    # Use index and values directly for sns.barplot
                    sns.barplot(x=state_counts.index, y=state_counts.values)
                    plt.title("Top 5 Regions with Highest Fire Activity")
                    plt.ylabel("Total Fire Incidents")
                    plots_base64.append(self._get_plot_base64())

            # 5. Visualization 3: High Confidence Fires Temporal Trend
            if 'confidence' in df.columns and 'acq_date' in df.columns:
                # FIRMS uses h/l/n or numbers for confidence. Let's try to be flexible.
                high_conf_df = df[df['confidence'].astype(str).str.lower().isin(['h', 'high', '100', '90'])]
                if not high_conf_df.empty:
                    time_df = high_conf_df.groupby('acq_date').size()
                    plt.figure(figsize=(12, 6))
                    sns.lineplot(x=time_df.index, y=time_df.values, marker='o')
                    plt.title("Temporal Trend of High-Confidence Fire Incidents")
                    plt.xlabel("Acquisition Date")
                    plt.ylabel("Count")
                    plt.xticks(rotation=45)
                    plots_base64.append(self._get_plot_base64())

            return plots_base64

        except Exception as e:
            logging.error(f"Analysis failed: {e}")
            raise MyException(e, sys)
