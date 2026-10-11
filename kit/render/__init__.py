from . import bland, retell, vapi

PLATFORMS = {"vapi": vapi, "retell": retell, "bland": bland}


def render(platform: str, intake: dict) -> dict:
    return PLATFORMS[platform].render(intake)
