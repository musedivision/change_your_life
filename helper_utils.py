from pathlib import Path
import pandas as pd
import xmltodict
import numpy as np
from IPython.display import display, FileLink, FileLinks
from ipyupload import FileUpload
import io

def getFileUpload():
    
    return FileUpload(
    accept='', # default
    multiple=False, # default
    disabled=False, # default
    style_button='', # default
    compress_level=0 
)

def uploadFileObject(upload):  
    """takes file upload object and returns io object """
    upload_bytes = [ i for i in upload.value.items() ][0][1]['content']
    return io.BytesIO(upload_bytes)

def upload2str(upload): return [ i for i in upload.value.items() ][0][1]['content']

def parse_inventory_xml(xml):
    items = xmltodict.parse(xml)["inventory"]["catalog_version"]

    item_arr = [ i for i in items.items() ][1]

    item_d_arr = [ dict(i) for i in item_arr[1] ]
    itemsku_2_inventorytotal = { x["item_sku"]:x["total_inventory"] for x in item_d_arr }
    
    # convert dict to df
    sku_inventory_df = pd.DataFrame.from_dict(itemsku_2_inventorytotal, orient='index')
    sku_inventory_df['item_sku'] = sku_inventory_df.index
    sku_inventory_df.columns = ["inventory_total", "item_sku"]

    # convert the strings to numbers
    sku_inventory_df["item_sku"] = pd.to_numeric(sku_inventory_df["item_sku"])
    sku_inventory_df["inventory_total"] = pd.to_numeric(sku_inventory_df["inventory_total"])
    
    return sku_inventory_df

def merge_katoche_dfs(cat_df, item_cat_df, item_df, sku_inventory_df):
    # item import sample
    # name, sku, price

    item_df = item_df[["name","sku", "nzd_price"]]
    item_df.columns = ["item_name", "item_sku", "nzd_price"]
    
    # merge item categories with item import
    # "item_name", "item_sku", "nzd_price", "category_name"

    df = item_df.merge(item_cat_df, on='item_name')
    df = df[["item_name", "item_sku", "nzd_price", "category_name"]]
    
    #sanity check
    # check the data types match
    assert(df["item_sku"].dtype == sku_inventory_df["item_sku"].dtype)
    
    # merge inventory data in on 
    df = df.merge(sku_inventory_df, on='item_sku')
    
    # if inventory total >= 1 --> yes else no
    df['opening_availability'] = np.where(df['inventory_total']>=1, 'Yes', 'No')
    
    return df


def make_excel_download(df):
    Path('./output').mkdir(exist_ok=True)

    df.to_excel('./output/active_hospo_catalogue.xlsx')
    
    return FileLinks(str(Path('./output')))