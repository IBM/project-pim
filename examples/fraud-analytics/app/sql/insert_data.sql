INSERT INTO PIM.INDEXED_TR(INDEX, USER_ID, CARD, YEAR, MONTH, DAY, TIME, AMOUNT, USE_CHIP, MERCHANT_NAME, MERCHANT_CITY, MERCHANT_STATE, ZIP, MCC, IS_ERRORS, IS_FRAUD)
SELECT
  INT(NULLIF(TRIM(SUBSTRING(LINE, 1, LOCATE(',', LINE) - 1)), '')) AS "INDEX",
  INT(NULLIF(TRIM(SUBSTRING(
    LINE,
    LOCATE(',', LINE) + 1,
    LOCATE(',', LINE, LOCATE(',', LINE) + 1) - LOCATE(',', LINE) - 1
  )), '')) AS USER_ID,
  INT(NULLIF(TRIM(SUBSTRING(
    LINE,
    LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1) -
    LOCATE(',', LINE,  LOCATE(',', LINE) + 1) - 1
  )), '')) AS CARD,
  INT(NULLIF(TRIM(SUBSTRING(
    LINE,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1) + 1,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1) + 1) -
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1) - 1
  )), '')) AS "YEAR",
  INT(NULLIF(TRIM(SUBSTRING(LINE,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1) + 1) + 1,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) -
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE) + 1) + 1) + 1) - 1
  )), '')) AS "MONTH",
  INT(NULLIF(TRIM(SUBSTRING(LINE,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1,
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) -
    LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE,  LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) - 1
  )), '')) AS "DAY",
  NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) - 1
  )), '') AS "TIME",
    NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) - 1
  )), '') AS AMOUNT,
  NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
  )), '') AS USE_CHIP, 
  NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
  )), '') AS MERCHANT_NAME,
    NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
  )), '') AS MERCHANT_CITY,
    NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
  )), '') AS MERCHANT_STATE,
      DOUBLE(NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
  )), '')) AS ZIP,
      INT(NULLIF(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
 )), '')) AS MCC,
       TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) -
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) - 1
 )) AS IS_ERRORS,
        RIGHT(TRIM(SUBSTRING(LINE,
LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE, LOCATE(',', LINE) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1
)), 3) AS IS_FRAUD
FROM TABLE(QSYS2.IFS_READ_UTF8(PATH_NAME => 'data_to_insert.csv', END_OF_LINE => 'ANY'))
