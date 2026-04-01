"""Command-line interface for the job tracker."""

import argparse
from datetime import datetime
from typing import Optional

from . import database

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


def _format_table(jobs: list[dict], columns: Optional[list[str]] = None) -> str:
    """Format jobs as a table."""
    if not jobs:
        return "No jobs found."

    default_columns = ["id", "company", "position", "status", "applied_date"]
    cols = columns or default_columns

    # Filter to existing columns
    cols = [c for c in cols if c in jobs[0]]

    if HAS_TABULATE:
        rows = [[j.get(c, "") for c in cols] for j in jobs]
        return tabulate(rows, headers=[c.replace("_", " ").title() for c in cols], tablefmt="simple")
    else:
        # Simple fallback
        lines = []
        header = " | ".join(c.replace("_", " ").title() for c in cols)
        lines.append(header)
        lines.append("-" * len(header))
        for j in jobs:
            lines.append(" | ".join(str(j.get(c, "")) for c in cols))
        return "\n".join(lines)


def cmd_add(args: argparse.Namespace) -> None:
    """Add a new job application."""
    if args.status and args.status not in database.STATUSES:
        print(f"Invalid status. Must be one of: {', '.join(database.STATUSES)}")
        return

    try:
        job_id = database.add_job(
            company=args.company,
            position=args.position,
            status=args.status or "applied",
            applied_date=args.date,
            salary=args.salary,
            location=args.location,
            url=args.url,
            description=getattr(args, "description", None),
            notes=args.notes,
            applied_resume_path=getattr(args, "applied_resume", None),
            cover_letter_path=getattr(args, "cover_letter", None),
            applied_resume_text=getattr(args, "applied_resume_text", None),
            cover_letter_text=getattr(args, "cover_letter_text", None),
        )
    except ValueError as e:
        print(f"Validation error: {e}")
        return
    print(f"[OK] Added job #{job_id}: {args.position} at {args.company}")


def cmd_list(args: argparse.Namespace) -> None:
    """List all jobs."""
    jobs = database.get_all_jobs(
        status_filter=args.status if args.status != "all" else None,
        company=getattr(args, "company", None),
        position=getattr(args, "position", None),
        description=getattr(args, "description", None),
        date_from=getattr(args, "date_from", None),
        date_to=getattr(args, "date_to", None),
    )
    print(_format_table(jobs))


def cmd_show(args: argparse.Namespace) -> None:
    """Show details of a single job."""
    job = database.get_job(args.id)
    if not job:
        print(f"Job #{args.id} not found.")
        return

    print(f"\nJob #{job['id']}")
    print("-" * 40)
    for key in [
        "company",
        "position",
        "status",
        "applied_date",
        "salary",
        "location",
        "url",
        "applied_resume_path",
        "cover_letter_path",
        "applied_resume_text",
        "cover_letter_text",
        "description",
        "notes",
    ]:
        value = job.get(key)
        if value:
            label = key.replace("_", " ").title()
            print(f"  {label}: {value}")
    print()


def cmd_update(args: argparse.Namespace) -> None:
    """Update a job."""
    job = database.get_job(args.id)
    if not job:
        print(f"Job #{args.id} not found.")
        return

    kwargs = {}
    if args.company is not None:
        kwargs["company"] = args.company
    if args.position is not None:
        kwargs["position"] = args.position
    if args.status is not None:
        if args.status not in database.STATUSES:
            print(f"Invalid status. Must be one of: {', '.join(database.STATUSES)}")
            return
        kwargs["status"] = args.status
    if args.date is not None:
        kwargs["applied_date"] = args.date
    if args.salary is not None:
        kwargs["salary"] = args.salary
    if args.location is not None:
        kwargs["location"] = args.location
    if args.url is not None:
        kwargs["url"] = args.url
    if args.notes is not None:
        kwargs["notes"] = args.notes
    if getattr(args, "description", None) is not None:
        kwargs["description"] = args.description
    if getattr(args, "applied_resume", None) is not None:
        kwargs["applied_resume_path"] = args.applied_resume
    if getattr(args, "cover_letter", None) is not None:
        kwargs["cover_letter_path"] = args.cover_letter
    if getattr(args, "applied_resume_text", None) is not None:
        kwargs["applied_resume_text"] = args.applied_resume_text
    if getattr(args, "cover_letter_text", None) is not None:
        kwargs["cover_letter_text"] = args.cover_letter_text

    if not kwargs:
        print("No updates specified. Use -h for options.")
        return

    try:
        database.update_job(args.id, **kwargs)
    except ValueError as e:
        print(f"Validation error: {e}")
        return
    print(f"[OK] Updated job #{args.id}")


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete a job."""
    if database.delete_job(args.id):
        print(f"[OK] Deleted job #{args.id}")
    else:
        print(f"Job #{args.id} not found.")


def cmd_search(args: argparse.Namespace) -> None:
    """Search jobs by company, position, or notes."""
    jobs = database.search_jobs(args.query)
    print(_format_table(jobs))


def cmd_stats(args: argparse.Namespace) -> None:
    """Show application statistics."""
    stats = database.get_stats()
    if not stats:
        print("No applications yet.")
        return

    total = sum(stats.values())
    print(f"\nApplication Stats (Total: {total})")
    print("-" * 30)
    for status in database.STATUSES:
        if status in stats:
            count = stats[status]
            pct = (count / total * 100) if total else 0
            bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
            print(f"  {status:12} {bar} {count}")
    print()


def main() -> None:
    """Main CLI entry point."""
    database.init_db()

    parser = argparse.ArgumentParser(
        prog="jobtracker",
        description="Track your job applications",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_parser = subparsers.add_parser("add", help="Add a new job application")
    add_parser.add_argument("company", help="Company name")
    add_parser.add_argument("position", help="Job position/title")
    add_parser.add_argument("-s", "--status", choices=database.STATUSES, default="applied")
    add_parser.add_argument("-d", "--date", help="Application date (YYYY-MM-DD)")
    add_parser.add_argument("--salary", help="Salary range or amount")
    add_parser.add_argument("-l", "--location", help="Job location")
    add_parser.add_argument("-u", "--url", help="Job posting URL")
    add_parser.add_argument("--description", help="Job description")
    add_parser.add_argument("-n", "--notes", help="Notes")
    add_parser.add_argument("--applied-resume", dest="applied_resume", help="Path to the resume you applied with")
    add_parser.add_argument("--cover-letter", dest="cover_letter", help="Path to the cover letter you applied with")
    add_parser.add_argument("--applied-resume-text", dest="applied_resume_text", help="Paste the resume text you applied with")
    add_parser.add_argument("--cover-letter-text", dest="cover_letter_text", help="Paste the cover letter text you applied with")
    add_parser.set_defaults(func=cmd_add)

    # list
    list_parser = subparsers.add_parser("list", help="List all jobs")
    list_parser.add_argument("-s", "--status", choices=["all"] + database.STATUSES, default="all", help="Filter by status")
    list_parser.add_argument("-c", "--company", help="Filter by company (partial match)")
    list_parser.add_argument("-p", "--position", help="Filter by position (partial match)")
    list_parser.add_argument("--description", help="Filter by description (partial match)")
    list_parser.add_argument("--date-from", help="Filter from date (YYYY-MM-DD)")
    list_parser.add_argument("--date-to", help="Filter to date (YYYY-MM-DD)")
    list_parser.set_defaults(func=cmd_list)

    # show
    show_parser = subparsers.add_parser("show", help="Show job details")
    show_parser.add_argument("id", type=int, help="Job ID")
    show_parser.set_defaults(func=cmd_show)

    # update
    update_parser = subparsers.add_parser("update", help="Update a job")
    update_parser.add_argument("id", type=int, help="Job ID")
    update_parser.add_argument("-c", "--company", help="Company name")
    update_parser.add_argument("-p", "--position", help="Position title")
    update_parser.add_argument("-s", "--status", choices=database.STATUSES)
    update_parser.add_argument("-d", "--date", help="Application date")
    update_parser.add_argument("--salary", help="Salary")
    update_parser.add_argument("-l", "--location", help="Location")
    update_parser.add_argument("-u", "--url", help="URL")
    update_parser.add_argument("--description", help="Job description")
    update_parser.add_argument("-n", "--notes", help="Notes")
    update_parser.add_argument("--applied-resume", dest="applied_resume", help="Path to the resume you applied with")
    update_parser.add_argument("--cover-letter", dest="cover_letter", help="Path to the cover letter you applied with")
    update_parser.add_argument("--applied-resume-text", dest="applied_resume_text", help="Paste the resume text you applied with")
    update_parser.add_argument("--cover-letter-text", dest="cover_letter_text", help="Paste the cover letter text you applied with")
    update_parser.set_defaults(func=cmd_update)

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a job")
    delete_parser.add_argument("id", type=int, help="Job ID")
    delete_parser.set_defaults(func=cmd_delete)

    # search
    search_parser = subparsers.add_parser("search", help="Search jobs")
    search_parser.add_argument("query", help="Search term (company, position, notes, description)")
    search_parser.set_defaults(func=cmd_search)

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show application statistics")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
