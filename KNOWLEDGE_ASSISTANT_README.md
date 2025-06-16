# 🧠 Personal Knowledge Assistant - MCP Server Example

A practical demonstration of Robyn's MCP (Model Context Protocol) implementation that turns your development environment into an AI-accessible workspace.

## What This Does

This MCP server allows AI assistants like Claude Desktop to:

- **📁 Access your files**: Read documents, list directories, browse project structures
- **🔍 Search content**: Find files containing specific text across your workspace  
- **📝 Manage notes**: Create and organize markdown notes in your Documents folder
- **✅ Track tasks**: Add, complete, and manage your todo list
- **🔧 Monitor system**: Check running processes and system statistics
- **🌐 Fetch web content**: Download and analyze content from URLs
- **🎯 Git integration**: View repository status and recent commits
- **🤖 Smart prompts**: Generate context-aware prompts for code analysis and planning

## Quick Start

1. **Run the server**:
   ```bash
   python example_knowledge_assistant.py
   ```

2. **Connect Claude Desktop** to: `http://localhost:8080/mcp`

3. **Ask Claude natural questions** like:
   - *"What files are in my projects directory?"*
   - *"Show me my recent git commits for my-project"*
   - *"Create a note about today's standup meeting"*
   - *"What processes are using the most CPU?"*
   - *"Add a task to review the quarterly report"*
   - *"Search my files for anything about machine learning"*

## Example Conversations with Claude

### 📁 File Management
```
You: "What's in my Documents folder?"
Claude: [Uses fs://dir/Documents resource]
"I can see your Documents folder contains:
📁 notes (your notes directory)
📄 tasks.json (your task list)
📁 projects (symlink to your projects)
..."
```

### 📝 Note Taking
```
You: "Create a note about the new API design we discussed"
Claude: [Uses create_note tool]
"I've created a note titled 'API Design Discussion' with the current timestamp. 
The note has been saved to your Documents/notes folder."
```

### 🔍 Code Analysis
```
You: "Help me review the main.py file in my web-app project"
Claude: [Uses fs://web-app/main.py resource, then analyze_file_structure prompt]
"I can see your main.py file. Here's my analysis:
- The code structure follows Flask patterns well
- Consider adding error handling for the database connections
- The API endpoints could benefit from input validation
..."
```

## Directory Structure

The assistant automatically creates:

```
~/Documents/
├── notes/           # Markdown notes created via MCP
└── tasks.json      # JSON task list

~/projects/          # Your development projects
├── project1/
├── project2/
└── ...
```

## Security Features

- **Home directory only**: File access is restricted to your home directory
- **Safe evaluation**: Mathematical expressions use restricted eval
- **Path validation**: All file paths are validated before access
- **Read-only git**: Git operations are read-only (status, log)

## MCP Resources Available

### File System
- `fs://{path}` - Read any file in your home directory
- `fs://dir/{path}` - List directory contents

### Git Integration  
- `git://repo/{repo_name}` - Get repository status and recent commits

### System Monitoring
- `system://processes` - Running processes (with fallback if psutil not available)
- `system://stats` - System statistics and disk usage

## MCP Tools Available

- **create_note(title, content, tags)** - Create markdown notes
- **add_task(task, priority, due_date)** - Add items to task list
- **complete_task(task_id)** - Mark tasks as done
- **search_files(query, directory)** - Search file contents
- **fetch_url_content(url, max_length)** - Download web content

## MCP Prompts Available

- **analyze_file_structure(directory)** - Generate project analysis prompts
- **code_review_request(file_path, focus_area)** - Create code review prompts  
- **task_prioritization(context)** - Help organize and prioritize work

## Optional Dependencies

For enhanced functionality, install:

```bash
pip install psutil  # Better system monitoring
```

The server works without these dependencies using fallbacks.

## Real-World Use Cases

### 🏗️ Development Workflow
*"Claude, look at my projects directory and help me prioritize which project to work on next based on recent activity"*

### 📊 Project Analysis  
*"Analyze the structure of my web-app project and suggest improvements"*

### 📝 Meeting Notes
*"Create a note about today's architecture review meeting with the key decisions we made"*

### 🔍 Code Search
*"Find all files in my projects that mention 'authentication' and summarize the different approaches I'm using"*

### 📋 Task Management
*"Add a task to refactor the user service, set priority to high, and due date to Friday"*

## Integration with Claude Desktop

Once connected, Claude can seamlessly:
- Browse your file system as if it's a native capability
- Remember context across conversations about your projects
- Suggest improvements based on your actual codebase
- Help organize and prioritize your real tasks
- Provide code reviews of your actual files

This transforms Claude from a general assistant into a personalized development companion that understands your specific workspace and projects.

## Advanced Usage

The MCP implementation supports:
- **URI templates** with parameter extraction
- **Auto-generated schemas** from Python type hints
- **Async/sync handlers** for all operations
- **Proper error handling** with MCP-compliant responses
- **Type-safe parameter passing** from JSON-RPC calls

This makes it easy to extend with additional resources, tools, and prompts specific to your workflow.