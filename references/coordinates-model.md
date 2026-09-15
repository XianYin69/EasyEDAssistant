# EasyEDAssistant Reference：坐标模型与数据地基

> 本文件由 SKILL.md v0.9.0「3. 坐标、单位与数据模型（承重的地基）」逐字迁移而来（v0.10.0 主干化重构）。
> 原章节编号保持不变；SKILL.md 是唯一入口，按触发条件加载本文件。

## 3. 坐标、单位与数据模型（承重的地基）

| 上下文 | 单位 | 说明 |
|---|---|---|
| 原理图 | 1 raw = 0.01 inch = 0.254 mm | **y-UP**；器件 anchor 5 raw 网格；排版优先 10 raw（100 mil）节拍 |
| PCB | 1 mil = 0.001 inch | **y-UP**；SMD 25 mil / 通孔 50 mil / 精密 5 mil 子栅 |
| mm 参数 | 边界换算 | 2.54 mm = 10 raw；0.5 mm ≈ 20 mil |

数据模型要点：

- `component.id` 是不透明稳定 ID；`ref` 是显示位号；功能名存 `role`。
  保留正常位号的大小写、前导零与声明顺序；`U_RF` 这类功能名不当位号。
- `pin`：`number` 是完整物理引脚编号，`name` 是符号脚名；**保留器件全部物理引脚**，
  不删脚、不猜 NC。
- PCB 器件 `x/y` 是**锚点**（footprint 原点），不是 bbox 中心，且偏移随旋转变化
  （#105）：规划一律用 `pcb list --include-bbox` 返回的 `center`，写入用
  `pcb modify --center --x <cx> --y <cy>`；旋转与 center 不能同一调用。
- 每器件绑定 `TOP`/`BOTTOM` 层；无左右镜像，只有翻面（`pcb.component.modify`）。
- 无程序化 undo：改前取**新鲜 primitiveId**，before/after 进审计日志。
