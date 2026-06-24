#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/prairie_lesson_learned_misunderstanding_kindness_whodunit.py
===============================================================================================================================

A small whodunit-style storyworld set on a prairie, built around a misunderstanding,
a kind act, and a lesson learned.

The seed tale idea:
- A child on the prairie thinks a tiny loss must be a theft.
- The search turns into a gentle whodunit.
- The clue trail reveals the missing thing was moved kindly, not stolen.
- The child learns to ask first, and the prairie community ends with warmth.

This world is intentionally small and constraint-checked:
- there is one mystery object;
- there are a few plausible suspects;
- kindness changes the social state;
- the final reveal fixes the misunderstanding and teaches a lesson learned.

The script follows the Storyweavers contract:
- self-contained stdlib script;
- eager import from storyworlds/results.py;
- lazy import of storyworlds/asp.py inside ASP helpers;
- StoryParams, registries, build_parser, resolve_params, generate, emit, main;
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, and --show-asp.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""  # helper, owner, neighbor, ranger, child, etc.
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def thing_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Site:
    place: str = "the prairie"
    covers: set[str] = field(default_factory=set)


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    location: str
    clue: str
    is_missing: bool = True


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    kindness: str
    moved_object: Optional[str] = None
    honest: bool = True


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.mysteries: dict[str, MysteryObject] = {}
        self.suspects: dict[str, Suspect] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_mystery(self, obj: MysteryObject) -> MysteryObject:
        self.mysteries[obj.id] = obj
        return obj

    def add_suspect(self, suspect: Suspect) -> Suspect:
        self.suspects[suspect.id] = suspect
        return suspect

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

        clone = World(self.site)
        clone.entities = copy.deepcopy(self.entities)
        clone.mysteries = copy.deepcopy(self.mysteries)
        clone.suspects = copy.deepcopy(self.suspects)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "prairie": Site(place="the prairie", covers={"grass", "fence", "barn", "path"}),
}

CHARACTERS = {
    "child": {"type": "boy", "label": "a curious child", "role": "child"},
    "child_girl": {"type": "girl", "label": "a curious child", "role": "child"},
    "ranger": {"type": "woman", "label": "the prairie ranger", "role": "ranger"},
    "neighbor": {"type": "woman", "label": "the neighbor", "role": "neighbor"},
    "shepherd": {"type": "man", "label": "the shepherd", "role": "neighbor"},
}

MYSTERIES = {
    "lantern": MysteryObject(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a red ribbon",
        location="the fence",
        clue="a ribbon snagged on a fence nail",
    ),
    "hat": MysteryObject(
        id="hat",
        label="hat",
        phrase="a straw hat with a blue band",
        location="the barn",
        clue="dusty straw near the barn door",
    ),
    "pie": MysteryObject(
        id="pie",
        label="pie",
        phrase="a blueberry pie on a cloth",
        location="the path",
        clue="blue crumbs on the path",
    ),
}

SUSPECTS = {
    "ranger": Suspect(
        id="ranger",
        label="the prairie ranger",
        alibi="she was checking the fence line",
        kindness="she had moved it to keep it safe from the wind",
        moved_object="lantern",
        honest=True,
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor",
        alibi="she was feeding the hens",
        kindness="she had moved it onto the porch so no one would step on it",
        moved_object="hat",
        honest=True,
    ),
    "shepherd": Suspect(
        id="shepherd",
        label="the shepherd",
        alibi="he was mending a loose gate",
        kindness="he had moved it out of the sun for the child",
        moved_object="pie",
        honest=True,
    ),
}

GENTLE_NAMES = ["Mia", "Noah", "Lena", "Owen", "June", "Iris", "Theo", "Ruby"]
TRAITS = ["curious", "careful", "stubborn", "thoughtful", "brave", "softhearted"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    child_name: str
    child_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _make_entity(world: World, params: StoryParams) -> Entity:
    return world.add_entity(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_type,
            label=f"{params.trait} child",
            role="child",
            meters={"distance": 0.0},
            memes={"wonder": 1.0, "worry": 0.0, "trust": 0.0, "lesson": 0.0},
        )
    )


def _case_prefix(name: str) -> str:
    return name[0].upper() + name[1:] if name else name


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def _missing_clause(obj: MysteryObject) -> str:
    return f"{_article(obj.label)} {obj.label}"


def _investigate(world: World, child: Entity, obj: MysteryObject) -> None:
    child.meters["search_steps"] = child.meters.get("search_steps", 0.0) + 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} looked across {world.site.place} and noticed that {_missing_clause(obj)} was gone."
    )
    world.say(
        f"At first, {child.pronoun('subject')} thought someone had taken {child.pronoun('object')}."
    )


def _clues(world: World, obj: MysteryObject, suspect: Suspect) -> None:
    world.say(
        f"The clue was plain enough: {obj.clue}. That pointed toward {suspect.label}."
    )
    world.say(
        f"Yet {suspect.label} had {suspect.alibi}, which made the case feel strange."
    )


def _kindness(world: World, child: Entity, suspect: Suspect, obj: MysteryObject) -> None:
    child.memes["worry"] -= 0.5
    child.memes["trust"] += 1
    world.say(
        f"When {child.id} found {suspect.label}, {suspect.kindness}."
    )
    world.say(
        f"It was not a theft at all, just a kind act that had been misunderstood."
    )
    obj.is_missing = False


def _lesson(world: World, child: Entity, suspect: Suspect, obj: MysteryObject) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} smiled and said sorry for jumping to conclusions."
    )
    world.say(
        f"{_case_prefix(child.id)} learned that on {world.site.place}, a missing thing can have a kind reason."
    )
    world.say(
        f"In the end, {_missing_clause(obj)} was safe, {suspect.label} was kindly thanked, and the prairie felt peaceful again."
    )


def _resolve_suspect(world: World, mystery_id: str) -> Suspect:
    for suspect in world.suspects.values():
        if suspect.moved_object == mystery_id:
            return suspect
    raise StoryError("No suspect in this world can explain the chosen mystery.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is active when the object is missing.
mystery_active(O) :- object(O), missing(O).

% A suspect is plausible when the clue matches what they moved.
plausible(S, O) :- suspect(S), moved(S, O), mystery_active(O).

% If the suspect was being kind, then the object was moved safely, not stolen.
kind_solution(O) :- plausible(S, O), kind(S).

% The lesson is learned when the child stops worrying and the object is found.
lesson_learned(C, O) :- child(C), object(O), found(O), kind_solution(O).

#show mystery_active/1.
#show plausible/2.
#show kind_solution/1.
#show lesson_learned/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("child", "child")]
    for oid, obj in MYSTERIES.items():
        lines.append(asp.fact("object", oid))
        if obj.is_missing:
            lines.append(asp.fact("missing", oid))
        lines.append(asp.fact("found", oid) if not obj.is_missing else asp.fact("unfound", oid))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("moved", sid, suspect.moved_object))
        if suspect.honest:
            lines.append(asp.fact("kind", sid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_reasonable() -> bool:
    import asp

    model = asp.one_model(asp_program())
    atoms = {str(sym) for sym in model}
    return any("lesson_learned" in a for a in atoms)


def asp_verify() -> int:
    python_ok = all(o.is_missing for o in MYSTERIES.values()) and any(
        s.honest and s.moved_object in MYSTERIES for s in SUSPECTS.values()
    )
    asp_ok = asp_reasonable()
    if python_ok == asp_ok:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print(f"MISMATCH: python_ok={python_ok} asp_ok={asp_ok}")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for mystery_id in MYSTERIES:
            if any(s.moved_object == mystery_id and s.honest for s in SUSPECTS.values()):
                out.append((place, mystery_id, "kind_revealed"))
    return out


def explain_rejection(mystery_id: str) -> str:
    if mystery_id not in MYSTERIES:
        return "(No story: that mystery does not exist in this prairie world.)"
    return "(No story: this world needs a kind explanation for the missing object.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("This prairie world only supports the prairie setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError(explain_rejection(params.mystery))
    world = World(SETTINGS[params.place])
    child = _make_entity(world, params)
    obj = world.add_mystery(MYSTERIES[params.mystery])
    suspect = _resolve_suspect(world, params.mystery)
    world.add_suspect(suspect)

    world.say(
        f"On the prairie, {child.id} was {params.trait} and wanted to solve a little mystery."
    )
    world.say(
        f"The trouble began when {_missing_clause(obj)} disappeared from {obj.location}."
    )

    world.para()
    _investigate(world, child, obj)
    _clues(world, obj, suspect)

    world.para()
    _kindness(world, child, suspect, obj)
    _lesson(world, child, suspect, obj)

    world.facts.update(child=child, object=obj, suspect=suspect, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    obj: MysteryObject = f["object"]
    suspect: Suspect = f["suspect"]
    return [
        f'Write a whodunit-style story for a young child on the prairie about a missing {obj.label} that turns out to have a kind explanation.',
        f"Tell a gentle mystery where {child.id} thinks {suspect.label} took the {obj.label}, but the clue trail proves the act was kindness.",
        f'Write a short prairie story that includes misunderstanding, kindness, and a lesson learned after a missing {obj.label} is found safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    obj: MysteryObject = world.facts["object"]
    suspect: Suspect = world.facts["suspect"]
    return [
        QAItem(
            question=f"What mystery was {child.id} trying to solve on the prairie?",
            answer=f"{child.id} was trying to find out what happened to {obj.phrase}. At first, it seemed like someone had taken it.",
        ),
        QAItem(
            question=f"Why did {child.id} think {suspect.label} might be involved?",
            answer=f"There was a clue near the missing object, and it pointed toward {suspect.label}. But the clue did not mean theft; it only meant {suspect.label} had moved it.",
        ),
        QAItem(
            question=f"What did {child.id} learn by the end of the story?",
            answer=f"{child.id} learned to ask before accusing anyone, because the missing {obj.label} had been moved kindly to keep it safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prairie?",
            answer="A prairie is a wide open grassland with big sky, gentle wind, and few trees.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, or protecting someone or something in a gentle way.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because they do not have all the facts.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="prairie", mystery="lantern", child_name="Mia", child_type="girl", trait="curious"),
    StoryParams(place="prairie", mystery="hat", child_name="Theo", child_type="boy", trait="thoughtful"),
    StoryParams(place="prairie", mystery="pie", child_name="Ruby", child_type="girl", trait="softhearted"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Prairie whodunit storyworld with kindness and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.place != "prairie":
        raise StoryError("This world only supports the prairie setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery object.")
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENTLE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="prairie", mystery=mystery, child_name=name, child_type=gender, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind}) role={e.role} meters={e.meters} memes={e.memes}")
    for m in world.mysteries.values():
        lines.append(f"  mystery {m.id}: missing={m.is_missing} location={m.location} clue={m.clue}")
    for s in world.suspects.values():
        lines.append(f"  suspect {s.id}: moved_object={s.moved_object} honest={s.honest}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(f"{asp_facts()}\n#show mystery_active/1.\n")
    return sorted(set(asp.atoms(model, "mystery_active")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-active mysteries:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
