# PIM-fraud-analytics
## Architecture
This workload runs on two LPARs (IBM i and Linux)


### Linux
The Linux LPAR is where the REST API is running. This LPAR does inference with 7 transactions (current + 6 previous) to determine if the current transaction is fraud.

### IBM i
The IBM i LPAR hosts the database with the credit card transactions. The schema has the following database elements:

- **Table:** Table contains the credit card transaction data 
- **UDF:** grabs the previous 6 transaction for a given user and card. This UDF will be called in the trigger
- **Trigger:** Upon insert, the trigger creates a JSON document with the current transaction, as well as the previous 6 transactions for that user/card (this is done by calling the UDF). The JSON document is then sent to the REST API on the linux lpar to determine if the current transaction is fraud. The result is sent back to IBM i, which inserts the transaction into the database with the `is_fraud` value set.

## Setup Steps
Clone this repository on your system
### Linux
The REST API endpoint `linux_inference_endpoint.py` can be run inside a podman container. It exposes a `/predict` endpoint which accepts current plus previous transactions and predicts current transaction is fraud or not.
- Build the image: `podman build -t fraud_analytics .`. Building tensorflow from scratch requires minimum of 192GB of memory with 120GB of disk.
- Run the container: `podman run -p 5000:5000 localhost/fraud_analytics`
   
### IBM i
- Create the schema and table using [create_table.sql](sql/create_table.sql)
- Load the data into table using [insert_data.sql](sql/insert_data.sql)
- Create the UDF that grabs the previous 6 transactions for a given user and card using [get_transactions.sql](sql/get_transactions.sql)
- Create the before insert trigger using [insert_trigger.sql](sql/insert_trigger.sql), ensure to replace the fraud_analytics REST endpoint to trigger the inference request. 
  - i.e. `http://<Linux partition 's ip where fraud analytics container runs>:5000/predict`

Use the following example to test if the pipeline is working
```
INSERT INTO PIM.INDEXED_TR (USER_ID, CARD, "YEAR", "MONTH", "DAY", "TIME", AMOUNT, USE_CHIP, 
                               MERCHANT_NAME, MERCHANT_CITY, MERCHANT_STATE, ZIP, MCC, IS_ERRORS)
VALUES (29, 3, 2019, 2, 20, '12:38', '$1.88', 'Chip Transaction', '6051395022895754231', 'Rome', 'Italy', 0, 5310, 'Example');

SELECT * FROM PIM.INDEXED_TR WHERE IS_ERRORS = 'Example';
```

If the insert is successful, you should see the row added to the database with the `IS_FRAUD` value set to Yes
