"""CLI commands for SaaS administration."""

import click

from ..models import APIKey, init_db
from ..models.base import session_scope


@click.group()
def admin():
    """Administration commands for lex-pdftotext SaaS."""
    pass


@admin.command()
@click.option("--name", required=True, help="Name for the API key")
@click.option("--email", required=True, help="Owner email address")
@click.option("--owner-name", help="Owner name (optional)")
def create_admin_key(name: str, email: str, owner_name: str | None):
    """Create the first admin API key."""
    # Initialize database
    init_db()

    with session_scope() as db:
        # Check if any admin key exists
        existing_admin = db.query(APIKey).filter(APIKey.is_admin.is_(True)).first()
        if existing_admin:
            click.echo(
                click.style("Warning: ", fg="yellow")
                + f"Admin key already exists: {existing_admin.name}"
            )
            if not click.confirm("Create another admin key?"):
                return

        # Create admin key
        api_key = APIKey.create(
            name=name,
            owner_email=email,
            owner_name=owner_name,
            rate_limit_per_minute=1000,
            rate_limit_per_hour=10000,
            monthly_quota=1000000,
            monthly_quota_bytes=10737418240,  # 10GB
            is_admin=True,
        )

        db.add(api_key)
        db.flush()  # Get the ID

        click.echo(click.style("\nAdmin API Key Created!", fg="green", bold=True))
        click.echo(f"\n  Name:  {api_key.name}")
        click.echo(f"  Email: {api_key.owner_email}")
        click.echo("\n  " + click.style("API Key:", fg="cyan") + f" {api_key.key}")
        click.echo("\n  " + click.style("Important:", fg="yellow") + " Save this key securely!")
        click.echo("  It will not be shown again.\n")


@admin.command()
def list_keys():
    """List all API keys."""
    init_db()

    with session_scope() as db:
        keys = db.query(APIKey).order_by(APIKey.created_at.desc()).all()

        if not keys:
            click.echo("No API keys found.")
            return

        click.echo(f"\n{'ID':<5} {'Name':<20} {'Email':<30} {'Admin':<6} {'Active':<7}")
        click.echo("-" * 70)

        for key in keys:
            admin_str = "Yes" if key.is_admin else "No"
            active_str = "Yes" if key.is_active else "No"
            click.echo(
                f"{key.id:<5} {key.name[:20]:<20} {key.owner_email[:30]:<30} "
                f"{admin_str:<6} {active_str:<7}"
            )

        click.echo(f"\nTotal: {len(keys)} keys\n")


@admin.command()
@click.argument("key_id", type=int)
def deactivate_key(key_id: int):
    """Deactivate an API key."""
    init_db()

    with session_scope() as db:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not api_key:
            click.echo(click.style(f"API key {key_id} not found.", fg="red"))
            return

        if not api_key.is_active:
            click.echo(f"API key {key_id} is already inactive.")
            return

        api_key.is_active = False
        click.echo(click.style(f"API key {key_id} ({api_key.name}) deactivated.", fg="green"))


@admin.command()
@click.argument("key_id", type=int)
def activate_key(key_id: int):
    """Activate an API key."""
    init_db()

    with session_scope() as db:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not api_key:
            click.echo(click.style(f"API key {key_id} not found.", fg="red"))
            return

        if api_key.is_active:
            click.echo(f"API key {key_id} is already active.")
            return

        api_key.is_active = True
        click.echo(click.style(f"API key {key_id} ({api_key.name}) activated.", fg="green"))


@admin.command()
@click.argument("key_id", type=int)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_key(key_id: int, yes: bool):
    """Delete an API key."""
    init_db()

    with session_scope() as db:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not api_key:
            click.echo(click.style(f"API key {key_id} not found.", fg="red"))
            return

        if api_key.is_admin:
            admin_count = db.query(APIKey).filter(APIKey.is_admin.is_(True)).count()
            if admin_count <= 1:
                click.echo(click.style("Cannot delete the last admin key.", fg="red"))
                return

        if not yes:
            if not click.confirm(f"Delete API key {key_id} ({api_key.name})?"):
                return

        db.delete(api_key)
        click.echo(click.style(f"API key {key_id} deleted.", fg="green"))


if __name__ == "__main__":
    admin()
