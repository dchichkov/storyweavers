#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fall_chitlin_vanilla_bad_ending_curiosity_sharing.py
====================================================================================

A standalone storyworld for a tiny detective-style domain built from the seed
words fall, chitlin, and vanilla, with curiosity, sharing, and a bad ending.

The world models a small case:
- a child detective notices something odd during fall cleanup,
- curiosity pulls the child deeper into the clue trail,
- sharing changes what gets eaten and who gets access,
- a bad ending happens when the last clue is ruined or lost before the case is solved.

The prose is driven by world state, not a frozen template.
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    weather: str
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
class Clue:
    id: str
    label: str
    scent: str
    location: str
    fragile: bool = False
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
class Snack:
    id: str
    label: str
    flavor: str
    shareable: bool
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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("scatter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.meters["tracks"] += 1
    out.append("__scatter__")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["ruined"] >= THRESHOLD:
        return out
    if world.facts.get("shared_last_piece"):
        sig = ("spoil",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        snack.meters["ruined"] += 1
        out.append("__spoil__")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter), Rule("spoil", _r_spoil)]


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


def reasonableness_gate(setting: Setting, clue: Clue, snack: Snack) -> bool:
    return "fall" in setting.tags and "vanilla" in snack.tags and clue.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for nid, snack in SNACKS.items():
                if reasonableness_gate(setting, clue, snack):
                    combos.append((sid, cid, nid))
    return combos


def clue_prediction(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _take_clue(sim, sim.get(clue_id), narrate=False)
    return {"ruined": sim.get("snack").meters["ruined"] >= THRESHOLD,
            "curiosity": sim.get("detective").memes["curiosity"]}


def _take_clue(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["moved"] += 1
    world.get("detective").memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, detective: Entity, friend: Entity, setting: Setting, clue: Clue, snack: Snack) -> None:
    detective.memes["curiosity"] += 1
    friend.memes["sharing"] += 1
    snack.meters["vanilla"] += 1
    world.say(
        f"On a cold fall afternoon, {detective.id} and {friend.id} worked a little detective case at {setting.place}. "
        f"{setting.detail} The sweet smell of {snack.flavor} drifted from a plate of {snack.label}."
    )
    world.say(
        f'{detective.id} leaned over the clue board. "{clue.label} at {clue.location}," {detective.id} murmured. '
        f'"That does not look right."'
    )


def curiosity(world: World, detective: Entity, clue: Clue) -> None:
    world.say(
        f'{detective.id} could not leave it alone. {detective.pronoun().capitalize()} followed the {clue.label} because '
        f'the question felt bigger than {detective.pronoun("possessive")} own boots.'
    )


def share_snack(world: World, detective: Entity, friend: Entity, snack: Snack) -> None:
    detective.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    world.facts["shared_last_piece"] = True
    world.say(
        f'{friend.id} smiled and broke the last {snack.label} in half. '
        f'"Here," {friend.id} said. "We can share the vanilla one."'
    )


def ruin_and_miss(world: World, clue: Clue, snack: Snack) -> None:
    snack.meters["ruined"] += 1
    world.say(
        f"Then the wind shoved the clue into a puddle of brown leaves. The paper curled up, the ink ran, and the last "
        f"bit of {snack.flavor} slipped from {world.get('detective').id}'s fingers into the mud."
    )


def bad_ending(world: World, detective: Entity, friend: Entity, setting: Setting, snack: Snack) -> None:
    detective.memes["sad"] += 1
    friend.memes["sad"] += 1
    world.say(
        f"For a moment they stood very still. The case was not solved, and the plate was empty. "
        f"The sweet {snack.label} was gone, and so was the clue that might have answered everything."
    )
    world.say(
        f"By the time {setting.place} grew dark, {detective.id} had only the muddy footprints and the taste of vanilla on {detective.pronoun('possessive')} tongue."
    )


def tell(setting: Setting, clue: Clue, snack: Snack,
         detective_name: str = "Milo", detective_gender: str = "boy",
         friend_name: str = "Pia", friend_gender: str = "girl") -> World:
    world = World()
    d = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    f = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    s = world.add(Entity(id="setting", type="place", label=setting.place))
    c = world.add(Entity(id="clue", type="clue", label=clue.label, attrs={"location": clue.location}))
    sn = world.add(Entity(id="snack", type="snack", label=snack.label, attrs={"flavor": snack.flavor}))

    setup(world, d, f, setting, clue, snack)
    world.para()
    curiosity(world, d, clue)
    share_snack(world, d, f, snack)
    _take_clue(world, c, narrate=False)
    world.para()
    ruin_and_miss(world, clue, snack)
    bad_ending(world, d, f, setting, snack)

    world.facts.update(
        detective=d, friend=f, setting=setting, clue=clue, snack=snack,
        outcome="bad_ending", shared_last_piece=True, clue_lost=True,
    )
    return world


SETTINGS = {
    "fall_market": Setting("fall_market", "the fall market", "Leaf banners shook above the stalls, and apples rolled in little wooden boxes.", "fall", {"fall"}),
    "old_house": Setting("old_house", "the old house", "The porch creaked, and a lantern gave the hallway a warm yellow glow.", "fall", {"fall"}),
    "pumpkin_path": Setting("pumpkin_path", "the pumpkin path", "Orange pumpkins lined the path, and dry leaves rustled under every step.", "fall", {"fall"}),
}

CLUES = {
    "crumb": Clue("crumb", "a vanilla crumb", "vanilla", "by the back counter", fragile=True, tags={"vanilla", "clue"}),
    "note": Clue("note", "a folded note", "ink", "under the jar", fragile=True, tags={"note", "clue"}),
    "wrapper": Clue("wrapper", "a candy wrapper", "sugar", "behind the basket", fragile=True, tags={"wrapper", "clue"}),
}

SNACKS = {
    "chitlin": Snack("chitlin", "a chitlin", "vanilla", True, {"vanilla", "snack"}),
    "plate": Snack("plate", "a plate of chitlins", "vanilla", True, {"vanilla", "snack"}),
    "treat": Snack("treat", "a little vanilla treat", "vanilla", True, {"vanilla", "snack"}),
}

NAMES = {
    "girls": ["Pia", "Nina", "Luna", "Mia", "Vera"],
    "boys": ["Milo", "Eli", "Noah", "Theo", "Leo"],
}

TRAITS = ["curious", "careful", "bright", "gentle"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    snack: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective-style story for a young child that includes the words "fall", "chitlin", and "vanilla".',
        f"Tell a small mystery about {f['detective'].id} and {f['friend'].id} at {f['setting'].place}, where curiosity leads to a bad ending.",
        f"Write a short story where sharing a vanilla chitlin changes the case, and the clue is lost before the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, fr, setting, snack = f["detective"], f["friend"], f["setting"], f["snack"]
    return [
        ("Who is the story about?",
         f"It is about {d.id}, who was acting like a little detective, and {fr.id}, who shared the snack. They were solving a small fall-day mystery together."),
        ("What did the detective want to know?",
         f"{d.id} wanted to know why the clue looked wrong. {d.pronoun().capitalize()} kept following the trail because curiosity made the question feel too big to ignore."),
        ("What happened when they shared the snack?",
         f"They split the vanilla chitlin and ate it together. That sharing left the last piece vulnerable, and the snack did not stay safe for the ending."),
        ("How did the story end?",
         "It ended badly. The clue got ruined and the mystery stayed unsolved, so the detective had only muddy footprints and an empty plate left to look at."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does fall mean?",
         "Fall is the season when leaves turn colors and the air gets cooler."),
        ("What is vanilla?",
         "Vanilla is a sweet flavor that smells warm and creamy."),
        ("What does a detective do?",
         "A detective looks for clues, asks careful questions, and tries to solve a mystery."),
        ("What is sharing?",
         "Sharing means letting someone else have some of what you have, like a snack or a toy."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fall_market", "crumb", "chitlin", "Milo", "boy", "Pia", "girl", "curious"),
    StoryParams("old_house", "note", "plate", "Nina", "girl", "Leo", "boy", "gentle"),
    StoryParams("pumpkin_path", "wrapper", "treat", "Theo", "boy", "Vera", "girl", "bright"),
]


def explain_rejection(setting: Setting, clue: Clue, snack: Snack) -> str:
    if not reasonableness_gate(setting, clue, snack):
        return "(No story: this setup does not make a plausible detective case with fall, chitlin, and vanilla.)"
    return "(No story: invalid combination.)"


def valid_outcome(_: StoryParams) -> str:
    return "bad_ending"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "fall" in s.tags:
            lines.append(asp.fact("fall_setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
        if "vanilla" in c.tags:
            lines.append(asp.fact("vanilla_clue", cid))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        if n.shareable:
            lines.append(asp.fact("shareable", nid))
        if "vanilla" in n.tags:
            lines.append(asp.fact("vanilla_snack", nid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,N) :- setting(S), clue(C), snack(N), fall_setting(S), fragile(C), vanilla_snack(N).
bad_ending(S,C,N) :- valid(S,C,N).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    sample = generate(CURATED[0])
    if not sample.story or "vanilla" not in sample.story.lower():
        rc = 1
        print("MISMATCH: normal story generation failed or missed required wording.")
    else:
        print("OK: smoke story generated.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a fall detective case with chitlin, vanilla, curiosity, sharing, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    clue = args.clue or rng.choice(sorted(CLUES))
    snack = args.snack or rng.choice(sorted(SNACKS))
    if not reasonableness_gate(SETTINGS[setting], CLUES[clue], SNACKS[snack]):
        raise StoryError(explain_rejection(SETTINGS[setting], CLUES[clue], SNACKS[snack]))
    detective_gender = rng.choice(["boy", "girl"])
    friend_gender = "girl" if detective_gender == "boy" else "boy"
    detective = args.detective or rng.choice(NAMES["boys" if detective_gender == "boy" else "girls"])
    friend = args.friend or rng.choice(NAMES["girls" if friend_gender == "girl" else "boys"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, clue, snack, detective, detective_gender, friend, friend_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], SNACKS[params.snack],
                 params.detective, params.detective_gender, params.friend, params.friend_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show bad_ending/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} at {p.setting} ({p.clue}, {p.snack})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
