"""
Run once to populate demo data:
    python seed.py

Creates:
  - admin@careerai.com / admin123        (role: admin)
  - recruiter@careerai.com / recruiter123 (role: recruiter, company: Nova Systems)
  - seeker@careerai.com / seeker123      (role: job_seeker)
  - ~10 sample job postings (including one intentionally scammy one, to
    demonstrate AI Job Safety Analysis flagging it)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app import models, security, services

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def get_or_create_user(email, name, password, role, company_name=None, verified=False):
    u = db.query(models.User).filter(models.User.email == email).first()
    if u:
        return u
    u = models.User(
        name=name, email=email, hashed_password=security.hash_password(password),
        role=role, company_name=company_name, company_verified=verified,
        profile_completion=80,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


admin = get_or_create_user("admin@careerai.com", "Ada Admin", "admin123", "admin")
recruiter = get_or_create_user("recruiter@careerai.com", "Rita Recruiter", "recruiter123",
                                "recruiter", company_name="Nova Systems", verified=True)
seeker = get_or_create_user("seeker@careerai.com", "Sam Seeker", "seeker123", "job_seeker")

print(f"Users ready: admin={admin.email}, recruiter={recruiter.email}, seeker={seeker.email}")

sample_jobs = [
    dict(title="Backend Engineer (Python)", company="Nova Systems", location="Remote",
         category="Engineering", employment_type="Full-time",
         description="Build and scale REST APIs powering our platform. Work closely with product and design.",
         requirements="3+ years experience with Python, FastAPI or Django, SQL databases, and REST API design.",
         skills_required=["python", "fastapi", "sql", "rest api", "docker"], salary_min=90000, salary_max=130000),
    dict(title="Frontend Engineer (React)", company="Nova Systems", location="Remote",
         category="Engineering", employment_type="Full-time",
         description="Own the customer-facing web app. Collaborate with design on a delightful UI.",
         requirements="2+ years with React, TypeScript, and modern CSS. Experience with REST/GraphQL APIs.",
         skills_required=["react", "javascript", "typescript", "css", "graphql"], salary_min=85000, salary_max=120000),
    dict(title="Data Analyst", company="Bluepeak Analytics", location="New York, NY",
         category="Data", employment_type="Full-time",
         description="Turn raw data into insight for our marketing and product teams using SQL and Python.",
         requirements="Experience with SQL, Excel, data visualization tools (Tableau/Power BI), and statistics.",
         skills_required=["sql", "excel", "tableau", "data analysis", "python"], salary_min=70000, salary_max=95000),
    dict(title="Machine Learning Engineer", company="Vertex AI Labs", location="San Francisco, CA",
         category="Engineering", employment_type="Full-time",
         description="Design and deploy ML models for our recommendation platform at scale.",
         requirements="Strong Python, experience with PyTorch/TensorFlow, and MLOps practices.",
         skills_required=["python", "pytorch", "tensorflow", "machine learning", "aws"], salary_min=120000, salary_max=170000),
    dict(title="Product Manager", company="Bluepeak Analytics", location="Remote",
         category="Product", employment_type="Full-time",
         description="Own the roadmap for our analytics product line and work with engineering and design daily.",
         requirements="3+ years PM experience, strong communication, and comfort with data-driven prioritization.",
         skills_required=["product management", "agile", "communication", "data analysis"], salary_min=95000, salary_max=140000),
    dict(title="DevOps Engineer", company="Nova Systems", location="Austin, TX",
         category="Engineering", employment_type="Full-time",
         description="Own our CI/CD pipelines and cloud infrastructure on AWS.",
         requirements="Experience with AWS, Docker, Kubernetes, Terraform, and CI/CD tooling.",
         skills_required=["aws", "docker", "kubernetes", "terraform", "ci/cd"], salary_min=100000, salary_max=145000),
    dict(title="Customer Success Associate", company="Harbor Retail Co.", location="Chicago, IL",
         category="Customer Support", employment_type="Full-time",
         description="Be the first point of contact for our customers, resolving issues and building relationships.",
         requirements="Strong communication skills and prior customer service experience preferred.",
         skills_required=["communication", "customer service"], salary_min=42000, salary_max=55000),
    dict(title="Junior Software Engineer", company="Vertex AI Labs", location="Remote",
         category="Engineering", employment_type="Full-time",
         description="Great entry-level role for a new grad who loves building things end to end.",
         requirements="CS degree or bootcamp grad. Familiarity with Python or JavaScript and Git.",
         skills_required=["python", "javascript", "git"], salary_min=65000, salary_max=85000),
    dict(title="Marketing Specialist (SEO/Content)", company="Harbor Retail Co.", location="Remote",
         category="Marketing", employment_type="Contract",
         description="Drive organic growth through SEO strategy and high-quality content.",
         requirements="Experience with SEO tools, content writing, and campaign analytics.",
         skills_required=["seo", "content writing", "marketing"], salary_min=50000, salary_max=70000),
    # Intentionally scammy listing to demonstrate AI Job Safety Analysis
    dict(title="Work From Home - Earn $$$ Fast!!!", company="", location="Remote",
         category="Other", employment_type="Full-time",
         description="No experience needed earn unlimited earning potential! Urgent hiring no interview required. "
                      "Contact us on WhatsApp only. A small registration fee is required to start — send money via "
                      "gift card or wire transfer to begin your training.",
         requirements="Must be willing to pay a processing fee upfront.",
         skills_required=[], salary_min=1000, salary_max=50000),
]

created = 0
for j in sample_jobs:
    exists = db.query(models.Job).filter(models.Job.title == j["title"], models.Job.company == j["company"]).first()
    if exists:
        continue
    job_text = f"{j['title']} {j['description']} {j['requirements']}"
    safety = services.analyze_job_safety(job_text, j.get("salary_min"), j.get("salary_max"), j["company"])
    quality = services.analyze_job_quality(j["description"], j["requirements"], j["skills_required"])
    job = models.Job(
        recruiter_id=recruiter.id, status="under_review" if safety["is_flagged_scam"] else "active",
        is_flagged_scam=safety["is_flagged_scam"], scam_reasons=safety["scam_reasons"],
        quality_score=quality, **j,
    )
    db.add(job)
    created += 1

db.commit()
print(f"Created {created} sample jobs (existing ones skipped).")
db.close()
print("Seed complete. Log in with seeker@careerai.com / seeker123, recruiter@careerai.com / recruiter123, or admin@careerai.com / admin123.")
