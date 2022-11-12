import os
import sys
import importlib
import subprocess
import tempfile

from functools import lru_cache
from fastapi import FastAPI
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict

from sdRDM import DataModel

CACHE_SIZE = 20

# * Settings
app = FastAPI(title="Software-driven RDM Application Service", version="0.1", docs_url="/")

# ! Types
class ServiceTemplate(BaseModel):
    data: Dict = Field(
        ...,
        description="Data that will be mapped to the applications interface"
    )
    
    name: str = Field(
        ...,
        description="Name of the root element if the data given has no __source__ information"
    )
    
    app: HttpUrl = Field(
        ...,
        description="Thin layer repository that will be fetched"
    )
    
    template: Dict = Field(
        default_factory=dict,
        description="Linking template that is used to map the data to the applications interface"
    )

# ! Endpoints
@app.post("/")
async def do_something(body: ServiceTemplate):
    """Function used to run an application"""
    
    # Parse the data model
    dataset, _ = DataModel.parse(data=body.data, root_name=body.name)
    
    # Convert model to other model
    dataset, _ = dataset.convert_to(template=body.template)[0]
    
    # Get the entrypoint
    entrypoint = _fetch_from_git(url=body.app)
    
    result = entrypoint.main(dataset)
    
    return result.to_dict()

@lru_cache(CACHE_SIZE)
def _fetch_from_git(url):
    """Fetches the application repository and entrypoint from git"""
    
    # Clone repository to temporary directory
    with tempfile.TemporaryDirectory() as dir:
        os.chdir(dir)
        subprocess.call(
            ["git", "clone", url]
        )
        
        # Go into the repo and get the entrypoint
        os.chdir(os.listdir()[0])
        
        # Install everything
        subprocess.call(["pip", "install", "."])
        
        if "requirements.txt" in os.listdir():
            subprocess.call(["pip", "install", "-r", "requirements.txt"])
        
        # Get entrypoint and result
        return _import_entry()

def _import_entry():
    """Imports the entrypoint from the application repository"""
    
    spec = importlib.util.spec_from_file_location("main", "entrypoint.py")
    entrypoint = importlib.util.module_from_spec(spec)
    sys.modules["main"] = entrypoint
    spec.loader.exec_module(entrypoint)

    return entrypoint
    