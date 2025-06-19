# src/bdr_calculator.py
import numpy as np
from scipy.interpolate import pchip_interpolate

def calculate_bd_rate(df, anchor_codec, test_codec, metric='vmaf'):
    """
    Calculates the BD-Rate between two codecs from a DataFrame.

    :param df: DataFrame containing the experiment results.
    :param anchor_codec: The reference codec (e.g., 'libx264').
    :param test_codec: The codec to test against the anchor.
    :param metric: The quality metric to use (e.g., 'vmaf').
    :return: The BD-Rate percentage. A negative value means the test_codec is better.
    """
    anchor_data = df[df['codec'] == anchor_codec].sort_values(by='bitrate_kbps')
    test_data = df[df['codec'] == test_codec].sort_values(by='bitrate_kbps')

    if len(anchor_data) < 2 or len(test_data) < 2:
        print(f"Warning: Not enough data points to calculate BD-Rate for {anchor_codec} vs {test_codec}.")
        return None

    # Use the log of the bitrate for interpolation
    anchor_log_br = np.log(anchor_data['bitrate_kbps'])
    test_log_br = np.log(test_data['bitrate_kbps'])

    # Determine the overlapping quality range for integration
    min_metric = max(anchor_data[metric].min(), test_data[metric].min())
    max_metric = min(anchor_data[metric].max(), test_data[metric].max())

    if min_metric >= max_metric:
        print(f"Warning: No overlapping quality range between {anchor_codec} and {test_codec}.")
        return None

    # Generate a range of metric values for integration
    integration_points = np.linspace(min_metric, max_metric, num=100)

    # Interpolate log-bitrate for both codecs at the integration points
    interp_log_br_anchor = pchip_interpolate(anchor_data[metric], anchor_log_br, integration_points)
    interp_log_br_test = pchip_interpolate(test_data[metric], test_log_br, integration_points)

    # Calculate the integral of the log-bitrate difference
    integral_diff = np.trapz(interp_log_br_test - interp_log_br_anchor, integration_points)

    # Calculate the average difference and convert back from log scale
    avg_diff = integral_diff / (max_metric - min_metric)
    bd_rate = (np.exp(avg_diff) - 1) * 100

    return bd_rate