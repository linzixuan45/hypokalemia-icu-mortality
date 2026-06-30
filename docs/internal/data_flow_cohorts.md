# 低钾项目：队列数据流

**代码映射**：`scripts/run_pipeline.py` · `scripts/train_models.py` · `scripts/supplementary_analysis.py`  
**用途**：Methods / 脚注 / 分析口径说明  
**关联**：`MC1_spec.md` · `result/analysis/manifest.json`

---

## 1. 两套人数勿混用

| 层级 | 含义 | 8-feature eval |
|------|------|----------------|
| **MIMIC-III train** | 开发集（自然患病率） | **652**（198 事件） |
| **MIMIC-III test** | 内部验证 | **163**（50 事件） |
| **MIMIC-IV val** | 时间外部验证 | **1413**（**130** 事件） |
| **F3 / NH** | 中国探索性外验（选项 β） | **110 / 25** · **100 / 33** |

R1 参考（勿与上表混用）：292/542 评估子集；2432/1302 全队列。

---

## 2. 代码与文稿对齐状态

| 项目 | 状态 |
|------|------|
| ICU ≥24h | ✅ `LOS_ICU_MIN = 1`（天） |
| 无 undersampling | ✅ `downsample_ratio = 0` |
| t₀ | ⚠️ Excel proxy（`t0_source_detail=excel_derived_interim`；待 SQL） |
| 结局 | ✅ 7-day from t₀ (`outcome_7d`) |

---

## 3. 预测文件与队列对应

| pkl | 队列 | n | 事件 |
|-----|------|---|------|
| `preds/8_features/test_preds.pkl` | MIMIC-III internal | 163 | 50 |
| `preds/8_features/val_preds.pkl` | MIMIC-IV temporal | 1413 | 130 |
| `preds/8_features/F3_preds.pkl` | 湘雅三院 | 110 | 25 |
| `preds/8_features/NH_preds.pkl` | 南华 | 100 | 33 |

---

## 4. 中国外验（选项 β）

- 队列定义：沿用 R1；模型权重来自 MIMIC 主分析（`train_models.py`）。
- NH AUROC **0.717**；F3 **0.830**（见 `manifest.json`）。

---

## 5. 分析输出目录

```
result/analysis/
├── manifest.json
├── cohorts/
├── preds/
├── tables/     # Table 2–6, S7–S15
└── figures/    # Figure 5/7, S5/S7/S8
```
