import numpy as np
import pandas as pd
import sqlite3 as sql

# read in aggregate data on each dearlership from DB.  Then cluster the 96
# dealership points in that N-dimensional space.

# engineer a feature that is max( count( make_name ) )

conn = sql.connect( 'subset.sql' )
cursor = conn.cursor()

query = """select dealer_id, make_Name from (select max(theCount),
              dealer_ID, make_Name from
            (select dealer_ID, count(make_name) AS theCount, make_name from
            orders GROUP BY dealer_id, make_name)
            GROUP BY dealer_ID)
            GROUP BY dealer_ID;"""
cursor.execute( query )
res = cursor.fetchall()


