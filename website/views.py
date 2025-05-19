from flask import Blueprint, render_template, jsonify, request, current_app, redirect, url_for
from flask_login import login_required, current_user
from .models import UserInteraction
from . import db
from sqlalchemy import func, case, extract, desc
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

views = Blueprint('views', __name__)

# Home/Dashboard route
@views.route('/')
@views.route('/dashboard-overview')
@views.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

# Sales Performance Metrics
@views.route('/chart_data/top_products')
@login_required
def top_products():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        UserInteraction.product_name,
        func.sum(UserInteraction.revenue_generated).label('total_revenue')
    ).group_by(UserInteraction.product_name)\
     .order_by(desc('total_revenue'))

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] for row in data]
    values = [float(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/scheduled_demos')
@login_required
def scheduled_demos():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        UserInteraction.product_name,
        func.sum(case((UserInteraction.demo_requested == True, 1), else_=0)).label('demo_count')
    ).group_by(UserInteraction.product_name)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] for row in data]
    values = [int(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/kpi/total_revenue')
@login_required
def total_revenue():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        func.sum(UserInteraction.revenue_generated).label('total_revenue')
    )

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    total = query.scalar() or 0.0
    return jsonify({'total_revenue': float(total)})

# Dashboard Overview
@views.route('/dashboard-overview-data')
@login_required
def dashboard_overview():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        func.sum(UserInteraction.num_jobs_placed).label('total_jobs'),
        func.sum(case((UserInteraction.demo_requested == True, 1), else_=0)).label('demo_requests'),
        func.sum(case((UserInteraction.ai_assistant_used == True, 1), else_=0)).label('ai_assistant_uses')
    )

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    result = query.first()

    return jsonify({
        'total_jobs': int(result.total_jobs or 0),
        'demo_requests': int(result.demo_requests or 0),
        'ai_assistant_uses': int(result.ai_assistant_uses or 0)
    })

# Statistical Analysis
@views.route('/chart_data/monthly_revenue')
@login_required
def monthly_revenue():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        func.strftime('%Y-%m', UserInteraction.timestamp).label('month'),
        func.sum(UserInteraction.revenue_generated).label('total_revenue')
    ).group_by('month').order_by('month')

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] for row in data]
    values = [float(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/peak_hours')
@login_required
def peak_hours():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        extract('hour', UserInteraction.timestamp).label('hour'),
        func.count(UserInteraction.id).label('request_count')
    ).group_by('hour').order_by('hour')

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [f"{int(row[0]):02d}:00" for row in data]
    values = [int(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/country_distribution')
@login_required
def country_distribution():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    job_type = request.args.get('job_type')

    query = db.session.query(
        UserInteraction.country,
        func.count(UserInteraction.id).label('request_count')
    ).group_by(UserInteraction.country)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    data = query.all()

    labels = [row[0] for row in data]
    values = [int(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/kpi/statistical_summary')
@login_required
def statistical_summary():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    try:
        query = db.session.query(
            UserInteraction.duration_on_site,
            UserInteraction.revenue_generated,
            UserInteraction.pages_visited,
            UserInteraction.conversion
        )

        if start_date and end_date:
            query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
        if country:
            query = query.filter(UserInteraction.country == country)
        if job_type:
            query = query.filter(UserInteraction.job_type == job_type)

        df = pd.read_sql(query.statement, db.engine)

        if df.empty:
            summary = {
                'mean_duration_on_site': 0.0,
                'std_duration_on_site': 0.0,
                'mean_revenue_per_conversion': 0.0,
                'mean_pages_visited': 0.0
            }
        else:
            summary = {
                'mean_duration_on_site': float(df['duration_on_site'].mean() or 0.0),
                'std_duration_on_site': float(df['duration_on_site'].std() or 0.0),
                'mean_revenue_per_conversion': float(df[df['conversion'] == True]['revenue_generated'].mean() or 0.0),
                'mean_pages_visited': float(df['pages_visited'].mean() or 0.0)
            }

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error in statistical_summary: {str(e)}")
        return jsonify({'error': 'Failed to compute statistics'}), 500

# Demo and Promotional Event Tracker
@views.route('/chart_data/demo_promo_requests')
@login_required
def demo_promo_requests():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        func.strftime('%Y-%m', UserInteraction.timestamp).label('month'),
        func.sum(case((UserInteraction.demo_requested == True, 1), else_=0)).label('demos'),
        func.sum(case((UserInteraction.promo_event_interested == True, 1), else_=0)).label('promos')
    ).group_by('month').order_by('month')

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] for row in data]
    demos = [int(row[1]) for row in data]
    promos = [int(row[2]) for row in data]

    return jsonify({'labels': labels, 'demos': demos, 'promos': promos})

@views.route('/chart_data/promo_interest')
@login_required
def promo_interest():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        func.sum(case((UserInteraction.promo_event_interested == True, 1), else_=0)).label('interested'),
        func.sum(case((UserInteraction.promo_event_interested == False, 1), else_=0)).label('not_interested')
    )

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    result = query.first()

    labels = ['Interested', 'Not Interested']
    values = [int(result.interested or 0), int(result.not_interested or 0)]

    return jsonify({'labels': labels, 'values': values})

# Job Type Distribution
@views.route('/chart_data/job_type_distribution')
@login_required
def job_type_distribution():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        UserInteraction.job_type,
        func.count(UserInteraction.id).label('job_count')
    ).group_by(UserInteraction.job_type)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] if row[0] else 'Unknown' for row in data]
    values = [int(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart/job_type_bar')
@login_required
def job_type_bar():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        UserInteraction.job_type,
        func.count(UserInteraction.id).label('job_count')
    ).group_by(UserInteraction.job_type)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] if row[0] else 'Unknown' for row in data]
    values = [int(row[1]) for row in data]

    plt.style.use('ggplot')
    fig = plt.Figure(figsize=(10, 6))
    ax = fig.subplots()
    ax.bar(labels, values, color='#60a5fa', edgecolor='#1e3a8a')
    ax.set_title('Job Type Distribution', fontsize=16, pad=15, color='#1f2937')
    ax.set_xlabel('Job Type', fontsize=12, color='#1f2937')
    ax.set_ylabel('Number of Jobs', fontsize=12, color='#1f2937')
    ax.tick_params(axis='x', rotation=45, labelsize=10, colors='#4b5563')
    ax.tick_params(axis='y', labelsize=10, colors='#4b5563')
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return jsonify({'image': image_base64})

# Other Charts
@views.route('/chart_data/device_distribution')
@login_required
def device_distribution():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    query = db.session.query(
        UserInteraction.user_device,
        func.count(UserInteraction.id).label('device_count')
    ).group_by(UserInteraction.user_device)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    data = query.all()

    labels = [row[0] if row[0] else 'Unknown' for row in data]
    values = [int(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/conversion_by_product')
@login_required
def conversion_by_product():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    query = db.session.query(
        UserInteraction.product_name,
        func.avg(case((UserInteraction.conversion == True, 1.0), else_=0.0)).label('conversion_rate')
    ).group_by(UserInteraction.product_name)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    data = query.all()

    labels = [row[0] for row in data]
    values = [float(row[1]) * 100 for row in data]

    return jsonify({'labels': labels, 'values': values})


# New Sales/Marketing Charts
@views.route('/chart_data/revenue_by_demo')
@login_required
def revenue_by_demo():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    query = db.session.query(
        UserInteraction.demo_requested,
        func.sum(UserInteraction.revenue_generated).label('total_revenue')
    ).group_by(UserInteraction.demo_requested)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    data = query.all()

    labels = ['Demo Requested' if row[0] else 'No Demo' for row in data]
    values = [float(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/promo_by_product')
@login_required
def promo_by_product():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    query = db.session.query(
        UserInteraction.product_name,
        func.sum(case((UserInteraction.promo_event_interested == True, 1), else_=0)).label('promo_count')
    ).group_by(UserInteraction.product_name)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    data = query.all()

    labels = [row[0] for row in data]
    values = [int(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

# New Sales/Marketing Charts
@views.route('/chart_data/roi_by_product')
@login_required
def roi_by_product():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    query = db.session.query(
        UserInteraction.product_name,
        func.sum(UserInteraction.revenue_generated - UserInteraction.cost_incurred).label('profit'),
        func.sum(UserInteraction.cost_incurred).label('cost')
    ).group_by(UserInteraction.product_name)

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    data = query.all()

    labels = [row[0] for row in data]
    values = [float((row[1] / row[2]) * 100) if row[2] > 0 else 0.0 for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/profit_loss_over_time')
@login_required
def profit_loss_over_time():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    query = db.session.query(
        func.strftime('%Y-%m', UserInteraction.timestamp).label('month'),
        func.sum(UserInteraction.revenue_generated - UserInteraction.cost_incurred).label('profit_loss')
    ).group_by('month').order_by('month')

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)

    data = query.all()

    labels = [row[0] for row in data]
    values = [float(row[1]) for row in data]

    return jsonify({'labels': labels, 'values': values})

@views.route('/chart_data/conversion_funnel')
@login_required
def conversion_funnel():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    job_type = request.args.get('job_type')

    query = db.session.query(
        func.count(UserInteraction.id).label('total_visits'),
        func.sum(case((UserInteraction.demo_requested == True, 1), else_=0)).label('demo_requests'),
        func.sum(case((UserInteraction.conversion == True, 1), else_=0)).label('conversions')
    )

    if start_date and end_date:
        query = query.filter(UserInteraction.timestamp.between(start_date, end_date))
    if country:
        query = query.filter(UserInteraction.country == country)
    if job_type:
        query = query.filter(UserInteraction.job_type == job_type)

    result = query.first()

    labels = ['Total Visits', 'Demo Requests', 'Conversions']
    values = [
        int(result.total_visits or 0),
        int(result.demo_requests or 0),
        int(result.conversions or 0)
    ]

    return jsonify({'labels': labels, 'values': values})