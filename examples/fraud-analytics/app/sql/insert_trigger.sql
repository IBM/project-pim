-- Create a trigger that builds the json document to send to the http service and set the is_fraud value
CREATE OR REPLACE TABLE PIM.INDEXED_JSON_DOC (OBJ VARCHAR(20000));

CREATE OR REPLACE TRIGGER PIM.IS_VALID_TRIGGER
  BEFORE INSERT ON PIM.INDEXED_TR
  REFERENCING NEW AS N FOR EACH ROW
  BEGIN
    DECLARE json_doc VARCHAR(20000);
    DECLARE response VARCHAR(20000);
    DECLARE is_fraud VARCHAR(4);
   -- Construct the JSON document
    SET json_doc = JSON_OBJECT(
        'current_transaction' VALUE JSON_OBJECT(
            'user_id'        VALUE N.USER_ID,
            'card'           VALUE N.CARD,
            'year'           VALUE N."YEAR",
            'month'          VALUE N."MONTH",
            'day'            VALUE N."DAY",
            'time'           VALUE N."TIME",
            'amount'         VALUE N.AMOUNT,
            'use_chip'       VALUE N.USE_CHIP,
            'merchant_name'  VALUE N.MERCHANT_NAME,
            'merchant_city'  VALUE N.MERCHANT_CITY,
            'merchant_state' VALUE N.MERCHANT_STATE,
            'zip_code'       VALUE INTEGER(N.ZIP),
            'mcc'            VALUE N.MCC
        ),
        'previous_transactions' VALUE PIM.GET_TRANSACTION_ARRAY(N.USER_ID, N.CARD) FORMAT JSON
     );

    -- Send the JSON document to the Python script via HTTP POST
    SELECT QSYS2.HTTP_POST(
    'http://9.114.97.18:5000/predict', -- URL
    json_doc,
    '{"headers": {"Content-Type": "application/json"}}' -- REQUEST_HEADER
    ) INTO response
    FROM SYSIBM.SYSDUMMY1;

    -- Parse the response and set IS_FRAUD
    SET is_fraud = JSON_VALUE(response, '$.fraud_prediction');
    SET N.IS_FRAUD = is_fraud;
  
  END;
