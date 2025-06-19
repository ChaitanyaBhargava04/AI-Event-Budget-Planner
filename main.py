import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

def render():
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    st.title("🎯 AI Event Budget Planner")
    st.markdown("Get a personalized budget plan based on your event 🎉")

    mode = st.radio("Choose Mode", ["Manual Prompt", "Step-wise"])

    lang_map = {
        "English": "English",
        "Hindi": "Hindi",
        "Marathi": "Marathi",
        "Gujarati": "Gujarati",
        "Tamil": "Tamil",
        "Telugu": "Telugu",
        "Kannada": "Kannada",
        "Bengali": "Bengali",
        "Punjabi": "Punjabi",
        "Malayalam": "Malayalam"
    }

    if mode == "Step-wise":
        if "step_chat_history" not in st.session_state:
            st.session_state.step_chat_history = []
            st.session_state.step_context = ""

        with st.form("budget_form"):
            event_type = st.selectbox("Event Type", ["Wedding", "Birthday", "Corporate", "Festival"])
            guest_count = st.number_input("Number of Guests", min_value=10, value=100)
            location = st.text_input("Location (City)")
            budget = st.number_input("Total Budget (₹)", min_value=10000, value=10000)
            preference = st.selectbox("Planning Style", ["economical", "balanced", "premium"])
            language = st.selectbox("Language", list(lang_map.keys()))
            submit = st.form_submit_button("Generate Plan")

        lang_name = lang_map.get(language, "English")  # Defined outside form submission

        if submit:
            priority_msg = ""
            if budget < 50000:
                priority_msg = "Focus on cost-saving essentials. Avoid luxury items unless necessary."
            elif budget < 200000:
                priority_msg = "Maintain balance between quality and cost. Optimize across major categories."
            else:
                priority_msg = "Emphasize premium experiences with top-tier vendors and personalization."

            event_focus = {
                "Wedding": "Give more attention to decoration, catering, and venue ambiance.",
                "Birthday": "Focus on entertainment, cake, and decoration suited to age group.",
                "Corporate": "Prioritize venue quality, audio/visual setup, and branding.",
                "Festival": "Emphasize theme-based decoration, lighting, and cultural elements."
            }.get(event_type, "")

            step1_prompt = f"""
You are an experienced Indian event planner. Strictly respond in {lang_name}. Analyze the user's budget priorities and needs.

Inputs:
- Event Type: {event_type}
- Guests: {guest_count}
- Location: {location}
- Budget: ₹{budget}
- Preference: {preference}

Guidelines:
{priority_msg}
{event_focus}

Summarize key goals and planning strategy.
"""

            with st.spinner("Analyzing priorities..."):
                model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                analysis = model.generate_content(step1_prompt).text.strip()

            step2_prompt = f"""
You are an expert Indian event planner. Generate a complete event budget plan with categories like venue, catering, decoration, etc. Only respond in {lang_name} without mixing English. Include smart tips.

Details:
- Type: {event_type}
- Guests: {guest_count}
- Location: {location}
- Budget: ₹{budget}
- Preference: {preference}
- Planning Context: {analysis}
"""

            with st.spinner("Generating your personalized event plan..."):
                response = model.generate_content(step2_prompt)
                final_plan = response.text.strip()

                st.session_state.step_context = final_plan
                st.session_state.step_chat_history = [("ai", final_plan)]

                st.subheader("📝 Personalized Budget Plan")
                st.markdown(
                    f"<div style='border:2px solid #ccc;padding:15px;border-radius:10px;background:#fefefe;'>{final_plan}</div>",
                    unsafe_allow_html=True
                )
                st.download_button("📄 Download Plan", data=final_plan, file_name="event_budget_plan.txt", mime="text/plain")

        # Follow-up chat (excluding plan repetition)
        if st.session_state.step_chat_history:
            st.subheader("💬 Ask follow-up questions")

            for role, msg in st.session_state.step_chat_history[1:]:  # Skip first (the plan)
                if role == "user":
                    st.markdown(f"<div style='background:#e1f5fe;padding:10px;border-radius:8px;margin:5px 0;'>🧑‍💬 <b>You</b>: {msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#f1f8e9;padding:10px;border-radius:8px;margin:5px 0;'>🤖 <b>Planner</b>: {msg}</div>", unsafe_allow_html=True)

            user_input = st.text_area("Your question", height=100, key="stepwise_chat_input")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Send", key="send_stepwise_chat"):
                    if user_input.strip():
                        st.session_state.step_chat_history.append(("user", user_input.strip()))
                        chat_prompt = f"{st.session_state.step_context}\n\n" + "\n".join(
                            [f"{'User' if r == 'user' else 'Planner'}: {m}" for r, m in st.session_state.step_chat_history]
                        )

                        try:
                            with st.spinner("Planner is replying..."):
                                model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                                reply = model.generate_content(f"You are an event planner. Always reply in {lang_name}.\n\n{chat_prompt}")
                                answer = reply.text.strip()
                                st.session_state.step_chat_history.append(("ai", answer))
                                st.rerun()
                        except Exception as e:
                            st.error(str(e))

            with col2:
                if st.button("Reset Chat", key="reset_stepwise_chat"):
                    st.session_state.step_chat_history = []
                    st.session_state.step_context = ""
                    st.rerun()

    else:
        language = st.selectbox("Language", list(lang_map.keys()), key="manual_lang_chat")
        lang_name = lang_map.get(language, "English")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        st.subheader("💬 Chat with the Event Planner")

        for role, msg in st.session_state.chat_history:
            if role == "user":
                st.markdown(f"<div style='background:#e3f2fd;padding:10px;border-radius:8px;margin:5px 0;'>🧑‍💬 <b>You</b>: {msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background:#fff8e1;padding:10px;border-radius:8px;margin:5px 0;'>🤖 <b>Planner</b>: {msg}</div>", unsafe_allow_html=True)

        user_input = st.text_area("Type your message", height=100, key="chat_input")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Send", key="send_manual_chat"):
                if user_input.strip():
                    st.session_state.chat_history.append(("user", user_input.strip()))

                    chat_prompt = "\n".join(
                        [f"{'User' if role == 'user' else 'Planner'}: {msg}" for role, msg in st.session_state.chat_history]
                    )

                    try:
                        with st.spinner("Planner is replying..."):
                            model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                            response = model.generate_content(f"You are an Indian event planner. Always reply in {lang_name}.\n\n{chat_prompt}")
                            ai_reply = response.text.strip()
                            st.session_state.chat_history.append(("ai", ai_reply))
                            st.rerun()
                    except Exception as e:
                        st.error(str(e))

        with col2:
            if st.button("Reset Chat", key="reset_manual_chat"):
                st.session_state.chat_history = []
                st.rerun()
if __name__ == "__main__":
    render()
