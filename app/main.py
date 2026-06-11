from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="Medical AI Chatbot"
)


@app.on_event("startup")
async def startup_event():

    print("Medical AI Chatbot Started")


app.include_router(router)