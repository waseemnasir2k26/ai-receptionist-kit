"""Writes presets/*.json. Run once; the JSON files are the source of truth afterwards."""
import json
from pathlib import Path

WEEK_STD = {"mon": "08:00-17:00", "tue": "08:00-17:00", "wed": "08:00-17:00", "thu": "08:00-17:00",
            "fri": "08:00-17:00", "sat": None, "sun": None}
WEEK_SAT = dict(WEEK_STD, sat="09:00-13:00")
WEEK_DENT = {"mon": "08:00-17:00", "tue": "08:00-17:00", "wed": "08:00-17:00", "thu": "08:00-17:00",
             "fri": "08:00-14:00", "sat": None, "sun": None}

P = {
    "plumber": dict(
        trade_label="plumbing", trade_article="a plumbing", description="Residential and light-commercial plumbing.",
        service_types=["leak repair", "drain cleaning", "water heater", "toilet or faucet repair", "pipe repair", "other plumbing"],
        emergency=dict(
            keywords=["burst pipe", "gas smell", "sewage backup", "flooding", "no water at all", "water heater leaking badly"],
            safety_script="If you smell gas, leave the building now and call 911 or the gas company emergency line from outside. If water is flooding, shut off the main valve if you can do it safely."),
        faqs=[("Do you handle emergencies?", "Yes. I can connect you to the on-call team right away."),
              ("Can I get an exact price on the phone?", "The team gives a quote after they have seen the job, so I cannot give one on the call."),
              ("What areas do you serve?", "I can check your ZIP code to confirm that we cover your area."),
              ("Do you work on water heaters?", "Yes, repairs and replacements. I can take the details and book a visit.")],
        qualifying_questions=["What is the problem, and where in the home is it?", "Is water still running or leaking right now?",
                              "Is this a house, apartment, or business?", "Have you shut off the water to that area?"],
        hours=WEEK_SAT),
    "hvac": dict(
        trade_label="HVAC (heating and cooling)", trade_article="an HVAC", description="Heating, cooling and ventilation service.",
        service_types=["AC repair", "furnace or heat repair", "tune-up or maintenance", "new system estimate", "thermostat or airflow issue", "other HVAC"],
        emergency=dict(
            keywords=["gas smell", "carbon monoxide alarm", "no heat when it is under 40 degrees",
                      "no cooling for an elderly person or baby when it is over 95 degrees", "burning smell from the unit", "smoke from the unit"],
            safety_script="If you smell gas or your carbon monoxide alarm is sounding, leave the building now and call 911 from outside."),
        faqs=[("Do you offer emergency service?", "Yes. For no heat in freezing weather, no cooling in dangerous heat, or any gas or carbon monoxide concern, I can connect you to the on-call team."),
              ("Can you tell me what the repair will cost?", "A technician gives a quote after diagnosing the system, so I cannot give one on the call."),
              ("Do you do maintenance plans?", "Yes. I can take your details and have the team follow up."),
              ("Do you install new systems?", "Yes. I can book an in-home estimate visit.")],
        qualifying_questions=["Is it the heating, the cooling, or something else?", "What is the system doing, or not doing?",
                              "Is anyone in the home elderly, very young, or medically fragile?", "Roughly how old is the system, if you know?"],
        hours=WEEK_SAT),
    "electrician": dict(
        trade_label="electrical", trade_article="an electrical", description="Residential and light-commercial electrical work.",
        service_types=["outlet or switch repair", "panel or breaker issue", "lighting install", "EV charger install", "wiring inspection", "other electrical"],
        emergency=dict(
            keywords=["sparks", "burning smell", "smoke from an outlet or panel", "exposed live wires", "downed power line", "water in the electrical panel"],
            safety_script="If you see smoke or fire, leave the building and call 911 from outside. Stay away from downed lines and exposed wires."),
        faqs=[("Do you take emergency calls?", "Yes. For sparks, burning smells, or exposed wires I can connect you to the on-call team right away."),
              ("Can you quote over the phone?", "The team quotes after they have seen the work, so I cannot give a price on the call."),
              ("Do you install EV chargers?", "Yes. I can take your details and book a site visit."),
              ("Are you licensed and insured?", "I can have someone from the team confirm license and insurance details with you.")],
        qualifying_questions=["What is happening with the electrical, and where?", "Do you smell burning or see scorch marks?",
                              "Is a breaker tripping repeatedly?", "Is this a home or a business?"],
        hours=WEEK_STD),
    "dental": dict(
        trade_label="dental", trade_article="a dental", description="General dental practice front desk.",
        service_types=["new patient exam", "cleaning", "toothache or pain visit", "filling or crown", "whitening or cosmetic consult", "other dental"],
        emergency=dict(
            keywords=["severe tooth pain", "knocked-out tooth", "facial swelling", "uncontrolled bleeding", "broken jaw", "swelling that affects breathing or swallowing"],
            safety_script="If swelling affects breathing or swallowing, or bleeding will not stop, please call 911 now."),
        faqs=[("Are you accepting new patients?", "I can take your details and book a new patient visit."),
              ("Do you take my insurance?", "I can note your insurance provider and the office will confirm coverage."),
              ("Can you tell me what is wrong with my tooth?", "I am not able to give dental advice, but I can book you with the dentist or connect you to the team."),
              ("Do you see emergencies?", "Yes. Describe what is happening and I will connect you to the team.")],
        qualifying_questions=["Are you a new or existing patient?", "What is the reason for your visit?", "Are you in pain right now?",
                              "Which days and times usually work for you?"],
        hours=WEEK_DENT),
    "cleaning": dict(
        trade_label="cleaning", trade_article="a cleaning", description="Home and office cleaning services.",
        service_types=["regular house cleaning", "deep clean", "move-in or move-out clean", "office cleaning", "post-construction clean", "other cleaning"],
        emergency=dict(
            keywords=["active flooding", "sewage backup", "fire or smoke damage cleanup", "biohazard", "water damage cleanup"],
            safety_script="If anyone is in danger, please call 911 first. Stay out of areas with sewage or standing water."),
        faqs=[("Do you bring your own supplies?", "I can note your preferences and the team will confirm what is provided."),
              ("How much will a clean cost?", "The team prepares a quote based on the size and condition of the space, so I cannot give one on the call."),
              ("Do you offer recurring service?", "Yes. I can record whether you want weekly, biweekly, monthly, or one-time."),
              ("Do you clean offices?", "Yes. I can take the details and set up a walkthrough.")],
        qualifying_questions=["Is this a home or an office?", "Roughly how many bedrooms and bathrooms, or how large is the space?",
                              "Is this a one-time or recurring clean?", "Any pets or special instructions?"],
        hours=WEEK_SAT),
    "roofer": dict(
        trade_label="roofing", trade_article="a roofing", description="Roof repair, replacement and storm damage.",
        service_types=["roof leak repair", "roof replacement estimate", "storm damage", "gutter work", "roof inspection", "other roofing"],
        emergency=dict(
            keywords=["active roof leak", "storm damage", "tree through the roof", "ceiling collapse", "water coming through the ceiling"],
            safety_script="If part of the ceiling is sagging or has collapsed, move everyone out of that room. If anyone is in danger, call 911."),
        faqs=[("Do you do emergency tarping?", "I can connect you to the on-call team about emergency leak and storm damage calls."),
              ("Can you give me a price for a new roof?", "The team prices a roof after an inspection, so I cannot give one on the call."),
              ("Do you work with insurance claims?", "I can note that it is an insurance claim and the team will explain their process."),
              ("Do you inspect roofs?", "Yes. I can book an inspection visit.")],
        qualifying_questions=["Is the roof leaking right now?", "Is the damage from a recent storm?",
                              "What type of roof is it, if you know?", "Is this a home or a commercial building?"],
        hours=WEEK_SAT),
}

out = Path(__file__).resolve().parent.parent / "presets"
out.mkdir(exist_ok=True)
for name, p in P.items():
    doc = {"preset": name, "trade": name, "trade_label": p["trade_label"], "trade_article": p["trade_article"],
           "description": p["description"], "service_types": p["service_types"], "emergency": p["emergency"],
           "faqs": [{"q": q, "a": a} for q, a in p["faqs"]], "qualifying_questions": p["qualifying_questions"],
           "hours": {"weekly": p["hours"]}}
    (out / f"{name}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("wrote", len(P))
