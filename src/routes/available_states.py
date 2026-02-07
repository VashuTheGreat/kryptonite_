from src.utils.main_utils import read_yaml_file

import fastapi
from src.exception import MyException
import sys
router=fastapi.APIRouter()

@router.get("/get_available_states")

async def get_available_states():
    try:
        data=await read_yaml_file(file_path="src/configuration/region.yaml")
        print(data)
        data=list(data['india'].keys())
        return {"data":data}
    except Exception as e:
        MyException(e,sys)