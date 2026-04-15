# Project Management & Analytics Folder

This directory contains essential tools and information for tracking the team's progress and individual contributions throughout the project.

## Team Profiles
Detailed information about each team member can be found in the [profiles](./profiles/) directory. Our team consists of:

*   **Pedro Silva** (@Pedr0S22)
*   **Beatriz Fernandes** (@2023215703BeaFernandes)
*   **Francisca Mateus** (@franciscamateusPt05)
*   **Ramyad Raadi** (@Ramyad20)
*   **Rebeca Power** (@reberapower1)

## Work Item Analytics
The [milestone-progress](./milestone-progress/) directory houses our data-driven analytics engine, `management_charts_generator.py`. This script processes GitLab export data to provide deep insights into project velocity and team effort.

### Key Features
*   **Automatic Data Discovery:** Automatically scans the `data-gitlab` folder for CSV exports, allowing you to select the dataset via a numbered menu.
*   **Burndown & Burnup Charts:** 
    *   **Strategic Milestones:** Tracks high-level project goals.
    *   **Tactical Sprints:** Monitors weekly iteration progress.
    *   **Sizing Logic:** Supports both Story Points (Weight) and Time Estimates.
    *   **Forecasting:** Includes an "Estimated Delivery" trendline based on current velocity.
*   **Team Effort Analysis:**
    *   **Spent vs. Estimated:** Compares hours actually logged against initial estimates for every member.
    *   **Fair Time Distribution:** Distributes an issue's time equally among all its assignees to prevent overcounting and ensure accurate metrics.
    *   **Weekly Averages:** Calculates the average weekly contribution per member over the project's lifetime.
    *   **Dual-Axis Visualization:** Uses a secondary Y-axis to compare high-magnitude total hours with lower-magnitude weekly averages in a single view.
*   **Hierarchical Menu System:** A structured CLI interface that allows you to navigate between global statistics and milestone-specific charts easily.

### How to Run
To generate charts, navigate to the `Management/milestone-progress/` directory and run:
```bash
python management_charts_generator.py
```
Follow the interactive prompts to select your data source and the specific analytics you wish to visualize.
