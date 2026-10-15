THEMES={
 "light":{"bg":"#F4F6FA","fg":"#172033","panel":"#FFFFFF","accent":"#174EA6","on_accent":"#FFFFFF","muted":"#45536B"},
 "dark":{"bg":"#131B28","fg":"#F1F5FC","panel":"#202C3D","accent":"#9CC3FF","on_accent":"#101B2E","muted":"#C0CBDC"}
}
def luminance(color):
    vals=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]
    return sum(a*b for a,b in zip(vals,(.2126,.7152,.0722)))
def contrast(a,b):
    x,y=sorted([luminance(a),luminance(b)])
    return (y+.05)/(x+.05)
