# Topic

基于 VisDrone 数据集的极端轻量化目标检测算法

## Inclusion

- 场景与任务匹配：明确提及无人机视角 (UAV, Drone, Aerial) 和目标检测 (Object Detection)，且最好提及 VisDrone 数据集。
- 轻量化意图：摘要中强调了模型轻量化、实时性、边缘设备部署、低算力消耗，或者提到了使用了轻量级网络架构（如 YOLO, MobileNet, GhostNet, 轻量级注意力机制等）。

## Exclusion

- 任务不符：纯目标跟踪 (Object Tracking)、图像分割、无人机路径规划或纯硬件设计。
- 明显不属于轻量化：摘要中明确强调追求极致精度（State-of-the-Art）而忽略计算成本，或者使用了明显的大型重载网络（如未经轻量化处理的大型 Vision Transformer）。
