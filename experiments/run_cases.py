from pathlib import Path

from opendssdirect import dss
import pandas as pd

if __name__ == "__main__":
    temp_file = (
        Path(__file__).parent.parent.parent
        / "io/inputs/ExternalDSSfiles/GFM_IEEE123/Run_IEEE123Bus_GFMDaily.dss"
    )
    dss.Command("Clear")
    dss.Command(f'Redirect "{temp_file}"')
    df = pd.read_csv(
        Path(__file__).parent.parent.parent
        / "io/inputs/ExternalDSSfiles/GFM_IEEE123/ieee123_Mon_stomonitor_1.csv"
    )
    import plotly.express as px

    # Prepare key columns
    key_cols = [val for val in ["t(sec)", None, None, None] if val != None]
    if key_cols:
        if "mean" != None:
            df = df.groupby(key_cols).agg("mean").reset_index()
        else:
            df = df.sort_values(key_cols)

    is_voltage = False

    # Create line plot
    fig = px.line(
        data_frame=df,
        x="t(sec)",
        y=[df.columns[2], df.columns[4], df.columns[6]],
    )

    fig.update_traces(line=dict(width=6))

    font_size = 44
    font_family = "Arial"
    # Apply scientific article style with larger fonts
    fig.update_layout(
        template="plotly_white",  # cleaner, publication-style template
        title=dict(
            text="Voltage Measurements Over Time",
            font=dict(size=font_size, family=font_family),
        ),
        xaxis=dict(
            title=dict(
                text="Time (sec)", font=dict(size=font_size, family=font_family)
            ),
            tickfont=dict(size=font_size, family=font_family),
        ),
        yaxis=dict(
            title=dict(
                text="Voltage (V)" if is_voltage else "Power (kW)",
                font=dict(size=font_size, family=font_family),
            ),
            tickfont=dict(size=font_size, family=font_family),
        ),
        legend=dict(
            title=dict(text="Phase", font=dict(size=40, family=font_family)),
            font=dict(size=font_size, family=font_family),
        ),
    )

    # Save to HTML
    fig.write_html("fig.html")
