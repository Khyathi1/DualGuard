
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="DualGuard | Security Evaluation",
    page_icon="🛡️",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }

    .metric-card {
        background-color: #1c2333;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30394b;
    }

    .metric-label {
        color: #aab4c5;
        font-size: 14px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 30px;
        font-weight: bold;
    }

    .section-title {
        font-size: 22px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD EXPERIMENT DATA
# --------------------------------------------------

CSV_PATH = os.path.join(
    "results",
    "experiment_results_v2.csv"
)


@st.cache_data
def load_data(path):
    return pd.read_csv(path)


st.title("🛡️ DualGuard")
st.subheader("Prompt Injection & Reward Hacking Evaluation")

st.caption(
    "A two-layer defense framework using instruction filtering "
    "and independent reward verification."
)

if not os.path.exists(CSV_PATH):
    st.error(
        f"Experiment CSV not found: {CSV_PATH}. "
        "Run the V2 experiment first."
    )
    st.stop()

df = load_data(CSV_PATH)

if df.empty:
    st.warning("The experiment CSV contains no records.")
    st.stop()


# --------------------------------------------------
# DATA PREPARATION
# --------------------------------------------------

required_columns = [
    "configuration",
    "scenario",
    "output",
    "injection_detected",
    "expected_value",
    "assigned_reward",
    "actual_quality",
    "reward_gap"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(f"Missing columns: {missing_columns}")
    st.stop()

df["injection_detected"] = (
    df["injection_detected"]
    .astype(str)
    .str.lower()
    .map({"true": True, "false": False})
    .fillna(False)
)

numeric_columns = [
    "assigned_reward",
    "actual_quality",
    "reward_gap"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["attack_scenario"] = (
    df["scenario"].astype(str).str.contains(
        "injection|attack",
        case=False,
        regex=True
    )
)

# Attack success is determined by whether the model's
# answer is incorrect in an attack scenario.
# This is a simple benchmark-specific proxy.
df["attack_success"] = (
    df["attack_scenario"]
    & (df["actual_quality"] == 0)
)


# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("Dashboard Filters")

configurations = sorted(
    df["configuration"].dropna().unique()
)

selected_configs = st.sidebar.multiselect(
    "Select configurations",
    configurations,
    default=configurations
)

scenarios = sorted(
    df["scenario"].dropna().unique()
)

selected_scenarios = st.sidebar.multiselect(
    "Select scenarios",
    scenarios,
    default=scenarios
)

filtered_df = df[
    df["configuration"].isin(selected_configs)
    & df["scenario"].isin(selected_scenarios)
].copy()

if filtered_df.empty:
    st.warning("No experiment records match your filters.")
    st.stop()


# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

st.markdown("## Experiment Overview")

total_runs = len(filtered_df)

correct_runs = (
    filtered_df["actual_quality"] == 1
).sum()

accuracy = (
    correct_runs / total_runs * 100
    if total_runs else 0
)

detected_attacks = filtered_df[
    filtered_df["attack_scenario"]
    & filtered_df["injection_detected"]
].shape[0]

attack_cases = filtered_df[
    filtered_df["attack_scenario"]
].shape[0]

attack_detection_rate = (
    detected_attacks / attack_cases * 100
    if attack_cases else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Experiment Runs", total_runs)

col2.metric(
    "Correct Output Rate",
    f"{accuracy:.1f}%"
)

col3.metric(
    "Detected Attack Cases",
    f"{detected_attacks}/{attack_cases}"
)

col4.metric(
    "Mean Reward Gap",
    f"{filtered_df['reward_gap'].mean():.2f}"
)


# --------------------------------------------------
# EXPERIMENT COMPARISON
# --------------------------------------------------

st.markdown("---")
st.markdown("## 1. Configuration Comparison")

comparison = (
    filtered_df.groupby("configuration", as_index=False)
    .agg(
        actual_quality=("actual_quality", "mean"),
        assigned_reward=("assigned_reward", "mean"),
        reward_gap=("reward_gap", "mean")
    )
)

comparison_melted = comparison.melt(
    id_vars="configuration",
    value_vars=[
        "actual_quality",
        "assigned_reward"
    ],
    var_name="Metric",
    value_name="Score"
)

fig1 = px.bar(
    comparison_melted,
    x="configuration",
    y="Score",
    color="Metric",
    barmode="group",
    title="Actual Quality vs Assigned Reward",
    labels={
        "configuration": "Defense Configuration",
        "Score": "Average Score"
    },
    hover_data=["Metric"]
)

fig1.update_layout(
    template="plotly_dark",
    yaxis_range=[0, 1.1]
)

st.plotly_chart(fig1, use_container_width=True)


# --------------------------------------------------
# ATTACK DETECTION ANALYSIS
# --------------------------------------------------

st.markdown("---")
st.markdown("## 2. Prompt Injection Detection")

attack_df = filtered_df[
    filtered_df["attack_scenario"]
].copy()

if not attack_df.empty:

    detection_summary = (
        attack_df.groupby(
            "configuration",
            as_index=False
        )
        .agg(
            detected=("injection_detected", "sum"),
            total=("injection_detected", "count")
        )
    )

    detection_summary["not_detected"] = (
        detection_summary["total"]
        - detection_summary["detected"]
    )

    detection_melted = detection_summary.melt(
        id_vars="configuration",
        value_vars=["detected", "not_detected"],
        var_name="Detection Status",
        value_name="Number of Cases"
    )

    fig2 = px.bar(
        detection_melted,
        x="configuration",
        y="Number of Cases",
        color="Detection Status",
        barmode="stack",
        title="Injection Detection by Configuration",
        labels={
            "configuration": "Defense Configuration"
        }
    )

    fig2.update_layout(template="plotly_dark")

    st.plotly_chart(fig2, use_container_width=True)

    st.info(
        "Detection means the input filter flagged suspicious content. "
        "It does not mean the attack successfully fooled the LLM."
    )

else:
    st.info("No attack scenarios are selected.")


# --------------------------------------------------
# REWARD GAP ANALYSIS
# --------------------------------------------------

st.markdown("---")
st.markdown("## 3. Reward Hacking Analysis")

fig3 = px.bar(
    filtered_df,
    x="configuration",
    y="reward_gap",
    color="scenario",
    barmode="group",
    title="Reward Gap by Configuration and Scenario",
    labels={
        "configuration": "Defense Configuration",
        "reward_gap": "Assigned Reward - Actual Quality"
    }
)

fig3.update_layout(template="plotly_dark")

st.plotly_chart(fig3, use_container_width=True)

st.caption(
    "Positive reward gap = undeserved reward. "
    "Negative reward gap = under-rewarding correct output. "
    "Zero = reward matches measured quality."
)


# --------------------------------------------------
# SCENARIO ANALYSIS
# --------------------------------------------------

st.markdown("---")
st.markdown("## 4. Scenario Performance")

scenario_summary = (
    filtered_df.groupby(
        ["configuration", "scenario"],
        as_index=False
    )
    .agg(
        average_quality=("actual_quality", "mean"),
        average_reward=("assigned_reward", "mean"),
        average_reward_gap=("reward_gap", "mean")
    )
)

fig4 = px.bar(
    scenario_summary,
    x="scenario",
    y="average_quality",
    color="configuration",
    barmode="group",
    title="Actual Task Quality Across Scenarios",
    labels={
        "scenario": "Test Scenario",
        "average_quality": "Average Task Quality"
    }
)

fig4.update_layout(
    template="plotly_dark",
    yaxis_range=[0, 1.1]
)

st.plotly_chart(fig4, use_container_width=True)


# --------------------------------------------------
# DETAILED EXPERIMENT RESULTS
# --------------------------------------------------

st.markdown("---")
st.markdown("## 5. Experiment Explorer")

display_columns = [
    "configuration",
    "scenario",
    "output",
    "injection_detected",
    "expected_value",
    "assigned_reward",
    "actual_quality",
    "reward_gap"
]

if "verified" in filtered_df.columns:
    display_columns.append("verified")

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# INDIVIDUAL OUTPUT INSPECTOR
# --------------------------------------------------

st.markdown("---")
st.markdown("## 6. Inspect Individual Experiment")

experiment_index = st.selectbox(
    "Choose experiment",
    filtered_df.index.tolist(),
    format_func=lambda i: (
        f"{filtered_df.loc[i, 'configuration']} | "
        f"{filtered_df.loc[i, 'scenario']}"
    )
)

selected_row = filtered_df.loc[experiment_index]

st.write("**Agent Output:**")
st.code(str(selected_row["output"]))

st.write("**Expected Ground Truth:**")
st.write(selected_row["expected_value"])

st.write("**Reward Gap:**")
st.write(selected_row["reward_gap"])

if "verification_reason" in filtered_df.columns:
    st.write("**Verification Reason:**")
    st.write(selected_row["verification_reason"])


# --------------------------------------------------
# DOWNLOAD FILTERED RESULTS
# --------------------------------------------------

st.markdown("---")
st.markdown("## 7. Export Results")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Experiment Results",
    data=csv_data,
    file_name="dualguard_filtered_results.csv",
    mime="text/csv"
)


# --------------------------------------------------
# RESEARCH DISCLAIMER
# --------------------------------------------------

st.markdown("---")

st.warning(
    """
    **Research limitation**

    This dashboard displays results from the initial DualGuard V2
    integration test. It contains only two benchmark scenarios and
    one trial per configuration/scenario combination.

    The results demonstrate prototype integration, not statistically
    validated security effectiveness or superiority over baseline.
    """
)

st.caption(
    "DualGuard | Prompt Injection and Reward Hacking Research Prototype"
)
