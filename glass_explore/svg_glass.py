import dash
from dash import html
from dash_svg import Svg, G, Rect,Line


VIEW_HEIGHT = 20

def generate_buildup(buildup):

    x=0
    children = []
    for i,gl in enumerate(buildup['layers']):
        t = gl['thickness']

        lite= Rect(width = t, height = VIEW_HEIGHT, x=x, fill=gl['color'])
        children.append(lite)

        if gl['coating'] and gl['coating'] != 'NONE':

            if gl['coating'] == 'BOTH':
                children.append(Line(x1 = x,y1=0,x2=x,y2=VIEW_HEIGHT, stroke= 'red', strokeWidth=0.5 ,strokeDasharray='1,1'))
                children.append(Line(x1 = x+t,y1=0,x2=x+t,y2=VIEW_HEIGHT, stroke= 'red', strokeWidth=0.5 ,strokeDasharray='1,1'))
            else:
                ff = gl['flipped'] + (gl['coating'] == 'FRONT')
                if ff == 1:
                    xl = x
                else:
                    xl = x+t
                children.append(Line(x1 = xl,y1=0,x2=xl,y2=VIEW_HEIGHT, stroke= 'red', strokeWidth=0.5 ,strokeDasharray='1,1'))


        if i < len(buildup['gas_layers']):
            x= t + buildup['gas_layers'][i]['thickness']
        
    total_t = t+x

    svg = Svg(
           children
        ,
        viewBox=f"0 0 {total_t} {VIEW_HEIGHT}", width = '100%', height = '100')

    return html.Div(svg)


if __name__ == "__main__":


    buildup ={
        'layers': [
            {
                'thickness' : 6,
                'color' : '#1320ff',
                'flipped' : True,
                'coating' : 'BACK'
            },
            {
                'thickness' : 6,
                'color' : '#666666',
                'flipped' : False,
                'coating' : 'NONE'
            }
        
        ],
        'gas_layers' : [{
            'thickness' : 4,
            'gas' : 'air'
        }]
    }


    app = dash.Dash(__name__)
    app.layout = generate_buildup(buildup)
    app.run_server(debug=True, use_reloader=True)  



