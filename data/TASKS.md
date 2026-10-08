# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-09T01:02:23`
- **進捗サマリー**: 全 **40** 話 （完了: **27** / 挿絵待ち: **2** / プロット作成済: **0** / 未着手: **11**）

## 🖥️ 各ローカルLLM PCの役割分担とノルマ

| PCホスト名 | 役割 (`role`) | 使用モデル / API | 1日あたり上限 (`daily_quota`) | 担当作業内容 |
|:---|:---|:---|:---:|:---|
| **`rtx5060lp`** | `writer` | Ollama `shosetsu` / `qwen3.5:9b` (`:11434`) | 2 話 | 小説本文・科学コラムの執筆 (`content/*.md`) |
| **`kenomac-mini`** | `illustrator` | Draw Things `FLUX.2` (`:7860`) + Ollama `gemma4:12b` | 5 枚 | 挿絵生成 (`content/*.png`) ＆ GitHub Pages (`docs/`) 更新 |
| **`sff7020`** | `director` | LM Studio `gemma-4-26b-a4b-qat` (`:1234`) | 2 件 | 先行プロット設計 (`data/plots/*.md`) ＆ 既存原稿の品質校閲 |

## 🚀 次回起動時の自動実行キュー（未完了タスク一覧）

| 話数 | タスクID | タイトル | 学部・研究室 | 現在の状態 | 次に担当するPC |
|:---:|:---|:---|:---|:---:|:---|
| #28 | `ep28-ice-core-paleoclimate-isotope-earth-science` | 南極の氷に閉じ込められた八十万年前の空気――同位体地球化学と地球の記憶 | 理学部・地球惑星環境学科 ／ 極地雪氷研究センター（古気候・同位体地球化学研究室） | `pending_illustration` | 🎨 `kenomac-mini` (挿絵生成) |
| #29 | `ep29-artificial-photosynthesis-photocatalyst-chemistry` | 太陽と水から未来の燃料を醸す葉っぱ――光触媒と人工光合成の化学 | 工学部・応用化学科 ／ 人工光合成研究センター（光触媒・太陽エネルギー変換研究室） | `pending_illustration` | 🎨 `kenomac-mini` (挿絵生成) |
| #30 | `ep30-graph-theory-four-color-theorem-math-teacher` | 白地図を彩る四色の魔法――グラフ理論とコンピュータが証明した数学のパズル | 理学部・数学科 ／ 教育学部・数学教育専攻（離散数学・グラフ理論研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #31 | `ep31-exoplanet-transit-spectroscopy-astronomy` | 幾千光年かなたの星のまばたき――系外惑星トランジット法と生命のサイン | 理学部・宇宙地球物理学科 ／ 天文学専攻（太陽系外惑星・宇宙生物学研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #32 | `ep32-gut-microbiome-brain-axis-bioscience` | お腹の中の小さな森が心を醸す――腸内フローラと『脳腸相関』の生命科学 | 農学部・応用生命化学科 ／ 薬学部・微生物薬品化学研究室（腸内細菌叢・神経免疫学） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #33 | `ep33-origami-engineering-miura-ori-space-solar-sail` | 一枚の折り紙が宇宙で翼を広げる日――ミウラ折りと折紙工学の幾何学 | 工学部・航空宇宙工学科 ／ 先端学際工学専攻（折紙工学・展開構造物研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #34 | `ep34-bioluminescence-gfp-live-cell-imaging` | オワンクラゲの緑の灯火――GFPが照らし出す生きた細胞の小宇宙 | 理学部・生物科学科 ／ 生命機能イメージング研究センター（分子細胞生物学研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #35 | `ep35-error-correcting-codes-reed-solomon-space-probe` | 傷ついたQRコードと深宇宙からの手紙――誤り訂正符号の代数幾何学 | 情報理工学部・数理情報工学科 ／ 教育学部・情報科教育専攻（符号理論・情報理論研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #36 | `ep36-superconductivity-meissner-quantum-levitation` | 液体窒素の白い霧と空中に浮かぶ磁石――超伝導と量子ピン止め効果の物理 | 理学部・物理学科 ／ 物性物理学研究所（低温物理・超伝導物質研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #37 | `ep37-circadian-rhythm-clock-genes-chronobiology` | 朝顔が咲く時刻を刻む細胞の振り子――時計遺伝子と体内時計の生物学 | 理学部・生物科学科 ／ 生命理学専攻（時間生物学・概日リズム研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #38 | `ep38-causal-inference-natural-experiment-data-science` | アイスクリームが売れると水難事故が増える？――相関と因果を見抜く統計学 | データサイエンス学部 ／ 経済・数理統計学科（統計的因果推論・教育データ科学研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #39 | `ep39-metamaterials-acoustic-cloaking-wave-physics` | 光と音を曲げる透明マントの設計図――メタマテリアルと波動の幾何学 | 工学部・物理工学科 ／ 先端フォトニクス・音響工学研究センター（波動メタマテリアル研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |
| #40 | `ep40-explainable-ai-medical-imaging-informatics-teacher` | AIの『まなざし』を言葉に翻訳する――説明可能なAI（XAI）と信頼のアルゴリズム | 情報学部・知能情報学科 ／ 教育学部・情報教育課程（人間中心AI・医療画像解析研究室） | `pending` | 📐 `sff7020` (プロット) / ✍️ `rtx5060lp` (執筆) |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | プロット (`sff7020`) | 執筆 (`rtx5060lp`) | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #27 | `ep27-autonomous-driving-slam-bayesian-informatics` | 霧のキャンパスを走る小さなロボット――ベイズ推定と自己位置推定のアルゴリズム | - | ✓ (2026-10-08) | 未校閲 | 🎨 (kenomac-mini) |
| #26 | `ep26-optogenetics-channelrhodopsin-neuroscience` | 青い光のスイッチで、眠っていた記憶が目を覚ます――光遺伝学と緑藻の贈りもの | - | ✓ (2026-10-08) | 未校閲 | 🎨 (kenomac-mini) |
| #25 | `ep25-fourier-transform-music-acoustics-math-teacher` | バイオリンの音色を数式に分解する放課後――フーリエ解析と音楽の数学 | - | ✓ (2026-10-07) | 未校閲 | 🎨 (kenomac-mini) |
| #24 | `ep24-click-chemistry-bioorthogonal-reaction` | 生きている細胞の中でパチンと留める分子のバックル――生体直交クリックケミストリー | - | ✓ (2026-10-07) | 未校閲 | 🎨 (kenomac-mini) |
| #23 | `ep23-topological-insulator-spintronics-physics` | 中身は電気を通さないのに、表面だけを電子が疾走する――トポロジカル絶縁体と次世代コンピュータ | - | ✓ (2026-10-07) | 未校閲 | 🎨 (kenomac-mini) |
| #22 | `ep22-ips-organoid-regenerative-medicine-pharmacology` | シャーレの上の小さな鼓動――iPS細胞オルガノイドと未来の創薬 | - | ✓ (2026-10-06) | 未校閲 | 🎨 (kenomac-mini) |
| #21 | `ep21-compressed-sensing-black-hole-imaging-informatics` | 地球サイズの瞳でブラックホールの影を現像する――スパースモデリングと情報科学 | - | ✓ (2026-10-06) | 未校閲 | 🎨 (kenomac-mini) |
| #20 | `ep20-turing-pattern-reaction-diffusion-math-biology` | シマウマの縞模様と熱帯魚の迷路を描く偏微分方程式――数理生物学のスケッチブック | - | ✓ (2026-10-06) | 未校閲 | 🎨 (kenomac-mini) |
| #19 | `ep19-mof-porous-coordination-polymers-carbon-capture` | 角砂糖ひと粒にサッカー場が広がる結晶――空気から水と未来を集める化学 | - | ✓ (2026-10-06) | 未校閲 | 🎨 (kenomac-mini) |
| #18 | `ep18-gravitational-waves-laser-interferometer` | 時空のさざ波を聴く地下の望遠鏡――ブラックホール連星と光の干渉計 | - | ✓ (2026-10-06) | 未校閲 | 🎨 (kenomac-mini) |
