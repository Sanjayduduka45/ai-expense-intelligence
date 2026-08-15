"""
Interactive AI Expense Assistant — Dedicated Right-Side Panel Component.

Styled as a modern, embedded right-hand financial copilot with suggestion pills,
compact message bubbles, and verified data grounding.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.frontend.utils.api_client import ask_ai_assistant


def render_assistant_chat(expenses_data: list[dict[str, Any]] | None) -> None:
    """
    Render the dedicated right-side AI Expense Assistant panel.
    """
    # ── Assistant Panel Container ─────────────────────────────────────────────
    st.markdown(
        """
        <div style="
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1.5px solid #E0E7FF;
            border-radius: 16px;
            padding: 16px 14px 10px 14px;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.05);
            margin-bottom: 12px;
        ">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="font-size: 1.25rem;">🤖</span>
                <span style="font-size: 1.05rem; font-weight: 700; color: #1E1B4B;">AI Expense Assistant</span>
                <span style="background-color: #ECFDF5; color: #059669; font-size: 0.68rem; font-weight: 600; padding: 2px 6px; border-radius: 9999px; margin-left: auto;">
                    ● Online
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #64748B; margin-bottom: 12px; line-height: 1.3;">
                Ask questions. Get grounded answers based on your verified financial data.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not expenses_data:
        st.markdown(
            """
            <div style="background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 18px; text-align: center; color: #64748B; font-size: 0.85rem;">
                💡 <b>No dataset loaded</b><br>
                Upload your transaction CSV or click <b>Load Sample Data</b> to chat with the assistant.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Suggested Questions Pills ─────────────────────────────────────────────
    st.markdown(
        "<div style='font-size: 0.75rem; font-weight: 600; color: #6366F1; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;'>Suggested Questions:</div>",
        unsafe_allow_html=True,
    )

    suggestions = [
        "What category is eating most of my money?",
        "How much did I spend on food?",
        "Where can I realistically cut spending?",
        "Which expenses look unusual?",
        "How much could I save if I reduce discretionary spending?",
    ]

    selected_prompt = None
    for idx, prompt_text in enumerate(suggestions):
        if st.button(f"💬 {prompt_text}", key=f"sugg_panel_{idx}", use_container_width=True):
            selected_prompt = prompt_text

    st.markdown("<hr style='margin: 12px 0 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # ── Conversation History ──────────────────────────────────────────────────
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    # Chat controls
    if st.session_state["chat_messages"]:
        c_hist, c_clear = st.columns([2, 1])
        with c_hist:
            st.markdown("<span style='font-size: 0.75rem; font-weight: 600; color: #64748B;'>CONVERSATION</span>", unsafe_allow_html=True)
        with c_clear:
            if st.button("🗑️ Clear", key="clear_chat_panel_btn", use_container_width=True):
                st.session_state["chat_messages"] = []
                st.rerun()

    # Render past conversation messages
    for msg in st.session_state["chat_messages"]:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 8px;">
                    <div style="
                        background-color: #EEF2FF;
                        border: 1px solid #C7D2FE;
                        color: #3730A3;
                        border-radius: 12px 12px 2px 12px;
                        padding: 8px 12px;
                        font-size: 0.85rem;
                        max-width: 90%;
                        line-height: 1.35;
                    ">
                        {msg['content']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Clean any leftover dollar sign in assistant reply
            reply_clean = msg["content"].replace("$", "₹")
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 8px;">
                    <div style="
                        background-color: #FFFFFF;
                        border: 1px solid #E2E8F0;
                        color: #0F172A;
                        border-radius: 12px 12px 12px 2px;
                        padding: 10px 12px;
                        font-size: 0.85rem;
                        max-width: 95%;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
                        line-height: 1.4;
                    ">
                        <div style="font-size: 0.7rem; font-weight: 600; color: #6366F1; margin-bottom: 4px;">🤖 ASSISTANT</div>
                        {reply_clean}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── User Input Box ────────────────────────────────────────────────────────
    with st.form("assistant_panel_input_form", clear_on_submit=True):
        col_inp, col_snd = st.columns([4, 1])
        with col_inp:
            typed_query = st.text_input(
                "Ask a question",
                placeholder="Type your question here...",
                label_visibility="collapsed",
            )
        with col_snd:
            send_clicked = st.form_submit_button("➤", use_container_width=True)

    prompt_to_send = (typed_query if send_clicked and typed_query.strip() else None) or selected_prompt

    if prompt_to_send:
        # Add user query
        st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_send})

        # Call backend
        with st.spinner("Analyzing verified metrics..."):
            history_payload = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["chat_messages"][:-1]
            ]
            res = ask_ai_assistant(prompt_to_send, expenses_data, history=history_payload)
            if res.get("success"):
                answer = res.get("data", {}).get("answer", "No answer provided.").replace("$", "₹")
                st.session_state["chat_messages"].append({"role": "assistant", "content": answer})
            else:
                err_msg = f"⚠️ Could not generate answer: {res.get('detail', 'Unknown error')}"
                st.session_state["chat_messages"].append({"role": "assistant", "content": err_msg})
        st.rerun()

    # ── Trust / Privacy Footer ────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align: center; margin-top: 10px; font-size: 0.72rem; color: #94A3B8;">
            🛡️ <i>Answers grounded strictly in your verified financial data.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )
