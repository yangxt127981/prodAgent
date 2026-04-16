"""排期信息服务 - 通过 Offer 单号查询商品直播排期"""
from __future__ import annotations

import httpx

OFFER_API_BASE = "https://zsxp.meione.cc/services/selection/api/show-schedule-offers/offer-code"

SALES_STATUS_MAP = {
    "SpotOffer": "现货在售",
    "Purchase": "预购商品",
}

LIVE_ROOM_MAP = {
    "ZB": "最佳福直播间",
    "SY2": "时尚女生直播间",
    "SYC": "时尚女生的衣橱",
    "SXF": "时尚姐姐的衣橱",
}

OFFER_TYPE_MAP = {
    "Cosmetic": "美妆",
    "Food": "食品",
    "Fashion": "时尚",
    "Dailylife": "生活",
    "Electronic": "消费电子",
    "Motherbaby": "母婴",
}


def fetch_offer_schedule(offer_code: str, auth_token: str) -> str:
    """同步调用排期接口，返回格式化的排期信息文本"""
    if not auth_token:
        return "（排期接口未配置 Authorization，无法获取排期信息）"
    try:
        with httpx.Client(timeout=10.0) as client:
            # 自动补充 Bearer 前缀
            token = auth_token if auth_token.startswith("Bearer ") else f"Bearer {auth_token}"
            resp = client.get(
                f"{OFFER_API_BASE}/{offer_code}",
                headers={"Authorization": token},
            )
        if resp.status_code != 200:
            return f"（排期接口返回异常状态码：{resp.status_code}）"

        data = resp.json()
        if not data:
            return "暂无排期信息"

        lines = []
        for item in data:
            show_date = (item.get("showDate") or "")[:10] or "未知"
            sales_status = SALES_STATUS_MAP.get(item.get("salesStatus", ""), item.get("salesStatus", "未知"))
            live_room = LIVE_ROOM_MAP.get(item.get("liveRoom", ""), item.get("liveRoom", "未知"))
            show_scene = item.get("showScene") or "未知"
            topic = item.get("topicName") or ""
            lines.append(
                f"直播日期：{show_date} | 直播间：{live_room} | 场次：{show_scene}"
                + (f" | 专题：{topic}" if topic else "")
                + f" | 状态：{sales_status}"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"（获取排期信息失败：{e}）"
