#!/usr/bin/env python3
"""
storyworlds/worlds/knife_lesson_learned_flashback_mystery.py
============================================================

A small mystery storyworld about a missing kitchen knife, a helpful flashback,
and a lesson learned about asking before using sharp tools.

Seed premise:
- A child notices a knife is gone from the knife block.
- The story uses a flashback to explain where the knife was last seen.
- The mystery is small and safe: the knife is found in a sensible place.
- The ending proves the lesson learned through changed state.

The world tracks typed entities with physical meters and emotional memes.
It uses a reasonableness gate and an inline ASP twin, plus verification.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    scene: str
    places: set[str] = field(default_factory=set)


@dataclass
class Knife:
    id: str
    label: str
    phrase: str
    sharp: bool = True
    safe_place: str = "the drawer"
    type: str = "knife"
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    lesson: str
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _initial(meters=None, memes=None):
    return dict(meters or {}, memes or {})


def _ensure(entity: Entity, keys: list[str]) -> None:
    for k in keys:
        entity.meters.setdefault(k, 0.0)
        entity.memes.setdefault(k, 0.0)


def _r_notice_missing(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    knife = world.get("knife")
    if knife.meters["missing"] >= THRESHOLD and ("noticed", "missing") not in world.fired:
        world.fired.add(("noticed", "missing"))
        child.memes["worry"] += 1
        out.append(f"{child.id} noticed that {knife.label} was not where it belonged.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["worry"] >= THRESHOLD and ("flashback",) not in world.fired:
        world.fired.add(("flashback",))
        child.memes["curiosity"] += 1
        out.append("__flashback__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    knife = world.get("knife")
    clue = world.get("clue")
    if clue.meters["revealed"] >= THRESHOLD and knife.meters["missing"] >= THRESHOLD:
        if ("found",) not in world.fired:
            world.fired.add(("found",))
            knife.meters["missing"] = 0.0
            knife.location = clue.location
            out.append(f"The clue led straight to the {clue.label}.")
    return out


CAUSAL_RULES = [_r_notice_missing, _r_flashback, _r_found]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue in CLUES:
            if setting == "kitchen" and clue in {"sink", "counter", "garden"}:
                combos.append((setting, clue))
            if setting == "shed" and clue in {"workbench", "toolbox"}:
                combos.append((setting, clue))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    child: str
    adult: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="kitchen", clue="sink", child="Mina", adult="mother"),
    StoryParams(setting="kitchen", clue="counter", child="Theo", adult="father"),
    StoryParams(setting="shed", clue="workbench", child="Lia", adult="uncle"),
]


SETTINGS = {
    "kitchen": Setting(place="the kitchen", scene="a warm room with a blue tile floor", places={"sink", "counter", "drawer"}),
    "shed": Setting(place="the shed", scene="a little back shed with dusty shelves", places={"workbench", "toolbox", "hook"}),
}

CLUES = {
    "sink": Clue(id="sink", label="sink", phrase="the sink by the window", location="the sink", tags={"water", "kitchen"}),
    "counter": Clue(id="counter", label="counter", phrase="the counter near the bowl of apples", location="the counter", tags={"kitchen"}),
    "garden": Clue(id="garden", label="garden door", phrase="the garden door", location="the garden door", tags={"outside"}),
    "workbench": Clue(id="workbench", label="workbench", phrase="the workbench with the wooden board", location="the workbench", tags={"shed"}),
    "toolbox": Clue(id="toolbox", label="toolbox", phrase="the old toolbox", location="the toolbox", tags={"shed"}),
}

KNIFE = Knife(id="knife", label="knife", phrase="a small kitchen knife", safe_place="the drawer", tags={"sharp", "kitchen"})
LESSON = Lesson(id="lesson", lesson="Sharp things belong with grown-ups", action="asked first", tags={"lesson"})


GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Theo", "Ben", "Owen", "Finn", "Noah"]
ADULTS = ["mother", "father", "aunt", "uncle"]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.places):
            lines.append(asp.fact("has_place", sid, p))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("located_at", cid, c.location.replace("the ", "")))
    lines.append(asp.fact("knife", "knife"))
    lines.append(asp.fact("sharp", "knife"))
    lines.append(asp.fact("safe_place", "knife", KNIFE.safe_place.replace("the ", "")))
    return "\n".join(lines)


ASP_RULES = r"""
mystery(Setting, Clue) :- setting(Setting), clue(Clue), has_place(Setting, Clue).
missing_knife :- sharp(knife).
revealed(Clue) :- located_at(Clue, sink).
lesson_learned :- missing_knife, revealed(sink).
#show mystery/2.
#show lesson_learned/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_gate() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery/2."))
    aps = sorted(set(asp.atoms(model, "mystery")))
    py = sorted((s, c) for s, c in valid_combos())
    return aps == py


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about a missing knife, a flashback, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--child")
    ap.add_argument("--adult", choices=ADULTS)
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
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("No valid mystery combination matches the chosen options.")
    setting, clue = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(setting=setting, clue=clue, child=child, adult=adult)


def tell(setting: Setting, clue: Clue, child: str, adult: str) -> World:
    world = World(setting)
    child_ent = world.add(Entity(id="child", kind="character", type="girl" if child in GIRL_NAMES else "boy", label=child))
    adult_ent = world.add(Entity(id="adult", kind="character", type=adult, label=f"the {adult}"))
    knife = world.add(Entity(id="knife", type="knife", label="knife", owner=adult_ent.id, location=KNIFE.safe_place, tags=set(KNIFE.tags)))
    clue_ent = world.add(Entity(id="clue", type="place", label=clue.label, location=clue.location, tags=set(clue.tags)))
    _ensure(child_ent, ["worry", "curiosity", "trust"])
    _ensure(adult_ent, ["calm", "lesson"])
    _ensure(knife, ["missing"])
    _ensure(clue_ent, ["revealed"])

    child_ent.memes["worry"] = 0.0
    knife.meters["missing"] = 1.0
    child_ent.memes["trust"] = 1.0
    clue_ent.meters["revealed"] = 0.0

    world.say(f"{setting.scene.capitalize()}. {child} was helping near {setting.place} when they noticed the knife block was uneven.")
    world.say(f"{child} remembered a strange little clue from earlier: {clue.phrase}.")
    world.para()
    world.say(f"That memory came back like a flashback. The last time anyone had seen the knife, it was near {clue.phrase}.")
    child_ent.meters["thinking"] = 1.0
    clue_ent.meters["revealed"] = 1.0
    propagate(world, narrate=False)
    if knife.meters["missing"] >= THRESHOLD:
        world.say(f"{child} asked {adult_ent.label_word} before touching anything sharp.")
    propagate(world)
    if knife.location == clue.location:
        world.para()
        world.say(f"The knife was found safely at {clue.phrase}, and {adult_ent.label_word} smiled because {child} had remembered the lesson.")
        child_ent.memes["lesson"] = 1.0
        child_ent.memes["pride"] = 1.0
        adult_ent.memes["relief"] = 1.0
        world.say(f"{LESSON.lesson}. {child} had {LESSON.action} after that, and the mystery was solved.")
    world.facts.update(child=child_ent, adult=adult_ent, knife=knife, clue=clue_ent, setting=setting, clue_cfg=clue, child_name=child, adult_name=adult)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about a missing knife in {f["setting"].place}. Include a flashback and a gentle lesson learned.',
        f"Tell a simple story where {f['child_name']} finds a clue, remembers where the knife was last seen, and asks {f['adult_name']} before using anything sharp.",
        f'Write a child-friendly mystery with the words "knife" and "flashback" that ends with a lesson learned about sharp tools.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    clue = f["clue_cfg"]
    knife = f["knife"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What mystery did {f['child_name']} notice in {setting.place}?",
            answer=f"{f['child_name']} noticed that the knife was missing from where it belonged. That small mystery made the room feel puzzling for a moment.",
        ),
        QAItem(
            question=f"What did the flashback help {f['child_name']} remember?",
            answer=f"The flashback helped {f['child_name']} remember the knife had last been seen near {clue.phrase}. That clue gave the story a safe way to solve the mystery.",
        ),
        QAItem(
            question=f"How was the knife found?",
            answer=f"It was found safely at {clue.phrase}. {f['adult_name']} and {f['child_name']} used the clue instead of guessing.",
        ),
        QAItem(
            question=f"What lesson did {f['child_name']} learn?",
            answer=f"{LESSON.lesson}. After that, {f['child_name']} had {LESSON.action} before touching any sharp tool.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Why should children ask before using a knife?", answer="A knife is sharp, so children should ask a grown-up before using one. That helps keep hands safe."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is when a story briefly shows something that happened earlier. It helps explain a clue or a memory."),
        QAItem(question="What is a mystery story?", answer="A mystery story is a story where someone notices a puzzling clue and figures out what happened."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.child, params.adult)
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


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    ok_gate = asp_verify_gate()
    smoke = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    ok_story = bool(smoke.story and smoke.world is not None)
    if ok_gate and ok_story:
        print("OK: ASP gate matches Python and smoke test generation works.")
        return 0
    if not ok_gate:
        print("MISMATCH: ASP gate does not match Python valid_combos().")
    if not ok_story:
        print("MISMATCH: story generation smoke test failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/2.\n#show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} mystery combos:")
        for setting, clue in combos:
            print(f"  {setting:8} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
