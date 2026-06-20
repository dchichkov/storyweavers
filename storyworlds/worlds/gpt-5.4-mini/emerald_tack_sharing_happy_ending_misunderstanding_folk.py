#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/emerald_tack_sharing_happy_ending_misunderstanding_folk.py
===========================================================================================

A standalone storyworld for a folk-tale style sharing story with a small
misunderstanding, a kind correction, and a happy ending.

Domain idea:
- A child finds a bright emerald pin and wants to use a tack to fasten it into a
  cloth banner.
- Another child mistakes the tack for a sharp, selfish thing and thinks the pin
  will be hidden away.
- The misunderstanding is resolved when they realize the tack is only a tool,
  the emerald is meant to be shared, and the family makes a little village
  banner together.
- The story always ends with a warm image proving the sharing changed the world:
  the emerald shines on the banner, and everyone gets to admire it.

This is a small classical simulation with:
- typed entities carrying physical meters and emotional memes,
- a causal rule engine,
- a Python reasonableness gate plus an inline ASP twin,
- three QA sets derived from world state,
- a complete CLI with trace / QA / JSON / ASP / verify modes.

Run examples:
    python storyworlds/worlds/gpt-5.4-mini/emerald_tack_sharing_happy_ending_misunderstanding_folk.py
    python storyworlds/worlds/gpt-5.4-mini/emerald_tack_sharing_happy_ending_misunderstanding_folk.py --trace
    python storyworlds/worlds/gpt-5.4-mini/emerald_tack_sharing_happy_ending_misunderstanding_folk.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/emerald_tack_sharing_happy_ending_misunderstanding_folk.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    item_kind: str = ""
    visible: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    style: str
    banner: str
    gathering: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Treasure:
    id: str
    label: str
    phrase: str
    gleam: str
    shared: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    use: str
    sharp: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_show(world: World) -> list[str]:
    out: list[str] = []
    emerald = world.get("emerald")
    if emerald.meters["shown"] >= THRESHOLD and not emerald.shared:
        sig = ("show", "emerald")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__show__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    emerald = world.get("emerald")
    if emerald.meters["shared"] >= THRESHOLD and not emerald.shared:
        sig = ("share", "emerald")
        if sig not in world.fired:
            world.fired.add(sig)
            emerald.shared = True
            for kid in world.characters():
                kid.memes["joy"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("show", "social", _r_show),
    Rule("share", "social", _r_share),
]


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


def valid_combo(setting: Setting, treasure: Treasure, tool: Tool) -> bool:
    return treasure.shared and tool.sharp and treasure.id == "emerald" and tool.id == "tack"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, treasure in TREASURES.items():
            for uid, tool in TOOLS.items():
                if valid_combo(setting, treasure, tool):
                    combos.append((sid, tid, uid))
    return combos


def reasonableness_reason(setting: Setting, treasure: Treasure, tool: Tool) -> str:
    if not treasure.shared:
        return "treasure must be shareable"
    if not tool.sharp:
        return "the tool must actually be a tack"
    if treasure.id != "emerald" or tool.id != "tack":
        return "this world is built around the emerald and the tack"
    return ""


def predict_share(world: World) -> dict:
    sim = world.copy()
    sim.get("emerald").meters["shown"] += 1
    propagate(sim, narrate=False)
    return {"shared": sim.get("emerald").shared}


def announce(world: World, child: Entity, other: Entity, setting: Setting, treasure: Treasure) -> None:
    world.say(
        f"On a quiet morning in {setting.place}, {child.id} found {treasure.phrase} "
        f"beside the old bench, where folk songs said small wonders liked to rest."
    )
    world.say(
        f'{other.id} leaned close. "What is that bright little {treasure.label}?" '
        f"{other.id} asked, and the air felt curious and still."
    )


def misunderstanding(world: World, child: Entity, other: Entity, tool: Tool, treasure: Treasure) -> None:
    child.memes["hope"] += 1
    other.memes["worry"] += 1
    world.say(
        f'{child.id} smiled and held up {tool.phrase}. "I can pin the {treasure.label} '
        f'to the banner with this," {child.id} said.'
    )
    world.say(
        f'{other.id} frowned. "A tack sounds too sharp," {other.id} said. '
        f'"Maybe you mean to hide the {treasure.label} away."'
    )


def clarify(world: World, child: Entity, other: Entity, treasure: Treasure, tool: Tool) -> None:
    pred = predict_share(world)
    world.facts["predicted_shared"] = pred["shared"]
    world.say(
        f"{child.id} shook {child.pronoun('possessive')} head and laughed softly. "
        f'"No, the {tool.label} is only a helper. I want the {treasure.label} to be seen, '
        f'not kept away."'
    )
    world.say(
        f"{other.id} blinked, then understood. " 
        f'"Oh! You mean the {treasure.label} will belong to everyone in the village hall."'
    )


def share_world(world: World, child: Entity, other: Entity, setting: Setting,
                treasure: Treasure, tool: Tool) -> None:
    treasure_ent = world.get("emerald")
    treasure_ent.meters["shown"] += 1
    treasure_ent.meters["shared"] += 1
    world.get("banner").meters["bright"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they walked to the village hall, where {setting.banner} waited on the wall. "
        f"{child.id} used {tool.phrase} to fasten the {treasure.label} in the center of the cloth."
    )
    world.say(
        f"The {treasure.label} glimmered like a little green star, and everyone gathered around to admire it."
    )
    world.say(
        f"{other.id} grinned. " 
        f'"It was never meant to be hidden," {other.id} said. "It was meant to be shared."'
    )


def ending(world: World, child: Entity, other: Entity, setting: Setting, treasure: Treasure) -> None:
    child.memes["joy"] += 1
    other.memes["joy"] += 1
    world.say(
        f"By evening, {setting.gathering} was full of smiling faces, and the emerald still shone on the banner."
    )
    world.say(
        f"{child.id} and {other.id} stood side by side, proud that one small treasure had become a gift for the whole village."
    )


def tell(setting: Setting, treasure: Treasure, tool: Tool,
         child_name: str = "Mira", child_gender: str = "girl",
         other_name: str = "Oren", other_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="other"))
    banner = world.add(Entity(id="banner", type="thing", label=setting.banner))
    emerald = world.add(Entity(id="emerald", type="treasure", label=treasure.label, shared=False))
    tack = world.add(Entity(id="tack", type="tool", label=tool.label))
    world.facts.update(setting=setting, treasure=treasure, tool=tool, child=child, other=other,
                       banner=banner, emerald=emerald, tack=tack)

    announce(world, child, other, setting, treasure)
    world.para()
    misunderstanding(world, child, other, tool, treasure)
    clarify(world, child, other, treasure, tool)
    world.para()
    share_world(world, child, other, setting, treasure, tool)
    ending(world, child, other, setting, treasure)

    world.facts["outcome"] = "shared"
    return world


SETTINGS = {
    "village": Setting("village", "the village green", "folk tale", "old banner", "the lantern gathering"),
    "mill": Setting("mill", "the old mill yard", "folk tale", "woven banner", "the evening supper"),
    "harbor": Setting("harbor", "the quiet harbor lane", "folk tale", "harbor banner", "the dockside feast"),
}

TREASURES = {
    "emerald": Treasure("emerald", "emerald", "a bright emerald", "green gleam", shared=True, tags={"emerald", "green"}),
}

TOOLS = {
    "tack": Tool("tack", "tack", "a small tack", "pin cloth", sharp=True, tags={"tack", "sharp"}),
}

GIRL_NAMES = ["Mira", "Lina", "Sera", "Nina", "Alma", "Tess"]
BOY_NAMES = ["Oren", "Jory", "Milo", "Evan", "Perry", "Theo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    treasure: str
    tool: str
    child: str
    child_gender: str
    other: str
    other_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story that includes the words "{f["treasure"].label}" and "{f["tool"].label}".',
        f"Tell a gentle sharing story in a village where {f['child'].id} and {f['other'].id} misunderstand a tack, then happily share the emerald.",
        f'Write a happy-ending story in a folk-tale voice about a bright emerald, a tack, a misunderstanding, and a shared treasure.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, other, treasure, tool, setting = f["child"], f["other"], f["treasure"], f["tool"], f["setting"]
    return [
        ("Who found the emerald?", f"{child.id} found the emerald near the old bench in {setting.place}."),
        ("What did the other child first misunderstand?", f"{other.id} first thought the tack meant the emerald might be hidden away. The two children were not arguing; they simply did not understand each other at first."),
        ("How did they solve the misunderstanding?", f"{child.id} explained that the tack was only a tool for fastening the emerald to the banner. After that, {other.id} understood and helped share it."),
        ("How did the story end?", f"It ended happily, with the emerald shining on the banner for everyone to see. The treasure became a shared gift instead of something secret."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tack?", "A tack is a small sharp tool used to pin paper or cloth to a board or banner."),
        ("What is an emerald?", "An emerald is a bright green gemstone that can shine like a little star."),
        ("What does it mean to share something?", "To share something means to let other people enjoy it too instead of keeping it all to yourself."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(E) :- emerald(E), shown(E), tack(T), tool(T).
happy_end :- shared(E).
misunderstanding :- child(C), other(O), emerald(E), tack(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("emerald", tid))
        lines.append(asp.fact("shared_treasure", tid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
        lines.append(asp.fact("tack", uid))
    lines.append(asp.fact("reason", "sharing"))
    lines.append(asp.fact("style", "folk"))
    lines.append(asp.fact("feature", "happy_ending"))
    lines.append(asp.fact("feature", "misunderstanding"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generate() produced empty story.")
    else:
        print("OK: generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: emerald, tack, sharing, misunderstanding, folk-tale style.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting or args.treasure or args.tool:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.treasure is None or c[1] == args.treasure)
                  and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, tool = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    other_gender = args.other_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    other = args.other or rng.choice([n for n in (BOY_NAMES if other_gender == "boy" else GIRL_NAMES) if n != child])
    return StoryParams(setting, treasure, tool, child, child_gender, other, other_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TREASURES[params.treasure],
        TOOLS[params.tool],
        params.child,
        params.child_gender,
        params.other,
        params.other_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("village", "emerald", "tack", "Mira", "girl", "Oren", "boy"),
    StoryParams("mill", "emerald", "tack", "Lina", "girl", "Theo", "boy"),
    StoryParams("harbor", "emerald", "tack", "Jory", "boy", "Sera", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for sid, tid, uid in asp_valid_combos():
            print(f"  {sid:8} {tid:8} {uid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.other}: emerald and tack in the {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
