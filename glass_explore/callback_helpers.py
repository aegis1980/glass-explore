import functools

import plotly.graph_objects as go
import glass_explore
from glass_explore import ALL_MANUFACTURERS, GRAPHTYPE_RGB,SelectedPointProps


def populate_standards(include_interesting):
    standards = glass_explore.standards()
    if include_interesting:
        options = [{"label" : s['description'], "value" : s['filename']} for s in standards]
    else:
        options = [{"label" : s['description'], "value" : s['filename']} for s in standards if s['interesting'] == False]
    return options
    

def graphing_ts_tv(selected_id : int, df, manufacturer, thickness):
    """
    Generates Tsolar vs Tvisible graph

    Args:
        selected_id (int) : id of selected glass
        df (_type_): _description_
        manufacturer (_type_): _description_
        thickness (_type_): _description_
    """
    fig = go.Figure()
    if manufacturer == ALL_MANUFACTURERS:

        msg = f'{len(df.index)} glasses'
        color = 'darkgrey'
        fig.add_trace(
            go.Scatter(
                mode='markers',
                x=df["Tsol"],
                y=df["Tvis"],
                customdata=df,
                marker=dict(
                    color=df['CssColor'],
                    size=10,
                ),

                showlegend=False,
                hovertemplate = 
                    '<b>id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[17]}' + 
                    '<br>%{customdata[18]}'
            )
        )
       
    else:
        mask_na = (df['Manufacturer'] != manufacturer)
        mask = (df['Manufacturer'] == manufacturer)

        if len(df[mask].index)==0:
            msg = f'No glasses from {manufacturer} with thickness, {thickness}mm'
            color = 'red'
        else:
            msg = f'{len(df[mask].index)} glasses'
            color = 'darkgrey'

        fig.add_trace(
            go.Scatter(
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
                mode='markers',
                x=df[mask]["Tsol"],
                y=df[mask]["Tvis"],
                customdata=df[mask],
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
                    '<br>%{customdata[17]}' + 
                    '<br>%{customdata[18]}'
            )
        )
   
    if selected_id:
        mask = (df['ID'] == int(selected_id))

        fig.add_trace(
            go.Scatter(
                mode='markers',
                x=df[mask]["Tsol"],
                y=df[mask]["Tvis"],
                customdata=df[mask],
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=SelectedPointProps.SIZE_2D,
                    line=dict(
                        color=SelectedPointProps.THICKNESS_OUTLINE,
                        width=SelectedPointProps.THICKNESS_OUTLINE
                    )
                ),
                showlegend=False
            )
        )    


    fig.update_layout(
        xaxis_title="T<sub>solar</sub>",
        yaxis_title="T<sub>visible</sub>",
        plot_bgcolor = "white",
        hovermode = 'closest'
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

    return fig, msg, color 


def graphing_3d_colorspace(selected_id,df, manufacturer, thickness, colorspace : int):

    fig = go.Figure()
    if manufacturer == ALL_MANUFACTURERS:

        msg = f'{len(df.index)} glasses'
        color = 'darkgrey'
        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df["RColor"] if colorspace == GRAPHTYPE_RGB else df["lColor"],
                y=df["GColor"] if colorspace == GRAPHTYPE_RGB else df["aColor"],
                z=df['BColor'] if colorspace == GRAPHTYPE_RGB else df["bColor"],
                customdata=df,
                marker=dict(
                    color=df['CssColor'],
                    size=3,
                ),

                showlegend=False,
                hovertemplate = 
                    '<b>id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[17]}' + 
                    '<br>%{customdata[18]}'
            )
        )
        
    else:
        mask_na = (df['Manufacturer'] != manufacturer)
        mask = (df['Manufacturer'] == manufacturer)

        if len(df[mask].index)==0:
            msg = f'No glasses from {manufacturer} with thickness, {thickness}mm'
            color = 'red'
        else:
            msg = f'{len(df[mask].index)} glasses'
            color = 'darkgrey'

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[mask_na]["RColor"] if colorspace == GRAPHTYPE_RGB else df[mask_na]["lColor"],
                y=df[mask_na]["GColor"] if colorspace == GRAPHTYPE_RGB else df[mask_na]["aColor"],
                z=df[mask_na]['BColor'] if colorspace == GRAPHTYPE_RGB else df[mask_na]["bColor"],
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
                x=df[mask]["RColor"] if colorspace == GRAPHTYPE_RGB else df[mask]["lColor"],
                y=df[mask]["GColor"] if colorspace == GRAPHTYPE_RGB else df[mask]["aColor"],
                z=df[mask]['BColor'] if colorspace == GRAPHTYPE_RGB else df[mask]["bColor"],
                customdata=df[mask],
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
                    '<br>%{customdata[17]}' + 
                    '<br>%{customdata[18]}'
            )
        )

    if selected_id:
        mask = (df['ID'] == id)

        fig.add_trace(
            go.Scatter3d(
                mode='markers',
                x=df[mask]["RColor"] if colorspace == GRAPHTYPE_RGB else df[mask]["lColor"],
                y=df[mask]["GColor"] if colorspace == GRAPHTYPE_RGB else df[mask]["aColor"],
                z=df[mask]['BColor'] if colorspace == GRAPHTYPE_RGB else df[mask]["bColor"],
                customdata=df[mask],
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=SelectedPointProps.SIZE_3D,
                    line=dict(
                        color=SelectedPointProps.COLOR_OUTLINE,
                        width=SelectedPointProps.THICKNESS_OUTLINE
                    )
                ),
                showlegend=False
            )

        )

    return fig, msg, color  