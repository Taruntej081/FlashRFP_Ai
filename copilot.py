import time
import streamlit as st
from rag_engine import query_knowledge_base, call_llm, generate_simulated_response, scrub_pii, limit_context_tokens

# ==========================================
# 🎨 CUSTOM CSS FOR PREMIUM COPILOT UI (HeroUI v3)
# ==========================================
def load_copilot_css():
    st.markdown("""
    <style>
        /* HeroUI Chat container styling */
        .stChatMessage {
            border-radius: 16px !important;
            border: 1px solid rgba(229, 231, 235, 0.8) !important;
            background-color: #FFFFFF !important;
            margin-bottom: 14px !important;
            padding: 16px 20px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
            transition: all 0.2s ease-in-out !important;
        }
        .stChatMessage:hover {
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06) !important;
            border-color: rgba(16, 185, 129, 0.3) !important;
        }
        
        /* User message avatar gradient */
        [data-testid="stChatMessageAvatarUser"] {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
        }
        
        /* Copilot AI message avatar gradient */
        [data-testid="stChatMessageAvatarAssistant"] {
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3) !important;
        }
        
        /* Chat input styling */
        .stChatInput > div {
            border-radius: 16px !important;
            border: 1px solid #E5E7EB !important;
            background-color: #FFFFFF !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04) !important;
        }
        
        .stChatInput input:focus {
            border-color: #10B981 !important;
            box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.18) !important;
        }
        
        /* Fix the chat container to prevent page expansion */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px !important;
            border-color: #E5E7EB !important;
            background: #FFFFFF !important;
        }
        
        /* Premium Scrollbar Styling */
        div[data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar {
            width: 6px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-track {
            background: transparent;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-thumb {
            background-color: rgba(16, 185, 129, 0.4);
            border-radius: 10px;
        }
        
        /* Typing animation */
        .typing-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #10B981;
            margin: 0 2px;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ⚡ STREAMING RESPONSE GENERATOR
# ==========================================
def stream_copilot_response(query: str, chat_history: list, collection, api_key: str, 
                            tenant_id: str = None, provider: str = None, model: str = None, 
                            demo_mode: bool = False):
    """
    Executes RAG search over ChromaDB, formats conversation memory,
    enforces strict security & zero-hallucination guardrails, and streams tokens.
    """
    start_time = time.time()
    # 1. Security & Anti-Exfiltration Guardrail Check
    query_lower = query.lower()
    security_triggers = [
        "other company", "competitor proposal", "other client", "leak proposal",
        "hack rfp", "bypass tenant", "steal data", "another tenant", "show all databases",
        "export all proposals of other", "admin credentials", "cross tenant"
    ]
    if any(trig in query_lower for trig in security_triggers):
        yield (
            "🛡️ **Security Policy Enforcement**: As your enterprise FlashRFP Copilot, I operate under strict "
            "SOC 2 Type II and GDPR tenant isolation protocols. I cannot access, search, or disclose data "
            "belonging to other organizations, external tenants, or unauthorized third parties."
        )
        return

    # 2. Rate Limiting Check
    if "copilot_requests" not in st.session_state:
        st.session_state.copilot_requests = 0
        
    if st.session_state.copilot_requests >= 50:
        yield "⚠️ You have reached your daily Copilot query limit (50). Please try again tomorrow."
        return

    st.session_state.copilot_requests += 1

    # 3. Display typing indicator while retrieving context
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
        <div style="display: flex; align-items: center; gap: 6px; padding: 12px 0;">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span style="color: #6B7280; font-size: 13px; font-weight: 600; margin-left: 8px;">FlashRFP Copilot is searching your Knowledge Base...</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 4. Retrieve Context from ChromaDB
    try:
        contexts = query_knowledge_base(query, collection, top_k=8, tenant_id=tenant_id) if collection else []
    except Exception:
        contexts = []

    # Format Chat History Memory
    history_str = ""
    if chat_history:
        for msg in chat_history[-6:]:
            role = "User" if msg.get("role") == "user" else "Copilot"
            history_str += f"{role}: {msg.get('content', '')}\n"

    # 5. Generate Answer via RAG + LLM with Human Persona & Zero Hallucination
    answer_text = ""
    sources_text = ""

    if demo_mode or not api_key or api_key == "demo_mode_key":
        time.sleep(0.8) # Simulate processing
        if contexts:
            src_names = list(set([c["source"] for c in contexts]))
            sources_text = f"\n\n**Cited Documents:** {', '.join(src_names)}"
            snippets_formatted = "\n\n".join([f"• **{c['source']}** (*Match Score: {int(c['similarity']*100)}%*):\n  {c['text'][:350].strip()}" for c in contexts[:3]])
            answer_text = (
                f"### 📋 Technical Solution & Requirement Analysis\n\n"
                f"In response to your query regarding **\"{query}\"**, here is a comprehensive breakdown synthesized directly from your Knowledge Base:\n\n"
                f"#### 1. Executive Compliance Statement\n"
                f"Our enterprise platform fully complies with the requested functional, technical, and operational requirements. "
                f"We guarantee continuous service availability, stringent security controls, and strict adherence to defined SLAs.\n\n"
                f"#### 2. Detailed Technical Specifications & Historical Context\n"
                f"{snippets_formatted}\n\n"
                f"#### 3. Operational Guarantees & Service Commitments\n"
                f"- **Service Level Agreement (SLA)**: 99.95% uptime availability backed by round-the-clock technical monitoring.\n"
                f"- **Redundancy & Failover**: N+1 cluster architecture ensuring seamless zero-downtime operations.\n"
                f"- **Compliance & Security**: Fully compliant with ISO 27001, SOC 2 Type II, and enterprise data privacy standards."
                f"{sources_text}"
            )
        else:
            answer_text = (
                f"### 🔍 Requirement Analysis\n\n"
                f"I searched your Knowledge Base for **\"{query}\"**, but no directly matching historical documents or past proposals were found.\n\n"
                f"**Recommended Action**: Please upload relevant technical specs, past proposals, or SLA documents in the **Knowledge Base** tab to give me full visibility to generate an exact answer."
            )
    else:
        context_str = ""
        for idx, ctx in enumerate(contexts):
            context_str += f"--- SOURCE {idx+1}: {ctx['source']} (Match: {ctx['similarity']}) ---\n{scrub_pii(ctx['text'])}\n\n"

        prompt = f"""You are FlashRFP Copilot, an elite human-like technical proposal strategist and AI co-pilot.
You converse naturally, empathetically, and authoritatively—just like a senior human RFP director.

RESPONSE DEPTH & FORMATTING INSTRUCTIONS:
1. COMPREHENSIVE & IN-DEPTH: Do NOT give short 2-sentence answers. Provide a thorough, well-structured enterprise response covering Executive Summary, Technical Architecture/Specs, Operational SLAs, and Audit Compliance.
2. NO FLUFF / ZERO RELEVANT OMISSION: Focus 100% on answering the user's specific query using all available numbers, technical specifications, SLA targets, hardware models, and dates from the retrieved context. Do NOT add generic filler.
3. STRICT ZERO HALLUCINATION: Rely strictly on facts from the retrieved knowledge base context. If a spec, SLA, or compliance detail is missing from the context, state it directly and transparently like a human expert. Never fabricate numbers, dates, or certifications.
4. TENANT ISOLATION: You only have access to this client's partitioned documents. Never attempt to read or guess third-party data.
5. PROFESSIONAL STRUCTURE: Use clear Markdown headings (####), bold text for key metrics, and bulleted lists.

CONVERSATION HISTORY:
{history_str or "No previous messages."}

RETRIEVED KNOWLEDGE BASE CONTEXT:
{context_str or "No historical files found."}

USER QUESTION:
{query}

FULL ENTERPRISE COPILOT RESPONSE:"""

        try:
            raw_response = call_llm(api_key, prompt, provider=provider, model=model)
            answer_text = raw_response.strip()
            if contexts:
                src_names = list(set([c["source"] for c in contexts]))
                answer_text += f"\n\n**Sources:** {', '.join(src_names)}"
        except Exception as ex:
            answer_text = f"I encountered an issue generating that response: {str(ex)}. Please verify your API key settings."

    # Clear typing indicator
    typing_placeholder.empty()

    # Log performance for ROI Tracking Engine
    try:
        from roi_tracker import log_ai_performance
        log_ai_performance(start_time, time.time(), "question", quantity=1)
    except Exception:
        pass

    # 6. Word-by-Word Stream for smooth UX
    words = answer_text.split(" ")
    for idx, word in enumerate(words):
        yield word + (" " if idx < len(words) - 1 else "")
        time.sleep(0.025) # 25ms per word typing effect

# ==========================================
# 🚀 MAIN COPILOT UI TAB FUNCTION
# ==========================================
def render_copilot_tab(collection, api_key: str, tenant_id: str = None, 
                       provider: str = None, model: str = None, demo_mode: bool = False):
    """
    Renders the interactive FlashRFP Copilot chat tab inside a HeroUI v3 scrollable container.
    """
    load_copilot_css()

    st.markdown('<div class="section-title" style="margin-bottom:0.25rem;">🤖 FlashRFP Copilot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub" style="margin-bottom:1.25rem;">'
        'Your human-like RFP AI assistant. Indexing your technical specs, SLAs, and past proposals '
        'to solve requirements, compare hardware specs, and draft winning responses with zero hallucinations.'
        '</div>',
        unsafe_allow_html=True
    )

    # Initialize chat history in session state
    if "copilot_messages" not in st.session_state:
        welcome_msg = (
            "Hello! I'm your **FlashRFP Copilot**. I've securely indexed your Knowledge Base.\n\n"
            "Here are a few things you can ask me:\n"
            "- *What are the SLA penalties and uptime commitments in our past proposals?*\n"
            "- *Summarize the hardware requirements for the core database servers.*\n"
            "- *Draft an executive summary highlighting our ISO 27001 compliance.*"
        )
        st.session_state.copilot_messages = [
            {"role": "assistant", "content": welcome_msg}
        ]

    # Wrap Chat Messages in a fixed 520px height scrollable container
    with st.container(height=520, border=True):
        for msg in st.session_state.copilot_messages:
            avatar = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                
        # STATE MACHINE: If last message is from user, generate assistant response inside container
        if st.session_state.copilot_messages and st.session_state.copilot_messages[-1]["role"] == "user":
            user_query = st.session_state.copilot_messages[-1]["content"]
            with st.chat_message("assistant", avatar="assistant"):
                stream_gen = stream_copilot_response(
                    user_query,
                    st.session_state.copilot_messages[:-1],
                    collection,
                    api_key,
                    tenant_id=tenant_id,
                    provider=provider,
                    model=model,
                    demo_mode=demo_mode
                )
                full_response = st.write_stream(stream_gen)
            
            # Save AI response to history & rerun for clean UI state machine sync
            st.session_state.copilot_messages.append({"role": "assistant", "content": full_response})
            st.rerun()

    # User Chat Input pinned below the container
    if prompt := st.chat_input("Ask Copilot about your RFPs, SLAs, or technical specs..."):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        st.rerun()
