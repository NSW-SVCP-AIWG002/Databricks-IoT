from typing import List
from langchain_core.messages import HumanMessage, BaseMessage
from conf.settings import GenieConfig


def trim_messages(
    messages: List[BaseMessage],
    max_turns: int = 5,
    max_size_bytes: int = 100 * 1024
) -> List[BaseMessage]:
    """
    メッセージリストを往復数とサイズで制限する
    
    Args:
        messages: メッセージリスト
        max_turns: 最大往復数（HumanMessageの数でカウント）
        max_size_bytes: 最大サイズ（バイト）
    
    Returns:
        制限後のメッセージリスト
    """
    if not messages:
        return messages
    
    # 1. 往復数で制限
    human_count = 0
    turn_cut_index = 0
    
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            human_count += 1
            if human_count > max_turns:
                turn_cut_index = i + 1
                break
    
    messages = messages[turn_cut_index:]
    
    # 2. サイズで制限
    total_size = 0
    size_cut_index = 0
    
    for i in range(len(messages) - 1, -1, -1):
        content = getattr(messages[i], 'content', '')
        total_size += len(str(content).encode('utf-8'))
        if total_size > max_size_bytes:
            size_cut_index = i + 1
            break
    
    return messages[size_cut_index:]

def unique_by_api(api_list):
    seen = set()
    result = []
    for item in api_list:
        if item['api'] not in seen:
            result.append(item)
            seen.add(item['api'])
    return result


def generate_genie_space_rules() -> str:
    """Genieスペース選択ルールのプロンプトを動的に生成"""
   
    spaces = GenieConfig.DATABRICKS_GENIE_SPACES
    space_names = list(spaces.keys())
   
    # 選択ルールを生成
    rules_lines = []
    for i, (space_name, config) in enumerate(spaces.items(), 1):
        # print(config)
        keywords_str = "」「".join(config["keywords"])
        # print("keywords_str", keywords_str)
        examples_str = "\n".join([f"   - 例）{ex}" for ex in config["examples"]])
       
        rule = f"""{i}. **「{space_name}」に関する要求の場合**
        - 「{keywords_str}」などのキーワードが含まれる場合
        - → `"space": "{space_name.upper()}"` を選択
        - 対象: {config['description']}
        {examples_str}"""
        rules_lines.append(rule)
   
    rules_text = "\n\n".join(rules_lines)
   
    # 出力例を生成
    output_examples = "\n\nまたは\n\n".join([
        f'```json\n{{"api": "GenieAPI", "prompt": "...", "space": "{name.upper()}"}}\n```'
        for name in space_names
    ])
   
    genie_space_rules = f"""
    ---
 
    ### 【Genieスペース自動選択ルール（厳守）】
 
    ユーザーの質問内容から、利用すべきGenieスペースを必ず判定すること。
 
    #### 利用可能なGenieスペース一覧
    {space_names}
 
    #### 選択ルール
 
    {rules_text}
 
    #### 出力形式（必須）
 
    GenieAPI を selected_apis に含める際は、以下のように
    **必ず space をセットすること（このキーが無い出力は不正）**
 
    {output_examples}
 
    ※ space には {[name.upper() for name in space_names]} のいずれかを指定すること。
 
    ---
    """
   
    return genie_space_rules
