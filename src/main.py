from fastapi import FastAPI

from src.api.v1.routers import addresses, clients, products, sell_note_items, sell_notes

app = FastAPI(title="ExamenPractico1 API", version="1.0.0")

app.include_router(clients.router, prefix="/api/v1")
app.include_router(addresses.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(sell_notes.router, prefix="/api/v1")
app.include_router(sell_note_items.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

