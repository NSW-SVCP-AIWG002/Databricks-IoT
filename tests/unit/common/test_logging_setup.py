"""
ログ出力先・ハンドラー設定の単体テスト

観点: ログ設計書 3章 ログ出力形式・出力先

検証内容:
  - 全環境で stdout への StreamHandler が設定される
  - stdout ハンドラーには JsonFormatter が設定される
  - development 環境のみ logs/app.log への FileHandler が追加される
  - testing / production 環境では FileHandler が存在しない
  - dev 環境の FileHandler はテキスト形式（非JSON）
"""
import os
import sys
import logging

import pytest
from flask import Flask
from pythonjsonlogger.json import JsonFormatter

from iot_app import configure_logging


@pytest.mark.unit
class TestConfigureLogging:
    """ログハンドラー設定テスト
    観点: ログ設計書 3章 ログ出力形式・出力先
    """

    def setup_method(self):
        """各テスト前: ルートロガーのハンドラーを保存・クリア"""
        self.app = Flask(__name__)
        self._root = logging.getLogger()
        self._saved_handlers = list(self._root.handlers)
        self._saved_level = self._root.level
        self._root.handlers.clear()

    def teardown_method(self):
        """各テスト後: ルートロガーを復元・ファイルハンドラーを閉じる"""
        for h in list(self._root.handlers):
            if isinstance(h, logging.FileHandler):
                h.close()
        self._root.handlers.clear()
        self._root.handlers.extend(self._saved_handlers)
        self._root.level = self._saved_level

        if os.path.exists("logs/app.log"):
            os.remove("logs/app.log")

    # -----------------------------------------------------------------------
    # 全環境共通: stdout StreamHandler
    # -----------------------------------------------------------------------

    def test_stdout_stream_handler_added(self):
        """3章: 全環境でstdoutへのStreamHandlerが設定される"""
        # Arrange / Act
        configure_logging(self.app, "testing")

        # Assert
        stdout_handlers = [
            h for h in self._root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
            and h.stream is sys.stdout
        ]
        assert len(stdout_handlers) == 1

    def test_stdout_handler_uses_json_formatter(self):
        """3章: stdoutのStreamHandlerにはJsonFormatterが設定される"""
        # Arrange / Act
        configure_logging(self.app, "testing")

        # Assert
        stdout_handlers = [
            h for h in self._root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
            and h.stream is sys.stdout
        ]
        assert len(stdout_handlers) == 1
        assert isinstance(stdout_handlers[0].formatter, JsonFormatter)

    # -----------------------------------------------------------------------
    # 非dev環境: FileHandler が存在しない
    # -----------------------------------------------------------------------

    def test_no_file_handler_in_testing(self):
        """3章: testing環境ではFileHandlerが存在しない"""
        # Arrange / Act
        configure_logging(self.app, "testing")

        # Assert
        file_handlers = [
            h for h in self._root.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 0

    def test_no_file_handler_in_production(self):
        """3章: production環境ではFileHandlerが存在しない"""
        # Arrange / Act
        configure_logging(self.app, "production")

        # Assert
        file_handlers = [
            h for h in self._root.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 0

    # -----------------------------------------------------------------------
    # development環境のみ: logs/app.log への FileHandler
    # -----------------------------------------------------------------------

    def test_file_handler_added_in_development(self):
        """3章: development環境ではlogs/app.logへのFileHandlerが追加される"""
        # Arrange / Act
        configure_logging(self.app, "development")

        # Assert
        file_handlers = [
            h for h in self._root.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert "app.log" in file_handlers[0].baseFilename

    def test_file_handler_uses_text_formatter(self):
        """3章: dev環境のFileHandlerはテキスト形式（非JSON）のフォーマッターを使用する"""
        # Arrange / Act
        configure_logging(self.app, "development")

        # Assert
        file_handlers = [
            h for h in self._root.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert not isinstance(file_handlers[0].formatter, JsonFormatter)
