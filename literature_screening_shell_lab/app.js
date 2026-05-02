const blueprints = {
  draft: {
    name: "低温限制土壤磷活性",
    demand: "温限环境下，哪些机制会影响土壤磷活性变化，以及现有证据主要来自哪些研究场景。",
    subtitle: "刚建线程",
    topic: "等待补充主题",
    topicAlt: "低温与冻融对土壤磷活性的影响",
    inclusion: ["等待补充纳入标准"],
    inclusionAlt: ["寒地或温限环境", "含磷活性直接证据"],
    exclusion: ["等待补充排除标准"],
    exclusionAlt: ["与低温无关", "没有磷机制结论"],
    databases: ["Scopus", "WoS", "PubMed", "CNKI"],
    planCount: 0,
    rounds: 0,
    reportTitle: "低温限制土壤磷活性-report",
    reportTitleAlt: "低温限制土壤磷活性-summary",
    reportTopic: "等待纳入文献后生成报告主题",
    reportTopicAlt: "围绕低温和冻融情景生成综述框架",
    reportModel: "deepseek-chat",
    reportProvider: "DeepSeek",
    reportGenerated: false,
    candidates: [],
    activity: [
      { tone: "muted", time: "刚刚", text: "线程已创建" },
      { tone: "muted", time: "刚刚", text: "等待补充主题与标准" }
    ]
  },
  active: {
    name: "低温限制土壤磷活性",
    demand: "温限环境下，哪些机制会影响土壤磷活性变化，以及现有证据主要来自哪些研究场景。",
    subtitle: "推进中",
    topic: "低温与季节冻融对土壤磷活性的限制机制",
    topicAlt: "寒地生态系统中低温对磷活性与周转的约束",
    inclusion: ["低温、冻融或寒地环境", "含磷活性或磷形态证据", "实验或实证研究"],
    inclusionAlt: ["低温场景", "含直接证据", "机制或实证研究"],
    exclusion: ["只谈施肥产量", "无磷机制结论", "与寒地环境无关"],
    exclusionAlt: ["无磷机制", "纯背景综述", "不在目标场景"],
    databases: ["Scopus", "WoS", "PubMed", "CNKI"],
    planCount: 4,
    rounds: 2,
    reportTitle: "低温限制土壤磷活性-report",
    reportTitleAlt: "低温限制土壤磷活性-mechanism",
    reportTopic: "围绕低温、冻融与微生物过程梳理土壤磷活性变化机制",
    reportTopicAlt: "按环境、机制与证据类型重组纳入文献",
    reportModel: "deepseek-reasoner",
    reportProvider: "DeepSeek",
    reportGenerated: false,
    candidates: [
      {
        id: "c1",
        title: "Phosphorus dynamics in seasonally frozen soils under alpine grassland",
        journal: "Soil Biology & Biochemistry",
        year: 2024,
        authors: "Li Y, Wang H",
        pages: "118-132",
        language: "EN",
        relevance: 93,
        hasLink: false,
        hasPdf: false,
        access: "pending",
        decision: "undecided",
        note: "需要先补首选链接。"
      },
      {
        id: "c2",
        title: "冻融循环对黑土磷有效性的影响研究",
        journal: "土壤通报",
        year: 2023,
        authors: "张某某, 李某某",
        pages: "266-274",
        language: "ZH",
        relevance: 96,
        hasLink: true,
        hasPdf: false,
        access: "ready",
        decision: "undecided",
        note: "中文证据完整，可以直接终判。"
      },
      {
        id: "c3",
        title: "Cold-region phosphorus immobilization driven by microbial turnover",
        journal: "Geoderma",
        year: 2022,
        authors: "Chen P, Zhao T",
        pages: "115823",
        language: "EN",
        relevance: 91,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "include",
        note: "机制清晰，已纳入报告。"
      },
      {
        id: "c4",
        title: "高寒草甸土壤磷形态与温度胁迫响应",
        journal: "生态学报",
        year: 2021,
        authors: "王某某, 刘某某",
        pages: "88-97",
        language: "ZH",
        relevance: 89,
        hasLink: true,
        hasPdf: false,
        access: "pending",
        decision: "undecided",
        note: "保留中文落地页。"
      },
      {
        id: "c5",
        title: "Microbial mediation of phosphorus availability during freeze-thaw events",
        journal: "Soil Ecology Letters",
        year: 2024,
        authors: "Qian L, Moore S",
        pages: "45-59",
        language: "EN",
        relevance: 92,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "exclude",
        note: "方法适合，但主题不够聚焦。"
      }
    ],
    activity: [
      { tone: "success", time: "09:16", text: "已生成线程方案" },
      { tone: "warning", time: "09:42", text: "候选池新增 18 篇文献" },
      { tone: "success", time: "10:03", text: "已有 1 篇纳入报告" }
    ]
  },
  report: {
    name: "低温限制土壤磷活性",
    demand: "温限环境下，哪些机制会影响土壤磷活性变化，以及现有证据主要来自哪些研究场景。",
    subtitle: "报告可生成",
    topic: "低温与季节冻融对土壤磷活性的限制机制",
    topicAlt: "寒地生态系统中磷活性约束机制",
    inclusion: ["寒地或温限环境", "含磷活性直接证据", "机制或实证研究"],
    inclusionAlt: ["寒地场景", "机制证据", "可进入报告"],
    exclusion: ["无磷机制证据", "纯背景综述", "与目标场景无关"],
    exclusionAlt: ["无机制", "不在目标场景", "证据不足"],
    databases: ["Scopus", "WoS", "PubMed", "CNKI"],
    planCount: 4,
    rounds: 3,
    reportTitle: "低温限制土壤磷活性-report",
    reportTitleAlt: "低温限制土壤磷活性-final",
    reportTopic: "围绕低温、冻融、微生物周转和磷形态变化生成机制综述",
    reportTopicAlt: "按环境类型和机制路径组织纳入文献",
    reportModel: "deepseek-chat",
    reportProvider: "DeepSeek",
    reportGenerated: true,
    candidates: [
      {
        id: "r1",
        title: "冻融循环对黑土磷有效性的影响研究",
        journal: "土壤通报",
        year: 2023,
        authors: "张某某, 李某某",
        pages: "266-274",
        language: "ZH",
        relevance: 96,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "include",
        note: "中文证据完整，已纳入。"
      },
      {
        id: "r2",
        title: "Microbial mediation of phosphorus availability during freeze-thaw events",
        journal: "Soil Ecology Letters",
        year: 2024,
        authors: "Li Y, Wang H",
        pages: "45-59",
        language: "EN",
        relevance: 92,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "include",
        note: "可放入机制章节。"
      },
      {
        id: "r3",
        title: "Cold-region phosphorus immobilization driven by microbial turnover",
        journal: "Geoderma",
        year: 2022,
        authors: "Chen P, Zhao T",
        pages: "115823",
        language: "EN",
        relevance: 91,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "include",
        note: "已纳入报告。"
      },
      {
        id: "r4",
        title: "高寒草甸土壤磷形态与低温胁迫耦合效应",
        journal: "生态学报",
        year: 2021,
        authors: "王某某, 刘某某",
        pages: "88-97",
        language: "ZH",
        relevance: 90,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "include",
        note: "可放入中文证据组。"
      },
      {
        id: "r5",
        title: "Freeze-thaw controls on phosphorus mineralization in alpine meadow soils",
        journal: "Environmental Soil Science",
        year: 2020,
        authors: "Moore S, Davis K",
        pages: "301-318",
        language: "EN",
        relevance: 87,
        hasLink: true,
        hasPdf: true,
        access: "ready",
        decision: "include",
        note: "补足高寒场景。"
      }
    ],
    activity: [
      { tone: "success", time: "14:08", text: "候选文献终判完成" },
      { tone: "success", time: "14:12", text: "报告源更新为 5 篇" },
      { tone: "warning", time: "14:16", text: "等待确认报告模型" }
    ]
  }
}

const stageRouteMap = {
  plan: "thread",
  screening: "workbench",
  workbench: "workbench",
  report: "report"
}

const host = document.querySelector("#scene-host")
const toast = document.querySelector("#toast")
const sceneButtons = [...document.querySelectorAll(".scene-button")]
const scenarioButtons = [...document.querySelectorAll(".scenario-button[data-scenario]")]
const demoActionButtons = [...document.querySelectorAll(".scenario-button[data-demo-action]")]

const state = {
  scene: "thread",
  scenario: "active",
  workflow: "all",
  selectedCandidateId: null,
  reportTab: "outline",
  demo: null,
  toastTimer: null,
  reportGenerating: false
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value))
}

function stageLabel(stage) {
  switch (stage) {
    case "needs-link":
      return "待补链接"
    case "needs-access":
      return "待获取全文"
    case "ready-for-decision":
      return "待终判"
    case "report-included":
      return "已纳入报告"
    case "report-excluded":
      return "最终排除"
    case "unavailable":
      return "无权限"
    case "deferred":
      return "暂缓"
    default:
      return "待处理"
  }
}

function stageTone(stage) {
  if (stage === "report-included" || stage === "ready-for-decision") return "success"
  if (stage === "needs-link" || stage === "needs-access" || stage === "deferred") return "warning"
  if (stage === "report-excluded" || stage === "unavailable") return "danger"
  return "muted"
}

function workflowLabel(key) {
  if (key === "retrieval") return "待获取全文"
  if (key === "decision") return "待终判"
  if (key === "done") return "已完成"
  return "全部候选"
}

function deriveStage(candidate) {
  if (candidate.decision === "include") return "report-included"
  if (candidate.decision === "exclude") return "report-excluded"
  if (candidate.access === "unavailable") return "unavailable"
  if (candidate.access === "deferred") return "deferred"
  if (candidate.access === "ready") return "ready-for-decision"
  if (!candidate.hasLink) return "needs-link"
  return "needs-access"
}

function reportSources(demo) {
  return demo.candidates.filter((candidate) => candidate.decision === "include")
}

function summaryOf(demo) {
  const counts = {
    total: demo.candidates.length,
    retrieval: 0,
    decision: 0,
    done: 0,
    included: 0,
    excluded: 0
  }

  demo.candidates.forEach((candidate) => {
    const stage = deriveStage(candidate)
    if (stage === "needs-link" || stage === "needs-access") counts.retrieval += 1
    if (stage === "ready-for-decision") counts.decision += 1
    if (stage === "report-included" || stage === "report-excluded") counts.done += 1
    if (stage === "report-included") counts.included += 1
    if (stage === "report-excluded") counts.excluded += 1
  })

  return counts
}

function workflowCards(demo) {
  const counts = summaryOf(demo)
  return [
    { key: "all", label: "全部候选", count: counts.total, copy: "总览" },
    { key: "retrieval", label: "待获取全文", count: counts.retrieval, copy: "开链接" },
    { key: "decision", label: "待终判", count: counts.decision, copy: "做终判" },
    { key: "done", label: "已完成", count: counts.done, copy: "已处理" }
  ]
}

function filteredCandidates(demo) {
  if (state.workflow === "all") return demo.candidates
  if (state.workflow === "retrieval") {
    return demo.candidates.filter((candidate) => {
      const stage = deriveStage(candidate)
      return stage === "needs-link" || stage === "needs-access"
    })
  }
  if (state.workflow === "decision") {
    return demo.candidates.filter((candidate) => deriveStage(candidate) === "ready-for-decision")
  }
  return demo.candidates.filter((candidate) => {
    const stage = deriveStage(candidate)
    return stage === "report-included" || stage === "report-excluded"
  })
}

function selectedCandidate(demo) {
  const list = filteredCandidates(demo)
  const current = list.find((candidate) => candidate.id === state.selectedCandidateId)
  return current ?? list[0] ?? null
}

function syncSelection() {
  const current = selectedCandidate(state.demo)
  state.selectedCandidateId = current ? current.id : null
}

function timeNow() {
  return new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit" }).format(new Date())
}

function addActivity(text, tone = "muted") {
  state.demo.activity.unshift({ text, tone, time: timeNow() })
}

function loadScenario(key) {
  state.scenario = key
  state.demo = deepClone(blueprints[key])
  state.workflow = "all"
  state.reportTab = state.demo.reportGenerated ? "outline" : "structure"
  state.reportGenerating = false
  state.selectedCandidateId = state.demo.candidates[0]?.id ?? null
  syncScenarioButtons()
  render()
}

function syncScenarioButtons() {
  scenarioButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.scenario === state.scenario)
  })
}

function syncSceneButtons() {
  sceneButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.scene === state.scene)
  })
}

function setScene(nextScene) {
  state.scene = nextScene
  syncSceneButtons()
  render()
}

function showToast(text) {
  toast.textContent = text
  toast.classList.add("is-visible")
  window.clearTimeout(state.toastTimer)
  state.toastTimer = window.setTimeout(() => {
    toast.classList.remove("is-visible")
  }, 2200)
}

function upgradeDraftToActive() {
  if (state.scenario !== "draft") return
  loadScenario("active")
  showToast("已切到推进中示例。")
}

function toggleManualEdit() {
  const demo = state.demo
  const usingAlt = demo.topic === demo.topicAlt
  demo.topic = usingAlt ? blueprints[state.scenario].topic : demo.topicAlt
  demo.inclusion = usingAlt ? deepClone(blueprints[state.scenario].inclusion) : deepClone(demo.inclusionAlt)
  demo.exclusion = usingAlt ? deepClone(blueprints[state.scenario].exclusion) : deepClone(demo.exclusionAlt)
  addActivity(usingAlt ? "恢复默认主题与标准" : "已切换到手动编辑版本", "warning")
  showToast(usingAlt ? "已恢复默认主题与标准。" : "已切到手动编辑版本。")
  render()
}

function clickThreadAction(action) {
  if (action === "edit") {
    toggleManualEdit()
    return
  }
  if (action === "plan") {
    upgradeDraftToActive()
    addActivity("查看线程方案", "success")
    showToast("已展示线程方案状态。")
    render()
    return
  }
  if (action === "screening" || action === "workbench") {
    upgradeDraftToActive()
    setScene("workbench")
    showToast(action === "screening" ? "进入初筛后的候选处理示例。" : "进入统一复核示例。")
    return
  }
  setScene("report")
}

function setWorkflow(nextWorkflow) {
  state.workflow = nextWorkflow
  syncSelection()
  render()
}

function setCandidate(id) {
  state.selectedCandidateId = id
  render()
}

function mutateCandidate(action) {
  const candidate = selectedCandidate(state.demo)
  if (!candidate) {
    showToast("当前没有可处理文献。")
    return
  }

  if (action === "open") {
    if (!candidate.hasLink) {
      showToast("当前没有首选链接。")
      return
    }
    addActivity(`打开《${candidate.title}》的首选链接`, "muted")
    showToast("已打开示意链接。")
    render()
    return
  }

  if (action === "link") {
    candidate.hasLink = true
    addActivity(`补充《${candidate.title}》的首选链接`, "warning")
    showToast("已补充首选链接。")
    render()
    return
  }

  if (action === "ready") {
    if (!candidate.hasLink) {
      showToast("请先补链接。")
      return
    }
    candidate.access = "ready"
    candidate.hasPdf = true
    addActivity(`标记《${candidate.title}》为已获取全文`, "success")
    showToast("已标记为已获取全文。")
    render()
    return
  }

  if (action === "unavailable") {
    candidate.access = "unavailable"
    addActivity(`标记《${candidate.title}》为无权限`, "danger")
    showToast("已标记为无权限。")
    render()
    return
  }

  if (action === "deferred") {
    candidate.access = "deferred"
    addActivity(`暂缓《${candidate.title}》`, "warning")
    showToast("已暂缓。")
    render()
    return
  }

  if (action === "include") {
    if (candidate.access !== "ready") {
      showToast("先把全文状态标为已获取。")
      return
    }
    candidate.decision = "include"
    addActivity(`纳入《${candidate.title}》进入报告源`, "success")
    showToast("已纳入报告。")
    render()
    return
  }

  if (action === "exclude") {
    candidate.decision = "exclude"
    addActivity(`最终排除《${candidate.title}》`, "danger")
    showToast("已最终排除。")
    render()
    return
  }
}

function setReportModel(modelName) {
  state.demo.reportModel = modelName
  state.demo.reportProvider = modelName.startsWith("kimi") ? "Kimi" : "DeepSeek"
  addActivity(`切换报告模型为 ${modelName}`, "warning")
  render()
}

function setReferenceStyle(style) {
  state.demo.referenceStyle = style
  showToast(`参考样式已切到 ${style === "apa7" ? "APA 7" : "GB/T 7714"}。`)
  render()
}

function cycleField(field) {
  if (field === "title") {
    state.demo.reportTitle =
      state.demo.reportTitle === state.demo.reportTitleAlt ? blueprints[state.scenario].reportTitle : state.demo.reportTitleAlt
  }
  if (field === "topic") {
    state.demo.reportTopic =
      state.demo.reportTopic === state.demo.reportTopicAlt ? blueprints[state.scenario].reportTopic : state.demo.reportTopicAlt
  }
  render()
}

function buildReferenceLine(candidate, index, style) {
  if (style === "apa7") {
    return `[${index}] ${candidate.authors} (${candidate.year}). ${candidate.title}. ${candidate.journal}, ${candidate.pages}.`
  }
  return `[${index}] ${candidate.authors}. ${candidate.title}[J]. ${candidate.journal}, ${candidate.year}: ${candidate.pages}.`
}

function buildReferencePreview() {
  const style = state.demo.referenceStyle || "gbt7714"
  const sources = reportSources(state.demo)
  if (!sources.length) {
    return "[1] 当前纳入文献为 0，暂时无法生成参考列表。"
  }
  return sources.map((candidate, index) => buildReferenceLine(candidate, index + 1, style)).join("\n")
}

function buildOutlinePreview() {
  const sources = reportSources(state.demo)
  if (!sources.length) {
    return "1. 研究背景\n2. 证据分组\n3. 机制讨论\n4. 研究空白\n\n当前报告源为 0。"
  }
  const blocks = sources.slice(0, 4).map((candidate, index) => `${index + 1}. ${candidate.title}`)
  return `1. 研究背景\n2. 环境分组\n3. 机制分组\n4. 研究空白\n\n纳入文献：\n${blocks.join("\n")}`
}

function generateReport() {
  const sources = reportSources(state.demo)
  if (!sources.length) {
    showToast("当前纳入文献为 0，暂时无法生成报告。")
    return
  }
  if (state.reportGenerating) return
  state.reportGenerating = true
  render()
  window.setTimeout(() => {
    state.reportGenerating = false
    state.demo.reportGenerated = true
    state.reportTab = "outline"
    addActivity("已生成报告预览", "success")
    render()
    showToast("报告预览已生成。")
  }, 850)
}

function autoAdvance() {
  if (state.scene === "thread") {
    if (state.scenario === "draft") {
      upgradeDraftToActive()
      return
    }
    setScene("workbench")
    showToast("已切到候选池。")
    return
  }

  if (state.scene === "workbench") {
    const nextCandidate =
      state.demo.candidates.find((candidate) => deriveStage(candidate) === "needs-link")
      ?? state.demo.candidates.find((candidate) => deriveStage(candidate) === "needs-access")
      ?? state.demo.candidates.find((candidate) => deriveStage(candidate) === "ready-for-decision")
      ?? null

    if (!nextCandidate) {
      setScene("report")
      showToast("候选池已处理完，切到报告台。")
      return
    }

    state.selectedCandidateId = nextCandidate.id
    const nextStage = deriveStage(nextCandidate)
    if (nextStage === "needs-link") {
      mutateCandidate("link")
      return
    }
    if (nextStage === "needs-access") {
      mutateCandidate("ready")
      return
    }
    mutateCandidate("include")
    return
  }

  generateReport()
}

function activityMarkup(demo) {
  return demo.activity
    .slice(0, 5)
    .map(
      (item) => `
        <article class="activity-item">
          <span class="${toneClass(item.tone)}">${item.time}</span>
          <div>${item.text}</div>
        </article>
      `
    )
    .join("")
}

function toneClass(tone) {
  return `tone-${tone === "success" ? "success" : tone === "warning" ? "warning" : tone === "danger" ? "danger" : "muted"}`
}

function renderThreadScene(demo) {
  const counts = summaryOf(demo)
  const stageCards = [
    { key: "plan", label: "线程方案", count: demo.planCount, copy: demo.planCount ? "已生成" : "待生成" },
    { key: "screening", label: "初筛轮次", count: demo.rounds, copy: demo.rounds ? "继续新增" : "还没开始" },
    { key: "workbench", label: "统一复核", count: counts.total, copy: counts.total ? "进入处理" : "暂无候选" },
    { key: "report", label: "生成报告", count: reportSources(demo).length, copy: reportSources(demo).length ? "可以生成" : "暂无报告源" }
  ]
  const nextAction =
    demo.planCount === 0 ? "先生成检索方案"
      : counts.retrieval > 0 ? "先处理待获取全文"
        : counts.decision > 0 ? "先完成终判"
          : reportSources(demo).length > 0 ? "可以生成报告"
            : "等待下一轮"

  return `
    <section class="scene-shell">
      <section class="hero-panel">
        <div>
          <div class="eyebrow">Thread</div>
          <div class="hero-title">${demo.name}</div>
          <p class="hero-subtitle">${demo.subtitle}</p>
          <div class="status-strip">
            ${demo.databases.map((item) => `<span class="status-chip">${item}</span>`).join("")}
            <span class="status-chip strong">报告源 ${reportSources(demo).length}</span>
          </div>
        </div>
        <div class="hero-metrics">
          <article class="metric-box">
            <small>研究需求</small>
            <strong>已录入</strong>
          </article>
          <article class="metric-box">
            <small>当前主题</small>
            <strong>${demo.topic === "等待补充主题" ? "待补充" : "已固定"}</strong>
          </article>
          <article class="metric-box">
            <small>下一步</small>
            <strong>${nextAction}</strong>
          </article>
        </div>
      </section>

      <section class="thread-grid">
        <section class="content-panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Context</div>
              <h3>一条线程，四个入口</h3>
            </div>
            <button class="ghost-button" data-thread-action="edit" type="button">编辑主题与标准</button>
          </div>

          <div class="context-grid">
            <article class="context-card">
              <div class="context-label">研究需求</div>
              <div class="context-value">${demo.demand}</div>
            </article>
            <article class="context-card">
              <div class="context-label">当前主题</div>
              <div class="context-value">${demo.topic}</div>
            </article>
            <article class="context-card">
              <div class="context-label">纳入标准</div>
              <div class="context-value">${demo.inclusion.join(" / ")}</div>
            </article>
            <article class="context-card">
              <div class="context-label">排除标准</div>
              <div class="context-value">${demo.exclusion.join(" / ")}</div>
            </article>
          </div>

          <div class="stage-entry-row">
            <button class="action-button primary" data-thread-action="plan" type="button">
              <strong>生成检索方案</strong>
              <span>进入方案阶段</span>
            </button>
            <button class="action-button" data-thread-action="screening" type="button">
              <strong>开始新一轮初筛</strong>
              <span>继续推进</span>
            </button>
            <button class="action-button" data-thread-action="workbench" type="button">
              <strong>进入统一复核</strong>
              <span>处理候选文献</span>
            </button>
            <button class="action-button warning" data-thread-action="report" type="button">
              <strong>生成报告</strong>
              <span>打开报告台</span>
            </button>
          </div>
        </section>

        <aside class="action-panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Snapshot</div>
              <h3>阶段快照</h3>
            </div>
          </div>
          <div class="stage-snapshot-grid compact-four">
            ${stageCards
              .map(
                (item) => `
                  <button class="snapshot-card stage-card-button" data-stage-route="${item.key}" type="button">
                    <div class="snapshot-label">${item.label}</div>
                    <strong>${item.count}</strong>
                    <div class="microcopy">${item.copy}</div>
                  </button>
                `
              )
              .join("")}
          </div>

          <div class="section-head section-head-tight">
            <div>
              <div class="eyebrow">Activity</div>
              <h3>最近动作</h3>
            </div>
          </div>
          <div class="activity-log">
            ${activityMarkup(demo)}
          </div>
        </aside>
      </section>
    </section>
  `
}

function candidateCard(candidate) {
  const stage = deriveStage(candidate)
  return `
    <article class="candidate-card ${candidate.id === state.selectedCandidateId ? "is-active" : ""}" data-candidate-id="${candidate.id}">
      <div class="candidate-head">
        <div>
          <div class="candidate-title">${candidate.title}</div>
          <div class="candidate-meta">${candidate.journal} · ${candidate.year} · ${candidate.language}</div>
        </div>
        <span class="${toneClass(stageTone(stage))}">${stageLabel(stage)}</span>
      </div>
      <div class="candidate-reason">相关度 ${candidate.relevance}% · ${candidate.note}</div>
    </article>
  `
}

function renderWorkbenchScene(demo) {
  const cards = workflowCards(demo)
  const visibleCandidates = filteredCandidates(demo)
  const focused = selectedCandidate(demo)
  const stage = focused ? deriveStage(focused) : null

  return `
    <section class="scene-shell">
      <section class="hero-panel">
        <div>
          <div class="eyebrow">Workbench</div>
          <div class="hero-title">候选池只做三件事</div>
          <p class="hero-subtitle">开链接、标状态、做终判。</p>
          <div class="workflow-grid">
            ${cards
              .map(
                (item) => `
                  <button class="workflow-card ${state.workflow === item.key ? "is-active" : ""}" data-workflow="${item.key}" type="button">
                    <small>${item.label}</small>
                    <strong>${item.count}</strong>
                    <div class="microcopy">${item.copy}</div>
                  </button>
                `
              )
              .join("")}
          </div>
        </div>
        <div class="hero-metrics">
          <article class="metric-box">
            <small>候选总数</small>
            <strong>${cards[0].count}</strong>
          </article>
          <article class="metric-box">
            <small>待终判</small>
            <strong>${cards[2].count}</strong>
          </article>
          <article class="metric-box">
            <small>已纳入报告</small>
            <strong>${reportSources(demo).length}</strong>
          </article>
        </div>
      </section>

      <section class="workbench-grid">
        <section class="list-panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Pool</div>
              <h3>${workflowLabel(state.workflow)}</h3>
            </div>
            <div class="microcopy">${visibleCandidates.length} 篇</div>
          </div>
          <div class="candidate-toolbar">
            <div class="search-shell">搜索 / 筛选占位</div>
            <button class="ghost-button" data-goto-scene="thread" type="button">回线程总览</button>
          </div>
          <div class="candidate-list">
            ${visibleCandidates.length ? visibleCandidates.map(candidateCard).join("") : `<article class="candidate-card is-active"><div class="candidate-title">当前分组为空</div><div class="candidate-reason">切换上方分组，或点击“自动演示一步”。</div></article>`}
          </div>
        </section>

        <aside class="focus-panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Inspector</div>
              <h3>${focused ? focused.title : "等待选择文献"}</h3>
            </div>
            <span class="${toneClass(stage ? stageTone(stage) : "muted")}">${focused ? stageLabel(stage) : "空状态"}</span>
          </div>

          ${
            focused
              ? `
                <div class="step-stack">
                  <article class="step-card">
                    <div class="step-index">1</div>
                    <div class="context-card">
                      <div class="step-title">先开链接</div>
                      <div class="step-copy">${focused.hasLink ? "已有首选链接。" : "当前还没有首选链接。"}</div>
                      <div class="action-grid" style="margin-top: 14px;">
                        <button class="tiny-button primary" data-candidate-action="${focused.hasLink ? "open" : "link"}" type="button">
                          ${focused.hasLink ? "打开首选链接" : "补首选链接"}
                        </button>
                        <button class="tiny-button" data-candidate-action="open" type="button" ${focused.hasPdf ? "" : "disabled"}>
                          打开 PDF
                        </button>
                      </div>
                    </div>
                  </article>

                  <article class="step-card">
                    <div class="step-index">2</div>
                    <div class="context-card">
                      <div class="step-title">再标状态</div>
                      <div class="step-copy">当前：${focused.access === "ready" ? "已获取全文" : focused.access === "unavailable" ? "无权限" : focused.access === "deferred" ? "暂缓" : "待处理"}</div>
                      <div class="action-grid" style="margin-top: 14px;">
                        <button class="tiny-button primary" data-candidate-action="ready" type="button">标记已获取</button>
                        <button class="tiny-button" data-candidate-action="unavailable" type="button">无权限</button>
                        <button class="tiny-button" data-candidate-action="deferred" type="button">暂缓</button>
                      </div>
                    </div>
                  </article>

                  <article class="step-card">
                    <div class="step-index">3</div>
                    <div class="context-card">
                      <div class="step-title">最后终判</div>
                      <div class="step-copy">当前：${focused.decision === "include" ? "已纳入报告" : focused.decision === "exclude" ? "最终排除" : "尚未终判"}</div>
                      <div class="action-grid" style="margin-top: 14px;">
                        <button class="tiny-button primary" data-candidate-action="include" type="button">纳入报告</button>
                        <button class="tiny-button" data-candidate-action="exclude" type="button">最终排除</button>
                      </div>
                    </div>
                  </article>
                </div>

                <div class="section-head section-head-tight">
                  <div>
                    <div class="eyebrow">Activity</div>
                    <h3>最近动作</h3>
                  </div>
                </div>
                <div class="activity-log">
                  ${activityMarkup(demo)}
                </div>
              `
              : `
                <div class="context-card" style="margin-top: 18px;">
                  <div class="step-title">当前没有可处理文献</div>
                  <div class="step-copy">切换分组，或点击左侧“自动演示一步”。</div>
                </div>
              `
          }
        </aside>
      </section>
    </section>
  `
}

function renderReportScene(demo) {
  const sources = reportSources(demo)
  const referenceStyle = demo.referenceStyle || "gbt7714"
  const previewBody = state.reportTab === "references" ? buildReferencePreview() : buildOutlinePreview()

  return `
    <section class="scene-shell">
      <section class="hero-panel">
        <div>
          <div class="eyebrow">Report</div>
          <div class="hero-title">报告始终可见</div>
          <p class="hero-subtitle">即使当前报告源为 0，也能先看到报告入口和生成方式。</p>
        </div>
        <div class="hero-metrics">
          <article class="metric-box">
            <small>报告源</small>
            <strong>${sources.length}</strong>
          </article>
          <article class="metric-box">
            <small>模型</small>
            <strong>${demo.reportModel}</strong>
          </article>
          <article class="metric-box">
            <small>状态</small>
            <strong>${state.reportGenerating ? "生成中" : demo.reportGenerated ? "已生成预览" : sources.length ? "可以生成" : "等待纳入"}</strong>
          </article>
        </div>
      </section>

      <section class="report-grid">
        <section class="report-panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Config</div>
              <h3>报告面板</h3>
            </div>
            <span class="${sources.length ? "tone-success" : "tone-warning"}">报告源 ${sources.length}</span>
          </div>

          <div class="field-stack">
            <button class="field-shell field-button" data-cycle-field="title" type="button">
              <strong>报告任务名</strong>
              <div class="muted">${demo.reportTitle}</div>
            </button>
            <button class="field-shell field-button" data-cycle-field="topic" type="button">
              <strong>报告主题</strong>
              <div class="muted">${demo.reportTopic}</div>
            </button>
            <div class="report-model-grid">
              <div class="field-shell">
                <strong>模型</strong>
                <div class="chip-row">
                  ${["deepseek-chat", "deepseek-reasoner", "kimi-k2"]
                    .map(
                      (item) => `
                        <button class="ghost-chip ${demo.reportModel === item ? "is-active" : ""}" data-report-model="${item}" type="button">${item}</button>
                      `
                    )
                    .join("")}
                </div>
              </div>
              <div class="field-shell">
                <strong>参考样式</strong>
                <div class="chip-row">
                  ${["gbt7714", "apa7"]
                    .map(
                      (item) => `
                        <button class="ghost-chip ${referenceStyle === item ? "is-active" : ""}" data-reference-style="${item}" type="button">
                          ${item === "gbt7714" ? "GB/T 7714" : "APA 7"}
                        </button>
                      `
                    )
                    .join("")}
                </div>
              </div>
            </div>
          </div>

          <div class="action-grid" style="margin-top: 18px;">
            <button class="ghost-button warning" data-report-generate type="button" ${state.reportGenerating ? "disabled" : ""}>
              ${state.reportGenerating ? "生成中..." : "生成报告"}
            </button>
            <button class="ghost-button" data-goto-scene="workbench" type="button">回候选池</button>
          </div>

          <div class="preview-shell">
            <div class="preview-tabs">
              <button class="preview-tab ${state.reportTab === "outline" ? "is-active" : ""}" data-report-tab="outline" type="button">结构</button>
              <button class="preview-tab ${state.reportTab === "references" ? "is-active" : ""}" data-report-tab="references" type="button">参考列表</button>
            </div>
            <div class="preview-body">${previewBody.replace(/\n/g, "<br>")}</div>
          </div>
        </section>

        <aside class="action-panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Sources</div>
              <h3>纳入文献</h3>
            </div>
          </div>
          <div class="report-source-list">
            ${
              sources.length
                ? sources
                    .map(
                      (candidate, index) => `
                        <button class="source-card source-button" data-source-id="${candidate.id}" type="button">
                          <div class="source-head">
                            <strong>${String(index + 1).padStart(2, "0")}</strong>
                            <span class="tone-success">已纳入</span>
                          </div>
                          <div class="source-title">${candidate.title}</div>
                          <div class="source-copy">${candidate.journal} · ${candidate.year}</div>
                        </button>
                      `
                    )
                    .join("")
                : `
                  <article class="source-card">
                    <div class="source-title">当前没有报告源</div>
                    <div class="source-copy">先去候选池把文献纳入报告。</div>
                  </article>
                `
            }
          </div>

          <div class="section-head section-head-tight">
            <div>
              <div class="eyebrow">Activity</div>
              <h3>最近动作</h3>
            </div>
          </div>
          <div class="activity-log">
            ${activityMarkup(demo)}
          </div>
        </aside>
      </section>
    </section>
  `
}

function render() {
  syncSelection()
  syncSceneButtons()

  if (state.scene === "thread") {
    host.innerHTML = renderThreadScene(state.demo)
  } else if (state.scene === "workbench") {
    host.innerHTML = renderWorkbenchScene(state.demo)
  } else {
    host.innerHTML = renderReportScene(state.demo)
  }

  bindRenderedEvents()
}

function bindRenderedEvents() {
  host.querySelectorAll("[data-thread-action]").forEach((button) => {
    button.addEventListener("click", () => {
      clickThreadAction(button.dataset.threadAction)
    })
  })

  host.querySelectorAll("[data-stage-route]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.stageRoute
      if (key === "plan") {
        clickThreadAction("plan")
        return
      }
      setScene(stageRouteMap[key])
    })
  })

  host.querySelectorAll("[data-goto-scene]").forEach((button) => {
    button.addEventListener("click", () => {
      setScene(button.dataset.gotoScene)
    })
  })

  host.querySelectorAll("[data-workflow]").forEach((button) => {
    button.addEventListener("click", () => {
      setWorkflow(button.dataset.workflow)
    })
  })

  host.querySelectorAll("[data-candidate-id]").forEach((button) => {
    button.addEventListener("click", () => {
      setCandidate(button.dataset.candidateId)
    })
  })

  host.querySelectorAll("[data-candidate-action]").forEach((button) => {
    button.addEventListener("click", () => {
      mutateCandidate(button.dataset.candidateAction)
    })
  })

  host.querySelectorAll("[data-report-model]").forEach((button) => {
    button.addEventListener("click", () => {
      setReportModel(button.dataset.reportModel)
    })
  })

  host.querySelectorAll("[data-reference-style]").forEach((button) => {
    button.addEventListener("click", () => {
      setReferenceStyle(button.dataset.referenceStyle)
    })
  })

  host.querySelectorAll("[data-cycle-field]").forEach((button) => {
    button.addEventListener("click", () => {
      cycleField(button.dataset.cycleField)
    })
  })

  host.querySelectorAll("[data-report-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.reportTab = button.dataset.reportTab
      render()
    })
  })

  host.querySelector("[data-report-generate]")?.addEventListener("click", () => {
    generateReport()
  })

  host.querySelectorAll("[data-source-id]").forEach((button) => {
    button.addEventListener("click", () => {
      setScene("workbench")
      state.selectedCandidateId = button.dataset.sourceId
      state.workflow = "done"
      render()
    })
  })
}

sceneButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setScene(button.dataset.scene)
  })
})

scenarioButtons.forEach((button) => {
  button.addEventListener("click", () => {
    loadScenario(button.dataset.scenario)
  })
})

demoActionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.demoAction === "reset") {
      loadScenario(state.scenario)
      showToast("已重置当前场景。")
      return
    }
    autoAdvance()
  })
})

loadScenario("active")
