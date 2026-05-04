#(c)2026 Jon Robinson. All Rights Reserved.


from urllib.parse import urlparse

import pandas as pd
from icecream import ic
import plotly.graph_objects as go


import glass_explore
from glass_explore import ALL_MANUFACTURERS, COLORSPACE_RGB,SelectedPointProps

GRAPH_CUSTOMDATA_COLUMNS = ['ID', 'Manufacturer', 'ProductName']


def graph_customdata(df: pd.DataFrame):
    return df.loc[:, GRAPH_CUSTOMDATA_COLUMNS].to_numpy()


def clickdata_for_glass_id(glass_id):
    return {'points': [{'customdata': [int(glass_id)]}]}


def number_of_glasses_message(df, manufacturer, thickness):

    if len(df.index)==0:
        msg = f'No glasses from {manufacturer} with thickness, {thickness}mm'
        msg_color = 'red'
    else:
        msg = f'{len(df.index)} glasses'
        msg_color = 'darkgrey'
    return msg, msg_color

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
        uirevision='constant-id-to-preserve-zoom-and-pan'
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


def populate_graph_colorspace(selected_id,df, manufacturer, thickness, colorspace : int):

    fig = go.Figure()
    if manufacturer == ALL_MANUFACTURERS:

        msg,msg_color = number_of_glasses_message(df,manufacturer,thickness)

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df["RColor"] if colorspace == COLORSPACE_RGB else df["lColor"],
                y=df["GColor"] if colorspace == COLORSPACE_RGB else df["aColor"],
                z=df['BColor'] if colorspace == COLORSPACE_RGB else df["bColor"],
                customdata=graph_customdata(df),
                marker=dict(
                    color=df['CssColor'],
                    size=3,
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
            go.Scatter3d(
                mode='markers',
                x=df[mask_na]["RColor"] if colorspace == COLORSPACE_RGB else df[mask_na]["lColor"],
                y=df[mask_na]["GColor"] if colorspace == COLORSPACE_RGB else df[mask_na]["aColor"],
                z=df[mask_na]['BColor'] if colorspace == COLORSPACE_RGB else df[mask_na]["bColor"],
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
                x=df[mask]["RColor"] if colorspace == COLORSPACE_RGB else df[mask]["lColor"],
                y=df[mask]["GColor"] if colorspace == COLORSPACE_RGB else df[mask]["aColor"],
                z=df[mask]['BColor'] if colorspace == COLORSPACE_RGB else df[mask]["bColor"],
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
                hovertemplate = 
                    '<b>nfrc_id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[1]}' +
                    '<br>%{customdata[2]}'
            )
        )

    if selected_id:
        mask = (df['ID'] == int(selected_id))

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[mask]["RColor"] if colorspace == COLORSPACE_RGB else df[mask]["lColor"],
                y=df[mask]["GColor"] if colorspace == COLORSPACE_RGB else df[mask]["aColor"],
                z=df[mask]['BColor'] if colorspace == COLORSPACE_RGB else df[mask]["bColor"],
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
