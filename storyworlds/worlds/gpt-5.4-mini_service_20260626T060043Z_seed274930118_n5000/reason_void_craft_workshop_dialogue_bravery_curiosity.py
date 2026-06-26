#!/usr/bin/env python3
"""
storyworlds/worlds/reason_void_craft_workshop_dialogue_bravery_curiosity.py
===========================================================================

A small mystery storyworld set in a craft workshop, built around reason,
the void, dialogue, bravery, and curiosity.

Premise:
A child or apprentice in a craft workshop notices an impossible gap: a small
void where an important piece, tool, or clue should be. The characters talk
through the mystery, inspect the workshop, and choose a brave, careful method
to find the missing thing.

State model:
- meters: physical presence, distance, clutter, hiddenness, brightness, etc.
- memes: curiosity, worry, bravery, trust, relief, doubt, satisfaction

The story is generated from a simulated sequence:
1) introduction and the workshop mood
2) discovery of the void and cautious dialogue
3) brave search guided by reason
4) resolution when the missing object is found or the void is explained

The narrative aims for a gentle mystery tone, with concrete workshop details
and a clear ending image showing what changed.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the craft workshop"
    sound: str = "the soft tap of tools"
    light: str = "lamplight"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    reveal: str
    location: str
    hidden_start: bool = True
    guarded_by_reason: bool = False


@dataclass
class Mystery:
    id: str
    name: str
    verb: str
    search: str
    domain: str
    void_reason: str
    trail: str
    places: list[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _add_memes(ent: Entity, **kwargs) -> None:
    for k, v in kwargs.items():
        ent.memes[k] = ent.memes.get(k, 0.0) + v


def _add_meters(ent: Entity, **kwargs) -> None:
    for k, v in kwargs.items():
        ent.meters[k] = ent.meters.get(k, 0.0) + v


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("curiosity", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meters(e, search_drive=1.0)
        out.append(f"{e.id} leaned closer, because the gap in the shelf did not make sense.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("bravery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meters(e, steadiness=1.0)
        out.append(f"{e.id} took a slow breath and kept looking instead of turning away.")
    return out


def _r_reason(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reason_seen"):
        return out
    if world.facts.get("clue_found"):
        world.facts["reason_seen"] = True
        out.append("The mystery began to make sense.")
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("clue_found") or world.facts.get("resolved"):
        return out
    world.facts["resolved"] = True
    for e in world.characters():
        _add_memes(e, relief=1.0, doubt=-0.5)
    out.append("The missing thing was found, and the empty place was no longer strange.")
    return out


RULES = [_r_curiosity, _r_bravery, _r_reason, _r_resolve]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            msgs = rule(world)
            if msgs:
                changed = True
                out.extend(msgs)
    if narrate:
        for msg in out:
            world.say(msg)
    return out


def reasonableness_gate(mystery: Mystery, clue: Clue) -> bool:
    if clue.location not in mystery.places:
        return False
    if mystery.domain != "craft workshop":
        return False
    return True


def predict_resolution(world: World, mystery: Mystery, clue: Clue, seeker: Entity) -> bool:
    sim = world.copy()
    sim.facts["clue_found"] = True
    propagate(sim, narrate=False)
    return bool(sim.facts.get("resolved"))


def _build_dialogue(world: World, seeker: Entity, helper: Entity, mystery: Mystery, clue: Clue) -> None:
    world.say(
        f'"What do you think happened to the {mystery.name}?" {seeker.id} asked.'
    )
    world.say(
        f'"Let us use reason," {helper.id} said. "A void is not magic; it usually means something moved, hid, or fell."'
    )
    world.say(
        f'{seeker.id} nodded, and {seeker.pronoun().capitalize()} looked from the empty spot to the floor again.'
    )


def _search(world: World, seeker: Entity, helper: Entity, mystery: Mystery, clue: Clue) -> None:
    _add_memes(seeker, curiosity=1.0, bravery=1.0)
    _add_memes(helper, trust=1.0)
    world.say(
        f"They searched the {world.setting.place} slowly, following {mystery.search}."
    )
    world.say(
        f'{seeker.id} checked {mystery.trail}, while {helper.id} lifted paper scraps and peered behind jars of buttons.'
    )
    propagate(world, narrate=True)
    if predict_resolution(world, mystery, clue, seeker):
        world.facts["clue_found"] = True
        world.say(
            f'At last, {seeker.id} spotted the {clue.label} where nobody had looked first.'
        )
        world.say(
            f'It had been tucked at {clue.location}, and that made the empty space understandable.'
        )


def tell(setting: Setting, mystery: Mystery, clue: Clue, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    seeker = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    clue_ent = world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        hidden=clue.hidden_start,
    ))

    world.facts.update(mystery=mystery, clue=clue, seeker=seeker, helper=helper, clue_ent=clue_ent)

    world.say(
        f"In the {setting.place}, {setting.sound} rode under the warm {setting.light}."
    )
    world.say(
        f"{seeker.id} noticed a small void where {mystery.name} should have been."
    )
    world.say(
        f'The empty place felt odd, like a missing note in a familiar song.'
    )
    world.para()
    _build_dialogue(world, seeker, helper, mystery, clue)
    world.para()
    _search(world, seeker, helper, mystery, clue)
    world.para()
    if world.facts.get("clue_found"):
        _add_memes(seeker, relief=1.0, satisfaction=1.0)
        _add_memes(helper, satisfaction=1.0)
        world.say(
            f"With the {clue.label} back in view, the workshop felt whole again."
        )
        world.say(
            f"{seeker.id} smiled, because bravery had turned a puzzling void into a solved mystery."
        )
    else:
        world.say(
            f"The search ended with thoughtful faces and better questions than before."
        )
    return world


SETTINGS = {
    "craft_workshop": Setting(
        place="the craft workshop",
        sound="the soft tap of scissors and glue sticks",
        light="lamplight",
        affords={"search", "dialogue"},
    )
}

MYSTERIES = {
    "missing_button": Mystery(
        id="missing_button",
        name="missing button",
        verb="vanish",
        search="the buttons, ribbons, and cloth scraps",
        domain="craft workshop",
        void_reason="someone had sorted the supplies into a new tin",
        trail="the edge of the sewing table and the ribbon basket",
        places=["the ribbon basket", "the sorting tin", "the sewing table"],
        tags={"reason", "void", "dialogue", "bravery", "curiosity"},
    ),
    "lost_stamp": Mystery(
        id="lost_stamp",
        name="lost stamp",
        verb="disappear",
        search="the stamp tray, ink pads, and paper stacks",
        domain="craft workshop",
        void_reason="the stamp rolled under a tray of paper",
        trail="the ink pad corner and the paper stack",
        places=["under the paper tray", "the stamp tray", "the ink corner"],
        tags={"reason", "void", "dialogue", "bravery", "curiosity"},
    ),
    "hidden_key": Mystery(
        id="hidden_key",
        name="little brass key",
        verb="hide",
        search="the hooks, drawers, and string bundles",
        domain="craft workshop",
        void_reason="it slipped into a drawer with thread",
        trail="the hook wall and the thread drawer",
        places=["the thread drawer", "the hook wall", "the workbench drawer"],
        tags={"reason", "void", "dialogue", "bravery", "curiosity"},
    ),
}

CLUES = {
    "missing_button": Clue(
        id="button",
        label="button",
        phrase="a tiny blue button",
        kind="button",
        reveal="It matched the yarn on the shelf.",
        location="the ribbon basket",
        hidden_start=True,
    ),
    "lost_stamp": Clue(
        id="stamp",
        label="wooden stamp",
        phrase="a small wooden stamp with a star on it",
        kind="stamp",
        reveal="It had rolled into a safe corner.",
        location="under the paper tray",
        hidden_start=True,
    ),
    "hidden_key": Clue(
        id="key",
        label="brass key",
        phrase="a little brass key with a round head",
        kind="key",
        reveal="It had slipped into the thread drawer.",
        location="the thread drawer",
        hidden_start=True,
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Lina", "Tara", "Ivy", "June"]
BOY_NAMES = ["Owen", "Ezra", "Milo", "Arlo", "Theo", "Kai"]
HELPER_NAMES = ["Ada", "Mina", "Noel", "Pia", "Rae", "Luca"]


@dataclass
class StoryParams:
    mystery: str
    clue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle craft-workshop mystery storyworld.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid, myst in MYSTERIES.items():
        for cid, clue in CLUES.items():
            if reasonableness_gate(myst, clue):
                out.append((mid, cid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.mystery and args.clue:
        if (args.mystery, args.clue) not in combos:
            raise StoryError("That mystery and clue do not fit the craft-workshop logic.")
    options = [c for c in combos if (args.mystery is None or c[0] == args.mystery) and (args.clue is None or c[1] == args.clue)]
    if not options:
        raise StoryError("No valid mystery matches those options.")

    mystery_id, clue_id = rng.choice(sorted(options))
    myst = MYSTERIES[mystery_id]
    clue = CLUES[clue_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        mystery=mystery_id,
        clue=clue_id,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    c: Clue = world.facts["clue"]
    s: Entity = world.facts["seeker"]
    h: Entity = world.facts["helper"]
    return [
        f"Write a gentle mystery set in a craft workshop where a child notices a void and asks careful questions.",
        f"Tell a story where {s.id} and {h.id} use dialogue, curiosity, and bravery to solve the mystery of the {m.name}.",
        f"Write a short child-friendly mystery that ends with the {c.label} found and the workshop feeling whole again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    c: Clue = world.facts["clue"]
    s: Entity = world.facts["seeker"]
    h: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"What strange thing did {s.id} notice in the workshop?",
            answer=f"{s.id} noticed a small void where the {m.name} should have been.",
        ),
        QAItem(
            question=f"What did {s.id} and {h.id} do instead of panicking?",
            answer=f"They talked it through, used reason, and searched carefully with curiosity and bravery.",
        ),
        QAItem(
            question=f"What was the missing thing in the mystery?",
            answer=f"The missing thing was {c.phrase}.",
        ),
        QAItem(
            question=f"Where was the {c.label} found?",
            answer=f"It was found at {c.location}, which explained the empty space.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a void?",
            answer="A void is an empty place or a gap where something seems to be missing.",
        ),
        QAItem(
            question="What does curiosity help people do?",
            answer="Curiosity helps people ask questions and look closely so they can learn what is going on.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something careful and hard even when you feel a little worried.",
        ),
        QAItem(
            question="Why do people use reason?",
            answer="People use reason to think clearly, compare clues, and choose a sensible answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is compatible when the clue belongs in the same workshop places.
compatible(M, C) :- mystery(M), clue(C), place_of(C, P), place(M, P).

% Bravery and curiosity should be present for the story to be worth telling.
storyworthy(M, C) :- compatible(M, C), has_tag(M, reason), has_tag(M, void),
                     has_tag(M, dialogue), has_tag(M, bravery), has_tag(M, curiosity).

#show compatible/2.
#show storyworthy/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("place", mid, m.domain))
        for p in m.places:
            lines.append(asp.fact("place_of", mid, p))
        for t in sorted(m.tags):
            lines.append(asp.fact("has_tag", mid, t))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("place_of", cid, c.location))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show storyworthy/2."))
    return sorted(set(asp.atoms(model, "storyworthy")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS["craft_workshop"],
        MYSTERIES[params.mystery],
        CLUES[params.clue],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
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


CURATED = [
    StoryParams("missing_button", "button", "Mira", "girl", "Noel", "boy"),
    StoryParams("lost_stamp", "stamp", "Owen", "boy", "Ada", "girl"),
    StoryParams("hidden_key", "key", "Ivy", "girl", "Luca", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show storyworthy/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible mystery/clue pairs ({len(stories)} storyworthy):\n")
        for mid, cid in combos:
            print(f"  {mid:14} {cid}")
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
            header = f"### {p.hero_name}: {p.mystery} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
