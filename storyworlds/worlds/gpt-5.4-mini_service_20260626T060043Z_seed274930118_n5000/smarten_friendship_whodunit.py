#!/usr/bin/env python3
"""
storyworlds/worlds/smarten_friendship_whodunit.py
==================================================

A small child-facing whodunit storyworld about friendship, clues, and a gentle
turn toward helping each other.

Seed tale sketch:
---
A careful child notices that a shiny badge has vanished before the school concert.
A best friend helps look for clues: a shoe print, a ribbon, and a sticky crumb.
The child first suspects a classmate, but the clues point somewhere kinder.
In the end, the missing badge is found, the room is smartened up, and the two
friends leave together feeling proud.

World idea:
---
- The hero values friendship and wants everything to look neat.
- A mystery object goes missing in a small setting.
- Clues are accumulated as meters on the world state.
- Suspicion rises, then a friend helps by looking carefully and smartening the
  scene.
- The ending proves the mystery was solved and the friendship grew.

The prose stays close to a whodunit: clues, suspicion, reveal, and resolution.
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
    found_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    supports: set[str] = field(default_factory=set)
    hiding_spots: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue_kind: str
    can_hide_in: set[str]
    can_leave_trace: set[str]
    owner_role: str = "hero"


@dataclass
class HelperItem:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    action: str
    effect: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues: list[str] = []
        self.suspect: str = ""
        self.solution: str = ""

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.clues = list(self.clues)
        w.suspect = self.suspect
        w.solution = self.solution
        return w


PLACES = {
    "library": Place(
        id="library",
        label="the library",
        indoors=True,
        supports={"search", "tidy", "hide"},
        hiding_spots=["behind the shelf", "under a table", "inside a returned book cart"],
    ),
    "classroom": Place(
        id="classroom",
        label="the classroom",
        indoors=True,
        supports={"search", "tidy", "hide"},
        hiding_spots=["under a desk", "by the art shelf", "near the window seat"],
    ),
    "hall": Place(
        id="hall",
        label="the school hall",
        indoors=True,
        supports={"search", "tidy", "hide"},
        hiding_spots=["behind a coat rack", "under a bench", "by the stage curtain"],
    ),
}

MYSTERIES = {
    "badge": Mystery(
        id="badge",
        label="badge",
        phrase="a shiny name badge",
        clue_kind="metal",
        can_hide_in={"library", "classroom", "hall"},
        can_leave_trace={"glint", "scratch"},
    ),
    "ribbon": Mystery(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon",
        clue_kind="cloth",
        can_hide_in={"library", "classroom", "hall"},
        can_leave_trace={"thread", "flutter"},
    ),
    "cookie": Mystery(
        id="cookie",
        label="cookie",
        phrase="a small iced cookie",
        clue_kind="crumb",
        can_hide_in={"library", "classroom", "hall"},
        can_leave_trace={"crumb", "sweet smell"},
    ),
}

HELPERS = {
    "spoon": HelperItem(
        id="spoon",
        label="a little spoon",
        phrase="a little spoon",
        helps_with={"crumb"},
        action="scoop",
        effect="made crumbs easy to gather",
    ),
    "cloth": HelperItem(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth",
        helps_with={"metal", "cloth"},
        action="wipe",
        effect="made the clue spots neat again",
    ),
    "basket": HelperItem(
        id="basket",
        label="a small basket",
        phrase="a small basket",
        helps_with={"metal", "cloth", "crumb"},
        action="carry",
        effect="kept the found things together",
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Ari", "Zoe", "Ben", "Maya", "Finn"]
TRAITS = ["careful", "bright", "brave", "curious", "kind", "steady"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def suspicious_and_soluble(place: Place, mystery: Mystery) -> bool:
    return place.id in mystery.can_hide_in


def compatible_helper(mystery: Mystery) -> Optional[HelperItem]:
    for h in HELPERS.values():
        if mystery.clue_kind in h.helps_with:
            return h
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if suspicious_and_soluble(place, mystery) and compatible_helper(mystery):
                combos.append((pid, mid))
    return combos


def _hint(world: World, text: str) -> None:
    world.clues.append(text)
    world.say(text)


def investigate(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    friend.memes["helpfulness"] = friend.memes.get("helpfulness", 0) + 1
    world.say(
        f"{hero.id} noticed something odd: {mystery.phrase} was missing from {world.place.label}."
    )
    world.say(
        f"{friend.id} said they would help, because friends looked twice when a mystery began."
    )


def add_clues(world: World, mystery: Mystery) -> None:
    if mystery.clue_kind == "metal":
        _hint(world, "Near the floor, there was a tiny glint by a shoe print.")
        _hint(world, "On the shelf edge, a faint scratch pointed toward the back.")
    elif mystery.clue_kind == "cloth":
        _hint(world, "A loose thread was caught on a chair leg.")
        _hint(world, "Something bright had fluttered near the curtains.")
    else:
        _hint(world, "A sweet smell hung in the air, and one crumb sat on the table.")
        _hint(world, "There were tiny white crumbs on the path to the sink.")


def suspect(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.suspect = friend.id
    world.say(
        f"{hero.id} first wondered if someone had taken it on purpose, and the room felt very quiet."
    )
    world.say(
        f"But {friend.id} only pointed to the clues and said, 'Let's be sure before we blame anyone.'"
    )


def smarten(world: World, helper: HelperItem) -> None:
    world.say(
        f"Together they used {helper.phrase} to {helper.action} the messy spots, which {helper.effect}."
    )
    if helper.id == "cloth":
        world.say("The shelves looked tidier at once, and the glint on the floor became easier to see.")
    elif helper.id == "spoon":
        world.say("The crumbs gathered into one neat pile, so the real trail stood out.")
    else:
        world.say("With everything kept together, the search felt calm and smart.")
    world.facts["smartened"] = True


def reveal(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.solution = mystery.id
    if mystery.clue_kind == "metal":
        ending = "behind the returned-book cart"
    elif mystery.clue_kind == "cloth":
        ending = "inside a folded stage curtain"
    else:
        ending = "beside the sink where the cookie crumbs led"
    world.say(
        f"At last, they found the {mystery.label} {ending}, tucked where nobody had looked closely enough."
    )
    world.say(
        f"{hero.id} laughed with relief, and {friend.id} laughed too, because the clues had been telling the truth all along."
    )
    world.say(
        f"The mystery was solved, the room was smartened up, and the two friends walked away together, proud of their careful teamwork."
    )


def tell(place: Place, mystery: Mystery, hero_name: str, friend_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Leo", "Ben", "Finn", "Ari"} else "girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy" if friend_name in {"Leo", "Ben", "Finn", "Ari"} else "girl"))

    helper = compatible_helper(mystery)
    if helper is None:
        raise StoryError("No reasonable helper exists for this mystery.")

    hero.traits = ["little", trait]
    friend.traits = ["kind"]

    world.say(
        f"{hero.id} was a little {trait} child who liked neat things and trusted {friend.id} most."
    )
    world.say(
        f"One afternoon at {place.label}, {hero.id} noticed that {mystery.phrase} had gone missing."
    )
    world.say(
        f"{friend.id} promised to help, because friendship meant following the clues instead of jumping to conclusions."
    )

    world.para()
    investigate(world, hero, friend, mystery)
    add_clues(world, mystery)
    suspect(world, hero, friend)
    smarten(world, helper)
    world.para()
    reveal(world, hero, friend, mystery)

    world.facts.update(
        hero=hero,
        friend=friend,
        mystery=mystery,
        helper=helper,
        place=place,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery = f["mystery"]
    place = f["place"]
    return [
        f'Write a short whodunit story for a young child set in {place.label} about a missing {mystery.label}.',
        f"Tell a friendship mystery where {hero.id} and {friend.id} follow clues, stay kind, and smarten the room.",
        f'Write a gentle detective story that uses the word "smarten" and ends with friends solving a small mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery = f["mystery"]
    helper = f["helper"]
    place = f["place"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What did {hero.id} and {friend.id} search for at {place.label}?",
            answer=f"They searched for the missing {mystery.label}, because {mystery.phrase} had vanished and started the little mystery.",
        ),
        QAItem(
            question=f"Why did {hero.id} trust {friend.id} during the mystery?",
            answer=f"{hero.id} trusted {friend.id} because {friend.id} stayed calm, looked at the clues, and acted like a true friend.",
        ),
        QAItem(
            question=f"What helped them smarten the clue spots?",
            answer=f"They used {helper.phrase} to smarten the messy spots, which made the clues easier to follow and the room tidier.",
        ),
        QAItem(
            question=f"How did the story end for the little {trait} detective?",
            answer=f"It ended happily: {hero.id} and {friend.id} found the {mystery.label}, solved the mystery, and walked away proud of their friendship.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "badge": [
        QAItem(
            question="What is a badge?",
            answer="A badge is a small marked object people wear or carry to show a name, job, or group.",
        )
    ],
    "ribbon": [
        QAItem(
            question="What is a ribbon?",
            answer="A ribbon is a narrow strip of cloth used for tying, decorating, or making things look pretty.",
        )
    ],
    "cookie": [
        QAItem(
            question="What is a cookie?",
            answer="A cookie is a small baked treat that can be sweet and crumbly.",
        )
    ],
    "smarten": [
        QAItem(
            question="What does it mean to smarten something up?",
            answer="To smarten something up means to make it look tidier, neater, or more polished.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind of caring bond where people help each other, listen, and stay kind.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [QAItem(
        question="What does a detective do?",
        answer="A detective looks for clues and tries to solve a mystery by paying attention to small details.",
    )]
    for key in [world.facts["mystery"].label, "smarten", "friendship"]:
        out.extend(WORLD_KNOWLEDGE.get(key, []))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    lines.append(f"  suspect: {world.suspect}")
    lines.append(f"  solution: {world.solution}")
    return "\n".join(lines)


def explain_rejection(place_id: str, mystery_id: str) -> str:
    place = PLACES[place_id]
    mystery = MYSTERIES[mystery_id]
    if not suspicious_and_soluble(place, mystery):
        return f"(No story: {mystery.phrase} does not fit a whodunit in {place.label}.)"
    if compatible_helper(mystery) is None:
        return f"(No story: there is no reasonable helper for {mystery.phrase}.)"
    return "(No story: the requested choices do not make a solid mystery.)"


CURATED = [
    StoryParams(place="library", mystery="badge", name="Mina", friend="Leo", trait="curious"),
    StoryParams(place="classroom", mystery="ribbon", name="Nora", friend="Ari", trait="careful"),
    StoryParams(place="hall", mystery="cookie", name="Maya", friend="Ben", trait="brave"),
]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        if not suspicious_and_soluble(PLACES[args.place], MYSTERIES[args.mystery]):
            raise StoryError(explain_rejection(args.place, args.mystery))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mystery_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, mystery=mystery_id, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], params.name, params.friend, params.trait)
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


ASP_RULES = r"""
% A mystery is compatible when it belongs in the place and has a helper.
solvable(P, M) :- place(P), mystery(M), can_hide_in(M, P), has_helper(M).

% A helper is good when it can deal with the mystery's clue kind.
good_helper(H, M) :- helper(H), mystery(M), clue_kind(M, K), helps_with(H, K).

% A story is valid when the place and mystery are compatible.
valid_story(P, M) :- solvable(P, M), good_helper(_, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for spot in place.hiding_spots:
            lines.append(asp.fact("hiding_spot", pid, spot))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        for p in sorted(m.can_hide_in):
            lines.append(asp.fact("can_hide_in", mid, p))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for k in sorted(h.helps_with):
            lines.append(asp.fact("helps_with", hid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small friendship whodunit storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible place/mystery combos:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
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
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
