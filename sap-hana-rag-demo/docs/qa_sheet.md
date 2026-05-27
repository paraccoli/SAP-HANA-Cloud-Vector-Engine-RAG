# 評価用QAセット（20問）

本システムおよびベンチマーク評価で使用する、手動作成された20問のQAセット一覧です。
これらの質問は、インプットした各種PDF資料（SAP HANA Cloudの導入ガイド、機能範囲書、管理者ガイド）に記載されている事実に基づいて設計されています。

---

## QAリスト一覧

| ID | 質問内容 (Query) | 期待される参照ソース (Expected Source) | 期待ページ | 対象トピック |
| :---: | :--- | :--- | :---: | :--- |
| **1** | SAP HANA Cloud 入門ガイドの主な目的と、それが何に適合するように設計されているか教えてください。 | `hana_cloud_intro_ja.pdf` | 0 | 導入・全体像 |
| **2** | SAP HANA Cloud の管理と開発のために提供されているツールには何がありますか？ | `hana_cloud_intro_ja.pdf` | 0 | 管理・開発ツール |
| **3** | SAP HANA Cloud におけるデータ階層化（Data Tiering）の概念について説明してください。 | `hana_cloud_intro_ja.pdf` | 1 | データ階層化 |
| **4** | SAP BTP サブアカウントで利用可能な SAP HANA Cloud の初期設定やアクセス方法について教えてください。 | `hana_cloud_intro_ja.pdf` | 1 | 初期設定・BTP |
| **5** | SAP HANA Cloud でサポートされている主要なデータベース技術（エンジン）の構成は何ですか？ | `hana_cloud_intro_ja.pdf` | 1 | サポートエンジン |
| **6** | On which cloud infrastructures (hyperscalers) is SAP HANA Cloud available? | `hana_cloud_feature_scope_en.pdf` | 2 | インフラ・環境 |
| **7** | What is the purpose of the Feature Scope Description document for SAP HANA Cloud? | `hana_cloud_feature_scope_en.pdf` | 2 | 機能範囲概要 |
| **8** | Does SAP HANA Cloud support Spatial and Property Graph data processing? | `hana_cloud_feature_scope_en.pdf` | 8 | 特殊データ型 |
| **9** | What are the capabilities of the JSON Document Store (DocStore) in SAP HANA Cloud? | `hana_cloud_feature_scope_en.pdf` | 9 | ドキュメントDB機能 |
| **10** | What is the maximum number of dimensions supported by the REAL_VECTOR type in SAP HANA Cloud? | `hana_cloud_feature_scope_en.pdf` | 7 | ベクトル型上限次元数 |
| **11** | Does SAP HANA Cloud Vector Engine support cosine similarity and L2 distance? | `hana_cloud_feature_scope_en.pdf` | 7 | 類似度・検索関数 |
| **12** | How is Machine Learning supported in SAP HANA Cloud? Mention the main libraries. | `hana_cloud_feature_scope_en.pdf` | 13 | 機械学習機能 |
| **13** | What is the default port and connection type used for connecting to SAP HANA Cloud? | `sap-hana-cloud-manage-guide.pdf` | 25 | ネットワーク・接続ポート |
| **14** | How can an administrator temporarily stop or restart an active SAP HANA Cloud instance? | `sap-hana-cloud-manage-guide.pdf` | 50 | インスタンス操作 |
| **15** | Explain how database backups are created and what the retention period is in SAP HANA Cloud. | `sap-hana-cloud-manage-guide.pdf` | 82 | バックアップと保持期間 |
| **16** | What are the prerequisite roles or privileges required to access SAP HANA Cloud Central? | `sap-hana-cloud-manage-guide.pdf` | 15 | 管理者権限 |
| **17** | What is SAP HANA Native Storage Extension (NSE) and how does it optimize storage costs? | `sap-hana-cloud-manage-guide.pdf` | 120 | ストレージ最適化 (NSE) |
| **18** | How are security and network access restricted (such as IP Whitelisting) in SAP HANA Cloud? | `sap-hana-cloud-manage-guide.pdf` | 40 | セキュリティ・接続制限 |
| **19** | What is the role of SAP BTP Cockpit in managing HANA Cloud instances? | `sap-hana-cloud-manage-guide.pdf` | 12 | BTP管理 |
| **20** | Does SAP HANA Cloud support automatic database scaling (compute and storage)? | `sap-hana-cloud-manage-guide.pdf` | 62 | オートスケーリング |

---

## 期待ページの扱いについて
* PDFから抽出されたテキストデータは、PyPDFLoaderによって0から始まるインデックス（0-based page）でメタデータ `page` に格納されています。
* 評価スクリプトでの Hit Rate 算出時、この期待ページ番号と合致するかどうかが「Page-level Hit Rate」の正解条件となります。
