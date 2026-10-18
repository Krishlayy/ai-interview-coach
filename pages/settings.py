"""
Settings Page — stub (Phase 5 placeholder).
"""
import streamlit as st
import os


def render():
    st.markdown(
        """
        <div style="margin-bottom:1.75rem;">
          <div style="font-size:0.68rem;font-weight:700;color:#60A5FA;
                      text-transform:uppercase;letter-spacing:0.18em;margin-bottom:0.6rem;">
            Configuration
          </div>
          <div style="font-size:clamp(1.5rem,2.5vw,2.1rem);font-weight:900;
                      letter-spacing:-0.04em;
                      background:linear-gradient(135deg,#F8FAFC 0%,#94A3B8 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text;margin-bottom:0.4rem;">
            Settings
          </div>
          <div style="font-size:0.9rem;color:#64748B;line-height:1.6;">
            Manage your API keys, preferences, and account settings.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── API Key section ───────────────────────────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
        'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:1rem;">'
        'API Configuration</div>',
        unsafe_allow_html=True,
    )

    api_key = os.getenv("GROQ_API_KEY", "")
    masked  = ("gsk_" + "•" * 20 + api_key[-4:]) if len(api_key) > 8 else "Not configured"
    key_color = "#22C55E" if api_key else "#EF4444"
    key_label = "Configured" if api_key else "Missing"

    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:0.85rem 1rem;background:rgba(255,255,255,0.02);
                    border:1px solid rgba(255,255,255,0.06);border-radius:12px;
                    margin-bottom:0.6rem;">
          <div>
            <div style="font-size:0.82rem;font-weight:600;color:#CBD5E1;">GROQ_API_KEY</div>
            <div style="font-size:0.75rem;color:#475569;margin-top:0.2rem;
                        font-family:'JetBrains Mono',monospace;">{masked}</div>
          </div>
          <span style="background:{key_color}18;color:{key_color};border:1px solid {key_color}35;
                       border-radius:100px;padding:0.25rem 0.85rem;
                       font-size:0.72rem;font-weight:700;">{key_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.8rem;color:#475569;line-height:1.6;">'
        'To update your API key, edit the <code style="background:rgba(255,255,255,0.06);'
        'padding:0.1rem 0.4rem;border-radius:4px;font-size:0.78rem;">.env</code> file '
        'in the project root and restart the application. '
        'Get a free key at '
        '<a href="https://console.groq.com" target="_blank" '
        'style="color:#60A5FA;text-decoration:none;">console.groq.com</a>.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Model info section ────────────────────────────────────────────────────
    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background:rgba(13,27,46,0.8);border:1px solid rgba(255,255,255,0.06);
                    border-radius:16px;padding:1.25rem 1.5rem;">
          <div style="font-size:0.72rem;font-weight:700;color:#64748B;
                      text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.9rem;">
            Model Configuration
          </div>
          <div style="display:flex;flex-direction:column;gap:0.6rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
              <span style="font-size:0.82rem;color:#64748B;">AI Model</span>
              <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">Llama 3.3 · 70B</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
              <span style="font-size:0.82rem;color:#64748B;">Provider</span>
              <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">Groq Cloud</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
              <span style="font-size:0.82rem;color:#64748B;">Context Window</span>
              <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">128k tokens</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0;">
              <span style="font-size:0.82rem;color:#64748B;">Database</span>
              <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">SQLite · Local</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
