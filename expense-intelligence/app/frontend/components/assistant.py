"""
Interactive AI Expense Assistant chat component.

Enables natural language Q&A grounded strictly in the verified expense data.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.frontend.utils.api_client import ask_ai_assistant


def render_assistant_chat(expenses_data: list[dict[str, Any]] | None) -> None:
    """
    Render interactive AI Assistant chat for querying analyzed expenses.
    """
    st.subheader("💬 Ask AI Expense Assistant")
    st.caption(
        "Ask specific questions about your spending patterns, categories, or savings strategies. "
        "Answers are grounded strictly in your verified financial metrics."
    )

    if not expenses_data:
        st.info("💡 **No expense dataset loaded.** Please upload a CSV file above to enable the AI assistant.")
        return

    # Pre-defined suggestion prompt buttons
    suggestions = [
        "What category is eating most of my money?",
        "How much did I spend on food?",
        "Where can I realistically cut spending?",
        "Which expenses look unusual?",
        "How much could I save if I reduce discretionary spending?",
    ]

    st.markdown("**Quick questions:**")
    # Display in 2 responsive rows
    row1 = suggestions[:3]
    row2 = suggestions[3:]

    selected_prompt = None

    cols1 = st.columns(len(row1))
    for idx, prompt_text in enumerate(row1):
        with cols1[idx]:
            if st.button(prompt_text, key=f"sugg_r1_{idx}", use_container_width=True):
                selected_prompt = prompt_text

    cols2 = st.columns(len(row2))
    for idx, prompt_text in enumerate(row2):
        with cols2[idx]:
            if st.button(prompt_text, key=f"sugg_r2_{idx}", use_container_width=True):
                selected_prompt = prompt_text

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    # Chat history control bar
    if st.session_state["chat_messages"]:
        col_space, col_clear = st.columns([5, 1])
        with col_clear:
            if st.button("🗑️ Clear Chat", key="clear_chat_btn", use_container_width=True):
                st.session_state["chat_messages"] = []
                st.rerun()

    # Display past conversation
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle user input via chat_input or suggestion button
    user_query = st.chat_input("Ask a question about your expenses...")
    prompt_to_send = user_query or selected_prompt

    if prompt_to_send:
        # Display user message
        st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        # Query backend
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data and generating answer..."):
                history_payload = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state["chat_messages"][:-1]
                ]
                res = ask_ai_assistant(prompt_to_send, expenses_data, history=history_payload)
                if res.get("success"):
                    answer = res.get("data", {}).get("answer", "No answer provided.")
                    st.markdown(answer)
                    st.session_state["chat_messages"].append({"role": "assistant", "content": answer})
                else:
                    err_msg = f"⚠️ Could not generate answer: {res.get('detail', 'Unknown error')}"
                    st.error(err_msg)
                    st.session_state["chat_messages"].append({"role": "assistant", "content": err_msg})
