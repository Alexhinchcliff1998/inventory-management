import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Integer, DateTime,
                        ForeignKey, CheckConstraint, select, insert, update, func, case)
from sqlalchemy.exc import IntegrityError

class Item(BaseModel):
    sku: str = Field(min_length=1,max_length=40,pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1,max_length=100)
    reorder_point: int = Field(ge=0,le=100000)

class Movement(BaseModel):
    quantity: int = Field(ge=-100000,le=100000)
    reason: str = Field(min_length=1,max_length=100)

metadata=MetaData()
items=Table('items',metadata,Column('sku',String(40),primary_key=True),Column('name',String(100),nullable=False),Column('on_hand',Integer,nullable=False,server_default='0'),Column('reorder_point',Integer,nullable=False),CheckConstraint('on_hand>=0'),CheckConstraint('reorder_point>=0'))
movements=Table('movements',metadata,Column('id',Integer,primary_key=True,autoincrement=True),Column('sku',String(40),ForeignKey('items.sku'),nullable=False),Column('quantity',Integer,nullable=False),Column('reason',String(100),nullable=False),Column('created_at',DateTime(timezone=True),server_default=func.now()))

def create_app(path=None):
    default_path=Path(path or os.getenv('INVENTORY_DB',str(Path(__file__).parent/'inventory.db')))
    url=f'sqlite:///{default_path}' if path else os.getenv('DATABASE_URL',f'sqlite:///{default_path}')
    engine=create_engine(url,connect_args={'timeout':10,'check_same_thread':False} if url.startswith('sqlite') else {})
    metadata.create_all(engine)
    app=FastAPI(title='Stockroom API',version='1.0.0')
    @app.get('/api/items')
    def list_items():
        with engine.connect() as db:
            return [dict(r) for r in db.execute(select(items,case((items.c.on_hand<=items.c.reorder_point,1),else_=0).label('needs_reorder')).order_by(items.c.sku)).mappings()]
    @app.post('/api/items',status_code=201)
    def add(item:Item):
        try:
            with engine.begin() as db:db.execute(insert(items).values(**item.model_dump()))
        except IntegrityError:raise HTTPException(409,'SKU already exists')
        return item.model_dump()
    @app.post('/api/items/{sku}/movements',status_code=201)
    def move(sku:str,movement:Movement):
        if movement.quantity==0:raise HTTPException(422,'Quantity must not be zero')
        with engine.begin() as db:
            row=db.execute(update(items).where(items.c.sku==sku,items.c.on_hand+movement.quantity>=0).values(on_hand=items.c.on_hand+movement.quantity).returning(items.c.on_hand)).first()
            if row is None:
                exists=db.execute(select(items.c.sku).where(items.c.sku==sku)).first()
                if not exists:raise HTTPException(404,'SKU not found')
                raise HTTPException(409,'Insufficient stock')
            db.execute(insert(movements).values(sku=sku,quantity=movement.quantity,reason=movement.reason))
        return {'sku':sku,'on_hand':row[0]}
    @app.get('/api/movements')
    def history():
        with engine.connect() as db:return [dict(r) for r in db.execute(select(movements).order_by(movements.c.id.desc()).limit(100)).mappings()]
    return app

app=create_app()
