# 一、相关文献总体情况

这批文献聚焦于人工智能与扩展现实技术在猫咪及动物交互中的应用，主要关注多模态感知、智能干预、XR界面与数字孪生设备等方向。研究普遍采用深度学习、计算机视觉和传感器数据分析等技术，重点解决动物情感识别、行为监测和疼痛评估等实际问题。文献在技术方法上呈现多样化，包括基于图像的面部地标分析、声音情感识别、传感器数据行为分类以及可解释性框架等，整体上体现了AI技术在动物交互领域从感知到干预的完整技术链条。

# 二、类型划分

## 面部表情与疼痛识别

这类文献主要关注利用计算机视觉和机器学习技术，通过分析猫咪面部特征（特别是地标点）来自动识别疼痛表情。研究比较了不同方法（如几何地标分析与深度学习）的准确性，并探讨了动态视频信息对识别效果的影响。

- Automated landmark-based cat facial analysis and its applications
- Automated video-based pain recognition in cats using facial landmarks
- Explainable automated pain recognition in cats
- Automated recognition of pain in cats

## 多模态情感与行为感知

这类文献侧重于结合多种感知模态（如视觉、声音、传感器数据）来识别动物的情感状态或行为模式。研究采用深度学习网络处理图像、声音频谱或惯性测量单元数据，实现高精度的情感分类或行为识别。

- Sentiment analysis of pets using deep learning technologies in artificial intelligence of things system
- Cat and Dog Behavior Recognition Method Using Deep Learning Approach Based on Inertial Measurement Unit Sensor Data
- JL-TFMSFNet: A domestic cat sound emotion recognition method based on jointly learning the time-frequency domain and multi-scale features

## 可解释性与模型评估

这类文献关注动物情感计算中AI模型的可解释性问题，通过量化评估框架（如显著性图分析）来揭示分类器决策依据的生物相关区域（如眼睛、鼻子），旨在提升模型透明度和可靠性。

- A segment-based framework for explainability in animal affective computing

## 交互学习与虚拟训练

这类文献探索通过虚拟环境或游戏化界面，让宠物机器人学习理解用户的多模态反馈，采用数学模型（如隐马尔可夫模型）实现自适应交互，为智能干预和XR界面设计提供参考。

- Teaching a pet-robot to understand user feedback through interactive virtual training tasks

# 三、逐篇文献总结分析

## Sentiment analysis of pets using deep learning technologies in artificial intelligence of things system

总结：
该文献提出了一种基于人工智能物联网系统的宠物情感分析方法，利用Mask R-CNN进行图像对象检测和姿态分析，并结合声音信号转换为频谱图作为特征，通过深度学习技术识别宠物情感。通过融合姿态与情感特征进行宠物情感识别，并将特定行为状态主动通知主人，相比传统语音识别方法，实验结果显示准确率提升了70%。

分析：
该文献对于AI/XR技术在动物交互中的应用具有参考价值，其多模态感知方法（结合视觉和声音特征）可支撑智能干预系统的设计，适用于宠物健康监测或行为管理场景。文献中的深度学习机制和物联网集成思路，可为数字孪生设备或XR界面开发提供技术借鉴，特别是在提升情感识别准确性和实时通知功能方面。

## Automated landmark-based cat facial analysis and its applications

总结：
该文献研究了基于面部地标的自动化猫咪面部分析方法，采用48个地标方案和AI流程，实现了品种识别、头型识别和疼痛识别等任务。结果表明，该方法在疼痛评估和形态学探索中具有潜力，准确率分别达到66%和75%。

分析：
该文献对于报告主题中AI在猫咪交互中的应用具有参考价值，其自动化地标检测机制可支撑多模态感知系统的设计，特别是在疼痛评估和形态分析场景中，为智能干预和数字孪生设备提供技术基础。

## Cat and Dog Behavior Recognition Method Using Deep Learning Approach Based on Inertial Measurement Unit Sensor Data

总结：
该文献研究了一种基于惯性测量单元传感器数据和深度学习方法的猫狗行为识别技术。通过构建一维卷积神经网络与长短期记忆混合模型，针对加速度计、陀螺仪和磁力计数据提取关键运动特征，实现了对猫和狗常见行为的高精度分类，准确率分别达到89%和94%。

分析：
该文献对于当前报告主题的参考价值在于，它展示了深度学习在多模态感知中处理传感器数据的机制，适用于动物交互中的行为监测应用场景。其模型设计可支撑智能干预系统的开发，为数字孪生设备提供行为识别基础，并丰富了AI在动物福利研究中的技术脉络。

## JL-TFMSFNet: A domestic cat sound emotion recognition method based on jointly learning the time-frequency domain and multi-scale features

总结：
该文献提出了一种名为JL-TFMSFNet的深度学习网络，用于家猫声音情感识别。该方法通过联合学习时频域信息和多尺度特征，结合梅尔特征提取、时频注意力机制和多分支模块，在自建和公开数据集上实现了优于现有模型的识别性能，平均准确率超过94%。

分析：
该文献为AI与猫咪交互中的多模态感知提供了具体技术方案，其联合学习时频域与多尺度特征的机制可直接应用于智能干预系统的声音情感分析模块。其提出的网络架构和注意力机制设计，对开发数字孪生设备中的实时声音处理组件具有参考价值。

## Automated video-based pain recognition in cats using facial landmarks

总结：
该研究提出了一种基于视频的端到端AI管道，用于自动识别猫咪的疼痛表情，利用48个面部地标点并优化时间维度信息捕获。该方法无需人工选择图像或标注地标，在两个不同数据集上分别达到超过70%和66%的准确率，优于以往基于单帧图像的方法，表明动态信息对猫咪疼痛识别至关重要。

分析：
该文献为AI与动物交互主题提供了视频动态分析的技术参考，适合支撑多模态感知中视觉时序信息处理的机制。其端到端自动化管道设计可应用于智能干预系统的实时疼痛监测场景，而数据集缺陷度量的定义有助于优化数字孪生设备的数据质量控制。

## Explainable automated pain recognition in cats

总结：
该研究探讨了在更现实的多品种、多性别环境下，使用AI模型对猫咪进行'疼痛'/'无痛'分类的可行性。研究比较了基于几何标志点的方法和深度学习方法，发现前者在更异质的数据集上表现更优，准确率超过77%。同时，研究还分析了机器学习识别的可解释性，发现鼻子和嘴巴区域对疼痛分类更为重要。

分析：
该文献为AI在动物行为评估中的应用提供了具体案例，特别适合支撑多模态感知中的视觉分析机制。其可解释性分析有助于设计更透明的智能干预系统，而基于异质数据集的研究方法对开发适应现实场景的数字孪生设备具有参考价值。

## Automated recognition of pain in cats

总结：
该文献研究了通过自动化方法识别猫咪面部疼痛表情，比较了基于卷积神经网络（ResNet50）和基于几何地标分析（受猫FACS启发）的两种机器学习路径。研究在29只家猫卵巢子宫切除术的不同时间点采集图像，对应不同疼痛强度，两种方法均达到72%以上的准确率。结果表明这两种方法可作为自动化猫咪疼痛检测的基础工具。

分析：
该文献为AI与XR技术在动物交互中的应用提供了具体的感知技术参考，其基于图像的面部表情识别机制可直接用于多模态感知系统中的视觉分析模块。研究中的两种机器学习方法（深度学习与地标分析）为智能干预系统设计提供了可选的疼痛检测方案，特别适合支撑需要客观评估动物状态的XR界面或数字孪生设备开发。

## A segment-based framework for explainability in animal affective computing

总结：
该文献提出了一种基于分段的框架，旨在增强动物情感计算领域的可解释性。该框架通过评估和比较显著性图，引入定量评分机制来衡量分类器输出与预定义语义区域的对齐程度。在猫、马和狗的数据集上评估显示，眼睛区域是分类器最重要的特征，揭示了机器识别动物情感状态的新见解。

分析：
该文献为动物情感计算中的AI模型可解释性提供了量化评估方法，适合支撑多模态感知系统中的信任构建和模型优化机制。其框架可应用于智能干预场景，帮助研究人员验证分类器是否使用预期的生物相关区域，从而提升XR界面或数字孪生设备中情感识别的可靠性。

## Teaching a pet-robot to understand user feedback through interactive virtual training tasks

总结：
该文献提出了一种人机教学框架，通过虚拟游戏在受控环境中让宠物机器人学习理解用户的多模态正负反馈。研究采用结合隐马尔可夫模型和经典条件反射数学模型的两阶段学习方法，使机器人能基于游戏状态预测反馈并探索用户奖励行为。实验结果显示，系统训练后对正负反馈的平均识别准确率达到90.33%。

分析：
该文献对于AI与XR技术在动物交互中的应用具有参考价值，其虚拟训练任务和反馈学习机制可支撑智能干预系统的设计，特别是在多模态感知和自适应交互场景中。它提供了通过游戏化界面实现机器人行为调整的思路，适合用于数字孪生设备或XR界面的用户适应性研究。

# 参考列表

[1] Tsai, MF, Huang, JY. Sentiment analysis of pets using deep learning technologies in artificial intelligence of things system[J]. SOFT COMPUTING, 2021, 25(21): 13741-13752.
[2] Martvel, G, Lazebnik, T, Feighelstein, M, et al. Automated landmark-based cat facial analysis and its applications[J]. FRONTIERS IN VETERINARY SCIENCE, 2024, 11.
[3] Chen, GY, Takegawa, Y, Matsumura, K, et al. Cat and Dog Behavior Recognition Method Using Deep Learning Approach Based on Inertial Measurement Unit Sensor Data[J]. SENSORS AND MATERIALS, 2025, 37(3): 1073-1098.
[4] Tang, L, Hu, SP, Yang, CJ, et al. JL-TFMSFNet: A domestic cat sound emotion recognition method based on jointly learning the time-frequency domain and multi-scale features[J]. EXPERT SYSTEMS WITH APPLICATIONS, 2024, 255.
[5] Martvel, G, Lazebnik, T, Feighelstein, M, et al. Automated video-based pain recognition in cats using facial landmarks[J]. SCIENTIFIC REPORTS, 2024, 14(1).
[6] Feighelstein, M, Henze, L, Meller, S, et al. Explainable automated pain recognition in cats[J]. SCIENTIFIC REPORTS, 2023, 13(1).
[7] Feighelstein, M, Shimshoni, I, Finka, LR, et al. Automated recognition of pain in cats[J]. SCIENTIFIC REPORTS, 2022, 12(1).
[8] Boneh-Shitrit, T, Finka, L, Mills, DS, et al. A segment-based framework for explainability in animal affective computing[J]. SCIENTIFIC REPORTS, 2025, 15(1).
[9] Austermann, A, Yamada, S. Teaching a pet-robot to understand user feedback through interactive virtual training tasks[J]. AUTONOMOUS AGENTS AND MULTI-AGENT SYSTEMS, 2010, 20(1): 85-104.
