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

This script generates burndown/burnup charts and member productivity charts based on GitLab data.
It allows users to select specific milestones or generate global project statistics.

Specifications:
- Burndown/Burnup: Tracks progress against ideal trends and provides forecasts.
- Member Spent Hours: Analyzes time spent vs. estimated per member, globally and per milestone.
- Dual-Axis Charts: Used for member statistics to compare high-magnitude totals with weekly averages.
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


def list_csv_files():
    """Lists all CSV files in the data-gitlab folder."""
    data_dir = ROOT_MILESTONE_PROGESS / DATA_GITLAB_FOLDER
    if not data_dir.exists():
        return []
    return list(data_dir.glob("*.csv"))


def generate_burndown(m_df, title, is_sprint, y_axis_label):
    """Generates static and interactive Burndown/Burnup charts."""
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
        bd_df["Estimated"] = None

    # Chart Title formatting
    prefix = "Tactical Sprint" if is_sprint else "Strategic Milestone"

    # GLOBAL CHART
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 6))

    plt.plot(
        actuals["Date"],
        actuals["Remaining"],
        marker="o",
        color="#1f77b4",
        linewidth=3,
        label="Actual Remaining",
    )
    plt.plot(
        bd_df["Date"],
        bd_df["Ideal"],
        linestyle="--",
        color="gray",
        linewidth=2,
        label="Ideal Trend",
    )

    if not all_closed:
        plt.plot(
            bd_df["Date"],
            bd_df["Estimated"],
            linestyle="-.",
            color="red",
            linewidth=2.5,
            label="Estimated Forecast",
        )

    plt.title(f"{prefix} Burndown/Burnup: {title}", fontsize=16, fontweight="bold")
    plt.xlabel("Timeline", fontsize=12)
    plt.ylabel(y_axis_label, fontsize=12)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show(block=False)

    # INTERACTIVE CHART
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=actuals["Date"],
            y=actuals["Remaining"],
            mode="lines+markers",
            name="Actual Remaining",
            line=dict(color="#1f77b4", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=bd_df["Date"],
            y=bd_df["Ideal"],
            mode="lines",
            name="Ideal Trend",
            line=dict(color="gray", dash="dash", width=2),
        )
    )

    if not all_closed:
        fig.add_trace(
            go.Scatter(
                x=bd_df["Date"],
                y=bd_df["Estimated"],
                mode="lines",
                name="Estimated Forecast",
                line=dict(color="red", dash="dashdot", width=2.5),
            )
        )

    fig.update_layout(
        title=f"<b>{prefix} Burndown/Burnup: {title}</b>",
        xaxis_title="Timeline",
        yaxis_title=y_axis_label,
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(tickformat="%b %d, %Y"),
    )
    # fig.show()

    print(f"Generated successfully: {title}")


def process_member_data(df):
    """Processes the dataframe to distribute time among members and calculate weekly stats."""
    # Ensure Time Spent and Estimate are parsed
    df = df.copy()
    df["Time Spent Numeric"] = df["Time Spent"].apply(parse_time)
    df["Time Estimate Numeric"] = df["Time Estimate"].apply(parse_time)

    # Handle multiple assignees: split and distribute hours
    expanded_rows = []
    for _, row in df.iterrows():
        assignees = str(row["Assignee Username"]).split(",")
        assignees = [a.strip() for a in assignees if a.strip() and a.strip() != "nan"]

        if not assignees:
            continue

        num_assignees = len(assignees)
        for assignee in assignees:
            new_row = row.copy()
            new_row["Member"] = assignee
            new_row["Spent Distributed"] = row["Time Spent Numeric"] / num_assignees
            new_row["Estimate Distributed"] = (
                row["Time Estimate Numeric"] / num_assignees
            )
            expanded_rows.append(new_row)

    member_df = pd.DataFrame(expanded_rows)

    # Calculate Project Duration in Weeks
    if "Created At (UTC)" in df.columns:
        df["Created At (UTC)"] = pd.to_datetime(df["Created At (UTC)"]).dt.tz_localize(
            None
        )
        start_date = df["Created At (UTC)"].min()
        end_date = pd.Timestamp.now()
        if "Closed At (UTC)" in df.columns:
            df["Closed At (UTC)"] = pd.to_datetime(
                df["Closed At (UTC)"], errors="coerce"
            ).dt.tz_localize(None)
            max_closed = df["Closed At (UTC)"].max()
            if pd.notna(max_closed):
                end_date = max(end_date, max_closed)

        duration_days = (end_date - start_date).days
        total_weeks = max(1, duration_days / 7.0)
    else:
        total_weeks = 1

    return member_df, total_weeks


def generate_member_stats_chart(member_df, total_weeks):
    """Generates a dual-axis bar chart for global member statistics."""
    stats = (
        member_df.groupby("Member")
        .agg({"Spent Distributed": "sum", "Estimate Distributed": "sum"})
        .reset_index()
    )
    stats["Weekly Average"] = stats["Spent Distributed"] / total_weeks

    # Sort by spent hours
    stats = stats.sort_values(by="Spent Distributed", ascending=False)

    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Primary Axis: Total Hours
    x = np.arange(len(stats["Member"]))
    width = 0.35

    ax1.bar(
        x - width / 2,
        stats["Spent Distributed"],
        width,
        label="Total Spent Hours",
        color="#1f77b4",
        alpha=0.8,
    )
    ax1.bar(
        x + width / 2,
        stats["Estimate Distributed"],
        width,
        label="Total Estimated Hours",
        color="#aec7e8",
        alpha=0.6,
    )

    ax1.set_xlabel("Team Member", fontsize=12)
    ax1.set_ylabel("Total Hours", fontsize=12, color="#1f77b4")
    ax1.set_xticks(x)
    ax1.set_xticklabels(stats["Member"], rotation=45)
    ax1.tick_params(axis="y", labelcolor="#1f77b4")

    # Secondary Axis: Weekly Average
    ax2 = ax1.twinx()
    ax2.plot(
        x,
        stats["Weekly Average"],
        color="red",
        marker="D",
        linewidth=2,
        label="Weekly Average (Spent)",
    )
    ax2.set_ylabel("Average Hours / Week", fontsize=12, color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    # Legend & Layout
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right")

    plt.title(
        f"Global Team Effort Analysis ({total_weeks:.1f} weeks)",
        fontsize=16,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.show(block=False)


def generate_milestone_member_stats_chart(member_df, milestone_name):
    """Generates a bar chart for member effort within a specific milestone."""
    m_stats = member_df[member_df["Milestone"] == milestone_name]
    if m_stats.empty:
        print(f"No data for milestone: {milestone_name}")
        return

    stats = (
        m_stats.groupby("Member")
        .agg({"Spent Distributed": "sum", "Estimate Distributed": "sum"})
        .reset_index()
    )
    stats = stats.sort_values(by="Spent Distributed", ascending=False)

    plt.figure(figsize=(12, 6))
    x = np.arange(len(stats["Member"]))
    width = 0.4

    plt.bar(
        x - width / 2,
        stats["Spent Distributed"],
        width,
        label="Hours Spent",
        color="#2ca02c",
    )
    plt.bar(
        x + width / 2,
        stats["Estimate Distributed"],
        width,
        label="Hours Estimated",
        color="#98df8a",
    )

    plt.xlabel("Team Member")
    plt.ylabel("Hours")
    plt.title(f"Effort per Member in Milestone: {milestone_name}", fontweight="bold")
    plt.xticks(x, stats["Member"], rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show(block=False)


def sub_menu_burndown(df):
    """Sub-menu for Burndown/Burnup charts."""
    milestones = df["Milestone"].dropna().unique()

    while True:
        print("\n--- Burndown/Burnup Charts ---")
        for i, m in enumerate(milestones, 1):
            print(f"{i}. {m}")
        print("-" * 28)
        print(f"{len(milestones) + 1}. Generate ALL Milestones")
        print("0. Back")

        choice = input("\nSelect a milestone (enter number): ").strip()

        if choice == "0":
            break

        try:
            choice_idx = int(choice)
            target_milestones = []
            if choice_idx == len(milestones) + 1:
                target_milestones = list(milestones)
            elif 1 <= choice_idx <= len(milestones):
                target_milestones = [milestones[choice_idx - 1]]
            else:
                print("Invalid choice.")
                continue

            # Pre-process for burndown sizing
            m_df_master = df.copy()
            if "Weight" in m_df_master.columns and m_df_master["Weight"].notna().any():
                m_df_master["Size"] = pd.to_numeric(
                    m_df_master["Weight"], errors="coerce"
                ).fillna(0)
                y_label = "Story Points"
            else:
                m_df_master["Size"] = m_df_master["Time Estimate"].apply(parse_time)
                y_label = "Hours"

            m_df_master["Created At (UTC)"] = pd.to_datetime(
                m_df_master["Created At (UTC)"]
            ).dt.tz_localize(None)
            m_df_master["Closed At (UTC)"] = pd.to_datetime(
                m_df_master["Closed At (UTC)"], errors="coerce"
            ).dt.tz_localize(None)

            for item in target_milestones:
                m_df = m_df_master[m_df_master["Milestone"] == item].copy()
                if m_df.empty:
                    continue
                is_sprint = any(k.lower() in str(item).lower() for k in SPRINT_KEYWORDS)
                generate_burndown(m_df, item, is_sprint, f"Remaining {y_label}")

        except ValueError:
            print("Please enter a number.")


def sub_menu_spent_hours(df):
    """Sub-menu for Spent Hours charts."""
    member_df, total_weeks = process_member_data(df)
    milestones = df["Milestone"].dropna().unique()

    while True:
        print("\n--- Member Spent Hours Charts ---")
        print("1. Global Member Effort (Project Total)")
        print("2. Milestone Effort Analysis")
        print("0. Back")

        choice = input("\nSelect an option: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            generate_member_stats_chart(member_df, total_weeks)
        elif choice == "2":
            print("\n--- Select Milestone ---")
            for i, m in enumerate(milestones, 1):
                print(f"{i}. {m}")
            print("0. Back")
            m_choice = input("\nSelect a milestone: ").strip()
            if m_choice == "0":
                continue
            try:
                m_idx = int(m_choice)
                if 1 <= m_idx <= len(milestones):
                    generate_milestone_member_stats_chart(
                        member_df, milestones[m_idx - 1]
                    )
                else:
                    print("Invalid milestone.")
            except ValueError:
                print("Please enter a number.")
        else:
            print("Invalid choice.")


def main():
    print("=== GitLab Work Item Analytics ===")

    # 1. Automatic File Detection
    csv_files = list_csv_files()
    if not csv_files:
        print(f"Error: No CSV files found in {DATA_GITLAB_FOLDER}.")
        return

    print("\n--- Available Data Files ---")
    for i, f in enumerate(csv_files, 1):
        print(f"{i}. {f.name}")

    file_choice = input("\nSelect a data file (enter number): ").strip()
    try:
        f_idx = int(file_choice)
        if 1 <= f_idx <= len(csv_files):
            file_path = csv_files[f_idx - 1]
            df = pd.read_csv(file_path)
            print(f"Loaded: {file_path.name}")
        else:
            print("Invalid file selection. Exiting.")
            return
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 2. Initial Project Summary
    total_spent = df["Time Spent"].apply(parse_time).sum()
    total_estimate = df["Time Estimate"].apply(parse_time).sum()
    print("\n" + "=" * 30)
    print("OVERALL PROJECT SUMMARY")
    print(f"Total Hours Spent:    {total_spent:.2f}h")
    print(f"Total Hours Estimated: {total_estimate:.2f}h")
    print("=" * 30)

    # 3. Main Menu
    while True:
        print("\n=== Main Menu ===")
        print("1. Burndown / Burnup Charts")
        print("2. Member Spent Hours Charts")
        print("0. Exit")

        main_choice = input("\nSelect an option: ").strip()

        if main_choice == "0":
            print("Exiting. Goodbye!")
            break
        elif main_choice == "1":
            sub_menu_burndown(df)
        elif main_choice == "2":
            sub_menu_spent_hours(df)
        else:
            print("Invalid option.")

    plt.show()


if __name__ == "__main__":
    main()
