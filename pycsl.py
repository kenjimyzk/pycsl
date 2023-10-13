import os
from core.base import Base
import pandas as pd

class Pycsl:
    def __init__(self):
        df = pd.read_excel(os.path.dirname(os.path.abspath(__file__))+"/input/config.xlsx", sheet_name="Metadata").fillna("")
        configs = df.to_dict(orient="records")
        for config in configs:
            ids = [x.strip() for x in config["ids"].split(",")]
            multilingual = len(ids)>1
            name = config["name"]
            language = config["language"]
            self.base = Base(ids, name, language, multilingual)    
            self.base.create()

if __name__=="__main__":
    Pycsl()