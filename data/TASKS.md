# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-11-02T09:00:02`
- **進捗サマリー**: 全 **101** 話 （完了: **101** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **0** / プロット作成済: **0** / 未着手待機: **0**）

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
| #101 | `ep101-dna-double-helix-x-ray-diffraction-molecular-crystallography` | X線が暴いた生命の二重らせん――Photo 51と分子結晶学の真実 | `rtx5060lp` | 2026-10-31 | 未校閲 | 🎨 (kenomac-mini) |
| #100 | `ep100-accelerating-universe-dark-energy-type-ia-supernovae` | 遠ざかる光が告げる宇宙の加速――Ia型超新星と暗黒エネルギーの謎 | `rtx5060lp` | 2026-10-31 | 未校閲 | 🎨 (kenomac-mini) |
| #99 | `ep99-game-theory-nash-equilibrium-fixed-point-theorem` | 誰も裏切れない沈黙の均衡――ナッシュ均衡と不動点定理の数理経済学 | `rtx5060lp` | 2026-10-31 | 未校閲 | 🎨 (kenomac-mini) |
| #98 | `ep98-allosteric-regulation-hemoglobin-cooperativity-structural-biology` | 形を変えて酸素を手渡す四重奏――ヘモグロビンのアロステリック協同性と分子呼吸 | `rtx5060lp` | 2026-10-31 | 未校閲 | 🎨 (kenomac-mini) |
| #97 | `ep97-quantum-grovers-algorithm-amplitude-amplification` | 重ね合わせの海を照らす鏡――グローバーの量子探索と確率振幅の反転増幅 | `rtx5060lp` | 2026-10-31 | 未校閲 | 🎨 (kenomac-mini) |
| #96 | `ep96-shannon-entropy-information-theory-coding` | 曖昧さを測るサイコロの目――シャノン情報エントロピーと符号化定理の数理 | `rtx5060lp` | 2026-10-31 | 未校閲 | 🎨 (kenomac-mini) |
| #95 | `ep95-super-resolution-microscopy-sted-nanoscopy` | 回折の壁を打ち破る光のドーナツ――超解像蛍光顕微鏡（STED）と分子ナノバイオロジー | `rtx5060lp` | 2026-10-29 | 未校閲 | 🎨 (kenomac-mini) |
| #94 | `ep94-public-key-rsa-cryptography-modular-arithmetic` | 公開された南京錠と秘密の鍵――RSA公開鍵暗号と合同式の幾何学 | `rtx5060lp` | 2026-10-29 | 未校閲 | 🎨 (kenomac-mini) |
| #93 | `ep93-orbital-forcing-milankovitch-cycles-paleoclimate` | 天体の時計が刻む氷河期の鼓動――ミランコビッチ・サイクルと軌道古気候学 | `rtx5060lp` | 2026-10-29 | 未校閲 | 🎨 (kenomac-mini) |
| #92 | `ep92-monte-carlo-tree-search-alphago-game-math` | ランダムな枝が切り拓く神の一手――モンテカルロ木探索（MCTS）とゲーム数理情報学 | `rtx5060lp` | 2026-10-26 | 未校閲 | 🎨 (kenomac-mini) |
