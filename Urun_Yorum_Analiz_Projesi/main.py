# app_main.py
from datetime import datetime
import sys
import os
import random
import pandas as pd
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QWidget, QLabel, QLineEdit, QPushButton, QSpinBox, QStyleFactory,
                             QSizePolicy, QFrame, QGridLayout, QScrollArea, QProgressBar,
                             QMessageBox, QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGraphicsDropShadowEffect, QDialog, QListWidget,
                             QDialogButtonBox, QCheckBox)
from PyQt6.QtWidgets import QToolButton
from PyQt6.QtCore import QThread, pyqtSlot, Qt, QTimer, QElapsedTimer, QCoreApplication
from PyQt6.QtGui import QIcon, QColor, QPixmap, QTextCursor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import numpy as np
from pandas.core.base import Self
import threading
import collections

# Proje modüllerini import et
from config import *
# Yeni Hali
from product_scraper import ProductScraperWorker
from hepsiburada_scraper import HepsiburadaScraperWorker
from sentiment_analyzer import SentimentAnalyzerWorker
from review_categorizer import ReviewCategorizerWorker
from report_builder import ReportBuilderWorker



GLOBAL_STYLESHEET = """
    QMainWindow {
        background-color: #1e1e2e;
    }
    QWidget {
        color: #E0E0E0;
    }
    QLabel {
        color: #E0E0E0;
        background-color: transparent;
    }
    QLineEdit, QComboBox {
        background-color: #2a2a3e;
        color: #E0E0E0;
        border: 1px solid #404060;
        border-radius: 5px;
        padding: 6px;
    }
    QLineEdit:hover, QComboBox:hover {
        border-color: #64B5F6;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        image: url(down_arrow.png); /* Bu dosyanın projenizde olması gerekir */
    }
    QGroupBox {
        color: #E0E0E0;
        font-weight: bold;
        border: 1px solid #404060;
        border-radius: 8px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
        background-color: #1e1e2e;
    }

    #accordion_button {
        background-color: #2a2a3e;
        border: 1px solid #404060;
        color: #E0E0E0;
        border-radius: 4px;
        padding: 8px;
        text-align: left;
        font-weight: bold;
    }
    #accordion_button:disabled {
        background-color: #212121;
        color: #757575;
        border: 1px solid #424242;
    }
    #accordion_button:checked {
        background-color: #3c3c50;
        border-bottom: 1px solid #1e1e2e;
    }
    #accordion_content_area {
        background-color: #222230;
        border: 1px solid #404060;
        border-top: none;
        border-radius: 0 0 4px 4px;
    }
    #confirm_button {
        background-color: #4CAF50;
        color: white;
        padding: 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    #confirm_button:disabled {
        background-color: #a5d6a7;
        color: #d0d0d0;
    }
    /* Aktif kategori accordion için özel stil */
    AccordionWidget[active="true"] #accordion_button {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff9800, stop:0.5 #ffc107, stop:1 #ff9800);
        border: 2px solid #ff9800;
        color: #1a1a2e;
        box-shadow: 0 0 15px rgba(255, 152, 0, 0.5);
    }
    AccordionWidget[active="true"]:hover #accordion_button {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8f00, stop:0.5 #ffb300, stop:1 #ff8f00);
        box-shadow: 0 0 20px rgba(255, 152, 0, 0.7);
    }
    #start_scraping_button {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00bcd4, stop:1 #64ffda) !important;
        color: white !important;
        font-size: 15px;
        font-weight: bold;
        border: 2px solid #64ffda !important;
        border-radius: 8px;
        padding: 12px 0;
        box-shadow: 0 0 15px rgba(100, 255, 218, 0.5);
    }
    #start_scraping_button:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0069D9, stop:1 #00AEEF) !important;
        box-shadow: 0 0 20px rgba(100, 255, 218, 0.7);
    }
    #start_scraping_button:disabled {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #506A84, stop:1 #6a8099) !important;
        color: #B0B0B0 !important;
        border: 2px solid #506A84 !important;
        box-shadow: none;
    }
"""

class AccordionWidget(QWidget):
    """Açılır kapanır panel widget'ı"""
    # AccordionWidget sınıfı içindeki __init__ metodunu bununla değiştirin:

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.title = title
        self.toggle_button = QPushButton()  # Metni toggle_content içinde ayarlayacağız
        self.toggle_button.setObjectName("accordion_button")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_content)
        
        self.content_area = QWidget()
        self.content_area.setObjectName("accordion_content_area")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(15, 10, 15, 15)
        self.content_layout.setSpacing(10)

        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)
        
        # --- BAŞLANGIÇ DURUMUNU KESİN OLARAK AYARLA ---
        # Widget'ın başlangıçta KESİNLİKLE kapalı olmasını sağla.
        self.toggle_button.setChecked(False)
        # toggle_content() çağrısı, bu kapalı durumu arayüze yansıtacak
        # (içeriği gizleyecek ve buton metnini '▶' olarak ayarlayacak).
        self.toggle_content()

    def toggle_content(self):
        is_checked = self.toggle_button.isChecked()
        self.content_area.setVisible(is_checked)
        if is_checked:
            self.toggle_button.setText(f"▼ {self.title}")
        else:
            self.toggle_button.setText(f"▶ {self.title}")

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)



class UrunAnalizGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Ticaret Ürün Yorum Analiz Aracı")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon("logo.png"))
        self.setStyleSheet(GLOBAL_STYLESHEET)

        self.scraper_thread = None
        # State flags
        self.product_id = None
        self._files_exist_flags = {'comments': False, 'sentiment': False, 'categorization': False, 'report': False}
        self.is_processing = False
        self._is_collecting = False
        self._is_analyzing = False
        self._is_categorizing = False
        self._all_steps_completed = False
        self.current_step_active = 0

        self.parallel_progress = {'Trendyol': 0, 'Hepsiburada': 0}
        self.review_limit_per_source = 0
        self.pending_scrapers_lock = threading.Lock()
        self._total_reviews_collected = 0
        self._total_review_target = 0

        # Canlı ilerleme için yeni veri yapıları ve zamanlayıcı
        self.product_progress = {}
        self.product_names = {}
        self.progress_display_timer = QTimer(self)
        self.progress_display_timer.setInterval(300) # Arayüzü saniyede ~3 kez güncelle
        self.progress_display_timer.timeout.connect(self.update_live_feed_display)

        # Process flags
        self._comments_collected = False
        self._analysis_completed = False
        self._categorization_completed = False
        self._is_reporting = False
        self._report_completed = False
        self._charts_available = False

        # File paths
        self._comments_filepath = ""
        self._sentiment_filepath = ""
        self._categorization_filepath = ""

        # Worker and thread references
        self.scraper_thread = None
        self.scraper_worker = None
        self.sentiment_thread = None
        self.sentiment_worker = None
        self.categorizer_thread = None
        self.categorizer_worker = None
        self.report_thread = None
        self.report_worker = None

        # Timer setup for progress updates
        self._bert_timer = QTimer(self)
        self._bert_analysis_start_time = None
        self._bert_estimated_total_seconds = 0
        self._BERT_COMMENTS_PER_SECOND = 5.0

        self._categorization_plot_timer = QTimer(self)
        self._CATEGORIZATION_PLOT_UPDATE_INTERVAL_MS = 1000
        self._categorization_start_time = None

        self.REPORTING_ESTIMATED_SECONDS = 50

        # Chart references
        self._sentiment_pie_figure = None
        self._sentiment_pie_canvas = None
        self._sentiment_line_figure = None
        self._sentiment_line_canvas = None
        self._category_sentiment_figures = []
        self._category_sentiment_canvases = []

        # UI references
        self.step1_button = None
        self.step2_button = None
        self.step3_button = None
        self.step4_button = None
        self.line_label_1 = None
        self.line_label_2 = None
        self.line_label_3 = None
        self._step_buttons = []
        self._is_shutting_down = False
        self.category_inputs = []
        self.progress_timer = QElapsedTimer() # Geçen 

        # Raporlama için zamanlayıcı
        self.report_timer = QTimer(self)
        self.report_start_time = None
        self.REPORT_ESTIMATED_DURATION = 15 * 60  # 15 dakika
        self.current_step = 0
        
        # Gemini ürün seçimi için değişkenler
        self._selected_products = []  # Gemini'den gelen ürünler
        self._product_spinboxes = []  # Her ürün için SpinBox widget'ları
        self._products_container = None  # Ürünleri gösteren container
        self._products_accordion = None  # Ürünler accordion'u
        self._start_scraping_button = None  # Çekmeye başla butonu
        self._auto_mode = False
        self._trendyol_selected_products = [] # Trendyol'dan gelen ürünler
        self._hepsiburada_selected_products = [] # Hepsiburada'dan gelen ürünler

        self.category_accordions = {}

        self.init_ui()
        self.update_step_buttons()
        self.update_feature_buttons()

         # --- YENİ VE GARANTİLİ KOD ---
        # Program başlarken kategori bölümünün hem fonksiyonel hem de görsel
        # olarak kesinlikle devre dışı olmasını sağla.
        self.category_accordion.setEnabled(False)
        self.category_accordion.setProperty("active", False)
        self.category_accordion.style().polish(self.category_accordion)

    def log_message(self, message, level="info"):
        """Log mesajlarını status_label'a yazar."""
        prefixes = {
            "info": "ℹ️ ",
            "success": "✅ ",
            "warning": "⚠️ ",
            "error": "❌ "
        }
        prefix = prefixes.get(level, "")

        # Update status label and optional in-UI log (reviews_list) if present
        try:
            self.status_label.setText(f"{prefix}{message}")
        except Exception:
            # status_label might not be created yet during early init
            pass

        if hasattr(self, 'reviews_list') and self.reviews_list is not None:
            try:
                self.reviews_list.append(f"{prefix}{message}")
            except Exception:
                pass

    def _handle_scraper_status_update(self, message, source=None):
        """
        Scraper'dan gelen durum mesajlarını filtreleyerek kullanıcı dostu hale getirir.
        """
        # Eğer iki kaynak aynı anda çalışıyorsa ve henüz ilk anlamlı mesaj yayınlanmadıysa,
        # Hepsiburada kaynağına öncelik ver.
        try:
            if getattr(self, "_both_sources_active", False) and not getattr(self, "_first_preferred_source_seen", False):
                if source == "Hepsiburada":
                    self._first_preferred_source_seen = True
                elif source == "Trendyol":
                    # Trendyol'dan gelen ilk mesajı yut; Hepsiburada görününce işaretlenecek
                    return
        except Exception:
            pass
        # Eğer kaynak belirtilmemişse varsayılan bir değer kullan
        if source is None:
            prefix = "📊 İşlem"
        else:
            # Her kaynak için bir emoji ve başlık belirleyelim
            source_info = {
                "Trendyol": "📱 Trendyol",
                "Hepsiburada": "🛒 Hepsiburada"
            }

            # Gelen kaynak adı source_info'da varsa onu, yoksa doğrudan kaynağın adını kullan
            prefix = source_info.get(source, f"✨ {source}")

        # --- AKILLI FİLTRELEME ---
        # Sadece içinde "yorum", "toplandı", "bulundu" gibi anahtar kelimeler geçen
        # veya bir sayı içeren mesajları göstermeyi tercih edelim.
        # "scroll", "bekleniyor" gibi teknik detayları atlayalım.

        meaningful_keywords = ["yorum", "toplandı", "bulundu", "tamamlandı", "aranıyor"]

        # Gelen mesajın anlamlı olup olmadığını kontrol et
        is_meaningful = any(keyword in message for keyword in meaningful_keywords) or any(char.isdigit() for char in message)

        if is_meaningful:
            # Eğer mesaj anlamlıysa, status_label'ı güncelle
            self.status_label.setText(f"{prefix}: {message}")

        # Anlamlı değilse: Hiçbir şey yapma. Böylece ekranda en son anlamlı mesaj kalır.
        # Örneğin "5 yorum toplandı" mesajı, ardından gelen "scroll yapılıyor" mesajı tarafından ezilmez.

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        centering_layout = QHBoxLayout(central_widget)
        centering_layout.addStretch(1)

        content_container_widget = QWidget()
        content_container_widget.setFixedWidth(1100)
        centering_layout.addWidget(content_container_widget)
        centering_layout.addStretch(1)

        main_layout = QVBoxLayout(content_container_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        top_fixed_widget = QWidget()
        top_fixed_layout = QVBoxLayout(top_fixed_widget)
        top_fixed_layout.setContentsMargins(0, 0, 0, 0)
        top_fixed_layout.setSpacing(10)

        input_layout = QVBoxLayout()
        input_layout.setSpacing(5)

        # Marka Adı
        brand_layout = QHBoxLayout()
        brand_label = QLabel("Marka Adı:")
        brand_label.setMinimumWidth(100)
        brand_layout.addWidget(brand_label)
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Örn: Apple, Samsung, Xiaomi...")
        brand_layout.addWidget(self.brand_input)
        input_layout.addLayout(brand_layout)

        # Ürün Adı
        query_layout = QHBoxLayout()
        query_label = QLabel("Ürün Adı:")
        query_label.setMinimumWidth(100)
        query_layout.addWidget(query_label)
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Örn: iPhone 13 128GB, Samsung Galaxy...")
        query_layout.addWidget(self.product_name_input)
        input_layout.addLayout(query_layout)

        # Kategori
        category_layout = QHBoxLayout()
        category_label = QLabel("Kategori:")
        category_label.setMinimumWidth(100)
        category_layout.addWidget(category_label)
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Örn: Cep Telefonu, Laptop, Kulaklık...")
        category_layout.addWidget(self.category_input)
        input_layout.addLayout(category_layout)

        source_layout = QHBoxLayout()
        source_label = QLabel("E-Ticaret Sitesi:")
        source_label.setMinimumWidth(150)
        source_layout.addWidget(source_label)
        self.source_selection_combo = QComboBox()
        self.source_selection_combo.addItems(["Trendyol", "Hepsiburada", "Her ikisi"])
        source_layout.addWidget(self.source_selection_combo)
        input_layout.addLayout(source_layout)
        
        # Maks. Yorum Sayısı artık her ürün için ayrı belirleniyor (kaldırıldı)
        
        top_fixed_layout.addLayout(input_layout)

        # --- Akıllı Kategori Ayarları (Accordion) ---
        self.category_accordion = AccordionWidget("Akıllı Kategori Ayarları")
        category_content_widget = QWidget()

        # Üst araç çubuğu (sağ üstte Ekle/Çıkar)
        category_content_layout = QVBoxLayout(category_content_widget)
        top_controls_layout = QHBoxLayout()
        top_controls_layout.addStretch(1)
        # Modern ikon butonları (QToolButton) — dairesel, temaya uyumlu
        self.add_category_row_button = QToolButton()
        self.add_category_row_button.setObjectName("category_add_btn")
        self.add_category_row_button.setText("＋")  # tam genişlikli artı işareti
        self.add_category_row_button.setToolTip("Kategori ekle")
        self.add_category_row_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_category_row_button.setFixedSize(28, 28)

        self.remove_category_row_button = QToolButton()
        self.remove_category_row_button.setObjectName("category_remove_btn")
        self.remove_category_row_button.setText("−")  # tam genişlikli eksi işareti
        self.remove_category_row_button.setToolTip("Kategori çıkar")
        self.remove_category_row_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_category_row_button.setFixedSize(28, 28)

        # Stil: temayla uyumlu, gölgeli dairesel butonlar
        self.add_category_row_button.setStyleSheet(
            """
            QToolButton#category_add_btn {
                background-color: #2196F3; /* blue */
                color: #ffffff;
                border: 0px;
                border-radius: 14px;
                font-weight: 800;
                font-size: 16px;
            }
            QToolButton#category_add_btn:hover { background-color: #42A5F5; }
            QToolButton#category_add_btn:pressed { background-color: #1E88E5; }
            """
        )
        self.remove_category_row_button.setStyleSheet(
            """
            QToolButton#category_remove_btn {
                background-color: #E53935; /* red */
                color: #ffffff;
                border: 0px;
                border-radius: 14px;
                font-weight: 800;
                font-size: 16px;
            }
            QToolButton#category_remove_btn:hover { background-color: #EF5350; }
            QToolButton#category_remove_btn:pressed { background-color: #D32F2F; }
            """
        )
        self.add_category_row_button.clicked.connect(self.add_category_row)
        self.remove_category_row_button.clicked.connect(self.remove_category_row)
        top_controls_layout.addWidget(self.add_category_row_button)
        top_controls_layout.addWidget(self.remove_category_row_button)
        category_content_layout.addLayout(top_controls_layout)

        # Alanlar için grid
        category_grid_layout = QGridLayout()
        self.category_fields_grid = category_grid_layout  # Dinamik satırlar için referans
        self.category_inputs.clear()  # Listeyi temizle
        self.MAX_CATEGORY_ROWS = 10
        for i in range(3):
            name_input = QLineEdit()
            desc_input = QLineEdit()
            name_input.setPlaceholderText(f"Kategori {i+1} Adı")
            desc_input.setPlaceholderText(f"Kategori {i+1} Açıklaması")
            category_grid_layout.addWidget(name_input, i, 0)
            category_grid_layout.addWidget(desc_input, i, 1)
            self.category_inputs.append((name_input, desc_input))
        category_content_layout.addLayout(category_grid_layout)
        
        # Onay butonu en altta
        self.confirm_categories_button = QPushButton("✅ Kategorileri Onayla")
        self.confirm_categories_button.setObjectName("confirm_button")
        self.confirm_categories_button.clicked.connect(self.lock_categories)
        self.confirm_categories_button.setEnabled(False)
        category_content_layout.addWidget(self.confirm_categories_button)
        
        self.category_accordion.add_widget(category_content_widget)
        top_fixed_layout.addWidget(self.category_accordion)

        # --- Kontrol Butonları ---
        buttons_container_layout = QHBoxLayout()
        buttons_container_layout.setSpacing(15)

        self.step_buttons_layout = QHBoxLayout()
        self.step_buttons_layout.setSpacing(0)
        
        # Adım 1: Yorumları Çek
        self.step1_button = QPushButton("1. Yorumları Çek")
        self._step_buttons.append(self.step1_button)
        self.step_buttons_layout.addWidget(self.step1_button)
        self.step1_button.clicked.connect(self.start_step_1_scraping_only)

        self.line_label_1 = self.create_line_separator()
        self.step_buttons_layout.addWidget(self.line_label_1)

        self.step2_button = QPushButton("2. Duygu Analizi")
        self._step_buttons.append(self.step2_button)
        self.step_buttons_layout.addWidget(self.step2_button)
        self.step2_button.clicked.connect(self.start_step_2_sentiment_only)

        self.line_label_2 = self.create_line_separator()
        self.step_buttons_layout.addWidget(self.line_label_2)

        self.step3_button = QPushButton("3. Kategorize Et")
        self._step_buttons.append(self.step3_button)
        self.step_buttons_layout.addWidget(self.step3_button)
        self.step3_button.clicked.connect(self.start_step_3_categorization_only)

        self.line_label_3 = self.create_line_separator()
        self.step_buttons_layout.addWidget(self.line_label_3)

        self.step4_button = QPushButton("4. Rapor Oluştur")
        self._step_buttons.append(self.step4_button)
        self.step_buttons_layout.addWidget(self.step4_button)
        self.step4_button.clicked.connect(self.on_step4_button_clicked)

        # Tüm butonlara ortak stil ve boyut ayarı
        for button in self._step_buttons:
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            button.setMinimumHeight(50)

        buttons_container_layout.addLayout(self.step_buttons_layout)
        buttons_container_layout.addStretch(1)

        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setSpacing(10)
        control_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Durdur butonu
        # Durdur butonu
        self.stop_button = QPushButton("Durdur")
        self.stop_button.setFixedSize(90, 36)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 16px;
                border: 1px solid #c0392b;
                font-weight: bold;
                font-size: 13px;
                padding: 0px;
            }
        """)
        control_buttons_layout.addWidget(self.stop_button)

        # Temizle butonu
        self.clear_state_button = QPushButton("Temizle")
        self.clear_state_button.setObjectName("clear_button")
        self.clear_state_button.clicked.connect(self.clear_state_and_files)
        self.clear_state_button.setFixedSize(90, 36)
        self.clear_state_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 16px; /* Yüksekliğin yarısı */
                border: 1px solid #2980b9;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2471a3;
            }
            QPushButton:disabled {
                background-color: #a9cce3;
                border: 1px solid #92b6d0;
            }
        """)
        control_buttons_layout.addWidget(self.clear_state_button)

        buttons_container_layout.addLayout(control_buttons_layout)
        top_fixed_layout.addLayout(buttons_container_layout)

        # --- Gemini Ürün Seçimi Accordion ---
        self._products_accordion = AccordionWidget("🧠 Seçilen Ürünler (Gemini AI)")
        self._products_accordion.setVisible(False)  # Başlangıçta gizli
        
        products_content_widget = QWidget()
        products_content_layout = QVBoxLayout(products_content_widget)
        products_content_layout.setContentsMargins(15, 15, 15, 15)
        products_content_layout.setSpacing(10)
        
        # Açıklama etiketi
        products_info_label = QLabel(
            "✨ Gemini AI en uygun ürünleri seçti. Linklere tıklayarak kontrol edin ve her ürün için yorum sayısını belirleyin:"
        )
        products_info_label.setWordWrap(True)
        products_info_label.setStyleSheet("color: #64B5F6; font-size: 13px; margin-bottom: 10px;")
        products_content_layout.addWidget(products_info_label)
        
        # Ürünlerin gösterileceği container
        from PyQt6.QtWidgets import QScrollArea
        self._products_scroll = QScrollArea()
        self._products_scroll.setWidgetResizable(True)
        self._products_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._products_container = QWidget()
        self._products_container_layout = QVBoxLayout(self._products_container)
        self._products_container_layout.setSpacing(10)
        self._products_container_layout.setContentsMargins(0, 0, 0, 0)
        self._products_scroll.setWidget(self._products_container)
        self._products_scroll.setMinimumHeight(260)
        products_content_layout.addWidget(self._products_scroll)
        
        # Çekmeye Başla butonu
        self._start_scraping_button = QPushButton("Ürünleri Onayla")
        self._start_scraping_button.setObjectName("start_scraping_button")
        self._start_scraping_button.setMinimumHeight(39)
        self._start_scraping_button.setEnabled(False)  # Başlangıçta devre dışı - Gemini seçince aktif olur
        self._start_scraping_button.setVisible(True)  # Her zaman görünür
        self._start_scraping_button.clicked.connect(self.on_start_scraping_with_counts)
        products_content_layout.addWidget(self._start_scraping_button)
        
        self._products_accordion.add_widget(products_content_widget)
        top_fixed_layout.addWidget(self._products_accordion)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("global_progress_bar")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        top_fixed_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Durum: Hazır")
        self.status_label.setObjectName("status_label")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_label.setWordWrap(True)
        top_fixed_layout.addWidget(self.status_label)

        main_layout.addWidget(top_fixed_widget)
        top_fixed_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # --- ALT SONUÇ VE YARDIMCI ARAÇLAR ALANI ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVisible(False) # Başlangıçta gizli
        
        scroll_content = QWidget()
        self.scroll_area.setWidget(scroll_content)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # Anlık Yorum Gösterimi Paneli
        self.reviews_accordion = AccordionWidget("📝 Canlı Yorum Akışı")
        self.reviews_list = QTextEdit()
        self.reviews_list.setReadOnly(True)
        self.reviews_list.setMinimumHeight(150)
        self.reviews_list.setPlaceholderText("Yorumlar çekilirken burada görünecek...")
        self.reviews_accordion.add_widget(self.reviews_list)
        scroll_layout.addWidget(self.reviews_accordion)

        # Analiz Sonuçları Bölümü
        self.results_group = QGroupBox("📊 Analiz Sonuçları")
        self.results_group.setVisible(False)
        results_layout = QVBoxLayout(self.results_group)
        results_layout.setSpacing(15)

        # Genel Duygu Dağılımı
        self.sentiment_accordion = AccordionWidget("📈 Genel Duygu Dağılımı")
        self.sentiment_chart_label = QLabel()
        self.sentiment_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sentiment_accordion.add_widget(self.sentiment_chart_label)
        results_layout.addWidget(self.sentiment_accordion)

        # Kategori Dağılımı
        self.category_pie_accordion = AccordionWidget("📊 Kategori Dağılımı")
        self.category_pie_label = QLabel()
        self.category_pie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.category_pie_accordion.add_widget(self.category_pie_label)
        results_layout.addWidget(self.category_pie_accordion)

        # Kategorilere Göre Zaman Serisi - İYİLEŞTİRİLMİŞ VERSİYON
        self.category_ts_accordion = AccordionWidget("📉 Kategorilere Göre Zaman Analizi")
        self.category_ts_content = QWidget()
        self.category_ts_layout = QVBoxLayout(self.category_ts_content)
        self.category_ts_layout.setContentsMargins(15, 15, 15, 15)
        self.category_ts_layout.setSpacing(25)  # Grafikler arası daha fazla boşluk
        self.category_ts_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.category_ts_accordion.add_widget(self.category_ts_content)
        results_layout.addWidget(self.category_ts_accordion)

        # Grafik label'larını temizle
        self.sentiment_chart_label.clear()
        self.category_pie_label.clear()
        # Zaman serisi grafiklerini temizle
        while self.category_ts_layout.count():
            child = self.category_ts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        scroll_layout.addWidget(self.results_group)

        # Yardımcı Araçlar Paneli
        self.utils_accordion = AccordionWidget("🛠️ Yardımcı Araçlar")
        utils_container = QWidget()
        utils_layout = QHBoxLayout(utils_container)
        utils_layout.setContentsMargins(10, 10, 10, 10)
        utils_layout.setSpacing(15)
        
        # Yardımcı araç butonları - modern tasarım
        self.view_csv_button = QPushButton("�  Yorumları Görüntüle")
        self.view_charts_button = QPushButton("📊  Grafikleri Görüntüle")
        self.open_report_button = QPushButton("📋  Raporu Aç")

        # Modern buton stili
        button_style = """
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
                padding: 12px 20px;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """

        # Butonları ayarla
        for btn in [self.view_csv_button, self.view_charts_button, self.open_report_button]:
            btn.setMinimumHeight(45)
            btn.setStyleSheet(button_style)
            utils_layout.addWidget(btn)

        self.view_csv_button.clicked.connect(self.show_csv_viewer)
        self.view_charts_button.clicked.connect(self.show_chart_viewer)
        self.open_report_button.clicked.connect(self.open_word_report)

        self.utils_accordion.add_widget(utils_container)
        scroll_layout.addWidget(self.utils_accordion)

        scroll_layout.addStretch(1)

        main_layout.addWidget(self.scroll_area)
        main_layout.setStretchFactor(self.scroll_area, 1)

        main_layout.addLayout(scroll_layout)

        self.set_ui_processing_state(False)

    def create_line_separator(self):
        """Adım butonları arasına çizgi eklemek için yardımcı fonksiyon"""
        line = QLabel(">")
        line.setObjectName("step-separator")
        line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return line

    def get_user_categories(self, show_warning=True):
        """Kullanıcının girdiği kategorileri toplar ve formatlar."""
        categories = []
        if not hasattr(self, "category_inputs"):
            if show_warning:
                QMessageBox.warning(self, "Uyarı", "Kategori giriş alanları bulunamadı.")
            return []
        for name_input, desc_input in self.category_inputs:
            name = name_input.text().strip()
            desc = desc_input.text().strip()
            if name and desc:
                csv_col = "".join(filter(str.isalnum, name.replace(" ", "_")))
                categories.append({
                    "category": name, "csv_col": csv_col,
                    "display_name": name, "aciklama": desc
                })
        if not categories:
            if show_warning:
                QMessageBox.information(self, "Bilgi", "Özel kategori girilmedi. Varsayılan kategoriler kullanılacak.")
            return [
                {"category": "Genel", "csv_col": "Genel", "display_name": "Genel", "aciklama": "Ürünle ilgili genel yorumlar"},
                {"category": "Fiyat", "csv_col": "Fiyat", "display_name": "Fiyat", "aciklama": "Ürünün fiyatı ve değeri hakkındaki yorumlar"},
                {"category": "Kalite", "csv_col": "Kalite", "display_name": "Kalite", "aciklama": "Ürünün malzeme kalitesi, dayanıklılığı hakkındaki yorumlar."},
                {"category": "Kargo", "csv_col": "Kargo", "display_name": "Kargo", "aciklama": "Ürünün kargolanması, teslimat hızı ve paketlemesi hakkındaki yorumlar."},
            ]
        return categories
    # lock_categories fonksiyonunu bulun ve bu blokla değiştirin

    def lock_categories(self, show_warning_if_default=False):
        """Kullanıcının girdiği kategorileri doğrular, saklar, kilitler ve paneli kapatır."""
        try:
            categories = self.get_user_categories(show_warning=show_warning_if_default)
        except Exception as e:
            QMessageBox.warning(self, "Kategori Hatası", f"Kategoriler alınırken hata: {e}")
            return

        validated = []
        for c in categories:
            if isinstance(c, dict) and all(k in c for k in ['category', 'csv_col', 'display_name']):
                validated.append(c)

        if not validated:
            self.category_definitions = self.get_user_categories(show_warning=False)
        else:
            self.category_definitions = validated

        for name_input, desc_input in self.category_inputs:
            name_input.setEnabled(False)
            desc_input.setEnabled(False)

        self.confirm_categories_button.setEnabled(False)
        self.confirm_categories_button.setText("✔️ Kategoriler Değerlendirmeye Alındı")
        

        # --- YENİ EKLENEN KOD (OTOMATİK KAPANMA) ---
        # Kategoriler onaylandıktan sonra akordeon panelini otomatik olarak kapat.
        if self.category_accordion.toggle_button.isChecked():
            self.category_accordion.toggle_button.setChecked(False)
            self.category_accordion.toggle_content()
        # --- YENİ KOD SONU ---

        # Görsel durumu güncelle
        self.category_accordion.setProperty("active", False)
        self.category_accordion.style().polish(self.category_accordion)

    def clear_previous_results(self):
        """Yeni bir analize başlamadan önce eski grafikleri ve sonuçları temizler."""
        if hasattr(self, "reviews_list"):
            self.reviews_list.clear()
        
        # Check if results_group exists and hide it
        if hasattr(self, "results_group"):
            self.results_group.setVisible(False)

        # Check if scroll_area exists and hide it
        if hasattr(self, "scroll_area"):
            self.scroll_area.setVisible(False)
            
        if hasattr(self, "category_pie_label"):
            self.category_pie_label.clear()
            self.category_pie_label.setText("Grafik burada gösterilecek...")
            
        if hasattr(self, "sentiment_chart_label"):
            self.sentiment_chart_label.clear()
            self.sentiment_chart_label.setText("Grafik burada gösterilecek...")

        if hasattr(self, 'category_accordions'):
            for accordion_widget in self.category_accordions.values():
                accordion_widget.deleteLater()
            self.category_accordions.clear()
            
        # Clear the container for time-series charts
        if hasattr(self, 'category_ts_container'):
            # Delete all widgets inside the layout
            while self.category_ts_layout.count():
                child = self.category_ts_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        self.update_step_buttons()


    ### BU FONKSİYONU TAMAMEN DEĞİŞTİRİN ###

    def clear_state_and_files(self):
        """Programı başlangıç durumuna döndürür ve oluşturulan dosyaları temizler (GARANTİLİ VERSİYON)."""
        reply = QMessageBox.question(
            self, 
            "Onay", 
            "Bu işlem tüm analiz sonuçlarını ve dosyaları silecek. Emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stop_all_processes()
            
            # 1. ÖNCE TÜM DURUM BAYRAKLARINI SIFIRLA
            self.product_id = None
            self._files_exist_flags = {k: False for k in self._files_exist_flags}
            self.current_step = 0
            self._charts_available = False
            if hasattr(self, 'last_chart_buffers'):
                self.last_chart_buffers = {}
            
            # 2. ARAYÜZ ELEMANLARINI BAŞLANGIÇ DURUMUNA GETİR
            self.brand_input.clear()
            self.product_name_input.clear()
            self.category_input.clear()
            if hasattr(self, 'reviews_list'): self.reviews_list.clear()
            self.progress_bar.setValue(0)
            if hasattr(self, 'results_group'): self.results_group.setVisible(False)
            if hasattr(self, 'scroll_area'): self.scroll_area.setVisible(False)
            
            # Kategori giriş alanlarını sıfırla
            for name_input, desc_input in self.category_inputs:
                name_input.clear()
                desc_input.clear()
                name_input.setEnabled(True)
                desc_input.setEnabled(True)
            self.confirm_categories_button.setEnabled(False)
            self.confirm_categories_button.setText("✅ Kategorileri Onayla")
            
            # --- AKILLI KATEGORİ AYARLARINI SIFIRLAYAN KESİN ÇÖZÜM ---
            # ADIM A: Butonu fonksiyonel olarak DEVRE DIŞI BIRAK.
            self.category_accordion.setEnabled(False)
            
            # ADIM B: 'active' özelliğini kaldırarak parlak/turuncu stili kaldır.
            self.category_accordion.setProperty("active", False)
            
            # ADIM C: EN KRİTİK ADIM! Analiz sırasında eklenen özel (yeşil) stili TEMİZLE.
            # Bu olmazsa, buton devre dışı kalsa bile yeşil görünmeye devam eder.
            self.category_accordion.toggle_button.setStyleSheet("") 
            
            # ADIM D: Buton metnini ve durumunu başlangıç haline getir.
            if hasattr(self, '_original_category_title'):
                 self.category_accordion.toggle_button.setText(f"▶ {self._original_category_title}")
            else:
                 self.category_accordion.toggle_button.setText(f"▶ Akıllı Kategori Ayarları")
            # Panel açıksa kapat
            if self.category_accordion.toggle_button.isChecked():
                self.category_accordion.toggle_button.setChecked(False)
                self.category_accordion.toggle_content()
                
            # ADIM E: Qt'ye bu widget'ın stilini yeniden hesaplamasını emret.
            # Bu komut, stil sayfasındaki :disabled (sönük) kuralının uygulanmasını garantiler.
            self.category_accordion.style().polish(self.category_accordion)
            # --- BLOK SONU ---

            # 3. FİZİKSEL DOSYALARI SİL
            try:
                if os.path.exists(OUTPUT_DIR):
                    for file in os.listdir(OUTPUT_DIR):
                        # Güvenlik için bilinen uzantıları sil
                        if file.endswith(('.csv', '.png', '.docx', '.json')):
                            os.unlink(os.path.join(OUTPUT_DIR, file))
            except Exception as e:
                print(f"Dosyalar temizlenirken hata: {e}")
            
            # 4. SON OLARAK DİĞER BUTONLARI GÜNCELLE
            self.update_step_buttons()
            self.update_feature_buttons()
            
            self.status_label.setText("Tüm veriler temizlendi. Yeni analiz için hazır.")

    # set_ui_processing_state fonksiyonunu bulun ve bu blokla değiştirin:

    def set_ui_processing_state(self, is_processing):
        """
        TÜM arayüz elemanlarının durumunu yöneten MERKEZİ fonksiyondur.
        Tek yetkili budur.
        """
        self.is_processing = is_processing
        
        # --- Genel Input Alanları ---
        # İşlem varsa kilitlenir, yoksa açılır.
        self.brand_input.setEnabled(not is_processing)
        self.product_name_input.setEnabled(not is_processing)
        self.category_input.setEnabled(not is_processing)
        self.source_selection_combo.setEnabled(not is_processing)
        
        # --- KATEGORİ BÖLÜMÜNÜN MANTIĞI (EN KRİTİK KISIM) ---
        
        # Önce, kategorilerin daha önce kullanıcı tarafından kilitlenip kilitlenmediğini kontrol et.
        categories_locked = "Değerlendirmeye Alındı" in self.confirm_categories_button.text()
        
        # Şimdi, kategori bölümünün düzenlenebilir olması için GEREKLİ TÜM ŞARTLARI kontrol et:
        # Şart 1: Şu an bir işlem ÇALIŞMIYOR olmalı (is_processing == False).
        # Şart 2: Adım 1'in çıktısı olan 'yorumlar' dosyası MEVCUT olmalı.
        # Şart 3: Adım 2'nin çıktısı olan 'duygu analizi' dosyası MEVCUT olmalı.
        # Şart 4: Kullanıcı daha önce kategorileri ONAYLAMAMIŞ olmalı.
        can_edit_categories = (not is_processing and
                            self._files_exist_flags.get('comments', False) and
                            self._files_exist_flags.get('sentiment', False) and
                            not categories_locked)

        # Şartlar sağlandıysa, Kategori bölümünü hem fonksiyonel hem de görsel olarak etkinleştir.
        # (Kategori alanı zaten görünür durumda, sadece aktiflik durumu değişiyor)

        self.category_accordion.setEnabled(can_edit_categories)
        self.confirm_categories_button.setEnabled(can_edit_categories)
        # Temizle sonrası sönük görünümü garanti et: explicitly disable when false
        if not can_edit_categories:
            try:
                self.category_accordion.toggle_button.setEnabled(False)
                self.category_accordion.toggle_button.setEnabled(True)
            except Exception:
                pass
        
        # Görsel stili "parlak/aktif" olarak ayarlayan QSS özelliğini ayarla.
        self.category_accordion.setProperty("active", can_edit_categories)
        
        # <<< SORUNU KESİN ÇÖZEN KOMUTLAR >>>
        # Qt'ye, bu widget'ların stilini HEMEN şimdi yeniden okuyup uygulamasını emret.
        # Bu komut olmazsa, arayüz sönük kalır.
        self.category_accordion.style().polish(self.category_accordion)
        self.confirm_categories_button.style().polish(self.confirm_categories_button)
        
        # Kullanıcıya yol gösteren durum mesajını ayarla.
        if can_edit_categories:
            self.status_label.setText("✅ 2. Adım tamamlandı! Kategori ayarları AKTİF - kategorilerinizi belirleyebilirsiniz!")

            # Kategori accordion'unun başlığını da görsel olarak vurgulayalım
            # Önce mevcut başlığı saklayalım
            if not hasattr(self, '_original_category_title'):
                self._original_category_title = self.category_accordion.title

            # Aktif olduğunu belli etmek için başlığı değiştirelim
            self.category_accordion.toggle_button.setText(f"🔥 {self._original_category_title} (AKTİF)")
            
            # Butonun rengini yeşil yap
            self.category_accordion.toggle_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #4CAF50, stop:1 #66BB6A);
                    color: white;
                    padding: 10px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                    border: 2px solid #4CAF50;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #66BB6A, stop:1 #4CAF50);
                    border-color: #66BB6A;
                }
            """)
        else:
            # Başlığı pasif duruma geri getir
            if hasattr(self, '_original_category_title'):
                self.category_accordion.toggle_button.setText(f"▶ {self._original_category_title}")
            
            # Butonun rengini varsayılan stile döndür
            self.category_accordion.toggle_button.setStyleSheet("")
        
        # --- Diğer Kontrol Butonları ---
        self.stop_button.setEnabled(is_processing)
        self.clear_state_button.setEnabled(not is_processing)
        
        # Progress bar ve zamanlayıcıyı ayarla.
        if not is_processing:
            self.current_step = 0
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("%p%")
        else:
            # Her yeni işlem başladığında zamanlayıcıyı SIFIRLA ve BAŞLAT.
            # Bu, her adımın kendi süresinin doğru ölçülmesini sağlar.
            self.progress_timer.restart()

        # Son olarak, Adım butonlarının (1, 2, 3, 4) stilini güncelle.
        self.update_step_buttons()
        self.update_feature_buttons()
        
    def update_progress(self, current, total, process_name="İşleniyor"):
        """
        İlerleme çubuğunu, yüzdeyi ve kalan süreyi günceller.
        Adım 4 (Raporlama) için sabit bir süreye dayalı tahmin, diğer adımlar için
        dinamik, geçen süreye dayalı bir tahmin kullanır.
        """
        if total <= 0:
            self.progress_bar.setFormat(f"{process_name}: Başlatılıyor...")
            self.progress_bar.setValue(0)
            return

        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)

        remaining_seconds = 0

        # Adım 4 (Raporlama) için sabit süreye dayalı tahmin
        if self.current_step == 4:
            if total > 0:
                progress_fraction = current / total
                remaining_seconds = int(self.REPORTING_ESTIMATED_SECONDS * (1 - progress_fraction))
        # Diğer adımlar için dinamik tahmin
        else:
            elapsed_ms = self.progress_timer.elapsed()
            if current <= 0 or elapsed_ms < 1000:
                self.progress_bar.setFormat(f"{process_name}: {current}/{total} (%p%) - Kalan Süre: Hesaplanıyor...")
                return
            
            ms_per_item = elapsed_ms / current
            remaining_items = total - current
            remaining_ms = remaining_items * ms_per_item
            remaining_seconds = int(remaining_ms / 1000)

        # Ortak formatlama
        if remaining_seconds < 0:
            remaining_seconds = 0
        
        minutes, seconds = divmod(remaining_seconds, 60)
        time_str = f"Kalan Süre: ~{minutes:02d}:{seconds:02d}"
        
        self.progress_bar.setFormat(f"{process_name}: {current}/{total} (%p%) - {time_str}")

    def reset_ui(self, status_message=None):
        """UI'ı başlangıç durumuna döndürür."""
        self.set_ui_processing_state(False)
        if status_message:
            self.status_label.setText(status_message)
        self.progress_bar.setValue(0)

    def stop_all_processes(self):
        """Tüm çalışan işlemleri durdur"""
        self.is_processing = False
        if hasattr(self, 'scraper_worker') and self.scraper_worker: self.scraper_worker.stop()
        if hasattr(self, 'sentiment_worker') and self.sentiment_worker: self.sentiment_worker.stop()
        if hasattr(self, 'categorizer_worker') and self.categorizer_worker: self.categorizer_worker.stop()
        if hasattr(self, 'report_worker') and self.report_worker: self.report_worker.stop()
        if hasattr(self, 'scraper_thread') and self.scraper_thread and self.scraper_thread.isRunning(): self.scraper_thread.quit(); self.scraper_thread.wait(1000)
        if hasattr(self, 'sentiment_thread') and self.sentiment_thread and self.sentiment_thread.isRunning(): self.sentiment_thread.quit(); self.sentiment_thread.wait(1000)
        if hasattr(self, 'categorizer_thread') and self.categorizer_thread and self.categorizer_thread.isRunning(): self.categorizer_thread.quit(); self.categorizer_thread.wait(1000)
        if hasattr(self, 'report_thread') and self.report_thread and self.report_thread.isRunning(): self.report_thread.quit(); self.report_thread.wait(1000)
        self.reset_ui(status_message="🔴 İşlemler kullanıcı tarafından durduruldu.")

    # app_main.py dosyasındaki bu fonksiyonu bulun ve aşağıdakiyle DEĞİŞTİRİN:

    # app_main.py dosyasındaki bu fonksiyonu bulun ve aşağıdakiyle DEĞİŞTİRİN:

    def start_step_1_scraping_only(self):
        """Sadece 1. adımı çalıştırır ve sonraki adımların eski dosyalarını temizler."""
        brand_name = self.brand_input.text().strip()
        product_name = self.product_name_input.text().strip()
        category_name = self.category_input.text().strip()
        
        if not product_name:
            QMessageBox.warning(self, "Hata", "Lütfen bir ürün adı girin.")
            return

        # Yorum çekme işlemi başladığında kategori ayarları accordion'unu kapat
        self.category_accordion.toggle_button.setChecked(False)
        self.category_accordion.toggle_content()

        import re
        self.product_id = re.sub(r'[^\w\s-]', '', product_name).strip()
        self.product_id = re.sub(r'[-\s]+', '_', self.product_id)[:50] or "unknown_product"
        
        # Bu ürüne ait sonraki adımların çıktı dosyalarını bul ve sil
        try:
            sentiment_file = os.path.join(OUTPUT_DIR, SENTIMENT_FILE_TEMPLATE.format(product_id=self.product_id))
            categorization_file = os.path.join(OUTPUT_DIR, CATEGORIZATION_FILE_TEMPLATE.format(product_id=self.product_id))
            report_file = os.path.join(OUTPUT_DIR, REPORT_FILE_TEMPLATE.format(product_id=self.product_id))
            
            for f in [sentiment_file, categorization_file, report_file]:
                if os.path.exists(f): os.remove(f)
            
            self._files_exist_flags['sentiment'] = False
            self._files_exist_flags['categorization'] = False
            self._files_exist_flags['report'] = False
        except Exception as e:
            print(f"[UYARI] Eski dosyalar temizlenirken hata oluştu: {e}")
        
        self._auto_mode = False
        self.current_step = 1
        self.clear_previous_results()
        self.set_ui_processing_state(True)
        
        source = self.source_selection_combo.currentText()
        self.start_step_1_scraping(brand_name, product_name, category_name, source)

    def start_step_2_sentiment_only(self):
        """Sadece 2. adımı çalıştır"""
        if not self.product_id:
            QMessageBox.warning(self, "Hata", "Önce yorumları çekmelisiniz!")
            return
        input_path = os.path.join(OUTPUT_DIR, COMMENTS_FILE_TEMPLATE.format(product_id=self.product_id))
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "Hata", "Yorumlar dosyası bulunamadı! Önce yorumları çekin.")
            return
        self._auto_mode = False
        self.current_step = 2
        self.set_ui_processing_state(True)
        self.start_step_2_sentiment_analysis(input_path, self.product_name_input.text())

    # app_main.py dosyasındaki bu fonksiyonu bulun ve tamamen aşağıdakiyle DEĞİŞTİRİN:

    # start_step_3_categorization_only fonksiyonunu tamamen bununla değiştirin:

    def start_step_3_categorization_only(self):
        """Sadece 3. adımı çalıştırır ve kategori onayını zorunlu kılar."""
        if not self.product_id:
            QMessageBox.warning(self, "Hata", "Önce önceki adımları tamamlayın!")
            return
        input_path = os.path.join(OUTPUT_DIR, SENTIMENT_FILE_TEMPLATE.format(product_id=self.product_id))
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "Hata", "Duygu analizi dosyası bulunamadı! Önce duygu analizini yapın.")
            return

        # --- KULLANICI ONAYI KONTROLÜ (HATASIZ VERSİYON) ---
        if "Değerlendirmeye Alındı" not in self.confirm_categories_button.text():
            reply = QMessageBox.question(
                self,
                "Kategori Onayı",
                "Özel kategoriler onaylanmadı.\n\n"
                "Varsayılan kategorilerle (Kalite, Fiyat vb.) devam edilsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            # Kullanıcı "Evet" dışında bir seçim yaparsa (Hayır veya pencereyi kapatırsa)
            # işlemi KESİNLİKLE durdur.
            if reply != QMessageBox.StandardButton.Yes:
                self.status_label.setText("⚠️ Kategorizasyon işlemi iptal edildi. Lütfen kategorileri onaylayın veya varsayılanları kabul edin.")
                self.set_ui_processing_state(False)
                return  # <-- FONKSİYONDAN TAMAMEN ÇIKAR

            # Kullanıcı "Evet" dediyse, varsayılanları kilitle ve devam et
            self.lock_categories(show_warning_if_default=False)

        # --- KONTROL SONU ---

        self._auto_mode = False
        self.current_step = 3
        self.set_ui_processing_state(True)
        self.start_step_3_categorization(input_path, self.product_name_input.text())

    def start_step_4_report_only(self):
        """Sadece 4. adımı (tam rapor oluşturmayı) çalıştırır."""
        if not self.product_id:
            QMessageBox.warning(self, "Hata", "Önce önceki adımları tamamlayın!")
            return
        input_path = os.path.join(OUTPUT_DIR, CATEGORIZATION_FILE_TEMPLATE.format(product_id=self.product_id))
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "Hata", "Kategorileme dosyası bulunamadı! Önce kategorizasyonu yapın.")
            return
        self._auto_mode = False
        self.current_step = 4
        self.set_ui_processing_state(True)
        # charts_only=False → tam rapor
        self.start_step_4_report_generation(input_path, self.product_name_input.text(), charts_only=False)


    def start_step_4_report_generation(self, input_path, product_title, charts_only=False):
        """Grafik veya tam rapor oluşturma işlemini DURUMA GÖRE akıllı etiketleme ile başlatır."""
        
        # --- YAZI SORUNUNU KESİN OLARAK ÇÖZEN MANTIK ---
        # Parametre yerine, o anki aktif adıma göre karar veriyoruz.
        if charts_only is False:
            # Kullanıcı 4. butona bastı, bu bir RAPORLAMA işlemidir.
            progress_label = "Rapor"
            status_message = "LLM'den rapor metinleri alınıyor..."
            is_charts_only_mode = False
        else:
            # İşlem 3. adımdan sonra otomatik tetiklendi, bu bir ANALİZ (grafik oluşturma) işlemidir.
            progress_label = "Analiz"
            status_message = "Analiz sonuçları için grafikler hazırlanıyor..."
            is_charts_only_mode = True
        
        self.progress_bar.setValue(0)
        self.status_label.setText(status_message)
        # --- MANTIK SONU ---

        user_categories = self.get_user_categories(show_warning=False)
        
        self.report_thread = QThread()
        # Worker'a doğru modu (sadece grafik mi, tam rapor mu) iletiyoruz.
        self.report_worker = ReportBuilderWorker(input_path, product_title, user_categories, self.product_id, charts_only=is_charts_only_mode)
        self.report_worker.moveToThread(self.report_thread)

        self.report_worker.charts_generated.connect(self.on_charts_generated)
        
        # Progress bar'a doğru etiketi (Analiz veya Rapor) gönderir.
        self.report_worker.progress_updated.connect(
            lambda cur, tot: self.update_progress(cur, tot, progress_label)
        )
        
        self.report_worker.error.connect(self.on_process_error)
        self.report_worker.status_message.connect(self.status_label.setText)

        if is_charts_only_mode:
            def on_charts_only_finished(dummy_path):
                self.set_ui_processing_state(False)
            self.report_worker.finished.connect(on_charts_only_finished)
        else:
            self.report_worker.finished.connect(self.on_report_finished)
        
        self.report_thread.started.connect(self.report_worker.run)
        self.report_thread.start()

    def on_step4_button_clicked(self):
        """4. adım butonuna basıldığında etiketi kesin 'Rapor' olarak ayarla ve başlat."""
        if not self.product_id:
            QMessageBox.warning(self, "Hata", "Önce önceki adımları tamamlayın!")
            return
        input_path = os.path.join(OUTPUT_DIR, CATEGORIZATION_FILE_TEMPLATE.format(product_id=self.product_id))
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "Hata", "Kategorileme dosyası bulunamadı! Önce kategorilemeyi yapın.")
            return
        self.current_step = 4
        # Burada charts_only=False göndererek 'Rapor' etiketini garanti ediyoruz
        self.start_step_4_report_generation(input_path, self.product_name_input.text(), charts_only=False)

    def start_full_analysis(self):
        brand_name = self.brand_input.text().strip()
        product_name = self.product_name_input.text().strip()
        category_name = self.category_input.text().strip()
        
        if not product_name:
            QMessageBox.warning(self, "Hata", "Lütfen bir ürün adı girin.")
            return
        self.category_settings_group.setChecked(False)
        self.clear_previous_results()
        import re
        self.product_id = re.sub(r'[^\w\s-]', '', product_name).strip()
        self.product_id = re.sub(r'[-\s]+', '_', self.product_id)[:50] or "unknown_product"

        self._auto_mode = True
        self.current_step = 1
        self.set_ui_processing_state(True)
        source = self.source_selection_combo.currentText()
        self.start_step_1_scraping(brand_name, product_name, category_name, source)

    def start_step_1_scraping(self, brand_name, product_name, category_name, source=None):
        # Scroll area'yı görünür yap ve yorum listesini temizle
        self.scroll_area.setVisible(True)

        self.clear_previous_results()
        self.set_ui_processing_state(True)
        self.log_message("Adım 1: Yorum çekme işlemi başlatılıyor...")

        # Kaynak belirleme (UI'dan veya parametreden)
        source_text = source if source is not None else self.source_selection_combo.currentText()
        source_key = (source_text or "").strip().lower()

        # 'Her ikisi' seçildiyse paralel moda geç
        if source_key == "her ikisi":
            review_limit = 200
            self.start_parallel_scraping(brand_name, product_name, category_name, review_limit)
            return

        # Tek kaynak modu için de canlı akışı başlat
        self.product_progress = collections.OrderedDict()
        self.product_names.clear()
        self.scroll_area.setVisible(True)
        self.reviews_accordion.toggle_button.setChecked(True)
        self.reviews_accordion.toggle_content()
        self.reviews_list.clear()
        self.progress_display_timer.start()

        # Tek kaynak için uygun worker'ı seç
        if source_key == "hepsiburada":
            self.scraper_worker = HepsiburadaScraperWorker(brand_name, product_name, category_name)
        else:  # Varsayılan Trendyol
            self.scraper_worker = ProductScraperWorker(brand_name, product_name, category_name)

        # Thread oluşturma ve bağlama
        self.scraper_thread = QThread()
        self.scraper_worker.moveToThread(self.scraper_thread)

        # === Sinyalleri Bağla ===
        self.scraper_worker.scraping_finished.connect(lambda reviews, title, source=source_text: self.on_scraping_finished(reviews, title, source))
        self.scraper_worker.scraping_error.connect(self.on_process_error)
        self.scraper_worker.status_update.connect(lambda msg: self._handle_scraper_status_update(msg, source_text))
        if hasattr(self.scraper_worker, 'product_switching'):
            self.scraper_worker.product_switching.connect(self.on_product_switching)
        if hasattr(self.scraper_worker, 'products_selected'):
            self.scraper_worker.products_selected.connect(self.on_products_selected)
        if hasattr(self.scraper_worker, 'product_list_updated'):
            self.scraper_worker.product_list_updated.connect(self.on_products_selected)
        
        # Her yorum bulunduğunda merkezi ilerleme fonksiyonunu çağır
        self.scraper_worker.review_found.connect(self.on_any_review_found)

        # Thread'i başlat
        self.scraper_thread.started.connect(self.scraper_worker.run)
        self.scraper_thread.start()
    
    # Mevcut fonksiyonu bu blok ile tamamen değiştirin
    def start_parallel_scraping(self, brand_name, product_name, category_name, review_limit):
        """Hem Trendyol hem Hepsiburada için paralel scraping (Zamanlayıcı Tabanlı UI)"""
        # Veri yapılarını ve zamanlayıcıyı başlat
        self.product_progress = collections.OrderedDict()
        self.review_limit_per_source = review_limit
        self.pending_scrapers = ["Trendyol", "Hepsiburada"]
        self.scraping_results = {}
        self._both_sources_active = True
        self._first_preferred_source_seen = False
        
        # Worker'ları ve thread'leri hazırla
        self.trendyol_thread = QThread()
        self.trendyol_worker = ProductScraperWorker(brand_name, product_name, category_name)
        self.trendyol_worker.moveToThread(self.trendyol_thread)
        
        self.hepsiburada_thread = QThread()
        self.hepsiburada_worker = HepsiburadaScraperWorker(brand_name, product_name, category_name)
        self.hepsiburada_worker.moveToThread(self.hepsiburada_thread)
        
        # Sinyalleri bağla
        self.trendyol_worker.scraping_finished.connect(lambda r, t: self.on_parallel_scraping_finished(r, t, "Trendyol"))
        self.hepsiburada_worker.scraping_finished.connect(lambda r, t: self.on_parallel_scraping_finished(r, t, "Hepsiburada"))
        self.trendyol_worker.scraping_error.connect(lambda e: self.on_parallel_scraping_error(e, "Trendyol"))
        self.hepsiburada_worker.scraping_error.connect(lambda e: self.on_parallel_scraping_error(e, "Hepsiburada"))
        self.trendyol_worker.status_update.connect(lambda m: self._handle_scraper_status_update(m, "Trendyol"))
        self.hepsiburada_worker.status_update.connect(lambda m: self._handle_scraper_status_update(m, "Hepsiburada"))
        self.trendyol_worker.products_selected.connect(self.on_trendyol_products_selected)
        self.hepsiburada_worker.products_selected.connect(self.on_hepsiburada_products_selected)
        self.trendyol_worker.product_list_updated.connect(self.check_and_combine_products)
        self.hepsiburada_worker.product_list_updated.connect(self.check_and_combine_products)
        self.trendyol_worker.product_switching.connect(self.on_product_switching)
        self.hepsiburada_worker.product_switching.connect(self.on_product_switching)
        self.trendyol_worker.review_found.connect(self.on_any_review_found)
        self.hepsiburada_worker.review_found.connect(self.on_any_review_found)
        
        # Thread'leri başlat
        self.trendyol_thread.started.connect(self.trendyol_worker.run)
        self.hepsiburada_thread.started.connect(self.hepsiburada_worker.run)
        self.hepsiburada_thread.start()
        self.trendyol_thread.start()

        # UI'ı hazırla ve zamanlayıcıyı başlat
        self.scroll_area.setVisible(True)
        self.reviews_accordion.toggle_button.setChecked(True)
        self.reviews_accordion.toggle_content()
        self.reviews_list.clear()
        self.progress_display_timer.start()
    
    def update_live_feed_display(self):
        """Zamanlayıcı tarafından tetiklenir, product_progress verisine göre arayüzü günceller."""
        if not self.is_processing:
            return

        display_lines = []
        # Hedef 1: Benzersiz ID takibi için OrderedDict kullanmaya devam et
        for key, progress in self.product_progress.items():
            try:
                source, product_id = key.split(' - ', 1)
                # ID'ye göre ürün adını al
                product_name_text = self.product_names.get(str(product_id), f"ID: {product_id}")
                
                # Hedef 2: Kaynak adını [Kaynak] formatında göster
                source_prefix = f"[{source}]"
                
                display_text = f"{source_prefix} {product_name_text}: {progress}"
                display_lines.append(display_text)
            except (ValueError, IndexError):
                display_lines.append(f"Hatalı ilerleme verisi: {key}")

        # Hedef 3: Arayüzü tek seferde güncelleyerek yavaşlamayı ve bozulmayı önle
        self.reviews_list.setText("\n".join(display_lines))

        scrollbar = self.reviews_list.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def on_parallel_scraping_finished(self, reviews, product_title, source):
        """Paralel scraping'den bir kaynak tamamlandığında (Sadece veri günceller)"""
        with self.pending_scrapers_lock:
            if source not in self.pending_scrapers:
                return
            self.pending_scrapers.remove(source)
            is_last_scraper = not self.pending_scrapers

        self.scraping_results[source] = {'reviews': reviews, 'title': product_title}

        # Canlı akıştaki [150/150] gibi son durumu koru, "Tamamlandı" yazma.

        # Eğer bu son scraper ise, zamanlayıcıyı durdur ve son birleştirme işlemini çağır
        if is_last_scraper:
            self.progress_display_timer.stop()
            # Son bir UI güncellemesi yap ve birleştirme mesajını ekle
            self.update_live_feed_display()
            self.reviews_list.append("\nHer iki kaynak da tamamlandı. Sonuçlar birleştiriliyor...")
            QApplication.processEvents()
            self.combine_parallel_results()
    
    def on_parallel_scraping_error(self, error_message, source):
        """Paralel scraping'de hata olduğunda (Sadece veri günceller)"""
        with self.pending_scrapers_lock:
            if source not in self.pending_scrapers:
                return
            self.pending_scrapers.remove(source)
            is_last_scraper = not self.pending_scrapers

        self.scraping_results[source] = {'reviews': [], 'title': f"Hata - {source}"}

        # Hata veren ürünlerin durumunu güncelle (modeli güncelle, UI'ı değil)
        for key in list(self.product_progress.keys()):
            if key.startswith(source):
                self.product_progress[key] = f"❌ Hata: {error_message[:50]}..."

        # Eğer bu son scraper ise, zamanlayıcıyı durdur ve son birleştirme işlemini çağır
        if is_last_scraper:
            self.progress_display_timer.stop()
            # Son bir UI güncellemesi yap ve birleştirme mesajını ekle
            self.update_live_feed_display()
            self.reviews_list.append("\nHer iki kaynak da tamamlandı. Sonuçlar birleştiriliyor...")
            QApplication.processEvents()
            self.combine_parallel_results()
    

    
    def combine_parallel_results(self):
        """Paralel scraping sonuçlarını birleştir (GÜVENLİ VERSİYON)"""
        all_reviews = []
        combined_title = ""
        
        # Sonuçları birleştir
        for source, data in self.scraping_results.items():
            original_reviews = data.get('reviews', [])
            title = data.get('title', '')
            
            # Orijinal listeyi değiştirmek yerine YENİ bir liste oluştur
            processed_reviews_for_source = []
            for review in original_reviews:
                if isinstance(review, dict):
                    processed_review = review.copy()
                    processed_review['source'] = source
                    processed_reviews_for_source.append(processed_review)
                else:
                    # Eğer string ise, standart bir sözlük yapısı oluştur
                    processed_reviews_for_source.append({
                        'review': str(review),
                        'rating': 0,
                        'date': 'Tarih bilinmiyor',
                        'source': source
                    })
            
            all_reviews.extend(processed_reviews_for_source)
            
            # Başlığı oluştur
            if combined_title and title:
                combined_title += f" & {title}"
            elif title:
                combined_title = title
    
        # Toplam sonucu göster
        total_reviews = len(all_reviews)
        trendyol_count = len(self.scraping_results.get('Trendyol', {}).get('reviews', []))
        hepsiburada_count = len(self.scraping_results.get('Hepsiburada', {}).get('reviews', []))

        status_text = (f"✅ Toplam {total_reviews} yorum toplandı "
                       f"(Trendyol: {trendyol_count}, Hepsiburada: {hepsiburada_count})")
        self.status_label.setText(status_text)
        
        # Birleşik sonucu işle
        self.on_scraping_finished(all_reviews, combined_title, "Her ikisi")

    def on_products_selected(self, products):
        """Gemini AI ürünleri seçtiğinde çalışır"""
        # Listeyi kopyala (orijinali değiştirmemek için)
        products_copy = []
        for product in products:
            # Her ürünün kopyasını oluştur
            product_copy = product.copy()
            
            # Tek kaynak modunda 'source' bilgisi ekle
            source_selection = self.source_selection_combo.currentText()
            if 'source' not in product_copy or product_copy.get('source') is None:
                if source_selection != "Her ikisi":
                    product_copy['source'] = source_selection
            
            products_copy.append(product_copy)
        
        # Listeyi kaydet
        self._selected_products = products_copy
        
        # UI'ı yenile
        self._refresh_products_ui()
    
    def _refresh_products_ui(self):
        """Mevcut self._selected_products listesini kullanarak UI'ı yeniler (silme işlemi sonrası)"""
        self._product_spinboxes = []
        
        # Eski ürünleri temizle
        while self._products_container_layout.count():
            child = self._products_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Her ürün için UI oluştur (self._selected_products listesini kullan)
        for idx, product in enumerate(self._selected_products):
            # Ürün frame
            product_frame = QFrame()
            product_frame.setObjectName("product_item_frame")
            product_frame.setStyleSheet("""
                QFrame#product_item_frame {
                    background-color: #2a2a3e;
                    border: 1px solid #404060;
                    border-radius: 8px;
                    padding: 10px;
                }
                QFrame#product_item_frame:hover {
                    border-color: #64B5F6;
                }
            """)
            
            product_layout = QVBoxLayout(product_frame)
            product_layout.setSpacing(8)
            
            # Ürün Adı (tam ve görünür - WordWrap ile düzgün görünsün)
            name_label = QLabel(product['name'])
            name_label.setWordWrap(True)  # Uzun metinleri alt satıra sar
            name_label.setMinimumHeight(40)  # ✅ En least 2 satır için yeterli yükseklik
            name_label.setMaximumWidth(900)  # ✅ Maximum genişlik ile sarmalama garantisi
            name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)  # ✅ Dinamik büyüme
            name_label.setStyleSheet("color: #E0E0E0; font-size: 13px; font-weight: bold; padding: 5px 0;")
            product_layout.addWidget(name_label)

            # --- Üst Satır: Link ve Sil Butonu ---
            top_row_layout = QHBoxLayout()

            # Kaynağa göre uygun link metni
            is_hb = ("hepsiburada" in product['url'].lower())
            link_text = "Hepsiburada'dan Görüntüle" if is_hb else "Trendyol'da Görüntüle"
            tooltip_site = "Hepsiburada'da" if is_hb else "Trendyol'da"
            url_label = QLabel(f'<a href="{product["url"]}" style="color: #64B5F6; text-decoration: none; font-size: 12px;">🔗 {link_text}</a>')
            url_label.setOpenExternalLinks(True)
            url_label.setToolTip(f"Tıklayarak {tooltip_site} görüntüleyin")
            top_row_layout.addWidget(url_label)
            top_row_layout.addStretch()

            # Sil Butonu
            delete_button = QPushButton("🗑️")
            delete_button.setFixedSize(30, 30)
            delete_button.setToolTip("Bu ürünü listeden kaldır")
            delete_button.setStyleSheet("background-color: #E53935; border-radius: 15px; font-size: 16px; color: white;")
            delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
            # Ürünün benzersiz ID'sini kullan (indeks yerine)
            product_unique_id = product.get('id') or product.get('sku') or f"product_{idx}"
            delete_button.clicked.connect(lambda checked=False, pid=product_unique_id, btn=delete_button: self._safe_handle_product_removal_by_id(pid, btn))
            top_row_layout.addWidget(delete_button)
            
            product_layout.addLayout(top_row_layout)
            
            # Yorum sayısı kontrolleri
            control_layout = QHBoxLayout()
            control_layout.setSpacing(10)
            control_layout.setContentsMargins(20, 0, 0, 0)
            
            review_count = product.get('review_count', 0)
            
            if review_count > 0:
                count_label = QLabel(f"Yorum Sayısı ({review_count} mevcut):")
            else:
                count_label = QLabel("Yorum Sayısı (Yorum Yok):")
            count_label.setStyleSheet("color: #B0B0B0; font-size: 12px;")
            control_layout.addWidget(count_label)
            
            # SpinBox
            spinbox = QSpinBox()
            if review_count > 0:
                spinbox.setRange(1, review_count)
                spinbox.setValue(review_count) # Varsayılan olarak maksimum yorum sayısını ayarla
            else:
                spinbox.setRange(0, 0)
                spinbox.setValue(0)
                spinbox.setEnabled(False)
            spinbox.setSingleStep(10)
            spinbox.setMinimumWidth(100)
            spinbox.setStyleSheet("""
                QSpinBox {
                    background-color: #1e1e2e;
                    color: #E0E0E0;
                    border: 1px solid #404060;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 13px;
                }
                QSpinBox:hover {
                    border-color: #64B5F6;
                }
            """)
            control_layout.addWidget(spinbox)
            control_layout.addStretch()
            
            product_layout.addLayout(control_layout)
            
            self._product_spinboxes.append(spinbox)
            self._products_container_layout.addWidget(product_frame)
        
        # Boşluk kalmamsı için layout'a stretch ekle
        self._products_container_layout.addStretch()
        
        # Ürün varsa accordion'u göster, yoksa gizle
        if len(self._selected_products) > 0:
            # Accordion'u göster ve aç
            self._products_accordion.setVisible(True)
            self._products_accordion.setEnabled(True)
            self._products_accordion.toggle_button.setChecked(True)
            self._products_accordion.toggle_content()
            
            # Butonu aktif hale getir (olası stil/cache sorunlarına karşı güvenli aktivasyon)
            try:
                self._start_scraping_button.setEnabled(True)
                self._start_scraping_button.setDisabled(False)
                self._start_scraping_button.setVisible(True)
                self._start_scraping_button.update()
                QCoreApplication.processEvents()
                # Etkinleştirmeyi event-loop sonrasına da planla (çifte güvence)
                QTimer.singleShot(0, lambda: self._start_scraping_button.setEnabled(True))
            except Exception:
                pass
            
            # Status güncelle
            self.status_label.setText(f"✅ {len(self._selected_products)} ürün hazır. Linklere tıklayıp kontrol edin, yorum sayılarını ayarlayın ve 'Ürünleri Onayla'ya tıklayın.")
            # Üstte global processing state bu butonu yanlışlıkla kilitlemesin diye merkezî kilitten muaf tut
            try:
                self._start_scraping_button.setEnabled(True)
                self._start_scraping_button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            except Exception:
                pass
        else:
            # Hiç ürün kalmadıysa accordion'u gizle ve butonu devre dışı bırak
            self._products_accordion.setVisible(False)
            try:
                self._start_scraping_button.setEnabled(False)
            except Exception:
                pass
            self.status_label.setText("⚠️ Hiç ürün kalmadı. Lütfen yeni arama yapın.")

    def on_trendyol_products_selected(self, products):
        """Trendyol'dan gelen ürünleri saklar ve birleştirme kontrolünü tetikler."""
        self._trendyol_selected_products = products
        self.check_and_combine_products()

    def on_hepsiburada_products_selected(self, products):
        """Hepsiburada'dan gelen ürünleri saklar ve birleştirme kontrolünü tetikler."""
        self._hepsiburada_selected_products = products
        self.check_and_combine_products()

    def check_and_combine_products(self):
        """Hem Trendyol hem Hepsiburada ürünleri geldiğinde birleştirir ve UI'a gönderir."""
        # Sadece paralel modda ve her iki kaynaktan da ürünler geldiyse birleştir
        # ÖNEMLI: Boş liste kontrolü - her ikisi de DOLU olmalı
        if self.source_selection_combo.currentText().lower() == "her ikisi" and \
           len(self._trendyol_selected_products) > 0 and \
           len(self._hepsiburada_selected_products) > 0:
            
            combined_products = []
            # Trendyol ürünlerini ekle
            for p in self._trendyol_selected_products:
                # Trendyol ürünlerine 'source' bilgisini ekle
                p_copy = p.copy()
                p_copy['source'] = 'Trendyol'
                combined_products.append(p_copy)
            
            # Hepsiburada ürünlerini ekle
            for p in self._hepsiburada_selected_products:
                # Hepsiburada ürünlerine 'source' bilgisini ekle
                p_copy = p.copy()
                p_copy['source'] = 'Hepsiburada'
                combined_products.append(p_copy)
            
            # Ürünleri karıştır (Trendyol ve Hepsiburada ürünleri karma gelsin)
            random.shuffle(combined_products)
            
            # Birleştirilmiş ürünleri UI'a gönder
            self.on_products_selected(combined_products)
            
            # Birleştirme sonrası geçici listeleri temizle
            self._trendyol_selected_products = []
            self._hepsiburada_selected_products = []

    def _safe_handle_product_removal_by_id(self, product_id, button):
        """ID/SKU ile güvenli ürün silme - butonu devre dışı bırakır"""
        # Butonu hemen devre dışı bırak (çift tıklama önlemi)
        if button:
            button.setEnabled(False)
        
        # Ürünü ID/SKU ile bul
        index_to_remove = -1
        for idx, product in enumerate(self._selected_products):
            prod_id = product.get('id') or product.get('sku')
            if prod_id == product_id:
                index_to_remove = idx
                break
        
        if index_to_remove == -1:
            self.status_label.setText(f"❌ Ürün bulunamadı (ID: {product_id})")
            return
        
        # Asıl silme işlemini çağır
        self._handle_product_removal(index_to_remove)
    
    def _safe_handle_product_removal(self, index_to_remove, button):
        """Güvenli ürün silme - butonu devre dışı bırakır (ESKİ - indeks ile)"""
        # Butonu hemen devre dışı bırak (çift tıklama önlemi)
        if button:
            button.setEnabled(False)
        
        # Asıl silme işlemini çağır
        self._handle_product_removal(index_to_remove)
    
    def _handle_product_removal(self, index_to_remove):
        """Kullanıcı bir ürünü silmek istediğinde çalışır."""
        
        # Güvenlik kontrolü: Liste ve indeks geçerliliği
        if not self._selected_products:
            self.status_label.setText("❌ Hata: Ürün listesi boş.")
            return
            
        if not (0 <= index_to_remove < len(self._selected_products)):
            self.status_label.setText(f"❌ Hata: Geçersiz ürün indeksi ({index_to_remove}/{len(self._selected_products)}).")
            return

        try:
            product_to_remove = self._selected_products[index_to_remove]
            product_name = product_to_remove.get('name', 'Bilinmeyen Ürün')
            product_source = product_to_remove.get('source')
        except (IndexError, KeyError) as e:
            self.status_label.setText(f"❌ Hata: Ürün verisi alınamadı: {e}")
            return
        
        reply = QMessageBox.question(self, "Ürünü Kaldır", 
                                       f"<b>{product_name[:80]}...</b><br><br>Bu ürünü listeden kaldırmak istediğinizden emin misiniz?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 1. KULLANICI GİRDİĞİ YORUM SAYILARINI SAKLA
                # Kullanıcı değer girdiyse, diğer ürünlerin değerleri korunmalı
                old_spinbox_values = []
                try:
                    for i, spinbox in enumerate(self._product_spinboxes):
                        if i != index_to_remove:
                            old_spinbox_values.append(spinbox.value())
                except Exception as e:
                    # Spinbox listesi geçersiz olabilir
                    old_spinbox_values = []
                
                # 2. UI LİSTESİNDEN SİL (Güvenli şekilde)
                try:
                    if 0 <= index_to_remove < len(self._selected_products):
                        self._selected_products.pop(index_to_remove)
                    else:
                        self.status_label.setText(f"❌ Hata: Geçersiz indeks ({index_to_remove})")
                        return
                except IndexError as e:
                    self.status_label.setText(f"❌ Silme hatası: {e}")
                    return
                
                # 3. UI'I YENİDEN OLUŞTUR (güncellenmiş liste ile - sadece UI yenileme)
                self._refresh_products_ui()
                
                # 4. ESKI DEĞERLERI GERİ YÜKLE (Güvenli şekilde)
                try:
                    for idx, value in enumerate(old_spinbox_values):
                        if idx < len(self._product_spinboxes):
                            self._product_spinboxes[idx].setValue(value)
                except Exception as e:
                    # Değer yükleme başarısız olsa bile devam et
                    pass
                
                # 5. BAŞARI MESAJI
                self.status_label.setText(f"✅ '{product_name[:50]}...' ürünü listeden kaldırıldı.")

            except Exception as e:
                self.status_label.setText(f"❌ Ürün kaldırılırken bir hata oluştu: {e}")    
    def on_start_scraping_with_counts(self):
        """Kullanıcı yorum sayılarını girip 'Ürünleri Onayla'ya bastığında"""
        if not self._selected_products:
            QMessageBox.warning(self, "Hata", "Önce ürün seçimi yapılmalı!")
            return
        
        review_counts = {} # Tekli mod için
        total_target = 0
        
        source_selection = self.source_selection_combo.currentText().lower()
        is_parallel_mode = (source_selection == "her ikisi")
        
        # Paralel mod için kaynak bazlı sayaçlar
        if is_parallel_mode:
            trendyol_review_counts = {}
            hepsiburada_review_counts = {}

        # Arayüzdeki her ürün için ID ve sayacı eşleştir
        for idx, product in enumerate(self._selected_products):
            spinbox = self._product_spinboxes[idx]
            count = spinbox.value()
            total_target += count
            
            # Benzersiz ID'yi al (Trendyol için 'id', Hepsiburada için 'sku')
            product_unique_id = product.get('id') or product.get('sku')
            if not product_unique_id:
                continue # ID yoksa bu ürünü atla (güvenlik önlemi)

            if is_parallel_mode:
                if product.get('source') == 'Trendyol':
                    trendyol_review_counts[product_unique_id] = count
                elif product.get('source') == 'Hepsiburada':
                    hepsiburada_review_counts[product_unique_id] = count
            else:
                # Tekli mod
                review_counts[product_unique_id] = count
        
        self._total_review_target = total_target
        self._total_reviews_collected = 0
        
        try:
            self.scroll_area.setVisible(True)
            self.reviews_accordion.setVisible(True)
            if not self.reviews_accordion.toggle_button.isChecked():
                self.reviews_accordion.toggle_button.setChecked(True)
                self.reviews_accordion.toggle_content()
            self.reviews_list.clear()
        except Exception:
            pass
        
        self._start_scraping_button.setEnabled(False)
        self._start_scraping_button.setText("⏳ Çekiliyor...")
        
        if self._products_accordion.toggle_button.isChecked():
            self._products_accordion.toggle_button.setChecked(False)
            self._products_accordion.toggle_content()
        
        # ID:sayı sözlüğünü ilgili worker'a gönder
        if is_parallel_mode:
            if hasattr(self, 'trendyol_worker') and self.trendyol_worker:
                self.trendyol_worker.set_review_counts_and_start(trendyol_review_counts)
            if hasattr(self, 'hepsiburada_worker') and self.hepsiburada_worker:
                self.hepsiburada_worker.set_review_counts_and_start(hepsiburada_review_counts)
        else:
            if hasattr(self, 'scraper_worker') and self.scraper_worker:
                self.scraper_worker.set_review_counts_and_start(review_counts)
            else:
                self.status_label.setText("❌ Worker bulunamadı! İşlem başlatılamıyor.")
                return
        
        self.status_label.setText(f"🚀 {len(self._selected_products)} üründen toplam {total_target} yorum çekiliyor...")
        self.update_progress(0, self._total_review_target, "Yorumlar Çekiliyor")
    
    def on_any_review_found(self, source, product_id, count_for_product, total_for_product):
        """Herhangi bir worker'dan bir yorum bulunduğunda tetiklenir. Sadece veri modelini günceller."""
        self._total_reviews_collected += 1
        self.update_progress(self._total_reviews_collected, self._total_review_target, "Yorumlar Çekiliyor")

        # Benzersiz ID kullanarak anahtar oluştur
        product_key = f"{source} - {str(product_id)}"
        progress_text = f"[{count_for_product} / {total_for_product}]"
        self.product_progress[product_key] = progress_text

    def on_product_switching(self, source, product_id, product_name, current, total):
        """Ürün değişimi - canlı akış için veri yapısını hazırlar."""
        # Görüntüleme için ürün adını ID ile eşleştirerek sakla
        self.product_names[str(product_id)] = product_name[:60]
        
        # Benzersiz ID kullanarak anahtar oluştur
        product_key = f"{source} - {str(product_id)}"
        if product_key not in self.product_progress:
            self.product_progress[product_key] = "⏳ Başlatılıyor..."
        
        # Hedef 2: Kaynak adını [Kaynak] formatında göster
        source_prefix = f"[{source}]"
        self.status_label.setText(f"{source_prefix} Ürün {current}/{total}: {product_name[:70]}...")

        # Scrollbar'ı en altta tut
        scrollbar = self.reviews_list.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents() # Arayüzün hemen güncellenmesini sağla
        

    def on_scraping_finished(self, reviews, product_title, source="Trendyol"):
        """
        Scraping bittiğinde çalışır ve gelen farklı formatlardaki yorumları
        standart bir formata dönüştürüp CSV'ye kaydeder.
        """
        self.progress_display_timer.stop() # Canlı akış zamanlayıcısını durdur
        if hasattr(self, '_start_scraping_button'):
            self._start_scraping_button.setText("Ürünleri Onayla")
            self._start_scraping_button.setEnabled(False)
        
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Adım 1 tamamlandı: {len(reviews)} yorum çekildi. CSV dosyası oluşturuluyor...")
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, COMMENTS_FILE_TEMPLATE.format(product_id=self.product_id))

        standardized_reviews = []
        if reviews:
            for review_data in reviews:
                # Her kaynak için standart bir sözlük yapısı oluştur
                standard_review = {
                    'product': 'Bilinmiyor',
                    'text': '',
                    'rating': 0,
                    'date': 'Tarih bilinmiyor',
                    'source': source
                }
                
                if isinstance(review_data, dict):
                    # Hepsiburada formatı: {'review': {'content': '...'}, 'star': 5, 'createdAt': '...'}
                    if 'review' in review_data and isinstance(review_data.get('review'), dict):
                        standard_review['text'] = review_data['review'].get('content', '')
                        standard_review['rating'] = review_data.get('star', 0)
                        timestamp_str = review_data.get('createdAt', '')
                        if timestamp_str:
                            try:
                                standard_review['date'] = datetime.fromisoformat(timestamp_str.replace('+00:00', '')).strftime('%Y-%m-%d')
                            except:
                                standard_review['date'] = timestamp_str.split('T')[0]
                        standard_review['source'] = review_data.get('source', 'Hepsiburada')
                        standard_review['product'] = review_data.get('product', product_title)

                    # Trendyol formatı: {'text': '...', 'rating': 5, 'date': '...'}
                    elif 'text' in review_data:
                        standard_review['text'] = review_data.get('text', '')
                        standard_review['rating'] = review_data.get('rating', 0)
                        standard_review['date'] = review_data.get('date', 'Tarih bilinmiyor')
                        standard_review['source'] = review_data.get('source', 'Trendyol')
                        standard_review['product'] = review_data.get('product', product_title)

                elif isinstance(review_data, str):
                    standard_review['text'] = review_data
                
                # Sadece metni olan yorumları ekle
                if standard_review['text']:
                    standardized_reviews.append(standard_review)

        if not standardized_reviews:
            self.status_label.setText("✅ İşlem tamamlandı ancak CSV'ye yazılacak geçerli yorum bulunamadı.")
            self.set_ui_processing_state(False)
            return

        try:
            df = pd.DataFrame(standardized_reviews)
            # Sütun sırasını belirle
            df = df[['text', 'date']]
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            self.status_label.setText(f"✅ {len(df)} yorum CSV dosyasına kaydedildi: {os.path.basename(output_path)}")
        except Exception as e:
            self.on_process_error(f"CSV dosyası kaydedilemedi: {e}")
            return

        self._comments_filepath = output_path
        self._files_exist_flags['comments'] = True
        self.update_step_buttons()
        self.update_feature_buttons()
        
        if self._auto_mode:
            self.current_step = 2
            self.start_step_2_sentiment_analysis(output_path, product_title)
        else:
            self.set_ui_processing_state(False)
            QMessageBox.information(self, "Adım 1 Tamamlandı", f"{len(standardized_reviews)} yorum başarıyla çekildi ve kaydedildi. Şimdi 'Duygu Analizi' adımına geçebilirsiniz.")
        
        if not self._auto_mode:
            self.status_label.setText("💡 Yorumlar çekildi. Duygu analizi tamamlandıktan sonra kategori ayarları aktif olacak.")

    def start_step_2_sentiment_analysis(self, input_path, product_title):
        self.progress_bar.setFormat("Duygu Analizi... %p%")
        self.progress_bar.setValue(0)
        self.status_label.setText("Duygu analizi yapılıyor, bu işlem biraz sürebilir...")
        
        self.sentiment_thread = QThread()
        self.sentiment_worker = SentimentAnalyzerWorker(input_path)
        self.sentiment_worker.moveToThread(self.sentiment_thread)
        
        self.sentiment_worker.analysis_finished.connect(lambda path: self.on_sentiment_finished(path, product_title))
        self.sentiment_worker.analysis_error.connect(self.on_process_error)
        self.sentiment_worker.status_update.connect(self.status_label.setText)
        
        # --- DEĞİŞİKLİK BURADA ---
        # Artık sadece yüzdeyi değil, kalan süreyi de gösteriyoruz.
        # Not: Bu satırın çalışması için SentimentAnalyzerWorker'ın (mevcut, toplam) şeklinde veri göndermesi gerekir.
        # Eğer sadece yüzde gönderiyorsa, bu satırı bir önceki gibi .setValue ile değiştirmeniz gerekebilir.
        # Ancak kodunuzun genel yapısına göre bu en doğru yaklaşımdır.
        self.sentiment_worker.progress_update.connect(lambda current, total: self.update_progress(current, total, "Duygu Analizi"))
        
        self.sentiment_thread.started.connect(self.sentiment_worker.run)
        self.sentiment_thread.start()


    def on_sentiment_finished(self, output_path, product_title):
        """Duygu analizi bittiğinde çalışır, durumu günceller ve merkezi UI fonksiyonunu çağırır."""
        self.progress_bar.setValue(100)
        
        # 1. Adım: Sadece uygulamanın İÇ DURUMUNU güncelle. Arayüze dokunma.
        self._sentiment_filepath = output_path
        self._files_exist_flags['sentiment'] = True

        # 2. Adım: Diğer butonların durumunu yeni dosya bilgisine göre güncelle.
        self.update_step_buttons()
        self.update_feature_buttons()
        
        # 3. Adım: Otomatik modda mıyız, değil miyiz kontrol et.
        if self._auto_mode:
            # Otomatik moddaysa, bir sonraki adıma geç.
            self.current_step = 3
            self.start_step_3_categorization(output_path, product_title)
        else:
            # Otomatik modda DEĞİLSEK:
            # Arayüzü yönetme işini TEK YETKİLİ fonksiyona devret.
            # Bu fonksiyon, hem işlem durumunu bitirecek hem de Kategori bölümünü
            # GEREKİYORSA (yani yorum dosyası da varsa) yakacaktır.
            self.set_ui_processing_state(False)


            # Kullanıcıya bilgi ver. set_ui_processing_state kendi bilgi mesajını zaten gösterecek
            # ama bu ek mesaj da faydalı.
            self.status_label.setText("Duygu analizi tamamlandı! Artık kategori ayarlarını yapabilirsiniz.")
            QMessageBox.information(self, "Adım 2 Tamamlandı",
                                    "Duygu analizi tamamlandı. Şimdi 'Akıllı Kategori Ayarları' bölümünden "
                                    "kategorilerinizi belirleyip 'Kategorize Et' adımına geçebilirsiniz.")

    # start_step_3_categorization_only fonksiyonunu tamamen bununla değiştirin:

    def start_step_3_categorization_only(self):
        """Sadece 3. adımı çalıştırır ve kategori onayını zorunlu kılar."""
        if not self.product_id:
            QMessageBox.warning(self, "Hata", "Önce önceki adımları tamamlayın!")
            return
        input_path = os.path.join(OUTPUT_DIR, SENTIMENT_FILE_TEMPLATE.format(product_id=self.product_id))
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "Hata", "Duygu analizi dosyası bulunamadı! Önce duygu analizini yapın.")
            return

        # --- KULLANICI ONAYI KONTROLÜ (HATASIZ VERSİYON) ---
        if "Değerlendirmeye Alındı" not in self.confirm_categories_button.text():
            reply = QMessageBox.question(
                self,
                "Kategori Onayı",
                "Özel kategoriler onaylanmadı.\n\n"
                "Varsayılan kategorilerle (Kalite, Fiyat vb.) devam edilsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            # Kullanıcı "Evet" dışında bir seçim yaparsa (Hayır veya pencereyi kapatırsa)
            # işlemi KESİNLİKLE durdur.
            if reply != QMessageBox.StandardButton.Yes:
                self.status_label.setText("⚠️ Kategorizasyon işlemi iptal edildi. Lütfen kategorileri onaylayın veya varsayılanları kabul edin.")
                self.set_ui_processing_state(False)
                return  # <-- FONKSİYONDAN TAMAMEN ÇIKAR

            # Kullanıcı "Evet" dediyse, varsayılanları kilitle ve devam et
            self.lock_categories(show_warning_if_default=False)

        # --- KONTROL SONU ---

        self._auto_mode = False
        self.current_step = 3
        self.set_ui_processing_state(True)
        self.start_step_3_categorization(input_path, self.product_name_input.text())

    def start_step_3_categorization(self, input_path, product_title):
        """Ana kategorizasyon işlemini başlatır (kategori onayı zaten yapılmış varsayılır)."""
        self.progress_bar.setFormat("Kategori Analizi... %p%")
        self.progress_bar.setValue(0)
        self.status_label.setText("Yorumlar kategorilere ayrılıyor...")
        user_categories = self.get_user_categories() # BU SATIRI EKLEYİN

        categorization_output = os.path.join(OUTPUT_DIR, CATEGORIZATION_FILE_TEMPLATE.format(product_id=self.product_id))
        
        self.categorizer_thread = QThread()
        self.categorizer_worker = ReviewCategorizerWorker(input_path, categorization_output, user_categories)
        self.categorizer_worker.moveToThread(self.categorizer_thread)
        
        self.categorizer_worker.categorization_finished.connect(lambda path: self.on_categorization_finished(path, product_title))
        self.categorizer_worker.error_occurred.connect(self.on_process_error)
        self.categorizer_worker.status_message.connect(self.status_label.setText)
        self.categorizer_worker.progress_updated.connect(lambda cur, tot: self.update_progress(cur, tot, "Kategorizasyon"))
        self.categorizer_thread.started.connect(self.categorizer_worker.run)
        self.categorizer_thread.start()

    def on_categorization_finished(self, output_path, product_title):
        self.progress_bar.setValue(100)
        self.status_label.setText("Adım 3 tamamlandı. Grafikler oluşturuluyor...")
        self.status_label.setText("✅ Kategori analizi tamamlandı. Grafikler yükleniyor...")
        
        # --- KATEGORİ İŞLEMİ BİTİNCE KATEGORİ BÖLÜMÜNÜ SÖNÜK HALE GETİR ---
        try:
            # Kullanıcı kategorileri onaylamış ve kategorizasyon tamamlanmış durumda;
            # tekrar düzenlenmesin diye kategori alanını devre dışı bırak ve kapat.
            self.category_accordion.setEnabled(False)
            self.category_accordion.setProperty("active", False)
            # Olası inline stilleri temizle
            self.category_accordion.toggle_button.setStyleSheet("")
            # Kapalı konuma getir
            if self.category_accordion.toggle_button.isChecked():
                self.category_accordion.toggle_button.setChecked(False)
                self.category_accordion.toggle_content()
            # Disabled stilini uygula
            self.category_accordion.style().polish(self.category_accordion)
            # Onay butonunu da devre dışı bırak
            self.confirm_categories_button.setEnabled(False)
        except Exception:
            pass
        # Mark categorization output as present so UI shows step completed
        try:
            self._categorization_filepath = output_path
            self._files_exist_flags['categorization'] = True
        except Exception:
            pass
        self.update_step_buttons()
        self.update_feature_buttons()

        print(f"[DEBUG] Kategorileme tamamlandı. Çıktı dosyası: {output_path}")
        print(f"[DEBUG] Dosya mevcut mu: {os.path.exists(output_path)}")

        # Otomatik olarak SADECE grafikleri oluşturmayı başlat
        # Ensure we do not remain in auto mode (prevent accidental full-report creation)
        self._auto_mode = False
        # Start charts-only generation and show them to user
        print("[DEBUG] Grafik oluşturma başlıyor...")
        self.start_step_4_report_generation(output_path, product_title, charts_only=True)

        # UI'ı tekrar kullanılabilir hale getir ki 4. butona basılabilsin
        self.set_ui_processing_state(False)

    def start_step_4_report_generation(self, input_path, product_title, charts_only=False):
        print(f"[DEBUG] start_step_4_report_generation çağrıldı: input_path={input_path}, charts_only={charts_only}")
        
        # Eğer sadece grafik oluşturuluyorsa, metni ona göre ayarla
        if charts_only:
            self.progress_bar.setFormat("Grafikler Oluşturuluyor... %p%")
            self.progress_bar.setValue(0)
            self.status_label.setText("Analiz için grafikler hazırlanıyor...")
        else:
            # Rapor oluşturma yazısı sadece 'Rapor Oluştur' butonundan sonra görünsün
            self.progress_bar.setFormat("%p%")
            self.progress_bar.setValue(0)
            # Kullanıcı raporu başlatırken aşağıda indeterminate ve metni set edeceğiz

        # Rapor oluşturma sürecinde ETA doğru tahmin edilemediği için indeterminate moda al
        if not charts_only:
            # Deterministik ilerleme kullanıldığı için doğrudan 0%'dan başla
            self._suppress_eta = False
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Rapor oluşturuluyor... %p%")
            self.status_label.setText("Rapor oluşturuluyor, lütfen bekleyin...")
        user_categories = self.get_user_categories(show_warning=False) # Rapor için uyarı gösterme
        
        self.report_thread = QThread()
        self.report_worker = ReportBuilderWorker(input_path, product_title, user_categories, self.product_id, charts_only=charts_only)
        self.report_worker.moveToThread(self.report_thread)

        self.report_worker.charts_generated.connect(self.on_charts_generated)
        # İlerleme etiketi: charts_only=False ise 'Rapor', aksi halde 'Analiz'
        label_for_progress = "Rapor" if (charts_only is False) else "Analiz"
        self.report_worker.progress_updated.connect(lambda cur, tot: self.update_progress(cur, tot, label_for_progress))

        # İlerleme artık yalnızca worker progress_updated sinyaliyle yönetiliyor

        if charts_only:
            def _charts_only_finished(dummy_path):
                try:
                    self.progress_bar.setValue(100)
                    self.status_label.setText("Grafikler oluşturuldu. Rapor oluşturmak için 4. adıma basın.")
                except Exception:
                    pass
                self.set_ui_processing_state(False)

            self.report_worker.finished.connect(_charts_only_finished)
            def _cleanup_report_thread(_):
                try:
                    if self.report_thread and self.report_thread.isRunning():
                        self.report_thread.quit(); self.report_thread.wait(2000)
                except Exception:
                    pass
            self.report_worker.finished.connect(_cleanup_report_thread)
        else:
            self.report_worker.finished.connect(self.on_report_finished)
            def _cleanup_report_thread(report_path):
                try:
                    if self.report_thread and self.report_thread.isRunning():
                        self.report_thread.quit(); self.report_thread.wait(2000)
                except Exception:
                    pass
            self.report_worker.finished.connect(_cleanup_report_thread)
        
        self.report_worker.error.connect(self.on_process_error)
        self.report_worker.status_message.connect(self.status_label.setText)
        
        self.report_thread.started.connect(self.report_worker.run)
        self.report_thread.start()

    ### BU FONKSİYONU DEĞİŞTİRİN ###

    def on_report_finished(self, report_path):
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Rapor oluşturma tamamlandı %p%")
        
        self.status_label.setText(f"Tüm analiz tamamlandı! Rapor oluşturuldu.")
        QMessageBox.information(self, "Analiz Tamamlandı", f"Ürün analizi başarıyla tamamlandı!\nRapor kaydedildi: {report_path}")
        
        
        # Diğer butonları güncelle (4. adımdan sonra yeni akış için)
        self.set_ui_processing_state(False)
        self.update_step_buttons()
        self.update_feature_buttons()

        # Kullanıcıya yeni bir analize başlayabileceğini veya mevcut raporu inceleyebileceğini söyle
        self.status_label.setText("Tüm adımlar tamamlandı. Raporu açabilir veya 'Temizle' butonu ile yeni bir analize başlayabilirsiniz.")
    
    def add_category_row(self):
        """Kategori alanlarına yeni bir satır ekler."""
        try:
            row_index = len(self.category_inputs)
            if hasattr(self, "MAX_CATEGORY_ROWS") and row_index >= self.MAX_CATEGORY_ROWS:
                QMessageBox.information(self, "Limit", f"En fazla {self.MAX_CATEGORY_ROWS} kategori ekleyebilirsiniz.")
                return
            name_input = QLineEdit()
            desc_input = QLineEdit()
            name_input.setPlaceholderText(f"Kategori {row_index+1} Adı")
            desc_input.setPlaceholderText(f"Kategori {row_index+1} Açıklaması")
            self.category_fields_grid.addWidget(name_input, row_index, 0)
            self.category_fields_grid.addWidget(desc_input, row_index, 1)
            self.category_inputs.append((name_input, desc_input))
        except Exception:
            pass

    def remove_category_row(self):
        """Kategori alanlarından son satırı kaldırır (minimum 1 bırakır)."""
        try:
            if len(self.category_inputs) <= 1:
                return
            name_input, desc_input = self.category_inputs.pop()
            name_input.deleteLater(); desc_input.deleteLater()
        except Exception:
            pass
    

    # app_main.py dosyasındaki bu fonksiyonu bulun ve aşağıdakiyle TAMAMEN DEĞİŞTİRİN:

    ### BU FONKSİYONU DEĞİŞTİRİN ###

    @pyqtSlot(dict)
    def on_charts_generated(self, chart_buffers):
        self.last_chart_buffers = chart_buffers 
        """Rapor oluşturucudan gelen grafikleri en-boy oranını koruyarak ve düzgünce arayüzde gösterir."""
        self.status_label.setText("📊 Analizler arayüze ekleniyor, lütfen bekleyin...")
        QCoreApplication.processEvents()
        
        try:
            print("[DEBUG] Grafik yükleme sinyali alındı. Yüklenecek grafikler:", list(chart_buffers.keys()))

            self.results_group.setVisible(True)
            self.scroll_area.setVisible(True)
            
            # --- İYİLEŞTİRİLMİŞ BOYUTLANDIRMA ---
            main_window_width = self.width() if self.width() > 1000 else 1000
            available_width = int(main_window_width * 0.85)
            MAX_PIE_CHART_WIDTH = min(available_width - 100, 600)
            MAX_TIMESERIES_WIDTH = min(available_width - 50, 900)

            # 1. DUYGU ANALİZİ PASTA GRAFİĞİ
            if 'sentiment_pie' in chart_buffers:
                image_data = chart_buffers['sentiment_pie']
                pixmap = QPixmap()
                if pixmap.loadFromData(image_data) and not pixmap.isNull():
                    sentiment_layout = self.sentiment_accordion.content_layout
                    while sentiment_layout.count():
                        child = sentiment_layout.takeAt(0)
                        if child.widget(): child.widget().deleteLater()

                    self.sentiment_chart_label = QLabel()
                    scaled_pixmap = pixmap.scaledToWidth(MAX_PIE_CHART_WIDTH, Qt.TransformationMode.SmoothTransformation)
                    self.sentiment_chart_label.setPixmap(scaled_pixmap)
                    self.sentiment_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    sentiment_layout.addWidget(self.sentiment_chart_label)
                    self.sentiment_accordion.setVisible(True)
                    
                    if not self.sentiment_accordion.toggle_button.isChecked():
                        self.sentiment_accordion.toggle_button.setChecked(True)
                        self.sentiment_accordion.toggle_content()

            # 2. KATEGORİ DAĞILIMI PASTA GRAFİĞİ
            if 'category_pie' in chart_buffers:
                image_data = chart_buffers['category_pie']
                pixmap = QPixmap()
                if pixmap.loadFromData(image_data) and not pixmap.isNull():
                    category_pie_layout = self.category_pie_accordion.content_layout
                    while category_pie_layout.count():
                        child = category_pie_layout.takeAt(0)
                        if child.widget(): child.widget().deleteLater()

                    self.category_pie_label = QLabel()
                    scaled_pixmap = pixmap.scaledToWidth(MAX_PIE_CHART_WIDTH, Qt.TransformationMode.SmoothTransformation)
                    self.category_pie_label.setPixmap(scaled_pixmap)
                    self.category_pie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    category_pie_layout.addWidget(self.category_pie_label)
                    self.category_pie_accordion.setVisible(True)

                    if not self.category_pie_accordion.toggle_button.isChecked():
                        self.category_pie_accordion.toggle_button.setChecked(True)
                        self.category_pie_accordion.toggle_content()

            # 3. KATEGORİ ZAMAN SERİSİ GRAFİKLERİ
            while self.category_ts_layout.count():
                child = self.category_ts_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            timeseries_count = 0
            for key, image_data in chart_buffers.items():
                if key.startswith('timeseries_') and image_data:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(image_data) and not pixmap.isNull():
                        category_name = key.replace('timeseries_', '').replace('_', ' ').title()

                        title_label = QLabel(f"<h3 style='color: #64ffda; margin: 10px 0;'>{category_name}</h3>")
                        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.category_ts_layout.addWidget(title_label)
                        
                        chart_label = QLabel()
                        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        target_width = min(MAX_TIMESERIES_WIDTH, pixmap.width())
                        scaled_pixmap = pixmap.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)

                        chart_label.setPixmap(scaled_pixmap)
                        self.category_ts_layout.addWidget(chart_label)
                        timeseries_count += 1
            
            if timeseries_count > 0:
                self.category_ts_accordion.setVisible(True)
                if not self.category_ts_accordion.toggle_button.isChecked():
                    self.category_ts_accordion.toggle_button.setChecked(True)
                    self.category_ts_accordion.toggle_content()
            else:
                self.category_ts_accordion.setVisible(False)
            
            # --- DÜZELTME: TÜM İŞLEMLER BİTTİKTEN SONRA, EN SONDA ÇALIŞACAK BLOK ---
            # 1. Durum metnini isteğine göre ayarla.
            self.status_label.setText("Analiz Sonuçları")
            
            # 2. Grafikler artık mevcut olduğu için bayrakları ayarla.
            self._charts_available = True
            self._files_exist_flags['report'] = True
            
            # 3. "Grafikleri Göster" butonunu ve diğerlerini güncelle.
            self.update_feature_buttons()
            # --- DÜZELTME SONU ---

        except Exception as e:
            import traceback
            QMessageBox.warning(self, "Grafik Hatası", f"Grafikler yüklenirken hata oluştu: {str(e)}\n{traceback.format_exc()}")

    def show_csv_viewer(self):
        """CSV dosyalarını görüntülemek için pencere aç"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QLabel, QPushButton
        from PyQt6.QtGui import QColor
        import pandas as pd
        import os

        try:
            # Mevcut CSV dosyalarını bul
            csv_files = []
            if os.path.exists(OUTPUT_DIR):
                for file in os.listdir(OUTPUT_DIR):
                    if file.endswith('.csv'):
                        csv_files.append(os.path.join(OUTPUT_DIR, file))

            if not csv_files:
                QMessageBox.information(self, "CSV Görüntüleyici", "Henüz CSV dosyası bulunamadı. Önce analiz yapın.")
                return

            # CSV görüntüleyici dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("CSV Dosya Görüntüleyici")
            dialog.setGeometry(200, 200, 1000, 600)
            dialog_layout = QVBoxLayout()

            # Dosya seçimi
            file_layout = QHBoxLayout()
            file_layout.addWidget(QLabel("Dosya seç:"))
            file_combo = QComboBox()
            file_combo.addItems([os.path.basename(f) for f in csv_files])
            file_layout.addWidget(file_combo)

            # Yenile butonu
            refresh_btn = QPushButton("Yenile")
            file_layout.addWidget(refresh_btn)

            dialog_layout.addLayout(file_layout)

            # Tablo
            table = QTableWidget()
            dialog_layout.addWidget(table)

            def load_csv():
                selected_file = csv_files[file_combo.currentIndex()]
                df = pd.read_csv(selected_file, encoding='utf-8')

                table.setRowCount(len(df))
                table.setColumnCount(len(df.columns))
                table.setHorizontalHeaderLabels(df.columns.tolist())

                for i in range(len(df)):
                    for j in range(len(df.columns)):
                        raw_value = df.iloc[i, j]
                        if pd.isna(raw_value) or raw_value == '' or str(raw_value) == 'nan':
                            value = "-"
                        else:
                            value = str(raw_value)
                            if len(value) > 100:
                                value = value[:100] + "..."
                        table.setItem(i, j, QTableWidgetItem(value))

            # İlk yükleme
            load_csv()

            # Dosya değiştiğinde yenile
            file_combo.currentTextChanged.connect(load_csv)
            refresh_btn.clicked.connect(load_csv)

            dialog.setLayout(dialog_layout)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"CSV görüntüleme hatası: {e}")

    def _buffer_to_pixmap(self, buffer):
        """BytesIO buffer'ı QPixmap'e dönüştürür."""
        try:
            from PyQt6.QtGui import QImage, QPixmap

            # Buffer validasyonu
            if not buffer or not hasattr(buffer, 'seek'):
                print("[HATA] Buffer geçersiz veya seek metodu yok")
                return None

            buffer.seek(0)
            image_data = buffer.getvalue()

            # Veri boyut kontrolü
            if not image_data or len(image_data) < 100:
                print(f"[HATA] Buffer çok küçük veya boş: {len(image_data) if image_data else 0} byte")
                return None

            print(f"[DEBUG] Buffer boyutu: {len(image_data)} byte")

            # QImage oluşturma
            image = QImage.fromData(image_data)
            if image.isNull():
                print("[HATA] QImage oluşturulamadı - Veri formatı geçersiz olabilir")
                return None

            # QPixmap oluşturma
            pixmap = QPixmap.fromImage(image)
            if pixmap.isNull():
                print("[HATA] QPixmap oluşturulamadı")
                return None

            print(f"[DEBUG] Görüntü başarıyla dönüştürüldü: {pixmap.width()}x{pixmap.height()}")
            return pixmap

        except Exception as e:
            import traceback
            print(f"[HATA] Grafik dönüştürme hatası: {str(e)}")
            print(f"[HATA] Hata detayı:\n{traceback.format_exc()}")
            return None


    def on_process_error(self, error_message):
        # Butonu eski haline getir
        if hasattr(self, '_start_scraping_button'):
            self._start_scraping_button.setText("Ürünleri Onayla")
            self._start_scraping_button.setEnabled(False)
        
        QMessageBox.critical(self, "İşlem Hatası", error_message)
        self.reset_ui(status_message=f"❌ Hata: {error_message}")

    def closeEvent(self, event):
        """Uygulama kapanırken çalışan thread'leri düzgünce durdur ve bekle."""
        # Durdurma bayrağını set et
        self.stop_all_processes()

        # Wait a short while for threads to finish
        try:
            if hasattr(self, 'scraper_thread') and self.scraper_thread:
                if self.scraper_thread.isRunning():
                    self.scraper_thread.quit(); self.scraper_thread.wait(2000)
        except Exception:
            pass
        try:
            if hasattr(self, 'sentiment_thread') and self.sentiment_thread:
                if self.sentiment_thread.isRunning():
                    self.sentiment_thread.quit(); self.sentiment_thread.wait(2000)
        except Exception:
            pass
        try:
            if hasattr(self, 'categorizer_thread') and self.categorizer_thread:
                if self.categorizer_thread.isRunning():
                    self.categorizer_thread.quit(); self.categorizer_thread.wait(2000)
        except Exception:
            pass
        try:
            if hasattr(self, 'report_thread') and self.report_thread:
                if self.report_thread.isRunning():
                    self.report_thread.quit(); self.report_thread.wait(2000)
        except Exception:
            pass

        # Call base implementation
        super().closeEvent(event)

    def reset_ui(self, status_message="Hazır."):
        self.set_ui_processing_state(False)
        self.status_label.setText(status_message)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.update_step_buttons()
        self.update_feature_buttons()

        # Akordeon panelini aç ve kategori girişlerini sıfırla
        self.category_accordion.toggle_button.setChecked(True)
        self.category_accordion.toggle_content()
        
        # Kategorileri tekrar düzenlenebilir yap
        for name_input, desc_input in self.category_inputs:
            name_input.setEnabled(True)
            desc_input.setEnabled(True)
            name_input.clear()  # Kategori girişlerini temizle
            desc_input.clear()  # Açıklama girişlerini temizle
        
        self.confirm_categories_button.setEnabled(True)
        self.confirm_categories_button.setText("✅ Kategorileri Değerlendirmeye Al")
        # <<<<<<<<<<<<<<<< BU KOD BLOĞUNU BURAYA EKLEYİN (BİTİŞ) >>>>>>>>>>>>>>>>>>>>

    # app_main.py dosyasındaki bu fonksiyonu bulun ve aşağıdakiyle TAMAMEN DEĞİŞTİRİN:

    def update_step_buttons(self):
        """Adım butonlarının ve ayraçların durumunu ve stilini günceller."""
        if not self.product_id:
            self._files_exist_flags = {k: False for k in self._files_exist_flags}
        else:
            comments_file = os.path.join(OUTPUT_DIR, COMMENTS_FILE_TEMPLATE.format(product_id=self.product_id))
            sentiment_file = os.path.join(OUTPUT_DIR, SENTIMENT_FILE_TEMPLATE.format(product_id=self.product_id))
            categorization_file = os.path.join(OUTPUT_DIR, CATEGORIZATION_FILE_TEMPLATE.format(product_id=self.product_id))
            report_file = os.path.join(OUTPUT_DIR, REPORT_FILE_TEMPLATE.format(product_id=self.product_id))

            self._files_exist_flags['comments'] = os.path.exists(comments_file)
            self._files_exist_flags['sentiment'] = os.path.exists(sentiment_file)
            self._files_exist_flags['categorization'] = os.path.exists(categorization_file)
            self._files_exist_flags['report'] = os.path.exists(report_file)

        # Butonların tıklanabilirlik durumunu ayarla
        self.step1_button.setEnabled(not self.is_processing)
        self.step2_button.setEnabled(not self.is_processing and self._files_exist_flags['comments'])
        self.step3_button.setEnabled(not self.is_processing and self._files_exist_flags['sentiment'])
        self.step4_button.setEnabled(not self.is_processing and self._files_exist_flags['categorization'])

        buttons = [self.step1_button, self.step2_button, self.step3_button, self.step4_button]
        separators = [self.line_label_1, self.line_label_2, self.line_label_3]
        file_keys = ['comments', 'sentiment', 'categorization', 'report']

        for i, button in enumerate(buttons):
            # --- MANTIK DÜZELTMELERİ BURADA ---
            # 1. Aktif Durum: Sadece o adım işleniyorsa 'aktif'tir.
            # 'current_step_active' yerine 'current_step' kullanıldı.
            is_active = (self.current_step == (i + 1)) and self.is_processing
            
            # 2. Tamamlandı Durumu: İlgili dosya mevcutsa 'tamamlanmış'tır.
            is_completed = self._files_exist_flags[file_keys[i]]

            # Stil atamaları (öncelik sırasına göre)
            if is_active:
                # AKTİF STİLİ
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #00bcd4, stop:0.5 #64ffda, stop:1 #00bcd4);
                        border: 2px solid #64ffda; color: #0f0f23;
                        font-weight: bold; font-size: 14px; border-radius: 18px;
                        padding: 10px 20px; min-width: 110px;
                    }
                """)
            elif is_completed:
                # TAMAMLANDI STİLİ
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #4caf50, stop:0.5 #8bc34a, stop:1 #4caf50);
                        border: 2px solid #8bc34a; color: white;
                        font-weight: bold; font-size: 14px; border-radius: 18px;
                        padding: 10px 20px; min-width: 110px;
                    }
                """)
            elif button.isEnabled():
                # BEKLEMEDE ( tıklanabilir ama tamamlanmamış ) STİLİ
                button.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 193, 7, 0.15); border: 2px solid rgba(255, 193, 7, 0.4);
                        color: #ffc107; font-weight: 600; font-size: 14px; border-radius: 18px;
                        padding: 10px 20px; min-width: 110px;
                    }
                    QPushButton:hover { background: rgba(255, 193, 7, 0.25); }
                """)
            else:
                # DEVRE DIŞI STİLİ
                button.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.05); border: 2px solid rgba(255, 255, 255, 0.1);
                        color: rgba(255, 255, 255, 0.3); font-weight: 500; font-size: 14px; border-radius: 18px;
                        padding: 10px 20px; min-width: 110px;
                    }
                """)

        # Ayraçların stilini güncelleme (Bu kısım doğruydu, aynı kalabilir)
        for i, separator in enumerate(separators):
            prev_step_completed = self._files_exist_flags[file_keys[i]]
            if prev_step_completed:
                separator.setStyleSheet("color: #4caf50; font-size: 24px;")
            else:
                separator.setStyleSheet("color: rgba(255, 255, 255, 0.2); font-size: 24px;")

    # ... (show_csv_viewer, show_chart_viewer, vb. fonksiyonları aynı kalır)
    ### BU FONKSİYONU TAMAMEN DEĞİŞTİRİN ###

    def show_chart_viewer(self):
        """Grafikleri hafızadan veya diskten yükleyerek bir pencerede gösterir."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QComboBox, QWidget
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        import os

        # Önce hafızadaki (en son oluşturulan) grafikleri kontrol et
        if hasattr(self, 'last_chart_buffers') and self.last_chart_buffers:
            chart_data = self.last_chart_buffers
            is_buffer = True
            chart_names = list(chart_data.keys())
        else:
            # Hafızada yoksa, diskteki PNG dosyalarını ara
            chart_files_paths = []
            if os.path.exists(OUTPUT_DIR):
                for file in os.listdir(OUTPUT_DIR):
                    if file.endswith('.png') and self.product_id in file:
                        chart_files_paths.append(os.path.join(OUTPUT_DIR, file))
            
            if not chart_files_paths:
                QMessageBox.information(self, "Grafik Görüntüleyici", 
                    "Henüz görüntülenecek grafik bulunamadı. Lütfen önce analiz yapın.")
                return
            
            chart_data = chart_files_paths
            is_buffer = False
            chart_names = [os.path.basename(f) for f in chart_data]

        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 Grafik Görüntüleyici")
            dialog.setGeometry(150, 150, 1000, 700)
            dialog_layout = QVBoxLayout(dialog)

            # Arayüz elemanları
            top_layout = QHBoxLayout()
            top_layout.addWidget(QLabel("Görüntülenecek Grafik:"))
            combo = QComboBox()
            combo.addItems(chart_names)
            top_layout.addWidget(combo, 1)
            dialog_layout.addLayout(top_layout)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            image_label = QLabel("Grafik seçin...")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_area.setWidget(image_label)
            dialog_layout.addWidget(scroll_area)

            def display_chart():
                index = combo.currentIndex()
                pixmap = QPixmap()
                
                if is_buffer:
                    # Hafızadaki buffer'dan yükle
                    key = chart_names[index]
                    pixmap.loadFromData(chart_data[key])
                else:
                    # Diskteki dosyadan yükle
                    pixmap.load(chart_data[index])
                
                if not pixmap.isNull():
                    # Görüntüyü pencereye sığacak şekilde ölçekle
                    scaled_pixmap = pixmap.scaled(
                        scroll_area.width() - 20, 
                        scroll_area.height() - 20, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    image_label.setPixmap(scaled_pixmap)
                else:
                    image_label.setText("Grafik yüklenemedi.")

            combo.currentIndexChanged.connect(display_chart)
            display_chart() # İlk grafiği yükle
            
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Grafik görüntüleme hatası: {e}")
    
    def _update_report_progress_display(self):
        """Rapor oluşturma sürecindeki ilerlemeyi günceller."""
        if self.report_start_time is None:
            return
        
        elapsed_seconds = (datetime.now() - self.report_start_time).total_seconds()
        progress_percentage = min(100, int((elapsed_seconds / self.REPORT_ESTIMATED_DURATION) * 100))
        
        self.progress_bar.setValue(progress_percentage)
        remaining_seconds = max(0, self.REPORT_ESTIMATED_DURATION - elapsed_seconds)
        
        if remaining_seconds > 0:
            minutes = int(remaining_seconds // 60)
            seconds = int(remaining_seconds % 60)
            self.status_label.setText(f"Rapor oluşturuluyor... (Yaklaşık {minutes:02d}:{seconds:02d} kaldı)")
        else:
            self.status_label.setText("Rapor oluşturma tamamlanıyor...")

    def show_category_explanation(self):
        """Kategorilendirme sistemi hakkında açıklama göster"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🧠 Kategorilendirme Sistemi Nasıl Çalışır?")
        dialog.setGeometry(300, 300, 800, 600)
        dialog_layout = QVBoxLayout()
        
        explanation_text = QTextEdit()
        explanation_text.setReadOnly(True)
        explanation_text.setHtml("""
        <h2>🧠 Kategorilendirme Sistemi</h2>
        
        <h3>📋 Kategoriler:</h3>
        <ul>
        <li><b>Kalite:</b> Ürün kalitesi, dayanıklılık, yapım kalitesi hakkındaki yorumlar</li>
        <li><b>Fiyat:</b> Fiyat-performans, değer, maliyet hakkındaki yorumlar</li>
        <li><b>Kargo:</b> Teslimat, paketleme ve kargo hızı hakkındaki yorumlar</li>
        <li><b>Müşteri_Hizmetleri:</b> Satış sonrası destek ve müşteri hizmetleri</li>
        <li><b>Tasarım:</b> Görünüm, stil ve estetik özellikler</li>
        </ul>
        
        <h3>🔢 1 ve 0 Sistemi:</h3>
        <p><b>1</b> = Bu yorum bu kategoriye ait</p>
        <p><b>0</b> = Bu yorum bu kategoriye ait değil</p>
        
        <h3>📊 Örnek:</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f8f9fa;">
        <th>Yorum</th>
        <th>Kalite</th>
        <th>Fiyat</th>
        <th>Kargo</th>
        <th>Müşteri_Hizmetleri</th>
        <th>Tasarım</th>
        </tr>
        <tr>
        <td>"Ürün çok kaliteli ve güzel görünüyor"</td>
        <td style="background-color: #d4edda;">1</td>
        <td style="background-color: #f8d7da;">0</td>
        <td style="background-color: #f8d7da;">0</td>
        <td style="background-color: #f8d7da;">0</td>
        <td style="background-color: #d4edda;">1</td>
        </tr>
        <tr>
        <td>"Kargo çok hızlı geldi, fiyatı uygun"</td>
        <td style="background-color: #f8d7da;">0</td>
        <td style="background-color: #d4edda;">1</td>
        <td style="background-color: #d4edda;">1</td>
        <td style="background-color: #f8d7da;">0</td>
        <td style="background-color: #f8d7da;">0</td>
        </tr>
        </table>
        
        <h3>🤖 AI Nasıl Karar Veriyor?</h3>
        <p>Ollama AI (gemma3:4b modeli) her yorumu okur ve şu soruları sorar:</p>
        <ul>
        <li>Bu yorumda kalite hakkında bahsediliyor mu?</li>
        <li>Bu yorumda fiyat hakkında bahsediliyor mu?</li>
        <li>Bu yorumda kargo hakkında bahsediliyor mu?</li>
        <li>Bu yorumda müşteri hizmetleri hakkında bahsediliyor mu?</li>
        <li>Bu yorumda tasarım hakkında bahsediliyor mu?</li>
        </ul>
        
        <p>Her soru için cevap <b>1</b> (evet) veya <b>0</b> (hayır) olarak verilir.</p>
        
        <h3>📈 Grafiklerde Ne Görüyoruz?</h3>
        <p>Grafikler, hangi kategorilerin <b>kaç kez</b> bahsedildiğini gösterir. 
        Yüksek sayılar, o konunun müşteriler için <b>önemli</b> olduğunu gösterir.</p>
        """)
        
        dialog_layout.addWidget(explanation_text)
        
        close_btn = QPushButton("Tamam")
        close_btn.clicked.connect(dialog.close)
        dialog_layout.addWidget(close_btn)
        
        dialog.setLayout(dialog_layout)
        dialog.exec()
    
    def open_word_report(self):
        """Word raporunu aç"""
        import os
        import subprocess
        import platform
        
        try:
            report_path = os.path.join("output", f"{self.product_id}_analiz_raporu.docx")
            
            if not os.path.exists(report_path):
                QMessageBox.warning(self, "Rapor Bulunamadı", 
                    "Word raporu henüz oluşturulmamış. Önce tam analiz yapın (Adım 4'e kadar).")
                return
            
            # İşletim sistemine göre dosyayı aç
            if platform.system() == "Windows":
                os.startfile(report_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", report_path])
            else:  # Linux
                subprocess.run(["xdg-open", report_path])
                
            self.status_label.setText("📋 Word raporu açıldı!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor açma hatası: {e}")
    
    def update_feature_buttons(self):
        """Özellik butonlarının durumunu güncelle"""
        self.update_step_buttons() # Önce dosya durumlarını güncelleyelim
        self.view_csv_button.setEnabled(self._files_exist_flags['comments'])
        self.view_charts_button.setEnabled(self._files_exist_flags['report']) # Grafikler raporla birlikte oluşuyor varsayımı
        self.open_report_button.setEnabled(self._files_exist_flags['report'])


# YENİ VE MODERN STİL SAYFASI
QSS_STYLE = """
/* === MODERN UI DESIGN SYSTEM === */

/* --- Global Variables & Base --- */
QWidget {
    font-family: 'Inter', 'SF Pro Display', 'Segoe UI Variable', sans-serif;
    font-size: 14px;
    color: #e4e6ea;
    background-color: transparent;
}

QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #0f0f23, 
                stop:0.3 #1a1a2e, 
                stop:0.7 #16213e, 
                stop:1 #0f0f23);
}

/* --- Modern Glass Cards --- */
QGroupBox {
    font-weight: 600;
    font-size: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    margin-top: 15px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 15px;
    left: 20px;
    color: #64ffda;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #00bcd4, 
                stop:1 #64ffda);
    border-radius: 12px;
    font-weight: 700;
}

/* --- Premium Input Fields & Error State --- */
QLineEdit, QSpinBox, QComboBox {
    font-size: 15px;
    padding: 12px 16px;
    border: 2px solid rgba(100, 255, 218, 0.2);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.05);
    color: #e4e6ea;
    selection-background-color: #64ffda;
    selection-color: #1a1a2e;
    transition: border 0.2s ease, background 0.2s ease;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 2px solid #64ffda;
    background: rgba(100, 255, 218, 0.08);
    box-shadow: 0 0 20px rgba(100, 255, 218, 0.3);
}

/* Hata durumundaki widget'lar için stil */
QLineEdit[error="true"], QComboBox[error="true"] {
    border: 2px solid #e74c3c; /* Kırmızı çerçeve */
}

/* --- SpinBox Okları --- */
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: border;
    background: rgba(100, 255, 218, 0.1);
    border: none;
    border-radius: 6px;
    width: 24px;
    margin: 3px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: rgba(100, 255, 218, 0.2);
}

QSpinBox::up-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 7px solid #64ffda;
    width: 0px; height: 0px;
}

QSpinBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid #64ffda;
    width: 0px; height: 0px;
}

/* --- ComboBox Ok --- */
QComboBox {
    min-width: 120px;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #64ffda;
    width: 0px; height: 0px;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background: rgba(26, 26, 46, 0.95);
    border: 1px solid rgba(100, 255, 218, 0.3);
    border-radius: 12px;
    color: #e4e6ea;
    selection-background-color: rgba(100, 255, 218, 0.2);
}

/* --- Dynamic Step Indicators --- */
QPushButton[class~="step-button"] {
    padding: 12px 20px;
    font-weight: 600;
    font-size: 14px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.05);
    color: #a0a3bd;
    min-width: 100px;
    transition: all 0.3s ease;
}

QPushButton[class~="step-button"]:hover {
    background: rgba(100, 255, 218, 0.1);
    border-color: rgba(100, 255, 218, 0.5);
    color: #64ffda;
    transform: translateY(-2px);
}

QPushButton[class~="step-button-active"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #00bcd4, 
                stop:1 #64ffda);
    border: 2px solid #64ffda;
    color: #1a1a2e;
    font-weight: 700;
    box-shadow: 0 8px 25px rgba(100, 255, 218, 0.4);
}

QPushButton[class~="step-button-completed"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #4caf50, 
                stop:1 #8bc34a);
    border: 2px solid #4caf50;
    color: white;
    font-weight: 700;
    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
}

QPushButton[class~="step-button-pending"] {
    background: rgba(255, 193, 7, 0.1);
    border: 2px solid rgba(255, 193, 7, 0.3);
    color: #ffc107;
}

QPushButton:focus {
    outline: none;
}

/* --- Elegant Separators --- */
QLabel[class~="step-separator"] {
    font-size: 28px;
    font-weight: 300;
    color: rgba(255, 255, 255, 0.2);
    margin: 0 10px;
}

QLabel[class~="separator-active"] {
    color: #64ffda;
    text-shadow: 0 0 10px rgba(100, 255, 218, 0.5);
}

QLabel[class~="separator-completed"] {
    color: #4caf50;
    text-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
}

/* --- Hero Action Buttons --- */
#auto_button, #stop_button {
    font-size: 16px;
    font-weight: 700;
    padding: 16px 32px;
    border: none;
    border-radius: 16px;
    min-height: 50px;
    min-width: 140px;
    letter-spacing: 0.5px;
}

#auto_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #4caf50, 
                stop:1 #8bc34a);
    color: white;
    box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
}

#auto_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #66bb6a, 
                stop:1 #9ccc65);
    box-shadow: 0 12px 35px rgba(76, 175, 80, 0.5);
    transform: translateY(-3px);
}

#stop_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #f44336, 
                stop:1 #ff5722);
    color: white;
    box-shadow: 0 8px 25px rgba(244, 67, 54, 0.4);
}

#stop_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #e57373, 
                stop:1 #ff8a65);
    box-shadow: 0 12px 35px rgba(244, 67, 54, 0.5);
    transform: translateY(-3px);
}

QPushButton:disabled {
    background: rgba(255, 255, 255, 0.05) !important;
    color: rgba(255, 255, 255, 0.3) !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: none !important;
}

/* --- Dynamic Status Display --- */
#status_label {
    font-size: 16px;
    font-weight: 600;
    padding: 10px 15px;
    border-radius: 10px;
    background: rgba(100, 255, 218, 0.1);
    color: #64ffda;
    border: 1px solid rgba(100, 255, 218, 0.2);
}

/* --- Futuristic Progress Bar --- */
QProgressBar {
    border: none;
    border-radius: 12px;
    text-align: center;
    font-weight: 700;
    font-size: 13px;
    color: white;
    background: rgba(255, 255, 255, 0.1);
    height: 24px;
}

QProgressBar::chunk {
    border-radius: 12px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #00bcd4, 
                stop:0.5 #64ffda, 
                stop:1 #4caf50);
    box-shadow: 0 0 15px rgba(100, 255, 218, 0.5);
}

/* --- Utility Buttons with Personality --- */
QGroupBox#utils_group QPushButton {
    background: rgba(156, 39, 176, 0.8);
    padding: 14px 18px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 12px;
    border: 1px solid rgba(156, 39, 176, 0.3);
    color: white;
}

QGroupBox#utils_group QPushButton:hover {
    background: rgba(186, 104, 200, 0.9);
    box-shadow: 0 6px 20px rgba(156, 39, 176, 0.4);
    transform: translateY(-2px);
}

/* --- Premium Text Areas --- */
QTextEdit {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 255, 218, 0.2);
    border-radius: 16px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    color: #e4e6ea;
    padding: 15px;
    selection-background-color: rgba(100, 255, 218, 0.3);
    selection-color: #1a1a2e;
}

QTextEdit:focus {
    border: 2px solid rgba(100, 255, 218, 0.5);
    background: rgba(0, 0, 0, 0.4);
}

/* --- Minimalist Scrollbars --- */
QScrollBar:vertical {
    border: none;
    background: rgba(255, 255, 255, 0.05);
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: rgba(100, 255, 218, 0.6);
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(100, 255, 218, 0.8);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: rgba(255, 255, 255, 0.05);
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: rgba(100, 255, 218, 0.6);
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(100, 255, 218, 0.8);
}

/* --- Tooltip Enhancement --- */
QToolTip {
    background: rgba(26, 26, 46, 0.95);
    color: #64ffda;
    border: 1px solid rgba(100, 255, 218, 0.3);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

/* --- Context Menu Styling --- */
QMenu {
    background: rgba(26, 26, 46, 0.95);
    border: 1px solid rgba(100, 255, 218, 0.3);
    border-radius: 12px;
    color: #e4e6ea;
    padding: 5px;
}

QMenu::item {
    padding: 8px 15px;
    border-radius: 6px;
}

QMenu::item:selected {
    background: rgba(100, 255, 218, 0.2);
    color: #64ffda;
}

/* --- Confirm Button Styling --- */
#confirm_button {
    font-size: 15px;
    font-weight: 600;
    padding: 12px;
    margin-top: 10px;
    background-color: #3b5998; /* Mavi renk */
    border: none;
    border-radius: 12px;
}

#confirm_button:hover {
    background-color: #4e73df;
}

#confirm_button:disabled {
    background: #27ae60 !important; /* Yeşil renk */
    color: white !important;
}

/* --- Accordion Butonları için Stil --- */
QPushButton#accordion_button {
    background: rgba(100, 255, 218, 0.1);
    border: 1px solid rgba(100, 255, 218, 0.3);
    border-radius: 12px;
    padding: 10px 15px;
    font-size: 15px;
    font-weight: 600;
    color: #64ffda;
    text-align: left;
    margin-bottom: 5px; /* İçerikle arasında boşluk bırak */
    transition: background 0.2s ease, border-color 0.2s ease;
}

QPushButton#accordion_button:hover {
    background: rgba(100, 255, 218, 0.2);
    border-color: #64ffda;
}

QPushButton#accordion_button:checked { /* Açık durumdayken */
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #00bcd4, 
                stop:1 #64ffda);
    color: #1a1a2e;
    border-color: #00bcd4;
    box-shadow: 0 4px 15px rgba(100, 255, 218, 0.3);
}

/* --- Accordion İçerik Alanı (QWidget) --- */
QWidget#accordion_content_area { /* AccordionWidget içindeki content_area için özel ID */
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-top: none; /* Üst kenarlığı kaldırdık, butonla bütünleşik durması için */
    border-radius: 0 0 12px 12px; /* Sadece alt kenarları yuvarladık */
    background: rgba(255, 255, 255, 0.01);
    padding: 15px;
    margin-bottom: 10px; /* Her accordion arasında boşluk */
}
/* --- Accordion ve Onay Butonları için DEVRE DIŞI (SÖNÜK) Stil --- */
QPushButton#accordion_button:disabled,
QPushButton#accordion_button[enabled="false"] {
    background: rgba(40, 40, 60, 0.5) !important;
    color: rgba(228, 230, 234, 0.4) !important;
    border: 1px solid rgba(100, 255, 218, 0.1) !important;
    box-shadow: none !important;
}

QPushButton#accordion_button:disabled:hover,
QPushButton#accordion_button[enabled="false"]:hover {
    background: rgba(40, 40, 60, 0.5) !important;
    border-color: rgba(100, 255, 218, 0.1) !important;
}

QPushButton#confirm_button:disabled,
QPushButton#confirm_button[enabled="false"] {
    background: rgba(40, 40, 60, 0.5) !important;
    color: rgba(228, 230, 234, 0.4) !important;
    border: 1px solid rgba(100, 255, 218, 0.1) !important;
}

/* --- ÜRÜNLER ONAYLA BUTONU (BAŞLATMA BUTONU) --- */
QPushButton#start_scraping_button {
    background-color: #3b5998 !important; /* Kategori Onayla ile aynı mavi */
    color: white !important;
    font-size: 15px;
    font-weight: bold;
    border: 2px solid #2d4373 !important;
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 4px 12px rgba(59, 89, 152, 0.4);
    min-height: 30px; 
}

QPushButton#start_scraping_button:hover {
    background-color: #4e73df !important; /* Hover rengi */
    box-shadow: 0 6px 18px rgba(78, 115, 223, 0.5);
    transform: translateY(-2px);
}

QPushButton#start_scraping_button:disabled {
    background-color: #506A84 !important; /* Devre dışı - gri */
    color: rgba(176, 176, 176, 0.6) !important;
    border: 2px solid rgba(80, 106, 132, 0.5) !important;
    box-shadow: none;
}

QPushButton#start_scraping_button:pressed {
    background-color: #2d4373 !important; /* Basılı - koyu mavi */
    transform: scale(0.98);
    box-shadow: 0 2px 8px rgba(59, 89, 152, 0.3);
}

üst"""
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UrunAnalizGUI()
    window.setStyleSheet(QSS_STYLE)
    window.show()
    sys.exit(app.exec())


