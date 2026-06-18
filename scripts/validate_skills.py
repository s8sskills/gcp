#!/usr/bin/env python3
import os
import sys
import re

try:
    import yaml
except ImportError:
    print("Please install PyYAML: pip install pyyaml")
    sys.exit(1)

# High-risk patterns in bash/sh code blocks
BANNED_PATTERNS = [
    (r"rm\s+-rf\s+(?:\/|\$HOME|\s*~)", "Destructive rm command targeting system or home directories."),
    (r"curl\s+.*\s*\|\s*(?:bash|sh)", "Piping unverified remote curl downloads directly into a shell."),
    (r"wget\s+.*\s*\|\s*(?:bash|sh)", "Piping unverified remote wget downloads directly into a shell."),
    (r"(?:\/etc\/passwd|\/etc\/shadow|\/etc\/hosts)", "Accessing or modifying sensitive system configuration paths."),
    (r"(?:sudo\s+)?(?:chmod|chown)\s+-R\s+777", "Setting dangerous recursive 777 permissions."),
]

def check_skill_file(filepath):
    print(f"🔍 Analyzing: {filepath}")
    errors = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Parse YAML Frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not frontmatter_match:
        errors.append("Missing or improperly formatted YAML frontmatter (needs opening/closing '---').")
        return errors

    raw_yaml = frontmatter_match.group(1)
    try:
        meta = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax in frontmatter: {e}")
        return errors

    # 2. Validate Frontmatter Schema
    if not meta:
        errors.append("Frontmatter is empty.")
        return errors
        
    if 'name' not in meta or not isinstance(meta['name'], str) or not meta['name'].strip():
        errors.append("Frontmatter missing required string field: 'name'.")
    elif not re.match(r"^[a-z0-9\-]+$", meta['name']):
        errors.append(f"Skill name '{meta['name']}' must be lowercase, alphanumeric, and contain only hyphens.")

    if 'description' not in meta or not isinstance(meta['description'], str) or not meta['description'].strip():
        errors.append("Frontmatter missing required string field: 'description'.")
    elif len(meta['description']) > 350:
        errors.append(f"Description is too long ({len(meta['description'])} chars). Keep it under 350 characters.")

    # 3. Code Block Safety & Rule Checks
    code_blocks = re.findall(r"```(?:bash|sh|shell|zsh)\n(.*?)\n```", content, re.DOTALL)
    for idx, block in enumerate(code_blocks):
        for pattern, reason in BANNED_PATTERNS:
            if re.search(pattern, block, re.IGNORECASE):
                errors.append(f"Security Alert (Code Block #{idx+1}): {reason}")

    # 4. Length Guideline Warning
    line_count = len(content.splitlines())
    if line_count > 500:
        print(f"⚠️  Warning: File is {line_count} lines. Skills should ideally remain under 500 lines.")

    return errors

def main():
    skills_dir = "skills"
    if not os.path.exists(skills_dir):
        print(f"No '{skills_dir}' directory found. Skipping checks.")
        sys.exit(0)

    all_errors = {}
    
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.upper() == "SKILL.MD":
                filepath = os.path.join(root, file)
                errors = check_skill_file(filepath)
                if errors:
                    all_errors[filepath] = errors

    if all_errors:
        print("\n❌ Validation Failed! Please resolve the following issues:")
        for path, errors in all_errors.items():
            print(f"\n📂 File: {path}")
            for err in errors:
                print(f"  - {err}")
        sys.exit(1)
        
    print("\n✅ All skills passed structure and security validations successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main()
