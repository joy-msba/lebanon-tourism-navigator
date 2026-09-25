import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# PAGE SETUP

st.set_page_config(
    page_title="Lebanon Tourism Opportunity Navigator",
    page_icon="🇱🇧",
    layout="wide"
)

st.image("lebanon-header-1.jpg", use_container_width=True)


st.title("Lebanon Tourism Opportunity Navigator")

st.caption("Based on Lebanon tourism data from 2023")

st.markdown(
    """
    This tool helps NGOs and development organizations **screen potential
    tourism opportunities**, understand local tourism service conditions,
    and identify towns that may benefit from further assessment.

    **Potential Untapped Opportunity** = a developable tourism attraction is
    consistently identified, while no tourism initiative is recorded during
    the past five years.
    """
)


# LOAD DATA

def load_data():
    return pd.read_csv("Tourism-Lebanon-2023.csv")


df = load_data()


# PREPARE DATA

initiative_col = (
    "Existence of initiatives and projects in the past five years "
    "to improve the tourism sector - exists"
)

attraction_yes_col = (
    "Existence of touristic attractions prone to be exploited "
    "and developed - exists"
)

attraction_no_candidates = [
    "Existence of touristic attractions that can be expolited and developed - does not exist",
    "Existence of touristic attractions prone to be exploited and developed - does not exist"
]

attraction_no_col = next(
    (
        col
        for col in attraction_no_candidates
        if col in df.columns
    ),
    None
)

if attraction_no_col is None:
    st.error("Attraction 'does not exist' column was not found.")
    st.stop()


data = pd.DataFrame({
    "Town":
        df["Town"].astype(str).str.strip(),

    "Tourism Index":
        pd.to_numeric(
            df["Tourism Index"],
            errors="coerce"
        ),

    "Hotels":
        pd.to_numeric(
            df["Total number of hotels"],
            errors="coerce"
        ).fillna(0),

    "Guest Houses":
        pd.to_numeric(
            df["Total number of guest houses"],
            errors="coerce"
        ).fillna(0),

    "Restaurants":
        pd.to_numeric(
            df["Total number of restaurants"],
            errors="coerce"
        ).fillna(0),

    "Cafés":
        pd.to_numeric(
            df["Total number of cafes"],
            errors="coerce"
        ).fillna(0),

    "Initiative Exists":
        pd.to_numeric(
            df[initiative_col],
            errors="coerce"
        ),

    "Attraction Exists":
        pd.to_numeric(
            df[attraction_yes_col],
            errors="coerce"
        ),

    "Attraction Does Not Exist":
        pd.to_numeric(
            df[attraction_no_col],
            errors="coerce"
        )
})

data["Area"] = (
        df["refArea"]
        .astype("string")
        .str.rstrip("/")
        .str.split("/")
        .str[-1]
        .str.replace("_", " ", regex=False)
    )


data["Accommodation"] = (
    data["Hotels"]
    + data["Guest Houses"]
)

data["Food Services"] = (
    data["Restaurants"]
    + data["Cafés"]
)


# STRATEGIC CLASSIFICATION

data["Potential Score"] = np.select(
    [
        (
            (data["Attraction Exists"] == 1)
            &
            (data["Attraction Does Not Exist"] == 0)
        ),

        (
            (data["Attraction Exists"] == 0)
            &
            (data["Attraction Does Not Exist"] == 1)
        )
    ],
    [1, 0],
    default=np.nan
)

data["Initiative Score"] = data["Initiative Exists"]


classified = data.dropna(
    subset=[
        "Potential Score",
        "Initiative Score"
    ]
).copy()


classified["Strategic Position"] = np.select(
    [
        (
            (classified["Potential Score"] == 1)
            &
            (classified["Initiative Score"] == 1)
        ),

        (
            (classified["Potential Score"] == 1)
            &
            (classified["Initiative Score"] == 0)
        ),

        (
            (classified["Potential Score"] == 0)
            &
            (classified["Initiative Score"] == 1)
        ),

        (
            (classified["Potential Score"] == 0)
            &
            (classified["Initiative Score"] == 0)
        )
    ],
    [
        "Attraction + Initiative",
        "Potential Untapped Opportunity",
        "Initiative Without Identified Attraction",
        "Neither Identified"
    ],
    default="Unclassified"
)


# TOURISM SERVICE SITUATION

service_labels = [
    "No Accommodation",
    "No Accommodation or Food Services",
    "No Food Services",
    "Accommodation & Food Services Present"
]


classified["Tourism Service Situation"] = np.select(
    [
        (
            (classified["Accommodation"] == 0)
            &
            (classified["Food Services"] > 0)
        ),

        (
            (classified["Accommodation"] == 0)
            &
            (classified["Food Services"] == 0)
        ),

        (
            (classified["Accommodation"] > 0)
            &
            (classified["Food Services"] == 0)
        ),

        (
            (classified["Accommodation"] > 0)
            &
            (classified["Food Services"] > 0)
        )
    ],
    service_labels,
    default="Other"
)


untapped = classified[
    classified["Strategic Position"]
    == "Potential Untapped Opportunity"
].copy()

untapped["Treemap Size"] = 1


# STABLE JITTER FOR MATRIX

rng = np.random.default_rng(42)

classified["x_plot"] = (
    classified["Initiative Score"]
    + rng.uniform(
        -0.18,
        0.18,
        len(classified)
    )
)

classified["y_plot"] = np.where(
    classified["Potential Score"] == 1,

    classified["Potential Score"]
    + rng.uniform(
        -0.22,
        0.05,
        len(classified)
    ),

    classified["Potential Score"]
    + rng.uniform(
        -0.15,
        0.15,
        len(classified)
    )
)


# LEFT SIDEBAR — LINKED INTERACTIONS

with st.sidebar:

    st.header("Explore Opportunities")

    st.caption(
        "Start with a geographic area, then examine the "
        "tourism service situations available within it."
    )


    # INTERACTION 1 — GEOGRAPHIC AREA

    area_counts = untapped["Area"].value_counts()

    areas = sorted(
        classified["Area"]
        .dropna()
        .unique()
        .tolist()
    )


    area_display = {
        f"All Lebanon ({len(untapped)})":
            "All Lebanon"
    }


    for area in areas:

        count = int(
            area_counts.get(
                area,
                0
            )
        )

        area_display[
            f"{area} ({count})"
        ] = area


    selected_area_label = st.selectbox(
        "1. Geographic area",
        list(area_display.keys())
    )

    selected_area = area_display[
        selected_area_label
    ]


    if selected_area == "All Lebanon":

        matrix_view = classified.copy()
        area_untapped = untapped.copy()

    else:

        matrix_view = classified[
            classified["Area"]
            == selected_area
        ].copy()

        area_untapped = untapped[
            untapped["Area"]
            == selected_area
        ].copy()


    # INTERACTION 2 — TOURISM SERVICE SITUATION

    service_counts = (
        area_untapped[
            "Tourism Service Situation"
        ]
        .value_counts()
    )


    available_services = [
        service
        for service in service_labels
        if service in service_counts.index
    ]


    service_display = {
        f"All service situations ({len(area_untapped)})":
            "All service situations"
    }


    for service in available_services:

        count = int(
            service_counts.get(
                service,
                0
            )
        )

        service_display[
            f"{service} ({count})"
        ] = service


    selected_service_label = st.radio(
        "2. Tourism Service Situation",
        list(service_display.keys()),
        key=f"service_filter_{selected_area}"
    )


    selected_service = service_display[
        selected_service_label
    ]


    if selected_service == "All service situations":

        service_view = area_untapped.copy()

    else:

        service_view = area_untapped[
            area_untapped[
                "Tourism Service Situation"
            ]
            == selected_service
        ].copy()


    # INTERACTION JUSTIFICATION

    with st.expander(
        "Interaction Design Justification"
    ):

        st.markdown(
            """
            **1. Geographic Area**

            This helps answer: **Where are the potential tourism
            opportunities located?**

            I used a dropdown because there are many geographic areas and showing
            them all at once would make the sidebar too crowded. I considered using
            radio buttons, but they would take up too much space. The dropdown keeps
            the page simple and lets the user focus on one area at a time.

            **2. Tourism Service Situation**

            This helps answer: **What tourism service conditions are found in the selected area?**
            
            I used radio buttons because there are only a few mutually exclusive categories. 
            Showing the choices directly makes them easier to compare without requiring the user to open another menu. 
            I considered a dropdown, but it would hide a small set of important categories.

            The available options also change after a geographic area is selected.
            This creates a step by step drill-down using progressive disclosure:
            users first choose a location, then see only the service situations that
            are relevant within that location.
            """
        )


# OVERVIEW

m1, m2, m3 = st.columns(3)

m1.metric(
    "Total Towns",
    len(data)
)

m2.metric(
    "Towns Included in Analysis",
    len(classified)
)

m3.metric(
    "Potential Untapped Opportunities",
    len(untapped)
)


excluded = len(data) - len(classified)

if excluded > 0:

    with st.expander(
        "Why are some towns excluded?"
    ):

        st.write(
            f"{excluded} towns are not included in the strategic matrix "
            "because their attraction indicators do not provide a consistent "
            "classification or their initiative status is unavailable."
        )


# CURRENT VIEW

area_name = (
    "Lebanon"
    if selected_area == "All Lebanon"
    else selected_area
)

service_name = (
    "All service situations"
    if selected_service == "All service situations"
    else selected_service
)

st.markdown(
    f"**Current view:** {area_name} · {service_name}"
)


# TWO KEY INSIGHTS

st.subheader("Key Insights")


untapped_share = (
    len(area_untapped)
    / len(matrix_view)
    * 100
    if len(matrix_view) > 0
    else 0
)


insight1, insight2 = st.columns(2)


with insight1:

    st.info(
        f"""
        **Insight 1 — Strategic Opportunity**

        **{len(area_untapped)} of {len(matrix_view)}** towns included
        in the analysis for **{area_name}** are Potential Untapped
        Opportunities (**{untapped_share:.1f}%**).
        """
    )


with insight2:

    if area_untapped.empty:

        st.info(
            """
            **Insight 2 — Tourism Service Pattern**

            No Potential Untapped Opportunities are identified
            for this area.
            """
        )

    elif selected_service == "All service situations":

        top_service = service_counts.index[0]
        top_count = int(service_counts.iloc[0])

        st.info(
            f"""
            **Insight 2 — Tourism Service Pattern**

            The most common service situation in **{area_name}** is
            **{top_service}** (**{top_count} towns**).
            """
        )

    else:

        service_share = (
            len(service_view)
            / len(area_untapped)
            * 100
        )

        st.info(
            f"""
            **Insight 2 — Selected Tourism Service Situation**

            **{len(service_view)} towns** match **{selected_service}**,
            representing **{service_share:.1f}%** of Potential Untapped
            Opportunities in **{area_name}**.
            """
        )


# VISUAL 1 — STRATEGIC MATRIX

st.divider()

st.header(
    "1. Strategic Tourism Opportunity Matrix"
)

st.markdown(
    """
    This matrix compares whether a town has an identified
    **developable tourism attraction** with whether a **tourism initiative**
    has been recorded during the past five years.

    The upper-left quadrant identifies **Potential Untapped Opportunities**
    for further investigation.
    """
)


if matrix_view.empty:

    st.warning(
        "No towns are available for this geographic selection."
    )

else:

    fig_matrix = px.scatter(
        matrix_view,

        x="x_plot",
        y="y_plot",

        color="Strategic Position",

        hover_name="Town",

        hover_data={
            "Area": True,
            "x_plot": False,
            "y_plot": False
        },

        color_discrete_map={
            "Potential Untapped Opportunity":
                "#E85D36",

            "Attraction + Initiative":
                "#7FB69A",

            "Initiative Without Identified Attraction":
                "#7FA8C9",

            "Neither Identified":
                "#C9B79C"
        }
    )


    for trace in fig_matrix.data:

        if trace.name == "Potential Untapped Opportunity":

            trace.update(
                marker=dict(
                    size=14,
                    opacity=0.95,

                    line=dict(
                        width=1.2,
                        color="black"
                    )
                )
            )

        else:

            trace.update(
                marker=dict(
                    size=10,
                    opacity=0.65
                )
            )


    fig_matrix.add_vline(
        x=0.5,
        line_dash="dash",
        line_color="gray"
    )

    fig_matrix.add_hline(
        y=0.5,
        line_dash="dash",
        line_color="gray"
    )


    fig_matrix.add_shape(
        type="rect",

        x0=-0.35,
        x1=0.5,

        y0=0.5,
        y1=1.35,

        fillcolor="#FFF2CC",
        opacity=0.35,

        line_width=0,
        layer="below"
    )


    fig_matrix.add_annotation(
        x=0.03,
        y=1.27,

        text=(
            "<b>POTENTIAL UNTAPPED OPPORTUNITY</b><br>"
            "Developable attraction identified<br>"
            "No recent initiative recorded"
        ),

        showarrow=False,
        align="left"
    )


    fig_matrix.update_xaxes(
        tickvals=[0, 1],

        ticktext=[
            "No Initiative Recorded",
            "Initiative Recorded"
        ],

        title=(
            "Tourism Initiative in the Past Five Years"
        ),

        range=[
            -0.35,
            1.35
        ]
    )


    fig_matrix.update_yaxes(
        tickvals=[0, 1],

        ticktext=[
            "Not Identified",
            "Identified"
        ],

        title="Developable Tourism Attraction",

        range=[
            -0.35,
            1.35
        ]
    )


    fig_matrix.update_layout(
        template="plotly_white",
        height=600,
        legend_title_text="Strategic Position"
    )


    st.plotly_chart(
        fig_matrix,
        use_container_width=True
    )


# VISUAL 2 — TREEMAP

st.divider()

st.header(
    "2. Tourism Service Situation of Potential Opportunities"
)

st.markdown(
    """
    The treemap examines towns identified as **Potential Untapped
    Opportunities** and organizes them by:

    **Tourism Service Situation → Geographic Area → Town**

    Each town has equal visual weight so the chart supports exploration
    rather than ranking towns by importance.
    """
)


if service_view.empty:

    st.warning(
        "No towns match the current selections."
    )

else:

    fig_tree = px.treemap(
        service_view,

        path=[
            px.Constant(
                "Potential Untapped Opportunities"
            ),

            "Tourism Service Situation",
            "Area",
            "Town"
        ],

        values="Treemap Size",

        color="Tourism Service Situation",

        color_discrete_map={
            "No Accommodation":
                "#E8A87C",

            "No Accommodation or Food Services":
                "#C38D9E",

            "No Food Services":
                "#85CDCA",

            "Accommodation & Food Services Present":
                "#8FB996"
        },

        # These values are used in our custom tooltip.
        custom_data=[
            "Town",
            "Area",
            "Tourism Index",
            "Hotels",
            "Guest Houses",
            "Restaurants",
            "Cafés",
            "Tourism Service Situation"
        ]
    )


    # Completely replace Plotly's default label/parent tooltip
    fig_tree.update_traces(

        root_color="lightgrey",

        marker=dict(
            line=dict(
                width=1,
                color="white"
            )
        ),

        hovertemplate=(
            "<b>Town: %{customdata[0]}</b><br>"
            "Geographic Area: %{customdata[1]}<br>"
            "Tourism Index: %{customdata[2]}<br>"
            "Hotels: %{customdata[3]}<br>"
            "Guest Houses: %{customdata[4]}<br>"
            "Restaurants: %{customdata[5]}<br>"
            "Cafés: %{customdata[6]}<br>"
            "Tourism Service Situation: %{customdata[7]}"
            "<extra></extra>"
        )
    )


    fig_tree.update_layout(
        margin=dict(
            t=10,
            l=10,
            r=10,
            b=10
        ),

        height=600
    )


    st.plotly_chart(
        fig_tree,
        use_container_width=True
    )


st.caption(
    """
    Tourism Service situations identify observable conditions in the dataset.
    They do not by themselves establish visitor demand, community priorities,
    project feasibility, or funding need.
    """
)


# CURRENT TOWN SHORTLIST

if not service_view.empty:

    st.subheader("Current Town Shortlist")

    shortlist = (
        service_view[
            [
                "Town",
                "Area",
                "Tourism Service Situation",
                "Tourism Index",
                "Hotels",
                "Guest Houses",
                "Restaurants",
                "Cafés"
            ]
        ]
        .sort_values(
            [
                "Area",
                "Town"
            ]
        )
        .reset_index(drop=True)
    )


    with st.expander(
        f"View {len(shortlist)} towns"
    ):

        st.dataframe(
            shortlist,
            use_container_width=True,
            hide_index=True
        )


    st.download_button(
        "Download current town shortlist",

        data=shortlist.to_csv(
            index=False
        ).encode("utf-8"),

        file_name="tourism_opportunity_shortlist.csv",

        mime="text/csv"
    )


# METHODOLOGY

st.divider()

st.caption(
    """
    **Methodology:** Attraction status is classified only when the two
    attraction indicators provide a consistent result. Tourism Service
    categories describe facilities recorded in the dataset. This dashboard
    is a screening tool for further assessment and does not rank towns for
    funding or investment.
    """
)