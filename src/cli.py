"""
CLI Entry Point for Agentic Builder SDK.

Allows platform meta-agents (Antigravity, CodeX, Cloud-Code, Hermes) to scaffold
new autonomous agent projects and perform incremental modifications via CLI commands.
"""
import argparse
import json
import sys
from pathlib import Path

from src.scaffold.generator import ScaffoldGenerator
from src.scaffold.patcher import ProjectPatcher
from src.scaffold.validator import VALID_SKILLS, VALID_TYPES


def output_result(data: dict, json_mode: bool = False):
    if json_mode:
        print(json.dumps(data, indent=2))
    else:
        if "message" in data:
            print(f"✅ {data['message']}")
        elif "status" in data and data["status"] == "success":
            print(f"🚀 Project '{data.get('project_name')}' generated at: {data.get('path')}")
        else:
            print(json.dumps(data, indent=2))


def handle_new(args):
    skills = args.skills.split(",") if args.skills else None
    generator = ScaffoldGenerator()
    result = generator.generate(
        name=args.name,
        agent_type=args.type,
        skills=skills,
        model=args.model,
        fallback_model=args.fallback,
        output_dir=args.output_dir,
        force=args.force
    )
    output_result(result, json_mode=args.json)


def handle_add(args):
    patcher = ProjectPatcher(project_dir=args.project_dir)
    target = args.target.lower()

    if target == "skill":
        if not args.value:
            print("❌ Error: Missing skill name. Usage: agentic-builder add skill <name>", file=sys.stderr)
            sys.exit(1)
        res = patcher.add_skill(args.value)
    elif target == "ui":
        port = int(args.value) if args.value and args.value.isdigit() else args.port
        res = patcher.add_ui(port=port)
    elif target == "model":
        if not args.value:
            print("❌ Error: Missing model name. Usage: agentic-builder add model <model_name>", file=sys.stderr)
            sys.exit(1)
        res = patcher.set_model(model=args.value, fallback_model=args.fallback)
    else:
        res = {"status": "error", "message": f"Unknown add target '{target}'. Valid targets: skill, ui, model."}

    output_result(res, json_mode=args.json)


def handle_list(args):
    target = (args.target or "all").lower()
    data = {}
    if target in ["types", "all"]:
        data["available_types"] = VALID_TYPES
    if target in ["skills", "all"]:
        data["available_skills"] = VALID_SKILLS

    output_result(data, json_mode=args.json)


def handle_info(args):
    try:
        patcher = ProjectPatcher(project_dir=args.project_dir)
        meta = patcher._load_meta()
        output_result(meta, json_mode=args.json)
    except Exception as e:
        res = {"status": "error", "message": str(e)}
        output_result(res, json_mode=args.json)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="agentic-builder",
        description="Agentic Builder SDK — CLI tool for scaffolding autonomous agent projects"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Verb: new
    parser_new = subparsers.add_parser("new", help="Scaffold a new autonomous agent project")
    parser_new.add_argument("name", help="Name of the project to scaffold")
    parser_new.add_argument("--type", default="react", choices=VALID_TYPES, help="Agent architecture type")
    parser_new.add_argument("--skills", help="Comma-separated list of skills (e.g. researcher,tester)")
    parser_new.add_argument("--model", default="gemini-2.5-flash-lite", help="Primary LLM model")
    parser_new.add_argument("--fallback", default="openai/gpt-4o", help="Fallback LLM model")
    parser_new.add_argument("--output-dir", default="..", help="Parent directory where project will be created")
    parser_new.add_argument("--force", action="store_true", help="Overwrite existing project directory")
    parser_new.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Verb: add
    parser_add = subparsers.add_parser("add", help="Add feature or patch existing agent project")
    parser_add.add_argument("target", choices=["skill", "ui", "model"], help="Feature to add/patch")
    parser_add.add_argument("value", nargs="?", help="Value for the feature (skill name, port, or model name)")
    parser_add.add_argument("--project-dir", default=".", help="Target project directory")
    parser_add.add_argument("--port", type=int, default=7860, help="Port for UI dashboard")
    parser_add.add_argument("--fallback", help="Fallback model name (when setting model)")
    parser_add.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Verb: list
    parser_list = subparsers.add_parser("list", help="List available types and skills")
    parser_list.add_argument("target", nargs="?", choices=["types", "skills"], help="Target to list")
    parser_list.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Verb: info
    parser_info = subparsers.add_parser("info", help="Display scaffold metadata of an existing project")
    parser_info.add_argument("--project-dir", default=".", help="Target project directory")
    parser_info.add_argument("--json", action="store_true", help="Output result in JSON format")

    args = parser.parse_args()

    if args.command == "new":
        handle_new(args)
    elif args.command == "add":
        handle_add(args)
    elif args.command == "list":
        handle_list(args)
    elif args.command == "info":
        handle_info(args)


if __name__ == "__main__":
    main()
