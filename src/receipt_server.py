import json
import os
import shutil
import socket
import subprocess
from collections import namedtuple

import uvicorn
from fastapi import FastAPI, Depends, UploadFile, File, Security, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from pydantic import BaseModel
from receipt_parser_core.config import read_config
from receipt_parser_core.enhancer import process_receipt
from starlette.responses import RedirectResponse
from starlette.status import HTTP_403_FORBIDDEN
from werkzeug.utils import secure_filename

import receipt_printer as printer
import util as util
from colors import bcolors

COOKIE_DOMAIN = "receipt.parser.de"
ALLOWED_PORT = 8721
ALLOWED_HOST = "0.0.0.0"

UPLOAD_FOLDER = 'data/img'
TMP_FOLDER = 'data/tmp/'
TRAINING_FOLDER = 'data/training/'
CERT_LOCATION = "cert/server.crt"
KEY_LOCATION = "cert/server.key"
DATA_PREFIX = "data/img/"
API_TOKEN_FILE = "data/.api_token"

# ZERO_CONF
ZERO_CONF_DESCRIPTION = "Receipt parser server._receipt-service._tcp.local."
ZERO_CONF_SERVICE = "_receipt-service._tcp.local."

PRINT_DEBUG_OUTPUT = False

API_KEY_NAME = "access_token"
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

config = read_config(util.get_config_dir() + "/config.yml")

if os.path.isfile(API_TOKEN_FILE):
    with open(API_TOKEN_FILE) as f:
        line = f.readline().strip()
        if not line:
           raise RuntimeError("can't find valid API token")
        else:
            API_KEY = line

else:
    raise RuntimeError("API token does not exist.")

class Receipt(BaseModel):
    company: str
    date: str
    total: str

async def get_api_key(
        api_query: str = Security(api_key_query),
        api_header: str = Security(api_key_header),
        api_cookie: str = Security(api_key_cookie),
):
    if api_query == API_KEY:
        return api_query
    elif api_header == API_KEY:
        return api_header
    elif api_cookie == API_KEY:
        return api_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

# Set header and cookies
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
origins = [
    "https://receipt-parser.com",
    "https://receipt-parser.com:8721",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prepare training dataset for neuronal parser
# If an photo is submitted, upload the corresponding json file
@app.post("/api/training", tags=["api"])
async def get_open_api_endpoint(receipt: Receipt,
                                api_key: APIKey = Depends(get_api_key)):
    if not receipt:
        raise HTTPException(
            status_code=415, detail="Invalid receipt send"
        )

    search_dir = util.get_work_dir() + TMP_FOLDER
    file = util.get_last_modified_file(search_dir)

    search_dir = util.get_work_dir() + TRAINING_FOLDER
    last = util.get_last_modified_file(search_dir)

    index = 0
    if last:
        filename = os.path.basename(last).split(".")[0]
        if filename and filename == '':
            index = int(filename) + 1

    shutil.copyfile(file, util.get_work_dir() + TRAINING_FOLDER + str(index) + ".png")
    training_set = {'company': receipt.company, "date": receipt.date, "total": receipt.total}

    with open(TRAINING_FOLDER + str(index) + '.json', 'w+') as out:
        json.dump(training_set, out)

    return JSONResponse(content="success")


# Current image api
@app.post("/api/upload", tags=["api"])
async def get_open_api_endpoint(
        legacy_parser: bool = True,
        grayscale_image: bool = True,
        gaussian_blur: bool = False,
        rotate_image: bool = False,
        file: UploadFile = File(...),
        api_key: APIKey = Depends(get_api_key)):
    if file.filename == "":
        printer.error("No filename exist")
        raise HTTPException(
            status_code=415, detail="Invalid image send"
        )

    if file and util.allowed_file(file.filename):
        print(file.filename)

        filename = secure_filename(file.filename)
        output = os.path.join(util.get_work_dir() + UPLOAD_FOLDER, filename)
        printer.info("Store file at: " + output)

        with open(output, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if PRINT_DEBUG_OUTPUT:
            items = []
            item = namedtuple("item", ("article", "sum"))
            items.append(item("Brot", "1.33"))
            items.append(item("Kaffee", "5.33"))

            receipt_data = {"storeName": "DebugStore",
                            "receiptTotal": "15.10",
                            "receiptDate": "09.25.2020",
                            "receiptCategory": "grocery",
                            "receiptItems": items}

            json_compatible_item_data = jsonable_encoder(receipt_data)
            return JSONResponse(content=json_compatible_item_data)

        printer.info("Parsing image")
        receipt = process_receipt(config, filename, rotate=rotate_image, grayscale=grayscale_image,
                                  gaussian_blur=gaussian_blur)

        printer.print_receipt(receipt)

        receipt_data = {"storeName": receipt.market,
                        "receiptTotal": receipt.sum,
                        "receiptDate": json.dumps(receipt.date, default=util.json_serial),
                        "receiptCategory": "grocery",
                        "receiptItems": receipt.items}

        json_compatible_item_data = jsonable_encoder(receipt_data)

        if config.debug_print_results_as_json:
            print("Result json is:")
            print(json_compatible_item_data)
            print()

        return JSONResponse(content=json_compatible_item_data)

    else:
        raise HTTPException(
            status_code=415, detail="Invalid image send"
        )


@app.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie(API_KEY_NAME, domain=COOKIE_DOMAIN)
    return response

if __name__ == "__main__":
    print("Current API token: " + bcolors.OKGREEN + API_KEY + bcolors.ENDC)
    print()

    c = subprocess.getoutput('echo ' + API_KEY + '| qrencode -t UTF8')
    print(c + "\n")

    if config.https:
        uvicorn.run("receipt_server:app", host="0.0.0.0", port=ALLOWED_PORT, log_level="info",
                    ssl_certfile=util.get_work_dir() + CERT_LOCATION, ssl_keyfile=util.get_work_dir() + KEY_LOCATION)
    else:
        uvicorn.run("receipt_server:app", host="0.0.0.0", port=ALLOWED_PORT, log_level="info")
