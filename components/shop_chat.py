# components/shop_chat.py
import streamlit as st
from components import marketplace


def show_shop_chat(fire_db=None, mongo_db=None):
    st.header("🛍️ Marketplace + Chat")
    st.caption("Browse listings and chat with the AI assistant side-by-side.")

    left, right = st.columns([2, 1])
    with left:
        marketplace.show_marketplace(fire_db, mongo_db)
    with right:
        st.subheader("🤖 Assistant")
        st.info("Chat feature coming soon...")