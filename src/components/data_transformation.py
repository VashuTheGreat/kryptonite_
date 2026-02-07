import os
import sys
import pandas as pd
import folium

from src.entity.config_entity import DataTransformationConfig
from src.entity.artifact_entity import DataIngestionArtifact,DataTransformationArtifact
from src.exception import MyException
from src.logger import logging
from src.constants import COLORS
from src.constants import copy_js
from branca.element import Element





class DataTransformation:
    def __init__(self, data_transformation_config: DataTransformationConfig):
        try:
            self.data_transformation_config = data_transformation_config
        except Exception as e:
            raise MyException(e, sys)

    async def initiate_data_transformation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataTransformationArtifact:
        try:
            logging.info("Starting data transformation")
            data = pd.read_csv(data_ingestion_artifact.feature_store_path)
            colors = COLORS
            center_lat = data["latitude"].mean()
            center_lon = data["longitude"].mean()



            m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="Esri.WorldImagery")
            m.get_root().html.add_child(Element(copy_js))


            for _, row in data.iterrows():
                raw_time = str(row['acq_time']).split(",")[-1].zfill(4)
                formatted_time = f"{raw_time[:2]}:{raw_time[2:]}"

                popup_html = f"""
                <div style="
                    font-family: Arial;
                    padding:10px;
                    border-radius:10px;
                    background: linear-gradient(135deg,#1f2937,#111827);
                    color:white;
                    width:200px;
                ">
                    <h4 style="margin:0 0 8px 0;color:#60a5fa;">🔥 Fire Alert</h4>

                    <p style="margin:4px 0;">
                        <b>Date:</b> {row['acq_date']}<br>
                        <b>Time:</b> {formatted_time}
                    </p>

                    <p style="margin:4px 0;">
                        <b>Lat:</b> {row['latitude']}<br>
                        <b>Lon:</b> {row['longitude']}
                    </p>

                    <button onclick="copyCoords({row['latitude']}, {row['longitude']})"
                        style="
                            margin-top:6px;
                            padding:6px 10px;
                            border:none;
                            border-radius:6px;
                            background:#3b82f6;
                            color:white;
                            cursor:pointer;
                            font-size:12px;
                        ">
                        📋 Copy Coordinates
                    </button>
                </div>
                """

                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=4,
                    color=colors.get(row["confidence"], "yellow"),
                    fill=True,
                    fill_opacity=0.7,
                    popup=popup_html
                ).add_to(m)


            os.makedirs(os.path.dirname(self.data_transformation_config.map_file_path), exist_ok=True)
            logging.info(f"Data transformation artifact created: {self.data_transformation_config.map_file_path}")
            file_name = self.data_transformation_config.map_file_path
            m.save(file_name)
            logging.info("Data transformation completed")
            logging.info(f"Data transformation artifact created: {self.data_transformation_config.map_file_path}")

            return DataTransformationArtifact(
                map_file_path=file_name,
                train_file_path=data_ingestion_artifact.train_file_path,
                test_file_path=data_ingestion_artifact.test_file_path,
                feature_store_path=data_ingestion_artifact.feature_store_path
            )
        except Exception as e:
            raise MyException(e, sys)
