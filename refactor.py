import re

with open('pip_desktop.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find js_ui in inject_custom_ui
# It starts at `    js_ui = """` and ends at `    """\n    window.evaluate_js(js_ui)`
js_ui_match = re.search(r'    js_ui = """(.*?)    """\n    window\.evaluate_js\(js_ui\)', content, re.DOTALL)
if not js_ui_match:
    print("Could not find js_ui in inject_custom_ui")
    exit(1)

js_ui_content = js_ui_match.group(1)

# Now we need to update the cookie domain logic in js_ui_content
js_ui_content = js_ui_content.replace(
    'document.cookie = pair.trim() + "; domain=.facebook.com; path=/; max-age=31536000";',
    'let domain = window.location.hostname.replace("www.", "");\n                    document.cookie = pair.trim() + "; domain=." + domain + "; path=/; max-age=31536000";'
)

# And remove the FB specific logic from js_ui_content, which is:
fb_specific_logic = """            // 1. Quét toàn bộ màn hình, tìm mọi icon (SVG) của Facebook và ẩn đi
            document.querySelectorAll('svg').forEach(svg => {
                if (!svg.closest('#pip-overlay-app')) {
                    let btn = svg.closest('div[role="button"]') || svg.closest('div[aria-label]');
                    if (btn) btn.style.display = 'none';
                    else svg.style.display = 'none';
                }
            });

            // 2. Ẩn chữ "Reels"
            document.querySelectorAll('span, h1, h2').forEach(el => {
                if (el.innerText && el.innerText.trim() === 'Reels') {
                    let p = el.closest('div[role="button"]') || el.parentElement;
                    if (p) p.style.display = 'none';
                }
            });"""

# Remove fb_specific_logic from js_ui_content
js_ui_content = js_ui_content.replace(fb_specific_logic, '')

# We define UNIVERSAL_OVERLAY_JS = """..."""
universal_overlay_js_def = 'UNIVERSAL_OVERLAY_JS = """' + js_ui_content + '    """\n\n'

# Now let's update inject_custom_ui
# We replace the whole `js_ui = """..."""\n    window.evaluate_js(js_ui)` with the fb_specific_logic as a new JS string
fb_js_replacement = '''    fb_js = """
        setInterval(() => {
''' + fb_specific_logic + '''
        }, 500);
    """
    window.evaluate_js(fb_js)'''

content = content[:js_ui_match.start()] + fb_js_replacement + content[js_ui_match.end():]

# Now for inject_youtube_ui, we just remove its js_ui definition
js_ui_yt_match = re.search(r'    js_ui = """(.*?)    """\n    window\.evaluate_js\(js_ui\)', content, re.DOTALL)
if js_ui_yt_match:
    content = content[:js_ui_yt_match.start()] + content[js_ui_yt_match.end():]
else:
    print("Could not find js_ui in inject_youtube_ui")

# Now add UNIVERSAL_OVERLAY_JS before def inject_custom_ui
content = content.replace('def inject_custom_ui(window):', universal_overlay_js_def + 'def inject_custom_ui(window):')

# Now let's update apply_saved_cookie
apply_saved_cookie_old = """                    var cookieStr = `{c}`;
                    cookieStr.split(';').forEach(pair => {{
                        document.cookie = pair.trim() + "; domain=.facebook.com; path=/; max-age=31536000";
                    }});"""
apply_saved_cookie_new = """                    var cookieStr = `{c}`;
                    var d = window.location.hostname.replace('www.', '');
                    cookieStr.split(';').forEach(pair => {{
                        document.cookie = pair.trim() + "; domain=." + d + "; path=/; max-age=31536000";
                    }});"""
content = content.replace(apply_saved_cookie_old, apply_saved_cookie_new)

# Now update on_loaded
on_loaded_old = """    if 'facebook.com' in current_url:
        print("Injecting Facebook UI...")
        apply_saved_cookie(window, api)
        inject_custom_ui(window)
    elif 'youtube.com' in current_url:
        print("Loaded YouTube")
        if '/shorts/' in current_url:
            print("Injecting YouTube Shorts UI...")
            inject_youtube_ui(window)
    elif 'tiktok.com' in current_url:
        print("Loaded TikTok")
    elif 'netflix.com' in current_url:
        print("Loaded Netflix")
        
    if not current_url.startswith('data:'):
        window.evaluate_js(TITLEBAR_JS)"""

on_loaded_new = """    if not current_url.startswith('data:'):
        apply_saved_cookie(window, api)

    if 'facebook.com' in current_url:
        print("Injecting Facebook UI...")
        inject_custom_ui(window)
    elif 'youtube.com' in current_url:
        print("Loaded YouTube")
        if '/shorts/' in current_url:
            print("Injecting YouTube Shorts UI...")
            inject_youtube_ui(window)
    elif 'tiktok.com' in current_url:
        print("Loaded TikTok")
    elif 'netflix.com' in current_url:
        print("Loaded Netflix")
        
    if not current_url.startswith('data:'):
        window.evaluate_js(UNIVERSAL_OVERLAY_JS)
        window.evaluate_js(TITLEBAR_JS)"""
content = content.replace(on_loaded_old, on_loaded_new)

with open('pip_desktop.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactoring complete.")
