#!/usr/bin/env python3
"""
storyworlds/worlds/history_dissension_mystery_to_solve_magic_detective.py
=========================================================================

A small detective-style story world about a magical mystery with a history
behind it and a little dissension among the suspects.

Premise:
A child detective helps a town find a missing magical object. The mystery is
not just "who took it?" but "what old history made the town split apart and
hide the truth?" The detective listens, notices clues, and solves the case by
revealing how the past caused the present argument.

The world is built around:
- physical meters: distances, possession, hiddenness, openness, sparkle, etc.
- emotional memes: worry, suspicion, trust, dissension, relief, curiosity

The story always reaches a clear turn:
- a strange clue appears
- the detective follows it through places and people
- the old history explains the dissension
- magic helps reveal the truth
- the ending proves the mystery is solved
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "detective girl"}
        male = {"boy", "father", "man", "detective boy"}
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
    clue_places: list[str]
    history_topic: str
    magic_kind: str


@dataclass
class Mystery:
    missing_item: str
    magical_property: str
    cause: str
    dissension_reason: str
    solved_by: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    assistant_name: str
    assistant_type: str
    missing_item: str
    magic_kind: str
    history_topic: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "museum": Setting(
        place="the old museum",
        clue_places=["the gallery", "the archive room", "the front desk"],
        history_topic="old museum history",
        magic_kind="glowing dust",
    ),
    "library": Setting(
        place="the quiet library",
        clue_places=["the reading nook", "the dusty shelves", "the back desk"],
        history_topic="library history",
        magic_kind="whispering ink",
    ),
    "village": Setting(
        place="the little village",
        clue_places=["the square", "the bakery door", "the bell tower"],
        history_topic="village history",
        magic_kind="moonlight charm",
    ),
}

DETECTIVES = [
    ("Mia", "girl", "curious"),
    ("Leo", "boy", "careful"),
    ("Nora", "girl", "brave"),
    ("Ben", "boy", "patient"),
]

ASSISTANTS = [
    ("Pip", "boy"),
    ("Luna", "girl"),
    ("Tess", "girl"),
    ("Otto", "boy"),
]

MISSING_ITEMS = {
    "silver key": {
        "phrase": "a small silver key",
        "magical_property": "opened the secret case",
        "cause": "it was hidden during an old argument",
        "dissension_reason": "two families had once fought over who should keep it",
        "solved_by": "a glowing reflection on a glass frame",
    },
    "blue lantern": {
        "phrase": "a blue lantern with a tiny star on it",
        "magical_property": "shone when the truth was near",
        "cause": "someone locked it away after a quarrel",
        "dissension_reason": "the elders disagreed about which side of town owned it",
        "solved_by": "a whisper from the archive cards",
    },
    "golden bell": {
        "phrase": "a little golden bell",
        "magical_property": "rang only for honest voices",
        "cause": "it vanished after a dispute in the square",
        "dissension_reason": "the town had split into two groups long ago",
        "solved_by": "a magic echo in the tower",
    },
}

PLACE_CLUES = {
    "museum": ["dust on one shelf", "an old label with a torn corner", "a faint glow under a rug"],
    "library": ["a book left open the wrong way", "ink that shimmered", "a gap in the shelf"],
    "village": ["mud on the steps", "a ribbon tied to the bell rope", "a note hidden in a crack"],
}


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    if params.missing_item not in MISSING_ITEMS:
        raise StoryError("unknown missing item")
    world = World(setting)
    mystery = Mystery(
        missing_item=params.missing_item,
        magical_property=MISSING_ITEMS[params.missing_item]["magical_property"],
        cause=MISSING_ITEMS[params.missing_item]["cause"],
        dissension_reason=MISSING_ITEMS[params.missing_item]["dissension_reason"],
        solved_by=MISSING_ITEMS[params.missing_item]["solved_by"],
    )
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
        memoir={"curiosity": 2} if False else None,  # kept out of prose, never used
    ))
    assistant = world.add(Entity(
        id=params.assistant_name,
        kind="character",
        type=params.assistant_type,
        label="helper",
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=params.missing_item,
        label=params.missing_item,
        phrase=MISSING_ITEMS[params.missing_item]["phrase"],
        hidden=True,
        magical=True,
    ))

    detective.meters["clues"] = 0
    detective.memes["curiosity"] = 2
    detective.memes["doubt"] = 0
    detective.memes["relief"] = 0
    assistant.memes["worry"] = 1
    assistant.memes["trust"] = 0
    world.facts.update(
        mystery=mystery,
        detective=detective,
        assistant=assistant,
        missing=missing,
        setting=setting,
    )
    return world


def _clue(world: World, text: str) -> None:
    world.say(text)
    det: Entity = world.facts["detective"]  # type: ignore[assignment]
    det.meters["clues"] += 1
    det.memes["curiosity"] += 1


def tell_story(world: World) -> None:
    det: Entity = world.facts["detective"]  # type: ignore[assignment]
    asst: Entity = world.facts["assistant"]  # type: ignore[assignment]
    myst: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]

    world.say(f"At {setting.place}, {det.id} was a little detective who liked solving tricky mysteries.")
    world.say(f"{asst.id} stayed close, because the town had been uneasy ever since the old history was whispered about again.")
    world.say(
        f"The missing thing was {MISSING_ITEMS[myst.missing_item]['phrase']}, "
        f"and everyone said it was special because {myst.magical_property}."
    )
    world.para()

    world.say(
        f"But the story was not simple. The people around {setting.place} were in dissension, "
        f"and that old split had begun years ago."
    )
    world.say(
        f"Some said the item should belong to one side, and others said it should belong to the other, "
        f"so nobody liked saying the full truth out loud."
    )
    world.say(
        f"{asst.id} worried that the mystery would stay unsolved, but {det.id} only nodded and began to look for clues."
    )
    world.para()

    # Investigation sequence
    for clue_place, clue_text in zip(setting.clue_places, PLACE_CLUES[world.facts["setting"].place.split()[-1] if False else world.setting.place.split()[-1]]):
        pass

    clue_texts = PLACE_CLUES["museum" if world.setting is SETTINGS["museum"] else "library" if world.setting is SETTINGS["library"] else "village"]
    world.say(f"First, {det.id} searched the {setting.clue_places[0]}.")
    _clue(world, f"There, {det.id} noticed {clue_texts[0]}, which felt like a clue from the past.")
    world.say(f"Then {det.id} followed the hint to the {setting.clue_places[1]}.")
    _clue(world, f"That place held {clue_texts[1]}, and it made the old argument seem closer to the truth.")
    world.say(f"At last, {det.id} went to the {setting.clue_places[2]}.")
    _clue(world, f"Behind one last corner, {det.id} found {clue_texts[2]}, shining with a little magic.")
    world.para()

    # Reveal
    det.memes["doubt"] += 1
    world.say(
        f"{det.id} saw how the magic fit the history: the missing item had been hidden during the old dissension, "
        f"not stolen for greed."
    )
    world.say(
        f"The real reason was simple and sad. People had argued for so long that the item was tucked away to stop the fighting."
    )
    world.say(
        f"When {det.id} said this out loud, the room went quiet, because everyone could finally hear the truth."
    )
    world.para()

    # Resolution
    det.memes["relief"] += 2
    asst.memes["trust"] += 2
    missing.hidden = False
    world.say(
        f"{det.id} used the magic to show where {myst.missing_item} had been kept, and the hidden place opened at once."
    )
    world.say(
        f"{det.id} returned {myst.missing_item} to the town and explained the old history kindly, so the dissension could fade."
    )
    world.say(
        f"In the end, {asst.id} smiled, the magical {myst.missing_item} was safe again, and {det.id} had solved the mystery."
    )


# ---------------------------------------------------------------------------
# Story contracts: sentences must read naturally and be grounded in state.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    det: Entity = world.facts["detective"]  # type: ignore[assignment]
    return [
        f"Write a short detective story for children set at {setting.place} about a magical mystery and old history.",
        f"Tell a story where {det.id} solves a mystery involving {mystery.missing_item} and a disagreement from the past.",
        f"Write a gentle detective tale with clues, dissension, and magic that ends with the truth being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    det: Entity = world.facts["detective"]  # type: ignore[assignment]
    asst: Entity = world.facts["assistant"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{det.id} solved the mystery by following clues, listening to the old history, and using magic to find {mystery.missing_item}.",
        ),
        QAItem(
            question=f"Why was there dissension around the missing item?",
            answer=f"There was dissension because {mystery.dissension_reason}, and that made people hide the truth for a long time.",
        ),
        QAItem(
            question=f"What did {det.id} use to help solve the case?",
            answer=f"{det.id} used careful detective work, clues from {setting.place}, and the magic of {mystery.solved_by}.",
        ),
        QAItem(
            question=f"How did {asst.id} feel near the end?",
            answer=f"{asst.id} felt relieved and hopeful once the missing item was found and the town could stop arguing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out the answer to a mystery.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something unusual or special in a story that can glow, whisper, reveal, or help in a surprising way.",
        ),
        QAItem(
            question="What does history mean?",
            answer="History means things that happened long ago and still matter because they affect what people think and do now.",
        ),
        QAItem(
            question="What does dissension mean?",
            answer="Dissension means a disagreement or split between people who do not all want the same thing.",
        ),
        QAItem(
            question="Why can old history matter in a mystery?",
            answer="Old history can matter because something that happened long ago may explain why people are hiding facts or arguing now.",
        ),
    ]
    if setting.history_topic:
        out.append(QAItem(
            question=f"What kind of place was {setting.place} in this story?",
            answer=f"{setting.place} was a place with clues, memories, and a history that helped explain the mystery.",
        ))
    if mystery.magical_property:
        out.append(QAItem(
            question=f"What did {mystery.missing_item} do in the story?",
            answer=f"{mystery.missing_item} was special because {mystery.magical_property}.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.hidden:
            parts.append("hidden=True")
        if e.magical:
            parts.append("magical=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.

place(P) :- setting(P).
mystery_item(I) :- missing(I).
detective(D) :- character(D).
assistant(A) :- character(A).

history_topic(P,H) :- setting_topic(P,H).
magic_kind(P,M) :- setting_magic(P,M).

valid(P,D,A,I) :- setting(P), character(D), character(A), missing(I),
                  detective_role(D), assistant_role(A),
                  clueable(P), magical(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("setting_topic", key, setting.history_topic))
        lines.append(asp.fact("setting_magic", key, setting.magic_kind))
        for cp in setting.clue_places:
            lines.append(asp.fact("clue_place", key, cp))
    for key in DETECTIVES:
        lines.append(asp.fact("detective_role", key[0]))
    for key in ASSISTANTS:
        lines.append(asp.fact("assistant_role", key[0]))
    for item in MISSING_ITEMS:
        lines.append(asp.fact("missing", item))
        lines.append(asp.fact("magical", item))
    for p in SETTINGS:
        lines.append(asp.fact("clueable", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((p, d, a, i) for (p, d, a, i) in asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} stories.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate and registries
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for detective_name, detective_type, _ in DETECTIVES:
            for assistant_name, assistant_type in ASSISTANTS:
                for item in MISSING_ITEMS:
                    combos.append((place, detective_name, assistant_name, item))
    return combos


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(explain_rejection("unknown place"))
    if args.missing_item and args.missing_item not in MISSING_ITEMS:
        raise StoryError(explain_rejection("unknown missing item"))

    place = args.place or rng.choice(list(SETTINGS))
    det_name, det_type, _ = rng.choice(DETECTIVES)
    ast_name, ast_type = rng.choice(ASSISTANTS)
    missing_item = args.missing_item or rng.choice(list(MISSING_ITEMS))
    if args.detective_name:
        det_name = args.detective_name
    if args.assistant_name:
        ast_name = args.assistant_name
    if args.detective_type:
        det_type = args.detective_type
    if args.assistant_type:
        ast_type = args.assistant_type
    return StoryParams(
        place=place,
        detective_name=det_name,
        detective_type=det_type,
        assistant_name=ast_name,
        assistant_type=ast_type,
        missing_item=missing_item,
        magic_kind=SETTINGS[place].magic_kind,
        history_topic=SETTINGS[place].history_topic,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style magical mystery story world.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--missing-item", choices=sorted(MISSING_ITEMS))
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--assistant-name")
    ap.add_argument("--assistant-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams("museum", "Mia", "girl", "Pip", "boy", "silver key", "glowing dust", "old museum history"),
    StoryParams("library", "Leo", "boy", "Luna", "girl", "blue lantern", "whispering ink", "library history"),
    StoryParams("village", "Nora", "girl", "Otto", "boy", "golden bell", "moonlight charm", "village history"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid(), indent=2, ensure_ascii=False))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} at {p.place} solving {p.missing_item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
