import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

import requests 
import pdfplumber 
import io 

api ="https://arxiv.org/pdf/"
paper_id =input ("Enter the arxiv paper id: ")

response =requests .get (api +paper_id )
print (f"Status Code: {response .status_code }")

if response .status_code ==200 :
    pdf_stream =io .BytesIO (response .content )


    with pdfplumber .open (pdf_stream )as pdf :
        first_page_text =pdf .pages [0 ].extract_text ()

        print ("\n--- Extracted Text from Page 1 ---\n")
        print (first_page_text )
else :
    print ("Failed to download the PDF. Check the tracking ID.")
