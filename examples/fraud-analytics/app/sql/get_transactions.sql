-- Create a scalar function that returns the a json object with the last 6 transacations for x user, y card
CREATE OR REPLACE FUNCTION PIM.GET_TRANSACTION_ARRAY (UID INTEGER, CARD_NUM INTEGER)
 RETURNS VARCHAR(20000)
 LANGUAGE SQL
 READS SQL DATA
  RETURN 
   WITH TRANSACTION_JSON AS (
     SELECT ("YEAR" || '-' || "MONTH" || '-' || "DAY" || ' ' || TIME || ':00.000000') AS TRANSACTION_TIMESTAMP,
            JSON_OBJECT('index'          VALUE INDEX,
                        'user_id'        VALUE USER_ID,
                        'card'           VALUE CARD,
                        'year'           VALUE "YEAR",
                        'month'          VALUE "MONTH",
                        'day'            VALUE "DAY",
                        'time'           VALUE "TIME",
                        'amount'         VALUE AMOUNT,
                        'use_chip'       VALUE USE_CHIP,
                        'merchant_name'  VALUE MERCHANT_NAME,
                        'merchant_city'  VALUE MERCHANT_CITY,
                        'merchant_state' VALUE MERCHANT_STATE,
                        'zip_code'       VALUE INTEGER(ZIP),
                        'mcc'            VALUE MCC,
                        'is_errors'      VALUE IS_ERRORS,
                        'is_fraud'       VALUE IS_FRAUD) AS TRANSACTION_JSON_OBJECT
       FROM PIM.INDEXED_TR A
       WHERE USER_ID = UID AND CARD = CARD_NUM
       ORDER BY TRANSACTION_TIMESTAMP DESC
       LIMIT 6)
   SELECT JSON_ARRAY((SELECT TRANSACTION_JSON_OBJECT FROM TRANSACTION_JSON) FORMAT JSON) FROM SYSIBM.SYSDUMMY1;
