import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

"""
pdf_download.py
===============
Download a PDF from arXiv by paper ID and save it under:
  <output_root>/<paper_title>/paper/<id>.pdf

Can be imported as a module or run as a CLI script.
"""

import os 
import re 
import requests 
import xml .etree .ElementTree as ET 

_API_PDF ="https://arxiv.org/pdf/"
_API_QUERY ="https://export.arxiv.org/api/query?id_list="
_HEADERS ={"User-Agent":"arxiv-pdf-downloader/1.0 (research tool; Python requests)"}


def download_pdf (
arxiv_id :str ,
output_root :str |None =None ,
)->str :
    """
    Download the PDF for *arxiv_id* from arXiv and save it locally.

    Parameters
    ----------
    arxiv_id    : arXiv paper ID, e.g. "1706.03762" or "1706.03762v1"
    output_root : root folder under which <title>/paper/ is created.
                  Defaults to  <this_file's_parent>/../arxiv_papers

    Returns
    -------
    str  – absolute path to the saved PDF file
    """

    arxiv_id =re .sub (r"^arxiv:","",arxiv_id .strip (),flags =re .IGNORECASE )

    if output_root is None :
        here =os .path .dirname (os .path .abspath (__file__ ))
        output_root =os .path .join (here ,"..","arxiv_papers")


    print (f"    Fetching metadata for: {arxiv_id } …")
    try :
        meta_resp =requests .get (
        _API_QUERY +arxiv_id ,headers =_HEADERS ,timeout =30 
        )
    except requests .exceptions .RequestException :
        meta_resp =None 

    title =arxiv_id 
    if meta_resp and meta_resp .status_code ==200 :
        root =ET .fromstring (meta_resp .text )
        ns ={"atom":"http://www.w3.org/2005/Atom"}
        entry =root .find ("atom:entry",ns )
        if entry is not None :
            title_tag =entry .find ("atom:title",ns )
            if title_tag is not None and title_tag .text :
                title =title_tag .text .replace ("\n"," ").strip ()
    elif meta_resp and meta_resp .status_code ==429 :
        print ("    arXiv API rate-limited; using ID as folder name.")


    safe_title =re .sub (r'[\\/*?":<>|]',"",title )
    safe_title =" ".join (safe_title .split ())[:80 ]
    print (f"    Paper: {safe_title }")


    pdf_url =f"{_API_PDF }{arxiv_id }"
    print (f"     Downloading: {pdf_url }")
    pdf_resp =requests .get (pdf_url ,headers =_HEADERS ,timeout =60 )

    if pdf_resp .status_code !=200 :
        raise ConnectionError (
        f"Failed to download PDF (status {pdf_resp .status_code }). "
        f"Check the arXiv ID: {arxiv_id }"
        )


    save_dir =os .path .join (output_root ,safe_title ,"paper")
    os .makedirs (save_dir ,exist_ok =True )

    filepath =os .path .abspath (os .path .join (save_dir ,f"{arxiv_id }.pdf"))
    with open (filepath ,"wb")as f :
        f .write (pdf_resp .content )

    print (f"    PDF saved →  {filepath }")
    return filepath 



if __name__ =="__main__":
    paper_id =input ("Enter the arXiv paper ID: ").strip ()
    try :
        path =download_pdf (paper_id )
        print (f"\nDone! PDF at: {path }")
    except (ConnectionError ,requests .exceptions .RequestException )as e :
        print (f"Error: {e }")
    except KeyboardInterrupt :
        print ("\nInterrupted.")
