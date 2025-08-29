#!/usr/bin/env uv run python

# /// script
# requires-python = ">=3.8"
# dependencies = [
#   # Add any third-party dependencies here if needed
#   # For this script, we'll use only standard library
# ]
# ///

import json
import sys
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path

class HookBase:
    """Base class for hook functionality"""
    
    def __init__(self, name, config=None):
        self.name = name
        self.config = {**self.get_default_config(), **(config or {})}
        self.hook_dir = Path(__file__).parent.parent / 'hooks' / name
    
    def get_default_config(self):
        return {
            'enabled': True,
            'matcher': '',
            'timeout': 60,
            'description': 'A Claude Code hook'
        }
    
    def execute(self, input_data):
        raise NotImplementedError('execute() must be implemented by subclass')
    
    def success(self, data=None):
        return {
            'success': True,
            'data': data,
            'hook': self.name
        }
    
    def error(self, message, data=None):
        return {
            'success': False,
            'error': message,
            'data': data,
            'hook': self.name
        }
    
    def block(self, reason):
        return {
            'decision': 'block',
            'reason': reason,
            'hook': self.name
        }
    
    def approve(self, reason):
        return {
            'decision': 'approve',
            'reason': reason,
            'hook': self.name
        }
    
    @staticmethod
    def parse_input():
        """Parse JSON input from stdin"""
        return json.load(sys.stdin)
    
    @staticmethod
    def output_result(result):
        """Output result with proper exit codes"""
        if result.get('success') is False:
            print(result.get('error'), file=sys.stderr)
            sys.exit(2 if result.get('decision') == 'block' else 1)
        elif result.get('decision') == 'block':
            print(result.get('reason'), file=sys.stderr)
            sys.exit(2)
        elif result.get('decision') == 'approve':
            print(json.dumps(result))
            sys.exit(0)
        else:
            if result.get('data'):
                print(json.dumps(result['data']))
            sys.exit(0)


class AutoCommitHook(HookBase):
    """Auto-commit hook implementation"""
    
    def __init__(self, config=None):
        # Load config from JSON file if it exists
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                file_config = json.load(f).get('defaultConfig', {})
                config = {**file_config, **(config or {})}
        
        super().__init__('auto-commit', config)
        self.tool_log_file = Path.cwd() / 'claude-tool-events.log'
    
    def get_default_config(self):
        return {
            'enabled': True,
            'matcher': 'Edit|Write|MultiEdit',
            'timeout': 30,
            'description': 'Automatically commit file changes with contextual messages',
            'commitMessageTemplate': 'Auto-commit: {{toolName}} modified {{fileName}}\n\n'
                                   '- File: {{filePath}}\n'
                                   '- Tool: {{toolName}}\n'
                                   '- Session: {{sessionId}}\n\n'
                                   '🤖 Generated with Claude Code\n'
                                   'Co-Authored-By: Claude <noreply@anthropic.com>',
            'excludePatterns': [
                '*.log', '*.tmp', '*.temp', '.env*', '*.key', '*.pem', '*.p12', '*.pfx',
                'node_modules/**', '.git/**', '*.pyc', '__pycache__/**'
            ],
            'skipEmptyCommits': True,
            'addAllFiles': False,
            'branchRestrictions': [],
            'maxCommitMessageLength': 500
        }
    
    def log_tool_event(self, event_type, data):
        """Log tool events to file"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'eventType': event_type,
            'toolName': data.get('toolName') or data.get('tool_name'),
            'parameters': list((data.get('parameters') or data.get('tool_input', {})).keys()),
            'sessionId': data.get('sessionId') or data.get('session_id'),
            'fullDataKeys': list(data.keys())
        }
        
        try:
            with open(self.tool_log_file, 'a') as f:
                f.write(json.dumps(log_entry, indent=2) + '\n\n')
        except Exception as e:
            print(f"Failed to log tool event: {e}", file=sys.stderr)
    
    def execute(self, input_data):
        """Main execution logic"""
        try:
            tool_name = input_data.get('tool_name')
            tool_input = input_data.get('tool_input', {})
            session_id = input_data.get('session_id')
            
            # Log the tool event
            self.log_tool_event('tool_execution', input_data)
            
            # Extract file path from tool input
            file_path = tool_input.get('file_path') or tool_input.get('filePath')
            
            if not file_path:
                return self.error('No file path found in tool input')
            
            # Check if we're in a git repository
            if not self.is_git_repository():
                return self.success({'message': 'Not in a git repository, skipping commit'})
            
            # Check if file should be excluded
            if self.should_exclude_file(file_path):
                return self.success({'message': f'File excluded from auto-commit: {file_path}'})
            
            # Check branch restrictions
            if self.is_branch_restricted():
                return self.success({'message': 'Current branch is restricted from auto-commits'})
            
            # Check if file exists
            if not os.path.exists(file_path):
                return self.error(f'File does not exist: {file_path}')
            
            # Add file to git
            self.run_git_command(['add', file_path])
            
            # Check if there are changes to commit
            if self.config['skipEmptyCommits'] and not self.has_changes_to_commit():
                return self.success({'message': 'No changes to commit'})
            
            # Generate commit message
            commit_message = self.generate_commit_message(tool_name, file_path, session_id)
            
            # Create commit
            self.run_git_command(['commit', '-m', commit_message])
            
            return self.success({
                'message': f'Successfully committed {os.path.basename(file_path)}',
                'filePath': file_path,
                'commitMessage': commit_message
            })
            
        except Exception as e:
            return self.error(f'Auto-commit failed: {str(e)}')
    
    def is_git_repository(self):
        """Check if current directory is a git repository"""
        try:
            self.run_git_command(['rev-parse', '--git-dir'])
            return True
        except:
            return False
    
    def should_exclude_file(self, file_path):
        """Check if file matches exclusion patterns"""
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, os.getcwd())
        
        # Normalize paths to use forward slashes
        normalized_relative_path = relative_path.replace('\\', '/')
        
        for pattern in self.config['excludePatterns']:
            # Convert glob patterns to regex
            regex_pattern = pattern.replace('**', '.*').replace('*', '[^/\\\\]*')
            regex = re.compile(regex_pattern)
            
            if regex.match(file_name) or regex.match(normalized_relative_path):
                return True
        
        return False
    
    def is_branch_restricted(self):
        """Check if current branch is restricted"""
        if not self.config['branchRestrictions']:
            return False
        
        try:
            current_branch = self.run_git_command(['branch', '--show-current'])
            return current_branch.strip() in self.config['branchRestrictions']
        except:
            return False
    
    def has_changes_to_commit(self):
        """Check if there are staged changes"""
        try:
            status = self.run_git_command(['status', '--porcelain'])
            return bool(status.strip())
        except:
            return False
    
    def generate_commit_message(self, tool_name, file_path, session_id):
        """Generate commit message from template"""
        file_name = os.path.basename(file_path)
        template = self.config['commitMessageTemplate']
        
        message = template.replace('{{toolName}}', tool_name or '')
        message = message.replace('{{fileName}}', file_name)
        message = message.replace('{{filePath}}', file_path)
        message = message.replace('{{sessionId}}', session_id or 'unknown')
        
        # Truncate if too long
        max_length = self.config['maxCommitMessageLength']
        if len(message) > max_length:
            message = message[:max_length - 3] + '...'
        
        return message
    
    def run_git_command(self, args):
        """Execute git command and return output"""
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            raise Exception(f'Git command failed: {result.stderr}')
        
        return result.stdout


# Main execution
if __name__ == '__main__':
    try:
        input_data = HookBase.parse_input()
        hook = AutoCommitHook()
        result = hook.execute(input_data)
        HookBase.output_result(result)
    except Exception as e:
        print(f'Auto-commit hook error: {str(e)}', file=sys.stderr)
        sys.exit(1)