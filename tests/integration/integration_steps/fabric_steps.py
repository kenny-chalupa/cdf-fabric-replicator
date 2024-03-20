
from azure.identity import DefaultAzureCredential
from deltalake import DeltaTable
from dateutil import tz
import pandas as pd
from pandas.testing import assert_frame_equal

def get_ts_delta_table(credential: DefaultAzureCredential, lakehouse_timeseries_path: str):
    token = credential.get_token("https://storage.azure.com/.default")
    return DeltaTable(lakehouse_timeseries_path,storage_options={"bearer_token": token.token, "use_fabric_endpoint": "true"},)

def read_deltalake_timeseries(timeseries_path:str, credential: DefaultAzureCredential):
    delta_table = get_ts_delta_table(credential, timeseries_path)
    df = delta_table.to_pandas()
    return df

def prepare_lakehouse_dataframe_for_comparison(dataframe, external_id):
    local_tz = tz.tzlocal()
    dataframe = dataframe.loc[dataframe["externalId"] == external_id]
    dataframe['timestamp'] = dataframe['timestamp'].dt.tz_localize(local_tz).dt.tz_convert('UTC')
    dataframe['timestamp'] = dataframe['timestamp'].dt.round('s')
    return dataframe

def prepare_test_dataframe_for_comparison(dataframe):
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'])
    dataframe['timestamp'] = dataframe['timestamp'].dt.round('s')
    return dataframe

def assert_timeseries_data_in_fabric(external_id, data_points, timeseries_path, azure_credential: DefaultAzureCredential):
    data_points_from_lakehouse = read_deltalake_timeseries(timeseries_path, azure_credential)
    lakehouse_dataframe = prepare_lakehouse_dataframe_for_comparison(data_points_from_lakehouse, external_id)
    test_dataframe = prepare_test_dataframe_for_comparison(data_points)
    assert_frame_equal(test_dataframe, lakehouse_dataframe, check_dtype=False)

def assert_data_model_in_fabric():
    # Assert the data model is populated in a Fabric lakehouse
    pass

def assert_data_model_update():
    # Assert the data model changes including versions and last updated timestamps are propagated to a Fabric lakehouse
    pass