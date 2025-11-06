from pathlib import Path

from opendssdirect import dss
import pandas as pd

if __name__ == "__main__":
    temp_file = (
        Path(__file__).parent.parent.parent
        / "data/inputs/ExternalDSSfiles/GFM_IEEE123_AmpLimit/Run_IEEE123Bus_GFMDaily_CurrentLimit.dss"
    )
    dss.Command("Clear")
    dss.Command(f'Redirect "{temp_file}"')
    df = pd.read_csv(
        Path(__file__).parent.parent.parent
        / "data/inputs/ExternalDSSfiles/GFM_IEEE123_AmpLimit/ieee123_Mon_stomonitor_1.csv"
    )
    import plotly.express as px

    # Prepare key columns
    key_cols = [val for val in ["t(sec)", None, None, None] if val != None]
    if key_cols:
        if "mean" != None:
            df = df.groupby(key_cols).agg("mean").reset_index()
        else:
            df = df.sort_values(key_cols)

    # Create line plot
    fig = px.line(
        data_frame=df,
        x="t(sec)",
        y=["P1 (kW)", "P2 (kW)", "P3 (kW)"],
        render_mode="auto",
    )

    fig.update_traces(connectgaps=True)

    # Apply scientific article style with larger fonts
    fig.update_layout(
        template="plotly_white",  # cleaner, publication-style template
        title=dict(
            text="Voltage Measurements Over Time",
            font=dict(size=22, family="Times New Roman"),
        ),
        xaxis=dict(
            title=dict(text="Time (sec)", font=dict(size=18, family="Times New Roman")),
            tickfont=dict(size=16, family="Times New Roman"),
        ),
        yaxis=dict(
            title=dict(
                text="Voltage (V)", font=dict(size=18, family="Times New Roman")
            ),
            tickfont=dict(size=16, family="Times New Roman"),
        ),
        legend=dict(
            title=dict(text="Phase", font=dict(size=16, family="Times New Roman")),
            font=dict(size=14, family="Times New Roman"),
        ),
    )

    # Save to HTML
    fig.write_html("fig.html")
