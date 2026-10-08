# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-08T21:37:40`
- **進捗サマリー**: 全 **40** 話 （完了: **28** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **5** / プロット作成済: **0** / 未着手待機: **7**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| #29 | `ep29-artificial-photosynthesis-photocatalyst-chemistry` | 太陽と水から未来の燃料を醸す葉っぱ――光触媒と人工光合成の化学 | 工学部・応用化学科 ／ 人工光合成研究センター（光触媒・太陽エネルギー変換研究室） | `queued` | 🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調) |
| #30 | `ep30-graph-theory-four-color-theorem-math-teacher` | 白地図を彩る四色の魔法――グラフ理論とコンピュータが証明した数学のパズル | 理学部・数学科 ／ 教育学部・数学教育専攻（離散数学・グラフ理論研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #31 | `ep31-exoplanet-transit-spectroscopy-astronomy` | 幾千光年かなたの星のまばたき――系外惑星トランジット法と生命のサイン | 理学部・宇宙地球物理学科 ／ 天文学専攻（太陽系外惑星・宇宙生物学研究室） | `queued` | 🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調) |
| #32 | `ep32-gut-microbiome-brain-axis-bioscience` | お腹の中の小さな森が心を醸す――腸内フローラと『脳腸相関』の生命科学 | 農学部・応用生命化学科 ／ 薬学部・微生物薬品化学研究室（腸内細菌叢・神経免疫学） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #33 | `ep33-origami-engineering-miura-ori-space-solar-sail` | 一枚の折り紙が宇宙で翼を広げる日――ミウラ折りと折紙工学の幾何学 | 工学部・航空宇宙工学科 ／ 先端学際工学専攻（折紙工学・展開構造物研究室） | `queued` | 🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調) |
| #34 | `ep34-bioluminescence-gfp-live-cell-imaging` | オワンクラゲの緑の灯火――GFPが照らし出す生きた細胞の小宇宙 | 理学部・生物科学科 ／ 生命機能イメージング研究センター（分子細胞生物学研究室） | `pending` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #35 | `ep35-error-correcting-codes-reed-solomon-space-probe` | 傷ついたQRコードと深宇宙からの手紙――誤り訂正符号の代数幾何学 | 情報理工学部・数理情報工学科 ／ 教育学部・情報科教育専攻（符号理論・情報理論研究室） | `pending` | 🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調) |
| #36 | `ep36-superconductivity-meissner-quantum-levitation` | 液体窒素の白い霧と空中に浮かぶ磁石――超伝導と量子ピン止め効果の物理 | 理学部・物理学科 ／ 物性物理学研究所（低温物理・超伝導物質研究室） | `pending` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #37 | `ep37-circadian-rhythm-clock-genes-chronobiology` | 朝顔が咲く時刻を刻む細胞の振り子――時計遺伝子と体内時計の生物学 | 理学部・生物科学科 ／ 生命理学専攻（時間生物学・概日リズム研究室） | `pending` | 🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調) |
| #38 | `ep38-causal-inference-natural-experiment-data-science` | アイスクリームが売れると水難事故が増える？――相関と因果を見抜く統計学 | データサイエンス学部 ／ 経済・数理統計学科（統計的因果推論・教育データ科学研究室） | `pending` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #39 | `ep39-metamaterials-acoustic-cloaking-wave-physics` | 光と音を曲げる透明マントの設計図――メタマテリアルと波動の幾何学 | 工学部・物理工学科 ／ 先端フォトニクス・音響工学研究センター（波動メタマテリアル研究室） | `pending` | 🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調) |
| #40 | `ep40-explainable-ai-medical-imaging-informatics-teacher` | AIの『まなざし』を言葉に翻訳する――説明可能なAI（XAI）と信頼のアルゴリズム | 情報学部・知能情報学科 ／ 教育学部・情報教育課程（人間中心AI・医療画像解析研究室） | `pending` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #28 | `ep28-ice-core-paleoclimate-isotope-earth-science` | 南極の氷に閉じ込められた八十万年前の空気――同位体地球化学と地球の記憶 | `rtx5060lp` | 2026-10-08 | 未校閲 | 🎨 (kenomac-mini) |
| #27 | `ep27-autonomous-driving-slam-bayesian-informatics` | 霧のキャンパスを走る小さなロボット――ベイズ推定と自己位置推定のアルゴリズム | `rtx5060lp` | 2026-10-08 | 未校閲 | 🎨 (kenomac-mini) |
| #26 | `ep26-optogenetics-channelrhodopsin-neuroscience` | 青い光のスイッチで、眠っていた記憶が目を覚ます――光遺伝学と緑藻の贈りもの | `rtx5060lp` | 2026-10-08 | 未校閲 | 🎨 (kenomac-mini) |
| #25 | `ep25-fourier-transform-music-acoustics-math-teacher` | バイオリンの音色を数式に分解する放課後――フーリエ解析と音楽の数学 | `rtx5060lp` | 2026-10-07 | 未校閲 | 🎨 (kenomac-mini) |
| #24 | `ep24-click-chemistry-bioorthogonal-reaction` | 生きている細胞の中でパチンと留める分子のバックル――生体直交クリックケミストリー | `rtx5060lp` | 2026-10-07 | 未校閲 | 🎨 (kenomac-mini) |
| #23 | `ep23-topological-insulator-spintronics-physics` | 中身は電気を通さないのに、表面だけを電子が疾走する――トポロジカル絶縁体と次世代コンピュータ | `rtx5060lp` | 2026-10-07 | 未校閲 | 🎨 (kenomac-mini) |
| #22 | `ep22-ips-organoid-regenerative-medicine-pharmacology` | シャーレの上の小さな鼓動――iPS細胞オルガノイドと未来の創薬 | `rtx5060lp` | 2026-10-06 | 未校閲 | 🎨 (kenomac-mini) |
| #21 | `ep21-compressed-sensing-black-hole-imaging-informatics` | 地球サイズの瞳でブラックホールの影を現像する――スパースモデリングと情報科学 | `rtx5060lp` | 2026-10-06 | 未校閲 | 🎨 (kenomac-mini) |
| #20 | `ep20-turing-pattern-reaction-diffusion-math-biology` | シマウマの縞模様と熱帯魚の迷路を描く偏微分方程式――数理生物学のスケッチブック | `rtx5060lp` | 2026-10-06 | 未校閲 | 🎨 (kenomac-mini) |
| #19 | `ep19-mof-porous-coordination-polymers-carbon-capture` | 角砂糖ひと粒にサッカー場が広がる結晶――空気から水と未来を集める化学 | `rtx5060lp` | 2026-10-06 | 未校閲 | 🎨 (kenomac-mini) |
