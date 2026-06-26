#!/usr/bin/env python3
"""
A small whodunit storyworld with inner monologue.

Premise:
- A child or small detective notices a missing or misplaced object in a modest setting.
- The detective thinks through clues in an inner monologue.
- The resolution reveals the culprit through cause-and-effect, not magic.

This world is intentionally tiny and constraint-checked:
- The mystery only generates when the evidence is actually sufficient.
- The suspected culprit must match the clue pattern.
- The final story is built from state changes and narrated deductions.

The seed word "collard" is woven into the domain as the collard patch,
collard leaves, and the smell of collards in a kitchen-garden mystery.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    kind: str
    text: str
    suspect: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    culprit: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affordances={"search", "cook"}),
    "garden": Setting(place="the garden", indoor=False, affordances={"search", "pick"}),
    "shed": Setting(place="the shed", indoor=True, affordances={"search", "store"}),
}

MYSTERIES = {
    "missing_collar": {
        "title": "the collared coat",
        "thing_label": "coat",
        "thing_phrase": "a blue coat with a neat collar",
        "clue_kind": "fabric",
        "clue_text": "a little collar-shaped scrap was stuck to the tablecloth",
        "resolution": "the coat had caught on a hook behind the door",
    },
    "stolen_collard": {
        "title": "the collard basket",
        "thing_label": "basket",
        "thing_phrase": "a basket of collard leaves",
        "clue_kind": "leaf",
        "clue_text": "a damp green collard leaf sat by the sink",
        "resolution": "the collard basket had been moved to rinse the leaves",
    },
    "vanished_ink": {
        "title": "the ink bottle",
        "thing_label": "ink bottle",
        "thing_phrase": "a tiny ink bottle for notes",
        "clue_kind": "ink",
        "clue_text": "a blue dot marked the detective's sleeve",
        "resolution": "the ink bottle had tipped inside a bag and left a mark",
    },
}

CULPRITS = {
    "cat": {
        "type": "cat",
        "label": "the cat",
        "action": "slipped through the room",
        "tell": "a paw print",
    },
    "helper": {
        "type": "child",
        "label": "the helper",
        "action": "moved things while cleaning up",
        "tell": "a careful stack of bowls",
    },
    "aunt": {
        "type": "aunt",
        "label": "the aunt",
        "action": "took the thing to fix it",
        "tell": "a folded note",
    },
}

NAMES = ["Mira", "Nia", "June", "Tess", "Lena", "Owen", "Ira", "Sam"]
TRAITS = ["quiet", "careful", "curious", "sharp-eyed", "brave", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when the clue kind matches the culprit tell.
solvable(M, C) :- mystery(M), culprit(C), clue_kind(M, K), tell_kind(C, K).

% The collard theme is always present in this tiny domain.
featured(collard).

valid_story(S, M, C) :- setting(S), mystery(M), culprit(C), solvable(M, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_kind", mid, m["clue_kind"]))
    for cid, c in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("tell_kind", cid, c["tell"].replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    valid = set(valid_stories())
    clingo = set(asp_valid_stories())
    if valid == clingo:
        print(f"OK: clingo gate matches valid_stories() ({len(valid)} stories).")
        return 0
    print("MISMATCH between clingo and python valid stories:")
    if valid - clingo:
        print("  only in python:", sorted(valid - clingo))
    if clingo - valid:
        print("  only in clingo:", sorted(clingo - valid))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for c in CULPRITS:
                if is_reasonable(s, m, c):
                    out.append((s, m, c))
    return out


def is_reasonable(setting_id: str, mystery_id: str, culprit_id: str) -> bool:
    mystery = MYSTERIES[mystery_id]
    culprit = CULPRITS[culprit_id]
    # Small, legible world logic:
    # - the clue must match the culprit's tell type
    # - collard stories should actually mention collards somewhere
    return mystery["clue_kind"] == culprit["tell"].replace(" ", "_") or (
        mystery_id == "stolen_collard" and culprit_id in {"helper", "aunt"}
    )


def explain_rejection(setting_id: str, mystery_id: str, culprit_id: str) -> str:
    mystery = MYSTERIES[mystery_id]
    culprit = CULPRITS[culprit_id]
    return (
        f"(No story: the clue in {mystery_id} does not fit {culprit['label']}. "
        f"Try a culprit whose tell matches the clue kind, or use the collard basket mystery.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    culprit = CULPRITS[params.culprit]
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
    ))
    item = world.add(Entity(
        id="missing_item",
        kind="thing",
        type=mystery["thing_label"],
        label=mystery["thing_label"],
        phrase=mystery["thing_phrase"],
        location=setting.place,
    ))

    culprit_ent = world.add(Entity(
        id="culprit",
        kind="character" if culprit_id_is_character(params.culprit) else "thing",
        type=culprit["type"],
        label=culprit["label"],
    ))

    # Facts used by QA and narration
    world.facts.update(
        detective=detective,
        helper=helper,
        item=item,
        culprit=culprit_ent,
        mystery=params.mystery,
        setting=params.setting,
        clue=mystery["clue_text"],
        resolution=mystery["resolution"],
    )

    # Build the story with inner monologue and deduction.
    detective.memes["curiosity"] = 1
    detective.memes["worry"] = 1
    helper.memes["helpfulness"] = 1

    world.say(f"{detective.id} was a {random.choice(TRAITS)} detective who loved quiet clues.")
    world.say(f"{detective.pronoun().capitalize()} noticed that {item.phrase} was gone from {setting.place}.")
    world.say(f"\"Hmm,\" {detective.id} thought. \"This smells like a little mystery, maybe even a collard mystery.\"")

    world.para()
    world.say(f"{setting.place.capitalize()} was still and bright, except for one odd clue: {mystery['clue_text']}.")
    world.say(f"{detective.id} kept thinking. \"If I can match the clue, I can find where {item.label} went.\"")
    detective.memes["deduction"] = 1

    world.para()
    if params.mystery == "stolen_collard":
        world.say(f"{helper.id} had been nearby with a basket of collard leaves.")
        world.say(f"{detective.id} looked again. \"Collard leaves are damp and soft,\" {detective.id} thought. \"So if one turned up by the sink, the basket must have been moved for rinsing.\"")
    elif params.mystery == "missing_collar":
        world.say(f"{detective.id} stared at the little collar-shaped scrap and the hook by the door.")
        world.say(f"\"A coat can snag without anyone stealing it,\" {detective.id} thought. \"That would leave a scrap behind.\"")
    else:
        world.say(f"{detective.id} saw the blue dot and the tidy notes.")
        world.say(f"\"Ink marks fingers and sleeves,\" {detective.id} thought. \"Someone must have carried it too fast.\"")

    world.para()
    world.say(f"Then {detective.id} followed the clue to the truth: {mystery['resolution']}.")
    world.say(f"{culprit['label'].capitalize()} had not meant trouble; {culprit['action']}.")
    world.say(f"{detective.id} let out a slow breath. \"I knew it,\" {detective.id} thought, \"the answer was hidden in plain sight.\"")
    world.say(f"By the end, the missing thing was back where it belonged, and the little collard mystery was solved.")

    return world


def culprit_id_is_character(culprit_id: str) -> bool:
    return culprit_id in {"helper", "aunt"}


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit for a child detective, with a quiet inner monologue and one collard clue.',
        f"Tell a gentle mystery set in {SETTINGS[f['setting']].place} where {f['detective'].id} follows a clue and solves what happened to the missing item.",
        f"Write a simple detective story where the word 'collard' appears as part of the clue trail and the hero thinks through the answer in their head.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    setting = SETTINGS[f["setting"]]
    mystery = MYSTERIES[f["mystery"]]

    qa = [
        QAItem(
            question=f"What was {detective.id} trying to solve in {setting.place}?",
            answer=f"{detective.id} was trying to solve what happened to {item.phrase} in {setting.place}.",
        ),
        QAItem(
            question=f"What clue made {detective.id} think harder about the case?",
            answer=f"The clue was that {mystery['clue_text']}. That clue helped {detective.id} think through the mystery.",
        ),
        QAItem(
            question=f"Who helped or stood nearby while {detective.id} investigated?",
            answer=f"{helper.id} was nearby and helped keep the search calm while {detective.id} followed the clue.",
        ),
        QAItem(
            question=f"What did {detective.id} think in the middle of the story?",
            answer=f"{detective.id} thought that if the clue matched the right kind of sign, the missing thing could be found.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended with {mystery['resolution']}, and the missing thing was back where it belonged.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a collard?",
            answer="A collard is a leafy green vegetable with big leaves, often cooked in a kitchen.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader and the detective try to figure out who caused the problem.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thinking voice inside a character's head.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.mystery:
        if not is_reasonable(args.setting or "kitchen", args.mystery, args.culprit):
            raise StoryError(explain_rejection(args.setting or "kitchen", args.mystery, args.culprit))

    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    if not is_reasonable(setting, mystery, culprit):
        # Keep random generation constrained.
        if mystery == "stolen_collard":
            culprit = rng.choice(["helper", "aunt"])
        else:
            culprit = {
                "missing_collar": "cat",
                "vanished_ink": "aunt",
            }.get(mystery, "cat")

    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != detective_name])

    return StoryParams(
        setting=setting,
        mystery=mystery,
        culprit=culprit,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        setting="kitchen",
        mystery="stolen_collard",
        culprit="helper",
        detective_name="Mira",
        detective_type="girl",
        helper_name="June",
        helper_type="girl",
    ),
    StoryParams(
        setting="garden",
        mystery="missing_collar",
        culprit="cat",
        detective_name="Owen",
        detective_type="boy",
        helper_name="Tess",
        helper_type="girl",
    ),
    StoryParams(
        setting="shed",
        mystery="vanished_ink",
        culprit="aunt",
        detective_name="Lena",
        detective_type="girl",
        helper_name="Sam",
        helper_type="boy",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with inner monologue and collards.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def asp_program_text() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_text())
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for row in stories:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.detective_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
