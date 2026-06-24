#!/usr/bin/env python3
"""
storyworlds/worlds/tend_rough_misunderstanding_repetition_sharing_ghost_story.py
=================================================================================

A small standalone storyworld in the Ghost Story style.

Premise:
- A child hears/feels something "rough" in a quiet old place.
- A misunderstanding makes the child think a ghost is upset or trapped.
- Repetition of a little action pattern ("tap, pause, listen") reveals the truth.
- Sharing a blanket, lantern, or toy with the ghost changes the mood from fear
  to kindness.
- The ending proves the ghost was never scary; it was lonely and needed tending.

This file models typed entities with meters (physical) and memes (emotional),
drives prose from simulated state, includes a Python reasonableness gate and an
inline ASP twin, and supports the standard storyworld CLI contract.
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
    kind: str = "thing"  # character | thing | spirit
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.attrs.get("plural", False)


@dataclass
class Setting:
    place: str
    hush: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Haunt:
    id: str
    label: str
    whisper: str
    roughness: str
    lonely: str
    kind: str = "spirit"
    type: str = "ghost"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    comfort: str
    shares: set[str] = field(default_factory=set)
    kind: str = "thing"
    type: str = "thing"


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def spirits(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "spirit"]

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["repeats"] < THRESHOLD:
        return out
    if ("repetition",) in world.fired:
        return out
    world.fired.add(("repetition",))
    child.memes["certainty"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    out.append("The same little tap-and-listen game began to feel like a clue.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.meters["sharing"] < THRESHOLD:
        return out
    if ("sharing",) in world.fired:
        return out
    world.fired.add(("sharing",))
    ghost.memes["warmth"] += 1
    ghost.memes["loneliness"] = max(0.0, ghost.memes["loneliness"] - 1)
    child.memes["kindness"] += 1
    out.append("Sharing made the quiet room feel less cold.")
    return out


def _r_tending(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.memes["warmth"] < THRESHOLD:
        return out
    if ("tending",) in world.fired:
        return out
    world.fired.add(("tending",))
    child.memes["bravery"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("A gentle tending beat changed the room from spooky to kind.")
    return out


CAUSAL_RULES = [
    Rule("repetition", "social", _r_repetition),
    Rule("sharing", "social", _r_sharing),
    Rule("tending", "social", _r_tending),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def startling_haunt(setting: Setting, haunt: Haunt) -> bool:
    return "rough" in haunt.roughness or "rough" in haunt.whisper


def can_share(item: SharedThing, haunt: Haunt) -> bool:
    return bool(item.shares & haunt.memes.get("needs", set())) if isinstance(haunt.memes.get("needs"), set) else True


def predict_turn(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    ghost = sim.get("ghost")
    child.meters["repeats"] += 1
    propagate(sim, narrate=False)
    child.meters["sharing"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "loneliness": sim.get("ghost").memes["loneliness"],
    }


def setup(world: World, child: Entity, ghost: Entity, setting: Setting, item: SharedThing) -> None:
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    ghost.memes["loneliness"] += 1
    ghost.memes["roughness"] += 1
    world.say(
        f"In {setting.place}, {child.id} heard a rough little sound in the hush: "
        f"{ghost.label} moving somewhere unseen."
    )
    world.say(
        f"{child.id} thought it might be a grumpy ghost, but {setting.hush} made the room feel even stranger."
    )


def repeat_and_listen(world: World, child: Entity, ghost: Entity) -> None:
    child.meters["repeats"] += 1
    world.say(
        f'{child.id} tapped on the wall, paused, and listened. Then {child.id} tapped again, just as softly.'
    )
    propagate(world, narrate=True)
    world.say(
        f'Each time, the same answer came back: a rough whisper, not a scary shout.'
    )


def misunderstanding_turn(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["misunderstanding"] += 1
    world.say(
        f"{child.id} was sure the ghost was angry, because the sound was rough and the room was so quiet."
    )


def share_and_tend(world: World, child: Entity, ghost: Entity, item: SharedThing) -> None:
    child.meters["sharing"] += 1
    world.say(
        f'{child.id} held out {item.phrase} and said, "You can share this with me if you are lonely."'
    )
    propagate(world, narrate=True)
    world.say(
        f'{ghost.label} drifted closer. The rough whisper softened into a grateful sigh.'
    )


def resolution(world: World, child: Entity, ghost: Entity, item: SharedThing) -> None:
    ghost.memes["loneliness"] = 0.0
    ghost.memes["gratitude"] += 1
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f'By the end, {child.id} knew the ghost had not been mean at all; it had only needed tending and a share.'
    )
    world.say(
        f'{child.id} left the quiet place with {item.label}, and the ghost floated on, no longer lonely.'
    )


def tell(setting: Setting, haunt: Haunt, item: SharedThing, child_name: str = "Mina") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label=child_name))
    ghost = world.add(Entity(id="ghost", kind="spirit", type="ghost", label=haunt.label))
    ghost.memes["loneliness"] = 1.0
    ghost.memes["roughness"] = 1.0
    world.add(Entity(id=item.id, kind="thing", type="blanket", label=item.label))
    world.facts.update(child=child, ghost=ghost, haunt=haunt, item=item, setting=setting)
    setup(world, child, ghost, setting, item)
    world.para()
    misunderstanding_turn(world, child, ghost)
    repeat_and_listen(world, child, ghost)
    world.para()
    share_and_tend(world, child, ghost, item)
    resolution(world, child, ghost, item)
    world.facts["resolved"] = ghost.memes["loneliness"] == 0.0
    return world


SETTINGS = {
    "attic": Setting(place="the attic", hush="Dust slept on the beams", affords={"listen", "share"}),
    "hall": Setting(place="the long hall", hush="Old boards answered with a creak", affords={"listen", "share"}),
    "cellar": Setting(place="the cellar", hush="Water dripped in the dark", affords={"listen", "share"}),
}

HAUNTS = {
    "soft_ghost": Haunt(id="soft_ghost", label="the little ghost", whisper="rough little whisper", roughness="rough", lonely="lonely"),
    "window_ghost": Haunt(id="window_ghost", label="the window ghost", whisper="rough tap at the glass", roughness="rough", lonely="lonely"),
    "toy_ghost": Haunt(id="toy_ghost", label="the toy ghost", whisper="rough breath in a box", roughness="rough", lonely="lonely"),
}

SHARABLES = {
    "blanket": SharedThing(id="blanket", label="blanket", phrase="a warm blanket", comfort="warmth", shares={"warmth"}),
    "lantern": SharedThing(id="lantern", label="lantern", phrase="a little lantern", comfort="light", shares={"light"}),
    "toy": SharedThing(id="toy", label="toy", phrase="a little toy train", comfort="play", shares={"play"}),
}

GHOST_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tess", "June", "Lia", "Rosa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HAUNTS:
            for it in SHARABLES:
                combos.append((s, h, it))
    return combos


@dataclass
class StoryParams:
    setting: str
    haunt: str
    shared: str
    child_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [("What is a ghost in a story?",
               "A ghost is a pretend spooky spirit character in a story. It is not real, and stories often use ghosts to make a mystery feel quiet and mysterious.")],
    "listen": [("Why do people pause and listen in a mystery?",
                "They pause and listen so they can notice tiny clues, like a footstep, a whisper, or a creak.")],
    "share": [("What does sharing mean?",
               "Sharing means letting someone else use or have part of something for a while.")],
    "tend": [("What does it mean to tend something?",
               "To tend something means to care for it gently and help it feel better.")],
    "rough": [("What is a rough sound?",
               "A rough sound is not smooth or soft; it may sound scratchy, hushed, or a little harsh.")],
    "blanket": [("What does a blanket do?",
                 "A blanket keeps you warm and cozy.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that can glow softly and help you see in the dark.")],
    "toy": [("Why do children share toys?",
              "Children share toys so everyone can play together and nobody feels left out.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old in {f["setting"].place} with a rough little mystery, a misunderstanding, repetition, and sharing.',
        f"Tell a quiet story where {f['child'].id} thinks {f['ghost'].label} is scary at first, then learns through repeated listening that the ghost is lonely and needs kindness.",
        f'Write a child-facing ghost story that includes the words "rough", "tend", and "share", and ends with the ghost no longer lonely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, setting, item = f["child"], f["ghost"], f["setting"], f["item"]
    qa = [
        QAItem(
            question=f"Where did {child.id} hear the rough sound?",
            answer=f"{child.id} heard it in {setting.place}, where the hush made every small sound seem spooky.",
        ),
        QAItem(
            question=f"Why did {child.id} first think {ghost.label} was scary?",
            answer=f"{child.id} misunderstood the rough whisper and thought it meant the ghost was angry, when it was really lonely.",
        ),
        QAItem(
            question=f"What did {child.id} do again and again to understand the sound?",
            answer=f"{child.id} tapped, paused, and listened again and again. The repetition turned the mystery into a clue.",
        ),
        QAItem(
            question=f"What did {child.id} share with {ghost.label}?",
            answer=f"{child.id} shared {item.phrase}, which helped the ghost feel cared for instead of alone.",
        ),
        QAItem(
            question=f"How did the story end for {ghost.label}?",
            answer=f"{ghost.label} was no longer lonely, and {child.id} understood that the ghost only needed tending and kindness.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag, pairs in KNOWLEDGE.items():
        out.extend(QAItem(question=q, answer=a) for q, a in pairs if tag in {"ghost", "listen", "share", "tend", "rough", "blanket", "lantern", "toy"})
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", haunt="soft_ghost", shared="blanket", child_name="Mina"),
    StoryParams(setting="hall", haunt="window_ghost", shared="lantern", child_name="Lena"),
    StoryParams(setting="cellar", haunt="toy_ghost", shared="toy", child_name="Ivy"),
]


def explain_rejection(setting: Setting, haunt: Haunt, item: SharedThing) -> str:
    return f"(No story: the quiet place, ghost, and shared thing do not fit this gentle ghost premise.)"


ASP_RULES = r"""
valid(S,H,I) :- setting(S), haunt(H), item(I).
misunderstanding :- rough(H), setting(S), haunt(H), item(I), valid(S,H,I).
repetition :- valid(S,H,I).
sharing :- valid(S,H,I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HAUNTS:
        lines.append(asp.fact("haunt", h))
        lines.append(asp.fact("rough", h))
    for i in SHARABLES:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with misunderstanding, repetition, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--shared", choices=SHARABLES)
    ap.add_argument("--name")
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
              and (args.haunt is None or c[1] == args.haunt)
              and (args.shared is None or c[2] == args.shared)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, haunt, shared = rng.choice(sorted(combos))
    return StoryParams(setting=setting, haunt=haunt, shared=shared, child_name=args.name or rng.choice(GHOST_NAMES))


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    haunt = HAUNTS[params.haunt]
    item = SHARABLES[params.shared]
    world = tell(setting, haunt, item, params.child_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
