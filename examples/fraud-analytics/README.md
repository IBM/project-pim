# Fraud Analytics

Builds [Vishu Tupili](vishrutha.tupili@ibm.com)'s [pim-fraud-analytics](https://github.ibm.com/project-pim/pim-fraud-analytics) for PIM on top of [base image](../../base-image/)

Tries to predict given credit card transaction could be fraud or not.

Please read about the architecture [here](https://github.ibm.com/project-pim/pim-fraud-analytics?tab=readme-ov-file#pim-fraud-analytics)

### Build
Ensure to replace the `FROM` image in [Containerfile](Containerfile) with the base image you have built before building this image.

```shell
podman build -t <your_registry>/custom-fraud-analytics

podman push <your_registry>/custom-fraud-analytics
```

### Usage
**Step 1:**
- Create table in IBMi DB2 - [create_table.sql](https://github.ibm.com/project-pim/pim-fraud-analytics/blob/main/create_table.sql)
- Insert data into table from this [csv](https://ibm.box.com/s/icbb56rmuij9ltlsmgxig50zintzh5e2) - For permission check with Dharaneeshwaran.Ravichandran@ibm.com or Manjunath.A.C@ibm.com.
**Step 2:**
- Deploy PIM stack using this [utility](../../docs/deployer-guide.md)

**Step 3:**
- Create GET function - [get_transactions.sql](https://github.ibm.com/project-pim/pim-fraud-analytics/blob/main/get_transactions.sql)
- Create Trigger - [insert_trigger.sql](https://github.ibm.com/project-pim/pim-fraud-analytics/blob/main/insert_trigger.sql)

**Step 4:**
Insert a new record to test the prediction
```
insert into PIM.INDEXED_TR(INDEX,USER_ID,CARD,YEAR,MONTH,DAY,TIME,AMOUNT,USE_CHIP,MERCHANT_NAME,MERCHANT_CITY,MERCHANT_STATE,ZIP,MCC,IS_ERRORS,IS_FRAUD) values (100526,29,3,2019,2,20,'12:38','$44.41','Swipe Transaction','-34551508091458520','La Verne','CA',91750,5912,'','No')
```
This is a sample for fraudulent transaction, hence even though we try to add `IS_FRAUD` as `No`, ML will predict this as fraudulent transaction and inserts `IS_FRAUD` as `Yes`
