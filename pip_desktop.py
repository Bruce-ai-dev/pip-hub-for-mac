import os
import json
import webview
import base64
import time
import pynput
from pathlib import Path

class PipApi:
    def _get_path(self, filename):
        dir_path = Path.home() / '.pip_hub'
        dir_path.mkdir(exist_ok=True)
        return str(dir_path / filename)

    def __init__(self):
        self.window = None
        self.config = {'hotkey': 'Tab', 'theme': 'dark', 'transparent_borders': False, 'boss_mode': 'minimize'}
        config_path = self._get_path('config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config.update(json.load(f))
            except: pass
        self.hotkey = self.config.get('hotkey', 'Tab')
        self.saved_bounds = None
        self.last_boss_trigger = 0
        
        # Apply fake icon on startup
        import threading
        def apply_fake_icon():
            import time; time.sleep(1) # wait for app to fully start
            self.set_fake_icon(self.config.get('fake_icon', 'off'))
        threading.Thread(target=apply_fake_icon, daemon=True).start()
        with open(self._get_path('pip_hub.log'), 'a') as f:
            f.write("[Pip Hub] App Started! Config loaded.\n")
        try:
            self.listener = pynput.keyboard.Listener(on_press=self.on_global_key_press)
            self.listener.start()
            with open(self._get_path('pip_hub.log'), 'a') as f:
                f.write("[Pip Hub] Pynput Listener Started Successfully!\n")
        except Exception as e:
            with open(self._get_path('pip_hub.log'), 'a') as f:
                f.write(f"[Pip Hub] Failed to start Pynput Listener: {e}\n")

    def on_global_key_press(self, key):
        if not self.window: return
        try:
            k = None
            if hasattr(key, 'char') and key.char:
                k = key.char.upper()
            elif hasattr(key, 'name') and key.name:
                name = key.name.upper()
                if name == 'SPACE': k = 'Space'
                elif name == 'ESC': k = 'Escape'
                else: k = key.name.capitalize()
            # Debugging log
            with open(self._get_path('pip_hub.log'), 'a') as f:
                f.write(f"[Pip Hub] Key pressed: {k} (Raw: {key}) - Configured Hotkey: {self.hotkey}\n")
            
            if k and k.upper() == self.hotkey.upper():
                now = time.time()
                if now - self.last_boss_trigger > 0.3:
                    self.last_boss_trigger = now
                    with open(self._get_path('pip_hub.log'), 'a') as f:
                        f.write("[Pip Hub] Hotkey matched! Triggering JS...\n")
                    import threading
                    threading.Thread(target=self.window.evaluate_js, args=('if (window.triggerBossKey) { window.triggerBossKey(); } else { pywebview.api.log("triggerBossKey NOT FOUND in window!"); }',), daemon=True).start()
        except Exception as e:
            with open(self._get_path('pip_hub.log'), 'a') as f:
                f.write(f"[Pip Hub] Error in hotkey: {e}\n")

    def _save_config(self):
        with open(self._get_path('config.json'), 'w') as f:
            json.dump(self.config, f)

    def get_hotkey(self):
        return self.hotkey

    def set_hotkey(self, key):
        self.hotkey = key
        self.config['hotkey'] = key
        self._save_config()
        return True

    def get_theme(self):
        return self.config.get('theme', 'dark')

    def set_theme(self, theme):
        self.config['theme'] = theme
        self._save_config()
        return True

    def get_transparent_borders(self):
        return self.config.get('transparent_borders', False)

    def set_transparent_borders(self, val):
        self.config['transparent_borders'] = val
        self._save_config()
        return True

    def get_boss_mode(self):
        return self.config.get('boss_mode', 'minimize')

    def set_boss_mode(self, mode):
        with open(self._get_path('pip_hub.log'), 'a') as f:
            f.write(f"[Pip Hub] Python set_boss_mode called with: {mode}\n")
        self.config['boss_mode'] = mode
        self._save_config()
        return True

    def get_transform_image(self, shape):
        if shape.startswith('custom_'):
            custom_icons = self.get_custom_icons()
            if shape in custom_icons:
                import base64
                path = os.path.join(self._get_path('custom-icons'), custom_icons[shape]['filename'])
                if os.path.exists(path):
                    try:
                        with open(path, 'rb') as f:
                            return base64.b64encode(f.read()).decode('utf-8')
                    except:
                        pass
        files = {
            'fly': 'conruoi.png',
            'star': 'star.png',
            'smile': 'smile.webp',
            'dot': 'chamden.png'
        }
        return get_base64_image(files.get(shape, 'conruoi.png'))


    def get_custom_icons(self):
        try:
            with open(self._get_path('custom_icons.json'), 'r') as f:
                return json.load(f)
        except:
            return {}

    def add_custom_icon(self, name, b64_data):
        import uuid
        import base64
        icons = self.get_custom_icons()
        icon_id = 'custom_' + str(uuid.uuid4().hex)[:8]
        filename = f"{icon_id}.png"
        
        custom_dir = self._get_path('custom-icons')
        if not os.path.exists(custom_dir):
            os.makedirs(custom_dir)
            
        filepath = os.path.join(custom_dir, filename)
        try:
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(b64_data))
            
            icons[icon_id] = {'name': name, 'filename': filename}
            with open(self._get_path('custom_icons.json'), 'w') as f:
                json.dump(icons, f)
            return True
        except Exception as e:
            self.log(f"Error saving custom icon: {e}")
            return False

    def delete_custom_icon(self, icon_id):
        icons = self.get_custom_icons()
        if icon_id in icons:
            filename = icons[icon_id]['filename']
            filepath = os.path.join(self._get_path('custom-icons'), filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            del icons[icon_id]
            with open(self._get_path('custom_icons.json'), 'w') as f:
                json.dump(icons, f)
        return True

    def get_fake_icon(self):
        return self.config.get('fake_icon', 'off')

    def _apply_icon(self, choice):
        try:
            import Cocoa
            import sys
            import random
            
            icon_files = {
                'canva': 'canva.webp',
                'excel': 'excel.svg.png',
                'mail': 'mail.webp',
                'note': 'note.png',
                'powerpoint': 'powerpoint.svg.png',
                'word': 'word.svg.png',
                'zalo': 'Zalo.webp'
            }
            
            if choice == 'random':
                choice = random.choice(list(icon_files.keys()))
                
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
            if choice == 'off':
                Cocoa.NSApplication.sharedApplication().performSelectorOnMainThread_withObject_waitUntilDone_(b'setApplicationIconImage:', None, False)
                return True
            elif choice.startswith('custom_'):
                custom_icons = self.get_custom_icons()
                if choice in custom_icons:
                    icon_path = os.path.join(self._get_path('custom-icons'), custom_icons[choice]['filename'])
                else:
                    return False
            else:
                filename = icon_files.get(choice)
                if not filename: return False
                icon_path = os.path.join(base_dir, 'icon-fake', filename)
                
            if os.path.exists(icon_path):
                img = Cocoa.NSImage.alloc().initWithContentsOfFile_(icon_path)
                if img:
                    Cocoa.NSApplication.sharedApplication().performSelectorOnMainThread_withObject_waitUntilDone_(b'setApplicationIconImage:', img, False)
        except Exception as e:
            with open(self._get_path('pip_hub.log'), 'a') as f:
                f.write(f"[Pip Hub] Fake icon error: {e}\n")
        return True

    def set_fake_icon(self, choice):
        self.config['fake_icon'] = choice
        self._save_config()
        return self._apply_icon(choice)

    def apply_temp_fake_icon(self, choice):
        return self._apply_icon(choice)

    def restore_fake_icon(self):
        return self._apply_icon(self.config.get('fake_icon', 'off'))

    def hide_as_arrow(self, screen_width):
        if self.window:
            self.saved_bounds = (self.window.x, self.window.y, self.window.width, self.window.height)
            self.window.move(int(-self.window.width + 25), self.window.y)
        return True

    def restore_from_arrow(self):
        if self.window and self.saved_bounds:
            self.window.move(self.saved_bounds[0], self.saved_bounds[1])
            self.saved_bounds = None
        return True
        
    def log(self, msg):
        with open(self._get_path('pip_hub.log'), 'a') as f:
            f.write(f"[JS] {msg}\n")
        return True

    def get_overlay_config(self):
        return self.config.get('overlay', {
            'opacity': 100,
            'muted': False,
            'ui_hidden': False,
            'fit': 'cover',
            'pinned': True
        })

    def save_overlay_config(self, key, value):
        if 'overlay' not in self.config:
            self.config['overlay'] = {}
        self.config['overlay'][key] = value
        self._save_config()
        return True

    def minimize_window(self):
        if self.window:
            self.window.minimize()
        return True

    def hide_window(self):
        if self.window:
            self.window.hide()
        return True
        
    def show_window(self):
        if self.window:
            self.window.show()
        return True

    def close(self):
        import os
        os._exit(0)

    def navigate_to(self, url):
        if 'netflix.com' in url:
            try:
                self.window.resize(800, 600)
            except:
                pass
        self.window.load_url(url)

    def toggle_pin(self, is_pinned):
        self.window.on_top = is_pinned

    def save_note(self, text):
        self.config['note_text'] = text
        self._save_config()
        return True

    def get_note(self):
        return self.config.get('note_text', '')

    def resize_note_window(self):
        try:
            if self.window:
                self.config['prev_width'] = self.window.width
                self.config['prev_height'] = self.window.height
                self.window.resize(400, 400)
        except:
            pass

    def restore_window_size(self):
        try:
            if self.window and 'prev_width' in self.config and 'prev_height' in self.config:
                self.window.resize(self.config['prev_width'], self.config['prev_height'])
        except:
            pass

        
    def nav_dashboard(self):
        global html_content
        try:
            self.window.on_top = False
        except:
            pass
        try:
            self.window.resize(480, 720)
        except:
            pass
        try:
            self.window.load_html(html_content)
        except Exception as e:
            print("load_html error:", e)
        return True

    def save_cookie(self, cookie_str):
        with open(self._get_path('cookie.txt'), 'w') as f:
            f.write(cookie_str)
        # Báo hiệu JS reload lại trang sau khi cập nhật file
        return True

    def has_saved_cookie(self):
        cookie_path = self._get_path('cookie.txt')
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r') as f:
                    if f.read().strip():
                        return True
            except: pass
        return False

    def check_accessibility(self):
        try:
            import ctypes
            app_services = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
            app_services.AXIsProcessTrusted.restype = ctypes.c_bool
            return app_services.AXIsProcessTrusted()
        except Exception as e:
            print("Error checking accessibility:", e)
        return True

    def open_accessibility_settings(self):
        import os
        os.system("open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'")
        return True

    def clear_webview_cookies(self):
        try:
            self.window.clear_cookies()
        except Exception as e:
            print("Error clearing webview cookies:", e)
        return True

    def clear_cookie_file(self):
        try:
            os.remove(self._get_path('cookie.txt'))
        except:
            pass
        return True

    def _read_bookmarks(self):
        bms = []
        bp = self._get_path('bookmarks.json')
        if os.path.exists(bp):
            try:
                with open(bp, 'r') as f:
                    bms = json.load(f)
            except: pass
        return bms

    def bookmark(self, url, title="", platform="", timestamp=0):
        if not url: return "No URL"
        bookmarks = self._read_bookmarks()
        existing = next((b for b in bookmarks if b.get("url") == url), None)
        if existing:
            existing['title'] = title
            existing['platform'] = platform
            existing['timestamp'] = timestamp
        else:
            bookmarks.append({'title': title, 'url': url, 'platform': platform, 'timestamp': timestamp})
        with open(self._get_path('bookmarks.json'), 'w') as f:
            json.dump(bookmarks, f, indent=4)
        return "Saved"


    def get_bookmarks(self):
        return self._read_bookmarks()

    def delete_bookmarks(self, urls):
        bookmarks = self._read_bookmarks()
        bookmarks = [b for b in bookmarks if b.get("url") not in urls]
        with open(self._get_path('bookmarks.json'), 'w') as f:
            json.dump(bookmarks, f, indent=4)
        return True

TITLEBAR_JS = """
if (!document.getElementById('pip-custom-titlebar') && !document.querySelector('.dash-titlebar')) {
    let style = document.createElement('style');
    style.textContent = `
        #pip-custom-titlebar {
            position: fixed; top: 0; left: 0; right: 0; height: 32px; z-index: 2147483647;
            display: flex; align-items: center; padding-left: 12px; gap: 8px;
            opacity: 0; transition: opacity 0.2s;
            background: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent);
            pointer-events: auto; -webkit-app-region: drag;
        }
        #pip-custom-titlebar:hover {
            opacity: 1;
        }
        .pip-mac-btn {
            width: 12px; height: 12px; border-radius: 50%; cursor: pointer; transition: transform 0.1s;
            border: 6px solid transparent; background-clip: padding-box; box-sizing: content-box;
            margin: -6px; /* Offset the border to keep gap same */ -webkit-app-region: no-drag;
        }
        .pip-mac-btn:active { transform: scale(0.85); }
    `;
    document.head.appendChild(style);

    let customTitleBar = document.createElement('div');
    customTitleBar.id = 'pip-custom-titlebar';
    customTitleBar.className = 'pywebview-drag-region';
    
    let closeBtn = document.createElement('div');
    closeBtn.className = 'pip-mac-btn';
    closeBtn.style.backgroundColor = '#ff5f56';
    closeBtn.onclick = () => { try { pywebview.api.nav_dashboard(); } catch(e){} };
    
    let minBtn = document.createElement('div');
    minBtn.className = 'pip-mac-btn';
    minBtn.style.backgroundColor = '#ffbd2e';
    minBtn.onclick = () => { try { pywebview.api.minimize_window(); } catch(e){} };
    
    let maxBtn = document.createElement('div');
    maxBtn.className = 'pip-mac-btn';
    maxBtn.style.backgroundColor = '#27c93f';
    
    customTitleBar.appendChild(closeBtn);
    customTitleBar.appendChild(minBtn);
    customTitleBar.appendChild(maxBtn);

    document.body.appendChild(customTitleBar);
}
"""

UNIVERSAL_OVERLAY_JS = """
    if (!document.getElementById('pip-overlay-app') && !document.querySelector('.dash-titlebar')) {
        let overlay = document.createElement('div');
        overlay.id = 'pip-overlay-app';
        // Xoá pointer-events: none đi để không bị lỗi trên WebKit Mac, thay vào đó thu gọn wrapper vào chính giữa
        overlay.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 2147483647; display: flex; flex-direction: column; gap: 10px; align-items: center; font-family: sans-serif; opacity: 0.95; transition: opacity 0.3s; width: 90%; max-width: 380px;';
        
        let hideTimeout;
        function showOverlay() {
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
            clearTimeout(hideTimeout);
            hideTimeout = setTimeout(() => {
                overlay.style.opacity = '0';
                overlay.style.pointerEvents = 'none';
            }, 2500);
        }
        document.addEventListener('mousemove', showOverlay);
        document.addEventListener('click', showOverlay);
        overlay.addEventListener('mouseenter', () => {
            clearTimeout(hideTimeout);
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
        });
        overlay.addEventListener('mouseleave', showOverlay);
        showOverlay(); 

        overlay.innerHTML = `
            <style>
                #pip-overlay-app {
                    --bg: rgba(30, 30, 46, 0.85);
                    --text: #cdd6f4;
                    --btn-ic: #bac2de;
                    --sep: #45475a;
                    --input-bg: #1e1e2e;
                    --input-border: #313244;
                }
                #pip-overlay-app.theme-light {
                    --bg: rgba(255, 255, 255, 0.95);
                    --text: #1e1e2e;
                    --btn-ic: #4c4f69;
                    --sep: #dce0e8;
                    --input-bg: #f4f5f8;
                    --input-border: #ccd0da;
                }
                #pip-overlay-app * { box-sizing: border-box; }
                .pip-btn { display: flex; align-items: center; justify-content: center; cursor: pointer; border: none; flex-shrink: 0; transition: transform 0.1s; }
                .pip-btn:active { transform: scale(0.9); }
                .dock-panel {
                    display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-evenly; align-items: center;
                    background: var(--bg); padding: 8px 10px; border-radius: 20px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.3); backdrop-filter: blur(5px); width: 100%; transition: background 0.3s;
                }
                .btn-lg { width: 36px; height: 36px; border-radius: 50%; background: #f38ba8; color: white; font-size: 14px; }
                .btn-md { width: 30px; height: 30px; border-radius: 50%; background: var(--sep); color: white; font-size: 12px; }
                .btn-ic { background: none; color: var(--btn-ic); font-size: 16px; padding: 4px; }
                .separator { width: 1px; height: 16px; background: var(--sep); transition: background 0.3s; }
                .url-container { display: flex; gap: 5px; width: 100%; background: var(--bg); padding: 5px; border-radius: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); backdrop-filter: blur(5px); transition: background 0.3s; }
                #url-input { flex:1; min-width: 0; border-radius: 12px; padding: 6px 12px; border: 1px solid var(--input-border); background: var(--input-bg); color: var(--text); font-size: 12px; outline:none; transition: all 0.3s; }
                
                .pip-fixed-video {
                    position: fixed !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    z-index: 9999 !important;
                    object-fit: cover !important;
                    object-position: center !important;
                    background-color: #000 !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    border-radius: 0 !important;
                }
                .tab-bar { display: flex; gap: 5px; margin-bottom: 10px; border-bottom: 1px solid #45475a; padding-bottom: 5px; }
                .tab-btn { background: none; border: none; color: #bac2de; font-size: 11px; cursor: pointer; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
                .tab-btn.active { background: #f38ba8; color: #11111b; }
                .tab-content { display: none; flex-direction: column; gap: 10px; }
                .tab-content.active { display: flex; }
                .setup-row { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #cdd6f4; font-weight: 600; }
                .slider { -webkit-appearance: none; width: 100px; height: 4px; border-radius: 2px; background: #45475a; outline: none; }
                .slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 12px; height: 12px; border-radius: 50%; background: #f38ba8; cursor: pointer; }
                
                /* Thu nhỏ kích thước tự động nếu màn hình bị bóp quá hẹp */
                @media (max-width: 340px) {
                    .dock-panel { gap: 4px; padding: 6px 5px; }
                    .btn-lg { width: 30px; height: 30px; font-size: 12px; }
                    .btn-md { width: 26px; height: 26px; font-size: 10px; }
                    .btn-ic { font-size: 14px; }
                }
                
                /* Kích hoạt chế độ Ultra-Mini Player khi bóp siêu hẹp */
                @media (max-width: 280px) {
                    .hide-on-mini { display: none !important; }
                    .dock-panel { flex-wrap: nowrap; justify-content: space-evenly; }
                    .btn-lg { width: 28px; height: 28px; font-size: 10px; }
                    .btn-md { width: 24px; height: 24px; font-size: 9px; }
                    .btn-ic { font-size: 12px; }
                }
            </style>
            
            <!-- Settings Modal (Tabs) -->
            <div id="cookie-prompt-div" style="display: none; flex-direction: column; background: rgba(30, 30, 46, 0.95); padding: 15px; border-radius: 12px; width: 280px; box-shadow: 0 4px 20px rgba(0,0,0,0.8); position: absolute; top: 80px; left: 50%; transform: translateX(-50%); z-index: 10000; border: 1px solid rgba(255,255,255,0.1);">
                <div class="tab-bar">
                    <button class="tab-btn active" id="tab-btn-cookie">Cookie</button>
                    <button class="tab-btn" id="tab-btn-setup">Setup Nhanh</button>
                </div>
                
                <div id="tab-cookie" class="tab-content active">
                    <div style="font-size: 11px; color: #bac2de; margin-bottom: 5px;">Dán toàn bộ Cookie Facebook vào đây:</div>
                    <textarea id="cookie-input" rows="3" style="border-radius: 8px; padding: 8px; background: rgba(0,0,0,0.3); color: #cdd6f4; border: 1px solid #45475a; font-size: 11px; outline: none; resize: none;"></textarea>
                    <div style="display: flex; gap: 5px; justify-content: flex-end; margin-top: 5px;">
                        <button id="btn-cancel-cookie" style="background: #45475a; color: white; border: none; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 11px;" data-i18n="cancel">Hủy</button>
                        <button id="btn-save-cookie" style="background: #f38ba8; color: #11111b; border: none; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-weight: bold; font-size: 11px;">Lưu</button>
                    </div>
                </div>

                <div id="tab-setup" class="tab-content">
                    <div class="setup-row">
                        <span>Độ mờ nền (Opacity)</span>
                        <input type="range" id="opacity-slider" class="slider" min="10" max="100" value="100">
                    </div>
                    <div class="setup-row">
                        <span>Tự động phát (Playback)</span>
                        <button id="setup-btn-playback" style="background: #a6e3a1; border:none; color: #11111b; font-size: 10px; font-weight:bold; padding: 4px 8px; border-radius: 6px; cursor: pointer;">Đang Bật</button>
                    </div>
                    <div class="setup-row">
                        <span>Giao diện Playback</span>
                        <button id="setup-btn-ui" style="background: #a6e3a1; border:none; color: #11111b; font-size: 10px; font-weight:bold; padding: 4px 8px; border-radius: 6px; cursor: pointer;">Đang Hiện</button>
                    </div>
                    <div class="setup-row">
                        <span>Âm lượng (Volume)</span>
                        <button id="setup-btn-volume" style="background: #f9e2af; border:none; color: #11111b; font-size: 10px; font-weight:bold; padding: 4px 8px; border-radius: 6px; cursor: pointer;">Đang Bật</button>
                    </div>
                </div>
            </div>

            <!-- URL Bar -->
            <div class="url-container">
                <input type="text" id="url-input" placeholder="Dán link Facebook Reel...">
                <button id="btn-go" class="pip-btn" style="border-radius: 12px; padding: 0 15px; background: #f38ba8; color: white; font-weight:bold; font-size: 12px;">Go</button>
            </div>

            <!-- Floating Controls Dock -->
            <div class="dock-panel">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <button id="btn-rotate" class="pip-btn btn-ic" title="Xoay Video">🔄</button>
                    <div class="separator hide-on-mini" style="margin-right: 2px;"></div>
                    <button id="btn-theme" class="pip-btn btn-ic hide-on-mini" title="Sáng/Tối">☀️</button>
                    <button id="btn-fit" class="pip-btn btn-ic hide-on-mini" title="Thu phóng Video (Fit/Cover)">🔲</button>
                    <button id="btn-cookie-toggle" class="pip-btn btn-ic hide-on-mini" title="Cài đặt Cookie">⚙️</button>
                    <button id="btn-pin" class="pip-btn btn-ic" title="Ghim cửa sổ">📌</button>
                    <div class="separator hide-on-mini"></div>
                    <button id="btn-bookmark" class="pip-btn btn-ic" style="color:#f9e2af;" title="Lưu video">⭐</button>
                </div>
                <div id="playback-controls-group" style="display: flex; gap: 8px; align-items: center;">
                    <button id="btn-prev" class="pip-btn btn-md hide-on-mini" title="Video trước">⏮</button>
                    <button id="btn-play-pause" class="pip-btn btn-lg" title="Play/Pause">⏸</button>
                    <button id="btn-next" class="pip-btn btn-md hide-on-mini" title="Video tiếp">⏭</button>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div class="hide-on-mini" style="width: 1px; height: 16px; background: #45475a;"></div>
                    <button id="btn-mute" class="pip-btn btn-md" title="Bật/Tắt âm thanh">🔊</button>
                    <button id="btn-hide-dock" class="pip-btn btn-md" title="Ẩn thanh công cụ (Nháy đúp chuột vào màn hình để hiện lại)">⬇️</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        let showDockBtn = document.createElement('div');
        showDockBtn.id = 'pip-show-dock-btn';
        showDockBtn.innerHTML = '🔽';
        showDockBtn.style.cssText = 'position: fixed; top: 0px; left: 50%; transform: translateX(-50%); z-index: 2147483647; background: rgba(30, 30, 46, 0.7); color: #cdd6f4; padding: 2px 15px; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; cursor: pointer; display: none; font-size: 14px; transition: background 0.3s; box-shadow: 0 2px 5px rgba(0,0,0,0.5); font-family: sans-serif; opacity: 0.8;';
        showDockBtn.addEventListener('mouseenter', () => showDockBtn.style.background = 'rgba(243, 139, 168, 0.9)');
        showDockBtn.addEventListener('mouseleave', () => showDockBtn.style.background = 'rgba(30, 30, 46, 0.7)');
        document.body.appendChild(showDockBtn);


        document.getElementById('url-input').value = window.location.href;
        window.pipIsPinned = false;
        window.pipIsMuted = false;

        // Hàm tìm video đang hiển thị chính giữa màn hình
        function getActiveVideo() {
            let active = null;
            document.querySelectorAll('video').forEach(v => {
                if (!v.paused) active = v;
            });
            if (active) return active;

            let fixedVideo = document.querySelector('video.pip-fixed-video');
            if (fixedVideo) return fixedVideo;

            let maxVisible = 0;
            document.querySelectorAll('video').forEach(v => {
                let rect = v.getBoundingClientRect();
                let visibleHeight = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
                if (visibleHeight > maxVisible) {
                    maxVisible = visibleHeight;
                    active = v;
                }
            });
            return active;
        }

        if (window.location.hostname.includes('netflix.com')) {
            let style = document.createElement('style');
            style.innerHTML = `
                body, .mainView {
                    background-color: #141414 !important;
                }
                .slider-item {
                    min-width: 160px !important;
                    height: auto !important;
                }
                .title-card {
                    min-width: 150px !important;
                }
                .lolomoRow {
                    min-height: 180px !important;
                    margin-bottom: 20px !important;
                }
                .rowContainer, .sliderContent {
                    height: auto !important;
                    min-height: 130px !important;
                }
            `;
            document.head.appendChild(style);
        }

        // Hàm ép video duy nhất hiển thị full màn hình, che lấp mọi thứ
        function updateFixedVideo() {
            let activeV = getActiveVideo();
            let isFullPagePlayer = window.location.hostname.includes('netflix.com') || (window.location.hostname.includes('youtube.com') && window.location.pathname.includes('/watch'));
            
            document.querySelectorAll('video').forEach(v => {
                if (v === activeV) {
                    if (!isFullPagePlayer) {
                        v.classList.add('pip-fixed-video');
                        if (!v.dataset.pipTop) v.dataset.pipTop = 0;
                        if (!v.dataset.pipLeft) v.dataset.pipLeft = 0;
                        v.style.setProperty('top', v.dataset.pipTop + 'px', 'important');
                        v.style.setProperty('left', v.dataset.pipLeft + 'px', 'important');
                        
                        let rect = v.getBoundingClientRect();
                        if (Math.abs(rect.top) > 1 || Math.abs(rect.left) > 1) {
                            v.dataset.pipTop = parseFloat(v.dataset.pipTop) - rect.top;
                            v.dataset.pipLeft = parseFloat(v.dataset.pipLeft) - rect.left;
                            v.style.setProperty('top', v.dataset.pipTop + 'px', 'important');
                            v.style.setProperty('left', v.dataset.pipLeft + 'px', 'important');
                        }
                        
                        let transformStr = window.pipRotation ? `rotate(${window.pipRotation}deg)` : 'none';
                        v.style.setProperty('transform', transformStr, 'important');
                        v.style.setProperty('object-fit', window.pipObjectFit, 'important');
                    } else {
                        // Xoá các thuộc tính bị ép để trả lại giao diện gốc cho Netflix / YouTube
                        v.classList.remove('pip-fixed-video');
                        v.style.removeProperty('top');
                        v.style.removeProperty('left');
                        delete v.dataset.pipTop;
                        delete v.dataset.pipLeft;
                    }
                } else if (v.classList.contains('pip-fixed-video')) {
                    v.classList.remove('pip-fixed-video');
                    v.style.removeProperty('top');
                    v.style.removeProperty('left');
                    v.style.removeProperty('transform');
                    delete v.dataset.pipTop;
                    delete v.dataset.pipLeft;
                }
            });
        }

        function loopFixedVideo() {
            updateFixedVideo();
            requestAnimationFrame(loopFixedVideo);
        }
        loopFixedVideo();

        // BIND EVENTS (Để tránh bị Content-Security-Policy của Facebook block inline onclick)
        document.getElementById('btn-cancel-cookie').addEventListener('click', () => {
            document.getElementById('cookie-prompt-div').style.display = 'none';
        });

        document.getElementById('btn-save-cookie').addEventListener('click', () => {
            let c = document.getElementById('cookie-input').value.trim();
            if (c) {
                c.split(';').forEach(pair => {
                    let domain = window.location.hostname.replace("www.", "");
                    document.cookie = pair.trim() + "; domain=." + domain + "; path=/; max-age=31536000";
                });
                pywebview.api.save_cookie(c).then(() => window.location.reload());
            }
        });

        document.getElementById('btn-cookie-toggle').addEventListener('click', () => {
            let div = document.getElementById('cookie-prompt-div');
            if(div.style.display === 'none') { div.style.display = 'flex'; }
            else { div.style.display = 'none'; }
        });

        if (window.location.hash === '#show_cookie') {
            setTimeout(() => {
                let div = document.getElementById('cookie-prompt-div');
                if (div) div.style.display = 'flex';
            }, 1000);
        }

        document.getElementById('tab-btn-cookie').addEventListener('click', (e) => {
            e.target.classList.add('active');
            document.getElementById('tab-btn-setup').classList.remove('active');
            document.getElementById('tab-cookie').classList.add('active');
            document.getElementById('tab-setup').classList.remove('active');
        });
        document.getElementById('tab-btn-setup').addEventListener('click', (e) => {
            e.target.classList.add('active');
            document.getElementById('tab-btn-cookie').classList.remove('active');
            document.getElementById('tab-setup').classList.add('active');
            document.getElementById('tab-cookie').classList.remove('active');
        });

        function initOverlayConfig() {
            pywebview.api.get_overlay_config().then(cfg => {
                document.documentElement.style.opacity = cfg.opacity / 100;
                let slider = document.getElementById('opacity-slider');
                if (slider) slider.value = cfg.opacity;
                window.pipIsMuted = cfg.muted;
                let setupMute = document.getElementById('setup-btn-volume');
                if (setupMute) { setupMute.innerText = cfg.muted ? 'Đang Tắt' : 'Đang Bật'; setupMute.style.background = cfg.muted ? '#f38ba8' : '#f9e2af'; }
                let dockMute = document.getElementById('btn-mute');
                if (dockMute) { dockMute.style.color = cfg.muted ? '#f38ba8' : '#bac2de'; dockMute.innerText = cfg.muted ? '🔇' : '🔊'; }
                let group = document.getElementById('playback-controls-group');
                let btnUi = document.getElementById('setup-btn-ui');
                if (cfg.ui_hidden) {
                    if(group) group.style.display = 'none';
                    if(btnUi) { btnUi.innerText = 'Đang Ẩn'; btnUi.style.background = '#f38ba8'; }
                } else {
                    if(group) group.style.display = 'flex';
                    if(btnUi) { btnUi.innerText = 'Đang Hiện'; btnUi.style.background = '#a6e3a1'; }
                }
                window.pipObjectFit = cfg.fit || 'cover';
                let btnFit = document.getElementById('btn-fit');
                if (btnFit) { btnFit.style.color = window.pipObjectFit === 'contain' ? '#f38ba8' : '#bac2de'; }
                window.pipIsPinned = cfg.pinned !== undefined ? cfg.pinned : true;
                pywebview.api.toggle_pin(window.pipIsPinned);
                let btnPin = document.getElementById('btn-pin');
                if (btnPin) { btnPin.style.color = window.pipIsPinned ? '#f38ba8' : '#bac2de'; btnPin.style.backgroundColor = window.pipIsPinned ? 'rgba(255, 77, 77, 0.2)' : 'transparent'; btnPin.style.borderRadius = '5px'; }
            });
            pywebview.api.get_transparent_borders().then(isTransparent => {
                if (isTransparent) {
                    let style = document.createElement('style');
                    style.innerHTML = 'body, html { background-color: transparent !important; } video { background-color: transparent !important; }';
                    document.head.appendChild(style);
                }
            });
            pywebview.api.get_boss_mode().then(m => window.pipBossMode = m || 'minimize');
        }
        initOverlayConfig();

        document.getElementById('opacity-slider').addEventListener('input', (e) => {
            document.documentElement.style.opacity = e.target.value / 100;
            pywebview.api.save_overlay_config('opacity', parseInt(e.target.value));
        });

        document.getElementById('setup-btn-playback').addEventListener('click', (e) => {
            let v = getActiveVideo();
            if(v) {
                if(v.paused) {
                    let p = v.play();
                    if(p && p.catch) p.catch(()=>{v.click();});
                    e.target.innerText = 'Đang Bật';
                    e.target.style.background = '#a6e3a1';
                } else {
                    v.pause();
                    e.target.innerText = 'Đang Tắt';
                    e.target.style.background = '#f38ba8';
                }
            }
        });
        
        document.getElementById('setup-btn-volume').addEventListener('click', (e) => {
            let v = getActiveVideo();
            if(v) {
                v.muted = !v.muted;
                window.pipIsMuted = v.muted;
                if(!v.muted) {
                    e.target.innerText = 'Đang Bật';
                    e.target.style.background = '#f9e2af';
                } else {
                    e.target.innerText = 'Đang Tắt';
                    e.target.style.background = '#f38ba8';
                }
                pywebview.api.save_overlay_config('muted', window.pipIsMuted);
                
                let dockMute = document.getElementById('btn-mute');
                if (dockMute) {
                    dockMute.style.color = v.muted ? '#f38ba8' : '#bac2de';
                    dockMute.innerText = v.muted ? '🔇' : '🔊';
                }
            }
        });

        document.getElementById('setup-btn-ui').addEventListener('click', (e) => {
            let group = document.getElementById('playback-controls-group');
            if (group.style.display !== 'none') {
                group.style.display = 'none';
                e.target.innerText = 'Đang Ẩn';
                e.target.style.background = '#f38ba8';
                pywebview.api.save_overlay_config('ui_hidden', true);
            } else {
                group.style.display = 'flex';
                e.target.innerText = 'Đang Hiện';
                e.target.style.background = '#a6e3a1';
                pywebview.api.save_overlay_config('ui_hidden', false);
            }
        });

        let hideDockBtn = document.getElementById('btn-hide-dock');
        if (hideDockBtn) {
            hideDockBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                let app = document.getElementById('pip-overlay-app');
                if (app) app.style.display = 'none';
                let showBtn = document.getElementById('pip-show-dock-btn');
                if (showBtn) showBtn.style.display = 'block';
            });
        }
        
        let showBtn = document.getElementById('pip-show-dock-btn');
        if (showBtn) {
            showBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showBtn.style.display = 'none';
                let app = document.getElementById('pip-overlay-app');
                if (app) {
                    app.style.display = 'flex';
                    showOverlay();
                }
            });
        }
        
        document.addEventListener('dblclick', (e) => {
            let app = document.getElementById('pip-overlay-app');
            if (app && app.style.display === 'none') {
                app.style.display = 'flex';
                showOverlay();
                let sb = document.getElementById('pip-show-dock-btn');
                if (sb) sb.style.display = 'none';
            }
        });

        window.pipBossHidden = false;
        window.pipBossMode = 'minimize';
        
        window.pipBossKeyString = '`';
        try {
            pywebview.api.get_hotkey().then(k => {
                if (k) window.pipBossKeyString = k.toLowerCase();
            });
        } catch(e) {}
        
        window.addEventListener('keydown', (e) => {
            if (!window.pipBossKeyString) return;
            let key = e.key ? e.key.toLowerCase() : '';
            let code = e.code ? e.code.toLowerCase() : '';
            
            // Map standard keys
            if (key === ' ') key = 'space';
            if (key === 'escape') key = 'esc';
            
            // Check match (e.key or e.code for dead keys like backquote on VN keyboard)
            let match = false;
            if (key === window.pipBossKeyString) match = true;
            if (window.pipBossKeyString === '`' && code === 'backquote') match = true;
            if (window.pipBossKeyString === 'tab' && code === 'tab') match = true;
            if (window.pipBossKeyString === 'esc' && code === 'escape') match = true;
            if (window.pipBossKeyString === 'space' && code === 'space') match = true;
            
            if (match) {
                if (window.triggerBossKey) {
                    window.triggerBossKey();
                }
            }
        });
        
        window.triggerBossKey = async function() {
            pywebview.api.log("triggerBossKey START");
            if (!window.pipBossHidden) {
                try {
                    let currentMode = await pywebview.api.get_boss_mode();
                    window.pipBossMode = currentMode || 'minimize';
                    pywebview.api.log("triggerBossKey got mode: " + window.pipBossMode);
                } catch(e){
                    pywebview.api.log("get_boss_mode error: " + e.toString());
                }
                try { pywebview.api.apply_temp_fake_icon('random'); } catch(e){}
                let v = getActiveVideo();
                if(v && !v.paused) v.pause();
                
                if (window.pipBossMode === 'opacity') {
                    document.documentElement.style.opacity = '0';
                    document.body.style.pointerEvents = 'none';
                    pywebview.api.hide_window();
                    window.pipBossHidden = true;
                } else if (window.pipBossMode === 'arrow') {
                    document.body.style.opacity = '0';
                    document.body.style.pointerEvents = 'none';
                    
                    let arrow = document.createElement('div');
                    arrow.id = 'pip-boss-arrow';
                    arrow.innerHTML = '▶';
                    arrow.style.cssText = 'position: fixed; top: 0; right: 0; height: 100vh; width: 25px; background: transparent; text-shadow: 0 0 5px rgba(0,0,0,1); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 16px; cursor: pointer; z-index: 2147483647; pointer-events: auto; font-family: monospace;';
                    arrow.onclick = (ev) => {
                        ev.stopPropagation();
                        document.body.style.opacity = '1';
                        document.body.style.pointerEvents = 'auto';
                        let a = document.getElementById('pip-boss-arrow');
                        if (a) a.remove();
                        try { pywebview.api.restore_fake_icon(); } catch(e){}
                        pywebview.api.restore_from_arrow();
                        window.pipBossHidden = false;
                    };
                    document.documentElement.appendChild(arrow);
                    
                    pywebview.api.hide_as_arrow(window.screen.availWidth);
                    window.pipBossHidden = true;
                } else if (window.pipBossMode && window.pipBossMode.startsWith('transform_')) {
                    pywebview.api.log("Entering transform mode...");
                    document.body.style.opacity = '0';
                    document.body.style.pointerEvents = 'none';
                    
                    let shape = window.pipBossMode.split('_')[1] || 'fly';
                    let imgB64 = '';
                    try { 
                        imgB64 = await pywebview.api.get_transform_image(shape); 
                        pywebview.api.log("Got transform image of length: " + (imgB64 ? imgB64.length : 0));
                    } catch(e){
                        pywebview.api.log("get_transform_image error: " + e.toString());
                    }
                    let charHTML = imgB64 ? `<img src="${imgB64}" style="width:100%; height:100%; object-fit:contain;">` : '🪰';
                    
                    let tf = document.createElement('div');
                    tf.id = 'pip-boss-transform';
                    tf.innerHTML = charHTML;
                    tf.style.cssText = 'position: fixed; top: 50%; left: 50%; width: 50px; height: 50px; transform: translate(-50%, -50%); background: transparent; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 2147483647; pointer-events: auto; transition: top 0.2s, left 0.2s;';
                    pywebview.api.log("Appended transform div to body");
                    
                    tf.onmouseover = (ev) => {
                        let w = window.innerWidth - 60;
                        let h = window.innerHeight - 60;
                        tf.style.left = (Math.random() * w + 30) + 'px';
                        tf.style.top = (Math.random() * h + 30) + 'px';
                        tf.style.transform = 'none';
                    };
                    
                    tf.onclick = (ev) => {
                        ev.stopPropagation();
                        document.body.style.opacity = '1';
                        document.body.style.pointerEvents = 'auto';
                        let a = document.getElementById('pip-boss-transform');
                        if (a) a.remove();
                        try { pywebview.api.restore_fake_icon(); } catch(e){}
                        window.pipBossHidden = false;
                    };
                    document.documentElement.appendChild(tf);
                    window.pipBossHidden = true;
                } else if (window.pipBossMode === 'note') {
                    try { pywebview.api.resize_note_window(); } catch(e){}
                    document.body.style.opacity = '0';
                    document.body.style.pointerEvents = 'none';
                    
                    let noteOverlay = document.createElement('div');
                    noteOverlay.id = 'pip-boss-note-ui';
                    noteOverlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: #fffcf0; z-index: 2147483647; display: flex; flex-direction: column; font-family: -apple-system, system-ui; pointer-events: auto; opacity: 1;';
                    
                    let header = document.createElement('div');
                    header.style.cssText = 'height: 40px; background: #fdf5c9; border-bottom: 1px solid #e0d8b0; display: flex; align-items: center; padding: 0 15px; font-weight: bold; color: #666; font-size: 14px; user-select: none; -webkit-app-region: drag; justify-content: space-between;';
                    header.innerHTML = '<span>Ghi chú nhanh</span><button id="btn-close-note" style="background:transparent; border:none; color:#ff5f56; cursor:pointer; font-size:14px; font-weight:bold; padding:0 5px;">Thoát</button>';
                    
                    let textarea = document.createElement('textarea');
                    textarea.style.cssText = 'flex: 1; border: none; outline: none; background: transparent; padding: 20px; font-size: 16px; color: #333; resize: none;';
                    textarea.addEventListener('keydown', (e) => { e.stopPropagation(); });
                    try {
                        pywebview.api.get_note().then(saved => {
                            textarea.value = saved || '';
                        });
                    } catch(e){}
                    // Removed oninput to prevent deadlock. Note is saved upon exiting.
                    
                    noteOverlay.appendChild(header);
                    noteOverlay.appendChild(textarea);
                    document.documentElement.appendChild(noteOverlay);
                    
                    setTimeout(() => {
                        textarea.focus();
                        let closeBtn = document.getElementById('btn-close-note');
                        if (closeBtn) {
                            closeBtn.onclick = () => {
                                if (window.triggerBossKey) window.triggerBossKey();
                            };
                        }
                    }, 100);
                    window.pipBossHidden = true;
                } else {
                    document.body.style.opacity = '0';
                    document.body.style.pointerEvents = 'none';
                    window.pipBossHidden = true;
                    pywebview.api.minimize_window();
                }
            } else {
                try { pywebview.api.restore_fake_icon(); } catch(e){}
                let slider = document.getElementById('opacity-slider');
                let targetOp = slider ? slider.value / 100 : 1;
                document.documentElement.style.opacity = targetOp;
                document.body.style.opacity = '1';
                document.body.style.pointerEvents = 'auto';
                try { pywebview.api.show_window(); } catch(e){}
                
                if (window.pipBossMode === 'arrow') {
                    let a = document.getElementById('pip-boss-arrow');
                    if (a) a.remove();
                    pywebview.api.restore_from_arrow();
                } else if (window.pipBossMode && window.pipBossMode.startsWith('transform_')) {
                    let a = document.getElementById('pip-boss-transform');
                    if (a) a.remove();
                } else if (window.pipBossMode === 'note') {
                    let a = document.getElementById('pip-boss-note-ui');
                    if (a) {
                        try {
                            let ta = a.querySelector('textarea');
                            if(ta) pywebview.api.save_note(ta.value);
                        } catch(e){}
                        a.remove();
                    }
                    try { pywebview.api.restore_window_size(); } catch(e){}
                }
                window.pipBossHidden = false;
            }
        };

        window.pipObjectFit = 'cover';
        document.getElementById('btn-fit').addEventListener('click', () => {
            window.pipObjectFit = window.pipObjectFit === 'cover' ? 'contain' : 'cover';
            let btn = document.getElementById('btn-fit');
            btn.style.color = window.pipObjectFit === 'contain' ? '#f38ba8' : '#bac2de';
            pywebview.api.save_overlay_config('fit', window.pipObjectFit);
        });

        window.pipRotation = 0;
        document.getElementById('btn-rotate').addEventListener('click', () => {
            window.pipRotation = (window.pipRotation + 90) % 360;
        });

        document.getElementById('btn-theme').addEventListener('click', () => {
            let app = document.getElementById('pip-overlay-app');
            app.classList.toggle('theme-light');
            let btn = document.getElementById('btn-theme');
            btn.innerText = btn.innerText === '☀️' ? '🌙' : '☀️';
        });

        document.getElementById('btn-pin').addEventListener('click', () => {
            window.pipIsPinned = !window.pipIsPinned;
            let btn = document.getElementById('btn-pin');
            btn.style.color = window.pipIsPinned ? '#f38ba8' : '#bac2de';
            btn.style.backgroundColor = window.pipIsPinned ? 'rgba(255, 77, 77, 0.2)' : 'transparent';
            btn.style.borderRadius = '5px';
            pywebview.api.toggle_pin(window.pipIsPinned);
            pywebview.api.save_overlay_config('pinned', window.pipIsPinned);
        });

        document.getElementById('btn-go').addEventListener('click', () => {
            let url = document.getElementById('url-input').value.trim();
            if (url) {
                if (!url.startsWith('http')) url = 'https://' + url;
                window.location.href = url;
            }
        });

        document.getElementById('btn-bookmark').addEventListener('click', () => {
            let url = window.location.href;
            let title = document.title || "";
            let platform = "other";
            if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'youtube';
            else if (url.includes('netflix.com')) platform = 'netflix';
            else if (url.includes('tiktok.com')) platform = 'tiktok';
            else if (url.includes('vimeo.com')) platform = 'vimeo';
            else if (url.includes('twitch.tv')) platform = 'twitch';
            
            let timestamp = 0;
            let v = getActiveVideo();
            if (v && v.currentTime) timestamp = Math.floor(v.currentTime);

            pywebview.api.bookmark(url, title, platform, timestamp).then(res => {
                let b = document.getElementById('btn-bookmark');
                b.style.color = '#a6e3a1'; 
                b.innerText = '★';
                b.title = 'Đã lưu';
            });
        });

        function togglePlayPause() {
            let v = getActiveVideo();
            if (v) {
                if (v.paused) {
                    let p = v.play();
                    if (p && p.catch) p.catch(e => v.click());
                } else {
                    v.pause();
                }
            }
        }

        document.getElementById('btn-play-pause').addEventListener('click', togglePlayPause);

        document.addEventListener('click', (e) => {
            if (e.target && e.target.tagName && e.target.tagName.toLowerCase() === 'video' && e.target.classList.contains('pip-fixed-video')) {
                togglePlayPause();
            }
        });

        document.getElementById('btn-next').addEventListener('click', () => {
            var nextBtn = document.querySelector('div[aria-label="Video tiếp theo"], div[aria-label="Next video"], div[aria-label="Next card"]');
            if(nextBtn) nextBtn.click();
            else {
                var el = document.elementFromPoint(window.innerWidth/2, window.innerHeight/2) || document.body;
                el.dispatchEvent(new WheelEvent('wheel', { deltaY: 800, bubbles: true }));
            }
        });

        document.getElementById('btn-prev').addEventListener('click', () => {
            var prevBtn = document.querySelector('div[aria-label="Video trước"], div[aria-label="Previous video"], div[aria-label="Previous card"]');
            if(prevBtn) prevBtn.click();
            else {
                var el = document.elementFromPoint(window.innerWidth/2, window.innerHeight/2) || document.body;
                el.dispatchEvent(new WheelEvent('wheel', { deltaY: -800, bubbles: true }));
            }
        });

        document.getElementById('btn-mute').addEventListener('click', () => {
            window.pipIsMuted = !window.pipIsMuted;
            document.querySelectorAll('video').forEach(v => v.muted = window.pipIsMuted);
            document.getElementById('btn-mute').innerText = window.pipIsMuted ? '🔇' : '🔊';
            pywebview.api.save_overlay_config('muted', window.pipIsMuted);
            let setupMute = document.getElementById('setup-btn-volume');
            if (setupMute) {
                setupMute.innerText = window.pipIsMuted ? 'Đang Tắt' : 'Đang Bật';
                setupMute.style.background = window.pipIsMuted ? '#f38ba8' : '#f9e2af';
            }
        });
        
        // Xoá sạch mọi UI rác an toàn tuyệt đối và không đụng vào thuật toán Play/Pause của Facebook
        setInterval(() => {
            // Đảm bảo trạng thái âm thanh của TẤT CẢ video luôn đồng bộ với nút Mute của chúng ta
            document.querySelectorAll('video').forEach(v => {
                if (v.muted !== window.pipIsMuted) {
                    v.muted = window.pipIsMuted;
                }
            });

            // 3. Render video độc lập, bất chấp giao diện của Facebook (Cinema Mode)
            updateFixedVideo();

            // 4. Đồng bộ nút Play/Pause với trạng thái thực của video
            let playBtn = document.getElementById('btn-play-pause');
            let activeV2 = getActiveVideo();
            if (playBtn) {
                if (!activeV2 || activeV2.paused) {
                    playBtn.innerText = '▶';
                    playBtn.style.background = '#f38ba8';
                    playBtn.style.color = '#ffffff';
                } else {
                    playBtn.innerText = '⏸';
                    playBtn.style.background = 'var(--sep)';
                    playBtn.style.color = 'var(--text)';
                }
            }

            // 5. Ghim thanh Timeline Slider xuống sát đáy màn hình
            document.querySelectorAll('div[role="slider"], input[type="range"]').forEach(slider => {
                let label = (slider.getAttribute('aria-label') || '').toLowerCase();
                if (label.includes('âm') || label.includes('vol')) return; // Bỏ qua thanh âm lượng

                let isForActive = false;
                if (activeV2) {
                    let p = activeV2;
                    for(let i=0; i<8; i++) {
                        if (p && p.parentElement) p = p.parentElement;
                    }
                    if (p && p.contains(slider)) isForActive = true;
                }
                
                if (isForActive) {
                    slider.style.position = 'fixed';
                    slider.style.bottom = '0px';
                    slider.style.left = '0px';
                    slider.style.width = '100vw';
                    slider.style.zIndex = '999999';
                    
                    // Gỡ bỏ overflow: hidden của các thẻ cha để slider không bị cắt lẹm
                    let parent = slider.parentElement;
                    for(let i=0; i<8; i++) {
                        if (parent && parent.tagName !== 'BODY') {
                            parent.style.overflow = 'visible';
                            parent = parent.parentElement;
                        }
                    }
                } else {
                    // Trả về mặc định nếu không phải video đang phát
                    slider.style.position = '';
                    slider.style.bottom = '';
                    slider.style.left = '';
                    slider.style.width = '';
                    slider.style.zIndex = '';
                }
            });


        }, 500);
    }
    """

def inject_custom_ui(window):
    # 1. CSS Ẩn giao diện Facebook thừa và xử lý khoảng trắng
    css = """
        body, html { background-color: #000000 !important; margin: 0 !important; padding: 0 !important; }
        div[role="banner"] { display: none !important; }
        div[role="navigation"] { display: none !important; }
        div[data-pagelet="LeftRail"] { display: none !important; }
        
        /* Ẩn thanh cuộn thừa */
        body, html { overflow: hidden !important; background-color: #000 !important; margin: 0 !important; padding: 0 !important; }
        ::-webkit-scrollbar { width: 0px; background: transparent; }
    """
    window.load_css(css)

    # 2. Bơm Giao diện điều khiển (HTML/CSS) dạng Dock nổi ở dưới cùng
    fb_js = """
        setInterval(() => {
            // 1. Quét toàn bộ màn hình, tìm mọi icon (SVG) của Facebook và ẩn đi
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
            });
        }, 500);
    """
    window.evaluate_js(fb_js)

def apply_saved_cookie(window, api):
    cookie_path = api._get_path('cookie.txt')
    if os.path.exists(cookie_path):
        try:
            with open(cookie_path, 'r') as f:
                c = f.read().strip()
                if c:
                    js = f"""
                    var cookieStr = `{c}`;
                    var d = window.location.hostname.replace('www.', '');
                    cookieStr.split(';').forEach(pair => {{
                        document.cookie = pair.trim() + "; domain=." + d + "; path=/; max-age=31536000";
                    }});
                    """
                    window.evaluate_js(js)
        except: pass

def inject_youtube_ui(window):
    css = """
        body, html { background-color: #000000 !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }
        /* Ẩn header và các thành phần thừa của YouTube */
        #masthead, ytd-masthead, ytd-mini-guide-renderer, #navigation-button { display: none !important; }
        
        /* Ẩn toàn bộ UI overlay của Shorts (like, dislike, comment, share, tên kênh, keyword) */
        ytd-reel-player-overlay-renderer { display: none !important; }
        
        ::-webkit-scrollbar { width: 0px; background: transparent; }
    """
    window.load_css(css)



DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PIP Hub</title>
    <style>
        /* Custom Title Bar for Frameless Dashboard */
        .dash-titlebar { position: fixed; top: 0; left: 0; right: 180px; height: 32px; z-index: 100; display: flex; align-items: center; padding-left: 12px; gap: 14px; pointer-events: auto; -webkit-app-region: drag; }
        .pip-mac-btn { width: 12px; height: 12px; border-radius: 50%; cursor: pointer; transition: transform 0.1s; border: 6px solid transparent; background-clip: padding-box; box-sizing: content-box; margin: -6px; -webkit-app-region: no-drag; }
        .pip-mac-btn:active { transform: scale(0.85); }
        body { 
            --bg-1: #11111b; --bg-2: #1e1e2e; --text: #cdd6f4; --card-bg: rgba(255, 255, 255, 0.03); --card-hover: rgba(255, 255, 255, 0.08);
            --modal-overlay: rgba(10, 10, 15, 0.7); --modal-bg: rgba(30, 30, 46, 0.85); --input-bg: rgba(0,0,0,0.3); --border-color: rgba(255,255,255,0.1); --btn-bg: rgba(255,255,255,0.05);
            margin: 0; padding: 60px 0 20px; background: radial-gradient(circle at top center, var(--bg-2) 0%, var(--bg-1) 100%); color: var(--text); font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; min-height: 100vh; overflow-y: auto; overflow-x: hidden; user-select: none; transition: background 0.3s; box-sizing: border-box;
        }
        @keyframes gradientFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        body.theme-light {
            --bg-1: #e6e9ef; --bg-2: #eff1f5; --text: #4c4f69; --card-bg: rgba(0, 0, 0, 0.03); --card-hover: rgba(0, 0, 0, 0.06);
            --modal-overlay: rgba(200, 200, 210, 0.5); --modal-bg: rgba(255, 255, 255, 0.85); --input-bg: rgba(0,0,0,0.05); --border-color: rgba(0,0,0,0.1); --btn-bg: rgba(0,0,0,0.05);
        }
        h1 { font-size: 38px; margin-top: 30px; margin-bottom: 5px; background: linear-gradient(45deg, #f38ba8, #cba6f7, #89b4fa, #f38ba8); background-size: 300% 300%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: 1.5px; z-index: 10; filter: drop-shadow(0 2px 8px rgba(243,139,168,0.3)); animation: gradientFlow 6s ease infinite; }
        .funny-quote { color: #bac2de; font-size: 14px; font-style: italic; margin-bottom: 30px; z-index: 10; font-weight: 500; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 15px; padding: 10px 20px 30px; z-index: 10; width: 100%; max-width: 480px; box-sizing: border-box; justify-content: center; }
        .card { position: relative; background: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; padding: 25px 15px; cursor: pointer; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; transform: translateZ(0); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15); overflow: hidden; }
        .card::before { content: ""; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(to right, transparent, rgba(255,255,255,0.05), transparent); transform: skewX(-20deg); transition: 0.5s; pointer-events: none; }
        .card:hover::before { left: 150%; }
        .card:hover { transform: translateY(-8px) translateZ(0); background: var(--card-hover); border-color: rgba(255, 255, 255, 0.2); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); }
        .card:active { transform: translateY(-2px) translateZ(0); }
        .icon-img { width: 45px; height: 45px; object-fit: contain; filter: drop-shadow(0 6px 8px rgba(0,0,0,0.3)); transition: transform 0.3s; }
        .card:hover .icon-img { transform: scale(1.15) rotate(3deg); }
        .name { font-size: 14px; font-weight: 700; color: var(--text); letter-spacing: 0.5px; opacity: 0.9; text-align: center; }
        .top-btn { position: absolute; top: 45px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 50%; cursor: pointer; transition: 0.3s; width: 44px; height: 44px; font-size: 18px; z-index: 10000; display:flex; align-items:center; justify-content:center; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); -webkit-app-region: no-drag; }
        .top-btn:hover { background: rgba(255,255,255,0.15); transform: scale(1.1) rotate(10deg); border-color: rgba(255,255,255,0.3); }
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--modal-overlay); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.4s; backdrop-filter: blur(5px); }
        .modal-overlay.show { opacity: 1; pointer-events: auto; }
        .modal-content { background: var(--modal-bg); border: 1px solid var(--border-color); border-radius: 24px; padding: 30px; text-align: center; width: 80%; max-width: 360px; transform: translateY(20px) scale(0.95); transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 20px 50px rgba(0,0,0,0.5); color: var(--text); backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px); }
        .modal-overlay.show .modal-content { transform: translateY(0) scale(1); }
        .modal-content h3 { margin-top: 0; color: var(--text); font-size: 20px; margin-bottom: 25px; font-weight: 800; letter-spacing: 0.5px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }
        .modal-options { display: flex; flex-direction: column; gap: 15px; }
        .modal-btn { background: var(--btn-bg); padding: 15px; border-radius: 16px; color: var(--text); font-weight: 600; cursor: pointer; transition: all 0.3s; border: 1px solid var(--border-color); font-size: 14px; }
        .modal-btn:hover { background: rgba(255,255,255,0.15); border-color: #f38ba8; color: #f38ba8; transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        .modal-close { margin-top: 30px; background: var(--btn-bg); border: 1px solid var(--border-color); color: var(--text); cursor: pointer; font-size: 14px; font-weight: 700; padding: 12px 30px; border-radius: 12px; transition: 0.3s; }
        .modal-close:hover { background: rgba(243, 139, 168, 0.15); color: #f38ba8; border-color: rgba(243, 139, 168, 0.3); transform: translateY(-2px); }
        @keyframes float1 { 0% { transform: translate(0, 0) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0, 0) scale(1); } }
        @keyframes float2 { 0% { transform: translate(0, 0) scale(1); } 33% { transform: translate(-30px, 50px) scale(1.2); } 66% { transform: translate(20px, -20px) scale(0.8); } 100% { transform: translate(0, 0) scale(1); } }
        .blob { position: absolute; border-radius: 50%; filter: blur(90px); z-index: 0; opacity: 0.45; pointer-events: none; mix-blend-mode: screen; }
        .blob-1 { top: -20px; left: -20px; width: 300px; height: 300px; background: #cba6f7; animation: float1 12s ease-in-out infinite; }
        .blob-2 { bottom: -20px; right: -20px; width: 350px; height: 350px; background: #f38ba8; animation: float2 14s ease-in-out infinite; }
        .bm-container { width: 95%; max-width: 540px; margin-top: 5px; background: var(--modal-bg); border: 1px solid var(--border-color); border-radius: 24px; padding: 25px; z-index: 10; display: flex; flex-direction: column; gap: 15px; max-height: 450px; box-sizing: border-box; backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px); box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .bm-header { display: flex; justify-content: space-between; align-items: center; }
        .bm-header h3 { margin: 0; font-size: 18px; color: var(--text); font-weight: 800; letter-spacing: 0.5px; }
        .bm-toolbar { display: flex; gap: 10px; align-items: center; }
        .bm-btn { background: var(--btn-bg); border: 1px solid var(--border-color); color: var(--text); padding: 6px 12px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: 0.3s; font-weight: 600; }
        .bm-btn:hover { background: rgba(255,255,255,0.15); transform: translateY(-2px); }
        .btn-del-bulk { background: rgba(243, 139, 168, 0.15); color: #f38ba8; border-color: rgba(243, 139, 168, 0.3); }
        .btn-del-bulk:hover { background: #f38ba8; color: #11111b; }
        .bm-chk { accent-color: #f38ba8; cursor: pointer; transform: scale(1.2); margin: 0; }
        #bm-filter { appearance: none; background: var(--btn-bg) url('data:image/svg+xml;utf8,<svg fill="gray" height="12" viewBox="0 0 24 24" width="12" xmlns="http://www.w3.org/2000/svg"><path d="M7 10l5 5 5-5z"/></svg>') no-repeat right 8px center; padding-right: 28px; color: var(--text); border: 1px solid var(--border-color); padding: 6px 28px 6px 12px; border-radius: 8px; font-size: 12px; outline: none; cursor: pointer; transition: 0.3s; }
        #bm-filter:hover { background-color: rgba(255,255,255,0.1); }
        .bm-table-container { overflow-y: auto; overflow-x: hidden; border-radius: 12px; border: 1px solid var(--border-color); background: var(--input-bg); }
        .bm-table-container::-webkit-scrollbar { width: 6px; }
        .bm-table-container::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
        .bm-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; table-layout: fixed;}
        .bm-table th { background: var(--btn-bg); padding: 12px 8px; color: var(--text); opacity: 0.9; font-weight: 700; position: sticky; top: 0; z-index: 2; letter-spacing: 0.5px; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
        .bm-table td { padding: 12px 8px; border-bottom: 1px solid var(--border-color); color: var(--text); opacity: 0.9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 13px; font-weight: 500; }
        .bm-table tr:hover td { background: var(--btn-bg); }
        .bm-action-btn { background: none; border: none; cursor: pointer; padding: 4px; border-radius: 6px; transition: 0.2s; font-size: 14px; }
        .bm-action-btn:hover { background: rgba(255,255,255,0.1); transform: scale(1.1); }
        
        .setting-row { display: flex; justify-content: space-between; align-items: center; color: var(--text); font-size: 14px; margin-top: 15px; font-weight: 600; padding: 5px 0; border-bottom: 1px solid var(--border-color); }
        .setting-row:last-child { border-bottom: none; }
        .setting-input { background: var(--input-bg); border: 1px solid var(--border-color); color: var(--text); border-radius: 10px; padding: 6px 12px; font-size: 13px; outline: none; cursor: pointer; transition: 0.3s; font-weight: 600; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); appearance: none; }
        .setting-input:hover { filter: brightness(1.2); border-color: var(--text); }
        .setting-btn { background: var(--btn-bg); border: 1px solid var(--border-color); color: var(--text); border-radius: 10px; padding: 6px 16px; cursor: pointer; font-size: 13px; font-weight: 700; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .setting-btn:hover { background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.3); transform: translateY(-1px); }
    </style>
</head>
<body>
    <div class="dash-titlebar pywebview-drag-region">
        <div class="pip-mac-btn" style="background-color: #ff5f56;" onclick="pywebview.api.close()"></div>
        <div class="pip-mac-btn" style="background-color: #ffbd2e;" onclick="pywebview.api.minimize_window()"></div>
        <div class="pip-mac-btn" style="background-color: #27c93f;"></div>
    </div>
    <button class="top-btn" id="donate-btn" onclick="openDonateModal()" style="right: 185px; background: linear-gradient(45deg, #f38ba8, #cba6f7); color: #11111b; font-size: 14px; font-weight: bold; width: auto; padding: 0 16px; border-radius: 22px; box-shadow: 0 4px 15px rgba(243,139,168,0.3);" title="Donate">💖 Donate</button>
    <button class="top-btn" id="guide-btn" onclick="openGuideModal()" style="right: 310px; color: #a6e3a1; font-size: 18px;" title="Hướng dẫn / Guide">📖</button>
    <button class="top-btn" id="lang-btn" onclick="toggleLanguage()" style="right: 130px; color: #89dceb; font-size: 14px; font-weight: bold; width: 44px; height: 44px;" title="Ngôn ngữ / Language">VN</button>
    <button class="top-btn" onclick="document.getElementById('settings-modal').classList.add('show')" style="right: 20px; color: var(--text);" title="Cài đặt">⚙️</button>
    <button class="top-btn" onclick="document.getElementById('bm-modal').classList.add('show')" style="right: 75px; color: #f9e2af;" title="Bookmarks">⭐</button>
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <h1>PIP Hub</h1>
    <p id="funny-text" class="funny-quote"></p>
    <div class="grid" id="platform-grid">
        <div class="card" onclick="openFBModal()">
            <img class="icon-img" src="##FB_ICON##" alt="Facebook">
            <div class="name">Facebook</div>
        </div>
        <div class="card" onclick="nav('https://www.tiktok.com/explore')">
            <img class="icon-img" src="##TIKTOK_ICON##" alt="TikTok">
            <div class="name">TikTok</div>
        </div>
        <div class="card" onclick="document.getElementById('yt-modal').classList.add('show')">
            <img class="icon-img" src="##YT_ICON##" alt="YouTube">
            <div class="name">YouTube</div>
        </div>
        <div class="card" onclick="nav('https://www.netflix.com/')">
            <img class="icon-img" src="##NETFLIX_ICON##" alt="Netflix">
            <div class="name">Netflix</div>
        </div>
        <div class="card" id="add-new-card" onclick="document.getElementById('add-modal').classList.add('show')">
            <div class="icon-img" style="font-size: 40px; display: flex; align-items: center; justify-content: center; color: var(--text); opacity: 0.8; font-weight: bold;">+</div>
            <div class="name" data-i18n="add_new">Add Mới</div>
        </div>
    </div>

    <div class="modal-overlay" id="add-modal" onclick="this.classList.remove('show')">
        <div class="modal-content" onclick="event.stopPropagation()">
            <h3><span data-i18n="title_add_platform">Thêm Nền Tảng</span></h3>
            <div style="display:flex; flex-direction:column; gap:15px; text-align:left;">
                <input type="text" id="add-name" placeholder="Tên" data-i18n="name" class="setting-input">
                <input type="text" id="add-url" placeholder="Link URL: (Bắt buộc)" data-i18n="url_req" class="setting-input">
                <input type="text" id="add-icon" placeholder="Icon nền tảng: ( không bắt buộc)" data-i18n="icon_opt" class="setting-input">
                <button class="setting-btn" onclick="saveNewPlatform()" style="background: #a6e3a1; color: #11111b; text-align:center;"><span data-i18n="save">Lưu lại</span></button>
            </div>
            <button class="modal-close" onclick="document.getElementById('add-modal').classList.remove('show')"><span data-i18n="close">Đóng</span></button>
        </div>
    </div>

    <div class="modal-overlay" id="bm-modal" onclick="this.classList.remove('show')">
        <div class="modal-content bm-container" onclick="event.stopPropagation()" style="width: 95%; max-width: 500px; padding: 20px;">
            <div class="bm-header">
            <h3><span data-i18n="title_bookmarks">Đã Lưu (Bookmarks)</span></h3>
            <div class="bm-toolbar">
                <input type="checkbox" id="bm-select-all" onchange="toggleSelectAll(this.checked)" style="margin:0; cursor:pointer;" title="Chọn tất cả">
                <button class="bm-btn btn-del-bulk" onclick="deleteSelected()" data-i18n="delete">Xóa</button>
                <select id="bm-filter" onchange="renderBookmarks()">
                    <option value="All" data-i18n="all">Tất cả</option>
                    <option value="Facebook">Facebook</option>
                    <option value="TikTok">TikTok</option>
                    <option value="YouTube">YouTube</option>
                </select>
            </div>
        </div>
        <div class="bm-table-container">
            <table class="bm-table">
                <thead>
                    <tr>
                        <th style="width: 8%; text-align:center;"></th>
                        <th style="width: 12%; text-align:center;" data-i18n="platform">Nền tảng</th>
                        <th style="width: 65%;" data-i18n="video_name">Tên Video</th>
                        <th style="width: 15%; text-align:center;" data-i18n="options">Tùy chọn</th>
                    </tr>
                </thead>
                <tbody id="bm-tbody">
                </tbody>
            </table>
        </div>
        <button class="modal-close" onclick="document.getElementById('bm-modal').classList.remove('show')"><span data-i18n="close">Đóng</span></button>
        </div>
    </div>
    
    <div style="position: absolute; bottom: 10px; width: 100%; text-align: center; color: rgba(255, 255, 255, 0.3); font-size: 11px; font-weight: 500; pointer-events: none;">
        Tool by ChungBruce
    </div>

    <div class="modal-overlay" id="yt-modal" onclick="this.classList.remove('show')">
        <div class="modal-content" onclick="event.stopPropagation()">
            <h3><span data-i18n="title_yt">Chọn chế độ YouTube</span></h3>
            <div class="modal-options">
                <div class="modal-btn" onclick="nav('https://www.youtube.com/shorts/')">⚡ Shorts</div>
                <div class="modal-btn" onclick="nav('https://www.youtube.com/')">📺 Long</div>
            </div>
            <button class="modal-close" onclick="document.getElementById('yt-modal').classList.remove('show')"><span data-i18n="close">Đóng</span></button>
        </div>
    </div>

    <div class="modal-overlay" id="settings-modal" onclick="this.classList.remove('show')">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 400px; padding: 35px;">
            <h3><span data-i18n="title_settings">Cài Đặt Hệ Thống</span></h3>
            <div class="modal-options" style="text-align: left; gap: 5px;">
                <div class="setting-row">
                    <span data-i18n="theme">Giao diện (Sáng/Tối)</span>
                    <button id="dash-btn-theme" class="setting-btn">🌙 Tối</button>
                </div>
                <div class="setting-row">
                    <span data-i18n="boss_key">Boss Key (Ẩn khẩn cấp)</span>
                    <input type="text" id="boss-key-input" readonly value="Tab" class="setting-input" style="color: #f38ba8; width: 70px; text-align: center;" placeholder="Bấm phím...">
                </div>
                <div class="setting-row">
                    <span data-i18n="boss_key_mode">Chế độ Boss Key</span>
                    <div style="display:flex; flex-direction:column; align-items:flex-end;">
                        <div style="display:flex; gap:5px; align-items:center;">
                            <select id="dash-boss-mode" class="setting-input" style="padding-right: 28px; background-image: url('data:image/svg+xml;utf8,<svg fill=\"gray\" height=\"12\" viewBox=\"0 0 24 24\" width=\"12\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M7 10l5 5 5-5z\"/></svg>'); background-repeat: no-repeat; background-position: right 8px center;">
                                <option value="minimize" data-i18n="minimize">Thu nhỏ (Dock)</option>
                                <option value="arrow" data-i18n="arrow">Mũi tên (Mép trái)</option>
                                <option value="opacity" data-i18n="invisible">Tàng hình (Độ mờ 0%)</option>
                                <option value="transform" data-i18n="transform">Biến hình 🪄</option>
                                <option value="note" data-i18n="note_mode">Ghi chú 📝</option>
                            </select>
                            <button id="dash-transform-btn" onclick="document.getElementById('transform-modal').classList.add('show')" class="setting-btn" style="display: none; padding: 5px 10px; min-width: auto;" title="Chọn hình dáng">⚙️</button>
                        </div>
                        <div id="dash-transform-note" style="display:none; font-size: 11px; color: gray; margin-top: 5px; margin-right: 35px;"></div>
                    </div>
                </div>
                <div class="setting-row">
                    <span data-i18n="fake_icon">Fake icon Dưới thanh Dock</span>
                    <select id="dash-fake-icon" class="setting-input" style="padding-right: 28px; background-image: url('data:image/svg+xml;utf8,<svg fill=\"gray\" height=\"12\" viewBox=\"0 0 24 24\" width=\"12\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M7 10l5 5 5-5z\"/></svg>'); background-repeat: no-repeat; background-position: right 8px center;">
                        <option value="off" data-i18n="off_default">Tắt (Mặc định)</option>
                        <option value="random">🎲 Random</option>
                        <option value="canva">Canva</option>
                        <option value="excel">Excel</option>
                        <option value="mail">Mail</option>
                        <option value="note">Note</option>
                        <option value="powerpoint">PowerPoint</option>
                        <option value="word">Word</option>
                        <option value="zalo">Zalo</option>
                    </select>
                </div>
                <div class="setting-row">
                    <span data-i18n="transparent">Viền trong suốt (Ẩn viền đen)</span>
                    <button id="dash-btn-transparency" class="setting-btn">Tắt</button>
                </div>
                <div style="font-size: 11px; color: #a6adc8; margin-top: 15px; font-style: italic; line-height: 1.5; opacity: 0.8; text-align: center;">
                    <span data-i18n="note_boss">* Lưu ý: Click vào ô trên rồi bấm phím muốn gán. Khi đang xem phim, bấm phím này để ẩn cửa sổ và dừng video, bấm lại để hiện ra. Cửa sổ phim phải đang được focus mới nhận phím.</span>
                </div>
            </div>
            <button class="modal-close" onclick="document.getElementById('settings-modal').classList.remove('show')"><span data-i18n="close">Đóng</span></button>
        </div>
    </div>
    
    <div class="modal-overlay" id="transform-modal" onclick="this.classList.remove('show')">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 300px; padding: 25px;">
            <h3 style="margin-bottom: 20px;" data-i18n="title_shape">Chọn Hình Dáng</h3>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button class="setting-btn" onclick="setTransformMode('fly')" style="font-size: 16px; justify-content: center;"><span data-i18n="fly">🪰 Con ruồi</span></button>
                <button class="setting-btn" onclick="setTransformMode('star')" style="font-size: 16px; justify-content: center;"><span data-i18n="star">⭐ Ngôi sao</span></button>
                <button class="setting-btn" onclick="setTransformMode('smile')" style="font-size: 16px; justify-content: center;"><span data-i18n="smile">😃 Mặt cười</span></button>
                <button class="setting-btn" onclick="setTransformMode('dot')" style="font-size: 16px; justify-content: center;"><span data-i18n="dot">⚫ Chấm đen</span></button>
                <hr style="border: 0; border-top: 1px solid var(--border-color); width: 100%; margin: 5px 0;">
                <div id="custom-icons-container" style="display: flex; flex-direction: column; gap: 10px;"></div>
                <button class="setting-btn" style="background: rgba(255, 255, 255, 0.1); justify-content: center;" onclick="openCustomIconModal()"><span data-i18n="custom">➕ Tuỳ chọn</span></button>
            </div>
            <button class="modal-close" style="margin-top: 15px;" onclick="document.getElementById('transform-modal').classList.remove('show'); document.getElementById('dash-boss-mode').value='minimize'; pywebview.api.set_boss_mode('minimize');" data-i18n="cancel">Hủy</button>
        </div>
    </div>
    
    <!-- Custom Icon Modal -->
    <div class="modal-overlay" id="custom-icon-modal" onclick="closeCustomIconModal()">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 320px; padding: 25px;">
            <h3 style="margin-top: 0; margin-bottom: 20px;" data-i18n="title_custom_shape">Thêm Tuỳ chọn</h3>
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <input type="file" id="customIconFile" accept="image/png" style="display: none;" onchange="document.getElementById('customIconFileName').innerText = this.files[0] ? this.files[0].name : 'Chưa chọn file'">
                <button class="setting-btn" onclick="document.getElementById('customIconFile').click()" style="justify-content: center;"><span data-i18n="upload_png">Upload Ảnh (PNG)</span></button>
                <div id="customIconFileName" style="color: var(--text); font-size: 12px; text-align: center; opacity: 0.8;" data-i18n="no_file">Chưa chọn file</div>
                
                <input type="text" id="customIconName" placeholder="Tên hiển thị (vd: Cục Shit)" data-i18n="display_name" style="width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border-color); color: var(--text); border-radius: 12px; text-align: center; box-sizing: border-box; outline: none; font-size: 14px;">
            </div>
            <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px;">
                <button class="modal-close" style="margin-top: 0;" onclick="closeCustomIconModal()" data-i18n="cancel">Hủy</button>
                <button class="modal-close" style="margin-top: 0; background: rgba(243, 139, 168, 0.15); color: #f38ba8; border-color: rgba(243, 139, 168, 0.3);" onclick="saveCustomIcon()"><span data-i18n="save">Lưu lại</span></button>
            </div>
        </div>
    </div>




    <div class="modal-overlay" id="donate-modal" onclick="closeDonateModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 550px; padding: 35px; width: 90%;">
            <h3 style="margin-bottom: 20px;"><span data-i18n="title_donate">Ủng hộ dự án 💖</span></h3>
            
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <!-- Bank Accordion -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden;">
                    <button class="setting-btn" onclick="toggleDonateAccordion('bank')" style="width: 100%; text-align: left; padding: 15px; background: transparent; border: none; font-size: 16px; font-weight: bold; border-radius: 0; display: flex; justify-content: space-between;">
                        <span style="display:flex; align-items:center; gap:8px;">🏦 <span data-i18n="donate_bank">Donate qua ngân hàng</span></span>
                        <span id="icon-bank">▼</span>
                    </button>
                    <div id="donate-bank" class="donate-tab" style="display: flex; gap: 20px; align-items: center; text-align: left; padding: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <img src="##DONATE_IMG##" alt="Donate QR" style="width: 200px; height: 200px; border-radius: 12px; object-fit: contain;">
                        <div style="flex: 1; font-size: 15px; line-height: 1.6; color: #bac2de;" data-i18n="donate_bank_desc">
                            Cảm ơn bạn đã sử dụng Piphub. Nếu hay hãy ủng hộ tôi bằng cách chuyển khoản qua ngân hàng để giúp đội ngũ tiếp tục phát triển
                        </div>
                    </div>
                </div>

                <!-- Crypto Accordion -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden;">
                    <button class="setting-btn" onclick="toggleDonateAccordion('crypto')" style="width: 100%; text-align: left; padding: 15px; background: transparent; border: none; font-size: 16px; font-weight: bold; border-radius: 0; display: flex; justify-content: space-between;">
                        <span style="display:flex; align-items:center; gap:8px;">🪙 <span data-i18n="donate_crypto">Donate via crypto</span></span>
                        <span id="icon-crypto">▶</span>
                    </button>
                    <div id="donate-crypto" class="donate-tab" style="display: none; text-align: left; padding: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <div style="font-size: 14px; margin-bottom: 15px; line-height: 1.5; color: #bac2de;" data-i18n="donate_crypto_desc">
                            Cảm ơn bạn đã sử dụng Piphub. Nếu hay hãy ủng hộ tôi bằng cách donate qua ví crypto EVM, BTC, SOL, SUI để giúp đội ngũ tiếp tục phát triển
                        </div>
                        
                        <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; justify-content: center;">
                            <button class="setting-btn crypto-btn" onclick="showCryptoTab('evm')" style="background: rgba(137, 220, 235, 0.2); color: #89dceb; border-color: #89dceb; min-width: 60px;">EVM</button>
                            <button class="setting-btn crypto-btn" onclick="showCryptoTab('btc')" style="background: rgba(249, 226, 175, 0.2); color: #f9e2af; border-color: #f9e2af; min-width: 60px;">BTC</button>
                            <button class="setting-btn crypto-btn" onclick="showCryptoTab('sol')" style="background: rgba(243, 139, 168, 0.2); color: #f38ba8; border-color: #f38ba8; min-width: 60px;">SOL</button>
                            <button class="setting-btn crypto-btn" onclick="showCryptoTab('sui')" style="background: rgba(166, 227, 161, 0.2); color: #a6e3a1; border-color: #a6e3a1; min-width: 60px;">SUI</button>
                        </div>

                        <div id="crypto-tab-evm" class="crypto-tab-content" style="background: rgba(137, 220, 235, 0.1); border-left: 4px solid #89dceb; padding: 15px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="color: #89dceb; font-weight: bold; font-size: 14px; margin-bottom: 5px;">EVM Network</div>
                                <div style="font-size: 13px; font-family: monospace; word-break: break-all; color: #cdd6f4;">0xd63d44ba0830e500e5b6ec31dd975c1558bb5c20</div>
                            </div>
                            <button class="setting-btn" onclick="copyText('0xd63d44ba0830e500e5b6ec31dd975c1558bb5c20')" style="margin-left: 15px;">Copy</button>
                        </div>
                        
                        <div id="crypto-tab-btc" class="crypto-tab-content" style="display: none; background: rgba(249, 226, 175, 0.1); border-left: 4px solid #f9e2af; padding: 15px; border-radius: 4px; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="color: #f9e2af; font-weight: bold; font-size: 14px; margin-bottom: 5px;">Bitcoin Network</div>
                                <div style="font-size: 13px; font-family: monospace; word-break: break-all; color: #cdd6f4;">bc1pdcrrcta5wl05t3pdanc8v79e72w2dcw7v5kpt5ckd4e09mhv2vfsj0qkuw</div>
                            </div>
                            <button class="setting-btn" onclick="copyText('bc1pdcrrcta5wl05t3pdanc8v79e72w2dcw7v5kpt5ckd4e09mhv2vfsj0qkuw')" style="margin-left: 15px;">Copy</button>
                        </div>
                        
                        <div id="crypto-tab-sol" class="crypto-tab-content" style="display: none; background: rgba(243, 139, 168, 0.1); border-left: 4px solid #f38ba8; padding: 15px; border-radius: 4px; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="color: #f38ba8; font-weight: bold; font-size: 14px; margin-bottom: 5px;">Solana Network</div>
                                <div style="font-size: 13px; font-family: monospace; word-break: break-all; color: #cdd6f4;">8RuTqrsMFQg1oxgaLx34vUCmuNw7YJGBTf3p2SeaZY9U</div>
                            </div>
                            <button class="setting-btn" onclick="copyText('8RuTqrsMFQg1oxgaLx34vUCmuNw7YJGBTf3p2SeaZY9U')" style="margin-left: 15px;">Copy</button>
                        </div>
                        
                        <div id="crypto-tab-sui" class="crypto-tab-content" style="display: none; background: rgba(166, 227, 161, 0.1); border-left: 4px solid #a6e3a1; padding: 15px; border-radius: 4px; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="color: #a6e3a1; font-weight: bold; font-size: 14px; margin-bottom: 5px;">SUI Network</div>
                                <div style="font-size: 13px; font-family: monospace; word-break: break-all; color: #cdd6f4;">0x4f1834e811f44f404cecd5df9183c9dd43bd03cdec3ea2a858421faee2956040</div>
                            </div>
                            <button class="setting-btn" onclick="copyText('0x4f1834e811f44f404cecd5df9183c9dd43bd03cdec3ea2a858421faee2956040')" style="margin-left: 15px;">Copy</button>
                        </div>
                    </div>
                </div>

                <!-- Paypal Accordion -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden;">
                    <button class="setting-btn" onclick="toggleDonateAccordion('paypal')" style="width: 100%; text-align: left; padding: 15px; background: transparent; border: none; font-size: 16px; font-weight: bold; border-radius: 0; display: flex; justify-content: space-between;">
                        <span style="display:flex; align-items:center; gap:8px;">☕ <span data-i18n="donate_paypal">Donate via Paypal</span></span>
                        <span id="icon-paypal">▶</span>
                    </button>
                    <div id="donate-paypal" class="donate-tab" style="display: none; padding: 25px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <div style="font-size: 16px; color: #f38ba8; font-weight: bold;" data-i18n="donate_paypal_desc">
                            Chưa làm đc tính năng này, lỗi nhiều :))
                        </div>
                    </div>
                </div>
            </div>
            
            <button class="modal-close" style="margin-top: 25px;" onclick="closeDonateModal(event)"><span data-i18n="close">Đóng</span></button>
        </div>
    </div>

    <div class="modal-overlay" id="fb-modal" onclick="closeFBModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 400px; padding: 35px; width: 90%; text-align: center;">
            <h3 style="margin-bottom: 20px;"><span data-i18n="fb_options">Tùy chọn Facebook</span></h3>
            
            <div id="fb-action-buttons" style="display: flex; flex-direction: column; gap: 15px;">
                <button class="setting-btn" onclick="closeFBModal(); nav('https://www.facebook.com/reels/')" style="width: 100%; padding: 15px; background: #0866ff; color: white; font-weight: bold; border-radius: 8px;">
                    <span data-i18n="fb_login">Login with FB</span>
                </button>
                <button class="setting-btn" onclick="showFBCookieInput()" style="width: 100%; padding: 15px; background: #f38ba8; color: #11111b; font-weight: bold; border-radius: 8px;">
                    <span data-i18n="fb_cookie">Dùng Cookie</span>
                </button>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button class="setting-btn" onclick="clearFBProfile()" style="flex: 1; padding: 10px; background: #eba0ac; color: #11111b; border-radius: 8px; font-weight: bold; font-size: 13px;">Xoá Profile</button>
                    <button class="setting-btn" onclick="clearFBCookieFile()" style="flex: 1; padding: 10px; background: #eba0ac; color: #11111b; border-radius: 8px; font-weight: bold; font-size: 13px;">Xoá Cookie</button>
                </div>
            </div>

            <div id="fb-cookie-input-div" style="display: none; flex-direction: column; gap: 10px; margin-top: 10px;">
                <textarea id="fb-cookie-val" rows="4" placeholder="Dán cookie Facebook vào đây..." style="width: 100%; border-radius: 8px; padding: 10px; background: rgba(0,0,0,0.3); color: #cdd6f4; border: 1px solid #45475a; font-size: 12px; outline: none; resize: none;"></textarea>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button class="setting-btn" onclick="hideFBCookieInput()" style="flex: 1; padding: 10px; background: #45475a; border-radius: 8px;"><span data-i18n="cancel">Hủy</span></button>
                    <button class="setting-btn" onclick="saveAndGoFB()" style="flex: 1; padding: 10px; background: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 8px;">Lưu & Vào FB</button>
                </div>
            </div>

            <button class="modal-close" style="margin-top: 25px;" onclick="closeFBModal(event)"><span data-i18n="close">Đóng</span></button>
        </div>
    </div>

    <div class="modal-overlay" id="access-modal" style="z-index: 10001;">
        <div class="modal-content" style="max-width: 450px; padding: 35px; width: 90%; text-align: center;">
            <h3 style="margin-bottom: 20px;"><span data-i18n="access_title">⚠️ Yêu cầu Quyền truy cập</span></h3>
            <p style="color: #bac2de; font-size: 14px; line-height: 1.6; margin-bottom: 25px;" data-i18n="access_desc">
                Để tính năng phím tắt ẩn nhanh (Boss Key) có thể hoạt động, Pip Hub cần bạn cấp quyền Trợ năng (Accessibility).<br><br><span style="color: #f9e2af; font-weight: bold;">Hướng dẫn:</span><br>1. Di chuyển app vào mục Applications (Ứng dụng) trên Macbook.<br>2. Bấm nút Mở Cài đặt bên dưới (hoặc vào Accessibility).<br>3. Bấm dấu <span style="color:#a6e3a1; font-weight:bold;">[+]</span> và chọn <b>PipHub Launcher</b>.
            </p>
            <div style="display: flex; gap: 15px;">
                <button class="setting-btn" onclick="document.getElementById('access-modal').classList.remove('show')" style="flex: 1; padding: 12px; background: #45475a; border-radius: 8px;"><span data-i18n="close">Đóng</span></button>
                <button class="setting-btn" onclick="pywebview.api.open_accessibility_settings(); document.getElementById('access-modal').classList.remove('show')" style="flex: 1; padding: 12px; background: #89b4fa; color: #11111b; font-weight: bold; border-radius: 8px;"><span data-i18n="access_open">Mở Cài đặt</span></button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="guide-modal" onclick="closeGuideModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 500px; padding: 35px; width: 90%; text-align: left; max-height: 80vh; overflow-y: auto;">
            <h3 style="margin-bottom: 20px; text-align: center;"><span data-i18n="guide_title">📖 Hướng dẫn sử dụng</span></h3>
            
            <div style="margin-bottom: 20px;">
                <h4 style="color: #f38ba8; margin-bottom: 10px;" data-i18n="guide_bosskey_title">1. Hướng dẫn dùng Boss Key</h4>
                <p style="color: #bac2de; font-size: 14px; line-height: 1.6; margin: 0;" data-i18n="guide_bosskey_desc">Boss Key (Phím tắt ẩn nhanh) giúp bạn ẩn/hiện cửa sổ đang xem ngay lập tức bằng một phím tắt duy nhất. Bạn có thể vào phần Cài đặt (⚙️) để thay đổi phím tắt này (mặc định là phím Tab).</p>
            </div>

            <div style="margin-bottom: 20px;">
                <h4 style="color: #cba6f7; margin-bottom: 10px;" data-i18n="guide_modes_title">2. Các chế độ của Boss Key</h4>
                <ul style="color: #bac2de; font-size: 14px; line-height: 1.6; margin: 0; padding-left: 20px;">
                    <li style="margin-bottom: 5px;" data-i18n="guide_mode_dock"><b>Thu nhỏ (Dock):</b> Thu nhỏ cửa sổ xuống thanh Dock của Mac.</li>
                    <li style="margin-bottom: 5px;" data-i18n="guide_mode_arrow"><b>Mũi tên (Mép trái):</b> Trượt cửa sổ ra ngoài mép trái màn hình, chỉ để lại một mũi tên nhỏ. Rê chuột vào mũi tên để hiển thị lại.</li>
                    <li style="margin-bottom: 5px;" data-i18n="guide_mode_invisible"><b>Tàng hình:</b> Làm cho cửa sổ hoàn toàn trong suốt (độ mờ 0%).</li>
                    <li style="margin-bottom: 5px;" data-i18n="guide_mode_transform"><b>Biến hình 🪄:</b> Thu nhỏ kích thước và chuyển icon thành giả mạo.</li>
                    <li data-i18n="guide_mode_note"><b>Ghi chú 📝:</b> Chuyển giao diện thành một ứng dụng Ghi chú giả, che giấu nội dung.</li>
                </ul>
            </div>

            <div style="margin-bottom: 20px;">
                <h4 style="color: #89b4fa; margin-bottom: 10px;" data-i18n="guide_platform_title">3. Hướng dẫn thêm Nền tảng</h4>
                <p style="color: #bac2de; font-size: 14px; line-height: 1.6; margin: 0;" data-i18n="guide_platform_desc">Bạn có thể thêm trang web tuỳ ý bằng cách kéo xuống dưới cùng màn hình chính, bấm nút <b>[+] Thêm Nền Tảng</b>. Điền Tên và URL của trang web (Icon không bắt buộc).</p>
            </div>

            <div style="text-align: center;">
                <button class="modal-close" style="margin-top: 15px;" onclick="closeGuideModal(event)"><span data-i18n="close">Đóng</span></button>
            </div>
        </div>
    </div>

    <script>
        
        const I18N = {
            'vn': {
                'title_settings': '<span data-i18n="title_settings">Cài Đặt Hệ Thống</span>',
                'title_bookmarks': 'Đã Lưu (Bookmarks)',
                'title_add_platform': 'Thêm Nền Tảng',
                'title_yt': 'Chọn chế độ YouTube',
                'title_shape': 'Chọn Hình Dáng',
                'title_custom_shape': 'Thêm Tuỳ chọn',
                'add_new': 'Add Mới',
                'name': 'Tên',
                'url_req': 'Link URL: (Bắt buộc)',
                'icon_opt': 'Icon nền tảng: (không bắt buộc)',
                'save': 'Lưu lại',
                'close': 'Đóng',
                'cancel': 'Hủy',
                'delete': 'Xóa',
                'all': 'Tất cả',
                'platform': 'Nền tảng',
                'video_name': 'Tên Video',
                'options': 'Tùy chọn',
                'theme': 'Giao diện (Sáng/Tối)',
                'boss_key': 'Boss Key (Ẩn khẩn cấp)',
                'boss_key_mode': 'Chế độ Boss Key',
                'fake_icon': 'Fake icon Dưới thanh Dock',
                'transparent': 'Viền trong suốt (Ẩn viền đen)',
                'note_boss': '* Lưu ý: Click vào ô trên rồi bấm phím muốn gán. Khi đang xem phim, bấm phím này để ẩn cửa sổ và dừng video, bấm lại để hiện ra.',
                'minimize': 'Thu nhỏ (Dock)',
                'arrow': 'Mũi tên (Mép trái)',
                'invisible': 'Tàng hình (Độ mờ 0%)',
                'transform': 'Biến hình 🪄',
                'note_mode': 'Ghi chú 📝',
                'off_default': 'Tắt (Mặc định)',
                'upload_png': 'Upload Ảnh (PNG)',
                'no_file': 'Chưa chọn file',
                'display_name': 'Tên hiển thị (vd: Cục Shit)',
                'custom': '➕ Tuỳ chọn',
                'fly': '🪰 Con ruồi',
                'star': '⭐ Ngôi sao',
                'smile': '😃 Mặt cười',
                'dot': '⚫ Chấm đen',
                'alert_png': 'Vui lòng chọn ảnh PNG',
                'alert_name': 'Vui lòng nhập tên hiển thị',
                'alert_err': 'Lỗi khi lưu icon!',
                'alert_del': 'Xoá icon này?',
                'alert_url': 'Vui lòng nhập Link URL!',
                'btn_on': 'Bật',
                'btn_off': 'Tắt',
                'btn_light': '☀️ Sáng',
                'btn_dark': '🌙 Tối',
                'title_donate': 'Ủng hộ dự án 💖',
                'donate_bank': 'Donate qua ngân hàng',
                'donate_crypto': 'Donate via crypto',
                'donate_paypal': 'Donate via Paypal',
                'donate_bank_desc': '<span style="color: #f38ba8; font-weight: bold; font-size: 16px;">Cảm ơn bạn đã sử dụng Piphub.</span><br><br>Nếu hay hãy ủng hộ tôi bằng cách <span style="color: #a6e3a1; font-weight:bold;">chuyển khoản qua ngân hàng</span> để giúp đội ngũ tiếp tục phát triển 🚀',
                'donate_crypto_desc': '<span style="color: #f38ba8; font-weight: bold; font-size: 16px;">Cảm ơn bạn đã sử dụng Piphub.</span><br><br>Nếu hay hãy ủng hộ tôi bằng cách donate qua ví crypto <span style="color: #f9e2af; font-weight:bold;">EVM, BTC, SOL, SUI</span> để giúp đội ngũ tiếp tục phát triển 🚀',
                'donate_paypal_desc': 'Chưa làm đc tính năng này, lỗi nhiều :))',
                'copied': 'Đã copy',
                'fb_options': 'Tùy chọn Facebook',
                'fb_login': 'Login with FB',
                'fb_cookie': 'Dùng Cookie',
                'access_title': '⚠️ Yêu cầu Quyền truy cập',
                'access_desc': 'Để tính năng phím tắt ẩn nhanh (Boss Key) có thể hoạt động, Pip Hub cần bạn cấp quyền Trợ năng (Accessibility).<br><br><span style="color: #f9e2af; font-weight: bold;">Hướng dẫn:</span><br>1. Di chuyển app vào mục Applications (Ứng dụng) trên Macbook.<br>2. Bấm nút Mở Cài đặt bên dưới (hoặc vào Accessibility).<br>3. Bấm dấu <span style="color:#a6e3a1; font-weight:bold;">[+]</span> và chọn <b>PipHub Launcher</b>.',
                'access_open': 'Mở Cài đặt',
                'guide_title': '📖 Hướng dẫn sử dụng',
                'guide_bosskey_title': '1. Hướng dẫn dùng Boss Key',
                'guide_bosskey_desc': 'Boss Key (Phím tắt ẩn nhanh) giúp bạn ẩn/hiện cửa sổ đang xem ngay lập tức bằng một phím tắt duy nhất. Bạn có thể vào phần Cài đặt (⚙️) để thay đổi phím tắt này (mặc định là phím Tab).',
                'guide_modes_title': '2. Các chế độ của Boss Key',
                'guide_mode_dock': '<b>Thu nhỏ (Dock):</b> Thu nhỏ cửa sổ xuống thanh Dock của Mac.',
                'guide_mode_arrow': '<b>Mũi tên (Mép trái):</b> Trượt cửa sổ ra ngoài mép trái màn hình, chỉ để lại một mũi tên nhỏ. Rê chuột vào mũi tên để hiển thị lại.',
                'guide_mode_invisible': '<b>Tàng hình:</b> Làm cho cửa sổ hoàn toàn trong suốt (độ mờ 0%).',
                'guide_mode_transform': '<b>Biến hình 🪄:</b> Thu nhỏ kích thước và chuyển icon thành giả mạo.',
                'guide_mode_note': '<b>Ghi chú 📝:</b> Chuyển giao diện thành một ứng dụng Ghi chú giả, che giấu nội dung.',
                'guide_platform_title': '3. Hướng dẫn thêm Nền tảng',
                'guide_platform_desc': 'Bạn có thể thêm trang web tuỳ ý bằng cách kéo xuống dưới cùng màn hình chính, bấm nút <b>[+] Thêm Nền Tảng</b>. Điền Tên và URL của trang web (Icon không bắt buộc).'
            },
            'en': {
                'title_settings': 'System Settings',
                'title_bookmarks': 'Bookmarks',
                'title_add_platform': 'Add Platform',
                'title_yt': 'Select YouTube Mode',
                'title_shape': 'Select Shape',
                'title_custom_shape': 'Add Custom Shape',
                'add_new': 'Add New',
                'name': 'Name',
                'url_req': 'URL Link: (Required)',
                'icon_opt': 'Platform Icon: (Optional)',
                'save': 'Save',
                'close': 'Close',
                'cancel': 'Cancel',
                'delete': 'Delete',
                'all': 'All',
                'platform': 'Platform',
                'video_name': 'Video Name',
                'options': 'Options',
                'theme': 'Theme (Light/Dark)',
                'boss_key': 'Boss Key (Emergency Hide)',
                'boss_key_mode': 'Boss Key Mode',
                'fake_icon': 'Fake icon in Dock',
                'transparent': 'Transparent Borders',
                'note_boss': '* Note: Click the box above and press a key to assign. While watching a video, press this key to hide the window and pause the video.',
                'minimize': 'Minimize (Dock)',
                'arrow': 'Arrow (Left edge)',
                'invisible': 'Invisible (Opacity 0%)',
                'transform': 'Transform 🪄',
                'note_mode': 'Quick Note 📝',
                'off_default': 'Off (Default)',
                'upload_png': 'Upload Image (PNG)',
                'no_file': 'No file selected',
                'display_name': 'Display name (e.g. Poop)',
                'custom': '➕ Custom',
                'fly': '🪰 Fly',
                'star': '⭐ Star',
                'smile': '😃 Smile',
                'dot': '⚫ Black Dot',
                'alert_png': 'Please select a PNG image',
                'alert_name': 'Please enter a display name',
                'alert_err': 'Error saving icon!',
                'alert_del': 'Delete this icon?',
                'alert_url': 'Please enter a URL!',
                'btn_on': 'On',
                'btn_off': 'Off',
                'btn_light': '☀️ Light',
                'btn_dark': '🌙 Dark',
                'title_donate': 'Support the Project 💖',
                'donate_bank': 'Bank Transfer',
                'donate_crypto': 'Crypto Transfer',
                'donate_paypal': 'PayPal',
                'donate_bank_desc': '<span style="color: #f38ba8; font-weight: bold; font-size: 16px;">Thank you for using Piphub.</span><br><br>If you like it, please support us via <span style="color: #a6e3a1; font-weight:bold;">bank transfer</span> to help the team continue development 🚀',
                'donate_crypto_desc': '<span style="color: #f38ba8; font-weight: bold; font-size: 16px;">Thank you for using Piphub.</span><br><br>If you like it, please support us via crypto wallets <span style="color: #f9e2af; font-weight:bold;">(EVM, BTC, SOL, SUI)</span> to help the team continue development 🚀',
                'donate_paypal_desc': 'Not implemented yet, too many errors :))',
                'copied': 'Copied',
                'fb_options': 'Facebook Options',
                'fb_login': 'Login with FB',
                'fb_cookie': 'Use Cookie',
                'access_title': '⚠️ Accessibility Permission',
                'access_desc': 'For the Boss Key feature to work globally, Pip Hub needs Accessibility permission.<br><br><span style="color: #f9e2af; font-weight: bold;">Instructions:</span><br>1. Move the app to the Applications folder on your Mac.<br>2. Click Open Settings below (or go to Accessibility).<br>3. Click the <span style="color:#a6e3a1; font-weight:bold;">[+]</span> icon and select <b>PipHub Launcher</b>.',
                'access_open': 'Open Settings',
                'guide_title': '📖 User Guide',
                'guide_bosskey_title': '1. How to use Boss Key',
                'guide_bosskey_desc': 'Boss Key allows you to instantly hide/show the active window using a single keyboard shortcut. You can change this shortcut in Settings (⚙️) (default is Tab key).',
                'guide_modes_title': '2. Boss Key Modes',
                'guide_mode_dock': '<b>Minimize (Dock):</b> Minimizes the window to the Mac Dock.',
                'guide_mode_arrow': '<b>Arrow (Left Edge):</b> Slides the window off-screen to the left, leaving only a small arrow. Hover over it to show again.',
                'guide_mode_invisible': '<b>Invisible:</b> Makes the window completely transparent (0% opacity).',
                'guide_mode_transform': '<b>Transform 🪄:</b> Shrinks the window and changes the icon to a fake one.',
                'guide_mode_note': '<b>Notes 📝:</b> Changes the UI to a fake Notes app, completely hiding your content.',
                'guide_platform_title': '3. Adding Custom Platforms',
                'guide_platform_desc': 'You can add custom websites by scrolling to the bottom of the main screen and clicking <b>[+] Add Platform</b>. Enter the Name and URL (Icon is optional).'
            }
        };

        let currentLang = 'vn';
        try { currentLang = localStorage.getItem('pip_lang') || 'vn'; } catch(e) {}

        function toggleLanguage() {
            currentLang = currentLang === 'vn' ? 'en' : 'vn';
            try { localStorage.setItem('pip_lang', currentLang); } catch(e) {}
            applyLanguage();
        }

        function toggleDonateAccordion(tabId) {
            let el = document.getElementById('donate-' + tabId);
            let icon = document.getElementById('icon-' + tabId);
            let isHidden = el.style.display === 'none';
            
            // Close all
            document.querySelectorAll('.donate-tab').forEach(e => e.style.display = 'none');
            document.getElementById('icon-bank').innerText = '▶';
            document.getElementById('icon-crypto').innerText = '▶';
            document.getElementById('icon-paypal').innerText = '▶';

            if (isHidden) {
                el.style.display = tabId === 'bank' ? 'flex' : 'block';
                icon.innerText = '▼';
            }
        }

        function showCryptoTab(net) {
            document.querySelectorAll('.crypto-tab-content').forEach(el => el.style.display = 'none');
            document.getElementById('crypto-tab-' + net).style.display = 'flex';
        }

        window.addEventListener('pywebviewready', function() {
            pywebview.api.check_accessibility().then(function(has_permission) {
                if (!has_permission) {
                    document.getElementById('access-modal').classList.add('show');
                }
            });
        });

        function openDonateModal() {
            document.getElementById('donate-modal').classList.add('show');
            document.querySelectorAll('.top-btn').forEach(btn => btn.style.display = 'none');
        }

        function closeDonateModal(e) {
            document.getElementById('donate-modal').classList.remove('show');
            document.querySelectorAll('.top-btn').forEach(btn => btn.style.display = 'flex');
        }

        function openGuideModal() {
            document.getElementById('guide-modal').classList.add('show');
            document.querySelectorAll('.top-btn').forEach(btn => btn.style.display = 'none');
        }

        function closeGuideModal(e) {
            document.getElementById('guide-modal').classList.remove('show');
            document.querySelectorAll('.top-btn').forEach(btn => btn.style.display = 'flex');
        }

        function openFBModal() {
            document.getElementById('fb-modal').classList.add('show');
            document.querySelectorAll('.top-btn').forEach(btn => btn.style.display = 'none');
            hideFBCookieInput();
        }

        function closeFBModal(e) {
            document.getElementById('fb-modal').classList.remove('show');
            document.querySelectorAll('.top-btn').forEach(btn => btn.style.display = 'flex');
        }

        function showFBCookieInput() {
            pywebview.api.has_saved_cookie().then(function(has_cookie) {
                if (has_cookie) {
                    closeFBModal();
                    nav('https://www.facebook.com/reels/');
                } else {
                    document.getElementById('fb-action-buttons').style.display = 'none';
                    document.getElementById('fb-cookie-input-div').style.display = 'flex';
                }
            });
        }

        function hideFBCookieInput() {
            document.getElementById('fb-action-buttons').style.display = 'flex';
            document.getElementById('fb-cookie-input-div').style.display = 'none';
            document.getElementById('fb-cookie-val').value = '';
        }

        function saveAndGoFB() {
            let val = document.getElementById('fb-cookie-val').value.trim();
            if (val) {
                pywebview.api.save_cookie(val).then(() => {
                    closeFBModal();
                    nav('https://www.facebook.com/reels/');
                });
            } else {
                alert("Vui lòng nhập cookie!");
            }
        }

        function clearFBProfile() {
            pywebview.api.clear_webview_cookies().then(() => {
                alert("Đã xoá profile (cookies nội bộ)!");
            });
        }

        function clearFBCookieFile() {
            pywebview.api.clear_cookie_file().then(() => {
                alert("Đã xoá file Cookie!");
            });
        }

        function copyText(text) {
            const el = document.createElement('textarea');
            el.value = text;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert(t('copied') + ": " + text);
        }

        function t(key) {
            return I18N[currentLang][key] || key;
        }

        function applyLanguage() {
            document.getElementById('lang-btn').innerText = currentLang === 'vn' ? 'VN' : 'EN';
            document.querySelectorAll('[data-i18n]').forEach(el => {
                let key = el.getAttribute('data-i18n');
                if (el.tagName === 'INPUT' && el.type === 'text') {
                    el.placeholder = t(key);
                } else if (el.tagName === 'OPTION') {
                    el.innerText = t(key);
                } else {
                    el.innerHTML = t(key);
                }
            });
            // Update specific buttons that have dynamic state
            let themeBtn = document.getElementById('dash-btn-theme');
            if (themeBtn) {
                let isLight = document.body.classList.contains('theme-light');
                themeBtn.innerText = isLight ? t('btn_light') : t('btn_dark');
            }
            let transBtn = document.getElementById('dash-btn-transparency');
            if (transBtn) {
                transBtn.innerText = transBtn.innerText === 'Bật' || transBtn.innerText === 'On' ? t('btn_on') : t('btn_off');
            }
        }

        const SHAPE_NAMES = { 'fly': '🪰 Con ruồi', 'star': '⭐ Ngôi sao', 'smile': '😃 Mặt cười', 'dot': '⚫ Chấm đen' };
        function setTransformMode(shape) {
            let mode = 'transform_' + shape;
            pywebview.api.set_boss_mode(mode);
            document.getElementById('transform-modal').classList.remove('show');
            document.getElementById('dash-boss-mode').value = 'transform';
            let btn = document.getElementById('dash-transform-btn');
            if (btn) btn.style.display = 'block';
            let note = document.getElementById('dash-transform-note');
            if (note) { note.style.display = 'block'; note.innerText = SHAPE_NAMES[shape] || ''; }
        }
        function openCustomIconModal() {
            document.getElementById('transform-modal').classList.remove('show');
            document.getElementById('custom-icon-modal').classList.add('show');
            document.getElementById('customIconFile').value = '';
            document.getElementById('customIconFileName').innerText = 'Chưa chọn file';
            document.getElementById('customIconName').value = '';
        }

        function closeCustomIconModal() {
            document.getElementById('custom-icon-modal').classList.remove('show');
            document.getElementById('transform-modal').classList.add('show');
        }

        function saveCustomIcon() {
            let fileInput = document.getElementById('customIconFile');
            let nameInput = document.getElementById('customIconName').value.trim();
            if (!fileInput.files[0]) { alert(t('alert_png')); return; }
            if (!nameInput) { alert(t('alert_name')); return; }
            
            let file = fileInput.files[0];
            let reader = new FileReader();
            reader.onload = function(e) {
                let base64 = e.target.result.split(',')[1];
                pywebview.api.add_custom_icon(nameInput, base64).then((success) => {
                    if(success) {
                        closeCustomIconModal();
                        loadCustomIcons();
                    } else {
                        alert(t('alert_err'));
                    }
                });
            };
            reader.readAsDataURL(file);
        }

        function loadCustomIcons() {
            pywebview.api.get_custom_icons().then((icons) => {
                let container = document.getElementById('custom-icons-container');
                if (!container) return;
                container.innerHTML = '';
                for (let id in icons) {
                    let btn = document.createElement('button');
                    btn.className = 'setting-btn';
                    btn.style.justifyContent = 'center';
                    btn.innerHTML = `<span>${icons[id].name}</span> <span style="color: #ff5f56; cursor: pointer; position: absolute; right: 15px;" onclick="event.stopPropagation(); deleteCustomIcon('${id}')">✖</span>`;
                    btn.onclick = () => setTransformMode(id);
                    SHAPE_NAMES[id] = icons[id].name; // store to display
                    container.appendChild(btn);
                }
            });
        }
        
        function deleteCustomIcon(id) {
            if(confirm(t('alert_del'))) {
                pywebview.api.delete_custom_icon(id).then(() => loadCustomIcons());
            }
        }

        const QUOTES = {
            'vn': [
                "Cứ xem đi... làm gì có ai thấy",
                "Lướt lướt.. lướt rớt cả màn",
                "1 công cụ xem mọi nền tảng",
                "Sếp ko thấy đâu.. cứ xem tự nhiên",
                "Nếu thấy hữu ích với bạn hãy donate nhé",
                "Ko phải khều donate đâu mà thật..cần tiền duy trì lắm",
                "Cái App này đc làm bởi chungbruce",
                "Sếp tới kìa.. bấm Hotkey ngay",
                "Nhớ đọc kỹ hướng dẫn trc khi dùng",
                "App an toàn tuyệt đối dùng tẹt"
            ],
            'en': [
                "Just watch... nobody will see",
                "Scrolling... scrolling off the screen",
                "1 tool for all platforms",
                "Boss won't see... watch freely",
                "If you find this useful, please consider donating",
                "Not begging for donations, but seriously... need money for maintenance",
                "This App was made by chungbruce",
                "Boss is coming... press Hotkey now",
                "Remember to read the instructions carefully before using",
                "App is absolutely safe, use freely"
            ]
        };

        let currentBookmarks = [];
        window.addEventListener('pywebviewready', function() {
            loadBookmarks();
            loadCustomIcons();
            
            pywebview.api.get_hotkey().then(k => {
                if (k) document.getElementById('boss-key-input').value = k;
            });
            
            pywebview.api.get_boss_mode().then(mode => {
                let sel = document.getElementById('dash-boss-mode');
                let btn = document.getElementById('dash-transform-btn');
                let note = document.getElementById('dash-transform-note');
                if (sel) {
                    if (mode && mode.startsWith('transform_')) {
                        sel.value = 'transform';
                        if (btn) btn.style.display = 'block';
                        if (note) {
                            let shape = mode.split('_')[1];
                            note.style.display = 'block';
                            note.innerText = SHAPE_NAMES[shape] || '';
                        }
                    } else {
                        sel.value = mode || 'minimize';
                        if (btn) btn.style.display = 'none';
                        if (note) note.style.display = 'none';
                    }
                }
            });
            
            pywebview.api.get_fake_icon().then(val => {
                let sel = document.getElementById('dash-fake-icon');
                if (sel) sel.value = val || 'off';
            });
            
            pywebview.api.get_transparent_borders().then(val => {
                let btn = document.getElementById('dash-btn-transparency');
                if (val) {
                    btn.innerText = 'Bật';
                    btn.style.background = '#a6e3a1';
                    btn.style.color = '#11111b';
                }
            });
            
            pywebview.api.get_theme().then(theme => {
                if (theme === 'light') {
                    document.body.classList.add('theme-light');
                    let btn = document.getElementById('dash-btn-theme');
                    btn.innerText = '☀️ Sáng';
                    btn.style.background = 'rgba(0,0,0,0.1)';
                }
            });
            
            let quoteEl = document.getElementById('funny-text');
            function updateQuote() {
                let qs = QUOTES[currentLang] || QUOTES['vn'];
                quoteEl.innerText = qs[Math.floor(Math.random() * qs.length)];
            }
            updateQuote();
            setInterval(() => {
                quoteEl.style.opacity = 0;
                setTimeout(() => {
                    updateQuote();
                    quoteEl.style.opacity = 1;
                }, 500);
            }, 10000);
        });

        function loadBookmarks() {
            pywebview.api.get_bookmarks().then(bookmarks => {
                currentBookmarks = bookmarks;
                renderBookmarks();
            });
        }

        function renderBookmarks() {
            let filter = document.getElementById('bm-filter').value;
            let tbody = document.getElementById('bm-tbody');
            tbody.innerHTML = '';
            
            let filtered = currentBookmarks;
            if(filter !== 'All') {
                filtered = currentBookmarks.filter(b => b.platform === filter);
            }
            
            filtered.forEach((b, index) => {
                let tr = document.createElement('tr');
                let platformIcon = '🌍';
                if (b.platform === 'youtube') platformIcon = '▶️';
                else if (b.platform === 'netflix') platformIcon = '🎬';
                else if (b.platform === 'tiktok') platformIcon = '🎵';
                else if (b.platform === 'facebook') platformIcon = '📘';
                else if (b.platform === 'twitch') platformIcon = '🟪';
                else if (b.platform === 'vimeo') platformIcon = '🔵';
                
                let title = b.title ? b.title : b.url;
                if (title.length > 55) title = title.substring(0, 55) + '...';
                
                let timeStr = "";
                if (b.timestamp && b.timestamp > 0) {
                    let m = Math.floor(b.timestamp / 60);
                    let s = b.timestamp % 60;
                    timeStr = ` <span style="font-size:10px; background:#f38ba8; color:#11111b; padding:2px 4px; border-radius:4px; font-weight:bold; margin-left: 5px;">${m}:${s < 10 ? '0'+s : s}</span>`;
                }

                tr.innerHTML = `
                    <td style="text-align:center"><input type="checkbox" class="bm-chk" value="${b.url}"></td>
                    <td style="font-size: 16px; text-align:center;" title="${b.platform || 'Khác'}">${platformIcon}</td>
                    <td title="${b.title || b.url}"><a href="#" onclick="nav('${b.url}', ${b.timestamp || 0}, '${b.platform || ''}')" style="color:#89b4fa; text-decoration:none; font-weight:500;">${title}</a>${timeStr}</td>
                    <td style="text-align:center">
                        <button class="bm-action-btn" title="Xem lại" onclick="nav('${b.url}', ${b.timestamp || 0}, '${b.platform || ''}')" style="color: #a6e3a1; font-size: 14px; margin-right: 2px;">▶</button>
                        <button class="bm-action-btn" title="Xóa" onclick="deleteUrls(['${b.url}'])" style="color: #f38ba8; font-size: 14px;">✖</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            document.getElementById('bm-select-all').checked = false;
        }

        function toggleSelectAll(checked) {
            document.querySelectorAll('.bm-chk').forEach(cb => cb.checked = checked);
        }

        function deleteSelected() {
            let selected = Array.from(document.querySelectorAll('.bm-chk:checked')).map(cb => cb.value);
            if(selected.length > 0) {
                deleteUrls(selected);
            }
        }

        function deleteUrls(urls) {
            pywebview.api.delete_bookmarks(urls).then(() => {
                loadBookmarks();
            loadCustomIcons();
            }).catch(e => console.error(e));
        }

        function nav(url, timestamp, platform) {
            if (timestamp && timestamp > 0) {
                if (platform === 'youtube') {
                    if (url.includes('?')) url += `&t=${timestamp}s`;
                    else url += `?t=${timestamp}s`;
                }
            }
            pywebview.api.navigate_to(url);
        }

        document.getElementById('dash-btn-theme').addEventListener('click', (e) => {
            let body = document.body;
            body.classList.toggle('theme-light');
            let isLight = body.classList.contains('theme-light');
            e.target.innerText = isLight ? '☀️ Sáng' : '🌙 Tối';
            e.target.style.background = isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)';
            pywebview.api.set_theme(isLight ? 'light' : 'dark');
        });

        document.getElementById('boss-key-input').addEventListener('keydown', (e) => {
            e.preventDefault();
            let key = e.key;
            if (key === ' ') key = 'Space';
            if (key.length === 1) key = key.toUpperCase();
            document.getElementById('boss-key-input').value = key;
            pywebview.api.set_hotkey(key);
        });

        document.getElementById('dash-btn-transparency').addEventListener('click', (e) => {
            let isOn = e.target.innerText === 'Bật';
            isOn = !isOn;
            if (isOn) {
                e.target.innerText = 'Bật';
                e.target.style.background = '#a6e3a1';
                e.target.style.color = '#11111b';
            } else {
                e.target.innerText = 'Tắt';
                e.target.style.background = 'rgba(255,255,255,0.1)';
                e.target.style.color = 'var(--text)';
            }
            pywebview.api.set_transparent_borders(isOn);
        });

        document.getElementById('dash-boss-mode').addEventListener('change', (e) => {
            let btn = document.getElementById('dash-transform-btn');
            let note = document.getElementById('dash-transform-note');
            if (e.target.value === 'transform') {
                if (btn) btn.style.display = 'block';
                document.getElementById('transform-modal').classList.add('show');
            } else {
                if (btn) btn.style.display = 'none';
                if (note) note.style.display = 'none';
                pywebview.api.set_boss_mode(e.target.value);
            }
        });

        document.getElementById('dash-fake-icon').addEventListener('change', (e) => {
            pywebview.api.set_fake_icon(e.target.value);
        });

        function loadCustomPlatforms() {
            try {
                let custom = JSON.parse(localStorage.getItem('custom_platforms')) || [];
                let grid = document.getElementById('platform-grid');
                let addCard = document.getElementById('add-new-card');
                custom.forEach(p => {
                    let card = document.createElement('div');
                    card.className = 'card';
                    card.onclick = () => nav(p.url);
                    
                    let iconHtml = '';
                    if (p.icon) {
                        iconHtml = `<img class="icon-img" src="${p.icon}" alt="${p.name}">`;
                    } else {
                        iconHtml = `<div class="icon-img" style="font-size: 32px; display: flex; align-items: center; justify-content: center; color: var(--text); font-weight: bold; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">${p.name.charAt(0).toUpperCase()}</div>`;
                    }
                    
                    card.innerHTML = `${iconHtml}<div class="name">${p.name}</div>`;
                    grid.insertBefore(card, addCard);
                });
            } catch(e) {}
        }
        
        function saveNewPlatform() {
            let name = document.getElementById('add-name').value.trim();
            let url = document.getElementById('add-url').value.trim();
            let icon = document.getElementById('add-icon').value.trim();
            
            if (!url) {
                alert(t('alert_url'));
                return;
            }
            if (!name) {
                name = "New Platform";
            }
            if (!url.startsWith('http')) {
                url = 'https://' + url;
            }
            
            let custom = JSON.parse(localStorage.getItem('custom_platforms')) || [];
            let p = { name, url, icon };
            custom.push(p);
            localStorage.setItem('custom_platforms', JSON.stringify(custom));
            
            // Add to grid visually
            let grid = document.getElementById('platform-grid');
            let addCard = document.getElementById('add-new-card');
            let card = document.createElement('div');
            card.className = 'card';
            card.onclick = () => nav(p.url);
            
            let iconHtml = '';
            if (p.icon) {
                iconHtml = `<img class="icon-img" src="${p.icon}" alt="${p.name}">`;
            } else {
                iconHtml = `<div class="icon-img" style="font-size: 32px; display: flex; align-items: center; justify-content: center; color: var(--text); font-weight: bold; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">${p.name.charAt(0).toUpperCase()}</div>`;
            }
            
            card.innerHTML = `${iconHtml}<div class="name">${p.name}</div>`;
            grid.insertBefore(card, addCard);
            
            document.getElementById('add-modal').classList.remove('show');
            
            // Clear inputs
            document.getElementById('add-name').value = '';
            document.getElementById('add-url').value = '';
            document.getElementById('add-icon').value = '';
        }

        document.addEventListener("DOMContentLoaded", () => {
            applyLanguage();
            loadCustomPlatforms();
        });

    </script>
</body>
</html>
"""

def on_loaded(window):
    current_url = window.get_current_url()
    if not current_url:
        return
        
    print(f"Page loaded: {current_url}")
    
    if sys.platform == 'darwin':
        try:
            import webview.platforms.cocoa as cocoa
            def set_spaces():
                try:
                    for app_window in cocoa.AppKit.NSApp.windows():
                        behavior = app_window.collectionBehavior()
                        if not (behavior & cocoa.AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces):
                            app_window.setCollectionBehavior_(behavior | cocoa.AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces)
                except Exception as e:
                    print("Error setting spaces:", e)
            cocoa.AppHelper.callAfter(set_spaces)
        except Exception as e:
            print("Cocoa error:", e)
    
    if not current_url.startswith('data:'):
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
        window.evaluate_js(TITLEBAR_JS)

import sys
def get_base64_image(filename):
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = filename.split('.')[-1]
            mime = "image/jpeg" if ext in ['jpg', 'jpeg'] else f"image/{ext}"
            return f"data:{mime};base64,{b64}"
    return ""

if __name__ == '__main__':
    api = PipApi()
    
    html_content = DASHBOARD_HTML
    html_content = html_content.replace('##FB_ICON##', get_base64_image('facebookicon.svg.webp'))
    html_content = html_content.replace('##TIKTOK_ICON##', get_base64_image('tiktokicon.webp'))
    html_content = html_content.replace('##YT_ICON##', get_base64_image('youtubeicon.webp'))
    html_content = html_content.replace('##NETFLIX_ICON##', get_base64_image('netflexicon.webp'))
    html_content = html_content.replace('##DONATE_IMG##', get_base64_image('Donate-nen.png'))
    
    # Khởi tạo cửa sổ rỗng với HTML trang chủ (PIP Hub)
    window = webview.create_window(
        'PIP Hub', 
        html=html_content,
        frameless=True, 
        easy_drag=False, 
        width=480, 
        height=720, 
        on_top=False, 
        js_api=api,
        transparent=True
    )
    
    api.window = window
    
    # Đăng ký sự kiện khi trang tải xong (nạp UI vào Facebook)
    window.events.loaded += lambda: on_loaded(window)
    
    def handle_closing():
        url = window.get_current_url()
        if url and not url.startswith('data:'):
            window.load_html(html_content)
            window.resize(480, 720)
            window.on_top = False
            return False
        return True
        
    window.events.closing += handle_closing
    
    webview.start(private_mode=False)
