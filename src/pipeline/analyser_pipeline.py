import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.getcwd())
from dotenv import load_dotenv
load_dotenv()

from src.components.data_ingestion import DataIngestion
from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact
from src.components.data_transformation import DataTransformation
from src.entity.config_entity import DataTransformationConfig
from src.entity.artifact_entity import DataTransformationArtifact
from src.entity.config_entity import DataValidationConfig, ModelTrainerConfig
from src.components.data_analyser import Analyser
from src.logger import logging
from src.exception import MyException
from typing import List

class Data_Analyser_pipeline:
    def __init__(self, country: str = "india"):
        self.country = country
        self.data_analyser = Analyser()

    async def init_config(self):
        await self.data_analyser.init_config(country=self.country)
    async def start_data_analyser(self)->List[str]:
        try:
            logging.info("Entered the start_data_analyser method of TrainPipeline class")
            data=await self.data_analyser.analyse()
            return data
        except Exception as e:
            raise MyException(e, sys) from e

  