# MC1 方法学规格 — Index Time (t₀) 与预测任务

**状态**：**已定稿 v1**（2026-05-24）  
**关联**：`TODO.md` P0 · `Revision_Response_R2.md` MC1 · `numbering_map.md`

---

## 1. 预测任务（一句话）

在 ICU 低钾患者队列中，于 **首次记录 K⁺ < 3.5 mmol/L 的时刻 t₀**，利用 **t₀ 及之前可观测的预测变量**，估计 **自 t₀ 起 7 个日历日内** 的全因死亡风险（关联性估计，非因果/非部署声明）。

---

## 2. 队列纳入（MIMIC-III / MIMIC-IV 主分析）

| 规则 | 定义 | 备注 |
|------|------|------|
| 年龄 | 18–100 岁（clip） | 与 R1 一致 |
| ICU 停留 | **主分析**：≥24 h（`icu_intime` → 末次观测或出院） | 与 MC6 敏感性 ≥6h/≥12h 分开跑 |
| 低钾事件 | 至少一次 serum K⁺ < 3.5 mmol/L | |
| **t₀** | **首次** K⁺ < 3.5 的 `charttime`（或 lab 时间戳） | 主分析 index time |
| 首次 ICU | 同一 `hadm_id` 仅保留首次 ICU stay | |
| 结局可观测 | t₀ 后至少可观测 7 天或至死亡/出院 | 删失规则见 §4 |

**代码对齐项**：`src/dataset.py` 主分析 `LOS_ICU_MIN = 1`（天，即 ≥24h）；完整 t₀ 时间戳来自 `data/mimic_t0_labs.parquet`（SQL 导出）；Excel 仅有聚合特征时使用 **proxy 分层**（见 `build_t0_cohort.py`）。

---

## 3. 分层定义（Supp Table S8）

| stratum | 操作定义 |
|----------|----------|
| **Admission hypokalemia** | t₀ 落在 ICU 入院后 **首次 potassium lab** 的 `charttime`；若 t₀ 与首次 lab 时间差 ≤ 24 h 且首次 lab K⁺ < 3.5 |
| **Acquired hypokalemia** | t₀ **晚于** 首次 potassium lab 的 `charttime` ≥ 24 h |
| **Legacy sensitivity** | 预测变量仍锚定 **ICU 入院后 0–48 h**（R1 设计），结局口径与 §4 一致 → Supp Table S9 |

**Excel proxy（无 charttime 时）**：`potassium_1st < 3.5` → admission；否则 acquired。

---

## 4. 结局

| 项目 | 定稿值 |
|------|--------|
| 结局变量 | `hospital_expire_flag`（院内死亡） |
| 预测 horizon | **自 t₀ 起 7 个日历日内**死亡 = 1 |
| 删失 | t₀+7d 前出院且存活 = 0；t₀+7d 内死亡 = 1 |
| 早期死亡 | ICU <24h 死亡者在 MC6 敏感性（S10）中单独报告 |

**与 R1 差异**：R1 为自 ICU 入院 7 天；R2 主分析改为 **自 t₀ 起 7 天**。

---

## 5. 预测变量窗口（20-feature / 8-feature）

**原则**：每个变量取 **≤ t₀** 的最后一次观测（或入院至 t₀ 的 aggregate，与 R1 变量定义表一致）。

| 变量（示例） | 窗口规则 | t₀ 后是否可用 |
|--------------|----------|---------------|
| `admission_age` | 入院时 | 是（≤ t₀） |
| `SOFA`（对照用，非 ML 特征） | ≤ t₀ 最近 SOFA | 是 |
| `los_icu` | **累计 ICU 天数至 t₀**（非最终 LOS） | 是 |
| 实验室 min/mean | 入院至 **t₀** 的 min/mean | 是 |
| `is_noninvasive_ventilator` 等 | t₀ 前是否发生 | 是 |

**8-feature mini-model**：与 20-feature 相同 t₀ 规则；不含 `los_icu`（R1 设计保留）。

---

## 6. 训练 / 验证划分

| 集合 | 规则 | 预期 n（R1 参考，t₀ 后待更新） |
|------|------|--------------------------------|
| MIMIC-III 开发 | 2001–2012，80% train / 20% internal test | 全队列 ~2432 → test 子集原 292 |
| MIMIC-IV 外验 | 2008–2020，时间外部 | 全队列 ~1302 → val 子集原 542 |
| 评估子集 | 与 locked `preds.pkl` **同一 patient/stay ID** | 重跑后更新 `paper_data_overview.md` |

---

## 7. 中国队列（F3 / NH）— 决策：选项 β

| 队列 | 队列定义 | 模型 |
|------|----------|------|
| F3 / NH | **沿用 R1 队列定义**（非 MIMIC t₀ 重锚定） | 应用 **MIMIC-t₀ 重训后的 locked 8/20-feature 模型** 外推 |
| Methods 表述 | Geographic exploratory validation under original cohort definition; not re-anchored to t₀ | |

---

## 8. 与 MC7 的绑定

- t₀ 队列上 **禁止 random undersampling**（`downsample_ratio=0`）。
- Youden 阈值：训练折 OOF 预测，**自然患病率**。
- 校准/DCA/Web 输出：自然患病率。

---

## 9. 验收标准（pipeline 完成后核对）

- [ ] Supp Table S8：admission vs acquired 分层 AUROC + 校准 + Brier
- [ ] Supp Table S9：legacy admission-anchored 敏感性
- [ ] Methods「Index time and prediction task」与本文 §1–§5 一致
- [ ] Abstract 无 admission-time prediction 措辞
- [ ] 评估子集 n 与 Table 2–3 脚注、Figure 1 一致
- [ ] `result/r2_locked/manifest.json` 记录 cohort 版本、git commit、随机种子

---

## 10. 开放问题 — 已定稿（2026-05-24）

| # | 问题 | **定稿决议** |
|---|------|-------------|
| 1 | 7-day mortality 起点 | **自 t₀**（与 index time 一致，非 ICU 入院） |
| 2 | 首次实验室面板 | **ICU 入院后第一次 `potassium` lab 的 charttime** 作为 admission 分层基准 |
| 3 | t₀ 与 ICU ≥24h | **是**：总 ICU stay 仍须 ≥24h（自 `icu_intime` 计），与 t₀ 发生时刻无关 |

**定稿签字**：R2 pipeline v1 · 日期：2026-05-24
