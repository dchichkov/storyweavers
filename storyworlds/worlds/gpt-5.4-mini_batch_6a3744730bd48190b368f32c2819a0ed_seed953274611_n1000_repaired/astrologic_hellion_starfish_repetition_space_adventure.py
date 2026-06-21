#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/astrologic_hellion_starfish_repetition_space_adventure.py
=========================================================================================

A small space-adventure storyworld about an astrologic map, a little hellion
pilot, and a rescued starfish. The world is built around repetition: the pilot
tries the same boastful plan twice, the crew repeats a warning twice, and the
solution also arrives with a repeated, safer rhythm.

The domain is intentionally tiny:
- a child-like crew in a small ship
- a risky detour toward a glittering asteroid lane
- repeated warnings from a careful helper
- a sensible correction that keeps the starfish safe

The text includes the seed words:
- astrologic
- hellion
- starfish

The stories are state-driven, not frozen templates: the ship, the crew, the
starfish, and the warning all accumulate meters/memes that drive what gets said.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class ShipPart:
    id: str
    label: str
    kind: str
    risky: bool = False
    safe_fix: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mission:
    id: str
    scene: str
    repetition_line: str
    danger_line: str
    resolution_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    mission: str
    route: str
    hazard: str
    fix: str
    pilot: str
    pilot_type: str
    helper: str
    helper_type: str
    captain: str
    captain_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.parts: dict[str, ShipPart] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_part(self, part: ShipPart) -> ShipPart:
        self.parts[part.id] = part
        return part

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.parts = copy.deepcopy(self.parts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    pilot = world.get("pilot")
    if pilot.memes["brag"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pilot.memes["restless"] += 1
    world.get("starfish").meters["shaken"] += 1
    out.append("__repeat__")
    return out


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    if world.parts["cargo"].meters["risk"] < THRESHOLD:
        return out
    sig = ("danger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["alarm"] += 1
    world.get("pilot").memes["worry"] += 1
    out.append("The control lights blinked harder.")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("danger", _r_danger)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


MISSIONS = {
    "astro-chart": Mission(
        id="astro-chart",
        scene="a small scout ship crossing a silver asteroid lane",
        repetition_line="Again and again, the map showed the same bright route and the same red warning ring.",
        danger_line="But the red ring meant the ship would scrape the rocks if it kept going straight.",
        resolution_line="So the crew repeated the safe check, repeated the safe turn, and listened to the calm lane instead.",
        ending_image="the ship glided past the rocks while a starfish floated safely in a warm tank",
        tags={"astrologic", "space", "repeat"},
    ),
    "moon-loop": Mission(
        id="moon-loop",
        scene="a tiny moon hopper circling a dusty crater field",
        repetition_line="Round and round, the console chirped the same astrologic note, the same note, the same note.",
        danger_line="Each chirp warned that the cargo cradle was loose and the starfish could slide loose in a jolt.",
        resolution_line="So the crew repeated the straps, repeated the latch, and made the cradle snug again.",
        ending_image="a tidy cradle, a quiet engine, and one starfish sleeping under a clear dome",
        tags={"astrologic", "space", "repeat"},
    ),
    "comet-bend": Mission(
        id="comet-bend",
        scene="a bright comet runner with blue windows and a humming tail",
        repetition_line="The same blinking arrow flashed twice, and the same blinking arrow flashed twice again.",
        danger_line="The arrow warned that the cargo bay was open to the cold glitter outside.",
        resolution_line="So the captain called for the latch, the pilot called for the latch, and the bay clicked shut.",
        ending_image="the comet runner coasting gently with the starfish tucked under a safe blue lid",
        tags={"astrologic", "space", "repeat"},
    ),
}

ROUTES = {
    "lane": {"id": "lane", "label": "the asteroid lane", "risk": "scraping the rocks"},
    "loop": {"id": "loop", "label": "the moon loop", "risk": "a hard jolt"},
    "comet": {"id": "comet", "label": "the comet bend", "risk": "cold wind in the bay"},
}

HAZARDS = {
    "scrape": {"id": "scrape", "label": "scraping rocks", "meter": "risk"},
    "jolt": {"id": "jolt", "label": "a loose cradle", "meter": "risk"},
    "open-bay": {"id": "open-bay", "label": "an open cargo bay", "meter": "risk"},
}

FIXES = {
    "turn": {"id": "turn", "label": "a safe turn", "verb": "turn the ship"},
    "strap": {"id": "strap", "label": "tight straps", "verb": "strap the cradle"},
    "latch": {"id": "latch", "label": "the bay latch", "verb": "close the bay"},
}

PILOT_NAMES = ["Nova", "Pip", "Mira", "Lio", "Tavi", "Zee"]
HELPER_NAMES = ["Kite", "Sol", "Ari", "June", "Moss", "Ray"]
CAPTAIN_NAMES = ["Captain Luna", "Captain Orion", "Captain Vega", "Captain Sora"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for mission in MISSIONS:
        for route in ROUTES:
            for hazard in HAZARDS:
                for fix in FIXES:
                    combos.append((mission, route, hazard, fix))
    return combos


def explain_combo(route: str, hazard: str) -> str:
    return f"(No story: the route {route} does not honestly match the hazard {hazard}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure storyworld with repetition.")
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--pilot")
    ap.add_argument("--helper")
    ap.add_argument("--captain")
    ap.add_argument("--pilot-type", choices=["girl", "boy"], dest="pilot_type")
    ap.add_argument("--helper-type", choices=["girl", "boy"], dest="helper_type")
    ap.add_argument("--captain-type", choices=["woman", "man"], dest="captain_type")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    mission = args.mission or rng.choice(list(MISSIONS))
    route = args.route or rng.choice(list(ROUTES))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    fix = args.fix or rng.choice(list(FIXES))
    if route == "lane" and hazard != "scrape":
        raise StoryError(explain_combo(route, hazard))
    if route == "loop" and hazard != "jolt":
        raise StoryError(explain_combo(route, hazard))
    if route == "comet" and hazard != "open-bay":
        raise StoryError(explain_combo(route, hazard))
    pilot_type = args.pilot_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    captain_type = args.captain_type or rng.choice(["woman", "man"])
    pilot = args.pilot or rng.choice(PILOT_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != pilot])
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    return StoryParams(mission=mission, route=route, hazard=hazard, fix=fix,
                       pilot=pilot, pilot_type=pilot_type,
                       helper=helper, helper_type=helper_type,
                       captain=captain, captain_type=captain_type)


def tell(params: StoryParams) -> World:
    world = World()
    mission = MISSIONS[params.mission]
    route = ROUTES[params.route]
    hazard = HAZARDS[params.hazard]
    fix = FIXES[params.fix]
    pilot = world.add(Entity(id="pilot", kind="character", type=params.pilot_type, label=params.pilot, role="pilot"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    captain = world.add(Entity(id="captain", kind="character", type=params.captain_type, label=params.captain, role="captain"))
    starfish = world.add(Entity(id="starfish", kind="thing", type="starfish", label="starfish", tags=["starfish"]))
    cargo = world.add_part(ShipPart(id="cargo", label="cargo cradle", kind="cargo"))
    pilot.memes["brag"] = 1.0
    world.say(f"{params.captain} guided a tiny ship through space, and {params.pilot} was a little hellion at the controls.")
    world.say(f"The mission felt astrologic, as if the stars were drawing the route by hand. {mission.repetition_line}")
    world.para()
    world.say(f"{params.pilot} kept saying the same thing twice: \"I can go faster, I can go faster.\"")
    world.say(f"{params.helper} shook {helper.pronoun('possessive')} head and pointed at the screen. \"No, no, look again.\"")
    if params.route == "lane":
        world.say(f"The scout ship was headed for {route['label']}. {mission.danger_line}")
    elif params.route == "loop":
        world.say(f"The moon hopper was headed for {route['label']}. {mission.danger_line}")
    else:
        world.say(f"The comet runner was headed for {route['label']}. {mission.danger_line}")
    cargo.meters["risk"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{params.helper} repeated the warning, then repeated it once more: \"Slow down. Slow down.\"")
    world.say(f"{params.captain} repeated the safe plan too: \"Use {fix['label']}. Use {fix['label']}.\"")
    world.get("starfish").memes["hope"] += 1
    world.say(f"{params.pilot} finally looked at the {params.hazard} sign and stopped the little hellion act.")
    world.say(f"{mission.resolution_line}")
    world.para()
    world.say(f"{params.captain} used {fix['label']} and the ship steadied at once.")
    world.say(f"The starfish stopped trembling and floated in a clear bowl of water beside the console.")
    world.say(f"{mission.ending_image[0].upper()}{mission.ending_image[1:]}.")
    world.facts.update(params=params, mission=mission, route=route, hazard=hazard, fix=fix,
                       pilot=pilot, helper=helper, captain=captain, starfish=starfish,
                       outcome="safe")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a space-adventure story that includes the words astrologic, hellion, and starfish.",
        f"Tell a repetitive little space story where {f['pilot'].label} acts like a hellion, but {f['helper'].label} keeps warning them twice.",
        f"Write a child-friendly spaceship story where an astrologic map points at danger and the crew repeats a safer plan instead.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mission = f["mission"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {f['pilot'].label}, {f['helper'].label}, and {f['captain'].label} aboard a small ship. The starfish is part of the rescue, so it matters to the ending too."
        ),
        QAItem(
            question="What made the story repetitive?",
            answer=f"The crew kept repeating the same warning and the same safer plan. That repetition matters because it helps the pilot stop the risky choice."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"At the start, the ship was headed toward danger, but by the end it was steady and safe. The starfish ended up floating calmly instead of being shaken by the risk."
        ),
        QAItem(
            question="Why did the helper keep warning the pilot?",
            answer=f"The helper saw that the route could hurt the ship or jolt the cargo cradle. Repeating the warning gave the pilot another chance to choose the safe move."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {mission.ending_image}. The ending image proves the danger was avoided and the starfish was safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does astrologic mean here?",
            answer="It means the stars, maps, and signs are being used to guide a space trip. In this story, it feels like a star-reading clue for where to go."
        ),
        QAItem(
            question="What is a hellion?",
            answer="A hellion is a wild, hard-to-control troublemaker. In a story for children, it usually means someone is acting too boldly and needs a calm warning."
        ),
        QAItem(
            question="What is a starfish?",
            answer="A starfish is a sea animal with arms shaped like a star. In this space story, it is used as a tiny rescue passenger to keep safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    for p in world.parts.values():
        lines.append(f"  {p.id}: meters={dict(p.meters)}")
    lines.append(f"  fired rules: {sorted(k[0] for k in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(route_lane, scrape).
risk(route_loop, jolt).
risk(route_comet, open_bay).
safe_fix(scrape, turn).
safe_fix(jolt, strap).
safe_fix(open_bay, latch).
repeat_triggers(brag) :- repeat_word.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", f"mission_{mid}"))
    for rid in ROUTES:
        lines.append(asp.fact("route", f"route_{rid}"))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", f"hazard_{hid}"))
    for fid in FIXES:
        lines.append(asp.fact("fix", f"fix_{fid}"))
    lines.append(asp.fact("seed_word", "astrologic"))
    lines.append(asp.fact("seed_word", "hellion"))
    lines.append(asp.fact("seed_word", "starfish"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_gate() -> int:
    import asp
    ok = True
    model = asp.one_model(asp_program("#show mission/1.\n#show route/1.\n#show hazard/1.\n#show fix/1."))
    if not model:
        print("MISMATCH: ASP produced no model.")
        ok = False
    return 0 if ok else 1


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mission/1.\n#show route/1.\n#show hazard/1.\n#show fix/1."))
    return [(a,) for a in asp.atoms(model, "mission")]


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    defaults = {
        "astro-chart": ("lane", "scrape", "turn"),
        "moon-loop": ("loop", "jolt", "strap"),
        "comet-bend": ("comet", "open-bay", "latch"),
    }
    mission = args.mission or rng.choice(list(MISSIONS))
    route, hazard, fix = defaults[mission]
    route = args.route or route
    hazard = args.hazard or hazard
    fix = args.fix or fix
    if (route, hazard, fix) != defaults[mission]:
        raise StoryError(f"(No story: {mission} needs {defaults[mission][0]}, {defaults[mission][1]}, and {defaults[mission][2]}.)")
    params = StoryParams(
        mission=mission,
        route=route,
        hazard=hazard,
        fix=fix,
        pilot=args.pilot or rng.choice(PILOT_NAMES),
        pilot_type=args.pilot_type or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(HELPER_NAMES),
        helper_type=args.helper_type or rng.choice(["girl", "boy"]),
        captain=args.captain or rng.choice(CAPTAIN_NAMES),
        captain_type=args.captain_type or rng.choice(["woman", "man"]),
    )
    return params


def asp_verify() -> int:
    rc = 0
    p = StoryParams(
        mission="astro-chart", route="lane", hazard="scrape", fix="turn",
        pilot="Nova", pilot_type="girl", helper="Kite", helper_type="boy",
        captain="Captain Luna", captain_type="woman",
    )
    try:
        sample = generate(p)
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"MISMATCH: normal generate failed: {e}")
        rc = 1
    try:
        import asp  # noqa: F401
    except Exception as e:
        print(f"MISMATCH: asp import failed: {e}")
        rc = 1
    rc |= asp_verify_gate()
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mission/1.\n#show route/1.\n#show hazard/1.\n#show fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this storyworld.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(mission="astro-chart", route="lane", hazard="scrape", fix="turn",
                        pilot="Nova", pilot_type="girl", helper="Kite", helper_type="boy",
                        captain="Captain Luna", captain_type="woman"),
            StoryParams(mission="moon-loop", route="loop", hazard="jolt", fix="strap",
                        pilot="Pip", pilot_type="boy", helper="Sol", helper_type="girl",
                        captain="Captain Orion", captain_type="man"),
            StoryParams(mission="comet-bend", route="comet", hazard="open-bay", fix="latch",
                        pilot="Mira", pilot_type="girl", helper="Ari", helper_type="boy",
                        captain="Captain Vega", captain_type="woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
