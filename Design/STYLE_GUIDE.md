# Graphic Standards Manual - V1.0

# Introduction

This document establishes the graphic standards and user interface guidelines for the Climate-Driven Energy Demand Analytics System project. Its primary purpose is to ensure visual consistency, usability, and accessibility across all system interfaces.

# Color Palette

## Surfaces & Backgrounds

* **Main Window Background**: #CCCCCC - Used for the primary application background.

* **Card/Info Background**: #EAEAEF - Used for containers, information, data display areas.

* **Sidebar/Menu Background**: #EAEAEF - Background for the navigation menu to separate it from the workspace.

* **Delimiters/Borders**: #000000 - Used for thin lines and borders to define boundaries.

## Interactive Elements (Buttons)

* **Submission & Authentication Buttons**: #000180 - Used for "Login", "Register", and "Submit Changes" to commit data or trigger the authentication layer.

* **Selectable Model Cards**: #000180 - Used for choosing between different options.

* **Reset**: #800002 - Used when selecting a prediction model.

* **Session Control**: #83E7FF - Used for "Logout" to clearly identify the action that terminates the secured session.

## Text

* **Primary Body Text**: #000000 - Standard color for general information and descriptions.

* **Active Page Indicator**: #000180 - High-contrast color used to highlight the current section in the navigation menu.

* **Page heading/Title**:  #FFFFFF - Used for page titles and main section headers.

* **Secondary/Muted Text**: #262626 - Used for less critical information or descriptive hints that should not distract from the main content.

# Typography

* **Page Heading/Titles**: Tw Cen MT Condensed, 48, Bold – Used for main section headers and page titles to establish a clear visual hierarchy.

* **General Body Text**: Tw Cen MT Condensed, 36, Regular – Used for descriptions and general findings within the dashboard.

* **Interactive Elements (Buttons)**: Tw Cen MT, 70, Bold – A high-readability font selected specifically for buttons (such as Login, Register, Submit changes).

* **Session Control**: Tw Cen MT, 50, Bold - Used for "Logout" to clearly identify the action that terminates the secured session.

* **Data Displays & Tables**: Tw Cen MT Condensed, Variable Size, Regular – Used for tabular data, chart labels, and information displays. The font size is dynamic to adapt to different screen resolutions and container sizes, ensuring that values remain legible under all conditions.

# Components Design

## Buttons & Action Elements

* **Shape**: Rounded Rectangles.

* **Corner Radius**: 40° (px).

* **Usage**: Applied to all primary and secondary buttons, including "Login", "Register", "Submit", and "Reset".

## Information Containers (Cards)

* **Shape**: Rounded Rectangles.

* **Corner Radius**: 5° (px).

* **Usage**: Used for background cards that house charts and the prediction output displays.

## Input Fields

* **Shape**: Rectangles with rounded corners.

* **Corner Radius**: 0 px.

* **Usage**: Dedicated to the authentication layer fields and forms.

## Sidemenu & Navigation

* **Shape**: Vertical Rectangular Panel.

* **Corner Radius**: 5°.

* **Usage**: Houses the "Active Page Indicator" and navigation links.

# Data Visualization

## Chart Axes & Resolution

* **X-Axis**: Represents the temporal Attribute. Depending on the view, this displays the date or hour.

* **Y-Axis**: Represents the electricity load demand, expressed in Megawatts (MW).

## Line Styles & Data Distinction

* **Solid Line (Historical Data)**: Used for the three days prior to the current date, representing real values.

* **Dashed Line (Forecasted Data)**: Used for the seven-day forecast horizon, representing the predictive values.

## Interactive Hover

* **Functionality**: A dynamic hover effect is implemented for both the solid and dashed lines.

* **Content**: When the cursor moves over any data point, a tooltip appears instantly.

* **Information**: It provides a quick and easy-to-read summary of the exact electrical demand for that point.

# Feedback States

* **Placement and Design**: Both success and error messages appear in cards positioned in the middle of the screen.

* **Error Visual Indicator**: Error messages include a warning icon represented by a yellow triangle with an exclamation mark.

* **Card Geometry**: These feedback cards follow the system's structural standards, maintaining consistency with other interface components.
