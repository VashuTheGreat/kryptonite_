import os
import sys

from pandas import DataFrame
from sklearn.model_selection import train_test_split

from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact
from src.exception import MyException
from src.logger import logging
from src.data_access.fire_data import FireDataFetcher

class Analyser:
    def __init__(self):
        pass
    async def init_config(self):
        pass