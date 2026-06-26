#!/usr/bin/env python3
"""
storyworlds/worlds/lanky_refraction_mortar_foreshadowing_mystery.py
====================================================================

A small mystery storyworld about a lanky child detective, strange refraction,
crumbly mortar, and a foreshadowed reveal.

The seed image:
---
A lanky child notices a strange bend of light in an old room. The refraction
seems to point at a wall where the mortar is cracked. A hidden clue waits
behind the brick, and earlier odd details suddenly make sense.

This world implements that premise as a tiny, state-driven mystery:
- the detective follows a light-based clue,
- the clue leads to a loose brick in mortar,
- a foreshadowed object is found,
- the ending proves what changed.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: Optional[str] = None
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    has_light: bool = True
    has_wall: bool = True


@dataclass
class Clue:
    id: str
    label: str
    source: str
    effect: str
    reveal: str
    requires_light: bool = False
    requires_mortar: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    hidden_by: str
    hidden_in: str
    type: str = "thing"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    object: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, has_light=True, has_wall=True),
    "hallway": Setting(place="the hallway", indoor=True, has_light=True, has_wall=True),
    "courtyard": Setting(place="the courtyard", indoor=False, has_light=True, has_wall=True),
    "workshop": Setting(place="the workshop", indoor=True, has_light=True, has_wall=True),
}

CLUES = {
    "prism": Clue(
        id="prism",
        label="a small glass prism",
        source="a beam of sun",
        effect="The light broke into a bright stripe and bent across the floor.",
        reveal="The stripe pointed straight at the loose brick.",
        requires_light=True,
        tags={"light", "glass", "refraction"},
    ),
    "mirror": Clue(
        id="mirror",
        label="a tilted mirror",
        source="a lamp",
        effect="The lamp light skipped off the mirror and flashed onto the wall.",
        reveal="The flash marked a patch of crumbling mortar.",
        requires_light=True,
        tags={"light", "reflection"},
    ),
    "window": Clue(
        id="window",
        label="a dusty windowpane",
        source="the afternoon light",
        effect="The light bent through the old glass and made a crooked shine.",
        reveal="The shine landed on a brick with a cracked edge.",
        requires_light=True,
        tags={"light", "refraction", "glass"},
    ),
}

OBJECTS = {
    "compass": MysteryObject(
        id="compass",
        label="a brass compass",
        phrase="a brass compass with a green ribbon",
        hidden_by="the loose brick",
        hidden_in="mortar",
    ),
    "note": MysteryObject(
        id="note",
        label="a folded note",
        phrase="a folded note with a smudged stamp",
        hidden_by="the cracked mortar",
        hidden_in="mortar",
    ),
    "key": MysteryObject(
        id="key",
        label="an old key",
        phrase="an old key wrapped in cloth",
        hidden_by="the loose brick",
        hidden_in="mortar",
    ),
}

GIRL_NAMES = ["Mina", "Clara", "Ivy", "Nora", "Lena", "Maya", "June"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Owen", "Luca", "Noah", "Miles"]
TRAITS = ["lanky", "curious", "quiet", "careful", "brave", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for obj in OBJECTS:
                combos.append((place, clue, obj))
    return combos


def reasonableness_gate(setting: Setting, clue: Clue, obj: MysteryObject) -> bool:
    return setting.has_wall and clue.requires_light


def explain_rejection(setting: Setting, clue: Clue, obj: MysteryObject) -> str:
    return (
        f"(No story: {clue.label} needs a lit place with a wall, and {setting.place} "
        f"does not make that mystery readable.)"
    )


@dataclass
class StoryState:
    detective: Entity
    parent: Entity
    clue: Entity
    object: Entity
    setting: Setting
    clue_def: Clue
    object_def: MysteryObject
    saw_refraction: bool = False
    found_object: bool = False
    foreshadowed: bool = False


def introduce(world: World, state: StoryState) -> None:
    d = state.detective
    world.say(
        f"{d.id} was a {d.trait if hasattr(d, 'trait') else 'lanky'} child who noticed little things."
    )


def narrate_setup(world: World, state: StoryState) -> None:
    d, p = state.detective, state.parent
    world.say(
        f"{d.id} loved quiet mysteries, and {p.pronoun('possessive')} pocket held a flashlight that never stayed put for long."
    )
    world.say(
        f"On that day, {d.id} and {p.id} were in {world.setting.place}, where old walls kept their secrets close."
    )
    world.say(
        f"Before anything strange happened, {d.id} noticed {state.clue_def.label} near the window."
    )


def foreshadow(world: World, state: StoryState) -> None:
    d = state.detective
    state.foreshadowed = True
    world.say(
        f"At first it seemed unimportant, but a thin line of light bent strangely and slipped across the floor."
    )
    world.say(
        f"{d.id} remembered that odd shine later, because it was the first hint of refraction."
    )


def inspect_clue(world: World, state: StoryState) -> None:
    if not state.clue_def.requires_light:
        return
    state.saw_refraction = True
    world.say(state.clue_def.effect)
    world.say(state.clue_def.reveal)


def discover_object(world: World, state: StoryState) -> None:
    obj = state.object
    obj.found = True
    state.found_object = True
    world.say(
        f"{state.detective.id} knelt by the wall and brushed away the old mortar until a hidden space opened."
    )
    world.say(
        f"Inside, {state.detective.id} found {obj.phrase}."
    )
    world.say(
        f"So the strange light had not been a mistake; it had been foreshadowing."
    )


def resolve(world: World, state: StoryState) -> None:
    d, p, obj = state.detective, state.parent, state.object
    d.memes["mystery_solved"] = d.memes.get("mystery_solved", 0) + 1
    d.memes["pride"] = d.memes.get("pride", 0) + 1
    world.say(
        f"{d.id} held up {obj.phrase} and smiled, because the clues finally fit together."
    )
    world.say(
        f"{p.id} laughed softly and said the old wall had been hiding the answer all along."
    )
    world.say(
        f"By the end, the loose mortar was only dust, and the little mystery was no longer lost."
    )


def tell(setting: Setting, clue_def: Clue, obj_def: MysteryObject, *,
         name: str = "Mina", gender: str = "girl", parent_type: str = "mother",
         trait: str = "lanky") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["lanky", trait],
    ))
    detective.trait = trait  # small convenience for narration
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    clue = world.add(Entity(id=clue_def.id, type="thing", label=clue_def.label))
    obj = world.add(Entity(id=obj_def.id, type=obj_def.type, label=obj_def.label, phrase=obj_def.phrase))
    state = StoryState(detective=detective, parent=parent, clue=clue, object=obj, setting=setting, clue_def=clue_def, object_def=obj_def)

    world.say(f"{detective.id} was a lanky child who liked puzzles and quiet corners.")
    world.say(
        f"{detective.id} had a habit of staring at light until even small changes looked important."
    )
    world.para()
    narrate_setup(world, state)
    foreshadow(world, state)
    world.para()
    inspect_clue(world, state)
    discover_object(world, state)
    world.para()
    resolve(world, state)

    world.facts.update(
        detective=detective,
        parent=parent,
        clue=clue_def,
        object=obj_def,
        setting=setting,
        state=state,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue"]
    obj = f["object"]
    return [
        f'Write a short mystery for a young child about a {detective.trait} detective who notices {clue.label}.',
        f"Tell a gentle story where refraction leads {detective.id} to a hidden {obj.label} in mortar.",
        f'Write a child-friendly mystery that uses the words "lanky", "refraction", and "mortar".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    parent = f["parent"]
    clue = f["clue"]
    obj = f["object"]
    setting = f["setting"]
    state = f["state"]
    qa = [
        QAItem(
            question=f"Who was the mystery about?",
            answer=f"It was about {detective.id}, a lanky child who liked puzzles, and {parent.id}, who stayed nearby while the clue was found.",
        ),
        QAItem(
            question=f"What strange thing did {detective.id} notice first?",
            answer=f"{detective.id} noticed {clue.label} and a bent line of light that showed the clue was important.",
        ),
        QAItem(
            question=f"What was hidden behind the mortar?",
            answer=f"Behind the mortar was {obj.phrase}, and that made the mystery make sense.",
        ),
        QAItem(
            question=f"Why did the light matter in {setting.place}?",
            answer="The light mattered because it bent in a noticeable way, and that refraction pointed the detective toward the hidden wall.",
        ),
    ]
    if state.foreshadowed:
        qa.append(QAItem(
            question="How was the answer hinted at before it was found?",
            answer="The story hinted at the answer with the strange light and the crooked shine before the wall was opened.",
        ))
    if state.found_object:
        qa.append(QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {detective.id} was no longer guessing, because the hidden object had been found and the mystery was solved.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is refraction?",
            answer="Refraction is when light bends as it passes through something like glass or water.",
        ),
        QAItem(
            question="What is mortar on a wall?",
            answer="Mortar is the paste that holds bricks together, and it can crack or crumble when it gets old.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a little hint early on about something important that will matter later.",
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
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue matters when it requires light and there is a place to see it.
has_light_hint(C) :- clue(C), needs_light(C).

% A mystery is valid when the clue can be followed and the hidden object is in mortar.
valid_story(P, C, O) :- place(P), clue(C), object(O), needs_light(C), in_mortar(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.has_light:
            lines.append(asp.fact("lit", pid))
        if setting.has_wall:
            lines.append(asp.fact("wall", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.requires_light:
            lines.append(asp.fact("needs_light", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("tag", cid, tag))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("in_mortar", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if len(clingo_set) != len(python_set):
        print("MISMATCH between clingo and valid_combos():")
        print("  clingo:", sorted(clingo_set))
        print("  python:", sorted(python_set))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    return 0


CURATED = [
    StoryParams(place="attic", clue="prism", object="compass", name="Mina", gender="girl", parent="mother", trait="lanky"),
    StoryParams(place="hallway", clue="mirror", object="note", name="Theo", gender="boy", parent="father", trait="quiet"),
    StoryParams(place="workshop", clue="window", object="key", name="Ivy", gender="girl", parent="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a lanky child, refraction, mortar, and a mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    object_ = args.object_ or rng.choice(list(OBJECTS))
    setting = SETTINGS[place]
    if not reasonableness_gate(setting, CLUES[clue], OBJECTS[object_]):
        raise StoryError(explain_rejection(setting, CLUES[clue], OBJECTS[object_]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else "lanky"
    return StoryParams(place=place, clue=clue, object=object_, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        OBJECTS[params.object],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, clue, object) combos:\n")
        for place, clue, obj in stories:
            print(f"  {place:10} {clue:8} {obj:8}")
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
            header = f"### {p.name}: {p.clue} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
