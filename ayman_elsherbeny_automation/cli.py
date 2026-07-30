#!/usr/bin/env python
"""
CLI entry point for أيمن الشربيني Automation
"""
import sys
import json
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ayman_elsherbeny_automation import config, logger, OUTPUT_DIR, INPUT_DIR, MODELS_DIR, CONFIG_DIR, LOGS_DIR
from ayman_elsherbeny_automation.core.automation import create_automation
from ayman_elsherbeny_automation.utils.device import get_gpu_memory_info, print_memory_summary

console = Console()


def print_banner():
    """Print application banner"""
    console.print(Panel.fit(
        "[bold cyan]أيمن الشربيني - Text/Image to Video Automation[/bold cyan]\n"
        "[dim]أوتوميشن احترافي لتحويل النصوص والصور إلى فيديوهات مع صوت[/dim]",
        border_style="cyan"
    ))


@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Custom config file path')
@click.pass_context
def cli(ctx, verbose, config):
    """أيمن الشربيني - Text/Image to Video with Audio Automation"""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    if ctx.invoked_subcommand is None:
        print_banner()
        ctx.invoke(info)


@cli.command()
@click.argument('prompt')
@click.option('--audio-text', '-a', help='Text for audio (defaults to prompt)')
@click.option('--voice', '-V', help='TTS voice')
@click.option('--language', '-L', default='ar', help='TTS language')
@click.option('--frames', '-f', type=int, default=25, help='Number of frames')
@click.option('--fps', type=int, default=7, help='Frames per second')
@click.option('--motion-bucket', '-m', type=int, default=127, help='Motion bucket ID (1-255)')
@click.option('--noise-aug', '-n', type=float, default=0.02, help='Noise augmentation strength')
@click.option('--seed', '-s', type=int, help='Random seed')
@click.option('--width', '-W', type=int, default=1024, help='Video width')
@click.option('--height', '-H', type=int, default=576, help='Video height')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.option('--keep-intermediate', '-k', is_flag=True, help='Keep intermediate files')
@click.option('--negative-prompt', help='Negative prompt for image generation')
def txt2vid(prompt, audio_text, voice, language, frames, fps, motion_bucket,
            noise_aug, seed, width, height, output, keep_intermediate, negative_prompt):
    """Text to Video with Audio"""
    print_banner()
    console.print(f"[bold]Prompt:[/bold] {prompt}")

    with create_automation() as automation:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating video...", total=None)
            result = automation.text_to_video(
                prompt=prompt,
                audio_text=audio_text,
                voice=voice,
                language=language,
                num_frames=frames,
                fps=fps,
                motion_bucket_id=motion_bucket,
                noise_aug_strength=noise_aug,
                seed=seed,
                width=width,
                height=height,
                output_name=output,
                keep_intermediate=keep_intermediate,
            )
            progress.update(task, completed=True)

    console.print(Panel(
        f"[green]✓ Completed![/green]\n"
        f"Video: {result['video']}\n"
        f"Audio: {result['audio']}\n"
        f"Merged: {result['merged']}",
        title="Result",
        border_style="green"
    ))


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--audio-text', '-a', help='Text for audio')
@click.option('--voice', '-V', help='TTS voice')
@click.option('--language', '-L', default='ar', help='TTS language')
@click.option('--frames', '-f', type=int, default=25, help='Number of frames')
@click.option('--fps', type=int, default=7, help='Frames per second')
@click.option('--motion-bucket', '-m', type=int, default=127, help='Motion bucket ID (1-255)')
@click.option('--noise-aug', '-n', type=float, default=0.02, help='Noise augmentation strength')
@click.option('--seed', '-s', type=int, help='Random seed')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.option('--keep-intermediate', '-k', is_flag=True, help='Keep intermediate files')
def img2vid(image_path, audio_text, voice, language, frames, fps, motion_bucket,
            noise_aug, seed, output, keep_intermediate):
    """Image to Video with Audio"""
    print_banner()
    console.print(f"[bold]Input image:[/bold] {image_path}")

    with create_automation() as automation:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating video...", total=None)
            result = automation.image_to_video(
                image_path=image_path,
                audio_text=audio_text,
                voice=voice,
                language=language,
                num_frames=frames,
                fps=fps,
                motion_bucket_id=motion_bucket,
                noise_aug_strength=noise_aug,
                seed=seed,
                output_name=output,
                keep_intermediate=keep_intermediate,
            )
            progress.update(task, completed=True)

    console.print(Panel(
        f"[green]✓ Completed![/green]\n"
        f"Video: {result['video']}\n"
        f"Audio: {result['audio']}\n"
        f"Merged: {result['merged']}",
        title="Result",
        border_style="green"
    ))


@cli.command()
@click.argument('text')
@click.option('--engine', '-e', type=click.Choice(['edge-tts', 'coqui-tts', 'gtts', 'pyttsx3']),
              default='edge-tts', help='TTS engine')
@click.option('--voice', '-V', help='Voice name')
@click.option('--language', '-L', default='ar', help='Language code')
@click.option('--output', '-o', help='Output filename')
def audio(text, engine, voice, language, output):
    """Generate audio only (Text-to-Speech)"""
    print_banner()

    # Update config for this run
    if engine:
        config.set('audio.tts_engine', engine)
    if voice:
        config.set('audio.voice', voice)
    if language:
        config.set('audio.language', language)

    from ayman_elsherbeny_automation.generation.audio_generator import create_audio_generator

    generator = create_audio_generator()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating audio...", total=None)
        output_path = generator.generate(
            text=text,
            output_path=output,
            voice=voice,
            language=language,
        )
        progress.update(task, completed=True)

    console.print(Panel(
        f"[green]✓ Audio generated![/green]\n"
        f"File: {output_path}",
        title="Result",
        border_style="green"
    ))


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--mode', '-m', type=click.Choice(['text_to_video', 'image_to_video']),
              default='text_to_video', help='Processing mode')
@click.option('--output-dir', '-d', help='Output directory')
def batch(input_file, mode, output_dir):
    """Batch processing from JSON file"""
    print_banner()

    with open(input_file, 'r', encoding='utf-8') as f:
        inputs = json.load(f)

    console.print(f"[bold]Processing {len(inputs)} items...[/bold]")

    with create_automation() as automation:
        results = automation.batch_process(
            inputs=inputs,
            mode=mode,
            output_dir=output_dir,
        )

    # Summary
    table = Table(title="Batch Results")
    table.add_column("#", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Output", style="green")

    for i, result in enumerate(results):
        if result and result.get('merged'):
            table.add_row(str(i+1), "✓ Success", str(result['merged']))
        else:
            table.add_row(str(i+1), "✗ Failed", "-")

    console.print(table)


@cli.command()
@click.option('--engine', '-e', type=click.Choice(['edge-tts', 'coqui-tts']),
              default='edge-tts', help='TTS engine')
@click.option('--language', '-L', default='ar', help='Language filter')
def voices(engine, language):
    """List available voices"""
    print_banner()

    if engine == 'edge-tts':
        import asyncio
        import edge_tts

        async def list_voices():
            voices = await edge_tts.list_voices()
            if language:
                voices = [v for v in voices if v['Locale'].startswith(language)]

            table = Table(title=f"Edge TTS Voices ({language or 'all'})")
            table.add_column("Name", style="cyan")
            table.add_column("Gender", style="yellow")
            table.add_column("Locale", style="green")
            table.add_column("Style", style="magenta")

            for v in voices:
                table.add_row(
                    v['ShortName'],
                    v['Gender'],
                    v['Locale'],
                    v.get('StyleList', ['-'])[0] if v.get('StyleList') else '-'
                )

            console.print(table)

        asyncio.run(list_voices())

    elif engine == 'coqui-tts':
        try:
            from TTS.api import TTS
            models = TTS.list_models()
            table = Table(title="Coqui TTS Models")
            table.add_column("Model", style="cyan")
            for m in models:
                table.add_row(m)
            console.print(table)
        except ImportError:
            console.print("[red]Coqui TTS not installed. Run: pip install TTS[/red]")


@cli.command()
def info():
    """Show system information"""
    print_banner()

    # GPU Info
    gpu_info = get_gpu_memory_info()
    if gpu_info['available']:
        console.print(Panel(
            f"GPU: {gpu_info['device_name']}\n"
            f"Allocated: {gpu_info['memory_allocated']:.2f} GB\n"
            f"Reserved: {gpu_info['memory_reserved']:.2f} GB\n"
            f"Max Allocated: {gpu_info['max_memory_allocated']:.2f} GB",
            title="GPU Information",
            border_style="blue"
        ))
    else:
        console.print(Panel(
            "No CUDA GPU available - running on CPU",
            title="GPU Information",
            border_style="yellow"
        ))

    # Config
    console.print(Panel(
        f"Video Model: {config.get('video.model')}\n"
        f"TTS Engine: {config.get('audio.tts_engine')}\n"
        f"Default Voice: {config.get('audio.voice')}\n"
        f"Device: {config.get('hardware.device')}\n"
        f"Precision: {config.get('video.dtype')}\n"
        f"Output Dir: {OUTPUT_DIR}",
        title="Configuration",
        border_style="green"
    ))

    # Directories
    console.print(f"\n[bold]Directories:[/bold]")
    console.print(f"  Input:  {INPUT_DIR}")
    console.print(f"  Output: {OUTPUT_DIR}")
    console.print(f"  Models: {MODELS_DIR}")
    console.print(f"  Config: {CONFIG_DIR}")
    console.print(f"  Logs:   {LOGS_DIR}")


@cli.command()
@click.option('--fraction', '-f', type=float, default=0.9, help='Memory fraction (0-1)')
def gpu_memory(fraction):
    """Set GPU memory fraction"""
    from ayman_elsherbeny_automation.utils.device import set_memory_fraction
    set_memory_fraction(fraction)
    console.print(f"[green]GPU memory fraction set to {fraction}[/green]")
    print_memory_summary()


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unhandled error")
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()