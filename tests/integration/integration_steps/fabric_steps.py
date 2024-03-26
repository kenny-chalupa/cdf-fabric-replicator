from azure.identity import DefaultAzureCredential
from deltalake import DeltaTable
from dateutil import tz
from pandas import DataFrame
import pandas as pd
from pandas.testing import assert_frame_equal
from deltalake.writer import write_deltalake
from deltalake.table import DeltaTable

from cognite.client.data_classes import TimeSeries

TIMESTAMP_COLUMN = "timestamp"

def get_ts_delta_table(credential: DefaultAzureCredential, lakehouse_timeseries_path: str):
    token = credential.get_token("https://storage.azure.com/.default")
    return DeltaTable(lakehouse_timeseries_path,storage_options={"bearer_token": token.token, "use_fabric_endpoint": "true"},)

def read_deltalake_timeseries(timeseries_path:str, credential: DefaultAzureCredential):
    delta_table = get_ts_delta_table(credential, timeseries_path)
    df = delta_table.to_pandas()
    return df

def prepare_lakehouse_dataframe_for_comparison(dataframe, external_id):
    dataframe = dataframe.loc[dataframe["externalId"] == external_id]
    dataframe[TIMESTAMP_COLUMN] = pd.to_datetime(dataframe[TIMESTAMP_COLUMN])
    if dataframe[TIMESTAMP_COLUMN].dt.tz is None:
        local_tz = tz.tzlocal()
        dataframe[TIMESTAMP_COLUMN] = dataframe[TIMESTAMP_COLUMN].dt.tz_localize(local_tz)
    dataframe[TIMESTAMP_COLUMN] = dataframe[TIMESTAMP_COLUMN].dt.tz_convert('UTC')
    dataframe[TIMESTAMP_COLUMN] = dataframe[TIMESTAMP_COLUMN].dt.round('s')
    return dataframe

def prepare_test_dataframe_for_comparison(dataframe):
    dataframe[TIMESTAMP_COLUMN] = pd.to_datetime(dataframe[TIMESTAMP_COLUMN])
    dataframe[TIMESTAMP_COLUMN] = dataframe[TIMESTAMP_COLUMN].dt.round('s')
    return dataframe

def assert_timeseries_data_in_fabric(external_id, data_points, timeseries_path, azure_credential: DefaultAzureCredential):
    data_points_from_lakehouse = read_deltalake_timeseries(timeseries_path, azure_credential)
    lakehouse_dataframe = prepare_lakehouse_dataframe_for_comparison(data_points_from_lakehouse, external_id)
    test_dataframe = prepare_test_dataframe_for_comparison(data_points)
    assert_frame_equal(test_dataframe, lakehouse_dataframe, check_dtype=False)

def write_timeseries_data_to_fabric(credential: DefaultAzureCredential, data_frame: DataFrame):
    token = credential.get_token("https://storage.azure.com/.default").token
    table_path = "abfss://40fd095c-e416-4c23-a279-2c14631c5426@msit-onelake.dfs.fabric.microsoft.com/765ff58d-4f56-420f-bf52-49e4553c39d1/Tables/cc_mtu_historic_int_test2"
    write_deltalake(table_path, data_frame, mode="append", storage_options={"bearer_token": token, "use_fabric_endpoint": "true"})
    return None


def remove_time_series_data_from_fabric(credential: DefaultAzureCredential, list_of_time_series: list[TimeSeries]):
    token = credential.get_token("https://storage.azure.com/.default").token
    DeltaTable(
        table_uri="abfss://40fd095c-e416-4c23-a279-2c14631c5426@msit-onelake.dfs.fabric.microsoft.com/765ff58d-4f56-420f-bf52-49e4553c39d1/Tables/cc_mtu_historic_int_test2",
        storage_options={"bearer_token": token, "use_fabric_endpoint": "true"}
    ).delete()


def assert_data_model_in_fabric():
    # Assert the data model is populated in a Fabric lakehouse
    pass

def assert_data_model_update():
    # Assert the data model changes including versions and last updated timestamps are propagated to a Fabric lakehouse
    pass