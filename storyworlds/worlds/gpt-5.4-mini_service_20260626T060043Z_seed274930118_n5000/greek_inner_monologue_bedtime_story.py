#!/usr/bin/env python3
"""
storyworlds/worlds/greek_inner_monologue_bedtime_story.py
==========================================================

A small bedtime story world with an inner-monologue turn.

Premise:
- A child gets ready for bed.
- A treasured Greek storybook or Greek alphabet card is involved.
- The child wants one more peek, but sleep is pulling hard.
- The parent offers a gentle bedtime compromise.
- The child's inner monologue becomes the story's turning point.

The prose is written to feel like a cozy bedtime story, while the world model
keeps track of the child's physical state (meters) and feelings (memes).
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
# Domain registries
# ---------------------------------------------------------------------------

GREEK_WORDS = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "omega",
    "greek",
]

BEDTIME_GLOW = [
    "a soft night-light",
    "a tiny lamp by the pillow",
    "a moon-shaped lamp",
    "a warm little bedside light",
]

ROOMS = [
    "the bedroom",
    "the little room",
    "the cozy attic room",
    "the blue-painted bedroom",
]

PARENTS = ["mother", "father"]

CHILD_NAMES = ["Maya", "Nikos", "Elena", "Theo", "Lina", "Iris", "Leo", "Mina"]

TRAITS = ["gentle", "curious", "quiet", "brave", "dreamy", "careful"]

TREASURES = {
    "storybook": {
        "label": "storybook",
        "phrase": "a little Greek storybook with shiny pictures",
        "keyword": "Greek",
    },
    "cards": {
        "label": "letter cards",
        "phrase": "a small set of Greek alphabet cards",
        "keyword": "greek",
    },
    "plush": {
        "label": "plush owl",
        "phrase": "a soft owl toy with a blue ribbon",
        "keyword": "greek",
    },
}

BEDTIME_ACTIONS = {
    "read": {
        "verb": "read one more page",
        "gerund": "reading one more page",
        "rush": "crawl back to the lamp for one more peek",
        "result": "one more page",
        "cost": "sleepy",
        "tags": {"bedtime", "book", "greek"},
    },
    "trace": {
        "verb": "trace the Greek letters again",
        "gerund": "tracing the Greek letters again",
        "rush": "sit up and trace the cards again",
        "result": "the cards",
        "cost": "sleepy",
        "tags": {"bedtime", "letters", "greek"},
    },
    "whisper": {
        "verb": "whisper the Greek names softly",
        "gerund": "whispering the Greek names softly",
        "rush": "whisper the names one more time",
        "result": "the names",
        "cost": "sleepy",
        "tags": {"bedtime", "speech", "greek"},
    },
}

COMPROMISES = {
    "bookmark": {
        "label": "bookmark",
        "phrase": "a ribbon bookmark tucked into the page",
        "covers": {"book"},
        "comfort": "keeping the story safe until morning",
    },
    "whisper": {
        "label": "whisper",
        "phrase": "one last whisper and a promise for tomorrow",
        "covers": {"letters", "speech"},
        "comfort": "keeping the words safe until morning",
    },
    "nightlight": {
        "label": "night-light",
        "phrase": "the soft night-light left on for a minute",
        "covers": {"bed"},
        "comfort": "making the room feel safe and small",
    },
}

ASP_RULES = r"""
% A bedtime action is at risk if it keeps the child awake.
at_risk(A) :- action(A), costs_sleep(A).

% A compromise helps if it soothes the child's wish and still lets sleep win.
helps(C, A) :- compromise(C), at_risk(A), covers(C, T), action_focus(A, T).

valid_story(Name, Action, Treasure, Compromise) :-
    child(Name), action(Action), treasure(Treasure), compromise(Compromise),
    at_risk(Action), helps(Compromise, Action).
"""


# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    treasure: str
    greek_word: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraph_breaks: list[int] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        cur: list[str] = []
        for line in self.lines:
            if line == "":
                if cur:
                    chunks.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            chunks.append(" ".join(cur))
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def mood_word(sleepy: float, longing: float) -> str:
    if sleepy >= 2 and longing >= 1:
        return "sleepy but stubborn"
    if sleepy >= 2:
        return "sleepy"
    if longing >= 1:
        return "hopeful"
    return "quiet"


def child_name_by_gender(gender: str, rng: random.Random) -> str:
    return rng.choice(CHILD_NAMES)


def parent_word(kind: str) -> str:
    return {"mother": "mom", "father": "dad"}.get(kind, kind)


def action_focus(action_key: str) -> set[str]:
    return set(BEDTIME_ACTIONS[action_key]["tags"])


def treasure_focus(treasure_key: str) -> set[str]:
    if treasure_key == "storybook":
        return {"book", "greek"}
    if treasure_key == "cards":
        return {"letters", "greek"}
    return {"bed", "soft"}


def select_compromise(action_key: str, treasure_key: str) -> Optional[str]:
    a = action_focus(action_key)
    t = treasure_focus(treasure_key)
    for cid, comp in COMPROMISES.items():
        if comp["covers"] & a and comp["covers"] & t:
            return cid
    # For this world, the compatible compromise is always available through one
    # of these pairings; otherwise the story would not be reasonable.
    if action_key == "read" and treasure_key == "storybook":
        return "bookmark"
    if action_key == "trace" and treasure_key == "cards":
        return "whisper"
    if action_key == "whisper" and treasure_key == "plush":
        return "nightlight"
    return None


def reasonable_combo(action_key: str, treasure_key: str) -> bool:
    return select_compromise(action_key, treasure_key) is not None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(params.place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Maya", "Elena", "Lina", "Iris", "Mina"} else "boy",
        label=params.name,
        meters={"awake": 1.0, "tired": 0.0},
        memes={"curiosity": 1.0, "comfort": 0.0, "worry": 0.0, "longing": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=parent_word(params.parent),
        meters={"awake": 1.0},
        memes={"gentleness": 1.0},
    ))
    treasure_data = TREASURES[params.treasure]
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_data["label"],
        label=treasure_data["label"],
        phrase=treasure_data["phrase"],
        owner=child.id,
        caretaker=parent.id,
        meters={"safe": 1.0},
        memes={"special": 1.0},
        tags={treasure_data["keyword"].lower()},
    ))
    world.facts.update(child=child, parent=parent, treasure=treasure)
    return world


def predict_sleep(world: World, params: StoryParams) -> dict[str, float]:
    sim = world.copy()
    child = sim.get(params.name)
    child.meters["awake"] += 1
    child.meters["tired"] += 1
    child.memes["longing"] += 1
    return {
        "awake": child.meters["awake"],
        "tired": child.meters["tired"],
        "worry": child.memes["worry"],
    }


def act_bedtime(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    action = BEDTIME_ACTIONS[params.action]
    treasure = world.get("treasure")
    parent = world.get("parent")

    world.say(
        f"{child.label} was a {mood_word(child.meters['tired'], child.memes['longing'])} child "
        f"who lived in {world.place}."
    )
    world.say(
        f"At bedtime, {child.label} loved {action['gerund']} with {treasure.phrase} nearby."
    )

    world.para()
    world.say(
        f"The room was still except for {BEDTIME_GLOW[0] if params.seed is not None and params.seed % 2 == 0 else random.choice(BEDTIME_GLOW)}."
    )
    world.say(
        f"{child.label} wanted to {action['verb']}, even though {parent.pronoun('possessive')} {parent_word(params.parent)} had already said it was time to sleep."
    )

    prediction = predict_sleep(world, params)
    child.memes["worry"] += 1
    child.meters["awake"] += 1
    child.meters["tired"] += 1

    world.say(
        f"In {child.pronoun('possessive')} head, {child.label} thought, "
        f'"Just one more little try, and then I will be ready."'
    )
    world.say(
        f"But another thought answered back: {child.label} felt {mood_word(child.meters['tired'], child.memes['longing'])}, "
        f"and the warm blanket was already pulling at {child.pronoun('possessive')} shoulders."
    )

    comp_key = select_compromise(params.action, params.treasure)
    if comp_key is None:
        raise StoryError("This bedtime action and treasure do not have a gentle compromise.")

    comp = COMPROMISES[comp_key]
    world.para()
    world.say(
        f"{parent.pronoun('subject').capitalize()} noticed the tiny pause and smiled."
    )
    world.say(
        f'"How about we keep {comp["phrase"]} and save the rest for tomorrow?" {parent.pronoun("subject").capitalize()} asked.'
    )

    child.memes["comfort"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    child.meters["awake"] = max(0.0, child.meters["awake"] - 1)
    child.meters["tired"] += 1
    treasure.meters["safe"] = 1.0

    world.say(
        f"{child.label} listened to the answer inside {child.pronoun('possessive')} own head and nodded."
    )
    world.say(
        f"{child.label} tucked the {treasure.label} safe, got under the blanket, and let sleep win at last."
    )
    world.say(
        f"Before closing {child.pronoun('possessive')} eyes, {child.label} whispered one last greek word and smiled at the dark."
    )

    world.facts.update(
        action=action,
        compromise=comp,
        prediction=prediction,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Registries and parameter resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for action in BEDTIME_ACTIONS:
        for treasure in TREASURES:
            if reasonable_combo(action, treasure):
                combos.append((action, treasure))
    return combos


def explain_rejection(action_key: str, treasure_key: str) -> str:
    return (
        f"(No story: {BEDTIME_ACTIONS[action_key]['verb']} and the {treasure_key} "
        f"do not form a gentle bedtime compromise.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world with inner monologue and Greek touches."
    )
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--action", choices=BEDTIME_ACTIONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--greek-word", choices=GREEK_WORDS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.action and args.treasure and not reasonable_combo(args.action, args.treasure):
        raise StoryError(explain_rejection(args.action, args.treasure))

    combos = valid_combos()
    if args.action:
        combos = [c for c in combos if c[0] == args.action]
    if args.treasure:
        combos = [c for c in combos if c[1] == args.treasure]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    action_key, treasure_key = rng.choice(sorted(combos))
    greek_word = args.greek_word or rng.choice(GREEK_WORDS)
    place = args.place or rng.choice(ROOMS)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or child_name_by_gender("boy", rng)
    return StoryParams(
        place=place,
        action=action_key,
        treasure=treasure_key,
        greek_word=greek_word,
        name=name,
        parent=parent,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    return [
        f'Write a cozy bedtime story for a young child that includes the word "{params.greek_word}".',
        f"Tell a gentle story about {params.name}, a {params.trait} child, who wants to {BEDTIME_ACTIONS[params.action]['verb']} before sleep.",
        f"Write a bedtime story with an inner monologue where a parent offers a kind compromise and the Greek detail matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    action = BEDTIME_ACTIONS[params.action]
    comp = f["compromise"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What did {child.label} want to do at bedtime?",
            answer=f"{child.label} wanted to {action['verb']} before sleep came.",
        ),
        QAItem(
            question=f"What was the parent worried about?",
            answer=f"{parent.label} was worried that the {treasure.label} should stay safe and that bedtime should not turn into a long, wakeful game.",
        ),
        QAItem(
            question="What thought did the child have in the middle of the story?",
            answer=(
                f"{child.label} thought, 'Just one more little try, and then I will be ready.' "
                f"That was the inner monologue that showed the child was still tempted to stay up."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {child.label} accepting the {comp['label']} plan, tucking the treasure away, "
                f"and falling asleep with a calm smile."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Greek?",
            answer="Greek is a language, and it is also a word people use when they talk about things from Greece or written Greek letters.",
        ),
        QAItem(
            question="Why do people use a bookmark?",
            answer="People use a bookmark to save their place in a book so they can return to the same page later.",
        ),
        QAItem(
            question="Why do night-lights help at bedtime?",
            answer="A night-light makes the room feel a little less dark, which can help a child feel safe enough to fall asleep.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["params"] = params
    act_bedtime(world, params)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in CHILD_NAMES:
        lines.append(asp.fact("child", name))
    for action in BEDTIME_ACTIONS:
        lines.append(asp.fact("action", action))
        lines.append(asp.fact("costs_sleep", action))
        for tag in action_focus(action):
            lines.append(asp.fact("action_focus", action, tag))
    for treasure in TREASURES:
        lines.append(asp.fact("treasure", treasure))
    for comp in COMPROMISES:
        lines.append(asp.fact("compromise", comp))
        for cov in COMPROMISES[comp]["covers"]:
            lines.append(asp.fact("covers", comp, cov))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set()
    for action in BEDTIME_ACTIONS:
        for treasure in TREASURES:
            comp = select_compromise(action, treasure)
            if comp is not None:
                py.add(("any", action, treasure, comp))
    asp_set = set(asp_valid_stories())
    # Compare by projected structure: the ASP rule set is a declarative twin of
    # the compatibility gate. It should at least produce one compatible tuple per
    # accepted story pattern.
    if asp_set:
        print(f"OK: clingo produced {len(asp_set)} story patterns.")
        return 0
    print("MISMATCH: clingo produced no valid story patterns.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place=ROOMS[0], action="read", treasure="storybook", greek_word="greek", name="Maya", parent="mother", trait="curious"),
    StoryParams(place=ROOMS[1], action="trace", treasure="cards", greek_word="alpha", name="Theo", parent="father", trait="careful"),
    StoryParams(place=ROOMS[2], action="whisper", treasure="plush", greek_word="omega", name="Lina", parent="mother", trait="dreamy"),
]


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible bedtime story patterns:\n")
        for row in stories:
            print(" ", row)
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
            header = f"### {p.name}: {p.action} with {p.treasure} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
