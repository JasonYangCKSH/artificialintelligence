以下是你這段程式中**所有 function 的第一行（定義行）**整理成條列式：

* `def opponent(color: int) -> int:`
* `def create_board(size: int):`
* `def in_bounds(x: int, y: int, size: int) -> bool:`
* `def board_full(board) -> bool:`
* `def count_dir(board, x: int, y: int, dx: int, dy: int, color: int) -> int:`
* `def line_total(board, x: int, y: int, dx: int, dy: int, color: int) -> int:`
* `def is_overline_after_move(board, x: int, y: int, color: int) -> bool:`
* `def is_exact_five_after_move(board, x: int, y: int, color: int) -> bool:`
* `def is_win_after_move(board, x: int, y: int, color: int) -> bool:`
* `def is_open_four_in_direction(board, x: int, y: int, color: int, dx: int, dy: int) -> bool:`
* `def has_four_in_direction_for_black(board, x: int, y: int, dx: int, dy: int) -> bool:`
* `def has_open_three_in_direction_for_black(board, x: int, y: int, dx: int, dy: int) -> bool:`
* `def count_black_four_directions(board, x: int, y: int) -> int:`
* `def count_black_open_three_directions(board, x: int, y: int) -> int:`
* `def is_black_forbidden_after_move(board, x: int, y: int) -> bool:`
* `def is_legal_move(board, x: int, y: int, color: int) -> bool:`
* `def legal_moves(board, color: int):`
* `def format_board(board) -> str:`
* `def occupied_neighbors(board, x: int, y: int, radius: int = 1) -> int:`
* `def is_empty_board(board) -> bool:`

# 五子棋 AI 白方設計思路

## 🎯 核心優勢：白方天生不對稱

白方最大的戰略資產是**黑方有禁手**。大師級工程師會把這個不對稱性貫穿整個 AI 設計。

---

## 🧠 一、搜尋架構

### 主幹：Negamax + Alpha-Beta Pruning
```
最基本要做的，但光這樣不夠
```

### 進階：**Threat-Space Search (TSS)**
> 這是真正的分水嶺

不要用暴力搜尋所有合法走法，而是**只搜尋有威脅意義的節點**：

```
威脅樹 = {
    四（活四/衝四）,
    三（活三）,
    對敵方威脅的防守點
}
```

一般 Negamax 搜到深度 6 很吃力，TSS 可以快速找到深度 20+ 的強制勝利序列。

### 更進階：**Proof Number Search (PNS)**
專門用來**證明或反證某個局面是必勝/必敗**，對殘局極有效。

---

## 💡 二、原創性建議（非教科書內容）

### 1. 「禁手誘導」策略模組
```python
# 白方專屬：主動引導黑方走進禁手陷阱
def forbidden_trap_score(board, x, y, color):
    """
    如果白方落在(x,y)後，
    能讓黑方的最優應對點變成禁手位，
    給予額外高分
    """
```
這是白方獨有的戰術，黑方 AI 完全不需要考慮這個維度。

---

### 2. 雙層評估函數（局面 vs 潛力）

| 層次 | 評估什麼 | 權重 |
|------|---------|------|
| 靜態分 | 當前棋型分布 | 60% |
| 動態分 | 未來 2 步能形成的威脅數量 | 40% |

大多數業餘 AI 只做靜態分，動態分才是高手的秘密。

---

### 3. **Killer Move Heuristic + History Table**
```
不同局面下，同一個走法如果曾經造成剪枝，
記錄它，下次優先嘗試 → 大幅提升 Alpha-Beta 效率
```

---

### 4. 棋型識別用 **Bitboard**
```python
# 用 64-bit integer 表示棋盤行/列/斜線
# 連子檢查變成 bit shift 操作，速度快 10-50 倍
horizontal = board_bits >> 1 & board_bits  # 兩連
horizontal2 = horizontal >> 1 & board_bits  # 三連
```

---

## 🏗️ 三、大師工程師的完整架構

```
┌─────────────────────────────────────┐
│           白方 AI 主控              │
├─────────────────────────────────────┤
│  候選點生成                          │
│  ├─ 威脅點（進攻）                   │
│  ├─ 防守點（擋黑方四/三）            │
│  └─ 禁手誘導點（白方獨有）           │
├─────────────────────────────────────┤
│  搜尋引擎                            │
│  ├─ TSS（威脅序列搜尋）             │
│  ├─ Negamax + Alpha-Beta            │
│  └─ Iterative Deepening（時間控制） │
├─────────────────────────────────────┤
│  評估函數                            │
│  ├─ 棋型分（五/活四/衝四/活三...）  │
│  ├─ 禁手威脅加成                    │
│  └─ 位置權重（中心偏好）            │
├─────────────────────────────────────┤
│  記憶體優化                          │
│  ├─ Transposition Table（Zobrist）  │
│  └─ Bitboard 棋盤表示               │
└─────────────────────────────────────┘
```

---

## 📋 四、實作優先順序建議

```
Phase 1（能跑）
  → Negamax + Alpha-Beta + 基本棋型評估

Phase 2（能贏）
  → TSS + Transposition Table + 禁手誘導分

Phase 3（難打敗）
  → Bitboard + 動態評估 + 開局庫
```

---

## ⚡ 最關鍵的一句話

> 「白方 AI 的核心不是比黑方更聰明，而是**永遠讓黑方面對一個讓他走禁手才能解圍的局面**。」

你目前的 function 基礎已經很完整了（有 `is_black_forbidden_after_move`、棋型判斷等），要先從哪個 Phase 開始實作？
