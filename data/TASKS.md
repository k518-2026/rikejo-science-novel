# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-11-24T09:00:01`
- **進捗サマリー**: 全 **136** 話 （完了: **136** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **0** / プロット作成済: **0** / 未着手待機: **0**）

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
| #136 | `ep136-gamification-learning-analytics-adaptive-curriculum-design-systems` | ゲーミフィケーションで描く学習の最適解――ゲーム理論と適応型カリキュラム設計 (有限な資源（時間）内で最大の達成度を得るための戦略を『ナッシュ均衡』や『動的計画法』を用いてモデル化。生徒それぞれに最適な課題提示を行うアダプティブ・ラーニングシステムの構築を通じて、教育工学のデータドリブンアプローチを描く)  | `rtx5060lp` | 2026-11-23 | 未校閲 | 🎨 (kenomac-mini) |
| #135 | `ep135-blockchain-cryptography-hash-function-decentralized-identity-systems` | 改ざん不可能な鎖を紡ぐ暗号理論――ブロックチェーンとハッシュ関数の数学的証明 (非対称鍵暗号や椭圆曲線暗号を用いた分散型台帳技術。一人の学生が持つ学歴・成績データを『デジタルアイデンティティ』として安全に管理するシステム構築を通じて、数論（素因数分解）と情報セキュリティの実用性を描く)  | `rtx5060lp` | 2026-11-23 | 未校閲 | 🎨 (kenomac-mini) |
| #134 | `ep134-cybernetics-control-theory-bipedal-robot-walking-mechanics` | 反発のバネで歩く制御論――サイバーネティクスと二足歩行ロボットの力学 (ニュートン・オイラー方程式に基づく運動量保存則を逆算し、エネルギー回復型スプリングローダー機構を用いた自律性あるくロボット開発。『フィードバックループ』という概念を実際の物理動作に落とし込み、制御工学の美しさを感じる物語)  | `rtx5060lp` | 2026-11-23 | 未校閲 | 🎨 (kenomac-mini) |
| #133 | `ep133-fractal-geometry-polymer-synthesis-nanoreactor-biology` | 自己相似の樹海を歩く分形合成――フラクタル幾何とポリマーナノリアクター (自然界に存在する『コルネット構造』のような無限の細分化を持つフラクタル形状（マンデルブロ集合やカントール曲線）を用いた多孔質材料設計。微小な反応槽内での物質拡散を最適化し、高効率な薬物送達システムを開発する高分子化学と分形幾何学) | `rtx5060lp` | 2026-11-23 | 未校閲 | 🎨 (kenomac-mini) |
| #132 | `ep132-manifold-learning-dimensionality-reduction-neural-net-teacher` | データの皺が描く多様体の地形――マニフォールド学習と教師となるアルゴリズムの美学 (高次元空間におけるデータを低次元多様体へ埋め込む「マンifold learning」。複雑な人間関係や教育現場のパターンを幾何学的に可視化し、AI 支援システムを開発する数学的アプローチ。文化祭での AI アート展示とプログラミング部との合同開発を描く計算機科学・応用代数) | `rtx5060lp` | 2026-11-23 | 未校閲 | 🎨 (kenomac-mini) |
| #131 | `ep131-topological-data-analysis-persistent-homology-data-shape` | データの雲が結ぶかたちの輪郭――トポロジカルデータ解析とパーシステントホモロジー | `rtx5060lp` | 2026-11-21 | 未校閲 | 🎨 (kenomac-mini) |
| #130 | `ep130-optical-tweezers-radiation-pressure-single-molecule-biophysics` | 光の指先が触れるナノの鼓動――光ピンセットと単一分子生物物理学 | `rtx5060lp` | 2026-11-21 | 未校閲 | 🎨 (kenomac-mini) |
| #129 | `ep129-gravitational-lensing-dark-matter-einstein-ring` | 歪んだ星影が暴く見えない質量――重力レンズ効果とダークマターの天体物理学 | `rtx5060lp` | 2026-11-21 | 未校閲 | 🎨 (kenomac-mini) |
| #128 | `ep128-cryo-electron-microscopy-vitrification-resolution-revolution` | 極冷の氷に凍結された生命の鼓動――クライオ電子顕微鏡と原子分解能の革命 | `rtx5060lp` | 2026-11-19 | 未校閲 | 🎨 (kenomac-mini) |
| #127 | `ep127-microfluidics-lab-on-a-chip-laminar-flow-biochemistry` | 一滴の液体が巡る微小な迷宮――マイクロ流体工学とチップ上の実験室 | `rtx5060lp` | 2026-11-19 | 未校閲 | 🎨 (kenomac-mini) |
