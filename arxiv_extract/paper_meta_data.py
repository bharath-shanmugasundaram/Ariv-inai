import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

import requests 
import xml .etree .ElementTree as ET 
from datetime import datetime 
import json 
import re 
import time 





NS ={
"atom":"http://www.w3.org/2005/Atom",
"arxiv":"http://arxiv.org/schemas/atom",
"opensearch":"http://a9.com/-/spec/opensearch/1.1/",
}


ARXIV_API_ENDPOINTS =[
"https://export.arxiv.org/api/query?id_list=",
"https://arxiv.org/e-print/",
]


def clean_text (text :str )->str :
    """Strip extra whitespace / newlines from API text fields."""
    if text is None :
        return ""
    return re .sub (r"\s+"," ",text ).strip ()


def parse_version_history (entry )->list [dict ]:
    """Return a list of {version, date, size_kb} dicts from the entry."""
    versions =[]
    for v in entry .findall ("arxiv:version",NS ):
        versions .append ({
        "version":v .get ("version",""),
        "date":clean_text (v .findtext ("arxiv:date","",NS )),
        "size_kb":clean_text (v .findtext ("arxiv:size","",NS )),
        })
    return versions 


def fetch_paper_metadata (arxiv_id :str )->dict :
    """
    Fetch every available metadata field for a single arXiv paper.

    Parameters
    ----------
    arxiv_id : str
        The arXiv ID, e.g. "2602.19021" or "2602.19021v1".

    Returns
    -------
    dict  – a flat/nested dictionary of all metadata.
    """

    arxiv_id =re .sub (r"^arxiv:","",arxiv_id ,flags =re .IGNORECASE ).strip ()

    url =ARXIV_API_ENDPOINTS [0 ]+arxiv_id 

    headers ={"User-Agent":"paper-metadata-extractor/1.0 (research tool; Python requests)"}
    response =None 
    last_error =None 
    for attempt in range (1 ,4 ):
        try :
            print (f"  Attempt {attempt }/3 → {url }")
            response =requests .get (url ,headers =headers ,timeout =30 )
            if response .status_code ==429 :
                wait =attempt *10 
                print (f"    Rate limited (429). Waiting {wait }s before retry…")
                time .sleep (wait )
                continue 
            response .raise_for_status ()
            break 
        except (requests .exceptions .Timeout ,requests .exceptions .ConnectionError )as e :
            last_error =e 
            if attempt <3 :
                wait =attempt *3 
                print (f"    Timeout/connection error. Retrying in {wait }s…")
                time .sleep (wait )
    if response is None or not response .ok :
        raise ConnectionError (
        f"Could not fetch arXiv data after 3 attempts. "
        f"Status: {response .status_code if response else 'N/A'}. {last_error or ''}"
        )

    root =ET .fromstring (response .text )


    entries =root .findall ("atom:entry",NS )
    if not entries :
        raise ValueError (f"No paper found for arXiv ID: {arxiv_id }")

    entry =entries [0 ]


    paper_id_raw =clean_text (entry .findtext ("atom:id","",NS ))

    canonical_id =paper_id_raw .split ("/abs/")[-1 ]if "/abs/"in paper_id_raw else paper_id_raw 

    title =clean_text (entry .findtext ("atom:title","",NS ))
    summary =clean_text (entry .findtext ("atom:summary","",NS ))

    published_raw =clean_text (entry .findtext ("atom:published","",NS ))
    updated_raw =clean_text (entry .findtext ("atom:updated","",NS ))


    authors =[]
    for author in entry .findall ("atom:author",NS ):
        name =clean_text (author .findtext ("atom:name","",NS ))
        affiliation =clean_text (author .findtext ("arxiv:affiliation","",NS ))
        authors .append ({"name":name ,"affiliation":affiliation or None })


    links ={}
    for link in entry .findall ("atom:link",NS ):
        rel =link .get ("rel","")
        href =link .get ("href","")
        title_attr =link .get ("title","")
        if title_attr =="pdf":
            links ["pdf"]=href 
        elif rel =="alternate":
            links ["abstract_page"]=href 
        elif title_attr =="doi":
            links ["doi_link"]=href 
        else :
            links [f"other_{rel }_{title_attr }".strip ("_")]=href 


    comment =clean_text (entry .findtext ("arxiv:comment","",NS ))
    journal_ref =clean_text (entry .findtext ("arxiv:journal_ref","",NS ))
    doi =clean_text (entry .findtext ("arxiv:doi","",NS ))
    primary_category =entry .find ("arxiv:primary_category",NS )
    primary_cat_str =primary_category .get ("term","")if primary_category is not None else ""

    categories =[
    cat .get ("term","")
    for cat in entry .findall ("atom:category",NS )
    ]


    versions =parse_version_history (entry )


    base_id =re .sub (r"v\d+$","",canonical_id )
    arxiv_url =f"https://arxiv.org/abs/{base_id }"
    pdf_url =links .get ("pdf")or f"https://arxiv.org/pdf/{base_id }"
    doi_url =f"https://doi.org/{doi }"if doi else None 


    def fmt_date (iso :str )->str :
        try :
            return datetime .fromisoformat (iso .replace ("Z","+00:00")).strftime ("%Y-%m-%d %H:%M UTC")
        except Exception :
            return iso 


    metadata ={

    "arxiv_id":base_id ,
    "canonical_id":canonical_id ,
    "arxiv_url":arxiv_url ,
    "pdf_url":pdf_url ,


    "title":title ,
    "abstract":summary ,


    "authors":authors ,
    "author_names":[a ["name"]for a in authors ],
    "submitter":authors [0 ]["name"]if authors else None ,


    "submitted_date":fmt_date (published_raw ),
    "last_updated":fmt_date (updated_raw ),


    "primary_category":primary_cat_str ,
    "all_categories":categories ,


    "journal_reference":journal_ref or None ,
    "doi":doi or None ,
    "doi_url":doi_url ,
    "comment":comment or None ,


    "links":links ,


    "version_history":versions ,
    "total_versions":len (versions ),
    }

    return metadata 


def print_metadata (meta :dict )->None :
    """Pretty-print the metadata dictionary to the terminal."""
    divider ="─"*60 

    print (f"\n{divider }")
    print (f"  arXiv Paper Metadata")
    print (f"{divider }")

    print (f"\n  Title        : {meta ['title']}")
    print (f"  arXiv ID     : {meta ['arxiv_id']}")
    print (f"  Abstract URL : {meta ['arxiv_url']}")
    print (f"  PDF URL      : {meta ['pdf_url']}")

    print (f"\n  Authors ({len (meta ['authors'])}):")
    for i ,author in enumerate (meta ["authors"],1 ):
        aff =f"  [{author ['affiliation']}]"if author ["affiliation"]else ""
        print (f"    {i }. {author ['name']}{aff }")

    print (f"\n  Submitted    : {meta ['submitted_date']}")
    print (f"  Last Updated : {meta ['last_updated']}")

    print (f"\n  Primary Category : {meta ['primary_category']}")
    print (f"  All Categories   : {', '.join (meta ['all_categories'])}")

    if meta ["journal_reference"]:
        print (f"\n  Journal Ref  : {meta ['journal_reference']}")
    if meta ["doi"]:
        print (f"  DOI          : {meta ['doi']}")
        print (f"  DOI URL      : {meta ['doi_url']}")
    if meta ["comment"]:
        print (f"  Comment      : {meta ['comment']}")

    print (f"\n  Version History ({meta ['total_versions']} version(s)):")
    for v in meta ["version_history"]:
        print (f"    {v ['version']}  |  {v ['date']}  |  {v ['size_kb']}")

    print (f"\n  Abstract:\n")

    words ,line =meta ["abstract"].split (),""
    for word in words :
        if len (line )+len (word )+1 >80 :
            print (f"    {line }")
            line =word 
        else :
            line =(line +" "+word ).strip ()
    if line :
        print (f"    {line }")

    print (f"\n{divider }\n")


def save_metadata (meta :dict ,filename :str |None =None )->str :
    """Save metadata as JSON. Returns the saved filename."""
    if filename is None :
        filename =f"{meta ['arxiv_id'].replace ('/','_')}_metadata.json"
    with open (filename ,"w",encoding ="utf-8")as f :
        json .dump (meta ,f ,indent =2 ,ensure_ascii =False )
    return filename 





if __name__ =="__main__":
    arxiv_id =input ("Enter the arXiv paper ID (e.g. 2602.19021): ").strip ()

    print (f"\n  Fetching metadata for: {arxiv_id } …")
    metadata =fetch_paper_metadata (arxiv_id )

    print_metadata (metadata )

    save_choice =input ("  Save metadata to JSON? (y/n): ").strip ().lower ()
    if save_choice =="y":
        saved_file =save_metadata (metadata )
        print (f"  Saved to: {saved_file }")
