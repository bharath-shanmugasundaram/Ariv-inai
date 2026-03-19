import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print












import requests 
import xml .etree .ElementTree as ET 

api ="https://export.arxiv.org/api/query?search_query=ti:"
user_input =input ("Enter the arxiv paper name: ")

response =requests .get (api +user_input )

root =ET .fromstring (response .text )

namespace ={'atom':'http://www.w3.org/2005/Atom'}
for entry in root .findall ('atom:entry',namespace ):
    title =entry .find ('atom:title',namespace ).text 
    summary =entry .find ('atom:summary',namespace ).text 
    link =entry .find ('atom:id',namespace ).text 

    print ("\n---")
    print (f"Title: {title }")
    print (f"Link: {link }")
    print (f"Summary: {summary [:200 ]}...")
