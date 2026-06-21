#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T222722Z_seed1055341754_n10/gunner_shopping_mall_humor_space_adventure.py
======================================================================================================

A standalone storyworld for a tiny Space-Adventure-style shopping mall tale:
a child named Gunner goes to the mall on a goofy errand, the imaginary mission
gets a little wild, a helpful grown-up or friend redirects it, and the ending
proves the mall trip changed something concrete.

The world is intentionally small and constraint-checked:
- typed entities with physical meters and emotional memes
- a reasonableness gate over shopping-mall mission setups
- a forward causal engine
- a Python gate plus inline ASP twin
- story prompts, story-grounded Q&A, and world-knowledge Q&A
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    title1: str
    title2: str
    mission: str
    dark_spot: str
    ending_image: str


@dataclass
class Mission:
    id: str
    label: str
    phrase: str
    where: str
    funny_mistake: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    flammable: bool = False
    spillable: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helpful: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    text: str
    fail: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("mall").meters["chaos"] >= THRESHOLD and ("alarm", "chaos") not in world.fired:
        world.fired.add(("alarm", "chaos"))
        world.get("parent").memes["concern"] += 1
        out.append("__alarm__")
    return out


def _r_sparkle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["sparkle"] >= THRESHOLD and ("sparkle", ent.id) not in world.fired:
            world.fired.add(("sparkle", ent.id))
            world.get("mall").meters["wonder"] += 1
            out.append("__sparkle__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("sparkle", _r_sparkle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for t in produced:
            world.say(t)
    return produced


def valid_mission(hazard: Hazard, mission: Mission) -> bool:
    return hazard.id in mission.tags or mission.id in {"toy_rocket", "echo_map"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def mission_risk(mission: Mission, hazard: Hazard) -> bool:
    if mission.id == "toy_rocket":
        return hazard.fragile or hazard.spillable
    if mission.id == "echo_map":
        return hazard.spillable or hazard.fragile
    return False


def response_ok(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= (2 + delay if hazard.spillable else 1 + delay)


def reasonableness_gate() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for m in MISSIONS:
            for h in HAZARDS:
                if valid_mission(h, m) and mission_risk(m, h):
                    combos.append((theme, m, h))
    return combos


def tell(theme: Theme, mission: Mission, hazard: Hazard, tool: Tool, response: Response,
         gunner_name: str = "Gunner", gunner_gender: str = "boy",
         helper_name: str = "Mira", helper_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    gunner = world.add(Entity(id=gunner_name, kind="character", type=gunner_gender, role="hero",
                              traits=["silly", "brave"], attrs={"mission": mission.id}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              traits=["clever", "calm"], attrs={"mission": mission.id}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent",
                              label="the parent", traits=["patient"]))
    mall = world.add(Entity(id="mall", kind="place", type="place", label="the mall"))
    kiosk = world.add(Entity(id="kiosk", kind="thing", type="thing", label=hazard.label,
                             attrs={"hazard": hazard.id}))

    gunner.memes["curiosity"] = 1.0
    helper.memes["wit"] = 1.0
    parent.memes["concern"] = 0.0
    mall.meters["wonder"] = 0.0
    mall.meters["chaos"] = 0.0
    kiosk.meters["risk"] = 0.0
    world.facts["delay"] = delay

    world.say(
        f"At {theme.scene}, {gunner_name} and {helper_name} turned a shopping trip into "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.title1} {gunner_name}!" {gunner_name} said. '
        f'"Let\'s find {theme.mission} before the escalator steals our socks!"'
    )
    world.say(
        f"But near {theme.dark_spot}, {hazard.phrase} made the mission look funny in a way that '
        f"could cause trouble."
    )

    world.para()
    gunner.memes["guts"] += 1
    helper.memes["alarm"] += 1
    world.say(
        f"{gunner_name} wanted to use {mission.phrase}, and the idea felt like a space launch in a snack aisle."
    )
    world.say(
        f'{helper_name} blinked. "We should not poke {hazard.label}. {parent.label_word.capitalize()} said so, and it could get messy."'
    )

    if mission_risk(mission, hazard):
        world.say(f"{gunner_name} grinned anyway and tried to {mission.funny_mistake}.")
        if mission.id == "toy_rocket":
            mall.meters["chaos"] += 1
            kiosk.meters["sparkle"] += 1
        else:
            mall.meters["chaos"] += 1
            kiosk.meters["spill"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(f'"{gunner_name}! {hazard.label.capitalize()}!" {helper_name} yelped.')
        world.say(f'"{parent.label_word.upper()}!"')

        if response_ok(response, hazard, delay):
            kiosk.meters["sparkle"] = 0.0
            mall.meters["chaos"] = 0.0
            world.say(
                f"{parent.label_word.capitalize()} came running and {response.text.format(target=hazard.label)}."
            )
            world.say(
                f"The goofy trouble fizzled out, and the mall stopped looking like a moon base with hiccups."
            )
            world.para()
            world.say(
                f"Then {parent.label_word.capitalize()} pointed to {tool.phrase} and smiled. "
                f'"Now we do the safe kind of mission," {parent.pronoun()} said, and {theme.ending_image}.'
            )
            gunner.memes["relief"] += 1
            helper.memes["joy"] += 1
            world.facts["outcome"] = "contained"
        else:
            world.say(
                f"{parent.label_word.capitalize()} came running and {response.fail.format(target=hazard.label)}."
            )
            world.say(
                "The whole little mission turned into a noisy emergency, and the shiny aisle became a very dramatic mess."
            )
            world.para()
            world.say(
                f"Still, everybody got out safely, and later {parent.label_word.capitalize()} used {tool.phrase} to start a much safer space game."
            )
            world.facts["outcome"] = "failed"
    else:
        world.say(
            f"{helper_name} talked {gunner_name} into using {tool.phrase} instead, and the prankish mission stayed harmless."
        )
        world.para()
        world.say(
            f"They marched on with the safe gadget, and {theme.ending_image}."
        )
        world.facts["outcome"] = "averted"

    world.facts.update(
        gunner=gunner, helper=helper, parent=parent, mall=mall, kiosk=kiosk,
        theme=theme, mission=mission, hazard=hazard, tool=tool, response=response,
    )
    return world


def ask_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous space-adventure story in a shopping mall that includes the word "gunner".',
        f"Tell a funny shopping-mall mission story where {f['gunner'].id} wants to use {f['mission'].phrase} but learns a safer way.",
        f'Write a child-facing story with a spaceship-feeling shopping mall, a silly mistake, and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gunner = f["gunner"]
    helper = f["helper"]
    parent = f["parent"]
    theme = f["theme"]
    mission = f["mission"]
    hazard = f["hazard"]
    tool = f["tool"]
    resp = f["response"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It's about {gunner.id} and {helper.id} on a space-style shopping mall adventure. {parent.label_word.capitalize()} helps keep the trip safe too.",
        ),
        QAItem(
            question=f"What kind of mission were {gunner.id} and {helper.id} pretending to do?",
            answer=f"They were pretending the mall was {theme.scene} and searching for {theme.mission}. That gave the shopping trip a silly space-adventure feeling.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {gunner.id} about {hazard.label}?",
            answer=f"Because {hazard.label} could turn the mission messy or risky. {helper.id} could see that using {mission.phrase} near it would not stay funny for long.",
        ),
        QAItem(
            question=f"What helped the story end safely?",
            answer=f"{parent.label_word.capitalize()} used {resp.text}." if f["outcome"] == "contained" else f"{helper.id} switched the plan to {tool.phrase}, which kept the adventure safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The mall went from noisy mission chaos to a calmer, brighter trip. By the end, {theme.ending_image} and the group had a safer game to enjoy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["mission"].tags) | set(f["hazard"].tags) | set(f["tool"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


THEMES = {
    "mallbase": Theme(
        id="mallbase",
        scene="the shopping mall",
        rig="the food court was their command center, the escalator was the launch ramp, and a shiny coin became the moon",
        title1="Captain",
        title2="Pilot",
        mission="the glowing space gumdrop",
        dark_spot="the shadowy corner by the fountain",
        ending_image="the food court lights blinked like friendly stars",
    ),
    "orbit": Theme(
        id="orbit",
        scene="the shopping mall",
        rig="the arcade was their starship bridge, the elevator doors were airlocks, and a pretzel stood in for a looping comet",
        title1="Commander",
        title2="Navigator",
        mission="the lost silver sticker",
        dark_spot="the dark aisle by the bookstore",
        ending_image="the elevator dinged like a tiny space bell",
    ),
}

MISSIONS = {
    "toy_rocket": Mission(
        id="toy_rocket",
        label="toy rocket",
        phrase="a toy rocket blaster",
        where="in the kiosk",
        funny_mistake="blast off with the rocket indoors",
        tags={"rocket", "space", "toy"},
    ),
    "echo_map": Mission(
        id="echo_map",
        label="echo map",
        phrase="an echo map scanner",
        where="by the fountain",
        funny_mistake="scan the whole mall like a moon cave",
        tags={"map", "space", "toy"},
    ),
}

HAZARDS = {
    "popcorn_cart": Hazard(
        id="popcorn_cart",
        label="the popcorn cart",
        phrase="a popcorn cart rattled and popped like a tiny volcano",
        spillable=True,
        fragile=False,
        tags={"food", "cart"},
    ),
    "glass_display": Hazard(
        id="glass_display",
        label="the glass display",
        phrase="the glass display shone too close and looked very breakable",
        spillable=False,
        fragile=True,
        tags={"glass", "display"},
    ),
    "fountain": Hazard(
        id="fountain",
        label="the fountain",
        phrase="the fountain splashed in every direction",
        spillable=True,
        fragile=False,
        tags={"water", "fountain"},
    ),
}

TOOLS = {
    "walkie": Tool(
        id="walkie",
        label="walkie-talkie",
        phrase="the walkie-talkie",
        helpful="keeps the mission coordinated",
        power=3,
        sense=3,
        tags={"radio", "space"},
    ),
    "sticker": Tool(
        id="sticker",
        label="sticker badge",
        phrase="the sticker badge",
        helpful="makes the mission feel official",
        power=2,
        sense=2,
        tags={"sticker", "space"},
    ),
    "snack": Tool(
        id="snack",
        label="snack bag",
        phrase="the snack bag",
        helpful="keeps everybody cheerful",
        power=2,
        sense=3,
        tags={"food"},
    ),
}

RESPONSES = {
    "cover_cart": Response(
        id="cover_cart",
        text="covered the popcorn cart with a clean cloth and carried the tray away",
        fail="tried to cover the popcorn cart, but the pops kept bouncing everywhere",
        power=3,
        sense=3,
    ),
    "close_door": Response(
        id="close_door",
        text="shut the glass display case door and asked everyone to take a step back",
        fail="closed the case door too late, after the clatter already started",
        power=2,
        sense=2,
    ),
    "shout_help": Response(
        id="shout_help",
        text="called mall security and got help fast",
        fail="called for help, but the mess was already too wild",
        power=4,
        sense=3,
        tags={"help"},
    ),
    "tiny_fan": Response(
        id="tiny_fan",
        text="waved a tiny fan at the problem and hoped for the best",
        fail="waved a tiny fan, which mostly made everybody laugh and not much else",
        power=1,
        sense=1,
    ),
}

GUNNER_NAMES = ["Gunner", "Milo", "Zed", "Nova", "Pip"]
HELPER_NAMES = ["Mira", "Tess", "Ravi", "June", "Bea"]


@dataclass
class StoryParams:
    theme: str
    mission: str
    hazard: str
    tool: str
    response: str
    gunner_name: str = "Gunner"
    gunner_gender: str = "boy"
    helper_name: str = "Mira"
    helper_gender: str = "girl"
    parent: str = "mother"
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(theme="mallbase", mission="toy_rocket", hazard="popcorn_cart", tool="walkie", response="shout_help", gunner_name="Gunner", gunner_gender="boy", helper_name="Mira", helper_gender="girl", parent="mother", delay=0),
    StoryParams(theme="orbit", mission="echo_map", hazard="glass_display", tool="sticker", response="close_door", gunner_name="Nova", gunner_gender="girl", helper_name="Ravi", helper_gender="boy", parent="father", delay=0),
    StoryParams(theme="mallbase", mission="toy_rocket", hazard="fountain", tool="snack", response="cover_cart", gunner_name="Gunner", gunner_gender="boy", helper_name="Bea", helper_gender="girl", parent="mother", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return reasonableness_gate()


def explain_rejection(mission: Mission, hazard: Hazard) -> str:
    return f"(No story: {mission.label} does not make a reasonable match for {hazard.label} in this mall adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous shopping-mall space-adventure storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.mission is None or c[1] == args.mission)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, mission, hazard = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    parent = args.parent or rng.choice(["mother", "father"])
    gunner_name = "gunner"
    if args.theme == "orbit":
        gunner_name = rng.choice(GUNNER_NAMES)
    helper_name = rng.choice(HELPER_NAMES)
    return StoryParams(theme=theme, mission=mission, hazard=hazard, tool=tool, response=response,
                       gunner_name=gunner_name, helper_name=helper_name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.mission not in MISSIONS or params.hazard not in HAZARDS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(
        THEMES[params.theme], MISSIONS[params.mission], HAZARDS[params.hazard],
        TOOLS[params.tool], RESPONSES[params.response],
        gunner_name=params.gunner_name, gunner_gender=params.gunner_gender,
        helper_name=params.helper_name, helper_gender=params.helper_gender,
        parent_type=params.parent, delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=ask_prompts(world),
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


ASP_RULES = r"""
valid(T, M, H) :- theme(T), mission(M), hazard(H), compatible(M, H).
contained(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for tag in m.tags:
            lines.append(asp.fact("compatible", mid, "popcorn_cart" if tag == "cart" else "glass_display" if tag == "glass" else "fountain"))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show contained/1."))
    return sorted(r for (r,) in asp.atoms(model, "contained"))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) == set(valid_combos()):
            print("OK: ASP gate matches Python valid_combos().")
        else:
            print("MISMATCH: ASP and Python valid_combos() differ.")
            rc = 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        traceback.print_exc()
        rc = 1
    return rc


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a humorous space-adventure story in a shopping mall that includes the word "gunner".',
        f"Tell a funny mall mission story where {f['gunner'].id} wants to use {f['mission'].phrase} but learns a safer way.",
        f"Write a child-facing story with a shopping-mall spaceship feeling and a silly mistake that gets fixed.",
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show contained/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
