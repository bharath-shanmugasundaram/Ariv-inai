import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

from flask import Flask ,request ,jsonify 
from flask_restful import Api ,Resource 
from flask_cors import CORS 

app =Flask (__name__ )
CORS (app )
api =Api (app )


items =[
{"id":1 ,"name":"Item 1","description":"First item"},
{"id":2 ,"name":"Item 2","description":"Second item"}
]


class Health (Resource ):
    def get (self ):
        return {"status":"healthy","message":"API is running"}


class Items (Resource ):
    def get (self ):
        return {"items":items }

    def post (self ):
        data =request .get_json ()
        if not data or "name"not in data :
            return {"error":"Name is required"},400 

        new_id =max ([item ["id"]for item in items ],default =0 )+1 
        new_item ={
        "id":new_id ,
        "name":data ["name"],
        "description":data .get ("description","")
        }
        items .append (new_item )
        return new_item ,201 


class ItemDetail (Resource ):
    def get (self ,item_id ):
        item =next ((item for item in items if item ["id"]==item_id ),None )
        if not item :
            return {"error":"Item not found"},404 
        return item 

    def put (self ,item_id ):
        item =next ((item for item in items if item ["id"]==item_id ),None )
        if not item :
            return {"error":"Item not found"},404 

        data =request .get_json ()
        if not data :
            return {"error":"No data provided"},400 

        item ["name"]=data .get ("name",item ["name"])
        item ["description"]=data .get ("description",item ["description"])
        return item 

    def delete (self ,item_id ):
        global items 
        item =next ((item for item in items if item ["id"]==item_id ),None )
        if not item :
            return {"error":"Item not found"},404 

        items =[item for item in items if item ["id"]!=item_id ]
        return {"message":"Item deleted"}


api .add_resource (Health ,"/health")
api .add_resource (Items ,"/items")
api .add_resource (ItemDetail ,"/items/<int:item_id>")


if __name__ =="__main__":
    app .run (debug =True ,host ="0.0.0.0",port =5000 )
