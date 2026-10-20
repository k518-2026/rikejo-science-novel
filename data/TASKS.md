# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-20T09:00:01`
- **進捗サマリー**: 全 **75** 話 （完了: **75** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **0** / プロット作成済: **0** / 未着手待機: **0**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| - | - | （全エピソード完了済み・次回起動時に新規テーマ自動生成） | - | Completed | `sff7020` / `rtx5060lp` |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #75 | `ep75-genetic-programming-symbolic-regression-evolution` | 数式が自ら進化する樹木――遺伝的プログラミングと記号回帰のアルゴリズム | `rtx5060lp` | 2026-10-20 | 未校閲 | 🎨 (kenomac-mini) |
| #74 | `ep74-atmospheric-photochemistry-ozone-hole-catalysis` | 極夜の成層圏が解いた塩素の連鎖――オゾン層破壊の光化学と地球の盾 | `rtx5060lp` | 2026-10-20 | 未校閲 | 🎨 (kenomac-mini) |
| #73 | `ep73-quantum-sensing-diamond-nv-center` | ダイヤモンドの傷が診る生体分子――NVセンターと極限量子センシング | `rtx5060lp` | 2026-10-20 | 未校閲 | 🎨 (kenomac-mini) |
| #72 | `ep72-finite-field-cryptography-elliptic-curves-security` | 有限の世界で織りなす安全の鎖――楕円曲線暗号と数論幾何学のセキュリティ | `rtx5060lp` | 2026-10-19 | 未校閲 | 🎨 (kenomac-mini) |
| #71 | `ep71-quantum-dots-nanocrystals-colloidal-chemistry` | 大きさが色を決めるナノの魔法――量子ドットとコロイド半導体化学 | `rtx5060lp` | 2026-10-19 | 未校閲 | 🎨 (kenomac-mini) |
| #70 | `ep70-graph-isomorphism-complexity-quasipolynomial` | 見かけが違っても同じ構造――グラフ同型問題と計算複雑性の迷宮 | `rtx5060lp` | 2026-10-19 | 未校閲 | 🎨 (kenomac-mini) |
| #69 | `ep69-prime-numbers-bounded-gaps-analytic-number-theory` | 無限の星屑に潜む等差数列――素数の間隔と解析的数論の地平 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #68 | `ep68-cryosphere-ice-albedo-feedback-climate` | 白い氷が世界を冷ます――海氷アルベドフィードバックと極域気候科学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #67 | `ep67-metal-organic-frameworks-porous-materials` | スプーン一杯に広がるサッカー場――金属有機構造体（MOF/PCP）とナノ細孔の化学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
| #66 | `ep66-paleomagnetism-geomagnetic-reversal-chiba-period` | 地層の砂粒が記憶した北と南――地磁気逆転の古地磁気学とチバニアンの地球科学 | `rtx5060lp` | 2026-10-18 | 未校閲 | 🎨 (kenomac-mini) |
