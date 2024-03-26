import pytest
from integration_steps.cdf_steps import push_data_to_cdf, assert_time_series_in_cdf, assert_time_series_in_cdf_by_id, assert_data_points_in_cdf
from integration_steps.time_series_generation import TimeSeriesGeneratorArgs
from integration_steps.fabric_steps import assert_timeseries_data_in_fabric
from integration_steps.service_steps import run_replicator, run_extractor
import pandas as pd

# Test for Timeseries data integration service
@pytest.mark.skip("Skipping test", allow_module_level=True)
@pytest.mark.parametrize(
    "time_series",
    [
        TimeSeriesGeneratorArgs(["int_test_fabcd_hist:mtu:39tic1091.pv"], 10)
    ],
    indirect=True,
)
def test_timeseries_data_integration_service(cognite_client, test_replicator, lakehouse_timeseries_path, time_series, azure_credential):
    # Push data points to CDF
    pushed_data = push_data_to_cdf(time_series, cognite_client)
    # Run replicator for data point subscription between CDF and Fabric
    run_replicator(test_replicator)
    # Assert timeseries data is populated in a Fabric lakehouse
    for ts_external_id, data_points in pushed_data.items():
        assert_timeseries_data_in_fabric(ts_external_id, data_points, lakehouse_timeseries_path, azure_credential)


# pytest.mark.skip("Skipping test", allow_module_level=True)
@pytest.mark.parametrize(
    "raw_time_series",
    [TimeSeriesGeneratorArgs(["akchalupa_test_fabcd_hist:mtu:39tic1091.pv"], 10)],
    indirect=True,
)
def test_extractor_timeseries_service(cognite_client, raw_time_series, test_extractor):

    # Run replicator to pick up new timeseries data points in Lakehouse
    run_extractor(test_extractor, raw_time_series)

    # Assert timeseries data is populated CDF
    assert_time_series_in_cdf_by_id(raw_time_series['externalId'].unique(), cognite_client)
    
    for ts in raw_time_series['externalId'].unique():
        expected_data_points = raw_time_series[raw_time_series["externalId"] == ts]
        assert_data_points_in_cdf(ts, expected_data_points, cognite_client)

    # for ts_external_id, data_points in pushed_data.items():
    #     assert_timeseries_data_in_fabric(ts_external_id, data_points, lakehouse_timeseries_path, azure_credential)
    assert True