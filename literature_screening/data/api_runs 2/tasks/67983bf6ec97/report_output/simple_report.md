# 一、相关文献总体情况

这批文献聚焦于基于智能优化与改进型自抗扰控制（ADRC）的无人海洋载具（USV/UUV/AUV/水下滑翔机等）导引与轨迹跟踪系统研究。总体研究情况表明，学者们主要关注在复杂海洋环境（如风浪流扰动、模型不确定性、外部干扰）下，如何通过改进ADRC框架（如引入扩张状态观测器ESO及其变体）并结合智能优化算法（如强化学习、遗传算法、模糊优化）或先进控制方法（如滑模控制、模型预测控制、反步法）来提升系统的轨迹跟踪精度、鲁棒性和自适应能力。研究分布广泛，涵盖了单载具的路径跟随、深度跟踪、三维轨迹跟踪，以及多载具协同、编队控制、避障、抗攻击等应用场景，多数研究通过仿真或实验验证了所提方法的有效性。

# 二、类型划分

## 智能优化增强的自抗扰控制

这类文献共同关注如何将智能优化算法（如深度强化学习、遗传算法、模糊满意优化、软演员-评论家等）与自抗扰控制（ADRC）相结合，以在线或实时优化控制参数（如ESO参数、导引律参数），从而提升无人海洋载具在不确定和扰动环境下的自适应能力和控制性能。

- Deep Reinforcement Learning Based Active Disturbance Rejection Control for ROV Position and Attitude Control
- ADRC based cooperative path following control for USV-UAV within restricted waters
- Soft Actor-Critic based active disturbance rejection path following control for unmanned surface vessel under wind and wave disturbances
- Multi-USV cooperative path planning by window update based self-organizing map and spectral clustering?
- Co-Design of USV Control System Based on Fuzzy Satisfactory Optimization for Automatic Target Arriving and Berthing
- Robust motion control of four-vector-thruster AUV "Aurora" under disturbances: optimized ESO-FAISMC control with thrust allocation optimization
- Extended state observer-based integral line-of-sight guidance law for path following of underactuated unmanned surface vehicles with uncertainties and ocean currents

## 改进型扩张状态观测器设计与扰动估计

这类文献共同关注如何设计改进的扩张状态观测器（ESO）或其变体（如线性ESO、降阶ESO、有限时间ESO、固定时间ESO、模型自由ESO等），以更精确、快速地估计无人海洋载具的系统不确定性、未知扰动（如洋流、风浪）、未建模动态和状态信息（如速度、侧滑角），为后续控制提供补偿基础。

- Path following of underactuated surface vessels based active disturbance rejection control considering lateral drift
- LADRC-based wake tracking control via sideslip angle estimation for AUVs following the trajectories of near-surface targets
- An Output Feedback Approach for 3-D Prescribed Time Stabilization Control of Unmanned Underwater Vehicles
- Collision-free trajectory tracking strategy of a UUV via finite-time extended state observer-based sliding mode predictive control
- Fixed-time extended state observer-based trajectory tracking control for autonomous underwater vehicles
- Extended state observer based trajectory tracking control of underactuated unmanned surface vehicle with signal quantization
- A novel combination between finite-time extended state observer and proportional-integral-derivative nonsingular fast terminal sliding mode controller for an autonomous underwater vehicle
- Disturbance rejection event-triggered robust nonlinear model predictive control for underactuated unmanned surface vehicle against DoS attacks without velocity measurements
- Tracking control for small autonomous underwater vehicles in the Trans-Atlantic Geotraverse hydrothermal field based on the modeling trajectory
- Adaptive output feedback super twisting algorithm for trajectory tracking control of USVs with saturated constraints
- Model-free Predictive Trajectory Tracking Control and Obstacle Avoidance for Unmanned Surface Vehicle With Uncertainty and Unknown Disturbances via Model-free Extended State Observer
- Distributed Lyapunov-Based Model Predictive Control for AUV Formation Systems with Multiple Constraints
- Fixed-time sliding mode output feedback tracking control for autonomous underwater vehicle with constraint
- Fixed-Time Resilient Edge-Triggered Estimation and Control of Surface Vehicles for Cooperative Target Tracking Under Attacks
- Improved line-of-sight path following for unmanned surface vehicle with exact compensation of sideslip angle
- Ocean Currents Compensation-Based IAILOS-ROESOs Guidance and Adaptive Sliding Mode Path Following Control for Unmanned Surface Vehicles
- Robust MPC-based trajectory tracking of autonomous underwater vehicles with model uncertainty

## 复合控制框架与鲁棒性提升

这类文献共同关注如何将自抗扰控制（ADRC）与其他控制方法（如滑模控制、模型预测控制、反步法、终端滑模等）结合，形成分层或双环复合控制框架，以处理无人海洋载具的欠驱动特性、输入饱和约束、跟踪误差收敛等问题，从而增强系统在复杂环境下的鲁棒性和稳定性。

- Optimized Line-of-Sight Active Disturbance Rejection Control for Depth Tracking of Hybrid Underwater Gliders in Disturbed Environments
- A hierarchical disturbance rejection depth tracking control of underactuated AUV with experimental verification
- Three-Dimensional Trajectory Tracking Control Strategy for Underactuated UUVs Based on Improved ADRC
- ADRC-SMC-based disturbance rejection depth-tracking control of underactuated AUV
- Piecewise Compensation Model Predictive Governor Combined With Conditional Disturbance Negation for Underactuated AUV Tracking Control
- Dual-Loop Controller for Underwater Snake-Like Robot Based on Dynamic Inverse Solution

## 导引律优化与路径跟踪

这类文献共同关注如何设计或改进导引律（如视线导引LOS及其变体、自适应导引、积分导引等），并结合自抗扰控制（ADRC）来处理无人海洋载具的路径跟随问题，特别是在洋流、侧滑角影响、路径曲率变化等场景下，通过优化前视距离、补偿扰动来提升跟踪精度和收敛速度。

- Design and test of an improved active disturbance rejection control system for water sampling unmanned surface vehicle

# 三、逐篇文献总结分析

## Deep Reinforcement Learning Based Active Disturbance Rejection Control for ROV Position and Attitude Control

总结：
该文献针对无人水下机器人（ROV）在外部扰动和参数不确定性下的轨迹跟踪问题，提出了一种基于深度强化学习的自抗扰控制策略。研究采用深度确定性策略梯度（DDPG）算法在线优化线性扩张状态观测器（LESO）参数，以更精确估计模型不确定性和环境扰动，并将总扰动补偿到控制输入中。仿真结果表明，相比PID、固定参数LADRC及基于非线性观测器的双闭环滑模控制（NESO-DSMC），该方法显著提高了扰动估计精度和控制鲁棒性。

分析：
该文献对于基于智能优化与改进型ADRC的无人海洋载具导引与轨迹跟踪系统具有直接参考价值，其将深度强化学习与ADRC结合的机制可支撑自适应控制参数优化设计。它适用于USV/UUV等载具在复杂海洋环境中的高精度轨迹跟踪应用场景，为系统设计提供了强化学习增强ADRC鲁棒性的具体实现思路。

## Design and test of an improved active disturbance rejection control system for water sampling unmanned surface vehicle

总结：
该文献针对水采样无人水面艇（WS-USV）系统，设计了改进的自抗扰控制（ADRC）方法，通过引入饱和函数处理推进器输入约束，以增强路径跟随控制系统的抗风浪流干扰能力。实验验证了该控制系统的可行性、稳定性和性能优势。

分析：
该文献为基于改进ADRC的无人海洋载具导引与轨迹跟踪系统提供了具体应用案例，其处理输入约束和抗环境干扰的机制可直接支撑系统设计中的鲁棒性优化。它适用于USV在复杂海洋环境下的作业场景，如采样任务，有助于研究脉络中控制算法的实际部署验证。

## ADRC based cooperative path following control for USV-UAV within restricted waters

总结：
该文献提出了一种基于线性自抗扰控制（LADRC）的无人水面艇（USV）与无人机（UAV）协同路径跟随控制策略，通过集成遗传算法实时优化扩展状态观测器（ESO）参数，并引入可变半径视线（LOS）算法以减少跟踪误差。仿真结果表明，该控制器在环境干扰下实现了鲁棒的协同路径跟随，与传统LOS相比，可变半径LOS的均方根误差和平均绝对误差分别降低了20.99%和24.30%。

分析：
该文献对于基于智能优化与改进型ADRC的无人海洋载具导引与轨迹跟踪系统具有参考价值，其LADRC与遗传算法结合的机制可支撑复杂海洋环境中参数自适应调整的系统设计。可变半径LOS算法适用于提升USV-UAV异构系统在受限水域的协同跟踪精度，为研究脉络中优化控制与导引融合提供了具体案例。

## Path following of underactuated surface vessels based active disturbance rejection control considering lateral drift

总结：
该文献针对欠驱动水面艇（USV）路径跟随问题，提出了一种结合线性扩张状态观测器（LESO）的自抗扰控制（ADRC）方法。研究采用Backstepping技术构建虚拟航向角，并利用LESO估计侧向漂移和未建模动态，同时引入速度观测器解决速度测量难题。仿真结果表明，该控制器在扰动下能精确跟踪参考路径，验证了控制策略的有效性。

分析：
该文献对于基于改进型ADRC的无人海洋载具导引系统具有直接参考价值，其结合LESO和Backstepping的机制可支撑系统设计中扰动抑制和未建模动态处理。它适用于USV在复杂海况下的路径跟随应用场景，为轨迹跟踪控制提供了具体算法实现和验证思路。

## Optimized Line-of-Sight Active Disturbance Rejection Control for Depth Tracking of Hybrid Underwater Gliders in Disturbed Environments

总结：
该文献针对混合驱动水下滑翔机在扰动环境中的深度跟踪问题，提出了一种优化的视线自抗扰控制策略。通过动态调整视线导引的前视距离和增强扩张状态观测器的扰动估计能力，该方法在仿真实验中显著降低了深度跟踪误差和俯仰角误差，并缩短了稳定时间。研究为高精度运动控制提供了有效的解决方案，但仅限于垂直平面仿真验证。

分析：
该文献对于基于智能优化与改进型ADRC的无人海洋载具导引与轨迹跟踪系统具有直接参考价值。其OLOS-ADRC机制适合支撑复杂海洋环境下无人载具的鲁棒控制设计，特别是针对系统不确定性和环境干扰的实时补偿应用场景。研究结果可为类似系统的仿真验证和算法优化提供技术借鉴，有助于提升轨迹跟踪的精度和稳定性。

## A hierarchical disturbance rejection depth tracking control of underactuated AUV with experimental verification

总结：
该文献针对欠驱动自主水下航行器（AUV）的深度跟踪控制问题，提出了一种分层抗扰控制方案。该方案结合自适应视线导引（ALOS）和自抗扰控制（ADRC），通过运动学和动力学两层设计，有效补偿扰动并提升跟踪性能。实验验证表明，该方案在小型AUV原型上实现了显著的深度跟踪效果。

分析：
该文献对于基于改进型ADRC的无人海洋载具轨迹跟踪系统具有直接参考价值，其分层抗扰机制可支撑系统设计中的扰动补偿和自适应导引部分。它适用于AUV等欠驱动平台的深度控制场景，为智能优化与ADRC结合的研究提供了实验验证案例。

## Three-Dimensional Trajectory Tracking Control Strategy for Underactuated UUVs Based on Improved ADRC

总结：
该文献针对欠驱动无人水下航行器（UUV）在外部扰动下轨迹跟踪精度低的问题，提出了一种结合反步控制与改进自抗扰控制（IADRC）的方法，通过引入非奇异终端滑模控制和参数自适应跟踪微分器，增强了系统的高精度轨迹跟踪性能。研究基于Lyapunov理论证明了跟踪误差的渐近收敛性，仿真结果验证了控制策略的有效性和优越性。

分析：
该文献对于基于改进型自抗扰控制的无人海洋载具轨迹跟踪系统具有直接参考价值，其改进ADRC框架和模型辅助扩展状态观测器设计，可支撑高精度、抗扰动的三维轨迹跟踪机制。它适用于欠驱动UUV在复杂海洋环境下的应用场景，为系统设计提供了理论验证和仿真基础。

## ADRC-SMC-based disturbance rejection depth-tracking control of underactuated AUV

总结：
该文献研究了欠驱动自主水下航行器（AUV）的深度跟踪控制问题，提出了一种基于自抗扰控制（ADRC）和滑模控制（SMC）的俯仰自动驾驶方法，以消除动态相关扰动。通过结合自适应视线（ALOS）导引，将深度跟踪转换为俯仰跟踪，并证明了闭环控制器的稳定性。实验验证了该方法在深度跟踪中的有效性和强抗扰能力。

分析：
该文献对于基于改进型自抗扰控制的无人海洋载具导引与轨迹跟踪系统具有参考价值，其ADRC-SMC机制可支撑系统在复杂动态环境下的抗扰设计，适用于USV/UUV等载具的深度或轨迹跟踪应用场景。ALOS导引方法为处理跟踪误差和角度补偿提供了思路，有助于优化系统闭环稳定性和实际作业性能。

## Piecewise Compensation Model Predictive Governor Combined With Conditional Disturbance Negation for Underactuated AUV Tracking Control

总结：
该文献针对欠驱动自主水下航行器（AUV）的精确跟踪控制问题，提出了一种结合分段补偿模型预测调节器和条件扰动抵消的新型控制架构。该架构通过分段补偿机制消除稳态跟踪误差，利用模型预测调节器生成满足约束的参考速度，并采用有限时间扩展状态观测器提升估计误差收敛性能。仿真与实验验证了该控制方案的有效性，展示了其在真实AUV应用中的潜力。

分析：
该文献对当前报告主题的参考价值在于：其基于有限时间扩展状态观测器的自抗扰控制（ADRC）框架可直接支撑无人海洋载具的轨迹跟踪系统设计；条件扰动抵消机制为处理海洋环境扰动提供了新思路，适合应用于USV/UUV等系统的鲁棒控制场景；分段补偿与模型预测的结合为欠驱动系统的约束优化控制提供了具体实现方案。

## Dual-Loop Controller for Underwater Snake-Like Robot Based on Dynamic Inverse Solution

总结：
该文献针对水下蛇形机器人在狭窄地形中姿态受限的问题，提出了一种基于动态逆解的双环控制方法（DI-ADRC）。该方法通过外环分析机器人动态特性并计算最优关节角度，内环嵌入ADRC输出关节旋转速度，相比传统方法减少了计算负担。实验验证了该方法在狭窄地形中的可行性，能提高控制精度和响应速度。

分析：
该文献对于基于智能优化与改进型ADRC的无人海洋载具导引与轨迹跟踪系统具有参考价值，其DI-ADRC结构可支撑轨迹跟踪控制中的动态逆解机制，适用于复杂水下环境的系统设计。它提供了改进ADRC以减少计算负担的思路，有助于优化无人海洋载具在狭窄或动态场景下的控制性能。

## Soft Actor-Critic based active disturbance rejection path following control for unmanned surface vessel under wind and wave disturbances

总结：
该文献研究了无人水面艇在风浪扰动下的路径跟踪控制问题。采用三自由度MMG模型描述USV动力学特性，结合线性自抗扰控制器与软演员-评论家强化学习算法，实现了自适应路径跟踪控制。通过直线和圆形路径仿真验证了该方法在风浪环境下的有效性。

分析：
该文献为基于智能优化与改进型ADRC的无人海洋载具轨迹跟踪系统提供了具体实现方案。其SAC优化LADRC参数的机制可直接支撑自适应控制系统的设计，风浪扰动下的验证场景对海洋环境应用具有参考价值。

## Multi-USV cooperative path planning by window update based self-organizing map and spectral clustering?

总结：
该文献提出了一种用于复杂海洋环境中多无人水面艇协同路径规划的分层两层框架。通过基于窗口更新的改进自组织图优化路径规划，并结合谱聚类方法进行任务分配，实现了多USV系统的协同作业。仿真结果表明该方法具有可行性和有效性，并采用B样条平滑策略、视线导引和自抗扰控制器确保路径跟踪精度。

分析：
该文献对于基于智能优化与改进型ADRC的无人海洋载具导引与轨迹跟踪系统研究具有重要参考价值。其分层框架和智能算法组合为多USV协同控制提供了机制设计思路，适用于海洋环境监测或搜救等应用场景。文献中的路径规划与跟踪方法可直接支撑系统设计中的轨迹生成和鲁棒控制模块。

## LADRC-based wake tracking control via sideslip angle estimation for AUVs following the trajectories of near-surface targets

总结：
该文献针对自主水下航行器（AUV）跟踪近水面目标轨迹时面临的非线性耦合、环境扰动和侧滑效应等问题，提出了一种基于线性自抗扰控制（LADRC）的尾流跟踪控制方法。该方法通过构建降阶扩张状态观测器实时估计侧滑角，并结合基于侧滑估计的视线导引律生成协调的偏航角和前向速度指令，最终设计了两个LADRC控制器实现偏航和前向通道的解耦鲁棒控制。仿真结果表明，该方法在轨迹精度、侧向偏差抑制、收敛速度和能效方面优于传统视线导引与PID结合扰动观测器的方案，提升了AUV在复杂近海环境中的稳定可靠尾流跟踪能力。

分析：
该文献对于基于智能优化与改进型自抗扰控制的无人海洋载具导引与轨迹跟踪系统研究具有直接参考价值。其提出的降阶扩张状态观测器结构为改进型ADRC提供了具体的技术实现思路，特别适用于处理系统非线性耦合和外部扰动。文献中侧滑角估计与视线导引律的结合机制，可为无人海洋载具在复杂海况下的精确轨迹跟踪系统设计提供关键技术支撑。

## Co-Design of USV Control System Based on Fuzzy Satisfactory Optimization for Automatic Target Arriving and Berthing

总结：
该文献针对无人水面艇（USV）在存在多形状凸障碍和扰动下的自动目标到达与靠泊问题，设计了一种包含轨迹优化和轨迹跟踪的复合控制系统。通过引入模糊满意优化处理最小运行时间和能耗的双目标优先级，并采用高斯伪谱法离散化模型求解最优轨迹，同时设计一阶自抗扰控制（ADRC）控制器实现扰动下的轨迹跟踪。仿真结果表明，该协同设计系统相比其他方法具有有效性。

分析：
该文献对于基于智能优化与改进型ADRC的无人海洋载具导引与轨迹跟踪系统研究具有参考价值，其模糊满意优化方法可用于支撑多目标优先级处理机制，适用于USV在复杂障碍环境下的轨迹优化场景。ADRC控制器的设计为系统在扰动下的鲁棒跟踪提供了具体实现方案，有助于完善轨迹跟踪系统的整体架构。

## An Output Feedback Approach for 3-D Prescribed Time Stabilization Control of Unmanned Underwater Vehicles

总结：
该文献针对无人水下航行器，提出了一种规定时间输出反馈三维稳定控制方案。通过构建基于时变缩放函数的规定时间扩张状态观测器（PTESO），在预设时间内估计不可测速度、未知水动力参数和外部扰动，并设计了简化结构的控制器。基于李雅普诺夫稳定性理论，严格证明了稳定误差在规定时间内收敛到零，并通过实验验证了方案的有效性。

分析：
该文献对于基于改进型自抗扰控制（ADRC）的无人海洋载具导引与轨迹跟踪系统具有直接参考价值。其PTESO机制可支撑系统在存在未知扰动和参数不确定性下的规定时间稳定控制，适用于需要高精度和快速响应的水下航行器应用场景，如轨迹跟踪和自主作业。

## Collision-free trajectory tracking strategy of a UUV via finite-time extended state observer-based sliding mode predictive control

总结：
该文献针对受海流扰动和静态障碍物影响的水下无人航行器轨迹跟踪问题，提出了一种双环控制框架。外环采用模型预测控制生成最优速度指令，内环结合有限时间扩张状态观测器和自适应积分终端滑模控制器，实现了对模型不确定性和外部扰动的快速估计与补偿。通过李雅普诺夫稳定性理论和有限时间分析技术，证明了该控制策略能使航行器在有限时间内收敛到参考轨迹，仿真实验验证了其有效性和可行性。

分析：
该文献对当前报告主题的参考价值在于：其改进的有限时间扩张状态观测器结构为自抗扰控制的性能提升提供了具体技术路径，适合支撑无人海洋载具在动态扰动环境下的鲁棒轨迹跟踪机制。双环架构结合模型预测与滑模控制的设计思路，可为复杂海洋场景下的系统集成提供参考框架。

## Fixed-time extended state observer-based trajectory tracking control for autonomous underwater vehicles

总结：
该文献研究了自主水下航行器（AUV）在时变外部扰动下的轨迹跟踪控制问题，提出了一种基于固定时间扩张状态观测器（FTESO）的跟踪控制器。该控制器通过FTESO在固定时间内估计外部扰动和AUV速度，并基于此设计固定时间控制器以减少跟踪误差并提升鲁棒性。理论分析和仿真结果表明，该方法能补偿未知扰动并使跟踪误差在固定时间内收敛到零。

分析：
该文献对于基于改进型自抗扰控制（ADRC）的无人海洋载具轨迹跟踪系统具有参考价值，其FTESO机制适合支撑固定时间收敛的扰动估计和控制系统设计。它可应用于需要高鲁棒性和精确轨迹跟踪的无人水下航行器场景，为系统设计提供了理论依据和仿真验证。

## Extended state observer based trajectory tracking control of underactuated unmanned surface vehicle with signal quantization

总结：
该文献针对欠驱动无人水面艇在复杂海洋环境中的模型不确定性和轨迹跟踪控制难题，提出了一种基于扩张状态观测器的信号量化轨迹跟踪控制策略。通过内外环控制架构，在运动学子系统设计导引律解决欠驱动问题，在动力学子系统利用ESO处理未知项并平滑量化信号，采用李雅普诺夫方法证明了闭环系统稳定性。

分析：
该文献为基于改进型自抗扰控制的无人海洋载具轨迹跟踪系统提供了具体实现方案，其ESO处理模型不确定性的机制可直接应用于ADRC框架。信号量化控制方法对实际系统中通信受限场景具有参考价值，内外环分离的设计思路适合支撑复杂海洋环境下的USV导引系统架构。

## A novel combination between finite-time extended state observer and proportional-integral-derivative nonsingular fast terminal sliding mode controller for an autonomous underwater vehicle

总结：
该文献研究了一种结合有限时间扩张状态观测器与比例积分微分非奇异快速终端滑模控制器的自主水下航行器控制方法。通过设计有限时间扩张状态观测器估计未知建模不确定性和外部扰动，并采用新型滑模面保证系统跟踪性能，基于李雅普诺夫稳定性理论证明了有限时间全局稳定收敛。仿真结果表明，相比现有方法，系统性能至少提升8.6%。

分析：
该文献为无人海洋载具轨迹跟踪系统提供了基于改进型自抗扰控制的具体实现方案，其有限时间扩张状态观测器设计可直接用于处理海洋环境中的不确定扰动。提出的滑模控制器结构适合支撑高精度轨迹跟踪的鲁棒控制机制，控制分配方法对多执行器系统的实际应用具有参考价值。

## Disturbance rejection event-triggered robust nonlinear model predictive control for underactuated unmanned surface vehicle against DoS attacks without velocity measurements

总结：
该文献针对受拒绝服务攻击且缺乏速度测量的欠驱动无人水面艇，提出了一种抗扰事件触发非线性模型预测控制方法。该方法采用非线性扩张状态观测器估计未知速度和集总扰动，并设计抗扰非线性模型预测控制器处理执行器饱和约束，同时引入事件触发机制降低计算负荷和拒绝服务攻击防御机制保证跟踪性能。理论分析确保了递归可行性和闭环稳定性，仿真验证了该方法在控制精度和计算效率方面的优越性。

分析：
该文献对当前报告主题的参考价值在于：其非线性扩张状态观测器技术可直接应用于改进型自抗扰控制框架，为无人海洋载具在扰动和攻击下的状态估计提供具体实现方案。文献中事件触发与模型预测控制的结合机制，适合支撑低通信频率、高实时性要求的轨迹跟踪系统设计。同时，其针对拒绝服务攻击的防御策略，为无人海洋载具在对抗性环境下的安全控制研究提供了技术脉络参考。

## Tracking control for small autonomous underwater vehicles in the Trans-Atlantic Geotraverse hydrothermal field based on the modeling trajectory

总结：
该文献研究了小型自主水下航行器在跨大西洋地质穿越热液场中的固定时间轨迹跟踪问题，针对洋流、未知扰动、模型不确定性和执行器故障等挑战，设计了自适应扩展状态观测器和固定时间滑模控制律。通过模拟地形和轨迹建模，验证了所提算法在复杂水下环境中的有效性和优越性。

分析：
该文献对于基于智能优化与改进型自抗扰控制的无人海洋载具导引与轨迹跟踪系统具有参考价值，其自适应扩展状态观测器技术可支撑ADRC/ESO在不确定环境下的应用，适用于小型AUV在复杂水下地形中的精确轨迹跟踪系统设计。

## Robust motion control of four-vector-thruster AUV "Aurora" under disturbances: optimized ESO-FAISMC control with thrust allocation optimization

总结：
该文献针对四矢量推进器AUV在内外扰动下的轨迹跟踪问题，提出了一种结合改进扩张状态观测器与模糊自适应积分滑模控制的优化框架。通过优化推力分配策略和模糊增益调节，有效抑制了抖振并提升了扰动估计精度。仿真结果表明，该控制方法相比传统方法显著降低了跟踪误差，实现了高精度稳定控制。

分析：
该文献为基于智能优化的改进型自抗扰控制提供了具体实现案例，其ESO-FAISMC框架适用于无人海洋载具在复杂扰动环境下的轨迹跟踪系统设计。它支撑了模糊自适应机制在增益调节中的应用，可参考用于提升USV/UUV等系统的鲁棒性和控制精度。

## Adaptive output feedback super twisting algorithm for trajectory tracking control of USVs with saturated constraints

总结：
该文献研究了全驱动无人水面艇（USV）在系统不确定性和输入饱和约束下的轨迹跟踪控制问题。提出了一种结合饱和自适应超螺旋算法与非奇异快速终端滑模（SASTA-NFTSM）的输出反馈方案，利用有限时间扩张状态观测器（FTESO）估计速度和系统不确定性。该方法通过连续控制律有效抑制了抖振现象，并保证了跟踪误差在有限时间内收敛到零。

分析：
该文献对于基于改进型自抗扰控制（ADRC）的无人海洋载具轨迹跟踪系统具有参考价值，其FTESO机制可支撑系统不确定性和外部扰动的实时估计。SASTA-NFTSM方案适用于处理输入饱和约束，为USV/UUV等载具在复杂海洋环境中的高精度控制提供了设计思路。

## Model-free Predictive Trajectory Tracking Control and Obstacle Avoidance for Unmanned Surface Vehicle With Uncertainty and Unknown Disturbances via Model-free Extended State Observer

总结：
该文献提出了一种基于模型自由扩张状态观测器（MFESO）的模型自由预测控制方法，用于解决无人水面艇（USV）在复杂环境中的轨迹跟踪与避障问题。该方法通过结合模型自由预测控制（MFPAC）处理系统动力学不确定性，并利用反步法消除旋转特性，无需精确的USV数学模型。稳定性分析表明该控制策略具有有界输入有界输出（BIBO）稳定性，仿真结果验证了算法的有效性。

分析：
该文献对当前报告主题的参考价值在于，其MFESO机制可直接支撑改进型自抗扰控制（ADRC）在无人海洋载具中的应用，特别是处理系统不确定性和未知扰动。它适用于需要模型自由控制的USV导引与轨迹跟踪系统设计，为智能优化提供了具体的控制框架实例。

## Distributed Lyapunov-Based Model Predictive Control for AUV Formation Systems with Multiple Constraints

总结：
该文献研究了三维空间中受多重约束的自主水下航行器编队跟踪问题，提出了一种结合快速有限时间扩张状态观测器和分布式Lyapunov模型预测控制的层次化控制框架。该框架通过观测器补偿内外扰动，利用在线优化处理状态约束和执行器饱和，并基于Lyapunov反步法构造稳定性约束以保证系统稳定。仿真结果表明，该方法相比其他方法在收敛速度和跟踪精度上均提升至少30%。

分析：
该文献对当前报告主题的参考价值在于：其快速有限时间扩张状态观测器设计可直接支撑改进型自抗扰控制在无人海洋载具中的应用，特别是针对水下环境的扰动补偿机制；分布式模型预测控制与Lyapunov稳定性约束的结合，为多无人载具协同作业系统的轨迹跟踪与约束管理提供了可借鉴的设计思路；适用于需要高精度编队跟踪的USV/UUV集群作业场景。

## Fixed-time sliding mode output feedback tracking control for autonomous underwater vehicle with constraint

总结：
该文献研究了自主水下航行器（AUV）在外部干扰和模型不确定性下的轨迹跟踪控制问题。通过引入规定性能函数约束输出跟踪误差，并设计固定时间扩张状态观测器（FxTESO）估计未知状态和集总干扰，构建了动态固定时间终端滑模（FxTTSM）表面和固定时间输出反馈控制器。基于李雅普诺夫函数理论分析了闭环系统稳定性，仿真验证了控制方案的有效性。

分析：
该文献对于基于智能优化与改进型自抗扰控制（ADRC）的无人海洋载具轨迹跟踪系统具有参考价值，其固定时间扩张状态观测器（FxTESO）机制可支撑系统在未知动态和干扰下的鲁棒性设计。它适用于AUV等无人海洋载具在复杂海洋环境中的轨迹跟踪应用场景，为系统设计提供了固定时间稳定性和输出反馈控制的实现思路。

## Fixed-Time Resilient Edge-Triggered Estimation and Control of Surface Vehicles for Cooperative Target Tracking Under Attacks

总结：
该文献研究了在拒绝服务攻击下，欠驱动无人水面艇的协同目标跟踪问题，提出了一种固定时间弹性协同边沿触发估计与控制架构。通过设计分布式边沿触发固定时间扩张状态观测器，在预定时间内恢复目标位置和速度，并利用固定时间控制律处理模型不确定性和外部扰动，确保闭环系统误差在固定时间内收敛。

分析：
该文献对于基于改进型自抗扰控制的无人海洋载具导引与轨迹跟踪系统具有参考价值，其固定时间扩张状态观测器机制可支撑系统在攻击环境下的鲁棒性设计，适用于协同作业场景中处理通信受限和扰动问题，为智能优化控制提供了具体实现思路。

## Improved line-of-sight path following for unmanned surface vehicle with exact compensation of sideslip angle

总结：
该文献针对受时变洋流影响的欠驱动无人水面艇，提出了一种改进的视线导引律用于路径跟随。研究通过结合降阶扩张状态观测器与自适应测量方法，精确估计未知侧滑角和外部扰动，并设计了能自适应响应路径曲率、前视距离和横向跟踪误差的期望前向速度。仿真与对比研究验证了该导引律在加速收敛和提升路径跟随精度方面的有效性。

分析：
该文献为基于改进型自抗扰控制的无人海洋载具导引系统提供了具体实现参考，其精确补偿侧滑角与扰动的机制可直接支撑高精度轨迹跟踪控制器的设计。研究中的自适应前视距离调整方法适用于动态海洋环境下的路径跟随应用场景，有助于增强系统在复杂海况下的鲁棒性。

## Extended state observer-based integral line-of-sight guidance law for path following of underactuated unmanned surface vehicles with uncertainties and ocean currents

总结：
该文献研究了欠驱动无人水面艇在模型不确定性和时变洋流下的路径跟随问题，提出了基于扩张状态观测器的积分视线导引律结合自适应模糊控制框架。通过观测器估计速度、自适应方法处理洋流，并引入模糊算法优化前视距离，同时采用积分滑模技术处理跟踪控制，证明了闭环系统误差一致最终有界。

分析：
该文献对于基于智能优化与改进型自抗扰控制的无人海洋载具导引系统具有参考价值，其ESO和自适应模糊机制可支撑系统在不确定环境下的鲁棒控制设计，适用于USV在复杂海况下的轨迹跟踪应用，为自抗扰控制与智能优化结合提供了具体实现思路。

## Ocean Currents Compensation-Based IAILOS-ROESOs Guidance and Adaptive Sliding Mode Path Following Control for Unmanned Surface Vehicles

总结：
该文献研究了无人水面艇在洋流和输入饱和条件下的路径跟随问题，提出了一种基于洋流补偿的改进自适应积分视线导引与降阶扩张状态观测器结合自适应积分滑模控制的复合方法。该方法在导引模块估计洋流影响并在运动学层面补偿，在控制模块利用RBF神经网络逼近集总扰动并估计误差边界，同时通过非线性微分估计器和改进辅助动态系统处理输入饱和。理论分析和仿真验证了所有误差收敛至零，控制策略有效。

分析：
该文献对于基于智能优化与改进型自抗扰控制的无人海洋载具导引与轨迹跟踪系统具有参考价值，其洋流补偿机制和降阶扩张状态观测器设计可支撑系统在动态海洋环境中的鲁棒性应用。自适应积分滑模控制结合RBF神经网络的方法适合处理未知扰动和输入饱和场景，为系统设计提供了具体的控制框架和理论验证基础。

## Robust MPC-based trajectory tracking of autonomous underwater vehicles with model uncertainty

总结：
该文献提出了一种基于鲁棒模型预测控制（MPC）的双闭环方法，用于处理自主水下航行器（AUV）在模型参数不确定和随机外部扰动下的轨迹跟踪问题。通过设计有限时间扩张状态观测器（FTESO）补偿动态模型不确定性，并结合Lyapunov稳定性理论分析控制器稳定性。仿真实验验证了该控制框架的有效性和鲁棒性，表明其是一种可行的AUV轨迹跟踪控制方法。

分析：
该文献对于基于智能优化与改进型自抗扰控制（ADRC）的无人海洋载具轨迹跟踪系统具有重要参考价值，其FTESO机制可直接应用于增强系统对模型不确定性的鲁棒性。它适合支撑无人海洋载具在复杂海洋环境中的轨迹跟踪系统设计，特别是针对外部扰动和参数变化的控制场景。此外，该研究为结合MPC与自抗扰控制思路提供了实践案例，有助于完善相关控制理论的研究脉络。

# 参考列表

[1] Luo, GS, Zhang, D, Feng, W, et al. Deep Reinforcement Learning Based Active Disturbance Rejection Control for ROV Position and Attitude Control[J]. APPLIED SCIENCES-BASEL, 2025, 15(8).
[2] Wu, DF, Yuan, KX, Huang, YQ, et al. Design and test of an improved active disturbance rejection control system for water sampling unmanned surface vehicle[J]. OCEAN ENGINEERING, 2022, 245.
[3] Gao, SH, Zhang, XK, Zhang, HG, et al. ADRC based cooperative path following control for USV-UAV within restricted waters[J]. ASIAN JOURNAL OF CONTROL, 2025.
[4] Zhang, HG, Zhang, XK, Gao, SH, et al. Path following of underactuated surface vessels based active disturbance rejection control considering lateral drift[J]. PROCEEDINGS OF THE INSTITUTION OF MECHANICAL ENGINEERS PART M-JOURNAL OF ENGINEERING FOR THE MARITIME ENVIRONMENT, 2025, 239(2): 435-444.
[5] Zhao, Y, Zhou, HF, Xu, P, et al. Optimized Line-of-Sight Active Disturbance Rejection Control for Depth Tracking of Hybrid Underwater Gliders in Disturbed Environments[J]. JOURNAL OF MARINE SCIENCE AND ENGINEERING, 2025, 13(10).
[6] Liu, C, Xiang, XB, Yang, LC, et al. A hierarchical disturbance rejection depth tracking control of underactuated AUV with experimental verification[J]. OCEAN ENGINEERING, 2022, 264.
[7] Geng, XL, Yang, ZP, Ming, C. Three-Dimensional Trajectory Tracking Control Strategy for Underactuated UUVs Based on Improved ADRC[J]. SYMMETRY-BASEL, 2025, 17(8).
[8] Liu, C, Xiang, XB, Duan, Y, et al. ADRC-SMC-based disturbance rejection depth-tracking control of underactuated AUV[J]. JOURNAL OF FIELD ROBOTICS, 2024, 41(4): 1103-1115.
[9] Kong, SH, Sun, JL, Wang, J, et al. Piecewise Compensation Model Predictive Governor Combined With Conditional Disturbance Negation for Underactuated AUV Tracking Control[J]. IEEE TRANSACTIONS ON INDUSTRIAL ELECTRONICS, 2023, 70(6): 6191-6200.
[10] Yu, JM, Sun, H, Sun, QL, et al. Dual-Loop Controller for Underwater Snake-Like Robot Based on Dynamic Inverse Solution[J]. IEEE JOURNAL OF OCEANIC ENGINEERING, 2026.
[11] Zheng, YM, Tao, J, Sun, QL, et al. Soft Actor-Critic based active disturbance rejection path following control for unmanned surface vessel under wind and wave disturbances[J]. OCEAN ENGINEERING, 2022, 247.
[12] Yao, P, Lou, YT, Zhang, KM. Multi-USV cooperative path planning by window update based self-organizing map and spectral clustering?[J]. OCEAN ENGINEERING, 2023, 275.
[13] He, WC, Meng, ZC, Li, YZ, et al. LADRC-based wake tracking control via sideslip angle estimation for AUVs following the trajectories of near-surface targets[J]. OCEAN ENGINEERING, 2026, 353.
[14] Chen, TY, Peng, HX, Chang, XY, et al. Co-Design of USV Control System Based on Fuzzy Satisfactory Optimization for Automatic Target Arriving and Berthing[J]. IEEE ACCESS, 2024, 12: 102449-102460.
[15] Zhang, J, Hua, CC, Luo, X, et al. An Output Feedback Approach for 3-D Prescribed Time Stabilization Control of Unmanned Underwater Vehicles[J]. IEEE TRANSACTIONS ON INDUSTRIAL ELECTRONICS, 2024, 71(8): 9580-9589.
[16] Zhang, X, Chen, HJ, Xing, W, et al. Collision-free trajectory tracking strategy of a UUV via finite-time extended state observer-based sliding mode predictive control[J]. JOURNAL OF THE FRANKLIN INSTITUTE-ENGINEERING AND APPLIED MATHEMATICS, 2024, 361(18).
[17] Zheng, JQ, Song, L, Liu, LY, et al. Fixed-time extended state observer-based trajectory tracking control for autonomous underwater vehicles[J]. ASIAN JOURNAL OF CONTROL, 2022, 24(2): 686-701.
[18] Cui, RY, Li, W, Ning, J, et al. Extended state observer based trajectory tracking control of underactuated unmanned surface vehicle with signal quantization[J]. ASIAN JOURNAL OF CONTROL, 2026.
[19] Thai, BH, Ji, S, Yoo, S, et al. A novel combination between finite-time extended state observer and proportional-integral-derivative nonsingular fast terminal sliding mode controller for an autonomous underwater vehicle[J]. NONLINEAR DYNAMICS, 2025, 113(10): 11593-11614.
[20] Feng, N, Wu, DF, Yu, HL, et al. Disturbance rejection event-triggered robust nonlinear model predictive control for underactuated unmanned surface vehicle against DoS attacks without velocity measurements[J]. ISA TRANSACTIONS, 2025, 167: 194-205.
[21] Chen, GF, Sheng, MW, Wan, L, et al. Tracking control for small autonomous underwater vehicles in the Trans-Atlantic Geotraverse hydrothermal field based on the modeling trajectory[J]. APPLIED OCEAN RESEARCH, 2022, 127.
[22] Tong, YP, Huang, B, Wang, Y, et al. Robust motion control of four-vector-thruster AUV "Aurora" under disturbances: optimized ESO-FAISMC control with thrust allocation optimization[J]. AIN SHAMS ENGINEERING JOURNAL, 2025, 16(12).
[23] Cao, G, Yang, J, Qiao, L, et al. Adaptive output feedback super twisting algorithm for trajectory tracking control of USVs with saturated constraints[J]. OCEAN ENGINEERING, 2022, 259.
[24] Luo, QD, Wang, HB, Li, N, et al. Model-free Predictive Trajectory Tracking Control and Obstacle Avoidance for Unmanned Surface Vehicle With Uncertainty and Unknown Disturbances via Model-free Extended State Observer[J]. INTERNATIONAL JOURNAL OF CONTROL AUTOMATION AND SYSTEMS, 2024, 22(6): 1985-1997.
[25] Yan, ZP, Zhang, MY, Zhou, JJ, et al. Distributed Lyapunov-Based Model Predictive Control for AUV Formation Systems with Multiple Constraints[J]. JOURNAL OF MARINE SCIENCE AND ENGINEERING, 2024, 12(3).
[26] Sun, HB, Zong, GD, Cui, JW, et al. Fixed-time sliding mode output feedback tracking control for autonomous underwater vehicle with constraint[J]. OCEAN ENGINEERING, 2022, 247.
[27] Gao, SN, Peng, ZH, Liu, L, et al. Fixed-Time Resilient Edge-Triggered Estimation and Control of Surface Vehicles for Cooperative Target Tracking Under Attacks[J]. IEEE TRANSACTIONS ON INTELLIGENT VEHICLES, 2023, 8(1): 547-556.
[28] Cao, Y, Cui, Y, Liu, ZY, et al. Improved line-of-sight path following for unmanned surface vehicle with exact compensation of sideslip angle[J]. PROCEEDINGS OF THE INSTITUTION OF MECHANICAL ENGINEERS PART M-JOURNAL OF ENGINEERING FOR THE MARITIME ENVIRONMENT, 2025, 239(3): 532-546.
[29] Li, MC, Guo, C, Yu, HM. Extended state observer-based integral line-of-sight guidance law for path following of underactuated unmanned surface vehicles with uncertainties and ocean currents[J]. INTERNATIONAL JOURNAL OF ADVANCED ROBOTIC SYSTEMS, 2021, 18(3).
[30] Zhang, H, He, ZP, Wang, GF, et al. Ocean Currents Compensation-Based IAILOS-ROESOs Guidance and Adaptive Sliding Mode Path Following Control for Unmanned Surface Vehicles[J]. INTERNATIONAL JOURNAL OF ADAPTIVE CONTROL AND SIGNAL PROCESSING, 2025, 39(4): 692-708.
[31] Yan, ZP, Yan, JY, Cai, SJ, et al. Robust MPC-based trajectory tracking of autonomous underwater vehicles with model uncertainty[J]. OCEAN ENGINEERING, 2023, 286.
