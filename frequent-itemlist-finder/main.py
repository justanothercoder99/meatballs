import functions_framework
import os
import pandas as pd
from io import StringIO

from dbHandler import DBHandler
from google.cloud import storage

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori

dbHandler = DBHandler()
dbHandler.setupEngine()

# Initialize storage client
storage_client = storage.Client()

MIN_SUPPORT = float(os.environ.get("MIN_SUPPORT", "0.1"))

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def blob_trigger(cloud_event):
    data = cloud_event.data
    bucket_name = data["bucket"]
    event_id = cloud_event["id"]
    blob_name = data["name"]

    if "transactions" not in blob_name:
        return 
    
    print(f"[ID:{event_id}] Triggered by upload: gs://{bucket_name}/{blob_name}")

    bucket = storage_client.bucket(bucket_name)
    blob   = bucket.blob(blob_name)
    csv_str = blob.download_as_text()
    df = pd.read_csv(StringIO(csv_str), names=["basket_num", "hshd_num", "purchase_date", "product_num", "spend", "units", "store_region", "week_num", "year"])
    print(df.columns)
    df = df[["basket_num", "product_num"]]
    transactions = (
        df.groupby("basket_num")["product_num"]
        .apply(list)
        .tolist()
    )

    # Now use TransactionEncoder:
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions, sparse=True)
    basket_sparse = pd.DataFrame.sparse.from_spmatrix(te_ary, columns=te.columns_)
    basket_sparse.columns = basket_sparse.columns.astype(str)

    frequent_itemsets = apriori(
        basket_sparse, 
        min_support=MIN_SUPPORT, 
        use_colnames=True
    )

    frequent_itemsets["itemset_label"] = (
        frequent_itemsets["itemsets"]
        .apply(lambda s: " & ".join(sorted(s)))
    )
    frequent_itemsets["frequency"] = frequent_itemsets["support"] * df['basket_num'].nunique()
    results_df = frequent_itemsets[["itemsets", "itemset_label", "support", "frequency"]]

    with dbHandler.engine.begin() as conn:
        results_df.to_sql(
            name       = "frequent_itemsets_results",
            con        = conn,
            if_exists  = "replace",
            index      = False,
            method     = "multi"
        )

    print(f"[ID:{event_id}] ✅ Wrote {len(results_df)} itemsets to frequent_itemsets_results.")
