#!/usr/bin/env python3
"""
storyworlds/worlds/morsel_hydrant_quesadilla_inner_monologue_detective_story.py
==============================================================================

A tiny detective story world with inner monologue, built around a missing
morsel, a hydrant, and a quesadilla.

Premise:
- A young detective notices a lost quesadilla morsel near a hydrant.
- The scene suggests a mystery, and the detective thinks aloud inside their head.

Tension:
- The detective worries someone took the bite.
- Clues show the morsel was not stolen by a person at all.

Turn:
- The hydrant's splash and a gust of wind explain the trail.

Resolution:
- The detective reconstructs the event and returns the morsel to its owner,
  ending with a clear, concrete change in the world state.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager imports from storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father"}
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
    mood: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    noun: str
    detail: str
    meaning: str
    source: str


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    alibi: str
    clue_fit: str
    guilt: float = 0.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    detective_name: str
    friend_name: str
    seed: Optional[int] = None


SETTINGS = {
    "corner": Setting(place="the corner bakery", mood="warm and busy", affords={"investigate"}),
    "street": Setting(place="the quiet street", mood="cool and still", affords={"investigate"}),
    "alley": Setting(place="the narrow alley", mood="damp and shadowy", affords={"investigate"}),
    "park": Setting(place="the little park", mood="bright but breezy", affords={"investigate"}),
}

CLUES = {
    "crumbs": Clue(
        id="crumbs",
        noun="crumbs",
        detail="a trail of tiny crumbs",
        meaning="something had been carried or nibbled nearby",
        source="quesadilla",
    ),
    "smear": Clue(
        id="smear",
        noun="smear",
        detail="a yellow smear on the curb",
        meaning="melted cheese had dripped there",
        source="quesadilla",
    ),
    "spray": Clue(
        id="spray",
        noun="spray",
        detail="a wet spray on the sidewalk",
        meaning="water had splashed from the hydrant",
        source="hydrant",
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the alley cat",
        role="cat",
        alibi="the cat was napping on a warm newspaper",
        clue_fit="no crumbs in the cat's path",
    ),
    "wind": Suspect(
        id="wind",
        label="the wind",
        role="wind",
        alibi="the wind had no paws and no hands",
        clue_fit="it could move crumbs but not eat them",
    ),
    "kid": Suspect(
        id="kid",
        label="the delivery kid",
        role="kid",
        alibi="the kid was still across the street with a bag of napkins",
        clue_fit="the kid did not match the wet spray near the hydrant",
    ),
}

DETECTIVE_NAMES = ["Maya", "Noah", "Iris", "Leo", "Nina", "Eli", "Zoe"]
FRIEND_NAMES = ["Pip", "Milo", "June", "Tess", "Rae", "Otis"]


def tell(setting: Setting, clue: Clue, suspect: Suspect, detective_name: str, friend_name: str) -> World:
    world = World(setting)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type="detective",
        label="the detective",
        meters={"focus": 1.0},
        memes={"curiosity": 1.0, "worry": 0.4},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type="friend",
        label="the friend",
        meters={"patience": 1.0},
        memes={"hope": 1.0},
    ))
    hydrant = world.add(Entity(
        id="hydrant",
        kind="thing",
        type="hydrant",
        label="the hydrant",
        phrase="a red hydrant",
        location=setting.place,
        meters={"water": 1.0},
        memes={"humming": 0.2},
    ))
    morsel = world.add(Entity(
        id="morsel",
        kind="thing",
        type="morsel",
        label="a morsel",
        phrase="a lonely quesadilla morsel",
        owner=friend.id,
        location=setting.place,
        meters={"warmth": 0.6, "mess": 0.0},
        memes={"value": 1.0},
    ))
    quesadilla = world.add(Entity(
        id="quesadilla",
        kind="thing",
        type="quesadilla",
        label="a quesadilla",
        phrase="a whole quesadilla with one missing bite",
        owner=friend.id,
        location=setting.place,
        meters={"warmth": 0.9, "missing_bites": 1.0},
        memes={"comfort": 1.0},
    ))

    world.say(
        f"{detective.name if False else detective_name} was a small detective who loved quiet clues and big questions."
    )
    world.say(
        f"{detective_name} and {friend_name} went to {setting.place}, where the air felt {setting.mood}."
    )
    world.say(
        f"{friend_name} held up {quesadilla.phrase} and frowned. One soft morsel had gone missing."
    )

    world.para()
    world.say(
        f"{detective_name} looked at the ground beside the hydrant and studied {clue.detail}."
    )
    world.say(
        f'In {detective_name}\'s head, a careful voice whispered, "{clue.meaning}."'
    )
    detective.memes["curiosity"] += 1.0
    detective.memes["worry"] += 0.4
    world.facts["clue"] = clue
    world.facts["suspect"] = suspect
    world.facts["detective"] = detective
    world.facts["friend"] = friend
    world.facts["morsel"] = morsel
    world.facts["quesadilla"] = quesadilla
    world.facts["hydrant"] = hydrant

    if clue.id == "spray":
        hydrant.meters["water"] += 1.0
        world.say(
            f"The hydrant had splashed the sidewalk, and the wet shine led away from the bite."
        )
    else:
        world.say(
            f"The crumbs pointed in a little curve, as if something had been nudged by the breeze."
        )

    world.para()
    world.say(
        f"{detective_name} first suspected {suspect.label}, because mysteries always liked to hide behind the nearest shadow."
    )
    world.say(
        f'But inside their head they thought, "{suspect.alibi}. That does not sound like a hungry thief."'
    )
    suspect.guilt += 0.2 if suspect.role != "cat" else 0.1
    world.facts["guilt_path"] = []

    if suspect.role == "cat":
        world.say(
            f"The cat only blinked slowly and licked a paw, which made {detective_name} even less certain."
        )
    elif suspect.role == "wind":
        world.say(
            f"The wind skated past the hydrant and made the napkin flutter like a tiny flag."
        )
    else:
        world.say(
            f"The delivery kid waved from across the street, still holding a stack of napkins and looking surprised."
        )

    world.para()
    world.say(
        f"{detective_name} bent down and noticed that the morsel was not stolen at all."
    )
    if clue.id == "spray":
        world.say(
            f"It had slipped when the hydrant sprayed water, then skidded toward the curb."
        )
    else:
        world.say(
            f"It had been pushed by the breeze, then left behind when the quesadilla was set down."
        )
    world.say(
        f'In the detective\'s head, the puzzle clicked into place: "{clue.source} and {clue.meaning}."'
    )

    if clue.id == "spray":
        morsel.location = "near the curb"
        morsel.meters["mess"] = 0.0
        hydrant.meters["water"] = 0.6
        world.say(
            f"{detective_name} picked up the dry little morsel and handed it back to {friend_name}."
        )
    else:
        morsel.location = "in the quesadilla"
        quesadilla.meters["missing_bites"] = 0.0
        world.say(
            f"{detective_name} found the lost bite tucked by the box and put it back where it belonged."
        )

    detective.memes["worry"] = 0.0
    detective.memes["satisfaction"] = 1.0
    friend.memes["relief"] = 1.0

    world.para()
    world.say(
        f"{friend_name} smiled, and the mystery shrank to a tiny, solved thing."
    )
    world.say(
        f"{detective_name} walked away thinking that the best clues were the ones that told the truth in the end."
    )

    world.facts["setting"] = setting
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    return [
        f'Write a short detective story for a young child that includes the words "{clue.noun}", "hydrant", and "quesadilla".',
        f"Tell a mystery where {f['detective'].id} notices {clue.detail} near a hydrant and solves the case with an inner monologue.",
        f"Write a gentle detective story about a missing morsel, a clue by a hydrant, and a child-friendly explanation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    friend: Entity = f["friend"]
    clue: Clue = f["clue"]
    quesadilla: Entity = f["quesadilla"]
    morsel: Entity = f["morsel"]
    setting: Setting = f["setting"]
    suspect: Suspect = f["suspect"]

    qa = [
        QAItem(
            question=f"What kind of story is this one about {detective.id} and the missing bite?",
            answer=f"It is a detective story, with {detective.id} noticing clues, guessing, and then solving the mystery.",
        ),
        QAItem(
            question=f"Where did {detective.id} find {clue.detail}?",
            answer=f"{detective.id} found {clue.detail} beside the hydrant at {setting.place}.",
        ),
        QAItem(
            question=f"What was missing from the quesadilla?",
            answer=f"One small morsel was missing from the quesadilla.",
        ),
        QAItem(
            question=f"Who first seemed suspicious in {detective.id}'s mind?",
            answer=f"{suspect.label} seemed suspicious at first, but the detective's inner monologue showed that the clue did not really fit.",
        ),
    ]

    if clue.id == "spray":
        qa.append(QAItem(
            question=f"Why did the detective stop worrying about the missing morsel?",
            answer=f"The detective realized the hydrant had sprayed water, and the morsel had only slipped away instead of being stolen.",
        ))
        qa.append(QAItem(
            question=f"What changed by the end of the story for {friend.id}?",
            answer=f"By the end, {friend.id} had the morsel back and the quesadilla was safe again.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did the detective explain the clue in their head?",
            answer=f"In the detective's inner monologue, the clue meant the bite had moved because of the breeze, not because of a thief.",
        ))
        qa.append(QAItem(
            question=f"What happened to the missing bite at the end?",
            answer=f"The detective found the missing bite and put it back into the quesadilla.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hydrant?",
            answer="A hydrant is a water pipe on a street that firefighters use, and it can splash water if it leaks or sprays.",
        ),
        QAItem(
            question="What is a quesadilla?",
            answer="A quesadilla is a warm tortilla filled with cheese or other tasty food, folded and cooked until it is melty.",
        ),
        QAItem(
            question="What is a morsel?",
            answer="A morsel is a very small bite or piece of food.",
        ),
        QAItem(
            question="What does inner monologue mean?",
            answer="Inner monologue is the voice of a character's thoughts inside their head.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for su in SUSPECTS:
                combos.append((s, c, su))
    return combos


CURATED = [
    StoryParams(setting="corner", clue="spray", suspect="cat", detective_name="Maya", friend_name="Pip"),
    StoryParams(setting="street", clue="crumbs", suspect="wind", detective_name="Iris", friend_name="June"),
    StoryParams(setting="park", clue="smear", suspect="kid", detective_name="Leo", friend_name="Tess"),
]


def explain_rejection(setting: str, clue: str, suspect: str) -> str:
    return "(No story: that combination does not fit this tiny mystery setup.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_noun", cid, c.noun))
        lines.append(asp.fact("source", cid, c.source))
    for suid, su in SUSPECTS.items():
        lines.append(asp.fact("suspect", suid))
        lines.append(asp.fact("suspect_role", suid, su.role))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, C, U) :- setting(S), clue(C), suspect(U).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    ap = argparse.ArgumentParser(description="A tiny detective story world with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective-name", dest="detective_name")
    ap.add_argument("--friend-name", dest="friend_name")
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
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        suspect=suspect,
        detective_name=args.detective_name or rng.choice(DETECTIVE_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        SUSPECTS[params.suspect],
        params.detective_name,
        params.friend_name,
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
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, clue, suspect) combos:\n")
        for s, c, u in triples:
            print(f"  {s:8} {c:8} {u:8}")
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
            header = f"### {p.detective_name}: {p.clue} at {p.setting} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
