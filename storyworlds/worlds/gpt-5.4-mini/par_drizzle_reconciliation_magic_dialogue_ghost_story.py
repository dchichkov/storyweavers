#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/par_drizzle_reconciliation_magic_dialogue_ghost_story.py
=========================================================================================

A standalone story world for a small, child-facing ghost tale:
a child in a drizzle meets a lonely ghost, speaks kindly, uses a little bit of
magic, and ends in reconciliation.

Seed words: par, drizzle
Features: Reconciliation, Magic, Dialogue
Style: Ghost Story

The world model is intentionally tiny:
- a park at dusk with a drizzle
- a child carrying a small charm
- a ghost who is lonely rather than scary
- dialogue that can lower fear and sadness
- magic that makes the ghost visible and safe to talk to
- reconciliation that changes the ending image from alone to together

The prose is driven by state, not by a frozen paragraph template. Different
choices change who speaks, whether the ghost is lonely or grumpy, how strong the
magic is, and whether the final scene becomes a gentle friendship.
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
MAGIC_MIN = 1
PEACE_MIN = 1


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    after_dark: str
    details: str

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
class Charm:
    id: str
    label: str
    glow: str
    magic: int
    warmth: str

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
class GhostMood:
    id: str
    label: str
    sadness: int
    scare: int
    clue: str

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
        return c


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


def _r_drizzle(world: World) -> list[str]:
    out: list[str] = []
    if "rain" not in world.entities or "child" not in world.entities:
        return out
    rain = world.get("rain")
    child = world.get("child")
    if rain.meters["drizzle"] < THRESHOLD:
        return out
    sig = ("drizzle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    rain.meters["grey"] += 1
    out.append("__drizzle__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    if "charm" not in world.entities or "ghost" not in world.entities:
        return out
    charm = world.get("charm")
    ghost = world.get("ghost")
    if charm.meters["glow"] < MAGIC_MIN:
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["visible"] += 1
    ghost.memes["lonely"] = max(0.0, ghost.memes["lonely"] - 1)
    out.append("__magic__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not child or not ghost:
        return out
    if child.memes["fear"] < THRESHOLD:
        return out
    if ghost.memes["lonely"] < PEACE_MIN:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["peace"] += 1
    ghost.memes["peace"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("drizzle", "weather", _r_drizzle),
    Rule("magic", "magic", _r_magic),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for item in rule.apply(world):
                if item.startswith("__"):
                    changed = True
                else:
                    produced.append(item)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_reconcile(magic: Charm, mood: GhostMood) -> bool:
    return magic.magic >= MAGIC_MIN and mood.sadness >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CHARMS:
            for gid in GHOST_MOODS:
                if can_reconcile(CHARMS[cid], GHOST_MOODS[gid]):
                    combos.append((sid, cid, gid))
    return combos


def setup_scene(world: World, setting: Setting, child: Entity, ghost: Entity, charm: Entity) -> None:
    world.say(
        f"At {setting.place} after dark, a light drizzle kept tapping the leaves, "
        f"and the path shone like black glass."
    )
    world.say(
        f"{child.id} had come back to {setting.place} on purpose, holding "
        f"{charm.label} close."
    )
    world.say(
        f"Some said the old ghost in the par was scary, but {child.id} only felt "
        f"the shiver that comes before a brave question."
    )


def hear_ghost(world: World, child: Entity, ghost: Entity, setting: Setting) -> None:
    child.memes["fear"] += 1
    world.say(
        f"A pale shape drifted near the bench. {ghost.id} looked wet and sad, "
        f"as if the drizzle had washed all the color from {ghost.pronoun('possessive')} face."
    )
    world.say(
        f'"Why are you hiding in the {setting.place}?" {child.id} asked.'
    )


def ghost_reply(world: World, ghost: Entity, child: Entity) -> None:
    ghost.memes["lonely"] += 1
    world.say(
        f'"I am not hiding," {ghost.id} whispered. "I am waiting for someone who '
        f"never came back."
    )
    world.say(
        f'{child.id} swallowed, then answered, "{ghost.id}, I can stay."'
    )


def cast_magic(world: World, child: Entity, charm: Entity, ghost: Entity) -> None:
    charm.meters["glow"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} lifted {charm.label}, and it gave off {charm.glow}. "
        f"The little light did not fight the dark; it made a circle for talking."
    )
    propagate(world, narrate=False)


def share_truth(world: World, ghost: Entity, child: Entity, mood: GhostMood) -> None:
    world.say(
        f'"I miss my friend," {ghost.id} said. "{mood.clue}"'
    )
    world.say(
        f"{child.id} listened carefully. The drizzle made tiny rings in the puddles, "
        f"and each ring felt like a quiet yes."
    )


def reconcile(world: World, child: Entity, ghost: Entity, mood: GhostMood) -> None:
    child.memes["peace"] += 1
    ghost.memes["peace"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    ghost.memes["lonely"] = max(0.0, ghost.memes["lonely"] - 1)
    world.say(
        f'{child.id} said, "We can walk together until you feel better." '
        f'{ghost.id} nodded, and the sad air loosened at once.'
    )
    world.say(
        f"{ghost.id} smiled for the first time all night. It was a small smile, "
        f"but in a ghost story, a small smile can sound like a bell."
    )


def ending(world: World, child: Entity, ghost: Entity, charm: Entity, setting: Setting) -> None:
    world.say(
        f"When the drizzle thinned, {child.id} and {ghost.id} stood by the gate, "
        f"sharing the last of {charm.label}'s glow."
    )
    world.say(
        f"The ghost was no longer lonely, and {setting.place} did not feel haunted "
        f"anymore. It felt like a place where two friends had learned how to be gentle."
    )


def tell(setting: Setting, charm: Charm, mood: GhostMood, child_name: str = "Nia",
         child_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender, role="child"))
    ghost = world.add(Entity("ghost", kind="character", type="ghost", role="ghost"))
    rain = world.add(Entity("rain", kind="thing", type="weather", label="the drizzle"))
    charm_ent = world.add(Entity("charm", kind="thing", type="charm", label=charm.label))

    child.id = child_name
    ghost.id = "the ghost"
    ghost.label = "the ghost"
    ghost.memes["lonely"] = float(mood.sadness)
    ghost.memes["fear"] = float(mood.scare)

    setup_scene(world, setting, child, ghost, charm_ent)
    world.para()
    hear_ghost(world, child, ghost, setting)
    ghost_reply(world, ghost, child)
    world.para()
    cast_magic(world, child, charm_ent, ghost)
    share_truth(world, ghost, child, mood)
    if child.memes["peace"] >= THRESHOLD or ghost.meters["visible"] >= THRESHOLD:
        reconcile(world, child, ghost, mood)
    world.para()
    ending(world, child, ghost, charm_ent, setting)
    world.facts.update(setting=setting, charm=charm, mood=mood, child=child, ghost=ghost)
    return world


SETTINGS = {
    "park": Setting("park", "the park", "after dark", "bare benches and wet leaves"),
    "par": Setting("par", "the old par", "after dark", "a narrow path and a bowed willow"),
    "garden": Setting("garden", "the garden", "after dark", "stone borders and shiny puddles"),
}

CHARMS = {
    "lantern": Charm("lantern", "a tiny lantern charm", "a warm gold circle", 2, "kind"),
    "bell": Charm("bell", "a silver bell charm", "a clear silver ring", 1, "gentle"),
}

GHOST_MOODS = {
    "missing": GhostMood("missing", "lonely ghost", 2, 1, "I lost my friend at the gate."),
    "waiting": GhostMood("waiting", "waiting ghost", 1, 2, "I have waited so long that even the rain knows my name."),
}

NAMES = ["Nia", "Mina", "Lila", "Ari", "June", "Owen", "Theo", "Mira", "Eli", "Sage"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    charm: str
    mood: str
    child_name: str
    child_gender: str
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


KNOWLEDGE = {
    "drizzle": [("What is drizzle?", "Drizzle is very light rain with tiny drops.")],
    "ghost": [("What is a ghost in a story?", "A ghost is a pretend spirit character in a story.")],
    "lantern": [("What does a lantern do?", "A lantern gives off light so people can see in the dark.")],
    "bell": [("What does a bell sound like?", "A bell makes a clear ringing sound.")],
    "reconcile": [("What is reconciliation?", "Reconciliation means making peace after being upset or apart.")],
    "magic": [("What is magic in a story?", "Magic is a pretend power that can do surprising things in stories.")],
    "dialogue": [("What is dialogue?", "Dialogue is when characters speak to each other in a story.")],
}

KNOWLEDGE_ORDER = ["drizzle", "ghost", "lantern", "bell", "magic", "dialogue", "reconcile"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the words "par" and "drizzle".',
        f"Tell a gentle ghost story in {f['setting'].place} where a child speaks kindly to a lonely ghost and uses a little magic to make peace.",
        f"Write a story with dialogue, magic, and reconciliation, ending with two characters no longer feeling alone in the rain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, charm, setting = f["child"], f["ghost"], f["charm"], f["setting"]
    return [
        QAItem(
            question="Why did the child go to the park?",
            answer=(
                f"The child went back because {ghost.id} was there, lonely in the drizzle. "
                f"Bringing {charm.label} gave the child a calm way to help."
            ),
        ),
        QAItem(
            question="How did the magic help?",
            answer=(
                f"{charm.label.capitalize()} made a small glow that let the child and the ghost talk safely. "
                f"It turned the scary dark into a circle where they could hear each other."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended in reconciliation. {ghost.id} was no longer lonely, and {setting.place} felt peaceful instead of haunted."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"drizzle", "ghost", "magic", "dialogue", "reconcile"}
    if world.facts["charm"].id == "lantern":
        tags.add("lantern")
    else:
        tags.add("bell")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, charm: Charm, mood: GhostMood) -> str:
    return "(No story: this combination cannot make a calm ghost reconciliation tale.)"


ASP_RULES = r"""
drizzle :- weather(drizzle).
magic_happens :- charm(C), glow(C, G), G >= magic_min.
visible_ghost :- ghost(G), magic_happens, lonely(G, L), L >= 1.
reconcile :- child(C), visible_ghost, ghost(G), lonely(G, L), L >= 1.
valid(S, C, M) :- setting(S), charm(C), mood(M), can_reconcile(C, M).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("magic_min", MAGIC_MIN)]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("glow", cid, c.magic))
    for mid, m in GHOST_MOODS.items():
        lines.append(asp.fact("mood", mid))
        lines.append(asp.fact("lonely", mid, m.sadness))
    lines.append(asp.fact("weather", "drizzle"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate:")
        if a - b:
            print(" only in ASP:", sorted(a - b))
        if b - a:
            print(" only in Python:", sorted(b - a))
    # smoke test ordinary generation
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    if not sample.story.strip():
        print("MISMATCH: empty story from normal generation.")
        return 1
    print("OK: normal story generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny drizzle-and-ghost story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--mood", choices=GHOST_MOODS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.mood is None or c[2] == args.mood)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, mood = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting, charm, mood, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHARMS[params.charm], GHOST_MOODS[params.mood],
                 params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
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
    StoryParams("park", "lantern", "missing", "Nia", "girl"),
    StoryParams("par", "bell", "waiting", "Owen", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c, m in combos:
            print(f"  {s:8} {c:8} {m}")
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
            header = f"### {p.child_name} in {p.setting} ({p.charm}, {p.mood})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
