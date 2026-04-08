/**
 * chat.js — 対話型AIチャット画面（CHT-001）
 *
 * SessionStorage キー定数
 */
const SS_THREAD_ID = 'chat_thread_id';
const SS_HISTORY   = 'chat_history';

const MAX_CHARS = 1000;

class ChatUI {
    constructor() {
        this.form            = document.getElementById('chat_form');
        this.input           = document.getElementById('question_input');
        this.submitBtn       = document.getElementById('submit_button');
        this.chatHistory     = document.getElementById('chat_history');
        this.loadingIndicator = document.getElementById('loading_indicator');
        this.charCount       = document.getElementById('char_count');
        this.newConvBtn      = document.getElementById('new_conversation_button');

        // SessionStorage から thread_id を復元、なければ新規生成
        this.threadId = sessionStorage.getItem(SS_THREAD_ID);
        if (!this.threadId) {
            this.threadId = crypto.randomUUID();
            sessionStorage.setItem(SS_THREAD_ID, this.threadId);
        }

        this._initEventListeners();
        this._restoreHistory();
    }

    // ----------------------------------------------------------------
    // イベントリスナー初期化
    // ----------------------------------------------------------------

    _initEventListeners() {
        // フォーム送信
        this.form.addEventListener('submit', (e) => this._handleSubmit(e));

        // 文字数カウント・送信ボタン活性制御
        this.input.addEventListener('input', () => this._onInputChange());

        // Enter 送信 / Shift+Enter 改行 / Ctrl+Enter 送信
        this.input.addEventListener('keydown', (e) => {
            if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && e.ctrlKey)) {
                e.preventDefault();
                if (!this.submitBtn.disabled) {
                    this.form.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            }
            // Escape でクリア
            if (e.key === 'Escape') {
                this.input.value = '';
                this._onInputChange();
            }
        });

        // 新規会話ボタン
        this.newConvBtn.addEventListener('click', () => this._startNewConversation());
    }

    // ----------------------------------------------------------------
    // 入力欄変更ハンドラ
    // ----------------------------------------------------------------

    _onInputChange() {
        const len = this.input.value.length;
        this.charCount.textContent = `${len}/${MAX_CHARS}`;
        this.charCount.classList.toggle('char-count--warn', len >= MAX_CHARS * 0.9);

        // 送信ボタン活性: テキストがあり、送信中でない
        const hasText = this.input.value.trim().length > 0;
        this.submitBtn.disabled = !hasText || this._sending;

        // textarea 高さ自動調整（最大10行）
        this.input.style.height = 'auto';
        const lineHeight = parseFloat(getComputedStyle(this.input).lineHeight);
        const maxHeight = lineHeight * 10;
        this.input.style.height = Math.min(this.input.scrollHeight, maxHeight) + 'px';
    }

    // ----------------------------------------------------------------
    // SessionStorage 操作
    // ----------------------------------------------------------------

    _restoreHistory() {
        const saved = sessionStorage.getItem(SS_HISTORY);
        if (!saved) return;

        let history;
        try {
            history = JSON.parse(saved);
        } catch {
            return;
        }

        history.forEach((entry) => {
            if (entry.role === 'user') {
                this._appendUserMessage(entry.content, entry.timestamp, false);
            } else {
                this._appendAIMessage(entry, false);
            }
        });
    }

    _saveToHistory(entry) {
        const saved = sessionStorage.getItem(SS_HISTORY);
        const history = saved ? JSON.parse(saved) : [];
        history.push(entry);
        sessionStorage.setItem(SS_HISTORY, JSON.stringify(history));
    }

    // ----------------------------------------------------------------
    // 送信処理
    // ----------------------------------------------------------------

    async _handleSubmit(e) {
        e.preventDefault();

        const question = this.input.value.trim();
        if (!question || this._sending) return;

        const timestamp = new Date().toISOString();

        // ユーザーメッセージを表示・保存
        const { bubble: userBubble } = this._appendUserMessage(question, timestamp, true);
        this._saveToHistory({ role: 'user', content: question, timestamp });

        this.input.value = '';
        this._onInputChange();

        this._setSending(true);
        this._showLoading();

        let response = null;
        try {
            response = await this._postQuestion(question, this.threadId);

            if (response.status === 'interrupted') {
                this._showHITLConfirmation(response, userBubble);
                this._saveToHistory({
                    role: 'ai',
                    content: response.message,
                    status: response.status,
                    df: response.df,
                    sql_query: response.sql_query,
                    timestamp: new Date().toISOString(),
                });
                // HITL 中は入力を無効にしたままにする
            } else {
                this._appendAIMessage(response, true);
                this._saveToHistory({
                    role: 'ai',
                    content: response.message,
                    status: response.status,
                    df: response.df,
                    fig_data: response.fig_data,
                    sql_query: response.sql_query,
                    timestamp: new Date().toISOString(),
                });
                this._setSending(false);
            }
        } catch (err) {
            this._appendErrorMessage(err.message || '回答の取得に失敗しました。', question, userBubble, err.errorCode);
            this._setSending(false);
        } finally {
            this._hideLoading();
        }
    }

    async _postQuestion(question, threadId) {
        const resp = await fetch('/api/analysis/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, thread_id: threadId }),
        });

        const data = await resp.json();

        if (!data.success) {
            const err = new Error(data.error_message || 'エラーが発生しました');
            err.errorCode = data.error_code;
            throw err;
        }

        return data;
    }

    // ----------------------------------------------------------------
    // リトライ
    // ----------------------------------------------------------------

    _handleRetry(question, retryBtn, errorBubble) {
        retryBtn.style.display = 'none';
        if (errorBubble) errorBubble.remove();

        this._setSending(true);
        this._showLoading();

        this._postQuestion(question, this.threadId)
            .then((response) => {
                if (response.status === 'interrupted') {
                    this._showHITLConfirmation(response, null);
                } else {
                    this._appendAIMessage(response, true);
                    this._saveToHistory({
                        role: 'ai',
                        content: response.message,
                        status: response.status,
                        df: response.df,
                        fig_data: response.fig_data,
                        sql_query: response.sql_query,
                        timestamp: new Date().toISOString(),
                    });
                    this._setSending(false);
                }
            })
            .catch((err) => {
                this._appendErrorMessage(err.message, question, null, err.errorCode);
                this._setSending(false);
            })
            .finally(() => {
                this._hideLoading();
            });
    }

    // ----------------------------------------------------------------
    // HITL 処理
    // ----------------------------------------------------------------

    _showHITLConfirmation(response, _userBubble) {
        const hitlView = document.createElement('div');
        hitlView.className = 'hitl-view';

        // グラフ作成要否確認メッセージ
        const msg = document.createElement('p');
        msg.className = 'hitl-view__message';
        msg.textContent = response.message || '以下のデータを取得しました。グラフを作成しますか？';
        hitlView.appendChild(msg);

        // Genie 取得結果表示（先頭100文字 + 省略）
        if (response.df != null) {
            const preview = document.createElement('pre');
            preview.className = 'hitl-view__preview';
            const previewText = JSON.stringify(response.df);
            preview.textContent = previewText.length > 100
                ? previewText.substring(0, 100) + '...'
                : previewText;
            hitlView.appendChild(preview);
        }

        // はい / いいえ ボタン
        const actions = document.createElement('div');
        actions.className = 'hitl-view__actions';

        const yesBtn = document.createElement('button');
        yesBtn.textContent = 'はい';
        yesBtn.className = 'button button--primary';
        yesBtn.type = 'button';
        yesBtn.addEventListener('click', () => this._handleHITLResponse('はい', hitlView));

        const noBtn = document.createElement('button');
        noBtn.textContent = 'いいえ';
        noBtn.className = 'button button--secondary';
        noBtn.type = 'button';
        noBtn.addEventListener('click', () => this._handleHITLResponse('いいえ', hitlView));

        actions.appendChild(yesBtn);
        actions.appendChild(noBtn);
        hitlView.appendChild(actions);

        this.chatHistory.appendChild(hitlView);
        this._scrollToBottom();
    }

    async _handleHITLResponse(answer, hitlView) {
        hitlView.querySelectorAll('button').forEach((btn) => { btn.disabled = true; });
        hitlView.style.display = 'none';

        this._showLoading();

        try {
            const response = await this._postQuestion(answer, this.threadId);
            this._appendAIMessage(response, true);
            this._saveToHistory({
                role: 'ai',
                content: response.message,
                status: response.status,
                df: response.df,
                fig_data: response.fig_data,
                sql_query: response.sql_query,
                timestamp: new Date().toISOString(),
            });
        } catch (err) {
            this._appendErrorMessage(err.message, answer, null, err.errorCode);
        } finally {
            this._hideLoading();
            this._setSending(false);
        }
    }

    // ----------------------------------------------------------------
    // 新規会話
    // ----------------------------------------------------------------

    _startNewConversation() {
        const saved = sessionStorage.getItem(SS_HISTORY);
        if (saved) {
            let history = [];
            try { history = JSON.parse(saved); } catch { /* noop */ }
            if (history.length > 0) {
                if (!window.confirm('現在の会話履歴がクリアされます。よろしいですか？')) {
                    return;
                }
            }
        }
        sessionStorage.removeItem(SS_HISTORY);
        this.threadId = crypto.randomUUID();
        sessionStorage.setItem(SS_THREAD_ID, this.threadId);
        this.chatHistory.innerHTML = '';
    }

    // ----------------------------------------------------------------
    // DOM 操作ヘルパー
    // ----------------------------------------------------------------

    _appendUserMessage(content, timestamp, scroll) {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-message--user';

        const bubble = document.createElement('div');
        bubble.className = 'chat-message__bubble--user';
        bubble.textContent = content;
        wrapper.appendChild(bubble);

        if (timestamp) {
            const meta = document.createElement('div');
            meta.className = 'chat-message__meta';
            meta.textContent = this._formatTime(timestamp);
            wrapper.appendChild(meta);
        }

        this.chatHistory.appendChild(wrapper);
        if (scroll) this._scrollToBottom();
        return { wrapper, bubble };
    }

    _appendAIMessage(data, scroll) {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-message--ai';

        const bubble = document.createElement('div');
        bubble.className = 'chat-message__bubble--ai';

        // Markdown レンダリング（DOMPurify でサニタイズ）
        if (data.content || data.message) {
            const raw = data.content || data.message || '';
            const rendered = typeof marked !== 'undefined'
                ? marked.parse(raw)
                : raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            const sanitized = typeof DOMPurify !== 'undefined'
                ? DOMPurify.sanitize(rendered)
                : rendered;
            bubble.innerHTML = sanitized;
        }

        // テーブル描画
        if (data.df) {
            try {
                const records = typeof data.df === 'string' ? JSON.parse(data.df) : data.df;
                if (Array.isArray(records) && records.length > 0) {
                    const tableWrapper = document.createElement('div');
                    tableWrapper.className = 'chat-table-wrapper';

                    const table = document.createElement('table');
                    table.className = 'chat-table';

                    const thead = document.createElement('thead');
                    const headerRow = document.createElement('tr');
                    Object.keys(records[0]).forEach((col) => {
                        const th = document.createElement('th');
                        th.textContent = col;
                        headerRow.appendChild(th);
                    });
                    thead.appendChild(headerRow);
                    table.appendChild(thead);

                    const tbody = document.createElement('tbody');
                    records.forEach((row) => {
                        const tr = document.createElement('tr');
                        Object.values(row).forEach((val) => {
                            const td = document.createElement('td');
                            td.textContent = val == null ? '' : val;
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    });
                    table.appendChild(tbody);
                    tableWrapper.appendChild(table);
                    bubble.appendChild(tableWrapper);
                }
            } catch (_) { /* パース失敗時は無視 */ }
        }

        // グラフ描画
        if (data.fig_data) {
            const graphContainer = document.createElement('div');
            graphContainer.className = 'chat-graph';
            const graphId = `graph-${Date.now()}`;
            graphContainer.id = graphId;
            bubble.appendChild(graphContainer);

            // fig_data が文字列の場合はパース
            let figData = data.fig_data;
            if (typeof figData === 'string') {
                try { figData = JSON.parse(figData); } catch { figData = null; }
            }
            if (figData && typeof Plotly !== 'undefined') {
                setTimeout(() => {
                    Plotly.newPlot(graphId, figData.data || [], figData.layout || {}, { responsive: true });
                }, 0);
            }
        }

        wrapper.appendChild(bubble);

        if (data.timestamp) {
            const meta = document.createElement('div');
            meta.className = 'chat-message__meta';
            meta.textContent = this._formatTime(data.timestamp);
            wrapper.appendChild(meta);
        }

        this.chatHistory.appendChild(wrapper);
        if (scroll) this._scrollToBottom();
        return { wrapper, bubble };
    }

    _appendErrorMessage(message, originalQuestion, userBubbleWrapper, errorCode = null) {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-message--ai';

        const bubble = document.createElement('div');
        bubble.className = 'chat-message__bubble--ai chat-message__bubble--error';
        bubble.textContent = message;
        wrapper.appendChild(bubble);

        // リトライボタン（VALIDATION_ERROR 以外）
        if (!errorCode || !['VALIDATION_ERROR', 'AUTH_ERROR'].includes(errorCode)) {
            const retryBtn = document.createElement('button');
            retryBtn.className = 'retry-button';
            retryBtn.textContent = 'リトライ';
            retryBtn.type = 'button';
            retryBtn.addEventListener('click', () =>
                this._handleRetry(originalQuestion, retryBtn, wrapper));
            bubble.appendChild(retryBtn);
        }

        this.chatHistory.appendChild(wrapper);
        this._scrollToBottom();
        return { wrapper, bubble };
    }

    // ----------------------------------------------------------------
    // UI 状態管理
    // ----------------------------------------------------------------

    _setSending(sending) {
        this._sending = sending;
        this.input.disabled = sending;
        this.submitBtn.disabled = sending || this.input.value.trim().length === 0;
        const retryList = document.querySelectorAll(".retry-button")
        retryList.forEach(function (btn) {
            btn.disabled = sending;
        });
        this.newConvBtn.disabled = sending;
    }

    _showLoading() {
        this.loadingIndicator.style.display = 'flex';
        this._scrollToBottom();
    }

    _hideLoading() {
        this.loadingIndicator.style.display = 'none';
    }

    _scrollToBottom() {
        const container = this.chatHistory.parentElement;
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    // ----------------------------------------------------------------
    // ユーティリティ
    // ----------------------------------------------------------------

    _formatTime(isoString) {
        try {
            const d = new Date(isoString);
            return d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
        } catch {
            return '';
        }
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new ChatUI();
});
