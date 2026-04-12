import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path
import re

"""
README

There is comments on this script. It specifically generates burndown charts for milestones and sprints based on GitLab data.
The script is designed to be flexible, allowing users to select specific milestones or generate charts for all milestones in the dataset.

Specifications:

If you want to get charts in the browser, uncomment 'fig.show()'.
If you want to save static PNGs, uncomment 'plt.savefig()' and 'plt.close()'.
If you want to save interactive HTML files, uncomment 'fig.write_html()'.
"""

ROOT_MILESTONE_PROGESS = Path(__file__).resolve().parent
DATA_GITLAB_FOLDER = "data-gitlab"

# CONFIGURATION
pio.renderers.default = "browser"
SPRINT_KEYWORDS = ["sprint", "week", "iteration"]


def parse_time(time_str):
    """Converts GitLab time estimates (e.g., '2h 30m') into decimal hours."""
    if pd.isna(time_str):
        return 0.0
    time_str = str(time_str)
    hours = 0.0
    minutes = 0.0
    h_match = re.search(r"(\d+)h", time_str)
    if h_match:
        hours += float(h_match.group(1))
    m_match = re.search(r"(\d+)m", time_str)
    if m_match:
        minutes += float(m_match.group(1))
    return hours + minutes / 60.0


def generate_burndown(m_df, title, is_sprint, y_axis_label):
    # Establish base boundaries
    kickoff = pd.to_datetime(m_df["Created At (UTC)"].min().date())

    # Check if all items in the scope are 100% closed
    all_closed = m_df["Closed At (UTC)"].isna().sum() == 0
    max_closed = m_df["Closed At (UTC)"].max()
    max_created = m_df["Created At (UTC)"].max()

    # Establish 'Today' anchor using the latest activity in the data
    today_dt = max(
        max_closed if pd.notna(max_closed) else kickoff,
        max_created if pd.notna(max_created) else kickoff,
    )
    today = pd.to_datetime(today_dt.date())

    deadline = pd.to_datetime(max_closed.date()) if pd.notna(max_closed) else kickoff

    # Only artificially extend the deadline for forecasting if the milestone/sprint is STILL ACTIVE
    if not all_closed:
        if deadline <= today:
            deadline = today + pd.Timedelta(days=5)

    date_range = pd.date_range(start=kickoff, end=deadline, freq="D")

    daily_data = []
    for current_date in date_range:
        eod = current_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        scope_df = m_df[m_df["Created At (UTC)"] <= eod]
        total_scope = scope_df["Size"].sum()

        closed_df = scope_df[
            scope_df["Closed At (UTC)"].notna() & (scope_df["Closed At (UTC)"] <= eod)
        ]
        total_completed = closed_df["Size"].sum()
        remaining = total_scope - total_completed

        # Stop actuals logic specifically for 100% completed deliverables
        if all_closed and current_date > pd.to_datetime(max_closed.date()):
            daily_data.append(
                {"Date": current_date, "Remaining": 0, "Total Scope": total_scope}
            )
        elif current_date <= today:
            daily_data.append(
                {
                    "Date": current_date,
                    "Remaining": remaining,
                    "Total Scope": total_scope,
                }
            )
        else:
            daily_data.append(
                {"Date": current_date, "Remaining": None, "Total Scope": total_scope}
            )

    bd_df = pd.DataFrame(daily_data)

    # 1. Ideal Trendline
    day_1_scope = (
        bd_df.iloc[0]["Total Scope"]
        if bd_df.iloc[0]["Total Scope"] > 0
        else bd_df["Total Scope"].max()
    )
    bd_df["Ideal"] = np.linspace(day_1_scope, 0, len(bd_df))

    # 2. Extract Actual points
    actuals = bd_df.dropna(subset=["Remaining"])
    x = np.arange(len(actuals))
    y = actuals["Remaining"].values

    # 3. Estimated Trendline (Forecast) - Only if NOT finished
    if len(actuals) > 1 and not all_closed:
        slope, intercept = np.polyfit(x, y, 1)
        forecast_x = np.arange(len(bd_df))
        est_y = slope * forecast_x + intercept
        bd_df["Estimated"] = [v if v >= 0 else 0 for v in est_y]
    else:
        # Don't plot the red line if the milestone is already perfectly completed
        bd_df["Estimated"] = None

    # Chart Title formatting
    prefix = "Tactical Sprint" if is_sprint else "Strategic Milestone"
    # safe_name = re.sub(r"[^A-Za-z0-9]+", "_", title)

    # GLOBAL CHART
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 6))

    plt.plot(
        actuals["Date"],
        actuals["Remaining"],
        marker="o",
        color="#1f77b4",
        linewidth=3,
        label="Actual Burndown",
    )
    plt.plot(
        bd_df["Date"],
        bd_df["Ideal"],
        linestyle="--",
        color="gray",
        linewidth=2,
        label="Ideal Burndown",
    )

    if not all_closed:
        plt.plot(
            bd_df["Date"],
            bd_df["Estimated"],
            linestyle="-.",
            color="red",
            linewidth=2.5,
            label="Estimated Delivery (Forecast)",
        )

    plt.title(f"{prefix} Burndown: {title}", fontsize=16, fontweight="bold")
    plt.xlabel("Timeline", fontsize=12)
    plt.ylabel(y_axis_label, fontsize=12)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    plt.legend(loc="upper right")
    plt.tight_layout()

    # static_filename = f"burndown_static_{'sprint' if is_sprint else 'milestone'}_{safe_name}.png"
    # plt.savefig(static_filename)
    # plt.close()
    plt.show(block=False)  # Changed to non-blocking so the script continues

    # INTERACTIVE CHARTs
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=actuals["Date"],
            y=actuals["Remaining"],
            mode="lines+markers",
            name="Actual Burndown",
            line=dict(color="#1f77b4", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=bd_df["Date"],
            y=bd_df["Ideal"],
            mode="lines",
            name="Ideal Burndown",
            line=dict(color="gray", dash="dash", width=2),
        )
    )

    if not all_closed:
        fig.add_trace(
            go.Scatter(
                x=bd_df["Date"],
                y=bd_df["Estimated"],
                mode="lines",
                name="Estimated Delivery",
                line=dict(color="red", dash="dashdot", width=2.5),
            )
        )

    fig.update_layout(
        title=f"<b>{prefix} Burndown: {title}</b>",
        xaxis_title="Timeline",
        yaxis_title=y_axis_label,
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(tickformat="%b %d, %Y"),
    )

    # interactive_filename = f"burndown_interactive_{'sprint' if is_sprint else 'milestone'}_{safe_name}.html"
    # fig.show() # Plotly interactive show
    # fig.write_html(interactive_filename)

    print(f"Generated successfully: {title}")


def process_milestones(df, target_milestones):
    """Processes specific milestones from the loaded dataframe."""
    # Sizing logic
    if "Weight" in df.columns and df["Weight"].notna().any():
        df["Size"] = pd.to_numeric(df["Weight"], errors="coerce").fillna(0)
        y_axis_label = "Remaining Story Points"
    elif "Time Estimate" in df.columns:
        df["Size"] = df["Time Estimate"].apply(parse_time)
        y_axis_label = "Remaining Hours"
    else:
        print("Error: Missing Size metrics ('Weight' or 'Time Estimate').")
        return

    df["Created At (UTC)"] = pd.to_datetime(
        df["Created At (UTC)"], errors="coerce"
    ).dt.tz_localize(None)
    df["Closed At (UTC)"] = pd.to_datetime(
        df["Closed At (UTC)"], errors="coerce"
    ).dt.tz_localize(None)

    for item in target_milestones:
        m_df = df[df["Milestone"] == item].copy()
        if m_df.empty or m_df["Created At (UTC)"].isna().all():
            print(f"Skipping '{item}': No valid data.")
            continue

        # Differentiate between a Tactical Sprint and a Strategic Milestone based on Name
        is_sprint = any(
            keyword.lower() in str(item).lower() for keyword in SPRINT_KEYWORDS
        )

        generate_burndown(m_df, item, is_sprint, y_axis_label)

    # Keep matplotlib windows open until user closes them
    plt.show()


def main():
    print("=== Burndown Chart Generator ===")

    # 1. File Input & Error Handling
    df = None
    while df is None:
        filename = input(
            "Enter the CSV file name and extension(e.g., data.csv): "
        ).strip()
        file_path = ROOT_MILESTONE_PROGESS / DATA_GITLAB_FOLDER / filename

        if not file_path.exists():
            print(f"Error: File '{file_path}' not found. Please try again.\n")
            continue

        try:
            df = pd.read_csv(file_path)
            print("File loaded successfully!\n")
        except Exception as e:
            print(f"Error reading CSV: {e}\n")
            continue

    # 2. Extract Milestones
    if "Milestone" not in df.columns:
        print("Error: 'Milestone' column not found in the CSV.")
        return

    milestones = df["Milestone"].dropna().unique()
    if len(milestones) == 0:
        print("No milestones found in the provided CSV.")
        return

    # 3. Interactive Menu Loop
    while True:
        print("\n--- Available Milestones ---")
        for i, m in enumerate(milestones, 1):
            print(f"{i}. {m}")
        print("-" * 28)
        print(f"{len(milestones) + 1}. Generate ALL Milestones")
        print("0. Exit")

        choice = input("\nSelect an option (enter number): ").strip()

        try:
            choice_idx = int(choice)
            if choice_idx == 0:
                print("Exiting generator. Goodbye!")
                break
            elif choice_idx == len(milestones) + 1:
                print("\nGenerating charts for ALL milestones...")
                process_milestones(df, milestones)
            elif 1 <= choice_idx <= len(milestones):
                selected = milestones[choice_idx - 1]
                print(f"\nGenerating charts for: {selected}...")
                process_milestones(df, [selected])
            else:
                print("Invalid choice. Please enter a valid menu number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


if __name__ == "__main__":
    main()
