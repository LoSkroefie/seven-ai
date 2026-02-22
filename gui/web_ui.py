"""
Seven AI — Gradio Web UI
A browser-based interface that runs alongside Seven's existing Tkinter GUI.
Does NOT replace or interfere with voice/GUI — this is an additional window into Seven's mind.

Features:
- Text chat with Seven (typed input → Seven's brain → response)
- Live emotional state display
- Knowledge graph visualization (interactive Plotly)
- Session memory browser
- System status dashboard
"""

import gradio as gr
import plotly.graph_objects as go
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class SevenWebUI:
    """Gradio web interface for Seven AI — runs alongside the main bot."""

    def __init__(self, bot_instance=None, port: int = 7860):
        self.bot = bot_instance
        self.port = port
        self.chat_history = []  # [(user_msg, bot_msg), ...]
        self._lock = threading.Lock()

    # ── Chat ──────────────────────────────────────────────────────────

    def chat(self, user_message: str, history: list) -> tuple:
        """Send a message to Seven and get a response."""
        if not user_message or not user_message.strip():
            return history, ""

        if not self.bot:
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": "[Seven is not connected]"})
            return history, ""

        try:
            response = self.bot._process_input(user_message.strip())
            if not response:
                response = "..."

            # Record in bot's memory systems the same way voice does
            if hasattr(self.bot, 'memory') and self.bot.memory:
                try:
                    self.bot.memory.add_to_conversation(user_message.strip(), response)
                except Exception:
                    pass

            # Push to Tkinter GUI if present
            if self.bot.gui:
                try:
                    self.bot.gui.add_message('conversation', speaker='You (Web)', text=user_message.strip())
                    self.bot.gui.add_message('conversation', speaker=self.bot.bot_name, text=response,
                                             emotion=self.bot.current_emotion.value if self.bot.current_emotion else 'calmness')
                except Exception:
                    pass

            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": f"[Error: {e}]"})

        return history, ""

    # ── Emotional State ───────────────────────────────────────────────

    def get_emotional_state(self) -> str:
        """Return Seven's current emotional state as formatted text."""
        if not self.bot:
            return "Seven is not connected."

        lines = []
        # Current emotion
        emotion = getattr(self.bot, 'current_emotion', None)
        lines.append(f"**Current Emotion:** {emotion.value if emotion else 'Unknown'}")

        # Emotion journal insights
        ej = getattr(self.bot, 'emotion_journal', None)
        if ej and hasattr(ej, 'get_emotional_insights'):
            try:
                insights = ej.get_emotional_insights()
                lines.append(f"**Most Common:** {insights.get('most_common_emotion', '?')}")
                lines.append(f"**Emotional Volatility:** {insights.get('emotional_volatility', 0):.2f}")
                lines.append(f"**Unique Emotions Experienced:** {insights.get('unique_emotions_experienced', 0)}")
            except Exception:
                pass

        # Persistent emotions (v2.6)
        pe = getattr(self.bot, 'persistent_emotions', None)
        if pe and hasattr(pe, 'get_emotional_state'):
            try:
                state = pe.get_emotional_state()
                if state:
                    lines.append(f"\n**Persistent State:** {state}")
            except Exception:
                pass

        # Relationship info
        rel = getattr(self.bot, 'relationship', None)
        if rel and hasattr(rel, 'get_relationship_summary'):
            try:
                summary = rel.get_relationship_summary()
                depth = summary.get('depth', 'unknown') if isinstance(summary, dict) else str(summary)
                lines.append(f"\n**Relationship Depth:** {depth}")
            except Exception:
                pass

        # Metrics
        metrics = getattr(self.bot, 'metrics', None)
        if metrics:
            lines.append(f"\n**Session Messages:** {getattr(metrics, 'session_messages', 0)}")
            lines.append(f"**Total Messages:** {getattr(metrics, 'total_messages', 0)}")
            last_ms = getattr(metrics, 'last_response_ms', 0)
            if last_ms:
                lines.append(f"**Last Response:** {last_ms}ms")

        return "\n".join(lines) if lines else "No emotional data available."

    # ── Knowledge Graph ───────────────────────────────────────────────

    def get_knowledge_graph(self) -> go.Figure:
        """Generate an interactive Plotly visualization of Seven's knowledge graph."""
        kg = getattr(self.bot, 'knowledge_graph', None) if self.bot else None

        fig = go.Figure()

        if not kg or not hasattr(kg, 'graph') or kg.graph.number_of_nodes() == 0:
            fig.add_annotation(
                text="No knowledge graph data yet — Seven learns as you talk.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16, color="#888")
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1a1a2e",
                plot_bgcolor="#1a1a2e",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                height=500,
            )
            return fig

        import networkx as nx

        # Layout
        try:
            pos = nx.spring_layout(kg.graph, k=2, iterations=50, seed=42)
        except Exception:
            pos = nx.circular_layout(kg.graph)

        # Edges
        edge_x, edge_y = [], []
        edge_labels_x, edge_labels_y, edge_labels_text = [], [], []
        for u, v, data in kg.graph.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            # Edge label at midpoint
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            edge_labels_x.append(mx)
            edge_labels_y.append(my)
            rel = data.get('relation', '?').replace('_', ' ')
            conf = data.get('confidence', 0)
            edge_labels_text.append(f"{rel} ({conf:.1f})")

        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y, mode='lines',
            line=dict(width=1.5, color='rgba(150,150,200,0.4)'),
            hoverinfo='none', showlegend=False
        ))

        # Edge labels
        fig.add_trace(go.Scatter(
            x=edge_labels_x, y=edge_labels_y, mode='text',
            text=edge_labels_text,
            textfont=dict(size=9, color='rgba(180,180,220,0.7)'),
            hoverinfo='none', showlegend=False
        ))

        # Nodes
        node_x, node_y, node_text, node_hover, node_size, node_color = [], [], [], [], [], []
        node_data = getattr(kg, 'node_data', {})

        for node in kg.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)

            nd = node_data.get(node, {})
            mentions = nd.get('mention_count', 0)
            ntype = nd.get('type', 'concept')
            first_seen = nd.get('first_seen', '?')
            degree = kg.graph.degree(node)

            node_hover.append(
                f"<b>{node}</b><br>"
                f"Type: {ntype}<br>"
                f"Mentions: {mentions}<br>"
                f"Connections: {degree}<br>"
                f"First seen: {first_seen[:10] if len(first_seen) > 10 else first_seen}"
            )
            node_size.append(max(15, min(50, 15 + mentions * 3 + degree * 5)))

            # Color by type
            type_colors = {
                'person': '#ff6b6b',
                'programming_language': '#4ecdc4',
                'skill': '#45b7d1',
                'project': '#f7dc6f',
                'concept': '#a29bfe',
            }
            node_color.append(type_colors.get(ntype, '#a29bfe'))

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode='markers+text',
            marker=dict(size=node_size, color=node_color, line=dict(width=2, color='#fff')),
            text=node_text, textposition="top center",
            textfont=dict(size=11, color='#e0e0e0'),
            hovertext=node_hover, hoverinfo='text',
            showlegend=False
        ))

        stats = kg.get_stats()
        fig.update_layout(
            title=dict(
                text=f"Seven's Knowledge Graph — {stats['total_nodes']} nodes, {stats['total_edges']} connections",
                font=dict(size=14, color='#ccc')
            ),
            template="plotly_dark",
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#16213e",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=550,
            margin=dict(l=20, r=20, t=50, b=20),
            hoverlabel=dict(bgcolor="#2d2d30", font_size=12),
        )

        return fig

    # ── Session Memory ────────────────────────────────────────────────

    def get_session_memory(self) -> str:
        """Return recent session memory entries."""
        if not self.bot:
            return "Seven is not connected."

        lines = []

        # From memory manager
        mem = getattr(self.bot, 'memory', None)
        if mem and hasattr(mem, 'get_recent_context'):
            try:
                recent = mem.get_recent_context(limit=20)
                if recent:
                    lines.append("### Recent Conversation Memory\n")
                    lines.append(recent if isinstance(recent, str) else str(recent))
            except Exception as e:
                lines.append(f"Memory access error: {e}")

        # From emotional memory
        em_path = config.DATA_DIR / "emotional_memory.json"
        if em_path.exists():
            try:
                data = json.loads(em_path.read_text())
                moods = data.get('mood_history', [])
                if moods:
                    lines.append("\n### Recent Mood History\n")
                    for m in moods[-10:]:
                        ts = m.get('timestamp', '?')
                        emo = m.get('emotion', '?')
                        lines.append(f"- `{ts[:19]}` → **{emo}**")
            except Exception:
                pass

        # User profile
        profile = None
        um = getattr(self.bot, 'user_model', None)
        if um and hasattr(um, 'profile'):
            profile = um.profile
        if profile:
            lines.append("\n### User Profile\n")
            name = profile.get('basic_info', {}).get('name') or 'Unknown'
            style = profile.get('personality', {}).get('communication_style', 'unknown')
            lines.append(f"- **Name:** {name}")
            lines.append(f"- **Style:** {style}")
            topics = profile.get('interests', {}).get('topics', [])
            if topics:
                lines.append(f"- **Topics:** {', '.join(topics[:10])}")

        return "\n".join(lines) if lines else "No session data yet."

    # ── System Status ─────────────────────────────────────────────────

    def get_system_status(self) -> str:
        """Return Seven's current system status."""
        if not self.bot:
            return "Seven is not connected."

        lines = ["### Seven AI — System Status\n"]

        # Core info
        lines.append(f"**Name:** {getattr(self.bot, 'bot_name', '?')}")
        lines.append(f"**Running:** {getattr(self.bot, 'running', False)}")
        lines.append(f"**Emotion:** {self.bot.current_emotion.value if self.bot.current_emotion else '?'}")

        # Module status
        modules = [
            ('Phase 5 Sentience', 'phase5'),
            ('V2 Systems', 'v2_system'),
            ('Personality', 'personality'),
            ('Memory', 'memory'),
            ('Knowledge Graph', 'knowledge_graph'),
            ('Vector Memory', 'vector_memory'),
            ('Voice Engine', 'voice_engine'),
            ('Vision', 'vision'),
            ('Music Player', 'music_player'),
            ('SSH Manager', 'ssh_manager'),
            ('System Monitor', 'system_monitor'),
            ('IRC Client', 'irc_client'),
            ('Autonomous Life', 'autonomous_life'),
            ('Autonomous Agent', 'autonomous_agent'),
            ('Emotional Complexity', 'emotional_complexity'),
            ('Metacognition', 'metacognition'),
            ('Vulnerability', 'vulnerability'),
            ('Persistent Emotions', 'persistent_emotions'),
            ('Surprise System', 'surprise_system'),
            ('Temporal Continuity', 'temporal_continuity'),
            ('Context Cascade', 'context_cascade'),
            ('Self Reflection', 'self_reflection'),
            ('Dream System', 'dream_system'),
            ('True Autonomy', 'true_autonomy'),
        ]

        lines.append("\n### Active Modules\n")
        active = 0
        for label, attr in modules:
            obj = getattr(self.bot, attr, None)
            if obj:
                active += 1
                avail = ""
                if hasattr(obj, 'available') and not obj.available:
                    avail = " (unavailable)"
                lines.append(f"- ✅ **{label}**{avail}")
            else:
                lines.append(f"- ⬜ {label}")

        lines.append(f"\n**Active:** {active}/{len(modules)}")

        # Knowledge graph stats
        kg = getattr(self.bot, 'knowledge_graph', None)
        if kg:
            stats = kg.get_stats()
            lines.append(f"\n### Knowledge Graph")
            lines.append(f"- Nodes: {stats['total_nodes']}")
            lines.append(f"- Edges: {stats['total_edges']}")
            lines.append(f"- Learned: {stats['learned_facts']}")
            lines.append(f"- Inferred: {stats['inferred_facts']}")

        return "\n".join(lines)

    # ── Build & Launch ────────────────────────────────────────────────

    def build(self) -> gr.Blocks:
        """Build the Gradio interface."""
        self._css = """
        .gradio-container { max-width: 1200px !important; }
        footer { display: none !important; }
        """
        self._theme = gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="cyan",
            neutral_hue="slate",
        )

        with gr.Blocks(title="Seven AI — Web Interface") as demo:

            gr.Markdown("# 🧠 Seven AI — Web Interface")
            gr.Markdown("*Browser window into Seven's mind. Voice and Tkinter GUI continue running independently.*")

            with gr.Tabs():

                # ── Tab 1: Chat ───────────────────────────────────────
                with gr.Tab("💬 Chat", id="chat"):
                    chatbot = gr.Chatbot(
                        label="Conversation with Seven",
                        height=480,
                        buttons=["copy"],
                    )
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Type a message to Seven...",
                            show_label=False,
                            scale=9,
                            container=False,
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)

                    # Wire chat
                    send_btn.click(
                        fn=self.chat,
                        inputs=[msg_input, chatbot],
                        outputs=[chatbot, msg_input],
                    )
                    msg_input.submit(
                        fn=self.chat,
                        inputs=[msg_input, chatbot],
                        outputs=[chatbot, msg_input],
                    )

                # ── Tab 2: Knowledge Graph ────────────────────────────
                with gr.Tab("🕸️ Knowledge Graph", id="kg"):
                    gr.Markdown("Seven's learned knowledge — nodes are concepts, edges are relationships.")
                    kg_plot = gr.Plot(label="Knowledge Graph")
                    kg_refresh = gr.Button("🔄 Refresh Graph")
                    kg_refresh.click(fn=self.get_knowledge_graph, outputs=[kg_plot])

                # ── Tab 3: Emotional State ────────────────────────────
                with gr.Tab("💜 Emotional State", id="emotions"):
                    emo_display = gr.Markdown(label="Emotional State")
                    emo_refresh = gr.Button("🔄 Refresh")
                    emo_refresh.click(fn=self.get_emotional_state, outputs=[emo_display])

                # ── Tab 4: Memory ─────────────────────────────────────
                with gr.Tab("🧠 Memory", id="memory"):
                    mem_display = gr.Markdown(label="Session Memory")
                    mem_refresh = gr.Button("🔄 Refresh")
                    mem_refresh.click(fn=self.get_session_memory, outputs=[mem_display])

                # ── Tab 5: System Status ──────────────────────────────
                with gr.Tab("⚙️ System", id="system"):
                    sys_display = gr.Markdown(label="System Status")
                    sys_refresh = gr.Button("🔄 Refresh")
                    sys_refresh.click(fn=self.get_system_status, outputs=[sys_display])

            # Auto-load on open
            demo.load(fn=self.get_emotional_state, outputs=[emo_display])
            demo.load(fn=self.get_knowledge_graph, outputs=[kg_plot])
            demo.load(fn=self.get_system_status, outputs=[sys_display])
            demo.load(fn=self.get_session_memory, outputs=[mem_display])

        return demo

    def launch(self, share: bool = False):
        """Launch the web UI in a background thread."""
        demo = self.build()
        demo.queue()
        demo.launch(
            server_name="0.0.0.0",
            server_port=self.port,
            share=share,
            prevent_thread_lock=True,
            show_error=True,
            quiet=True,
            theme=self._theme,
            css=self._css,
        )
        return demo


def launch_web_ui(bot_instance=None, port: int = 7860, share: bool = False):
    """Convenience function to create and launch the web UI."""
    web = SevenWebUI(bot_instance=bot_instance, port=port)
    demo = web.launch(share=share)
    return web, demo
