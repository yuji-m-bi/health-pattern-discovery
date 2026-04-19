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


# 取得したデータ
## 1 基本属性
分析の メインテーブル
Demographics

| ファイル         | 内容          | 重要度 |
| ------------ | ----------- | --- |
| `DEMO_J.XPT` | 年齢・性別・人種・所得 | 必須  |

SEQN       個人ID
RIDAGEYR   年齢
RIAGENDR   性別
RIDRETH1   人種
INDFMPIR   所得指標

## 2 身体データ
健康状態の中心指標
Body Measures
Blood Pressure

| ファイル        | 内容        | 重要度 |
| ----------- | --------- | --- |
| `BMX_J.XPT` | BMI・身長・体重 | 必須  |
| `BPX_J.XPT` | 血圧        | 必須  |

BMXBMI  BMI
BPXSY1  収縮期血圧
BPXDI1  拡張期血圧

## 3 血液検査（代謝）
糖尿病や脂質代謝
Laboratory
Plasma Fasting Glucose
Cholesterol - High - Density Lipoprotein (HDL)
Cholesterol - Low-Density Lipoproteins (LDL) & Triglycerides

| ファイル           | 内容         | 重要度 |
| -------------- | ---------- | --- |
| `GLU_J.XPT`    | 血糖         | 重要  |
| `HDL_J.XPT`    | HDLコレステロール | 重要  |
| `TRIGLY_J.XPT` | 中性脂肪       | 重要  |

## 4 生活習慣
Questionnaire
Physical Activity
Sleep Disorders
Smoking - Cigarette Use
Alcohol Use

| ファイル        | 内容    |
| ----------- | ----- |
| `PAQ_J.XPT` | 運動    |
| `SLQ_J.XPT` | 睡眠    |
| `SMQ_J.XPT` | 喫煙    |
| `ALQ_J.XPT` | アルコール |

## 5 食事
Dietary
Dietary Interview - Total Nutrient Intakes, First Day

| ファイル           | 内容     |
| -------------- | ------ |
| `DR1TOT_J.XPT` | 1日栄養摂取 |


# データの結合
NHANESは SEQNで結合
DEMO
  +
BMX
  +
BPX
  +
GLU
  +
PAQ
## データ結合スクリプト（自動で全XPTを対象）
`src/merge_nhanes.py` を使うと、指定フォルダ内の `*.xpt` をすべて読み込み、`SEQN` で自動結合できます。

```bash
python src/merge_nhanes.py --data-dir data/2017_2018
```

CSV保存したい場合:

```bash
python src/merge_nhanes.py --data-dir data/2017_2018 --output data/merged/nhanes_2017_2018.csv
```

## 健康クラスタ探索（糖尿病予備群に近い集団の探索）

結合済みデータに対して、PCA + KMeans で健康クラスタを探索するスクリプトを追加しています。

- スクリプト: `src/nhanes_health_cluster_analysis.py`
- 特徴:
  - 候補列から「実在する列のみ」を自動採用
  - 欠損処理を `drop` / `median` で切替可能
  - PCA寄与率表示、PCA散布図、シルエット比較（k=2〜6）
  - 血糖をPCA入力に「入れる版 / 除外版」の両方を実行
  - クラスタ別に血糖平均と前糖尿病域割合（100〜125 mg/dL）を比較

実行例:

```bash
python src/nhanes_health_cluster_analysis.py
```

`df` が notebook 上ですでにある場合は、`run_analysis(df)` を直接呼び出せます。


## クラスタリング実行フロー（merge_nhanes.py との接続）

はい、`python src/merge_nhanes.py` で作成した結合CSVを、そのままクラスタリング入力として使う前提です。

1. まずXPTを結合
```bash
python src/merge_nhanes.py --data-dir data/2017_2018 --output data/merged/nhanes_2017_2018.csv
```

2. 次にKMeans分析（手法別ファイル）
```bash
python src/cluster_kmeans.py --input data/merged/nhanes_2017_2018.csv --output-dir outputs/kmeans
```

### 手法別ファイル構成
- `src/cluster_common.py`: 前処理・列選択・PCAなど共通処理
- `src/cluster_kmeans.py`: KMeans分析本体
- `src/nhanes_health_cluster_analysis.py`: 後方互換ラッパー（内部でKMeansを呼び出し）

### kごとの図の保存
`cluster_kmeans.py` は次を保存します（with_glucose / without_glucose それぞれ）:
- `*_kmeans_k2.png` ... `*_kmeans_k6.png`（kごとの個別図）
- `*_kmeans_all_k.png`（k=2〜6を1枚にまとめた比較図）

補足: `without_glucose` ではPCA入力から血糖列を外しますが、比較表示のため血糖列は別途保持して集計します。
以前の `[without_glucose] LBXGLU が無いため比較不可` は実装上の保持漏れで、食事データ不足が原因ではありません。

## 初心者向け: このコードから何を判断すればよいか

### まず押さえる結論（このリポジトリで言えること）
- **NHANES 2017-2018 の公開データを横断結合**し、体格・血圧・血糖・脂質・生活習慣を1人単位でまとめて見られる。
- **KMeansクラスタ**により、似た健康プロファイルの集団を分け、
  - どの集団で血糖が高めか
  - 前糖尿病域（100〜125 mg/dL）の人がどれくらいいるか
  を比較できる。
- つまり「診断」ではなく、**集団の傾向（どんな人にリスクが集まりやすいか）を探索する分析**。

### 判断の流れ（初心者向け）
1. **データ品質の確認**: 欠損が多すぎないか（`drop`だと標本が減る）。
2. **クラスタの妥当性**: シルエット係数が最も高い `k` を採用。
3. **クラスタ解釈**: `BMXBMI`, `BPXSY1`, `LBXTR`, `LBDHDD`, `LBXGLU` の平均で特徴づける。
4. **意思決定に使う**:
   - 前糖尿病比率が高いクラスタ → 生活習慣介入の優先対象候補
   - BMI/血圧/脂質が同時に高いクラスタ → 複合リスク群として重点フォロー
5. **注意点**:
   - NHANESは横断調査なので「因果」は言えない
   - サンプルウェイトを使わない集計は全国推定値とはズレうる

## 追加実装: dfからアピールしやすいアウトプットを作る

クラスタ分析に加え、初心者にも伝わりやすい「リスク有病率」「年代/性別差」「リスク組み合わせ」を自動出力するスクリプトを追加しました。

- スクリプト: `src/nhanes_decision_guide.py`
- 出力:
  - `nhanes_with_risk_flags.csv`（各個人のリスクフラグ）
  - `risk_prevalence.csv`（全体有病率）
  - `risk_by_sex.csv`（性別比較）
  - `risk_by_age_band.csv`（年代比較）
  - `risk_combo_top10.csv`（リスクの同時保有パターン）
  - `top_glucose_correlations.csv`（血糖と相関が高い特徴）

実行例:

```bash
python src/nhanes_decision_guide.py --input data/merged/nhanes_2017_2018.csv --output-dir outputs/decision_guide
```

### これで何が言いやすくなるか（発表・ポートフォリオ向け）
- 「前糖尿病疑いは全体の何%か」
- 「どの年代・性別で複数リスクの重なりが目立つか」
- 「血糖に相関する因子（BMI・脂質・血圧など）の優先順位」

この3点があると、単なるクラスタ図だけでなく、**施策優先度の説明**までつなげやすくなります。
