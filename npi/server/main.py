"""the http server for NPI backend"""


import uvicorn
from fastapi import FastAPI
from npi.server.router import router
from npi.server.middleware import auth


app = FastAPI()
app.middleware("http")(auth)
app.include_router(router)


def main():
    """the main function"""
    uvicorn.run("npi.server.main:app",
                host="0.0.0.0", port=9140, reload=True)


if __name__ == "__main__":
    main()
