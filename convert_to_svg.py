import base64
import struct

def png_to_svg(png_path, svg_path):
    with open(png_path, 'rb') as f:
        data = f.read()
    
    # Get dimensions from PNG header (IHDR chunk starts at byte 12, width/height at 16)
    w, h = struct.unpack('>LL', data[16:24])
    
    b64 = base64.b64encode(data).decode('utf-8')
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <image href="data:image/png;base64,{b64}" width="{w}" height="{h}"/>
</svg>'''

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
        
if __name__ == "__main__":
    png_to_svg(r"D:\Conti Rate Calculator\Image (1).png", r"D:\Conti Rate Calculator\client\src\assets\aaw1.svg")
    print("Successfully converted PNG to SVG!")
