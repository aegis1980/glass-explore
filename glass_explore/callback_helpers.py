#(c)2026 Jon Robinson. All Rights Reserved.


from urllib.parse import urlparse

import pandas as pd
from icecream import ic
import plotly.graph_objects as go
from dash import html


import glass_explore
from glass_explore import ALL_MANUFACTURERS, COLORSPACE_LAB, COLORSPACE_RGB,SelectedPointProps, utils

GRAPH_CUSTOMDATA_COLUMNS = ['ID', 'Manufacturer', 'ProductName']


def graph_customdata(df: pd.DataFrame):
    return df.loc[:, GRAPH_CUSTOMDATA_COLUMNS].to_numpy()


def clickdata_for_glass_id(glass_id):
    return {'points': [{'customdata': [int(glass_id)]}]}


def coating_surface_control(coated_side):
    """
    Label, options and help text of the coating surface picker for a product.

    The option values are always the surface numbers 1-4 (utils.lite_placement_from_surface),
    so the selection carries over from one product to the next. Only the wording changes: a
    lite coated on both faces or on neither has no single coated surface to name, so its four
    placements are described as position and flip instead.
    """
    if utils.has_single_coated_face(coated_side):
        return (
            "Coating on surface",
            [{"label": str(s), "value": s} for s in utils.COATING_SURFACES],
            "Numbered from outside: 1 and 2 are the outer lite, 3 and 4 the inner lite.",
        )

    options = [
        {"label": "Outer", "value": 2},
        {"label": "Outer, flipped", "value": 1},
        {"label": "Inner", "value": 4},
        {"label": "Inner, flipped", "value": 3},
    ]
    if str(coated_side).upper() == 'BOTH':
        return "Position", options, "This glass is coated on both faces; flipping swaps them."
    return "Position", options, "This glass has no surface coating."


def number_of_glasses_message(df, manufacturer, thickness):

    if len(df.index)==0:
        msg = f'No glasses from {manufacturer} with thickness, {thickness}mm'
        msg_color = 'red'
    else:
        msg = f'{len(df.index)} glasses'
        msg_color = 'darkgrey'
    return msg, msg_color

def search_message(found, filtered, manufacturer, thickness):
    """
    Text and colour of the line under the search modal's filters.

    Args:
        found: search.SearchResult
        filtered: True when a manufacturer or a thickness is selected in the modal
        manufacturer, thickness: the modal's filters (thickness None for any), for the wording
    """
    shown = len(found.ids)

    if not found.has_query:
        if found.total == 0:
            where = manufacturer if thickness is None else f'{manufacturer} with thickness, {thickness}mm'
            return f'No glasses from {where}', 'red'
        if shown < found.total:
            return f'Showing the first {shown} of {found.total} glasses; type to search', 'darkgrey'
        return ('1 glass' if found.total == 1 else f'{found.total} glasses'), 'darkgrey'

    if found.total == 0:
        if filtered and found.total_unfiltered:
            return f'No match with these filters; {found.total_unfiltered} without them', 'red'
        return 'No match', 'red'

    if found.similar:
        msg = f'No exact match; {found.total} with similar spelling'
    else:
        msg = '1 match' if found.total == 1 else f'{found.total} matches'
    if shown < found.total:
        msg += f' (first {shown} shown)'
    return msg, 'darkgrey'


def results_summary(props, standard, uvalue, shgc, tvis):
    """
    Children of the summary bar (energy_layout.summary_bar): the selected glass and the
    headline results, labelled as in the results table for the standard.
    """
    solar_label, visible_label = ("SHGC", "Tvis") if standard == "nfrc" else ("g", "τᵥ")
    return [
        html.Div(props['ProductName'], className="summary-bar-product"),
        html.Div(
            [
                html.Span(["U ", html.Strong(uvalue)]),
                html.Span([f"{solar_label} ", html.Strong(shgc)]),
                html.Span([f"{visible_label} ", html.Strong(tvis)]),
                html.I(className="bi bi-chevron-down"),
            ],
            className="summary-bar-values",
        ),
    ]


def populate_standards(include_interesting):
    standards = glass_explore.standards()
    if include_interesting:
        options = [{"label" : s['description'], "value" : s['filename']} for s in standards]
    else:
        options = [{"label" : s['description'], "value" : s['filename']} for s in standards if s['interesting'] == False]
    return options
    

def populate_graph_ts_tv(selected_id : int, df: pd.DataFrame, manufacturer, thickness: int):
    """
    Generates Tsolar vs Tvisible graph

    Args:
        selected_id (int) : id of selected glass
        df (_type_): _description_
        manufacturer (_type_): _description_
        thickness (int): _description_
    """
    fig = go.Figure()
    if manufacturer == ALL_MANUFACTURERS:
        msg,msg_color = number_of_glasses_message(df,manufacturer,thickness)
        fig.add_trace(
            go.Scatter(
                name="all",
                mode='markers',
                x=df["Tsol"],
                y=df["Tvis"],
                customdata=graph_customdata(df),
                marker=dict(
                    color=df['CssColor'],
                    size=10,
                ),

                showlegend=False,
                hovertemplate = 
                    '<b>id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[1]}' +
                    '<br>%{customdata[2]}'
            )
        )
       
    else:
        mask_na = (df['Manufacturer'] != manufacturer)
        mask = (df['Manufacturer'] == manufacturer)

        msg,msg_color = number_of_glasses_message(df[mask],manufacturer,thickness)

        fig.add_trace(
            go.Scatter(
                name="all",
                mode='markers',
                x=df[mask_na]["Tsol"],
                y=df[mask_na]["Tvis"],
                marker=dict(
                    color=df[mask_na]['CssColor'],
                    opacity = 0.4,
                    size=10,
                ),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        fig.add_trace(
            go.Scatter(
                name="manufacturer",
                mode='markers',
                x=df[mask]["Tsol"],
                y=df[mask]["Tvis"],
                customdata=graph_customdata(df[mask]),
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=20,
                    line=dict(
                        color='Red',
                        width=1
                    )
                ),
                showlegend=False,
                hovertemplate = 
                    '<b>id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[1]}' +
                    '<br>%{customdata[2]}'
            )
        )
   
    if selected_id:
        mask = (df['ID'] == int(selected_id))

        fig.add_trace(
            go.Scatter(
                name="selected_id",
                mode='markers',
                x=df[mask]["Tsol"],
                y=df[mask]["Tvis"],
                customdata=graph_customdata(df[mask]),
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=SelectedPointProps.SIZE_2D,
                    line=dict(
                        color=SelectedPointProps.THICKNESS_OUTLINE,
                        width=SelectedPointProps.THICKNESS_OUTLINE
                    )
                ),
                showlegend=False,
                hoverinfo='skip'
            )
        )    


    fig.update_layout(
        xaxis_title="T<sub>solar</sub>",
        yaxis_title="T<sub>visible</sub>",
        plot_bgcolor = "white",
        hovermode = 'closest',
        uirevision='constant-id-to-preserve-zoom-and-pan',
        # Both axes have a fixed range, so there is nothing to drag. With no drag mode a
        # finger on the graph scrolls the page instead of being swallowed by the plot.
        dragmode=False,
        # Plotly's default margins (80-100 px) leave little of a phone's width for the plot
        margin=dict(l=60, r=20, t=40, b=60),
    )

    fig.update_xaxes(
        dtick=0.1, 
        range=[0, 1],
        zeroline = False,
        fixedrange=True,
        showgrid = True,
        gridcolor='LightGrey',
        minor=dict(showgrid=True)
      #  autorange="reversed",
      #  constrain="domain",  # meanwhile compresses the xaxis by decreasing its "domain"
    ) 
    fig.update_yaxes(
        dtick=0.1, 
        range=[0, 1],
        zeroline = False,
        fixedrange=True,
        showgrid = True,
        gridcolor='LightGrey',
        minor=dict(showgrid=True)
    )

    return fig, msg, msg_color 


# The colour space graphs: the glass table columns plotted on x, y and z, the axis titles and
# the number format of the values in the hover text.
_COLORSPACE_AXES = {
    COLORSPACE_RGB: (("RColor", "GColor", "BColor"), ("R", "G", "B"), ".0f"),
    COLORSPACE_LAB: (("lColor", "aColor", "bColor"), ("L*", "a*", "b*"), ".1f"),
}


def populate_graph_colorspace(selected_id,df, manufacturer, thickness, colorspace : int):
    """
    Generates the 3D graph of the glasses' colours, in RGB or CIE L*a*b* coordinates

    Args:
        selected_id (int) : id of selected glass
        df (pd.DataFrame): glass table, already filtered to the thickness
        manufacturer (str): manufacturer to pick out, or ALL_MANUFACTURERS
        thickness (int): thickness in mm, for the message
        colorspace (int): COLORSPACE_RGB or COLORSPACE_LAB
    """
    (x_col, y_col, z_col), (x_title, y_title, z_title), fmt = _COLORSPACE_AXES.get(colorspace, _COLORSPACE_AXES[COLORSPACE_LAB])

    hovertemplate = (
        '<b>id</b>: %{customdata[0]}' +
        f'<br>(<b>{x_title}</b>: %{{x:{fmt}}} <b>{y_title}</b>: %{{y:{fmt}}} <b>{z_title}</b>: %{{z:{fmt}}})' +
        '<br>%{customdata[1]}' +
        '<br>%{customdata[2]}' +
        '<extra></extra>'  # no box with the trace name beside the label
    )

    fig = go.Figure()
    if manufacturer == ALL_MANUFACTURERS:

        msg,msg_color = number_of_glasses_message(df,manufacturer,thickness)

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[x_col],
                y=df[y_col],
                z=df[z_col],
                customdata=graph_customdata(df),
                marker=dict(
                    color=df['CssColor'],
                    size=3,
                ),

                showlegend=False,
                hovertemplate=hovertemplate
            )
        )

    else:
        mask_na = (df['Manufacturer'] != manufacturer)
        mask = (df['Manufacturer'] == manufacturer)

        msg,msg_color = number_of_glasses_message(df[mask],manufacturer,thickness)

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[mask_na][x_col],
                y=df[mask_na][y_col],
                z=df[mask_na][z_col],
                marker=dict(
                    color=df[mask_na]['CssColor'],
                    opacity = 0.4,
                    size=3,
                ),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[mask][x_col],
                y=df[mask][y_col],
                z=df[mask][z_col],
                customdata=graph_customdata(df[mask]),
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=6,
                    line=dict(
                        color='red',
                        width=2
                    )
                ),
                showlegend=False,
                hovertemplate=hovertemplate
            )
        )

    if selected_id:
        mask = (df['ID'] == int(selected_id))

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[mask][x_col],
                y=df[mask][y_col],
                z=df[mask][z_col],
                customdata=graph_customdata(df[mask]),
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=SelectedPointProps.SIZE_3D,
                    line=dict(
                        color=SelectedPointProps.COLOR_OUTLINE,
                        width=SelectedPointProps.THICKNESS_OUTLINE
                    )
                ),
                showlegend=False,
                hoverinfo='skip'
            )

        )

    # Without these the axes are titled x, y and z
    fig.update_scenes(xaxis_title_text=x_title, yaxis_title_text=y_title, zaxis_title_text=z_title)

    # A little further back than plotly's default eye (1.25 on each axis) and aimed slightly
    # below the middle of the box, which lifts it in the frame. The default view crops the
    # axis labels at the bottom of the scene, most of all in the square graph of a phone.
    fig.update_scenes(camera_eye=dict(x=1.5, y=1.5, z=1.3), camera_center=dict(x=0, y=0, z=-0.12))

    # Keep the user's camera (rotation, zoom) when the figure is updated, for example when
    # the highlight moves on a click; without a uirevision plotly resets the view each time.
    # One value per colour space, so each still opens in the default view.
    # No margins beyond room for the mode bar: the scene keeps its own space around the axes.
    fig.update_layout(uirevision=f'colorspace-{colorspace}', margin=dict(l=0, r=0, t=40, b=0))

    return fig, msg, msg_color


def populate_datatable(df : pd.DataFrame, manufacturer : str,thickness : float) -> pd.DataFrame:
    """_summary_

    Args:
        selected_id (int): _description_
        df (pd.DataFrame): _description_
        manufacturer (str): _description_
        thickness (float): _description_

    Returns:
        pd.DataFrame: dataframe
    """


    if manufacturer == ALL_MANUFACTURERS:
        msg,msg_color = number_of_glasses_message(df,manufacturer,thickness)
        return df,msg,msg_color
    else:
        mask = (df['Manufacturer'] == manufacturer)
        msg,msg_color = number_of_glasses_message(df[mask],manufacturer,thickness)
        return df[mask],msg,msg_color


def get_root_netloc(url) -> str:
    r = urlparse(url)
    return f'{r.scheme}://{r.netloc}'


def round_to_nearest_even(x : float) -> int:
    return int(round(x / 2.) * 2)
