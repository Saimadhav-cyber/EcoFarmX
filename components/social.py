# components/social.py
import urllib.parse
import streamlit as st


def _make_message(product: str, qty: str, price: str, link: str) -> str:
    return (
        f"EcoFarmX Update:\n"
        f"Product: {product}\nQuantity: {qty}\nPrice: {price}\n"
        f"See details: {link}"
    )


def show_social_share():
    st.header("📣 Social Media Integration")
    st.caption("Create share-ready messages for WhatsApp, Facebook, and Instagram.")

    product = st.text_input("Item/Story Title", "Organic Tomatoes from EcoFarmX")
    qty = st.text_input("Quantity", "100kg")
    price = st.text_input("Price", "₹40/kg")
    link = st.text_input("Optional Link (product/story)", "https://example.com/your-listing")

    msg = _make_message(product, qty, price, link)
    st.text_area("Message Preview", msg, height=120)

    encoded = urllib.parse.quote(msg)
    wa = f"https://api.whatsapp.com/send?text={encoded}"
    fb = f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(link)}&quote={encoded}"
    ig_note = "Instagram does not support direct URL sharing; copy the message and post manually."

    st.markdown("### Quick Share Links")
    st.markdown(f"- WhatsApp: [Open](<{wa}>)")
    st.markdown(f"- Facebook: [Open](<{fb}>)")
    st.markdown(f"- Instagram: {ig_note}")

    st.info("Tip: On mobile, the WhatsApp link opens the app with your prepared message.")