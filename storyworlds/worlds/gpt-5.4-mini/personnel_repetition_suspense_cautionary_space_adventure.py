#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/personnel_repetition_suspense_cautionary_space_adventure.py
===========================================================================================

A standalone storyworld for a small space-adventure tale about personnel on a
tiny ship, a repeated warning beat, a suspenseful choice, and a cautious fix.

Premise:
- A young crew member wants to press deeper into a silent station corridor.
- Ship personnel repeat a caution because the corridor is unstable.
- A suspense beat escalates when a hatch begins to cycle on its own.
- A careful adult pauses the mission, uses a safer tool, and the crew learns
  to follow the repeated safety rule.

The world is intentionally small: one ship, one corridor, one risky hatch, one
cautious rescue tool, and a calm ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_RISE = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    scene: str
    ship: str
    corridor: str
    sound: str
    view: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Risk:
    id: str
    label: str
    threat: str
    warning: str
    repeat_line: str
    what_if: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "station": Setting(
        "station",
        "a silent research station",
        "the little ship",
        "the long corridor",
        "a soft hum from the walls",
        "tiny lights blinking like sleepy stars",
    ),
    "drift": Setting(
        "drift",
        "a drifting cargo pod",
        "the little ship",
        "the narrow passage",
        "a hush and a click from the hull",
        "faint numbers glowing on metal panels",
    ),
    "moonbase": Setting(
        "moonbase",
        "a moon base with one bright bay",
        "the little ship",
        "the access corridor",
        "dusty floors and a low radio buzz",
        "a round window showing the moon dust outside",
    ),
}

RISKS = {
    "hatch": Risk(
        "hatch",
        "the hatch",
        "a hatch that can seal shut",
        "Do not touch the hatch panel yet.",
        "Do not open and close that hatch again.",
        "What if the hatch jams while we are inside?",
        {"hatch", "door", "space"},
    ),
    "airlock": Risk(
        "airlock",
        "the airlock",
        "an airlock that must not cycle without checks",
        "Do not press the airlock button yet.",
        "Do not cycle that airlock again.",
        "What if the airlock opens the wrong way?",
        {"airlock", "space"},
    ),
    "panel": Risk(
        "panel",
        "the panel",
        "a control panel with a warning light",
        "Do not poke the panel yet.",
        "Do not tap that panel again.",
        "What if the panel wakes something up?",
        {"panel", "warning"},
    ),
}

TOOLS = {
    "scanner": Tool(
        "scanner",
        "scanner",
        "a small scanner",
        "scan the hatch and confirm it is stuck",
        safe=True,
        tags={"scanner"},
    ),
    "lamp": Tool(
        "lamp",
        "lamp",
        "a portable lamp",
        "shine light into the corridor",
        safe=True,
        tags={"lamp"},
    ),
    "magnet": Tool(
        "magnet",
        "magnet",
        "a soft clamp magnet",
        "hold the broken latch still",
        safe=True,
        tags={"magnet"},
    ),
}

RESPONSES = {
    "scan": Response(
        "scan",
        3,
        3,
        "used the scanner and found the hatch was jammed before anything worse happened",
        "tried the scanner, but the hatch was already locked tight and the warning grew louder",
        "used the scanner to check the hatch",
        {"scanner"},
    ),
    "clamp": Response(
        "clamp",
        3,
        4,
        "slipped a soft clamp magnet over the latch and held it still until the alarm stopped",
        "tried the clamp, but the hatch kept grinding and the alarm kept rising",
        "used a soft clamp magnet to hold the latch still",
        {"magnet"},
    ),
    "lamp": Response(
        "lamp",
        2,
        2,
        "shone the lamp into the seam and saw the loose wire that had been hiding",
        "shone the lamp around, but the problem was bigger than the light could solve",
        "shone a lamp into the seam",
        {"lamp"},
    ),
    "shout_for_help": Response(
        "shout_for_help",
        4,
        5,
        "called the rest of the personnel and kept everyone back until the hatch settled",
        "called for help, but the warning kept growing before the crew arrived",
        "called the rest of the personnel for help",
        {"help"},
    ),
    "push_button": Response(
        "push_button",
        0,
        1,
        "pushed the button again and made the alarm louder",
        "pushed the button and made the problem worse",
        "pushed the button again",
        {"unsafe"},
    ),
}

NAMES = ["Mara", "Jin", "Tali", "Oren", "Pia", "Niko", "Sera", "Rin"]
ADULT_ROLES = ["captain", "engineer", "pilot", "medic"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def risk_is_real(risk: Risk) -> bool:
    return True


def is_reasonable_combo(setting: Setting, risk: Risk, tool: Tool, response: Response) -> bool:
    return risk_is_real(risk) and tool.safe and response.sense >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid in RISKS:
            for tid in TOOLS:
                for resp in sensible_responses():
                    combos.append((sid, rid, tid, resp.id))
    return combos


def severity(risk: Risk, delay: int) -> int:
    return 2 + delay


def contained(response: Response, risk: Risk, delay: int) -> bool:
    return response.power >= severity(risk, delay)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    return out


def predict(world: World, risk_id: str) -> dict:
    sim = world.copy()
    risk = sim.get("risk")
    risk.meters["alarm"] += 1
    return {"alarm": risk.meters["alarm"], "suspense": sim.get("ship").memes["suspense"]}


def tell(setting: Setting, risk: Risk, tool: Tool, response: Response,
         hero_name: str, hero_gender: str, ally_name: str, ally_gender: str,
         adult_role: str, delay: int = 0) -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="child"))
    ally = world.add(Entity(ally_name, kind="character", type=ally_gender, role="crew"))
    adult = world.add(Entity("Personnel", kind="character", type=adult_role, role="adult", label="the personnel"))
    ship = world.add(Entity("ship", type="ship", label="the ship"))
    hatch = world.add(Entity("risk", type="thing", label=risk.label))
    world.facts["delay"] = delay
    hero.memes["curiosity"] += 1
    ally.memes["caution"] += 1

    world.say(
        f"On the {setting.scene}, {hero_name} and {ally_name} rode the little ship through "
        f"{setting.view}. {setting.ship} moved forward with {setting.sound}."
    )
    world.say(
        f"{hero_name} wanted to get closer to {risk.label}, but {ally_name} kept pointing at the sign: "
        f'"{risk.warning}"'
    )

    world.para()
    world.say(
        f"Again and again, {ally_name} said, \"{risk.repeat_line}\" "
        f"Again and again, the warning made the corridor feel smaller."
    )
    hero.memes["pressure"] += 1

    world.para()
    world.say(
        f"Then the hatch began to twitch on its own. A tiny click came from the seam, then another click."
    )
    world.get("ship").memes["suspense"] += 1
    world.say(
        f'"What if {risk.what_if.lower()}" {ally_name} whispered, and the {setting.corridor} went very still.'
    )

    world.para()
    world.say(
        f"{hero_name} reached for {tool.phrase}, but {ally_name} shook {ally_name.lower()} head. "
        f'"No. We call {adult.label_word if adult.label_word else adult_role} first."'
    )

    if delay > 0:
        world.say(f"The delay made the humming stronger, and the suspense stretched longer.")

    if response.id == "push_button":
        world.say(
            f"{hero_name} ignored the caution and {response.text}. The light turned red and the alarm grew sharp."
        )
    elif response.id == "shout_for_help":
        world.say(
            f"{adult.label_word.capitalize()} came fast, and {response.text}. Everyone backed away from the seam."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} came fast, and {response.text}. The repeated warning had been right."
        )

    world.para()
    if contained(response, risk, delay):
        adult.memes["approval"] += 1
        hero.memes["relief"] += 1
        ally.memes["relief"] += 1
        world.say(
            f"At last, the hatch stopped shaking. {hero_name} and {ally_name} stood beside {adult.pronoun('object')}, "
            f"and the little ship felt calm again."
        )
        world.say(
            f"To finish the mission, they used the scanner one careful time and then left the corridor cleaner than they found it."
        )
    else:
        hero.memes["fear"] += 1
        ally.memes["fear"] += 1
        world.say(
            f"The warning kept climbing, so {adult.label_word} ordered everyone back. They shut the door and waited."
        )
        world.say(
            f"When the hatch finally settled, the crew promised to listen sooner next time."
        )

    world.facts.update(
        hero=hero,
        ally=ally,
        adult=adult,
        setting=setting,
        risk=risk,
        tool=tool,
        response=response,
        outcome="contained" if contained(response, risk, delay) else "warned",
        ship=ship,
        hatch=hatch,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure for a 3-to-5-year-old that repeats the warning "{f["risk"].warning}" and includes the word "personnel".',
        f"Tell a cautious story where {f['hero'].id} and {f['ally'].id} explore {f['setting'].scene} and the personnel must step in.",
        f'Write a suspenseful story about a hatch, a warning sign, and safe personnel who solve the problem without being reckless.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    adult = f["adult"]
    risk = f["risk"]
    tool = f["tool"]
    response = f["response"]
    answers = [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {hero.id}, {ally.id}, and the personnel who helped keep the ship safe. The adventure stays small, but the choice matters a lot.",
        ),
        QAItem(
            question="What warning did the crew repeat?",
            answer=f'They repeated, "{risk.repeat_line}" over and over. The repetition made the danger feel real, because the hatch was acting strange and the crew needed to be careful.',
        ),
        QAItem(
            question="What did the child want to do?",
            answer=f"{hero.id} wanted to move closer to {risk.label}. That choice felt exciting at first, but it also made the corridor more tense.",
        ),
    ]
    if f["outcome"] == "contained":
        answers.append(
            QAItem(
                question="How did the personnel solve the problem?",
                answer=f"{adult.label_word.capitalize()} came in, and {response.qa_text}. The safe tool and the calm help stopped the suspense before anyone got hurt.",
            )
        )
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="It ended with the hatch quiet and the crew standing together in a calm corridor. The personnel proved that listening and pausing can save a mission.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="What happened when the warning was ignored?",
                answer=f"The alarm grew louder and the personnel had to order everyone back. The crew waited, and the hatch only settled after the danger had been noticed.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["risk"].tags) | set(f["tool"].tags)
    out: list[QAItem] = []
    if "space" in tags:
        out.append(QAItem(
            question="What is a hatch on a spaceship?",
            answer="A hatch is a door or panel that can open and close in a ship or station. In space stories, hatches matter because they can keep air and people in safe places.",
        ))
    if "scanner" in tags:
        out.append(QAItem(
            question="What does a scanner do?",
            answer="A scanner checks what is there without poking or breaking it. That makes it a careful tool for strange spaces.",
        ))
    if "lamp" in tags:
        out.append(QAItem(
            question="Why use a lamp in a dark corridor?",
            answer="A lamp gives light so people can see seams, buttons, and signs. Light helps a crew stay cautious instead of guessing.",
        ))
    if "magnet" in tags:
        out.append(QAItem(
            question="What can a soft magnet help with?",
            answer="A soft magnet can hold metal pieces still for a moment. That is useful when a latch is loose and needs gentle help.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)




@dataclass
class StoryParams:
    setting: str
    risk: str
    tool: str
    response: str
    hero: str
    hero_gender: str
    ally: str
    ally_gender: str
    adult_role: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    StoryParams("station", "hatch", "scanner", "scan", "Mara", "girl", "Jin", "boy", "captain", 0),
    StoryParams("drift", "airlock", "magnet", "clamp", "Tali", "girl", "Oren", "boy", "engineer", 1),
    StoryParams("moonbase", "panel", "lamp", "shout_for_help", "Pia", "girl", "Niko", "boy", "medic", 0),
]



def explain_rejection(risk: Risk, tool: Tool, response: Response) -> str:
    if response.sense < 2:
        return f"(No story: '{response.id}' is too unsafe for a cautionary space adventure.)"
    return f"(No story: this space setup is not reasonable with {risk.label} and {tool.label}.)"


def valid_story_params(params: StoryParams) -> bool:
    return params.risk in RISKS and params.tool in TOOLS and params.response in RESPONSES


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), min_sense(M), S >= M.
valid(S, R, T, P) :- setting(S), risk(R), tool(T), response(P), sensible(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for pid, r in RESPONSES.items():
        lines.append(asp.fact("response", pid))
        lines.append(asp.fact("sense", pid, r.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in clingo:", sorted(a - b))
        print("  only in python:", sorted(b - a))

    # smoke test: ordinary story generation should work
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary space adventure world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--ally")
    ap.add_argument("--adult-role", choices=ADULT_ROLES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_rejection(RISKS[args.risk or "hatch"], TOOLS[args.tool or "scanner"], RESPONSES[args.response]))
    setting = args.setting or rng.choice(list(SETTINGS))
    risk = args.risk or rng.choice(list(RISKS))
    tool = args.tool or rng.choice(list(TOOLS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    if not is_reasonable_combo(SETTINGS[setting], RISKS[risk], TOOLS[tool], RESPONSES[response]):
        raise StoryError(explain_rejection(RISKS[risk], TOOLS[tool], RESPONSES[response]))
    hero = args.hero or rng.choice(NAMES)
    ally = args.ally or rng.choice([n for n in NAMES if n != hero])
    adult_role = args.adult_role or rng.choice(ADULT_ROLES)
    return StoryParams(setting, risk, tool, response, hero, "girl", ally, "boy", adult_role, args.delay or 0)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        RISKS[params.risk],
        TOOLS[params.tool],
        RESPONSES[params.response],
        params.hero,
        params.hero_gender,
        params.ally,
        params.ally_gender,
        params.adult_role,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
