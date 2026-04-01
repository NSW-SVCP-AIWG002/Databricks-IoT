# tests/unit/ai-chat/conftest.py
#
# テストモジュール読み込み前に標準ライブラリおよびサードパーティ製パッケージを
# sys.modules へ登録しておく。
#
# test_conversational-ai-chat.py はモジュールレベルで
#   sys.modules.setdefault("pandas", MagicMock())
# を実行するが、setdefault は既にキーが存在する場合に上書きしない。
# pandas を先にインポートしておくことで実パッケージが使われ、
# submodule import（from pandas.api.types import ...）が正常に動作する。

import numpy  # noqa: F401
import pandas  # noqa: F401
import pandas.api.types  # noqa: F401
