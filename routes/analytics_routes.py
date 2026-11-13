from flask import Blueprint, render_template, jsonify
from routes.auth_routes import login_required
import analytics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    kpis = analytics.compute_overall_kpis()
    corr_data = analytics.compute_correlation_and_regression()
    quadrants = analytics.get_quadrant_analysis()
    insights = analytics.generate_academic_insights()
    dept_comp = analytics.get_department_comparison()

    return render_template(
        'analytics.html',
        kpis=kpis,
        corr=corr_data,
        quadrants=quadrants,
        insights=insights,
        dept_comp=dept_comp
    )

@analytics_bp.route('/api/analytics/scatter')
@login_required
def scatter_api():
    corr_data = analytics.compute_correlation_and_regression()
    return jsonify(corr_data)

