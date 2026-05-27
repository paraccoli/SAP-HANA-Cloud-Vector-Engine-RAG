# システムアーキテクチャ設計図

本システムは、SAP HANA Cloud の Vector Engine と Google Gemini API (LangChain経由) を融合したエンタープライズ文書検索（RAG）システムです。データフローは大きく分けて「ドキュメント・インジェスト（データ蓄積）」と「RAGクエリ（検索・回答生成）」の2つで構成されます。

---

## 1. ドキュメント・インジェストフロー
ローカルのPDFドキュメント（SAPヘルプや役割定義書など）を読み込み、適切なサイズにチャンク分割したうえでベクトル化し、SAP HANA Cloud に永続化する流れです。

```mermaid
flowchart TD
    subgraph Source [1. 文書ソース層]
        PDF["PDFドキュメント (data/raw/*.pdf)"]
    end
    
    subgraph Preprocess [2. 前処理・Embedding層]
        Loader["PyPDFLoader (LangChain)"]
        Splitter["RecursiveCharacterTextSplitter<br>(chunk_size=512, overlap=64)"]
        Embed["GoogleGenerativeAIEmbeddings<br>(models/gemini-embedding-001)"]
    end
    
    subgraph VectorStore [3. ベクトルストア層]
        HANA[("SAP HANA Cloud<br>(REAL_VECTOR型 / テーブル名: SAP_RAG_DOCS)")]
    end
    
    PDF --> Loader
    Loader -->|文書ロード| Splitter
    Splitter -->|テキストチャンク分割| Embed
    Embed -->|768次元ベクトル化| HANA
```

---

## 2. RAGクエリ（検索・回答生成）フロー
ユーザーが質問を投げてから、HANA DBによる高速なベクトル類似度検索（内蔵のCOSINE_SIMILARITY関数）を実行し、得られた関連文書をコンテキストとしてGemini LLMに与え、正確な回答を生成する流れです。

```mermaid
flowchart TD
    UserInput([ユーザーの質問])
    
    subgraph Retrieval [1. 検索・抽出層]
        Query["質問テキスト"]
        EmbedQuery["GoogleGenerativeAIEmbeddings<br>(クエリのベクトル化)"]
        HANADB[("SAP HANA Cloud")]
        SQL["SQL検索<br>(COSINE_SIMILARITYによるTop-3検索)"]
        Context["関連する文書コンテキスト (Top-3)"]
    end
    
    subgraph Generation [2. 生成層]
        Prompt["RAGプロンプトテンプレート"]
        LLM["Google Gemini 3.5 Flash"]
        Answer["回答テキスト"]
    end
    
    UserInput --> Query
    Query --> EmbedQuery
    EmbedQuery -->|クエリベクトル送信| HANADB
    HANADB -->|Vector Engineによる類似度判定| SQL
    SQL -->|Top-3のチャンク抽出| Context
    
    Query --> Prompt
    Context -->|文脈追加| Prompt
    Prompt --> LLM
    LLM -->|グラウンディングされた回答| Answer
    Answer --> UserInput
```
