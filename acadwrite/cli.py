"""Command-line interface for AcadWrite."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from acadwrite.__version__ import __version__
from acadwrite.config import Settings
from acadwrite.models import CitationStyle, WritingStyle
from acadwrite.models.outline import Outline
from acadwrite.services import FileIntelClient, FormatterService, LLMClient
from acadwrite.workflows import (
    AnalysisDepth,
    ChapterProcessor,
    CitationManager,
    CounterargumentGenerator,
    CounterargumentReport,
    SectionGenerator,
)

app = typer.Typer(
    name="acadwrite",
    help="Academic writing assistant using FileIntel RAG",
    add_completion=False,
)

citations_app = typer.Typer(help="Citation management commands")
config_app = typer.Typer(help="Configuration commands")

app.add_typer(citations_app, name="citations")
app.add_typer(config_app, name="config")

console = Console()


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        console.print(f"[bold]AcadWrite[/bold] version [cyan]{__version__}[/cyan]")
        console.print("Academic writing assistant using FileIntel RAG")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
) -> None:
    """AcadWrite - Academic Writing Assistant."""
    pass


@app.command()
def generate(
    heading: str = typer.Argument(..., help="Section heading to generate content for"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    context: Optional[str] = typer.Option(None, help="Previous section context"),
    style: str = typer.Option("formal", help="Writing style: formal|technical|accessible"),
    citation_style: str = typer.Option("inline", help="Citation style: inline|footnote"),
    max_words: int = typer.Option(1000, help="Maximum section length in words"),
    max_sources: Optional[int] = typer.Option(None, help="Maximum number of sources"),
) -> None:
    """Generate a single academic section with citations."""
    asyncio.run(
        _generate_async(
            heading, collection, output, context, style, citation_style, max_words, max_sources
        )
    )


async def _generate_async(
    heading: str,
    collection: str,
    output: Optional[Path],
    context: Optional[str],
    style: str,
    citation_style: str,
    max_words: int,
    max_sources: Optional[int],
) -> None:
    """Async implementation of generate command."""
    # Load settings
    settings = Settings.load()

    # Parse style enums
    try:
        writing_style = WritingStyle[style.upper()]
    except KeyError:
        console.print(f"[red]Invalid writing style: {style}[/red]")
        console.print(f"Valid options: {', '.join(s.name.lower() for s in WritingStyle)}")
        raise typer.Exit(1)

    try:
        cite_style = CitationStyle[citation_style.upper()]
    except KeyError:
        console.print(f"[red]Invalid citation style: {citation_style}[/red]")
        console.print(f"Valid options: {', '.join(s.name.lower() for s in CitationStyle)}")
        raise typer.Exit(1)

    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Initialize services
        task = progress.add_task("Initializing services...", total=None)

        async with FileIntelClient(
            base_url=settings.fileintel.base_url,
            timeout=settings.fileintel.timeout,
        ) as client:
            formatter = FormatterService()
            generator = SectionGenerator(client, formatter)

            # Generate section
            progress.update(task, description=f"Querying FileIntel for '{heading}'...")
            try:
                section = await generator.generate(
                    heading=heading,
                    collection=collection,
                    context=context,
                    style=writing_style,
                    citation_style=cite_style,
                    max_words=max_words,
                    max_sources=max_sources,
                )
            except Exception as e:
                console.print(f"[red]Error generating section: {e}[/red]")
                raise typer.Exit(1)

            # Format output
            progress.update(task, description="Formatting output...")
            markdown_output = section.to_markdown(cite_style)

            # Add footnotes if using footnote style
            if cite_style == CitationStyle.FOOTNOTE and section.citations:
                footnotes = formatter.generate_footnotes(section.citations)
                if footnotes:
                    markdown_output = f"{markdown_output}\n\n{footnotes}"

    # Output result
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown_output)
        console.print(f"[green]Section saved to {output}[/green]")
        console.print(f"Word count: {section.word_count()}")
        console.print(f"Citations: {len(section.citations)}")
    else:
        console.print("\n" + markdown_output)
        console.print(
            f"\n[dim]Word count: {section.word_count()} | Citations: {len(section.citations)}[/dim]"
        )


@app.command()
def chapter(
    outline_path: Path = typer.Argument(..., help="Path to outline file (.yaml or .md)"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection name"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    single_file: bool = typer.Option(False, "--single-file", help="Combine into one file"),
    style: str = typer.Option("formal", help="Writing style"),
    citation_style: str = typer.Option("inline", help="Citation style: inline|footnote"),
    max_words: Optional[int] = typer.Option(None, help="Maximum words per section"),
    continue_on_error: bool = typer.Option(True, help="Continue if section fails"),
) -> None:
    """Generate multiple sections from an outline file."""
    asyncio.run(
        _chapter_async(
            outline_path,
            collection,
            output_dir,
            single_file,
            style,
            citation_style,
            max_words,
            continue_on_error,
        )
    )


async def _chapter_async(
    outline_path: Path,
    collection: str,
    output_dir: Optional[Path],
    single_file: bool,
    style: str,
    citation_style: str,
    max_words: Optional[int],
    continue_on_error: bool,
) -> None:
    """Async implementation of chapter command."""
    # Verify outline file exists
    if not outline_path.exists():
        console.print(f"[red]Outline file not found: {outline_path}[/red]")
        raise typer.Exit(1)

    # Load settings
    settings = Settings.load()

    # Parse style enums
    try:
        writing_style = WritingStyle[style.upper()]
    except KeyError:
        console.print(f"[red]Invalid writing style: {style}[/red]")
        console.print(f"Valid options: {', '.join(s.name.lower() for s in WritingStyle)}")
        raise typer.Exit(1)

    try:
        cite_style = CitationStyle[citation_style.upper()]
    except KeyError:
        console.print(f"[red]Invalid citation style: {citation_style}[/red]")
        console.print(f"Valid options: {', '.join(s.name.lower() for s in CitationStyle)}")
        raise typer.Exit(1)

    # Parse outline
    try:
        if outline_path.suffix == ".yaml" or outline_path.suffix == ".yml":
            outline = Outline.from_yaml(outline_path)
        elif outline_path.suffix == ".md":
            outline = Outline.from_markdown(outline_path)
        else:
            console.print(f"[red]Unsupported outline format: {outline_path.suffix}[/red]")
            console.print("Supported formats: .yaml, .yml, .md")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error parsing outline: {e}[/red]")
        raise typer.Exit(1)

    # Determine output directory
    if output_dir is None:
        output_dir = Path.cwd() / "output"

    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Initialize services
        task = progress.add_task("Initializing services...", total=None)

        async with FileIntelClient(
            base_url=settings.fileintel.base_url,
            timeout=settings.fileintel.timeout,
        ) as fileintel:
            formatter = FormatterService()
            section_gen = SectionGenerator(fileintel, formatter)
            processor = ChapterProcessor(section_gen, formatter)

            # Process chapter
            progress.update(task, description=f"Processing chapter: {outline.title}")

            try:
                chapter = await processor.process(
                    outline=outline,
                    collection=collection,
                    style=writing_style,
                    citation_style=cite_style,
                    max_words_per_section=max_words,
                    continue_on_error=continue_on_error,
                )
            except Exception as e:
                console.print(f"[red]Error processing chapter: {e}[/red]")
                raise typer.Exit(1)

            # Save chapter
            progress.update(task, description="Saving files...")
            saved_files = processor.save_chapter(
                chapter=chapter,
                output_dir=output_dir,
                citation_style=cite_style,
                single_file=single_file,
            )

    # Display summary
    console.print(f"\n[green]Chapter generated successfully![/green]")
    console.print(f"\nTitle: {chapter.metadata.title}")
    console.print(f"Sections: {chapter.metadata.total_sections}")
    console.print(f"Total words: {chapter.metadata.total_word_count}")
    console.print(
        f"Citations: {chapter.metadata.unique_citations} unique ({chapter.metadata.total_citations} total)"
    )
    console.print(f"\n[cyan]Files saved to {output_dir}:[/cyan]")
    for file_type, file_path in saved_files.items():
        console.print(f"  • {file_type}: {file_path.name}")


@app.command()
def contra(
    claim: str = typer.Argument(..., help="Claim to find counterarguments for"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    depth: str = typer.Option("standard", help="Analysis depth: quick|standard|deep"),
    synthesis: bool = typer.Option(False, "--synthesis", help="Include synthesis section"),
    max_sources: int = typer.Option(5, help="Maximum sources per side"),
) -> None:
    """Find counterarguments and opposing evidence for a claim."""
    asyncio.run(_contra_async(claim, collection, output, depth, synthesis, max_sources))


async def _contra_async(
    claim: str,
    collection: str,
    output: Optional[Path],
    depth: str,
    synthesis: bool,
    max_sources: int,
) -> None:
    """Async implementation of contra command."""
    # Load settings
    settings = Settings.load()

    # Parse depth enum
    try:
        analysis_depth = AnalysisDepth[depth.upper()]
    except KeyError:
        console.print(f"[red]Invalid analysis depth: {depth}[/red]")
        console.print(f"Valid options: {', '.join(d.value for d in AnalysisDepth)}")
        raise typer.Exit(1)

    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Initialize services
        task = progress.add_task("Initializing services...", total=None)

        async with FileIntelClient(
            base_url=settings.fileintel.base_url,
            timeout=settings.fileintel.timeout,
        ) as fileintel:
            llm = LLMClient(
                base_url=settings.llm.base_url,
                model=settings.llm.model,
                api_key=settings.llm.api_key,
                temperature=settings.llm.temperature,
            )

            generator = CounterargumentGenerator(fileintel, llm)

            # Generate report
            progress.update(task, description=f"Analyzing claim: '{claim[:50]}...'")

            try:
                report = await generator.generate(
                    claim=claim,
                    collection=collection,
                    depth=analysis_depth,
                    include_synthesis=synthesis,
                    max_sources_per_side=max_sources,
                )
            except Exception as e:
                console.print(f"[red]Error generating analysis: {e}[/red]")
                raise typer.Exit(1)
            finally:
                await llm.close()

            # Format report
            progress.update(task, description="Formatting report...")
            markdown_output = _format_counterargument_report(report)

    # Output result
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown_output)
        console.print(f"[green]Report saved to {output}[/green]")
        console.print(f"Supporting evidence: {len(report.supporting_evidence)} sources")
        console.print(f"Contradicting evidence: {len(report.contradicting_evidence)} sources")
    else:
        console.print("\n" + markdown_output)
        console.print(
            f"\n[dim]Supporting: {len(report.supporting_evidence)} | "
            f"Contradicting: {len(report.contradicting_evidence)}[/dim]"
        )


def _format_counterargument_report(report: CounterargumentReport) -> str:
    """Format counterargument report as markdown.

    Args:
        report: CounterargumentReport to format

    Returns:
        Markdown-formatted report
    """
    lines = [
        "# Counterargument Analysis",
        "",
        "## Original Claim",
        "",
        f"> {report.original_claim}",
        "",
        "## Inverted Claim",
        "",
        f"> {report.inverted_claim}",
        "",
        "---",
        "",
        f"## Supporting Evidence ({len(report.supporting_evidence)} sources)",
        "",
    ]

    if report.supporting_evidence:
        for i, evidence in enumerate(report.supporting_evidence, 1):
            source = evidence.source
            lines.append(f"### {i}. {source.document_metadata.title or source.filename}")
            lines.append("")
            lines.append(f"**Key Point:** {evidence.key_point}")
            lines.append("")
            lines.append(f"**Source:** {source.citation}")
            lines.append("")
            if source.in_text_citation:
                lines.append(f"**Citation:** {source.in_text_citation}")
                lines.append("")
            lines.append(f"**Relevance Score:** {source.relevance_score:.2f}")
            lines.append("")
    else:
        lines.append("*No supporting evidence found.*")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            f"## Contradicting Evidence ({len(report.contradicting_evidence)} sources)",
            "",
        ]
    )

    if report.contradicting_evidence:
        for i, evidence in enumerate(report.contradicting_evidence, 1):
            source = evidence.source
            lines.append(f"### {i}. {source.document_metadata.title or source.filename}")
            lines.append("")
            lines.append(f"**Key Point:** {evidence.key_point}")
            lines.append("")
            lines.append(f"**Source:** {source.citation}")
            lines.append("")
            if source.in_text_citation:
                lines.append(f"**Citation:** {source.in_text_citation}")
                lines.append("")
            lines.append(f"**Relevance Score:** {source.relevance_score:.2f}")
            lines.append("")
    else:
        lines.append("*No contradicting evidence found.*")
        lines.append("")

    # Add synthesis if present
    if report.synthesis:
        lines.extend(
            [
                "---",
                "",
                "## Synthesis",
                "",
                report.synthesis,
                "",
            ]
        )

    return "\n".join(lines)


@citations_app.command("extract")
def citations_extract(
    file_path: Path = typer.Argument(..., help="Markdown file to extract citations from"),
    format: str = typer.Option("bibtex", help="Output format: bibtex|ris|json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Extract citations from a generated document."""
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Read file
    try:
        text = file_path.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)

    # Extract citations
    manager = CitationManager()
    citations = manager.extract_from_text(text)

    if not citations:
        console.print(f"[yellow]No citations found in {file_path}[/yellow]")
        return

    console.print(f"[green]Extracted {len(citations)} citation(s)[/green]")

    # Export in requested format
    try:
        export_text = manager.export(citations, format)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Output result
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(export_text)
        console.print(f"[green]Citations exported to {output}[/green]")
    else:
        console.print("\n" + export_text)


@citations_app.command("check")
def citations_check(
    file_path: Path = typer.Argument(..., help="Markdown file to check"),
    strict: bool = typer.Option(False, "--strict", help="Strict checking mode"),
) -> None:
    """Check citation integrity in a document."""
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Read file
    try:
        text = file_path.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)

    # Check citations
    manager = CitationManager()
    check_result = manager.check_citations(text, strict=strict)

    # Display results
    console.print(f"\n[bold]Citation Check Results for {file_path}[/bold]\n")
    console.print(f"Total citations: {check_result.total_citations}")
    console.print(f"Valid citations: {check_result.valid_citations}")

    if check_result.invalid_citations:
        console.print(f"\n[red]Invalid citations ({len(check_result.invalid_citations)}):[/red]")
        for invalid in check_result.invalid_citations:
            console.print(f"  - {invalid}")

    if check_result.missing_pages:
        console.print(
            f"\n[yellow]Missing page numbers ({len(check_result.missing_pages)}):[/yellow]"
        )
        for missing in check_result.missing_pages:
            console.print(f"  - {missing}")

    if check_result.warnings:
        console.print(f"\n[yellow]Warnings ({len(check_result.warnings)}):[/yellow]")
        for warning in check_result.warnings:
            console.print(f"  - {warning}")

    # Overall status
    if check_result.invalid_citations:
        console.print(f"\n[red]✗ Citation check FAILED[/red]")
        raise typer.Exit(1)
    elif check_result.missing_pages or check_result.warnings:
        console.print(f"\n[yellow]⚠ Citation check passed with warnings[/yellow]")
    else:
        console.print(f"\n[green]✓ All citations valid[/green]")


@citations_app.command("dedupe")
def citations_dedupe(
    file_path: Path = typer.Argument(..., help="Markdown file to deduplicate"),
    in_place: bool = typer.Option(False, "--in-place", help="Modify file in place"),
) -> None:
    """Deduplicate citations in a document."""
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Deduplicate
    manager = CitationManager()
    num_duplicates = manager.deduplicate_in_file(file_path)

    if num_duplicates == 0:
        console.print(f"[green]No duplicate citations found in {file_path}[/green]")
    else:
        console.print(f"[green]Found {num_duplicates} duplicate citation(s)[/green]")
        if in_place:
            console.print("[yellow]Note: In-place modification not yet fully implemented[/yellow]")
            console.print("[yellow]This feature will be completed in a future update[/yellow]")
        else:
            console.print("[dim]Use --in-place to modify the file directly[/dim]")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    settings = Settings.load()
    console.print("[bold]AcadWrite Configuration[/bold]")
    console.print(f"\n[cyan]FileIntel:[/cyan]")
    console.print(f"  Base URL: {settings.fileintel.base_url}")
    console.print(f"  Timeout: {settings.fileintel.timeout}s")
    console.print(f"  Max Retries: {settings.fileintel.max_retries}")
    console.print(f"\n[cyan]LLM:[/cyan]")
    console.print(f"  Provider: {settings.llm.provider}")
    console.print(f"  Model: {settings.llm.model}")
    console.print(f"  API Key: {'(set)' if settings.llm.api_key else '(not set)'}")
    console.print(f"\n[cyan]Writing:[/cyan]")
    console.print(f"  Citation Style: {settings.writing.citation_style}")
    console.print(f"  Markdown Dialect: {settings.writing.markdown_dialect}")

    # Create table version
    table = Table(title="AcadWrite Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=25)
    table.add_column("Value", style="green")

    # FileIntel settings
    table.add_row("[bold]FileIntel", "")
    table.add_row("  Base URL", settings.fileintel.base_url)
    table.add_row("  Timeout", f"{settings.fileintel.timeout}s")
    table.add_row("  Max Retries", str(settings.fileintel.max_retries))

    # LLM settings
    table.add_row("[bold]LLM", "")
    table.add_row("  Provider", settings.llm.provider)
    table.add_row("  Base URL", settings.llm.base_url)
    table.add_row("  Model", settings.llm.model)
    table.add_row("  API Key", "(set)" if settings.llm.api_key else "[red](not set)[/red]")
    table.add_row("  Temperature", str(settings.llm.temperature))

    # Writing settings
    table.add_row("[bold]Writing", "")
    table.add_row("  Citation Style", settings.writing.citation_style)
    table.add_row("  Markdown Dialect", settings.writing.markdown_dialect)

    console.print("\n")
    console.print(table)


@config_app.command("check")
def config_check() -> None:
    """Verify configuration and connectivity."""
    settings = Settings.load()

    console.print("[bold]Checking AcadWrite Configuration...[/bold]\n")

    checks_passed = 0
    checks_total = 0

    # Check FileIntel configuration
    console.print("[cyan]FileIntel Configuration:[/cyan]")
    checks_total += 1
    if settings.fileintel.base_url:
        console.print(f"  ✓ Base URL configured: {settings.fileintel.base_url}")
        checks_passed += 1
    else:
        console.print("  ✗ Base URL not configured")

    # Check FileIntel connectivity
    checks_total += 1
    try:
        import httpx

        response = httpx.get(f"{settings.fileintel.base_url}/health", timeout=5.0)
        if response.status_code == 200:
            console.print(f"  ✓ FileIntel is reachable")
            checks_passed += 1
        else:
            console.print(f"  ✗ FileIntel returned status {response.status_code}")
    except Exception as e:
        console.print(f"  ✗ Cannot reach FileIntel: {str(e)[:50]}")

    # Check LLM configuration
    console.print("\n[cyan]LLM Configuration:[/cyan]")
    checks_total += 1
    if settings.llm.api_key:
        console.print(f"  ✓ API key is set")
        checks_passed += 1
    else:
        console.print(f"  ⚠ API key not set (required for counterargument analysis)")

    checks_total += 1
    if settings.llm.base_url:
        console.print(f"  ✓ Base URL configured: {settings.llm.base_url}")
        checks_passed += 1
    else:
        console.print(f"  ✗ Base URL not configured")

    # Check writing configuration
    console.print("\n[cyan]Writing Configuration:[/cyan]")
    checks_total += 1
    console.print(f"  ✓ Citation style: {settings.writing.citation_style}")
    console.print(f"  ✓ Markdown dialect: {settings.writing.markdown_dialect}")
    checks_passed += 1

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    if checks_passed == checks_total:
        console.print(f"[green]✓ All checks passed ({checks_passed}/{checks_total})[/green]")
    elif checks_passed >= checks_total - 1:
        console.print(f"[yellow]⚠ {checks_passed}/{checks_total} checks passed[/yellow]")
    else:
        console.print(f"[red]✗ Only {checks_passed}/{checks_total} checks passed[/red]")
        raise typer.Exit(1)


@config_app.command("init")
def config_init(
    output: Path = typer.Option(
        Path.home() / ".acadwrite" / "config.yaml", help="Config file path"
    ),
) -> None:
    """Create a default configuration file."""
    console.print(f"[yellow]Command 'config init' not yet implemented[/yellow]")
    console.print(f"Would create config at: {output}")
