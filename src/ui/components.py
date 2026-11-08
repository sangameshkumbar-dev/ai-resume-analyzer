"""
Reusable visual UI components, gauges, and Plotly charts for the Streamlit dashboard.
"""
import plotly.graph_objects as go
from typing import Dict, Any


def render_match_gauge(score: float, title: str = "Overall Match Score") -> go.Figure:
    """Create a sleek gauge indicator for match scores."""
    # Determine color based on score
    if score >= 80:
        bar_color = "#10B981"  # Emerald Green
    elif score >= 60:
        bar_color = "#3B82F6"  # Royal Blue
    elif score >= 45:
        bar_color = "#F59E0B"  # Amber
    else:
        bar_color = "#EF4444"  # Red

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': '#1E293B'}},
        number={'suffix': "%", 'font': {'size': 36, 'color': '#0F172A', 'weight': 'bold'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
            'bar': {'color': bar_color, 'thickness': 0.3},
            'bgcolor': "#F1F5F9",
            'borderwidth': 1,
            'bordercolor': "#CBD5E1",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.1)'},
                {'range': [50, 75], 'color': 'rgba(245, 158, 11, 0.1)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
            ],
            'threshold': {
                'line': {'color': "#0F172A", 'width': 3},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def render_radar_breakdown(
    skills_score: float,
    semantic_score: float,
    experience_score: float,
    education_score: float
) -> go.Figure:
    """Create a multi-dimensional radar chart comparing score pillars."""
    categories = ['Technical Skills', 'Semantic Fit', 'Experience Length', 'Education Level']
    values = [skills_score, semantic_score, experience_score, education_score]
    # Close radar polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.25)',
        line=dict(color='#2563EB', width=2),
        name='Candidate Alignment'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color='#64748B')
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#1E293B', weight='bold')
            )
        ),
        showlegend=False,
        height=290,
        margin=dict(l=40, r=40, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def render_score_bar_breakdown(breakdown: Dict[str, float]) -> go.Figure:
    """Horizontal bar chart showing points contributed by each factor."""
    labels = ["Hard Skills", "Semantic Similarity", "Experience Alignment", "Education Level"]
    values = [
        breakdown.get("skills", 0),
        breakdown.get("semantic", 0),
        breakdown.get("experience", 0),
        breakdown.get("education", 0)
    ]
    max_pts = [40, 30, 20, 10]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation='h',
        name='Points Earned',
        marker=dict(color='#3B82F6'),
        text=[f"{v} pts" for v in values],
        textposition='inside'
    ))
    fig.add_trace(go.Bar(
        y=labels,
        x=[m - v for m, v in zip(max_pts, values)],
        orientation='h',
        name='Unearned Points',
        marker=dict(color='#E2E8F0'),
        hoverinfo='none'
    ))

    fig.update_layout(
        barmode='stack',
        height=220,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 45], showgrid=True, gridcolor='#F1F5F9', title="Points (Max Total = 100)"),
        yaxis=dict(autorange="reversed"),
        showlegend=False
    )
    return fig

