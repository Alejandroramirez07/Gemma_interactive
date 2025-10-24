from flask import Flask, request, render_template_string, send_from_directory
import subprocess
import os
import time

app = Flask(__name__)

# Create uploads directory if it doesn't exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('static', exist_ok=True)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>My Local AI Assistant</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .nav {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .nav-button {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .nav-button:hover {
            background: #218838;
        }
        .nav-button.active {
            background: #007cba;
        }
        .chat-container, .tools-container, .upload-container {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: none;
        }
        .active-tab {
            display: block;
        }
        .message-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .send-button {
            background: #007cba;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .send-button:hover {
            background: #005a87;
        }
        .send-button:disabled {
            background: #cccccc;
            cursor: not-allowed;
        }
        .response-box {
            margin-top: 20px;
            padding: 20px;
            background: #e8f4f8;
            border-radius: 5px;
            border-left: 4px solid #007cba;
            white-space: pre-wrap;
            line-height: 1.5;
        }
        .tool-selector {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .file-input {
            margin: 15px 0;
        }
        .status {
            padding: 10px;
            background: #fff3cd;
            border-radius: 5px;
            margin: 10px 0;
        }
        .conversation-history {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            background: #fafafa;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background: #e3f2fd;
            margin-left: 20px;
        }
        .ai-message {
            background: #f3e5f5;
            margin-right: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 My Local AI Assistant</h1>
        <p><em>Powered by Gemma - Running completely offline on your computer</em></p>
    </div>

    <div class="nav">
        <a href="#" class="nav-button active" onclick="showTab('chat')">💬 Chat</a>
        <a href="#" class="nav-button" onclick="showTab('tools')">🛠️ AI Tools</a>
        <a href="#" class="nav-button" onclick="showTab('upload')">📁 Analyze Files</a>
        <a href="#" class="nav-button" onclick="showTab('history')">📚 Conversation History</a>
    </div>

    <!-- Chat Tab -->
    <div id="chat" class="chat-container active-tab">
        <h3>💬 Chat with Gemma</h3>
        <form method="post" id="chatForm">
            <input type="hidden" name="tab" value="chat">
            <input type="text" name="message" class="message-input" 
                   placeholder="Ask me anything about your coursework..." required
                   value="{{ last_message if last_message else '' }}">
            <button type="submit" class="send-button" id="chatButton">Send Message</button>
        </form>
        
        {% if response and active_tab == 'chat' %}
        <div class="response-box">
            <strong>Gemma's Response:</strong><br>
            {{ response }}
        </div>
        {% endif %}
    </div>

    <!-- AI Tools Tab -->
    <div id="tools" class="tools-container">
        <h3>🛠️ AI Study Tools</h3>
        <form method="post" id="toolsForm">
            <input type="hidden" name="tab" value="tools">
            <select name="tool_type" class="tool-selector" required>
                <option value="">Select a tool...</option>
                <option value="summarize">📋 Summarize Text</option>
                <option value="explain">🎓 Explain Concept</option>
                <option value="quiz">❓ Create Quiz Questions</option>
                <option value="examples">💡 Give Examples</option>
                <option value="key_points">🔑 Extract Key Points</option>
            </select>
            <textarea name="message" class="message-input" rows="4" 
                     placeholder="Enter your text or question here..." required>{{ last_message if last_message else '' }}</textarea>
            <button type="submit" class="send-button" id="toolsButton">Process</button>
        </form>
        
        {% if response and active_tab == 'tools' %}
        <div class="response-box">
            <strong>Result:</strong><br>
            {{ response }}
        </div>
        {% endif %}
    </div>

    <!-- File Upload Tab -->
    <div id="upload" class="upload-container">
        <h3>📁 Analyze Text Files</h3>
        <div class="status">
            <strong>Supported files:</strong> .txt, .py, .html, .css, .js, .md
        </div>
        <form method="post" enctype="multipart/form-data" id="uploadForm">
            <input type="hidden" name="tab" value="upload">
            <input type="file" name="file" class="file-input" accept=".txt,.py,.html,.css,.js,.md" required>
            <select name="analysis_type" class="tool-selector" required>
                <option value="">Select analysis type...</option>
                <option value="summarize">📋 Summarize</option>
                <option value="explain">🎓 Explain Content</option>
                <option value="key_points">🔑 Key Points</option>
                <option value="questions">❓ Generate Questions</option>
            </select>
            <button type="submit" class="send-button" id="uploadButton">Analyze File</button>
        </form>
        
        {% if response and active_tab == 'upload' %}
        <div class="response-box">
            <strong>Analysis Result:</strong><br>
            {{ response }}
        </div>
        {% endif %}
    </div>

    <!-- History Tab -->
    <div id="history" class="chat-container">
        <h3>📚 Conversation History</h3>
        <div class="conversation-history" id="conversationHistory">
            {% for msg in conversation_history %}
                <div class="message user-message">
                    <strong>You:</strong> {{ msg.user }}
                </div>
                <div class="message ai-message">
                    <strong>Gemma:</strong> {{ msg.ai }}
                </div>
            {% else %}
                <p>No conversation history yet. Start chatting!</p>
            {% endfor %}
        </div>
        <button class="send-button" onclick="clearHistory()">Clear History</button>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.chat-container, .tools-container, .upload-container').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Show selected tab
            document.getElementById(tabName).style.display = 'block';
            
            // Update active nav button
            document.querySelectorAll('.nav-button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
        }

        // Add loading indicators to all forms
        document.getElementById('chatForm')?.addEventListener('submit', function() {
            const button = this.querySelector('button');
            button.textContent = 'Thinking...';
            button.disabled = true;
        });

        document.getElementById('toolsForm')?.addEventListener('submit', function() {
            const button = this.querySelector('button');
            button.textContent = 'Processing...';
            button.disabled = true;
        });

        document.getElementById('uploadForm')?.addEventListener('submit', function() {
            const button = this.querySelector('button');
            button.textContent = 'Analyzing...';
            button.disabled = true;
        });

        function clearHistory() {
            if (confirm('Are you sure you want to clear conversation history?')) {
                fetch('/clear-history', { method: 'POST' })
                    .then(() => location.reload());
            }
        }

        // Auto-scroll conversation history to bottom
        const historyDiv = document.getElementById('conversationHistory');
        if (historyDiv) {
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }
    </script>
</body>
</html>
'''

# Store conversation history
conversation_history = []

def call_gemma(prompt):
    """Helper function to call Gemma and return response"""
    try:
        result = subprocess.run(
            ['ollama', 'run', 'gemma', prompt],
            capture_output=True, 
            text=True, 
            timeout=60  # 60 second timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Sorry, the request timed out. Please try a simpler question."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def chat():
    response = ""
    last_message = ""
    active_tab = "chat"
    
    if request.method == 'POST':
        active_tab = request.form.get('tab', 'chat')
        last_message = request.form.get('message', '')
        
        if active_tab == 'upload' and 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            if file and file.filename:
                filename = file.filename
                filepath = os.path.join('uploads', filename)
                file.save(filepath)
                
                # Read file content (limit to first 2000 chars to avoid long processing)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read(2000)
                except:
                    with open(filepath, 'r', encoding='latin-1') as f:
                        content = f.read(2000)
                
                analysis_type = request.form.get('analysis_type', 'summarize')
                
                if analysis_type == 'summarize':
                    prompt = f"Summarize the main points of this text: {content}"
                elif analysis_type == 'explain':
                    prompt = f"Explain the content of this text in simple terms: {content}"
                elif analysis_type == 'key_points':
                    prompt = f"Extract the key points from this text: {content}"
                elif analysis_type == 'questions':
                    prompt = f"Generate 3 quiz questions based on this text: {content}"
                else:
                    prompt = f"Analyze this text: {content}"
                
                response = call_gemma(prompt)
                last_message = f"File: {filename} | Analysis: {analysis_type}"
                
        else:
            # Handle text input
            tool_type = request.form.get('tool_type', '')
            
            if tool_type == 'summarize':
                prompt = f"Summarize this in 3-5 bullet points: {last_message}"
            elif tool_type == 'explain':
                prompt = f"Explain this concept in simple terms for a student: {last_message}"
            elif tool_type == 'quiz':
                prompt = f"Create 3 multiple-choice quiz questions about: {last_message}"
            elif tool_type == 'examples':
                prompt = f"Provide 2-3 practical examples of: {last_message}"
            elif tool_type == 'key_points':
                prompt = f"Extract the key points from: {last_message}"
            else:
                prompt = last_message
            
            response = call_gemma(prompt)
        
        # Store in conversation history
        if last_message and response:
            conversation_history.append({
                'user': last_message,
                'ai': response
            })
            # Keep only last 10 conversations to prevent memory issues
            if len(conversation_history) > 10:
                conversation_history.pop(0)
    
    return render_template_string(
        HTML, 
        response=response, 
        last_message=last_message,
        active_tab=active_tab,
        conversation_history=conversation_history
    )

@app.route('/clear-history', methods=['POST'])
def clear_history():
    global conversation_history
    conversation_history = []
    return '', 204

@app.route('/favicon.ico')
def favicon():
    return '', 404

if __name__ == '__main__':
    print("🚀 Starting Enhanced Local AI Assistant...")
    print("📧 Open: http://localhost:5000")
    print("✨ Features: Chat, Study Tools, File Analysis, Conversation History")
    app.run(host='localhost', port=5000, debug=True)