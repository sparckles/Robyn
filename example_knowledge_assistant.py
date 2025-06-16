#!/usr/bin/env python3
"""
Personal Knowledge Assistant - A practical MCP server example

This MCP server provides access to personal knowledge management features:
- File system access for notes and documents
- Git repository information
- System information and process management
- Note-taking and task management
- Web content fetching and summarization

Perfect for connecting to Claude Desktop to get AI assistance with your personal workspace.

Setup:
1. Run: python example_knowledge_assistant.py
2. Connect Claude Desktop to: http://localhost:8080/mcp
3. Ask Claude to help you manage your files, notes, and tasks!

Example queries to Claude:
- "What files are in my projects directory?"
- "Show me my recent git commits"
- "Create a note about today's meeting"
- "What processes are using the most memory?"
- "Fetch and summarize this article: https://example.com/article"
"""

import json
import os
import subprocess
import platform
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.request import urlopen
from urllib.error import URLError
from robyn import Robyn

# Try to import optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

app = Robyn(__file__)

# Configuration
NOTES_DIR = Path.home() / "Documents" / "notes"
PROJECTS_DIR = Path.home() / "projects"
TASKS_FILE = Path.home() / "Documents" / "tasks.json"

# Ensure directories exist
NOTES_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

#
# FILE SYSTEM RESOURCES
#

@app.mcp.resource("fs://{path}")
def read_file_content(path: str) -> str:
    """Read content from a file in the user's home directory"""
    try:
        # Security: only allow access to user's home directory
        full_path = Path.home() / path.lstrip('/')
        if not str(full_path).startswith(str(Path.home())):
            return "Error: Access denied - path outside home directory"
        
        if not full_path.exists():
            return f"Error: File not found: {path}"
        
        if full_path.is_file():
            return full_path.read_text(encoding='utf-8', errors='replace')
        else:
            return f"Error: {path} is not a file"
    except Exception as e:
        return f"Error reading file: {e}"

@app.mcp.resource("fs://dir/{path}")
def list_directory(path: str) -> str:
    """List contents of a directory"""
    try:
        full_path = Path.home() / path.lstrip('/')
        if not str(full_path).startswith(str(Path.home())):
            return "Error: Access denied - path outside home directory"
        
        if not full_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not full_path.is_dir():
            return f"Error: {path} is not a directory"
        
        items = []
        for item in sorted(full_path.iterdir()):
            size = ""
            if item.is_file():
                size = f" ({item.stat().st_size:,} bytes)"
            items.append(f"{'📁' if item.is_dir() else '📄'} {item.name}{size}")
        
        return f"Contents of {path}:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

@app.mcp.resource("git://repo/{repo_name}")
def git_repository_info(repo_name: str) -> str:
    """Get Git repository information"""
    try:
        repo_path = PROJECTS_DIR / repo_name
        if not repo_path.exists():
            return f"Error: Repository not found: {repo_name}"
        
        # Get recent commits
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error: Not a git repository or git command failed: {result.stderr}"
        
        # Get status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        info = f"Git Repository: {repo_name}\n"
        info += f"Location: {repo_path}\n\n"
        
        if status_result.stdout.strip():
            info += "📝 Modified files:\n" + status_result.stdout + "\n"
        else:
            info += "✅ Working directory clean\n\n"
        
        info += "📚 Recent commits:\n" + result.stdout
        
        return info
    except FileNotFoundError:
        return "Error: Git not found. Please install Git."
    except Exception as e:
        return f"Error getting git info: {e}"

#
# SYSTEM RESOURCES
#

@app.mcp.resource("system://processes")
def system_processes() -> str:
    """Get information about running processes"""
    if not HAS_PSUTIL:
        try:
            # Fallback to system commands
            if platform.system() == "Darwin" or platform.system() == "Linux":
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')[:16]  # Header + top 15
                    return "🖥️  Running Processes:\n" + "\n".join(lines)
            elif platform.system() == "Windows":
                result = subprocess.run(["tasklist"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')[:16]  # Header + top 15
                    return "🖥️  Running Processes:\n" + "\n".join(lines)
            
            return "❌ Process information not available (install psutil for better process monitoring)"
        except Exception as e:
            return f"❌ Error getting process info: {e}"
    
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] > 1 or info['memory_percent'] > 1:  # Only show active processes
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cpu': round(info['cpu_percent'], 1),
                        'memory': round(info['memory_percent'], 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        
        result = "🖥️  Top Processes by CPU Usage:\n"
        result += f"{'PID':<8} {'Name':<25} {'CPU%':<8} {'Memory%':<8}\n"
        result += "-" * 50 + "\n"
        
        for proc in processes[:15]:  # Top 15
            result += f"{proc['pid']:<8} {proc['name']:<25} {proc['cpu']:<8} {proc['memory']:<8}\n"
        
        return result
    except Exception as e:
        return f"❌ Error getting process info: {e}"

@app.mcp.resource("system://stats")
def system_stats() -> str:
    """Get system statistics"""
    if not HAS_PSUTIL:
        try:
            # Basic system info using standard library
            stats = f"🖥️  System Information\n"
            stats += f"{'='*30}\n\n"
            stats += f"💻 Platform: {platform.system()} {platform.release()}\n"
            stats += f"🏗️  Architecture: {platform.machine()}\n"
            stats += f"🐍 Python: {platform.python_version()}\n"
            stats += f"📂 Home: {Path.home()}\n"
            stats += f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Try to get disk usage for home directory
            home_stat = os.statvfs(str(Path.home()))
            total_bytes = home_stat.f_frsize * home_stat.f_blocks
            free_bytes = home_stat.f_frsize * home_stat.f_available
            used_bytes = total_bytes - free_bytes
            
            stats += f"💾 Disk (Home): {used_bytes // (1024**3):.1f}GB used / {total_bytes // (1024**3):.1f}GB total\n"
            stats += f"\n💡 Install 'psutil' for detailed system monitoring"
            
            return stats
        except Exception as e:
            return f"❌ Error getting system info: {e}"
    
    try:
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory info
        memory = psutil.virtual_memory()
        
        # Disk info
        disk = psutil.disk_usage('/')
        
        stats = f"🖥️  System Statistics\n"
        stats += f"{'='*30}\n\n"
        stats += f"💻 CPU: {cpu_percent}% used ({cpu_count} cores)\n"
        stats += f"🧠 Memory: {memory.percent}% used ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)\n"
        stats += f"💾 Disk: {disk.percent}% used ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)\n"
        stats += f"⏰ Uptime: {datetime.now() - datetime.fromtimestamp(psutil.boot_time())}\n"
        
        return stats
    except Exception as e:
        return f"❌ Error getting system stats: {e}"

#
# PRODUCTIVITY TOOLS
#

@app.mcp.tool()
def create_note(title: str, content: str, tags: str = "") -> str:
    """Create a new note in the notes directory"""
    try:
        # Create filename from title
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title.replace(' ', '_')}.md"
        
        note_file = NOTES_DIR / filename
        
        # Create note content
        note_content = f"# {title}\n\n"
        note_content += f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        if tags:
            note_content += f"Tags: {tags}\n"
        note_content += f"\n---\n\n{content}\n"
        
        note_file.write_text(note_content, encoding='utf-8')
        
        return f"✅ Note created: {filename}\nLocation: {note_file}"
    except Exception as e:
        return f"❌ Error creating note: {e}"

@app.mcp.tool()
def add_task(task: str, priority: str = "medium", due_date: str = "") -> str:
    """Add a task to the task list"""
    try:
        # Load existing tasks
        tasks = []
        if TASKS_FILE.exists():
            tasks = json.loads(TASKS_FILE.read_text())
        
        # Create new task
        new_task = {
            "id": len(tasks) + 1,
            "task": task,
            "priority": priority,
            "due_date": due_date,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        
        tasks.append(new_task)
        
        # Save tasks
        TASKS_FILE.write_text(json.dumps(tasks, indent=2))
        
        return f"✅ Task added: {task}\nPriority: {priority}\nID: {new_task['id']}"
    except Exception as e:
        return f"❌ Error adding task: {e}"

@app.mcp.tool()
def complete_task(task_id: int) -> str:
    """Mark a task as completed"""
    try:
        if not TASKS_FILE.exists():
            return "❌ No tasks file found"
        
        tasks = json.loads(TASKS_FILE.read_text())
        
        for task in tasks:
            if task["id"] == task_id:
                task["completed"] = True
                task["completed_date"] = datetime.now().isoformat()
                TASKS_FILE.write_text(json.dumps(tasks, indent=2))
                return f"✅ Task {task_id} marked as completed: {task['task']}"
        
        return f"❌ Task {task_id} not found"
    except Exception as e:
        return f"❌ Error completing task: {e}"

@app.mcp.tool()
def search_files(query: str, directory: str = "") -> str:
    """Search for files containing specific text"""
    try:
        search_dir = Path.home() / directory.lstrip('/') if directory else Path.home()
        
        if not str(search_dir).startswith(str(Path.home())):
            return "❌ Access denied - path outside home directory"
        
        matches = []
        for file_path in search_dir.rglob("*.txt"):
            try:
                if file_path.is_file() and query.lower() in file_path.read_text(encoding='utf-8', errors='ignore').lower():
                    relative_path = file_path.relative_to(Path.home())
                    matches.append(str(relative_path))
            except:
                continue  # Skip files that can't be read
        
        for file_path in search_dir.rglob("*.md"):
            try:
                if file_path.is_file() and query.lower() in file_path.read_text(encoding='utf-8', errors='ignore').lower():
                    relative_path = file_path.relative_to(Path.home())
                    matches.append(str(relative_path))
            except:
                continue
        
        if matches:
            return f"🔍 Found {len(matches)} files containing '{query}':\n" + "\n".join(f"📄 {match}" for match in matches[:20])
        else:
            return f"🔍 No files found containing '{query}'"
    except Exception as e:
        return f"❌ Error searching files: {e}"

@app.mcp.tool()
def fetch_url_content(url: str, max_length: int = 5000) -> str:
    """Fetch and return content from a URL"""
    try:
        from urllib.request import Request
        
        # Create request with user agent
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; Personal Knowledge Assistant)'
        })
        
        with urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='replace')
        
        if len(content) > max_length:
            truncated_content = content[:max_length]
            truncated_content += f"\n\n... (content truncated, original was {len(content)} characters)"
            content = truncated_content
        
        return f"📰 Content from {url}:\n\n{content}"
    except URLError as e:
        return f"❌ Error fetching URL: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"

#
# AI ASSISTANCE PROMPTS
#

@app.mcp.prompt()
def analyze_file_structure(directory: str = "projects") -> str:
    """Generate a prompt to analyze project structure"""
    return f"""Please analyze the structure of my {directory} directory and provide insights about:

1. **Project Organization**: How well are the projects organized?
2. **Code Quality**: Any patterns you notice in file naming or structure
3. **Recommendations**: Suggestions for better organization
4. **Missing Elements**: Important files or directories that might be missing (README, tests, etc.)

Focus on actionable insights that could improve my development workflow."""

@app.mcp.prompt()
def code_review_request(file_path: str, focus_area: str = "general") -> str:
    """Generate a code review prompt for a specific file"""
    return f"""Please review the code in {file_path} with focus on {focus_area}.

Provide feedback on:
1. **Code Quality**: Readability, maintainability, and best practices
2. **Performance**: Potential optimizations or inefficiencies  
3. **Security**: Any security concerns or vulnerabilities
4. **Architecture**: Design patterns and code structure
5. **Testing**: Testability and potential test cases

Please be specific and provide actionable recommendations."""

@app.mcp.prompt()
def task_prioritization(context: str = "") -> str:
    """Generate a prompt to help prioritize tasks"""
    context_info = f"\n\nContext: {context}" if context else ""
    
    return f"""Based on my current task list, please help me prioritize my work by:

1. **Urgency Analysis**: Which tasks need immediate attention?
2. **Impact Assessment**: Which tasks will have the biggest positive impact?
3. **Effort Estimation**: Quick wins vs. complex projects
4. **Dependencies**: Tasks that block other work
5. **Time Blocking**: Suggested schedule for tackling these tasks

Please provide a concrete action plan for the next week.{context_info}"""

#
# STANDARD ROBYN ROUTES
#

@app.get("/")
def home():
    """Personal Knowledge Assistant home page"""
    return {
        "name": "Personal Knowledge Assistant",
        "description": "MCP server for personal productivity and knowledge management",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "capabilities": {
            "resources": {
                "file_system": "Read files and list directories in your home folder",
                "git_repos": "Access git repository information",
                "system_info": "Monitor system processes and statistics"
            },
            "tools": {
                "note_taking": "Create and manage markdown notes",
                "task_management": "Add and complete tasks",
                "file_search": "Search file contents",
                "web_content": "Fetch content from URLs"
            },
            "prompts": {
                "code_analysis": "Generate prompts for code review and analysis",
                "task_planning": "Help prioritize and organize work"
            }
        },
        "setup": {
            "notes_directory": str(NOTES_DIR),
            "projects_directory": str(PROJECTS_DIR),
            "tasks_file": str(TASKS_FILE)
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "directories": {
            "notes": NOTES_DIR.exists(),
            "projects": PROJECTS_DIR.exists()
        }
    }

if __name__ == "__main__":
    print("🧠 Personal Knowledge Assistant - MCP Server")
    print("=" * 50)
    print(f"🏠 Home Directory: {Path.home()}")
    print(f"📝 Notes: {NOTES_DIR}")
    print(f"💻 Projects: {PROJECTS_DIR}")
    print(f"✅ Tasks: {TASKS_FILE}")
    print()
    print(f"🌐 Server: http://localhost:8080")
    print(f"🔌 MCP Endpoint: http://localhost:8080/mcp")
    print(f"❤️  Health Check: http://localhost:8080/health")
    print()
    print("🤖 Connect this to Claude Desktop and ask things like:")
    print("   • 'What files are in my projects directory?'")
    print("   • 'Show me my recent git commits for my-project'")
    print("   • 'Create a note about today's meeting'")
    print("   • 'What processes are using the most CPU?'")
    print("   • 'Add a task to review the quarterly report'")
    print("   • 'Search my files for anything about machine learning'")
    print()
    print("🚀 Starting server...")
    
    app.start(port=8080)