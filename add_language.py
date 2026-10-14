import re

with open('pip_desktop.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the EN/VN button to the dashboard
btn_html = """    <button class="top-btn" id="lang-btn" onclick="toggleLanguage()" style="right: 130px; color: #89dceb; font-size: 14px; font-weight: bold; width: 44px; height: 44px;" title="Ngôn ngữ / Language">VN</button>
    <button class="top-btn" onclick="document.getElementById('settings-modal').classList.add('show')" style="right: 20px; color: var(--text);" title="Cài đặt">⚙️</button>"""
content = re.sub(r'    <button class="top-btn" onclick="document.getElementById\(\'settings-modal\'\)\.classList\.add\(\'show\'\)" style="right: 20px; color: var\(--text\);" title="Cài đặt">⚙️</button>', btn_html, content)

# 2. Add translation script
script_addition = """
        const I18N = {
            'vn': {
                'title_settings': 'Cài Đặt Hệ Thống',
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
                'btn_dark': '🌙 Tối'
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
                'btn_dark': '🌙 Dark'
            }
        };

        let currentLang = localStorage.getItem('pip_lang') || 'vn';

        function toggleLanguage() {
            currentLang = currentLang === 'vn' ? 'en' : 'vn';
            localStorage.setItem('pip_lang', currentLang);
            applyLanguage();
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
                    // if it has child elements, we might overwrite them if not careful, but for this app it's mostly text
                    el.childNodes.forEach(child => {
                        if (child.nodeType === 3) { // text node
                            let text = child.textContent.trim();
                            if (text.length > 0) {
                                child.textContent = t(key);
                            }
                        }
                    });
                    if (el.childNodes.length === 0) el.innerText = t(key);
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
"""
content = content.replace("const SHAPE_NAMES = { 'fly': '🪰 Con ruồi', 'star': '⭐ Ngôi sao', 'smile': '😃 Mặt cười', 'dot': '⚫ Chấm đen' };", script_addition + "\n        const SHAPE_NAMES = { 'fly': '🪰 Con ruồi', 'star': '⭐ Ngôi sao', 'smile': '😃 Mặt cười', 'dot': '⚫ Chấm đen' };")

content = content.replace("loadCustomPlatforms();", "applyLanguage();\n            loadCustomPlatforms();")

# Now inject data-i18n attributes
replacements = {
    'Cài Đặt Hệ Thống': '<span data-i18n="title_settings">Cài Đặt Hệ Thống</span>',
    '<h3>Đã Lưu (Bookmarks)</h3>': '<h3><span data-i18n="title_bookmarks">Đã Lưu (Bookmarks)</span></h3>',
    '<h3>Thêm Nền Tảng</h3>': '<h3><span data-i18n="title_add_platform">Thêm Nền Tảng</span></h3>',
    '<h3>Chọn chế độ YouTube</h3>': '<h3><span data-i18n="title_yt">Chọn chế độ YouTube</span></h3>',
    '<h3 style="margin-bottom: 20px;">Chọn Hình Dáng</h3>': '<h3 style="margin-bottom: 20px;" data-i18n="title_shape">Chọn Hình Dáng</h3>',
    '<h3 style="margin-top: 0; margin-bottom: 20px;">Thêm Tuỳ chọn</h3>': '<h3 style="margin-top: 0; margin-bottom: 20px;" data-i18n="title_custom_shape">Thêm Tuỳ chọn</h3>',
    '<div class="name">Add Mới</div>': '<div class="name" data-i18n="add_new">Add Mới</div>',
    'placeholder="Tên"': 'placeholder="Tên" data-i18n="name"',
    'placeholder="Link URL: ( Bắt buộc)"': 'placeholder="Link URL: (Bắt buộc)" data-i18n="url_req"',
    'placeholder="Icon nền tảng: ( ko bắt buộc)"': 'placeholder="Icon nền tảng: ( không bắt buộc)" data-i18n="icon_opt"',
    'Lưu lại</button>': '<span data-i18n="save">Lưu lại</span></button>',
    '>Lưu lại</button>': ' data-i18n="save">Lưu lại</button>',
    'Đóng</button>': '<span data-i18n="close">Đóng</span></button>',
    '>Đóng</button>': ' data-i18n="close">Đóng</button>',
    '>Hủy</button>': ' data-i18n="cancel">Hủy</button>',
    '>Xóa</button>': ' data-i18n="delete">Xóa</button>',
    '>Tất cả</option>': ' data-i18n="all">Tất cả</option>',
    '<th style="width: 12%; text-align:center;">Nền tảng</th>': '<th style="width: 12%; text-align:center;" data-i18n="platform">Nền tảng</th>',
    '<th style="width: 65%;">Tên Video</th>': '<th style="width: 65%;" data-i18n="video_name">Tên Video</th>',
    '<th style="width: 15%; text-align:center;">Tùy chọn</th>': '<th style="width: 15%; text-align:center;" data-i18n="options">Tùy chọn</th>',
    '<span>Giao diện (Sáng/Tối)</span>': '<span data-i18n="theme">Giao diện (Sáng/Tối)</span>',
    '<span>Boss Key (Ẩn khẩn cấp)</span>': '<span data-i18n="boss_key">Boss Key (Ẩn khẩn cấp)</span>',
    '<span>Chế độ Boss Key</span>': '<span data-i18n="boss_key_mode">Chế độ Boss Key</span>',
    '<span>Fake icon Dưới thanh Dock</span>': '<span data-i18n="fake_icon">Fake icon Dưới thanh Dock</span>',
    '<span>Viền trong suốt (Ẩn viền đen)</span>': '<span data-i18n="transparent">Viền trong suốt (Ẩn viền đen)</span>',
    '>Thu nhỏ (Dock)</option>': ' data-i18n="minimize">Thu nhỏ (Dock)</option>',
    '>Mũi tên (Mép trái)</option>': ' data-i18n="arrow">Mũi tên (Mép trái)</option>',
    '>Tàng hình (Độ mờ 0%)</option>': ' data-i18n="invisible">Tàng hình (Độ mờ 0%)</option>',
    '>Biến hình 🪄</option>': ' data-i18n="transform">Biến hình 🪄</option>',
    '>Ghi chú 📝</option>': ' data-i18n="note_mode">Ghi chú 📝</option>',
    '>Tắt (Mặc định)</option>': ' data-i18n="off_default">Tắt (Mặc định)</option>',
    '* Lưu ý: Click vào ô trên rồi bấm phím muốn gán. Khi đang xem phim, bấm phím này để ẩn cửa sổ và dừng video, bấm lại để hiện ra. Cửa sổ phim phải đang được focus mới nhận phím.': '<span data-i18n="note_boss">* Lưu ý: Click vào ô trên rồi bấm phím muốn gán. Khi đang xem phim, bấm phím này để ẩn cửa sổ và dừng video, bấm lại để hiện ra. Cửa sổ phim phải đang được focus mới nhận phím.</span>',
    '🪰 Con ruồi</button>': '<span data-i18n="fly">🪰 Con ruồi</span></button>',
    '⭐ Ngôi sao</button>': '<span data-i18n="star">⭐ Ngôi sao</span></button>',
    '😃 Mặt cười</button>': '<span data-i18n="smile">😃 Mặt cười</span></button>',
    '⚫ Chấm đen</button>': '<span data-i18n="dot">⚫ Chấm đen</span></button>',
    '➕ Tuỳ chọn</button>': '<span data-i18n="custom">➕ Tuỳ chọn</span></button>',
    'Upload Ảnh (PNG)</button>': '<span data-i18n="upload_png">Upload Ảnh (PNG)</span></button>',
    '>Chưa chọn file</div>': ' data-i18n="no_file">Chưa chọn file</div>',
    'placeholder="Tên hiển thị (vd: Cục Shit)"': 'placeholder="Tên hiển thị (vd: Cục Shit)" data-i18n="display_name"'
}

for k, v in replacements.items():
    content = content.replace(k, v)

# Update alerts
content = content.replace("alert('Vui lòng chọn ảnh PNG')", "alert(t('alert_png'))")
content = content.replace("alert('Vui lòng nhập tên hiển thị')", "alert(t('alert_name'))")
content = content.replace("alert('Lỗi khi lưu icon!')", "alert(t('alert_err'))")
content = content.replace("confirm('Xoá icon này?')", "confirm(t('alert_del'))")
content = content.replace("alert(\"Vui lòng nhập Link URL!\")", "alert(t('alert_url'))")

with open('pip_desktop.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
