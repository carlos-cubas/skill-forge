"""
ElevenLabs integration CLI commands.

This module provides CLI commands for managing ElevenLabs integration:
- skillforge elevenlabs connect - Store API credentials
- skillforge elevenlabs sync - Sync skills to Knowledge Base
- skillforge elevenlabs status - Show sync status
- skillforge elevenlabs disconnect - Remove stored credentials
- skillforge elevenlabs create - Create new agent with skills
- skillforge elevenlabs configure - Configure existing agent with skills
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from skillforge.adapters.elevenlabs.agent import (
    AgentError,
    SkillNotSyncedError,
    create_agent as create_agent_func,
    configure_agent as configure_agent_func,
)
from skillforge.adapters.elevenlabs.credentials import (
    CredentialsNotFoundError,
    InvalidCredentialsError,
    delete_credentials,
    load_credentials,
    save_credentials,
    verify_credentials,
)
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest
from skillforge.adapters.elevenlabs.sync import (
    SyncError,
    sync_skill_to_kb,
    sync_skills_to_kb,
)
from skillforge.core.config import load_config
from skillforge.core.loader import SkillLoader

app = typer.Typer(help="ElevenLabs integration commands")
console = Console()


@app.command()
def connect(
    api_key: str = typer.Option(
        ...,
        "--api-key",
        prompt="Enter your ElevenLabs API key",
        hide_input=True,
        help="ElevenLabs API key",
    ),
    skip_verify: bool = typer.Option(
        False,
        "--skip-verify",
        help="Skip API key verification",
    ),
) -> None:
    """Store ElevenLabs API credentials.

    Securely stores your ElevenLabs API key for use with skill sync commands.
    The key is stored in ~/.skillforge/elevenlabs.json with restricted permissions.

    Example:
        $ skillforge elevenlabs connect --api-key YOUR_API_KEY
    """
    if not api_key.strip():
        console.print("[red]Error:[/red] API key cannot be empty")
        raise typer.Exit(1)

    # Verify credentials unless skipped
    if not skip_verify:
        with console.status("[bold]Verifying credentials...[/bold]"):
            try:
                verify_credentials(api_key)
                console.print("[green]Credentials verified successfully[/green]")
            except InvalidCredentialsError as e:
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1)
            except ImportError as e:
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1)
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Could not verify credentials: {e}"
                )
                console.print("Saving credentials anyway...")

    # Save credentials
    try:
        save_credentials(api_key)
        console.print("[green]ElevenLabs credentials saved successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to save credentials: {e}")
        raise typer.Exit(1)


@app.command()
def disconnect() -> None:
    """Remove stored ElevenLabs credentials.

    Deletes the stored API key from ~/.skillforge/elevenlabs.json.

    Example:
        $ skillforge elevenlabs disconnect
    """
    if delete_credentials():
        console.print("[green]ElevenLabs credentials removed[/green]")
    else:
        console.print("[yellow]No credentials found[/yellow]")


@app.command()
def sync(
    skills: Optional[str] = typer.Option(
        None,
        "--skills",
        help="Comma-separated list of skill names to sync (default: all)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-sync even if content unchanged",
    ),
) -> None:
    """Sync skills to ElevenLabs Knowledge Base.

    Uploads skill content to ElevenLabs KB, enabling RAG-based skill retrieval
    in conversational AI agents. Each skill is formatted with a `# SKILL: name`
    header for easy retrieval.

    Examples:
        $ skillforge elevenlabs sync                    # Sync all skills
        $ skillforge elevenlabs sync --skills X,Y      # Sync specific skills
        $ skillforge elevenlabs sync --force           # Force re-sync all
    """
    # Check credentials
    try:
        load_credentials()
    except CredentialsNotFoundError:
        # Check for environment variable fallback
        import os

        if not os.environ.get("ELEVENLABS_API_KEY"):
            console.print(
                "[red]Error:[/red] No credentials found. "
                "Run 'skillforge elevenlabs connect' or set ELEVENLABS_API_KEY"
            )
            raise typer.Exit(1)

    # Load config and discover skills
    config = load_config()
    loader = SkillLoader(config.skill_paths)

    with console.status("[bold]Discovering skills...[/bold]"):
        all_skills = loader.discover()

    if not all_skills:
        console.print("[yellow]No skills found to sync[/yellow]")
        console.print("Check your .skillforge.yaml skill_paths configuration")
        raise typer.Exit(0)

    # Filter to specific skills if requested
    if skills:
        skill_names = [s.strip() for s in skills.split(",")]
        skills_to_sync = {}
        missing = []

        for name in skill_names:
            if name in all_skills:
                skills_to_sync[name] = all_skills[name]
            else:
                missing.append(name)

        if missing:
            console.print(
                f"[yellow]Warning:[/yellow] Skills not found: {', '.join(missing)}"
            )

        if not skills_to_sync:
            console.print("[red]Error:[/red] No matching skills found")
            raise typer.Exit(1)
    else:
        skills_to_sync = all_skills

    # Show what we're syncing
    console.print(f"\n[bold]Syncing {len(skills_to_sync)} skill(s)...[/bold]\n")

    # Initialize manifest
    manifest = ElevenLabsManifest()

    # Sync each skill with progress
    synced = 0
    skipped = 0
    errors = []

    for skill_name, skill in skills_to_sync.items():
        try:
            with console.status(f"[bold]Syncing {skill_name}...[/bold]"):
                doc_id, was_updated = sync_skill_to_kb(skill, manifest, force)

            if was_updated:
                console.print(f"  [green]+[/green] {skill_name} -> {doc_id[:20]}...")
                synced += 1
            else:
                console.print(f"  [dim]-[/dim] {skill_name} (unchanged)")
                skipped += 1

        except SyncError as e:
            console.print(f"  [red]x[/red] {skill_name}: {e}")
            errors.append(skill_name)

    # Save manifest
    manifest.save()

    # Summary
    console.print()
    if synced > 0:
        console.print(f"[green]Synced {synced} skill(s)[/green]")
    if skipped > 0:
        console.print(f"[dim]Skipped {skipped} unchanged skill(s)[/dim]")
    if errors:
        console.print(f"[red]Failed to sync {len(errors)} skill(s)[/red]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show ElevenLabs sync status.

    Displays which skills have been synced to the Knowledge Base,
    their document IDs, and sync timestamps.

    Example:
        $ skillforge elevenlabs status
    """
    manifest = ElevenLabsManifest()
    synced_skills = manifest.list_synced_skills()

    if not synced_skills:
        console.print("[yellow]No skills synced to ElevenLabs[/yellow]")
        console.print("Run 'skillforge elevenlabs sync' to sync skills")
        return

    # Create table
    table = Table(title="ElevenLabs Sync Status")
    table.add_column("Skill", style="cyan")
    table.add_column("Document ID", style="dim")
    table.add_column("Synced At", style="green")

    for skill_name in synced_skills:
        info = manifest.get_sync_info(skill_name)
        if info:
            doc_id = info.get("document_id", "")
            synced_at = info.get("synced_at", "")
            # Truncate doc_id for display
            display_id = doc_id[:20] + "..." if len(doc_id) > 20 else doc_id
            table.add_row(skill_name, display_id, synced_at)

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(synced_skills)} skill(s) synced")


@app.command()
def create(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name for the new agent",
    ),
    system_prompt: Path = typer.Option(
        ...,
        "--system-prompt",
        "-p",
        help="Path to file containing the core system prompt",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    skills: str = typer.Option(
        ...,
        "--skills",
        "-s",
        help="Comma-separated list of skill names",
    ),
    first_message: str = typer.Option(
        "Hello! How can I help you today?",
        "--first-message",
        "-m",
        help="Initial message the agent sends to users",
    ),
    voice_id: Optional[str] = typer.Option(
        None,
        "--voice-id",
        "-v",
        help="ElevenLabs voice ID (uses default if not specified)",
    ),
    language: str = typer.Option(
        "en",
        "--language",
        "-l",
        help="Agent language code (e.g., 'en', 'es', 'fr')",
    ),
    llm: str = typer.Option(
        "gpt-4o-mini",
        "--llm",
        help="LLM model to use (e.g., 'gpt-4o-mini', 'gpt-4o')",
    ),
) -> None:
    """Create a new ElevenLabs agent with skills.

    The agent will be configured with:
    - Combined prompt: core system prompt + meta-skill + skill directory
    - Knowledge Base references for each skill (for RAG retrieval)

    Prerequisites:
    - Run 'skillforge elevenlabs connect' to store credentials
    - Run 'skillforge elevenlabs sync' to sync skills to KB

    Examples:
        $ skillforge elevenlabs create \\
            --name "Math Tutor" \\
            --system-prompt ./prompts/tutor.md \\
            --skills socratic-questioning,adaptive-scaffolding \\
            --first-message "Hi! What math topic shall we explore?"

        $ skillforge elevenlabs create \\
            --name "Event Coach" \\
            --system-prompt ./prompts/coach.md \\
            --skills rapid-interviewing,goal-extraction \\
            --voice-id "21m00Tcm4TlvDq8ikWAM" \\
            --language es
    """
    # Check credentials
    try:
        load_credentials()
    except CredentialsNotFoundError:
        import os

        if not os.environ.get("ELEVENLABS_API_KEY"):
            console.print(
                "[red]Error:[/red] No credentials found. "
                "Run 'skillforge elevenlabs connect' or set ELEVENLABS_API_KEY"
            )
            raise typer.Exit(1)

    # Parse skill names
    skill_names = [s.strip() for s in skills.split(",") if s.strip()]
    if not skill_names:
        console.print("[red]Error:[/red] No skills specified")
        raise typer.Exit(1)

    # Read system prompt from file
    try:
        core_prompt = system_prompt.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to read system prompt file: {e}")
        raise typer.Exit(1)

    # Create the agent
    console.print(f"\n[bold]Creating agent '{name}'...[/bold]")
    console.print(f"  Skills: {', '.join(skill_names)}")
    console.print(f"  Language: {language}")
    console.print(f"  LLM: {llm}")
    if voice_id:
        console.print(f"  Voice ID: {voice_id}")

    try:
        agent_id = create_agent_func(
            name=name,
            core_prompt=core_prompt,
            first_message=first_message,
            skills=skill_names,
            voice_id=voice_id,
            language=language,
            llm=llm,
        )

        console.print(f"\n[green]Agent created successfully![/green]")
        console.print(f"  Agent ID: [bold]{agent_id}[/bold]")
        console.print("\nTo configure this agent later:")
        console.print(f"  skillforge elevenlabs configure --agent-id {agent_id} ...")

    except SkillNotSyncedError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("\nSync the required skills first:")
        console.print(f"  skillforge elevenlabs sync --skills {skills}")
        raise typer.Exit(1)

    except AgentError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def configure(
    agent_id: str = typer.Option(
        ...,
        "--agent-id",
        "-a",
        help="ID of the agent to configure",
    ),
    skills: str = typer.Option(
        ...,
        "--skills",
        "-s",
        help="Comma-separated list of skill names",
    ),
    system_prompt: Optional[Path] = typer.Option(
        None,
        "--system-prompt",
        "-p",
        help="Path to file containing new core system prompt (preserves existing if not specified)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Configure an existing ElevenLabs agent with skills.

    Updates the agent's configuration to include:
    - Combined prompt: core system prompt + meta-skill + skill directory
    - Knowledge Base references for each skill (for RAG retrieval)

    By default, preserves the agent's existing core prompt (the part before any
    "---" separator) and only updates the meta-skill and skill directory sections.
    Use --system-prompt to replace the core prompt entirely.

    Prerequisites:
    - Run 'skillforge elevenlabs connect' to store credentials
    - Run 'skillforge elevenlabs sync' to sync skills to KB

    Examples:
        $ skillforge elevenlabs configure \\
            --agent-id abc123 \\
            --skills socratic-questioning,adaptive-scaffolding

        $ skillforge elevenlabs configure \\
            --agent-id abc123 \\
            --system-prompt ./prompts/new-tutor.md \\
            --skills socratic-questioning,adaptive-scaffolding
    """
    # Check credentials
    try:
        load_credentials()
    except CredentialsNotFoundError:
        import os

        if not os.environ.get("ELEVENLABS_API_KEY"):
            console.print(
                "[red]Error:[/red] No credentials found. "
                "Run 'skillforge elevenlabs connect' or set ELEVENLABS_API_KEY"
            )
            raise typer.Exit(1)

    # Parse skill names
    skill_names = [s.strip() for s in skills.split(",") if s.strip()]
    if not skill_names:
        console.print("[red]Error:[/red] No skills specified")
        raise typer.Exit(1)

    # Read new system prompt if provided
    core_prompt = None
    if system_prompt:
        try:
            core_prompt = system_prompt.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to read system prompt file: {e}")
            raise typer.Exit(1)

    # Configure the agent
    console.print(f"\n[bold]Configuring agent {agent_id}...[/bold]")
    console.print(f"  Skills: {', '.join(skill_names)}")
    if system_prompt:
        console.print(f"  System prompt: {system_prompt}")
    else:
        console.print("  System prompt: [dim](preserving existing)[/dim]")

    try:
        configure_agent_func(
            agent_id=agent_id,
            skills=skill_names,
            core_prompt=core_prompt,
            preserve_prompt=True,
        )

        console.print(f"\n[green]Agent configured successfully![/green]")
        console.print(f"  Skills equipped: {', '.join(skill_names)}")

    except SkillNotSyncedError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("\nSync the required skills first:")
        console.print(f"  skillforge elevenlabs sync --skills {skills}")
        raise typer.Exit(1)

    except AgentError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)
