# health-pattern-discovery
Exploring health patterns

## NHANESのダウンロード方法

NHANES（National Health and Nutrition Examination Survey）は、CDC/NCHSが公開している調査データ。

1. NHANESデータ検索ページを開く。
   - https://wwwn.cdc.gov/nchs/nhanes/search/default.aspx
2. 調査サイクル（例: 2017-2018）を選択する。
3. コンポーネント（Demographics / Dietary / Examination / Laboratory / Questionnaire / Limited Access）を選択する。
4. 対象データセットの `Data File`（XPT）と `Codebook` を確認する。
5. 必要なXPTをダウンロードし、Python/Rで読み込む。

## NHANESに記載されているデータ（網羅）

NHANESで公開されるデータの網羅的な一覧は、CDC公式のデータ検索ページに集約されている。
- NHANES Data, Documentation, Codebooks, SAS Code:
  https://wwwn.cdc.gov/nchs/nhanes/search/default.aspx

以下は、公開構造としての網羅的な分類。

### 1. Demographics
- 回答者基本属性（年齢、性別、人種/民族、教育、婚姻、世帯情報など）
- サンプリング設計・ウェイト関連項目
- 出生国・在住年数などの背景情報（サイクル依存）

### 2. Dietary
- 24時間思い出し法（Day 1 / Day 2）
- 個別食品摂取記録（Individual Foods）
- 総栄養素摂取量（Total Nutrients）
- 食行動・栄養関連質問票
- サプリメント使用データ

### 3. Examination
- 身体計測（身長、体重、BMI、腹囲など）
- 血圧、脈拍
- 歯科・口腔、皮膚、眼科、聴力などの各種身体検査
- 骨密度・身体機能関連測定
- 検査車両（MEC）で実施される各種計測

### 4. Laboratory
- 血液検査（脂質、糖代謝、腎機能、肝機能、血算など）
- 尿検査（アルブミン、クレアチニン、各種化学指標など）
- 感染症・免疫関連検査
- 環境曝露・毒性関連バイオマーカー
- 栄養・微量元素・ホルモン関連検査

### 5. Questionnaire
- 既往歴・慢性疾患
- 喫煙、飲酒、薬物使用
- 身体活動、睡眠
- メンタルヘルス
- 医療アクセス・受診歴・保険
- 生殖健康、口腔健康、職業歴、生活習慣
- 小児・高齢者向け特有項目（サイクル依存）

### 6. Limited Access
- 公開版では匿名化の都合で提供されない詳細情報
- NCHS Research Data Center（RDC）経由で申請利用する制限付きデータ

## 「どこまで網羅されているか」を確認する方法

「全データセット」「全変数」の完全な網羅はサイクルごとに変わるため、最終確認はCDC公式一覧で行う。
- データセット単位の網羅確認: `Search Variables` / コンポーネント別一覧
- 変数単位の網羅確認: 各データセットの `Codebook`

実務上は、対象サイクルを固定してから、必要なコンポーネントのCodebookを順に確認する方法が最短。
