import io
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path

st.set_page_config(page_title="मराठी पोस्टर डिझायनर", page_icon="🌿", layout="wide")
st.title("🌿 मराठी पोस्टर डिझायनर")
st.caption("मजकूर स्वतंत्रपणे रेंडर होतो, त्यामुळे मराठी शब्द आणि फोन नंबर तुम्ही स्वतः तपासून बदलू शकता.")

W, H = 1800, 2700
GREEN = (0, 83, 28)
DARK_GREEN = (0, 59, 20)
LEAF = (130, 190, 35)
CREAM = (255, 249, 222)
YELLOW = (255, 208, 0)
BROWN = (104, 35, 15)
WHITE = (255, 255, 255)

def find_font(bold=False):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
        "NotoSansDevanagari-Bold.ttf" if bold else "NotoSansDevanagari-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None

def font(size, bold=False):
    path = find_font(bold)
    if path:
        try:
            return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
        except Exception:
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def fit_font(draw, text, max_width, start_size, bold=False):
    size = start_size
    while size > 18:
        f = font(size, bold)
        box = draw.textbbox((0, 0), text, font=f, direction="ltr", language="mr")
        if box[2] - box[0] <= max_width:
            return f
        size -= 3
    return font(size, bold)

def centered(draw, text, y, max_width, size, fill, bold=False, outline_width=0, outline_fill=None):
    f = fit_font(draw, text, max_width, size, bold)
    box = draw.textbbox((0, 0), text, font=f, language="mr", direction="ltr", stroke_width=outline_width)
    x = (W - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=f, fill=fill, language="mr", direction="ltr",
              stroke_width=outline_width, stroke_fill=outline_fill)
    return y + (box[3] - box[1])

def crop_cover(img, size):
    return ImageOps.fit(img.convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

def draw_rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def make_poster(data, uploads, logo):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)

    # Outer frame and subtle header field
    d.rectangle((0, 0, W, H), fill=CREAM)
    d.rectangle((0, 0, W, 34), fill=LEAF)
    d.rectangle((0, 34, W, 54), fill=GREEN)
    d.rectangle((0, H-38, W, H), fill=LEAF)

    # Header logo area
    if logo:
        try:
            lg = Image.open(logo).convert("RGBA")
            lg.thumbnail((250, 220), Image.Resampling.LANCZOS)
            im.paste(lg, ((W-lg.width)//2, 72), lg if lg.mode == "RGBA" else None)
        except Exception:
            pass
    else:
        d.ellipse((760, 75, 1040, 285), fill=(255,255,255), outline=GREEN, width=12)
        centered(d, "🌱", 112, 240, 100, GREEN, True)

    centered(d, data["brand"], 305, 1600, 112, GREEN, True)
    centered(d, data["tagline"], 430, 1600, 57, BROWN, True)

    # Organic badge
    draw_rounded(d, (1270, 100, 1660, 235), 42, LEAF)
    centered(d, data["badge"], 128, 355, 45, WHITE, True)

    # Product section header
    draw_rounded(d, (300, 530, 1500, 640), 38, YELLOW)
    centered(d, data["products_heading"], 548, 1150, 60, BROWN, True)

    # Product cards
    names = data["product_names"]
    top, bottom = 690, 1515
    margin, gap = 34, 22
    card_w = (W - 2*margin - 4*gap) // 5
    for i, name in enumerate(names):
        x = margin + i*(card_w+gap)
        draw_rounded(d, (x, top, x+card_w, bottom), 24, (255,255,248), outline=(210,190,130), width=4)
        draw_rounded(d, (x+8, top+8, x+card_w-8, top+110), 18, GREEN if i%2 else BROWN)
        f = fit_font(d, name, card_w-28, 43, True)
        bbox = d.textbbox((0,0), name, font=f, language="mr")
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        d.text((x+(card_w-tw)//2, top+35), name, font=f, fill=WHITE, language="mr", direction="ltr")
        product = uploads[i]
        img_top, img_bottom = top+130, bottom-24
        if product is not None:
            try:
                pimg = Image.open(product)
                pimg = crop_cover(pimg, (card_w-24, img_bottom-img_top))
                im.paste(pimg, (x+12, img_top))
            except Exception:
                d.text((x+20, img_top+180), "उत्पादनाचा फोटो", font=font(26, True), fill=GREEN)
        else:
            # Clean placeholder that makes missing photos obvious during editing
            d.ellipse((x+card_w//2-70, img_top+150, x+card_w//2+70, img_top+290), fill=(238,220,160), outline=(190,150,65), width=4)
            d.text((x+25, img_top+330), "येथे फोटो अपलोड करा", font=fit_font(d, "येथे फोटो अपलोड करा", card_w-40, 24, True), fill=GREEN)

    # Trust strip
    trust_y = 1575
    trust_items = [data["trust_1"], data["trust_2"], data["trust_3"]]
    section_w = W // 3
    for i, item in enumerate(trust_items):
        cx = section_w*i + section_w//2
        d.ellipse((cx-55, trust_y, cx+55, trust_y+110), fill=GREEN)
        centered_text = item
        f = fit_font(d, centered_text, section_w-50, 48, True)
        bbox = d.textbbox((0,0), centered_text, font=f, language="mr")
        d.text((cx-(bbox[2]-bbox[0])//2, trust_y+125), centered_text, font=f, fill=GREEN, language="mr", direction="ltr")
        if i:
            d.line((section_w*i, trust_y-5, section_w*i, trust_y+210), fill=LEAF, width=5)

    # Contact block
    contact_top = 1835
    d.rectangle((0, contact_top, W, H-40), fill=DARK_GREEN)
    d.rectangle((0, contact_top, W, contact_top+12), fill=YELLOW)
    draw_rounded(d, (620, contact_top+35, 1180, contact_top+130), 32, YELLOW)
    centered(d, data["contact_heading"], contact_top+48, 520, 58, BROWN, True)

    contact_lines = [
        "पत्ता: " + data["address"],
        "ईमेल: " + data["email"],
    ]
    y = contact_top+180
    for line in contact_lines:
        f = fit_font(d, line, 1640, 43, True)
        d.text((85, y), line, font=f, fill=WHITE, language="mr", direction="ltr")
        y += 82

    d.line((900, contact_top+390, 900, H-120), fill=YELLOW, width=6)
    left_name = data["contact_1_name"]
    left_phone = data["contact_1_phone"]
    right_name = data["contact_2_name"]
    right_phone = data["contact_2_phone"]
    centered_at(d, left_name, 2260, 850, 54, WHITE, True)
    centered_at(d, left_phone, 2335, 850, 63, WHITE, True)
    centered_at(d, right_name, 2260, 850, 54, WHITE, True, offset_x=900)
    centered_at(d, right_phone, 2335, 850, 63, WHITE, True, offset_x=900)
    centered(d, data["footer"], 2505, 1600, 35, (215,245,155), True)
    return im

def centered_at(draw, text, y, region_w, size, fill, bold=False, offset_x=0):
    f = fit_font(draw, text, region_w-50, size, bold)
    box = draw.textbbox((0,0), text, font=f, language="mr")
    x = offset_x + (region_w-(box[2]-box[0]))//2
    draw.text((x, y), text, font=f, fill=fill, language="mr", direction="ltr")

with st.sidebar:
    st.header("१. पोस्टरचा मजकूर")
    brand = st.text_input("व्यवसायाचे नाव", "वर्धमान अॅग्रो")
    tagline = st.text_input("टॅगलाइन", "नैसर्गिक गोडवा, विश्वासाची गुणवत्ता!")
    badge = st.text_input("बॅजवरील मजकूर", "१००% नैसर्गिक")
    products_heading = st.text_input("उत्पादन विभागाचे शीर्षक", "आमची प्रमुख उत्पादने")
    product_names = []
    default_names = ["गूळ", "गूळ पावडर", "गूळ क्यूब", "मसाला क्यूब", "काकवी"]
    st.header("२. उत्पादनांची नावे")
    for i, default in enumerate(default_names):
        product_names.append(st.text_input(f"उत्पादन {i+1}", default))
    st.header("३. संपर्क माहिती")
    address = st.text_input("पत्ता", "Hupri-Kolhapur Road, Near HP Petrol Pump, Sangavde")
    email = st.text_input("ईमेल", "vardhamnagro76@gmail.com")
    contact_1_name = st.text_input("संपर्क व्यक्ती १", "रोहन पाटील")
    contact_1_phone = st.text_input("फोन नंबर १", "76200 54200")
    contact_2_name = st.text_input("संपर्क व्यक्ती २", "शीतल हेरलेगे")
    contact_2_phone = st.text_input("फोन नंबर २", "9637671144")
    trust_1 = st.text_input("विश्वास चिन्ह १", "शुद्धता")
    trust_2 = st.text_input("विश्वास चिन्ह २", "गुणवत्ता")
    trust_3 = st.text_input("विश्वास चिन्ह ३", "विश्वास")
    contact_heading = st.text_input("संपर्क विभागाचे शीर्षक", "संपर्क")
    footer = st.text_input("खालची ओळ", "नैसर्गिक गोडवा • शुद्धता • विश्वास")

st.subheader("४. लोगो आणि उत्पादनांचे फोटो")
logo_file = st.file_uploader("लोगो अपलोड करा (पर्यायी)", type=["png", "jpg", "jpeg"])
uploads = []
cols = st.columns(5)
for i, col in enumerate(cols):
    with col:
        uploads.append(st.file_uploader(f"{product_names[i]} फोटो", type=["png", "jpg", "jpeg"], key=f"product_{i}"))

data = {
    "brand": brand, "tagline": tagline, "badge": badge,
    "products_heading": products_heading, "product_names": product_names,
    "address": address, "email": email, "contact_1_name": contact_1_name,
    "contact_1_phone": contact_1_phone, "contact_2_name": contact_2_name,
    "contact_2_phone": contact_2_phone, "trust_1": trust_1, "trust_2": trust_2,
    "trust_3": trust_3, "contact_heading": contact_heading, "footer": footer
}

if st.button("पोस्टर तयार करा", type="primary", use_container_width=True):
    with st.spinner("पोस्टर तयार होत आहे..."):
        poster = make_poster(data, uploads, logo_file)
        st.session_state["poster_bytes"] = poster
        buf = io.BytesIO()
        poster.save(buf, format="PNG", dpi=(300, 300), optimize=True)
        st.session_state["poster_png"] = buf.getvalue()

if "poster_bytes" in st.session_state:
    st.subheader("पोस्टरचे प्रिव्ह्यू")
    st.image(st.session_state["poster_bytes"], use_container_width=True)
    st.download_button("PNG पोस्टर डाउनलोड करा", data=st.session_state["poster_png"],
                       file_name="vardhaman_agro_poster.png", mime="image/png",
                       use_container_width=True)
    st.info("रस्त्यावर प्रिंट करण्यापूर्वी प्रिंटिंग प्रेसकडून अपेक्षित आकार, DPI आणि bleed तपासून घ्या.")
else:
    st.info("डावीकडील मजकूर तपासा, लोगो आणि पाच उत्पादनांचे फोटो अपलोड करा, मग “पोस्टर तयार करा” दाबा.")
