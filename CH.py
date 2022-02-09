###  This function is for connecting with clickhouse data base and exporting necessary data from there

import pandahouse
import os

class Getch:
    def __init__(self, query, db='simulator_20211220'):
        self.connection = {
            'host': 'https://clickhouse.lab.karpov.courses',
            'password': 'dpo_python_2020',  # password was changed
            'user': 'student',  # username was changed
            'database': db,
        }
        self.query = query
        self.getchdf

    @property
    def getchdf(self):
        try:
            self.df = pandahouse.read_clickhouse(self.query, connection=self.connection)

        except Exception as err:
            print("\033[31m {}".format(err))
            exit(0)

class Insertch:
    def __init__(self, data, table_name, db = 'simulator_20211220'):
        self.connection = {
            'host': 'https://clickhouse.lab.karpov.courses',
            'password': 'dpo_python_2020',  # password was changed
            'user': 'student',  # username was changed
            'database': db,
        }
        self.data = data
        self.table_name = table_name
        self.tochdf

    @property
    def tochdf(self):
        try:
            self.insert = pandahouse.read_clickhouse(self.data, self.table_name, index=False, connection=self.connection)
        except Exception as err:
            print("\033[31m {}".format(err))
            # exit(0)


# THIS query for creating a new table
# CREATE table simulator_20211220.alerts_log (
# `time`              DateTime,
# `day_0_value`       Float64,
# `day_1_value`        Float64,
# `day_7_value`        Float64,
# `day_1_diff`        Float64,
# `day_7_diff`         Float64,
# `slice_`             Sting,
# `metric`             Sting,
# `metric_name`        Sting,
# `group_level`        Sting,
# `is_alert`           UInt8
# )
#
# ENGINE = MergeTree
# ORDER BY (time, slice_, metric, group_level)
# SETTINGS index_granuality = 8192