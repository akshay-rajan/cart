from fastapi import FastAPI, HTTPException, Path, Body, status, Request, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from typing import List, Dict, Tuple, Optional, Annotated
from models import Item
from database import items

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=RedirectResponse)
def home(request: Request):
    return RedirectResponse(url="/items")

@app.get("/items", response_class=HTMLResponse)
def get_items(request: Request):
    items_response = [(id, item) for id, item in items.items()]
    return templates.TemplateResponse("items.html", {
        "request": request,
        "items": items_response,
        "title": "Items"
    })

@app.post("/search", response_class=RedirectResponse)
def search(id: str = Form(...)):
    return RedirectResponse(url=f"/items/{id}", status_code=status.HTTP_302_FOUND)

@app.get("/items/{id}", response_class=HTMLResponse)
def get_item(request: Request, id: int = Path(..., ge=0)):
    item = items.get(id)
    response = templates.TemplateResponse(
        "search.html", 
        {
            "request": request,
            "item": item,
            "id": id,
            "title": "Search Results"
        }
    )
    if not item:
        response.status_code = status.HTTP_404_NOT_FOUND
    return response

@app.get("/create", response_class=HTMLResponse)
def create_item(request: Request):
    return templates.TemplateResponse("create.html", {
        "request": request,
        "title": "Add Item"
    })

@app.post("/items", status_code=status.HTTP_201_CREATED)
def add_item(item: Annotated[Item, Form(...)]):
    max_id = max(items.keys())
    items[max_id + 1] = item.model_dump()
    return RedirectResponse(url="/items", status_code=status.HTTP_302_FOUND)

@app.get("/edit", response_class=HTMLResponse)
def edit_item(request: Request, id: int = Query(...)):
    item = items.get(id)
    if not item:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "item": item,
            "id": id,
            "title": "Sorry..."
        }, status_code=status.HTTP_404_NOT_FOUND)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "title": "Edit Item",
        "item": item,
        "id": id
    })

@app.post("/items/{id}")
def update_item(
    request: Request, 
    item: Annotated[Item, Form(...)],
    id: int = Path(..., ge=0)
):
    stored_item = items.get(id)
    if not stored_item:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "item": stored_item,
            "id": id,
            "title": "Sorry..."
        }, status_code=status.HTTP_404_NOT_FOUND)
    
    # Merge the stored item with the new item
    updated_item = stored_item.copy()
    updated_item.update(item.model_dump())
    items.update({id: updated_item})
    
    return RedirectResponse(url="/items", status_code=status.HTTP_302_FOUND)

@app.get("/delete/{id}", response_class=RedirectResponse)
def delete_item(request: Request, id: int = Path(...)):
    if id not in items:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "id": id,
            "title": "Sorry..."
        }, status_code=status.HTTP_404_NOT_FOUND)
    del items[id]
    return RedirectResponse(url="/items", status_code=status.HTTP_302_FOUND)
