#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/charcoal_millimeter_quest_magic_twist_space_adventure.py
========================================================================================

A small space-adventure storyworld about a child mission, a tricky machine,
magic charcoal, and a tiny millimeter-based twist.

The world is intentionally narrow: a young crewmate goes on a quest to finish a
model rocket, but the final piece is off by just one millimeter. A magic
charcoal stick reveals the mismatch, the crew solves it with a careful trim, and
the finished rocket finally glows and launches.

This script follows the shared Storyweavers world contract:
- standalone stdlib only
- imports results eagerly
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python/ASP parity checks and a smoke test in --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    region: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class QuestSetting:
    id: str
    scene: str
    ship_name: str
    goal: str
    dark_place: str
    style_note: str

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
    where: str
    magic: bool = False
    messy: bool = False

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
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    size_mm: int
    fits_if_trimmed: bool = True
    fragile: bool = False

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
class Wonder:
    id: str
    label: str
    effect: str
    helper: str
    twist: str

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
class World:
    def __init__(self, setting: QuestSetting) -> None:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_glow(world: World) -> list[str]:
    out = []
    rocket = world.entities.get("rocket")
    if rocket and rocket.meters["ready"] >= THRESHOLD and ("glow", "rocket") not in world.fired:
        world.fired.add(("glow", "rocket"))
        rocket.meters["glow"] += 1
        out.append("__glow__")
    return out


def _r_launch(world: World) -> list[str]:
    out = []
    rocket = world.entities.get("rocket")
    if rocket and rocket.meters["glow"] >= THRESHOLD and rocket.meters["fit"] >= THRESHOLD and ("launch", "rocket") not in world.fired:
        world.fired.add(("launch", "rocket"))
        rocket.meters["launch"] += 1
        out.append("__launch__")
    return out


CAUSAL_RULES = [Rule("glow", "magic", _r_glow), Rule("launch", "magic", _r_launch)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def build_smoke_path(world: World) -> str:
    return world.setting.dark_place


def explain_measure(millimeters: int) -> str:
    return f"Only {millimeters} millimeter{'' if millimeters == 1 else 's'} off"


def predict_fit(world: World, artifact_id: str) -> dict:
    sim = world.copy()
    artifact = sim.get(artifact_id)
    artifact.meters["fit"] += 1
    if artifact.attrs.get("trimmed"):
        artifact.meters["fit"] += 1
    propagate(sim, narrate=False)
    return {"fit": sim.get("rocket").meters["fit"], "launch": sim.get("rocket").meters["launch"]}


def do_quest(world: World, child: Entity, setting: QuestSetting, artifact: Artifact, tool: Tool, wonder: Wonder) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"On a quiet night above the silver planet, {child.id} climbed into the little ship and began a quest in {setting.scene}. "
        f"{setting.style_note}"
    )
    world.say(
        f"{child.id} wanted to finish the model rocket for the mission board, but the last {artifact.label} was {artifact.size_mm} millimeters wide and the slot was just a little tighter."
    )
    world.say(
        f"The room went still. Then {child.id} found {tool.phrase} {tool.where}, and the dark little corner looked like a place where secrets could hide."
    )
    world.say(
        f'{child.id} whispered, "If I can make one careful change, the rocket might fit."'
    )


def magic_hint(world: World, child: Entity, tool: Tool, artifact: Artifact, wonder: Wonder) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{tool.label.capitalize()} gave a soft, magic shine. In the glow, {child.id} could see the tiny edge of {artifact.label} standing proud by a single millimeter."
    )
    world.say(
        f'"{wonder.effect}," {child.id} said, and the {wonder.helper} would show the {wonder.twist} hidden in the gap.'
    )


def twist_reveal(world: World, child: Entity, artifact: Artifact) -> None:
    child.memes["focus"] += 1
    world.say(
        f"That was the twist: the rocket was not broken at all. It only needed a careful trim, because the last piece was almost right."
    )
    world.say(
        f"{child.id} took a breath and shaved away the tiniest sliver. It was so small it was hardly more than a whisper, but the fit changed at once."
    )


def finish(world: World, child: Entity, setting: QuestSetting, artifact: Artifact) -> None:
    rocket = world.get("rocket")
    rocket.meters["fit"] += 1
    rocket.meters["ready"] += 1
    artifact.attrs["trimmed"] = True
    propagate(world, narrate=False)
    world.say(
        f"The rocket clicked into place. Its nose cone sat straight, its fins shone silver, and the whole little ship waited in proud silence."
    )
    world.say(
        f"Then the launch button lit up. The rocket glowed, rose, and zipped into the stars above {setting.goal}."
    )
    world.say(
        f"{child.id} smiled at the bright trail and tucked the magic charcoal away. The quest was over, and the millimeter problem was solved."
    )


SETTINGS = {
    "space_station": QuestSetting(
        "space_station",
        "the quiet observatory bay on the space station",
        "Comet Kite",
        "the star map doorway",
        "the shadowy docking nook",
        "The room hummed like a sleeping engine, and the stars blinked outside the window.",
    ),
    "moon_base": QuestSetting(
        "moon_base",
        "the tiny workshop under the moon dome",
        "Luna Spark",
        "the crater gate",
        "the dim cargo corner",
        "Dust floated like glitter, and the blue Earth hung low and round beyond the glass.",
    ),
    "asteroid_lab": QuestSetting(
        "asteroid_lab",
        "the little lab carved into a shining asteroid",
        "Orbit Fox",
        "the tunnel to the launch pad",
        "the dark tool alcove",
        "The metal walls felt cool, and every sound bounced back like a secret.",
    ),
}

TOOLS = {
    "charcoal": Tool("charcoal", "charcoal stick", "a charcoal stick", "on the magnetic shelf", magic=True),
    "lamp": Tool("lamp", "lantern lamp", "a lantern lamp", "beside the map table"),
    "glow": Tool("glow", "glow pebble", "a glow pebble", "in a small jar", magic=True),
}

ARTIFACTS = {
    "panel": Artifact("panel", "panel", "the final panel", 11, fits_if_trimmed=True),
    "ring": Artifact("ring", "ring", "the silver ring", 9, fits_if_trimmed=True),
    "fin": Artifact("fin", "fin", "the last fin", 13, fits_if_trimmed=True),
}

WONDERS = {
    "quest": Wonder("quest", "quest", "the answer was worth searching for", "map", "twist"),
    "magic": Wonder("magic", "magic", "the light could reveal what plain eyes missed", "glow", "secret"),
    "twist": Wonder("twist", "twist", "the problem was only one tiny millimeter", "charcoal", "turn"),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Iris", "Sage"]
BOY_NAMES = ["Orin", "Jett", "Milo", "Arlo", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    tool: str
    artifact: str
    wonder: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, t, a, w) for s in SETTINGS for t in TOOLS for a in ARTIFACTS for w in WONDERS if TOOLS[t].magic]


def reason_ok(tool: Tool, artifact: Artifact) -> bool:
    return tool.magic and artifact.fits_if_trimmed


def explain_rejection(tool: Tool, artifact: Artifact) -> str:
    if not tool.magic:
        return f"(No story: {tool.label} is not magical enough for this quest.)"
    if not artifact.fits_if_trimmed:
        return f"(No story: {artifact.label} cannot be saved by a tiny trim.)"
    return "(No story: this combination is not reasonable.)"


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    tool = TOOLS[params.tool]
    artifact = ARTIFACTS[params.artifact]
    wonder = WONDERS[params.wonder]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="quester"))
    rocket = world.add(Entity(id="rocket", kind="thing", type="rocket", label="rocket"))
    rocket.meters["ready"] = 0
    world.facts.update(child=child, setting=setting, tool=tool, artifact=artifact, wonder=wonder)
    do_quest(world, child, setting, artifact, tool, wonder)
    world.para()
    magic_hint(world, child, tool, artifact, wonder)
    predicted = predict_fit(world, artifact.id)
    world.facts["predicted"] = predicted
    world.para()
    twist_reveal(world, child, artifact)
    finish(world, child, setting, artifact)
    world.facts["outcome"] = "launch"
    world.facts["rocket"] = rocket
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure quest for a child where the word "{f["tool"].label}" matters and the word "millimeter" appears.',
        f"Tell a magical rocket story where {f['child'].id} finds a tiny mistake and solves it with a quest, a twist, and {f['tool'].label}.",
        f"Write a child-friendly story set in space where one small millimeter changes everything, then the hero fixes it with magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    artifact = f["artifact"]
    tool = f["tool"]
    qa = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {child.id} going on a small quest in space to finish a rocket. The adventure turned on one tiny millimeter and a magical clue.",
        ),
        QAItem(
            question="What problem did {0} find?".format(child.id),
            answer=f"{child.id} found that {artifact.label} was almost right, but it was off by just one millimeter. That tiny mismatch kept the rocket from fitting until the edge was trimmed.",
        ),
        QAItem(
            question="How did the magic help?",
            answer=f"The {tool.label} glowed and showed the tiny gap clearly. That made the twist easy to understand, so {child.id} knew exactly where to fix the piece.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The rocket clicked into place and launched into the stars above {setting.goal}. The ending proved the millimeter problem was solved for real.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is charcoal?",
            answer="Charcoal is a black, smoky piece of burned wood that can mark on paper or stone. In stories, it can also feel magical and mysterious.",
        ),
        QAItem(
            question="What is a millimeter?",
            answer="A millimeter is a very tiny unit of length. It is much smaller than a centimeter, so it can matter when two pieces need to fit exactly.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search for something important. In space stories, it often means following clues to solve a problem.",
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can reveal a hidden clue, change what a character can see, or make an ordinary tool feel special. It helps the hero notice something they might have missed.",
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S,T,A,W) :- setting(S), tool(T), artifact(A), wonder(W), magic_tool(T), trim_fit(A).
launch(R) :- rocket(R), ready(R), fit(R), glow(R).
magic_tool(charcoal).
trim_fit(panel).
trim_fit(ring).
trim_fit(fin).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.magic:
            lines.append(asp.fact("magic_tool", tid))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if art.fits_if_trimmed:
            lines.append(asp.fact("trim_fit", aid))
    for wid in WONDERS:
        lines.append(asp.fact("wonder", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/4."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        print("MISMATCH in combo parity:")
        if a - b:
            print("  only in asp:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
        return 1
    print(f"OK: ASP and Python combo gates match ({len(a)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space quest storyworld with charcoal and millimeter twists.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    tool = args.tool or rng.choice(sorted([k for k, v in TOOLS.items() if v.magic]))
    artifact = args.artifact or rng.choice(sorted(ARTIFACTS))
    wonder = args.wonder or rng.choice(sorted(WONDERS))
    if not reason_ok(TOOLS[tool], ARTIFACTS[artifact]):
        raise StoryError(explain_rejection(TOOLS[tool], ARTIFACTS[artifact]))
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(names)
    return StoryParams(setting, tool, artifact, wonder, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("space_station", "charcoal", "panel", "quest", "Nova", "girl"),
    StoryParams("moon_base", "glow", "ring", "magic", "Orin", "boy"),
    StoryParams("asteroid_lab", "charcoal", "fin", "twist", "Mira", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_combo/4."))
        return
    if args.verify:
        rc = asp_verify()
        if rc:
            sys.exit(rc)
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            print("SMOKE TEST FAILED: empty story.")
            sys.exit(1)
        print("OK: story generation smoke test passed.")
        sys.exit(0)
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.tool} / {p.artifact} / {p.wonder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
