"""
About dialog for BowlBets application.
Displays user guide and application information.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextBrowser, QPushButton, QTabWidget, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os


class AboutDialog(QDialog):
    """Dialog showing application information and user guide."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About BowlBets")
        self.resize(800, 600)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Create tab widget
        tabs = QTabWidget()

        # About tab
        about_tab = self._create_about_tab()
        tabs.addTab(about_tab, "About")

        # User Guide tab
        guide_tab = self._create_guide_tab()
        tabs.addTab(guide_tab, "User Guide")

        layout.addWidget(tabs)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_about_tab(self):
        """Create the About tab with app information."""
        widget = QWidget()
        layout = QVBoxLayout()

        # App name and version
        title = QLabel("BowlBets")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("Version 2.0")
        version.setFont(QFont("Arial", 12))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(version)

        # Description
        desc = QLabel(
            "A college football bowl game betting tracker for two people.\n\n"
            "Track spreads, over/under bets, and compete with a friend "
            "throughout the bowl season!"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("margin: 20px; font-size: 12px;")
        layout.addWidget(desc)

        # Features
        features = QLabel(
            "<b>Features:</b><br>"
            "• Automatic game and odds syncing via College Football Data API<br>"
            "• Spread and Over/Under betting<br>"
            "• Automatic profit/loss calculation<br>"
            "• Series import/export for sharing with friends<br>"
            "• Manual odds entry and adjustment<br>"
            "• Team logos and venue information<br>"
            "• Live score tracking and updates"
        )
        features.setWordWrap(True)
        features.setStyleSheet("margin: 20px; font-size: 11px;")
        layout.addWidget(features)

        # Credits
        layout.addStretch()
        credits = QLabel(
            "Built with Python & PyQt6<br>"
            "Data provided by collegefootballdata.com<br><br>"
            "© 2024 BowlBets"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet("color: #888; font-size: 10px; margin-top: 20px;")
        layout.addWidget(credits)

        widget.setLayout(layout)
        return widget

    def _create_guide_tab(self):
        """Create the User Guide tab with documentation."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Text browser for displaying the guide
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        # Load user guide from file
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "USER_GUIDE.md")

        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_content = f.read()

            # Convert markdown to HTML (basic conversion)
            html_content = self._markdown_to_html(guide_content)
            browser.setHtml(html_content)
        else:
            browser.setHtml("<h2>User Guide Not Found</h2><p>The user guide file could not be located.</p>")

        layout.addWidget(browser)
        widget.setLayout(layout)
        return widget

    def _markdown_to_html(self, markdown_text):
        """
        Basic markdown to HTML conversion.
        Handles headers, bold, italic, lists, and code blocks.
        """
        html = '<html><head><style>'
        html += 'body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }'
        html += 'h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }'
        html += 'h2 { color: #34495e; border-bottom: 2px solid #bdc3c7; padding-bottom: 8px; margin-top: 30px; }'
        html += 'h3 { color: #7f8c8d; margin-top: 20px; }'
        html += 'code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }'
        html += 'pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }'
        html += 'ul, ol { margin-left: 20px; }'
        html += 'li { margin: 5px 0; }'
        html += 'strong { color: #2980b9; }'
        html += 'em { color: #8e44ad; }'
        html += 'hr { border: none; border-top: 1px solid #bdc3c7; margin: 30px 0; }'
        html += 'a { color: #3498db; text-decoration: none; }'
        html += 'a:hover { text-decoration: underline; }'
        html += 'blockquote { border-left: 4px solid #3498db; padding-left: 15px; margin-left: 0; color: #7f8c8d; }'
        html += '</style></head><body>'

        lines = markdown_text.split('\n')
        in_code_block = False
        in_unordered_list = False
        in_ordered_list = False

        for line in lines:
            # Code blocks
            if line.strip().startswith('```'):
                # Close any open lists
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False

                if in_code_block:
                    html += '</code></pre>'
                    in_code_block = False
                else:
                    html += '<pre><code>'
                    in_code_block = True
                continue

            if in_code_block:
                html += line + '\n'
                continue

            # Horizontal rules
            if line.strip() in ['---', '***', '___']:
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                html += '<hr>'
                continue

            # Headers
            if line.startswith('# '):
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                html += f'<h1>{line[2:]}</h1>'
                continue
            elif line.startswith('## '):
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                html += f'<h2>{line[3:]}</h2>'
                continue
            elif line.startswith('### '):
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                html += f'<h3>{line[4:]}</h3>'
                continue
            elif line.startswith('#### '):
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                html += f'<h4>{line[5:]}</h4>'
                continue

            # Unordered Lists
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                # Close ordered list if open
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                # Open unordered list if not already open
                if not in_unordered_list:
                    html += '<ul>'
                    in_unordered_list = True
                content = line.strip()[2:]
                content = self._process_inline_markdown(content)
                html += f'<li>{content}</li>'
                continue

            # Ordered Lists
            if line.strip() and line.strip()[0].isdigit() and '. ' in line.strip()[:4]:
                # Close unordered list if open
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                # Open ordered list if not already open
                if not in_ordered_list:
                    html += '<ol>'
                    in_ordered_list = True
                # Extract content after number and period
                content = line.strip().split('. ', 1)[1] if '. ' in line.strip() else line.strip()
                content = self._process_inline_markdown(content)
                html += f'<li>{content}</li>'
                continue

            # Regular paragraphs
            if line.strip():
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False
                content = self._process_inline_markdown(line)
                html += f'<p>{content}</p>'
                continue

            # Empty lines - close lists
            if not line.strip():
                if in_unordered_list:
                    html += '</ul>'
                    in_unordered_list = False
                if in_ordered_list:
                    html += '</ol>'
                    in_ordered_list = False

        # Close any remaining open tags
        if in_unordered_list:
            html += '</ul>'
        if in_ordered_list:
            html += '</ol>'
        if in_code_block:
            html += '</code></pre>'

        html += '</body></html>'
        return html

    def _process_inline_markdown(self, text):
        """Process inline markdown (bold, italic, code, links)."""
        import re

        # Links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

        # Bold **text** or __text__
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)

        # Italic *text* or _text_
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

        # Inline code `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

        return text
