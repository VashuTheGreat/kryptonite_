import fastapi

router=fastapi.APIRouter()
from src.pipeline.analyser_pipeline import Data_Analyser_pipeline
@router.get("/data_analyser")
async def data_analyser(country:str="india"):
    data_analyser_pipeline=Data_Analyser_pipeline(country=country)
    data=await data_analyser_pipeline.start_data_analyser()
    return data
