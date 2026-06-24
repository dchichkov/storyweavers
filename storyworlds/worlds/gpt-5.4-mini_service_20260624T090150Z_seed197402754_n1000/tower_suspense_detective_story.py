#!/usr/bin/env python3
"""
storyworlds/worlds/tower_suspense_detective_story.py
====================================================

A small storyworld about a young detective, a tall tower, and a suspenseful
mystery that resolves through observation rather than danger.

Seed image:
---
A child detective hears a strange sound in a tower at dusk. The old tower is
locked, the caretaker is worried, and somebody seems to have taken the brass key.
The detective follows clues, notices a hidden message, and discovers that the
"mystery thief" is only a helpful pigeon carrying the key to a nest. The tower
bell rings, the caretaker relaxes, and the detective leaves with a satisfying
answer.

World model:
---
- Characters have emotional memes and physical meters.
- Suspense grows when the tower is dark, the clue is missing, and the caretaker
  cannot open the door.
- The detective can inspect places, collect clues, and deduce the answer.
- The story ends when the key is found and the tower is safely opened.

This script follows the storyworld contract:
- self-contained stdlib script
- eager results import
- lazy ASP import inside helpers
- parser / parameter resolution / generate / emit / main
- --verify compares ASP/Python parity and exercises stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SUSPENSE_THRESHOLD = 1.0
DETECTIVE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "location"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "caretaker"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old tower"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    leads_to: str
    reveal: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    detective_name: str
    detective_type: str
    caretaker_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "dusk": Setting(place="the old tower at dusk", indoors=True, affords={"inspect", "listen", "climb"}),
    "night": Setting(place="the old tower at night", indoors=True, affords={"inspect", "listen", "climb"}),
    "rain": Setting(place="the old tower in the rain", indoors=True, affords={"inspect", "listen", "climb"}),
}

CLUES = {
    "key": Clue(
        id="key",
        label="brass key",
        phrase="a small brass key on a blue ribbon",
        leads_to="nest",
        reveal="a pigeon nest tucked in the stair rafters",
    ),
    "note": Clue(
        id="note",
        label="folded note",
        phrase="a folded note with a sketch of the tower stair",
        leads_to="loft",
        reveal="a loose loft board hiding the truth",
    ),
    "feather": Clue(
        id="feather",
        label="gray feather",
        phrase="a soft gray feather caught on a nail",
        leads_to="ledge",
        reveal="a narrow ledge outside the bell window",
    ),
}

DETECTIVE_NAMES = ["Mina", "Theo", "Iris", "Nico", "Lina", "Jasper"]
DETECTIVE_TYPES = ["girl", "boy"]
CARETAKER_TYPES = ["caretaker", "watchman", "guard"]


def valid_combos() -> list[tuple[str, str]]:
    return [(setting_id, clue_id) for setting_id in SETTINGS for clue_id in CLUES]


def reasonableness_gate(setting_id: str, clue_id: str) -> bool:
    return setting_id in SETTINGS and clue_id in CLUES


def explain_rejection(setting_id: str, clue_id: str) -> str:
    return f"(No story: the setting '{setting_id}' and clue '{clue_id}' do not make a workable tower mystery.)"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        meters={"courage": 0.0, "focus": 0.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "confidence": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=params.caretaker_type,
        label="the caretaker",
        meters={"worry": 1.0},
        memes={"worry": 1.0, "relief": 0.0},
    ))
    key = world.add(Entity(
        id="Key",
        type="key",
        label=clue.label,
        phrase=clue.phrase,
        owner="Caretaker",
        carried_by=None,
        hidden_in=clue.leads_to,
    ))
    tower = world.add(Entity(
        id="Tower",
        kind="location",
        type="tower",
        label="the old tower",
        meters={"dark": 1.0, "quiet": 1.0},
        memes={"mystery": 1.0},
    ))

    world.facts.update(
        detective=detective,
        caretaker=caretaker,
        key=key,
        tower=tower,
        clue=clue,
        setting=setting,
    )
    return world


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get(world.facts["detective"].id)
    caretaker = world.get("Caretaker")
    tower = world.get("Tower")
    if detective.memes["curiosity"] >= SUSPENSE_THRESHOLD and tower.meters["dark"] >= 1.0:
        sig = ("suspense", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["suspense"] += 1.0
            out.append(f"The tower felt strange, and {detective.label} knew a mystery was waiting.")
    if caretaker.memes["worry"] >= 1.0 and world.facts["Key"].carried_by is None:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            caretaker.memes["worry"] += 0.5
            out.append("That made the caretaker even more uneasy.")
    return out


def _r_deduction(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get(world.facts["detective"].id)
    key = world.facts["Key"]
    if detective.meters["focus"] >= DETECTIVE_THRESHOLD and key.hidden_in and ("deduce", key.hidden_in) not in world.fired:
        world.fired.add(("deduce", key.hidden_in))
        detective.memes["confidence"] += 1.0
        out.append(f"{detective.label} saw how the clues fit together.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_suspense, _r_deduction):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def inspect(world: World, actor: Entity, clue: Clue) -> None:
    actor.meters["focus"] += 1.0
    actor.meters["courage"] += 0.5
    world.say(f"{actor.label} leaned closer and noticed {clue.phrase}.")
    propagate(world)


def listen(world: World, actor: Entity) -> None:
    actor.meters["focus"] += 1.0
    actor.memes["curiosity"] += 0.5
    world.say(f"{actor.label} held still and listened to the tower's quiet creaks.")
    propagate(world)


def climb(world: World, actor: Entity, clue: Clue) -> None:
    actor.meters["courage"] += 1.0
    actor.meters["focus"] += 1.0
    world.say(f"{actor.label} climbed the narrow stairs one careful step at a time.")
    if clue.leads_to == "nest":
        world.say("Near the rafters, a pigeon fluttered up from a warm nest.")
        world.facts["Key"].carried_by = "Pigeon"
        world.facts["Key"].hidden_in = None
        world.say("In the nest sat the brass key on a blue ribbon, exactly where the clues led.")
    elif clue.leads_to == "loft":
        world.say("Behind a loose board, the detective found the brass key tucked safely away.")
        world.facts["Key"].carried_by = actor.id
        world.facts["Key"].hidden_in = None
    else:
        world.say("On a narrow ledge, the detective spotted the brass key shining in the dim light.")
        world.facts["Key"].carried_by = actor.id
        world.facts["Key"].hidden_in = None
    propagate(world)


def open_tower(world: World, detective: Entity, caretaker: Entity) -> None:
    key = world.facts["Key"]
    if key.carried_by not in {detective.id, "Pigeon"}:
        raise StoryError("The tower cannot be opened until the key is found.")
    caretaker.memes["worry"] = 0.0
    caretaker.memes["relief"] = 1.0
    detective.memes["confidence"] += 1.0
    world.say(f"{detective.label} held up the brass key, and the caretaker let out a long breath.")
    world.say("The old tower door opened with a soft click, and the suspense melted away.")
    if key.carried_by == "Pigeon":
        world.say("The pigeon hopped onto the sill as if it had solved the case all along.")
    else:
        world.say("At the end, the key was safe in the detective's hand, and the tower was open at last.")


def tell(setting: Setting, clue: Clue, detective_name: str, detective_type: str, caretaker_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label=detective_name,
        meters={"courage": 0.0, "focus": 0.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "confidence": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        label="the caretaker",
        meters={"worry": 1.0},
        memes={"worry": 1.0, "relief": 0.0},
    ))
    key = world.add(Entity(
        id="Key",
        type="key",
        label=clue.label,
        phrase=clue.phrase,
        owner="Caretaker",
        carried_by=None,
        hidden_in=clue.leads_to,
    ))
    tower = world.add(Entity(
        id="Tower",
        kind="location",
        type="tower",
        label="the old tower",
        meters={"dark": 1.0, "quiet": 1.0},
        memes={"mystery": 1.0},
    ))
    world.facts.update(detective=detective, caretaker=caretaker, key=key, tower=tower, clue=clue)

    world.say(f"{detective.label} was a little {detective_type} detective who loved solving quiet mysteries.")
    world.say(f"One evening, {detective.label} came to {setting.place}, where the old tower stood in the dim light.")
    world.say(f"The caretaker looked worried because the {clue.label} was missing and the tower door would not open.")

    world.para()
    inspect(world, detective, clue)
    listen(world, detective)
    world.say("The clue seemed small, but the detective knew small things could point to big answers.")
    world.say(f"{detective.label} followed the clue deeper into the tower.")

    world.para()
    climb(world, detective, clue)
    open_tower(world, detective, caretaker)

    world.para()
    world.say(f"In the end, {detective.label} walked away with a clear answer and a calmer heart.")
    world.say(f"The tower was no longer frightening; it was just a quiet old building with a solved mystery.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        f'Write a suspenseful detective story for a young child set in {setting.place} with a tower mystery and the clue "{clue.label}".',
        f"Tell a short detective story where {detective.label} follows a clue through an old tower and finds a gentle answer.",
        f"Write a child-friendly suspense story in which a detective notices a hidden clue in a tower and solves the problem calmly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    caretaker = f["caretaker"]
    clue = f["clue"]
    key = f["key"]
    qa = [
        QAItem(
            question=f"Who solved the mystery in the tower?",
            answer=f"{detective.label} solved it by following the clue carefully and not rushing past the evidence.",
        ),
        QAItem(
            question=f"Why was the caretaker worried at the beginning?",
            answer=f"The caretaker was worried because the {clue.label} was missing, so the tower could not be opened right away.",
        ),
        QAItem(
            question=f"What did the detective find when the clues led upward?",
            answer=f"The detective found the brass key, which had been hidden where the clues pointed.",
        ),
        QAItem(
            question=f"How did the story end for the caretaker?",
            answer=f"The caretaker felt relief when the key was found and the tower door opened safely.",
        ),
    ]
    if key.carried_by == "Pigeon":
        qa.append(
            QAItem(
                question="Who was carrying the key at the surprising moment?",
                answer="A helpful pigeon was carrying it, which made the mystery feel startling at first and gentle at the end.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tower?",
            answer="A tower is a tall building that reaches upward above the smaller buildings around it.",
        ),
        QAItem(
            question="Why can a mystery feel suspenseful?",
            answer="A mystery feels suspenseful when important information is missing and you want to find out what will happen next.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and uses evidence to figure out what happened.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("leads_to", cid, clue.leads_to))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, C) :- setting(S), clue(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        sample = resolve_params(argparse.Namespace(setting=None, clue=None, detective_name=None, detective_type=None, caretaker_type=None), random.Random(7))
        _ = generate(sample)
        print("OK: generated story exercised during verification.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful detective story world set around a tower.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", dest="detective_name")
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
    ap.add_argument("--caretaker-type", choices=CARETAKER_TYPES)
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
    if args.setting and args.clue and not reasonableness_gate(args.setting, args.clue):
        raise StoryError(explain_rejection(args.setting, args.clue))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid tower mystery matches the given options.)")
    setting, clue = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        detective_name=args.detective_name or rng.choice(DETECTIVE_NAMES),
        detective_type=args.detective_type or rng.choice(DETECTIVE_TYPES),
        caretaker_type=args.caretaker_type or rng.choice(CARETAKER_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        params.detective_name,
        params.detective_type,
        params.caretaker_type,
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue) combos:\n")
        for s, c in combos:
            print(f"  {s:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for sid in SETTINGS:
            for cid in CLUES:
                p = StoryParams(
                    setting=sid,
                    clue=cid,
                    detective_name=DETECTIVE_NAMES[0],
                    detective_type=DETECTIVE_TYPES[0],
                    caretaker_type=CARETAKER_TYPES[0],
                )
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.detective_name}: {p.clue} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
