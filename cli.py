"""
Command-Line Interface for Reddit Analysis System
Provides easy command-line access to analysis features
"""

import argparse
import sys
import logging
from pathlib import Path
import json

from reddit_analyzer import RedditAnalyzer


def format_insights(insights):
    """Format insights for terminal display (handles dicts and strings)."""
    import textwrap
    formatted = []
    for insight in insights:
        if isinstance(insight, dict):
            title = insight.get('insight', 'Insight')
            evidence = insight.get('evidence', '')
            importance = insight.get('importance', '')
            formatted.append(f"\n🎯 {title}")
            if evidence:
                wrapped = textwrap.fill(
                    str(evidence), width=80,
                    initial_indent='   Evidence: ',
                    subsequent_indent='             '
                )
                formatted.append(wrapped)
            if importance:
                wrapped = textwrap.fill(
                    str(importance), width=80,
                    initial_indent='   Impact: ',
                    subsequent_indent='           '
                )
                formatted.append(wrapped)
        else:
            formatted.append(f"  • {insight}")
    return "\n".join(formatted)


def format_theme_distribution(theme_percentages):
    """Format theme percentages for display."""
    if not theme_percentages:
        return ""
    lines = ["\n  Theme Distribution:"]
    for theme, pct in sorted(theme_percentages.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"    • {theme}: {pct}%")
    return "\n".join(lines)


def setup_cli_logging(verbose: bool = False):
    """Setup logging for CLI"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def analyze_single(args):
    """Analyze a single Reddit post"""
    print(f"\n{'='*60}")
    print("Reddit Post Analysis")
    print(f"{'='*60}\n")
    
    try:
        # Initialize analyzer
        if args.config:
            analyzer = RedditAnalyzer.from_config_file(args.config)
        else:
            analyzer = RedditAnalyzer.from_env()
        
        # Analyze post
        result = analyzer.analyze_post_url(args.url, use_cache=not args.no_cache)
        
        # Display results
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60 + "\n")
        
        print("📊 EXECUTIVE SUMMARY")
        print("-" * 60)
        print(result['synthesis']['executive_summary'])
        print()
        
        print("🔍 KEY ISSUE")
        print("-" * 60)
        print(result['synthesis']['key_issue'])
        print()
        
        print("💡 KEY INSIGHTS")
        print("-" * 60)
        print(format_insights(result['synthesis'].get('key_insights', [])[:5]))
        print()
        
        print("✅ RECOMMENDED ACTIONS")
        print("-" * 60)
        for action in result['synthesis']['recommended_actions'][:5]:
            print(f"  • {action}")
        print()
        
        print("📈 STATISTICS")
        print("-" * 60)
        print(f"  Post Score: {result['metadata']['score']}")
        print(f"  Comments Analyzed: {result['comments_analysis']['total_processed']}")
        print(f"  High Quality Comments: {result['comments_analysis']['high_quality_count']}"
              f" ({result['comments_analysis'].get('high_quality_percentage', 0)}%)")
        print(f"  Analysis Time: {result['metadata']['analysis_duration_seconds']:.1f}s")
        # Theme and tone distributions if available
        theme_block = format_theme_distribution(result['comments_analysis'].get('theme_percentages', {}))
        if theme_block:
            print(theme_block)
        tone_dist = result['comments_analysis'].get('tone_distribution', {})
        if tone_dist:
            print("\n  Tone Distribution:")
            for tone, count in sorted(tone_dist.items(), key=lambda x: x[1], reverse=True)[:6]:
                print(f"    • {tone}: {count}")
        print()
        
        # Show output files
        if result.get('metadata', {}).get('post_id'):
            print("📁 OUTPUT FILES")
            print("-" * 60)
            output_dir = Path('./analysis_results')
            json_files = list(output_dir.glob(f"{result['metadata']['post_id']}*.json"))
            md_files = list(output_dir.glob(f"{result['metadata']['post_id']}*.md"))
            
            if json_files:
                print(f"  JSON: {json_files[0]}")
            if md_files:
                print(f"  Markdown: {md_files[0]}")
            print()
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def analyze_batch(args):
    """Analyze multiple posts from a file"""
    print(f"\n{'='*60}")
    print("Reddit Batch Analysis")
    print(f"{'='*60}\n")
    
    try:
        # Read URLs from file
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"Found {len(urls)} URLs to analyze\n")
        
        # Initialize analyzer
        if args.config:
            analyzer = RedditAnalyzer.from_config_file(args.config)
        else:
            analyzer = RedditAnalyzer.from_env()
        
        # Analyze posts
        results = analyzer.analyze_multiple_posts(urls, use_cache=not args.no_cache)
        
        # Summary
        successful = sum(1 for r in results if r.get('success', False))
        print(f"\n{'='*60}")
        print(f"BATCH ANALYSIS COMPLETE: {successful}/{len(urls)} successful")
        print(f"{'='*60}\n")
        
        return 0 if successful == len(urls) else 1
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def show_cache_stats(args):
    """Show cache statistics"""
    try:
        if args.config:
            analyzer = RedditAnalyzer.from_config_file(args.config)
        else:
            analyzer = RedditAnalyzer.from_env()
        
        stats = analyzer.get_cache_stats()
        
        print("\n📦 CACHE STATISTICS")
        print("="*60)
        print(f"  Posts: {stats.get('posts', 0)}")
        print(f"  Comments: {stats.get('comments', 0)}")
        print(f"  OCR Results: {stats.get('ocr_results', 0)}")
        print(f"  Link Content: {stats.get('link_content', 0)}")
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        return 1


def clear_cache(args):
    """Clear cache"""
    try:
        if args.config:
            analyzer = RedditAnalyzer.from_config_file(args.config)
        else:
            analyzer = RedditAnalyzer.from_env()
        
        if args.all:
            if not args.yes:
                response = input("⚠️  Clear ALL cache entries? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled")
                    return 0
            
            result = analyzer.clear_cache(expired_only=False)
            print(f"✅ All cache cleared")
        else:
            result = analyzer.clear_cache(expired_only=True)
            print(f"✅ Expired cache cleared:")
            for key, count in result.items():
                print(f"  {key}: {count} entries")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Reddit Post & Comment Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single post
  python cli.py analyze "https://reddit.com/r/AskReddit/comments/example/"
  
  # Analyze multiple posts from file
  python cli.py batch urls.txt
  
  # Show cache statistics
  python cli.py cache-stats
  
  # Clear expired cache
  python cli.py cache-clear
  
  # Use custom config
  python cli.py analyze "URL" --config custom_config.yaml
        """
    )
    
    parser.add_argument('--config', '-c', help='Path to config file (default: config.yaml)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single Reddit post')
    analyze_parser.add_argument('url', help='Reddit post URL')
    analyze_parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    analyze_parser.set_defaults(func=analyze_single)
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Analyze multiple posts from file')
    batch_parser.add_argument('file', help='File containing Reddit URLs (one per line)')
    batch_parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    batch_parser.set_defaults(func=analyze_batch)
    
    # Cache stats command
    cache_stats_parser = subparsers.add_parser('cache-stats', help='Show cache statistics')
    cache_stats_parser.set_defaults(func=show_cache_stats)
    
    # Cache clear command
    cache_clear_parser = subparsers.add_parser('cache-clear', help='Clear cache')
    cache_clear_parser.add_argument('--all', action='store_true', help='Clear all cache (not just expired)')
    cache_clear_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    cache_clear_parser.set_defaults(func=clear_cache)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_cli_logging(args.verbose)
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
