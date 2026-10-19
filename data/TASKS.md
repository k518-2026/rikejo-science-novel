# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-19T09:01:08`
- **進捗サマリー**: 全 **75** 話 （完了: **69** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **5** / プロット作成済: **0** / 未着手待機: **1**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| #70 | `ep70-graph-isomorphism-automata-computational-theory-coding` | 図の形が変えても同じなら―グラフ同型問題と計算複雑性のパズル (コンピュータが『この二つの迷路は本当に同じ形状か』を瞬時に判断できるかを問う「グラフ同型問題」と、その解法にまつわる対称性・不変量や量子アルゴリズムの可能性) | 理学部数学科／計算機科学分野（理論情報学研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #71 | `ep71-topological-data-analysis-persistence-homology-ai-coding` | 形が崩れても残る穴―トポロジカルデータ分析とAIの幾何学 (点雲や画像から『環』や『球面』のような本質的な形状（ホモロジー）を抽出する「位相的データ解析」と、機械学習における特徴量の新しい捉え方) | 理学部数学科／応用数学分野（トポロジカルデータ分析研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #72 | `ep72-finite-field-cryptography-elliptic-curves-security` | 有限の世界で織りなす安全の鎖―楕円曲線暗号と数理情報セキュリティ (整数ではなく「余りの世界（有限体）」での計算を行う数論幾何学が、現代通信の鍵となる『楕円曲線暗号』を解明する) | 理学部数学科／代数幾何学分野（サイバー数学研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #73 | `ep73-quantum-sensing-magnetometry-biophysics-coding-healthcare` | 磁場が揺れる瞬間を捉える―量子センシングと生体分子の探査 (原子レベルのスピン状態を検出する「超感応磁力計（NVセンターなど）」を用いて、細胞内の微小な磁性変化や酵素反応を追跡する技術) | 理学部物理学科／量子光学分野（ナノバイオサイエンス研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #74 | `ep74-stochastic-differential-equations-finance-bio-math-coding` | ブラウン運動の先にある未来―確率微分方程式と不確定性のモデル化 (ランダムな歩行（ブラウン運動）や株式価格変動を記述する「ストキャスティック・ディファレンシャル・エクス」を用いて、予測不能な現象からパターンを見出す) | 理学部数学科／確率統計分野（数理金融・リスク管理研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #75 | `ep75-adaptive-algorithms-genetic-programming-evolution-computing-coding` | 自我を進化させるプログラム―適応型アルゴリズムと遺伝的プログラミング (生物の進化のようにコードが自己改良する「ゲネティック・プログラミング」を用いて、多様化する環境に対応できる自律エージェントを創り出す) | 工学部情報工学科／人工知能分野（進化的計算研究室） | `pending` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #69 | `ep69-prime-numbers-bounded-gaps-analytic-number-theory` | 無限の星屑に潜む等差数列――素数の間隔と解析的数論の地平 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #68 | `ep68-cryosphere-ice-albedo-feedback-climate` | 白い氷が世界を冷ます――海氷アルベドフィードバックと極域気候科学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #67 | `ep67-metal-organic-frameworks-porous-materials` | スプーン一杯に広がるサッカー場――金属有機構造体（MOF/PCP）とナノ細孔の化学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #66 | `ep66-paleomagnetism-geomagnetic-reversal-chiba-period` | 地層の砂粒が記憶した北と南――地磁気逆転の古地磁気学とチバニアンの地球科学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #65 | `ep65-dna-computing-molecular-automata-biomath` | 試験管で巡る最短ルート――DNA分子コンピューティングと自律型ナノオートマトン | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #64 | `ep64-metrology-optical-lattice-clock-space-time` | 時空の歪みを測る光の格子――18桁精度の光格子時計と相対論的測地学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #63 | `ep63-epigenetics-dna-methylation-chromatin-biology` | 塩基配列の向こうに灯るスイッチ――エピジェネティクスと運命の分子生物学 | `rtx5060lp` | 2026-10-17 | 未校閲 | 🎨 (kenomac-mini) |
| #62 | `ep62-supercritical-fluid-green-chemistry-materials` | 気体と液体の境界が溶け合う場所――超臨界流体とグリーンケミストリー | `rtx5060lp` | 2026-10-17 | 未校閲 | 🎨 (kenomac-mini) |
| #61 | `ep61-gravitational-lensing-dark-matter-astrophysics` | 時空の歪みが映す光のリング――重力レンズ効果と見えない暗黒物質 | `rtx5060lp` | 2026-10-17 | 未校閲 | 🎨 (kenomac-mini) |
| #60 | `ep60-wilson-cloud-chamber-positron-particle-physics` | 霧の小宇宙を切り裂く光の軌跡――ウィルソンの霧箱と反物質の発見 | `rtx5060lp` | 2026-10-17 | 未校閲 | 🎨 (kenomac-mini) |
