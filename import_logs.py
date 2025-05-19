import random
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from website import create_app, db
from website.models import UserInteraction

fake = Faker()
app = create_app()

PRODUCTS = ['ModelForge', 'Smart Logistics Suite', 'FinPredictor', 'DocuAI']
DEVICES = ['Desktop', 'Mobile', 'Tablet']
BROWSERS = ['Chrome', 'Firefox', 'Safari', 'Edge']
JOB_TYPES = ['Prototyping', 'Issue Resolution', 'Design Automation', 'Document Analysis']

def generate_random_timestamp(start_year=2023):
    now = datetime.now()
    start_date = datetime(start_year, 1, 1)
    return fake.date_time_between(start_date=start_date, end_date=now)

def generate_user_interaction():
    duration = round(random.uniform(0.5, 10.0), 2)  # time spent on site (mins)
    pages = random.randint(1, int(duration * 2))
    conversion = random.random() < (duration / 15)  # more time = higher chance
    revenue = round(random.uniform(20, 500), 2) if conversion else 0.0
    num_jobs = random.randint(0, 5) if conversion else random.randint(0, 2)  # More jobs if converted
    job_type = random.choice(JOB_TYPES) if num_jobs > 0 else None

    # Calculate cost_incurred
    base_cost = round(random.uniform(5, 20), 2)
    demo_cost = round(random.uniform(50, 100), 2) if random.random() < 0.3 else 0
    promo_cost = round(random.uniform(20, 50), 2) if random.random() < 0.2 else 0
    ai_cost = round(random.uniform(10, 30), 2) if random.random() < 0.4 else 0
    if conversion and revenue > 0:
        revenue_based_cost = round(revenue * random.uniform(0.5, 0.8), 2)
        cost_incurred = max(revenue_based_cost, base_cost + demo_cost + promo_cost + ai_cost)
    else:
        cost_incurred = base_cost + demo_cost + promo_cost + ai_cost

    return UserInteraction(
        timestamp=generate_random_timestamp(),
        ip_address=fake.ipv4_public(),
        country=fake.country(),
        user_id=fake.uuid4(),
        product_name=random.choice(PRODUCTS),
        demo_requested=random.random() < 0.3,
        promo_event_interested=random.random() < 0.2,
        ai_assistant_used=random.random() < 0.4,
        duration_on_site=duration,
        pages_visited=pages,
        conversion=conversion,
        revenue_generated=revenue,
        user_device=random.choice(DEVICES),
        browser=random.choice(BROWSERS),
        cost_incurred=cost_incurred,
        num_jobs_placed=num_jobs,
        job_type=job_type
    )

def seed_data(n=10000, csv_file='web_server_logs.csv'):
    with app.app_context():
        db.create_all()
        interactions = []
        for _ in range(n):
            interaction = generate_user_interaction()
            db.session.add(interaction)
            interactions.append({
                'date': interaction.timestamp.strftime('%Y-%m-%d'),
                'time': interaction.timestamp.strftime('%H:%M:%S'),
                'c-ip': interaction.ip_address,
                'cs-uri-stem': f'/products/{interaction.product_name.lower().replace(" ", "_")}' if interaction.product_name else '/',
                'cs-method': 'GET' if random.random() < 0.8 else 'POST',
                'sc-status': '200' if random.random() < 0.95 else '404',
                'cs-user-agent': f'{interaction.browser}/{random.randint(1, 120)}',
                'country': interaction.country,
                'user_id': interaction.user_id,
                'product_name': interaction.product_name,
                'demo_requested': str(interaction.demo_requested),
                'promo_event_interested': str(interaction.promo_event_interested),
                'ai_assistant_used': str(interaction.ai_assistant_used),
                'duration_on_site': interaction.duration_on_site,
                'pages_visited': interaction.pages_visited,
                'conversion': str(interaction.conversion),
                'revenue_generated': interaction.revenue_generated,
                'user_device': interaction.user_device,
                'browser': interaction.browser,
                'cost_incurred': interaction.cost_incurred,
                'num_jobs_placed': interaction.num_jobs_placed,
                'job_type': interaction.job_type or ''
            })
        db.session.commit()

        # Save to CSV
        df = pd.DataFrame(interactions)
        df.to_csv(csv_file, index=False)
        print(f"Seeded {n} user interactions and saved to {csv_file}.")

if __name__ == "__main__":
    seed_data(500000)