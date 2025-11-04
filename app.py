from flask import Flask, render_template, abort, send_from_directory
import markdown
import os
from datetime import datetime
import re

app = Flask(__name__)

# Configuration
POSTS_DIR = 'posts'  # Directory containing your .md files
ASSETS_DIR = 'posts/assets'  # Directory containing images
app.config['POSTS_DIR'] = POSTS_DIR
app.config['ASSETS_DIR'] = ASSETS_DIR

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content"""
    frontmatter = {}
    if content.startswith('---'):
        try:
            _, fm, body = content.split('---', 2)
            for line in fm.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            return frontmatter, body.strip()
        except:
            pass
    return frontmatter, content

def get_posts():
    """Get all blog posts from the posts directory"""
    posts = []
    
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
        return posts
    
    for filename in os.listdir(POSTS_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(POSTS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, body = parse_frontmatter(content)
            
            # Extract title from frontmatter or first heading
            title = frontmatter.get('title', '')
            if not title:
                title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
                title = title_match.group(1) if title_match else filename[:-3]
            
            # Extract date
            date_str = frontmatter.get('date', '')
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                date = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # Create excerpt
            excerpt = frontmatter.get('excerpt', '')
            if not excerpt:
                excerpt = body[:200].replace('#', '').strip() + '...'
            
            slug = filename[:-3]
            
            posts.append({
                'slug': slug,
                'title': title,
                'date': date,
                'excerpt': excerpt,
                'filename': filename
            })
    
    # Sort by date, newest first
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def get_post(slug):
    """Get a single post by slug"""
    filename = f"{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter, body = parse_frontmatter(content)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(body, extensions=['fenced_code', 'codehilite', 'tables'])
    
    title = frontmatter.get('title', '')
    if not title:
        title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
        title = title_match.group(1) if title_match else slug
    
    date_str = frontmatter.get('date', '')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except:
        date = datetime.fromtimestamp(os.path.getmtime(filepath))
    
    return {
        'slug': slug,
        'title': title,
        'date': date,
        'content': html_content,
        'author': frontmatter.get('author', 'Anonymous')
    }

@app.route('/')
def index():
    posts = get_posts()
    return render_template('index.html', posts=posts)

@app.route('/post/<slug>')
def post(slug):
    post = get_post(slug)
    if not post:
        abort(404)
    return render_template('post.html', post=post)

@app.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve images from posts/assets directory"""
    return send_from_directory(ASSETS_DIR, filename)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)