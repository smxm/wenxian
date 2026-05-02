# 一、相关文献总体情况

这批文献聚焦于机器学习在场地效应评估与预测中的应用，主要关注如何利用数据驱动方法改进场地放大因子、地形效应和局部响应的预测精度。研究普遍采用多种机器学习算法（如神经网络、随机森林、支持向量机等）整合多源数据（如强震记录、微动谱比、地形参数、地质条件等），以降低预测误差、增强模型可解释性，并探索在数据稀缺或复杂地质条件下的适用性。文献分布显示，研究重点包括基于代理指标的预测、地形放大效应量化、混合建模框架以及区域微区划应用，旨在支撑地震风险评估和工程抗震设计的系统优化。

# 二、类型划分

## 基于代理指标的场地放大预测

这类文献共同关注如何利用场地条件代理（如VS30、HVSR、频率参数等）和地震动指标，通过机器学习模型预测场地放大因子，以改进传统地面运动预测方程并降低场地间变异性。

- A Data-Driven Approach to Evaluate Site Amplification of Ground-Motion Models Using Vector Proxies Derived from Horizontal-to-Vertical Spectral Ratios
- On the relation between empirical amplification and proxies measured at swiss and japanese stations: Systematic regression analysis and neural network prediction of amplification
- Development of a site and motion proxy-based site amplification model for shallow bedrock profiles using machine learning
- Impact of several site-condition proxies and ground-motion intensity measures on the spectral amplification factor using neuro-fuzzy approach: an example on the KiK-Net dataset
- Neural Network-Based Prediction of Amplification Factors for Nonlinear Soil Behaviour: Insights into Site Proxies

## 地形放大效应的机器学习量化

这类文献共同关注如何利用机器学习算法（如神经网络、U-Net、回归模型）量化地形参数（如坡度、高程、曲率）对地震动放大的影响，旨在提升复杂地形区域的预测精度和计算效率。

- A novel seismic topographic effect prediction method based on neural network models
- A Quantitative Seismic Topographic Effect Prediction Method Based upon BP Neural Network Algorithm and FEM Simulation
- The i-FSC proxy for predicting inter-event and spatial variation of topographic site effects
- Prediction of seismic topographic effects from DEM data via U-Net deep learning model
- Prediction framework of slope topographic amplification on seismic acceleration based on machine learning algorithms

## 神经网络与深度学习方法应用

这类文献共同关注如何应用神经网络和深度学习模型（如DNN、CNN、迁移学习）直接从观测数据（如微动谱比、剪切波速度剖面）估计场地放大因子，以替代传统理论模型并提升泛化能力。

- Machine learning based ground motion site amplification prediction
- Deep-Neural-Network-Based Estimation of Site Amplification Factor from Microtremor H/V Spectral Ratio
- Estimation of site amplification from geotechnical array data using neural networks
- Transfer learning model for estimating site amplification factors from limited microtremor H/V spectral ratios
- Assessment of Site Amplification Factors in Southern Lima, Peru Based on Microtremor H/V Spectral Ratios and Deep Neural Network
- Predicting Models for Local Sedimentary Basin Effect Using a Convolutional Neural Network

## 混合建模与数据融合框架

这类文献共同关注如何结合物理模型与机器学习方法，或整合多源地质与地震数据，以构建混合预测框架，旨在平衡模型精度与数据需求，并增强场地响应预测的可靠性。

- Site amplification prediction model of shallow bedrock sites based on machine learning models
- Seismic site amplification prediction- an integrated Bayesian optimisation explainable machine learning approach
- Combining physical model with neural networks for earthquake site response prediction
- Correspondence between Site Amplification and Topographical, Geological Parameters: Collation of Data from Swiss and Japanese Stations, and Neural Networks-Based Prediction of Local Response

## 区域微区划与风险评估应用

这类文献共同关注如何利用机器学习技术基于环境噪声或地质数据绘制区域场地放大图或进行微区划，以支持城市地震风险评估和灾害地图的系统设计。

- Machine learning techniques for estimating seismic site amplification in the Santiago basin, Chile
- Establishing site response-based micro-zonation by applying machine learning techniques on ambient noise data: a case study from Northern Potwar Region, Pakistan

# 三、逐篇文献总结分析

## A Data-Driven Approach to Evaluate Site Amplification of Ground-Motion Models Using Vector Proxies Derived from Horizontal-to-Vertical Spectral Ratios

总结：
该文献提出了一种基于强震数据的数据驱动框架，利用水平-垂直谱比（HVSR）代理来改进地面运动模型中的场地放大预测。研究通过集成多种机器学习算法（如多元回归、随机森林和支持向量机）及特征选择方法，构建自动化工作流程，并对比了数据驱动模型与传统模型的场地间变异性。结果表明，采用HVSR谱向量的数据驱动模型能显著降低场地间变异性，尤其在低频段效果更佳，支持向量机模型相比基线模型平均降低24.1%的变异性。

分析：
该文献对于机器学习在场地效应评估中的应用具有重要参考价值，它展示了数据驱动方法如何通过HVSR代理优化场地放大预测，适用于支撑基于强震数据的场地分类和变异性分析机制。其自动化工作流程和特征选择策略可为类似系统设计提供借鉴，特别是在处理地震工程中的不确定性时，有助于提升预测模型的准确性和鲁棒性。

## A novel seismic topographic effect prediction method based on neural network models

总结：
该文献研究了一种基于神经网络模型的地形放大效应预测方法，通过有限元数值模拟分析地形变量与放大因子的关系，并利用反向传播神经网络进行量化。结果表明，海拔、坡度、坡向和频率是影响地形放大的关键变量，神经网络方法能有效预测地形效应，并提出了两种输入变量组合以平衡精度与可扩展性。

分析：
该文献对于机器学习在场地效应评估中的应用具有参考价值，它展示了神经网络如何量化地形对地震动的影响，适合支撑场地效应预测中的机制建模和系统设计。其方法可用于优化地震风险评估工具，特别是在复杂地形区域的放大因子预测场景中，为研究脉络提供了基于数据驱动的实证案例。

## Machine learning based ground motion site amplification prediction

总结：
该文献研究了利用机器学习预测地震动场地放大因子，通过整合KiK-net台站记录的六个参数，应用随机森林、XGBoost和深度神经网络算法进行预测，并采用SHAP分析解释参数重要性。结果表明，机器学习方法相比传统GMPE显著提升了预测精度，其中XGBoost表现最佳，SHAP分析增强了结果的可解释性。

分析：
该文献对于报告主题‘机器学习在场地效应评估与预测中的应用’具有直接参考价值，它展示了机器学习如何改进场地放大因子的预测机制，适用于地震灾害分析中的风险评估场景。其方法可支撑系统设计，如结合SHAP分析提升模型可解释性，为研究脉络提供实证案例。

## On the relation between empirical amplification and proxies measured at swiss and japanese stations: Systematic regression analysis and neural network prediction of amplification

总结：
该文献通过系统回归分析和神经网络预测，研究了瑞士和日本台站场地条件指标（如VS30、基岩深度）与经验放大函数之间的关系。回归分析表明，场地条件参数在1.7-6.7 Hz频段内与放大因子相关性较好，其中频率相关的四分之一波长速度和VS30等指标表现最佳。神经网络预测结果与回归分析一致，更完整的输入信息（如四分之一波长参数）能更好地估计局部放大效应。

分析：
该文献对于机器学习在场地效应评估中的应用具有参考价值，因为它展示了如何利用神经网络整合多源场地条件数据来预测放大效应。它适合支撑基于代理指标的场地放大预测机制，特别是在地震工程中用于系统设计或风险评估场景。文献中对比瑞士和日本数据的相似性，为跨区域机器学习模型的应用提供了实证基础。

## Site amplification prediction model of shallow bedrock sites based on machine learning models

总结：
该文献研究了基于机器学习模型预测浅层基岩场地放大效应的方法。通过随机森林和深度神经网络算法，利用场地响应分析模拟数据中的输入地震动响应谱和剪切波速剖面矩阵，替代传统简化场地参数。结果表明，两种机器学习模型在线性和非线性放大预测上均优于回归模型，其中深度神经网络模型预测精度更高。

分析：
该文献对于机器学习在场地效应评估中的应用具有参考价值，展示了机器学习在提升场地放大预测精度方面的潜力。它适合支撑基于数据驱动的场地效应预测机制，可应用于地震风险评估和工程抗震设计场景，为系统设计提供更准确的场地放大估计方法。

## Seismic site amplification prediction- an integrated Bayesian optimisation explainable machine learning approach

总结：
该研究提出了一种集成贝叶斯优化和可解释机器学习的框架，用于预测地震场地放大效应。基于日本KiK-Net强震网络数据，开发了多种机器学习模型，其中回归树集成（RTE）模型表现最优，显著降低了预测误差。研究还利用Shapley加性解释等方法增强模型透明度，揭示了关键变量的影响。

分析：
该文献为机器学习在场地效应评估中的应用提供了具体案例，适合支撑基于数据驱动的预测机制。其集成贝叶斯优化和可解释性分析的方法，可参考用于提升地震风险评估系统的设计精度和可靠性。

## A Quantitative Seismic Topographic Effect Prediction Method Based upon BP Neural Network Algorithm and FEM Simulation

总结：
该文献提出了一种基于BP神经网络算法和三维有限元模拟的定量地震地形效应预测方法。研究通过有限元模拟发现，峰值加速度和反应谱随高程增加而增大，但低矮山丘的峰值加速度放大系数与坡度相关性不明显。建立的BP神经网络模型能够有效预测放大系数，预测误差较小且训练效率较高。

分析：
该文献为机器学习在地震场地效应评估中的应用提供了具体案例，展示了BP神经网络在预测地形放大系数方面的可行性和精度。其方法适合支撑地震工程中场地效应预测的自动化系统设计，特别是针对复杂地形条件下的地震动参数快速评估。研究中的输入变量组合设计思路可为类似预测模型的工程应用提供参考。

## Deep-Neural-Network-Based Estimation of Site Amplification Factor from Microtremor H/V Spectral Ratio

总结：
该文献提出了一种基于深度神经网络（DNN）的新方法，直接从微动水平-垂直谱比（MHVR）估计S波场地放大因子（SAF）。研究利用日本中国地区的观测数据，通过峰值频率和频率依赖关系训练模型，并采用k折交叉验证优化性能。结果表明，DNN模型在估计SAF方面优于现有的双经验校正方法，具有更好的泛化能力。

分析：
该文献对于机器学习在场地效应评估中的应用具有重要参考价值，它展示了DNN如何直接从微动数据中提取场地放大因子，适用于地震风险评估中的信号处理机制。这为系统设计提供了新思路，特别是在缺乏传统钻孔数据的场景下，可支撑更高效、自动化的场地效应预测研究脉络。

## Development of a site and motion proxy-based site amplification model for shallow bedrock profiles using machine learning

总结：
该研究针对浅层基岩场地，利用机器学习技术开发了基于场地和运动代理的线性与非线性场地放大模型。通过随机森林、XGBoost和深度神经网络算法，结合一维场地响应分析数据，模型显著提升了预测性能，优于传统回归方法。结果表明，同时使用场地和运动代理进行训练能有效捕捉地震响应中的复杂非线性相互作用。

分析：
该文献为机器学习在地震场地效应评估中的应用提供了具体案例，适合支撑基于代理的预测机制和区域地震动建模场景。其模型设计思路可参考用于优化系统设计中的数据处理流程，特别是在数据有限条件下提升预测准确性。研究脉络上，它展示了机器学习如何替代传统方法，为相关领域的技术改进提供实证基础。

## Estimation of site amplification from geotechnical array data using neural networks

总结：
该文献利用深度学习技术，基于约600个KiK-net垂直台阵站点的观测数据，训练全连接神经网络和卷积神经网络，从离散化的剪切波速度剖面预测地表至钻孔的傅里叶放大函数。与基于理论SH一维放大函数的预测相比，神经网络在未用于训练的站点上使预测与观测之间的均方对数误差降低了高达50%。研究表明，神经网络可能实现一种纯粹数据驱动的场地响应预测方法，不依赖于代理变量或简化假设。

分析：
该文献为机器学习在场地效应评估中的应用提供了具体案例，展示了神经网络在预测场地放大函数方面的有效性。它适合支撑基于数据驱动的场地响应预测机制，特别是在处理复杂地质条件时减少对理论模型的依赖。对于研究如何将实际台阵数据与深度学习结合以改进地震工程中的场地分类和风险评估具有参考价值。

## The i-FSC proxy for predicting inter-event and spatial variation of topographic site effects

总结：
该文献研究了近源区域地形对地震动放大的预测，通过神经网络识别控制放大的关键几何参数，并建立了i-FSC代理模型。该模型结合频率缩放曲率和归一化照明角，能有效预测地形放大因子，且计算资源需求低。

分析：
该文献为机器学习在场地效应评估中的应用提供了具体机制，i-FSC代理模型适用于支撑地形放大效应的量化预测系统设计。它特别适合应用于近断层区域的地震风险评估，有助于优化场地效应研究中的计算效率和准确性。

## Transfer learning model for estimating site amplification factors from limited microtremor H/V spectral ratios

总结：
该文献研究了利用迁移学习技术改进基于微动水平垂直谱比的场地放大因子估计模型。通过预训练的深度神经网络模型，结合新区域数据构建迁移学习模型，提升了在有限数据下的预测性能。结果表明，该模型在外部测试集上优于原模型，并验证了在小样本数据下的有效性。

分析：
该文献对于机器学习在场地效应评估中的应用具有参考价值，特别适合支撑迁移学习在数据稀缺场景下的机制设计。它提供了利用预训练模型适应新区域的方法，可应用于地震风险评估中的场地放大预测系统。

## Assessment of Site Amplification Factors in Southern Lima, Peru Based on Microtremor H/V Spectral Ratios and Deep Neural Network

总结：
该文献提出了一种基于微动水平垂直谱比和深度神经网络的场地放大因子评估方法，旨在低成本、高精度地估计地震波放大效应。研究验证了该模型在秘鲁利马南部的适用性，通过约250个站点的数据分析，发现东南沿海风成砂区域在低频段存在较大放大，而西北冲积层区域放大较小。

分析：
该文献对于机器学习在场地效应评估中的应用具有直接参考价值，其深度神经网络模型可支撑场地放大因子的快速量化评估机制。它适用于地震灾害风险评估场景，为系统设计提供了基于微动数据的预测方法，有助于研究脉络中机器学习与地球物理数据的结合应用。

## Machine learning techniques for estimating seismic site amplification in the Santiago basin, Chile

总结：
该文献提出了一种基于机器学习的方法，整合定性和定量数据来绘制智利圣地亚哥盆地的地震场地放大图。该方法利用剪切波速度、优势频率和重力异常图等数据，通过空间协变量训练模型，提高了放大图、Vs30和f0的预测精度。结果表明机器学习在数字土壤制图中具有超越传统地统计技术的潜力，能有效扩展局部动态特性的测量。

分析：
该文献对于机器学习在场地效应评估中的应用具有直接参考价值，展示了如何结合多源地质数据提升预测准确性。它适合支撑基于人工智能的场地放大量化机制，为区域地震风险评估提供方法学支持，并可用于优化地震灾害地图的系统设计。

## Establishing site response-based micro-zonation by applying machine learning techniques on ambient noise data: a case study from Northern Potwar Region, Pakistan

总结：
该研究应用机器学习技术于环境噪声数据，以建立基于场地响应参数的微区划。通过聚类分析，识别出三个不同脆弱性区域，并利用Arc GIS工具展示空间分布。结果表明研究区域对场地放大具有中到高度脆弱性，地震事件可能导致灾难性后果。

分析：
该文献为机器学习在场地效应评估中的应用提供了具体案例，适合支撑基于环境噪声数据的场地放大预测机制。其微区划方法可应用于城市地震风险评估系统设计，有助于优化场地响应参数的空间分析研究脉络。

## Correspondence between Site Amplification and Topographical, Geological Parameters: Collation of Data from Swiss and Japanese Stations, and Neural Networks-Based Prediction of Local Response

总结：
该研究通过整合瑞士和日本台站的地形、地质参数与实测场地放大因子数据，分析了间接参数与场地局部响应的相关性。研究发现低频段（0.5-3.33 Hz）相关性更高，地形参数主要通过反映地下特性影响放大效应。研究进一步利用神经网络预测场地响应，在1.67-5 Hz频段取得最佳效果，且地形参数比地质参数更具预测力。

分析：
该文献为机器学习在场地效应评估中的应用提供了实证案例，展示了神经网络如何利用地形地质参数预测场地放大。其数据集整合方法和参数相关性分析，可支撑场地效应预测模型的输入特征选择机制。研究结果特别适用于缺乏现场测量数据时，基于公开地理信息进行场地响应预测的应用场景。

## Combining physical model with neural networks for earthquake site response prediction

总结：
该文献提出了一种结合神经网络与经典均匀分层模型的方法，用于预测地震场地响应。该方法从物理和数据角度提升预测精度，降低了模型复杂度和训练数据量的需求。相比纯物理驱动方法，平均减少约50%的估计误差，并首次在全地震频段再现场地响应的四阶段特征。

分析：
该文献为机器学习在地震场地效应评估中的应用提供了混合建模框架，适合支撑物理与数据融合的预测机制。它可用于地震风险分析和抗震设计场景，为系统设计提供兼顾准确性与效率的参考，并丰富了研究脉络中关于模型简化与数据增强的讨论。

## Prediction of seismic topographic effects from DEM data via U-Net deep learning model

总结：
该研究利用U-Net深度学习模型，以数字高程模型（DEM）数据为输入，预测地震地形放大效应，通过多层卷积提取地形特征并结合多尺度信息。模型在四川-西藏地区二郎山区域应用，基于谱元法模拟地震动，结果显示U-Net模型在均方根误差上优于传统反向传播神经网络，且加入入射角和地下速度结构可提高预测精度。

分析：
该文献为机器学习在场地效应评估中的应用提供了数据驱动框架，特别适合支撑地形放大效应的预测机制，可应用于地震工程中的局部地震响应分析。其U-Net模型设计适用于处理空间地形数据，有助于系统设计中的多尺度特征整合，为研究脉络中结合地形与地下条件耦合影响提供了参考。

## Impact of several site-condition proxies and ground-motion intensity measures on the spectral amplification factor using neuro-fuzzy approach: an example on the KiK-Net dataset

总结：
该文献利用自适应神经模糊推理系统（ANFIS）机器学习算法，基于KiK-Net数据集，研究了22种场地条件代理和3种地震动强度指标对响应谱放大因子的影响。通过敏感性分析，确定了PGV/VS30为最有效的地震动强度指标，并选取了[f0HV, CV2, PGV/VS30]作为最优变量组合，以综合考虑场地刚度和深度特性。研究旨在为地震规范修订和场地特定研究提供改进的场地效应评估方法。

分析：
该文献对于机器学习在场地效应评估与预测中的应用主题具有重要参考价值，它展示了如何利用ANFIS算法整合多种场地参数和地震动指标来预测谱放大因子。其敏感性分析方法和变量组合策略，可支撑场地效应预测模型的机制设计，适用于地震工程中的场地分类和抗震设计优化场景。

## Predicting Models for Local Sedimentary Basin Effect Using a Convolutional Neural Network

总结：
该研究针对梯形沉积盆地，通过构建标准盆地模型量化场地条件参数与放大参数的关系，并利用卷积神经网络（CNN）建立盆地放大特征的预测模型。研究采用贝叶斯优化方法选择CNN结构参数以提高预测精度，结果表明优化后的CNN模型能有效预测峰值地面加速度的最大放大值和危险位置。

分析：
该文献为机器学习在场地效应评估中的应用提供了具体案例，展示了CNN如何替代传统递归算法快速预测场地放大特征。它适合支撑基于深度学习的场地响应预测机制，适用于地震灾害评估和工程实践中的场地放大效应分析，为系统设计提供了数据驱动的建模思路。

## Prediction framework of slope topographic amplification on seismic acceleration based on machine learning algorithms

总结：
该文献研究了基于机器学习算法预测斜坡地形对地震加速度的放大效应。通过采用人工智能回归算法，以斜坡倾角、高度和地震波频率为参数，建立了放大比与参数间的多元非线性关系预测模型。结果表明，相比传统方法，该模型的确定系数提高了17.84%–32.60%，均方根误差降低了30.05%–77.36%，并成功应用于实际地震案例，为工程抗震设计提供了指导。

分析：
该文献对于机器学习在场地效应评估中的应用主题具有重要参考价值，它展示了机器学习在量化斜坡地形放大效应中的有效性，适合支撑场地效应预测的建模机制。其方法可应用于地震风险评估和工程抗震设计场景，为系统设计提供数据驱动的预测框架，并丰富了机器学习在地震工程中的研究脉络。

## Neural Network-Based Prediction of Amplification Factors for Nonlinear Soil Behaviour: Insights into Site Proxies

总结：
该研究采用广义回归神经网络和径向基函数网络，基于324个非线性砂土和黏土柱的波传播数据库，预测地震放大因子。通过参数化分析，识别了影响放大因子的关键场地和地震参数，如峰值地面加速度和共振频率，并提出了简化预测方程。结果表明，使用有限参数可显著降低预测偏差，尤其对于软土的长周期放大因子有重要发现。

分析：
该文献为机器学习在场地效应评估中的应用提供了具体案例，展示了神经网络如何优化土壤分类和放大因子预测。它适合支撑基于数据驱动的场地放大机制研究，为地震工程中的代码改进和基础设施设计提供参考。研究中的参数选择和简化方程可直接应用于系统设计，增强预测的实用性和准确性。

# 参考列表

[1] Esteghamati, M.Z, Kottke, A.R, Rodriguez-Marek, A. A Data-Driven Approach to Evaluate Site Amplification of Ground-Motion Models Using Vector Proxies Derived from Horizontal-to-Vertical Spectral Ratios[J]. Bulletin of the Seismological Society of America, 2022, 112(6): 3001-3015.
[2] Jiang, Q, Wei, W, Xu, H, et al. A novel seismic topographic effect prediction method based on neural network models[J]. European Physical Journal Plus, 2023, 138(11).
[3] Wang, X, Wang, Z, Wang, J, et al. Machine learning based ground motion site amplification prediction[J]. Frontiers in Earth Science, 2023, 11.
[4] Bergamo, P, Hammer, C, Fäh, D. On the relation between empirical amplification and proxies measured at swiss and japanese stations: Systematic regression analysis and neural network prediction of amplification[J]. Bulletin of the Seismological Society of America, 2021, 111(1): 101-120.
[5] Lee, Y.-G, Kim, S.-J, Achmet, Z, et al. Site amplification prediction model of shallow bedrock sites based on machine learning models[J]. Soil Dynamics and Earthquake Engineering, 2023, 166.
[6] Raja, M.N.A, Mercado, V, Abdoun, T, et al. Seismic site amplification prediction- an integrated Bayesian optimisation explainable machine learning approach[J]. Georisk, 2025, 19(3): 573-592.
[7] Jiang, Q, Rong, M, Wei, W, et al. A Quantitative Seismic Topographic Effect Prediction Method Based upon BP Neural Network Algorithm and FEM Simulation[J]. Journal of Earth Science, 2024, 35(4): 1355-1366.
[8] Pan, D, Miura, H, Kanno, T, et al. Deep-Neural-Network-Based Estimation of Site Amplification Factor from Microtremor H/V Spectral Ratio[J]. Bulletin of the Seismological Society of America, 2022, 112(3): 1630-1646.
[9] Lee, Y.-G, Park, D, Kwon, O.-S. Development of a site and motion proxy-based site amplification model for shallow bedrock profiles using machine learning[J]. Frontiers in Built Environment, 2025, 11.
[10] Roten, D, Olsen, K.B. Estimation of site amplification from geotechnical array data using neural networks[J]. Bulletin of the Seismological Society of America, 2021, 111(4): 1784-1794.
[11] Bou Nassif, A, Maufroy, E, Lacroix, P, et al. The i-FSC proxy for predicting inter-event and spatial variation of topographic site effects[J]. Bulletin of Earthquake Engineering, 2025, 23(2): 671-692.
[12] Pan, D, Miura, H, Kwan, C. Transfer learning model for estimating site amplification factors from limited microtremor H/V spectral ratios[J]. Geophysical Journal International, 2024, 237(1): 622-635.
[13] Miura, H, Gonzales, C, Diaz, M, et al. Assessment of Site Amplification Factors in Southern Lima, Peru Based on Microtremor H/V Spectral Ratios and Deep Neural Network[J]. Journal of Disaster Research, 2023, 18(4): 298-307.
[14] Díaz, J.P, Sáez, E, Monsalve, M, et al. Machine learning techniques for estimating seismic site amplification in the Santiago basin, Chile[J]. Engineering Geology, 2022, 306.
[15] Qadri, S.M.T, Malik, O.A. Establishing site response-based micro-zonation by applying machine learning techniques on ambient noise data: a case study from Northern Potwar Region, Pakistan[J]. Environmental Earth Sciences, 2021, 80(2).
[16] Bergamo, P, Hammer, C, Fäh, D. Correspondence between Site Amplification and Topographical, Geological Parameters: Collation of Data from Swiss and Japanese Stations, and Neural Networks-Based Prediction of Local Response[J]. Bulletin of the Seismological Society of America, 2022, 112(2): 1008-1030.
[17] Zhang, H, Zheng, K, Miao, Y. Combining physical model with neural networks for earthquake site response prediction[J]. Soil Dynamics and Earthquake Engineering, 2025, 189.
[18] Li, Y, Zhou, H. Prediction of seismic topographic effects from DEM data via U-Net deep learning model[J]. European Physical Journal Plus, 2026, 141(1).
[19] Zaoui, M.A.I, Derras, B, Régnier, J. Impact of several site-condition proxies and ground-motion intensity measures on the spectral amplification factor using neuro-fuzzy approach: an example on the KiK-Net dataset[J]. Natural Hazards, 2025, 121(7): 8703-8732.
[20] Yang, X, Hu, M, Chen, X, et al. Predicting Models for Local Sedimentary Basin Effect Using a Convolutional Neural Network[J]. Applied Sciences (Switzerland), 2023, 13(16).
[21] Ju, S, Jia, J, Pan, X. Prediction framework of slope topographic amplification on seismic acceleration based on machine learning algorithms[J]. Engineering Applications of Artificial Intelligence, 2024, 133.
[22] Boudghene Stambouli, A, Guizani, L. Neural Network-Based Prediction of Amplification Factors for Nonlinear Soil Behaviour: Insights into Site Proxies[J]. Applied Sciences (Switzerland), 2025, 15(7).
