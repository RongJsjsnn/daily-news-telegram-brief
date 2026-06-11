from __future__ import annotations

from datetime import datetime

from config import SECTION_ORDER, SECTION_TITLES, Settings
from models import NewsItem


RESTAURANT_IMPACT_KEYWORDS = [
    "消费政策",
    "消费券",
    "促消费",
    "服务消费",
    "消费趋势",
    "消费者支出",
    "食品安全",
    "食品",
    "农产品",
    "粮食",
    "猪肉",
    "蔬菜",
    "水产",
    "油价",
    "燃油",
    "物流",
    "供应链",
    "外卖",
    "外卖平台",
    "AI商业",
    "人工智能应用",
    "人口",
    "客流",
    "旅游",
    "餐饮",
    "食材",
]


def _clean_text(text: str) -> str:
    return " ".join((text or "").replace("\n", " ").split())


def _trim_text(text: str, max_len: int = 120) -> str:
    text = _clean_text(text).strip("，。；、. ")
    if len(text) <= max_len:
        return text
    clipped = text[: max_len - 1]
    for mark in ["。", "；", "，", "、", "."]:
        index = clipped.rfind(mark)
        if index >= max_len // 2:
            clipped = clipped[:index]
            break
    return clipped.rstrip("，。；、. ")


def _ensure_period(text: str) -> str:
    text = text.rstrip("，；、. ")
    if text.endswith(("。", "！", "？")):
        return text
    return f"{text}。"


def _event_context(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}"
    if any(k in text for k in ["就业", "GDP", "通胀", "利率", "油价", "消费者支出", "房地产", "经济增长"]):
        return "原因多与宏观周期、价格压力和市场预期有关，当前进展以官方数据和机构跟踪为主。"
    if any(k in text for k in ["美国", "欧盟", "俄罗斯", "联合国", "中东", "制裁", "关税"]):
        return "背景是地缘政治、贸易规则和安全利益博弈，后续取决于相关国家谈判和政策执行。"
    if any(k in text for k in ["国务院", "部委", "政策", "监管", "地方"]):
        return "背景是政策部门希望稳增长、稳就业或规范行业秩序，当前重点在地方执行和配套落地。"
    if any(k in text for k in ["AI", "人工智能", "芯片", "半导体", "大模型", "互联网"]):
        return "背景是技术商业化和产业竞争加速，当前进展集中在产品落地、监管适配和企业投入。"
    if any(k in text for k in RESTAURANT_IMPACT_KEYWORDS):
        return "背景是消费需求、成本和供应链变化，当前影响仍需看价格、客流和平台政策后续走势。"
    return "目前公开信息主要来自新闻源披露，后续影响仍需观察相关机构、企业或地方执行进展。"


def _news_overview(item: NewsItem) -> str:
    summary = _clean_text(item.summary)
    if summary and summary != item.title:
        base = summary
    else:
        base = f"{item.source} 报道称，{item.title}"
    base = _trim_text(base, 76)
    context = _event_context(item)
    overview = f"{base}。{context}"
    return _ensure_period(_trim_text(overview, 120))


def _brief_summary(item: NewsItem) -> str:
    text = item.summary or item.title
    text = " ".join(text.replace("\n", " ").split())
    if len(text) > 48:
        text = text[:45] + "..."
    return text


def _common_people_impact(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}"
    if any(k in text for k in ["通胀", "价格", "食品", "能源", "利率"]):
        return "这类变化会先传导到生活成本和消费预期，普通家庭应关注食品、能源、房租与贷款支出的边际变化。若价格压力持续，低频大额消费可能继续延后，就业岗位也会更偏向现金流稳定的行业。"
    if any(k in text for k in ["AI", "人工智能", "芯片", "科技", "互联网"]):
        return "技术变化会抬高部分岗位的技能门槛，也会创造运营、内容、销售和本地服务的新工具红利。普通人更需要把 AI 工具纳入日常工作，避免在效率竞争中被动承压。"
    return "对普通人的影响主要体现在就业信心、消费意愿和公共服务预期上。短期不一定立刻改变生活，但会影响企业招聘、居民支出和个人风险偏好。"


def _china_economy_impact(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}"
    if item.category == "international":
        return "外部环境变化会影响中国出口、跨境供应链和企业海外布局节奏。若政策不确定性上升，企业会更重视成本控制、区域分散和国内市场韧性。"
    if item.category == "restaurant":
        return "餐饮相关变化会直接影响食品供应链、门店现金流和居民服务消费。对中国经济而言，餐饮是就业密集型行业，也是观察消费修复质量的重要窗口。"
    if any(k in text for k in ["制造业", "出口", "投资", "产业"]):
        return "这会影响产业链订单、企业投资和就业吸纳能力。若政策端继续加码，制造业和服务业之间的需求传导会成为观察重点。"
    return "这类新闻会通过政策预期、居民消费和企业投资间接影响经济运行。真正需要跟踪的是它是否能转化为订单、就业和实际收入改善。"


def _half_year_forecast(item: NewsItem) -> str:
    if item.category == "technology":
        return "未来半年，技术扩散会继续从概念热度转向商业落地，监管、算力、成本和客户预算将决定行业分化。头部企业会扩大生态绑定，中小企业则更依赖垂直场景。"
    if item.category == "restaurant":
        return "未来半年，餐饮行业大概率继续在低客单、高复购、强供应链之间竞争。下沉市场和区域品牌仍有机会，但粗放扩张会受到房租、人力和流量成本约束。"
    if item.category == "international":
        return "未来半年，外部博弈更可能表现为规则、关税、技术准入和供应链再配置。企业需要按不确定性上升来安排库存、采购和海外市场节奏。"
    return "未来半年，事件影响会取决于政策跟进、企业执行和居民信心恢复速度。若没有配套措施，短期热度可能回落；若形成制度安排，则会逐步影响行业格局。"


def _great_power_logic(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}"
    if any(k in text for k in ["美国", "欧盟", "俄罗斯", "中东", "全球", "制裁", "关税", "芯片", "供应链"]):
        return "这背后体现的是规则制定权、产业链控制权和市场准入权的竞争。中美、欧美及全球南方之间的关系会继续围绕技术、能源、贸易和资本流向重新分层。"
    return "本条新闻大国博弈属性较弱。"


def _restaurant_impact(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}"
    if any(k in text for k in RESTAURANT_IMPACT_KEYWORDS):
        return "餐饮业需要重点关注食材成本、客流恢复和外卖平台费用变化。对万州餐饮尤其是万州烤鱼而言，稳定鱼类供应、优化套餐客单价、借助川渝餐饮流量做品牌化，会比单纯打折更重要。"
    return "本条新闻对餐饮行业影响有限。"


def _core_judgement(item: NewsItem) -> str:
    if item.category == "international":
        return "这条新闻的本质是外部规则变化正在重新定价企业和个人的风险。"
    if item.category == "restaurant":
        return "这条新闻的本质是餐饮竞争正在从开店速度转向供应链和复购能力。"
    if item.category == "technology":
        return "这条新闻的本质是技术红利正在从概念竞争进入效率竞争。"
    return "这条新闻的本质是政策、产业和居民预期之间的再平衡。"


def _render_item(item: NewsItem) -> str:
    published_at = item.published_at.strftime("%Y-%m-%d %H:%M")
    return f"""### 【{item.rating}评级】{item.title}

来源：{item.source} | 发布时间：{published_at}

新闻概述：
{_news_overview(item)}

链接：{item.url}

对普通人的影响：
{_common_people_impact(item)}

对中国经济影响：
{_china_economy_impact(item)}

未来半年预测：
{_half_year_forecast(item)}

大国博弈逻辑：
{_great_power_logic(item)}

对餐饮业影响，尤其万州餐饮：
{_restaurant_impact(item)}

一句话核心判断：
{_core_judgement(item)}
"""


def render_brief(grouped_news: dict[str, list[NewsItem]], settings: Settings, now: datetime) -> str:
    title_date = now.strftime("%Y年%m月%d日")
    lines = [
        f"# 每日战略新闻简报（{title_date}）",
        "",
        f"生成规则：抓取最近 {settings.lookback_hours} 小时新闻，去重后按来源可靠度、时效性和战略影响排序；不包含军事板块。",
        "",
    ]

    for category in SECTION_ORDER:
        lines.append(f"## {SECTION_TITLES[category]}")
        lines.append("")
        items = grouped_news.get(category, [])
        if not items:
            lines.append("近24小时内未抓取到足够可靠的相关 RSS 新闻，建议补充该板块 RSS 或新闻 API。")
            lines.append("")
            continue

        for index, item in enumerate(items):
            lines.append(_render_item(item).strip())
            lines.append("")
            if index < len(items) - 1:
                lines.append("---")
                lines.append("")

    return "\n".join(lines).strip() + "\n"
