"""
Seed the database with realistic demo incidents.
Run: python -m scripts.seed
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.opsmesh.core.config import settings
from src.opsmesh.models.incident import Incident, IncidentSeverity, IncidentStatus

# Realistic incident templates
TEMPLATES = [
    {
        "title": "High CPU usage on {service}",
        "description": "CPU utilization exceeded 95% threshold for more than 10 minutes. Auto-scaling attempted but failed due to resource limits.",
        "source": "datadog",
        "severity": IncidentSeverity.HIGH,
    },
    {
        "title": "Database connection pool exhausted on {service}",
        "description": "All available database connections are in use. New requests are queuing. Connection leak suspected in recent deployment.",
        "source": "prometheus",
        "severity": IncidentSeverity.CRITICAL,
    },
    {
        "title": "Elevated 5xx error rate on {service}",
        "description": "5xx error rate increased from 0.1% to 3.4% in the last 5 minutes. Correlates with increased traffic from marketing campaign.",
        "source": "cloudwatch",
        "severity": IncidentSeverity.HIGH,
    },
    {
        "title": "SSL certificate expiring soon for {service}",
        "description": "SSL certificate expires in 7 days. Auto-renewal via Let's Encrypt failed. Manual intervention required.",
        "source": "certbot",
        "severity": IncidentSeverity.MEDIUM,
    },
    {
        "title": "Memory leak detected in {service}",
        "description": "Heap memory growing linearly at ~50MB/hour. No releases in the last 48 hours. Likely introduced in commit abc123.",
        "source": "grafana",
        "severity": IncidentSeverity.HIGH,
    },
    {
        "title": "Disk space warning on {service} host",
        "description": "Disk usage at 87%. Log rotation may not be configured correctly. Projected to hit 95% within 48 hours.",
        "source": "nagios",
        "severity": IncidentSeverity.MEDIUM,
    },
    {
        "title": "API latency spike on {service}",
        "description": "P99 latency increased from 200ms to 1.8s. Downstream dependency payment-gateway responding slowly.",
        "source": "datadog",
        "severity": IncidentSeverity.HIGH,
    },
    {
        "title": "Failed deployment rollback on {service}",
        "description": "Deployment v2.3.1 failed health checks. Automatic rollback to v2.3.0 also failed. Service running on stale containers.",
        "source": "argocd",
        "severity": IncidentSeverity.CRITICAL,
    },
    {
        "title": "Unusual login pattern detected for {service}",
        "description": "12 failed login attempts from 3 different IPs targeting admin accounts in the last hour. Possible credential stuffing attack.",
        "source": "auth0",
        "severity": IncidentSeverity.MEDIUM,
    },
    {
        "title": "Queue depth growing on {service}",
        "description": "SQS queue depth exceeded 10,000 messages. Consumer throughput dropped 60% after latest deployment.",
        "source": "cloudwatch",
        "severity": IncidentSeverity.HIGH,
    },
    {
        "title": "DNS resolution failures for {service}",
        "description": "Intermittent DNS lookup failures causing connection timeouts to upstream services. Affecting ~5% of requests.",
        "source": "datadog",
        "severity": IncidentSeverity.MEDIUM,
    },
    {
        "title": "Cache hit rate drop on {service}",
        "description": "Redis cache hit rate dropped from 94% to 61%. Possible key eviction due to memory pressure or changed access patterns.",
        "source": "prometheus",
        "severity": IncidentSeverity.LOW,
    },
    {
        "title": "Kubernetes pod crash loop on {service}",
        "description": "Pod restarting every 30 seconds. OOMKilled — container memory limit of 512Mi insufficient for current workload.",
        "source": "kubernetes",
        "severity": IncidentSeverity.CRITICAL,
    },
    {
        "title": "Scheduled job missed execution on {service}",
        "description": "Nightly data sync job did not run at 02:00 UTC. Cron scheduler shows no errors. Job manually triggered.",
        "source": "airflow",
        "severity": IncidentSeverity.LOW,
    },
    {
        "title": "Third-party API degradation affecting {service}",
        "description": "Stripe API returning elevated error rates. Payment processing success rate dropped to 91%. Circuit breaker engaged.",
        "source": "pagerduty",
        "severity": IncidentSeverity.HIGH,
    },
]

SERVICES = [
    "payment-service",
    "auth-service",
    "user-api",
    "order-processor",
    "notification-service",
    "search-indexer",
    "analytics-pipeline",
    "api-gateway",
    "inventory-service",
    "billing-service",
]

ENVIRONMENTS = ["prod", "staging", "dev"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
STATUSES = list(IncidentStatus)
ASSIGNEES = [
    "alice@opsmesh.dev",
    "bob@opsmesh.dev",
    "carol@opsmesh.dev",
    "dave@opsmesh.dev",
    None,
    None,  # Some unassigned
]


async def seed():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async with session_factory() as session:
        # Check if data already exists
        from sqlalchemy import func, select

        count = (
            await session.execute(select(func.count()).select_from(Incident))
        ).scalar()
        if count and count > 0:
            print(f"Database already has {count} incidents. Skipping seed.")
            print("To re-seed, run: DELETE FROM incidents;")
            return

        now = datetime.now(timezone.utc)
        incidents = []

        for i in range(50):
            template = random.choice(TEMPLATES)
            service = random.choice(SERVICES)
            status = random.choice(STATUSES)
            detected_at = now - timedelta(
                hours=random.randint(1, 168),  # up to 1 week ago
                minutes=random.randint(0, 59),
            )

            incident = Incident(
                title=template["title"].format(service=service),
                description=template["description"],
                source=template["source"],
                severity=template["severity"],
                status=status,
                service=service,
                environment=random.choice(ENVIRONMENTS),
                region=random.choice(REGIONS),
                detected_at=detected_at,
                assigned_to=random.choice(ASSIGNEES),
                processing_status="completed" if status != IncidentStatus.OPEN else "pending",
                severity_score=round(random.uniform(0.1, 1.0), 2),
            )

            # Set timestamps based on status
            if status in (
                IncidentStatus.ACKNOWLEDGED,
                IncidentStatus.INVESTIGATING,
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED,
            ):
                incident.acknowledged_at = detected_at + timedelta(
                    minutes=random.randint(2, 30)
                )
            if status in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED):
                incident.resolved_at = detected_at + timedelta(
                    hours=random.randint(1, 24)
                )

            incidents.append(incident)

        session.add_all(incidents)
        await session.commit()
        print(f"Seeded {len(incidents)} incidents successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
