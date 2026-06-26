#!/usr/bin/env python3
"""
storyworlds/worlds/protector_agency_gibberish_sound_effects_kindness_misunderstanding.py
========================================================================================

A small heartwarming storyworld about a child, a protector agency, a confusing
message full of gibberish, and the kind sound effects that help everyone sort
out a misunderstanding.

The premise:
- A child worries that a neighborhood "protector agency" sounds scary or bossy.
- A scrambled message full of gibberish makes the child think a helper has sent
  a warning.
- In truth, the agency is a gentle group that uses friendly sound effects and
  simple kindness to communicate.
- A misunderstanding is cleared when the child hears the right sounds and sees
  the agency helping in a calm, caring way.

The model tracks:
- Physical meters: distance, noise, mess, tokens, and small object states.
- Emotional memes: worry, trust, kindness, confusion, relief, confidence.

The prose is generated from the simulated state, not from a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
    indoor: bool = False
    acoustic: str = ""
    notes: str = ""


@dataclass
class Signal:
    id: str
    label: str
    sound: str
    intended_meaning: str
    muddled_meaning: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Protector:
    id: str
    label: str
    help_verb: str
    kindness_action: str
    sound_effect: str
    calm_effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "market": Place(
        id="market",
        label="the little market street",
        indoor=False,
        acoustic="busy and bright",
        notes="Stalls, bells, and soft footsteps blend together here.",
    ),
    "library": Place(
        id="library",
        label="the quiet library hall",
        indoor=True,
        acoustic="gentle and hushed",
        notes="Even whispers and page turns sound important here.",
    ),
    "courtyard": Place(
        id="courtyard",
        label="the sunny courtyard",
        indoor=False,
        acoustic="open and echoing",
        notes="The walls bounce little sounds back like a playful game.",
    ),
}

SIGNALS = {
    "gibberish_note": Signal(
        id="gibberish_note",
        label="a scribbly note",
        sound="zip-zap, blorble, tippity-tap",
        intended_meaning="a friendly request for help",
        muddled_meaning="a stern warning or an angry order",
        clue="the note had funny loops and a smiling little stamp",
        tags={"gibberish"},
    ),
    "knock_pattern": Signal(
        id="knock_pattern",
        label="a knock pattern",
        sound="tok-tok... tok!",
        intended_meaning="someone is coming with a warm hello",
        muddled_meaning="someone is upset or in a hurry",
        clue="the knocks were light, patient, and spaced like dancing steps",
        tags={"sound_effects"},
    ),
    "humming_tune": Signal(
        id="humming_tune",
        label="a humming tune",
        sound="mmm-hmm, mmm-hmm",
        intended_meaning="everything is okay and help is on the way",
        muddled_meaning="a secret plan or a mysterious warning",
        clue="the tune matched the helper badges' little stars",
        tags={"sound_effects", "kindness"},
    ),
}

PROTECTORS = {
    "snack_team": Protector(
        id="snack_team",
        label="the protector agency snack team",
        help_verb="bring snacks",
        kindness_action="share crackers and warm apple slices",
        sound_effect="crinkle-crinkle",
        calm_effect="the room feels softer and safer",
        tags={"protector", "agency", "kindness"},
    ),
    "lamp_team": Protector(
        id="lamp_team",
        label="the protector agency lamp team",
        help_verb="fix the lamp",
        kindness_action="offer a blanket while they work",
        sound_effect="click-whirr",
        calm_effect="the shadows get smaller and friendlier",
        tags={"protector", "agency", "sound_effects"},
    ),
    "book_team": Protector(
        id="book_team",
        label="the protector agency book team",
        help_verb="sort the books",
        kindness_action="leave tiny notes with doodled hearts",
        sound_effect="thump-thump, shffft",
        calm_effect="the shelves become neat and welcoming",
        tags={"protector", "agency", "kindness"},
    ),
}

HERO_NAMES = ["Mina", "Owen", "Lila", "Noah", "Tessa", "Eli", "Maya", "Theo"]
ADULT_NAMES = ["Aunt June", "Mr. Reed", "Nina", "Papa Jo", "Ms. Vale"]
TRAITS = ["curious", "gentle", "careful", "bright-eyed", "shy", "cheerful"]


@dataclass
class StoryParams:
    place: str
    signal: str
    protector: str
    name: str
    trait: str
    adult: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def setting_detail(place: Place) -> str:
    if place.indoor:
        return f"The air in {place.label} was {place.acoustic}, with small sounds bouncing softly off the walls."
    return f"{place.label.capitalize()} felt {place.acoustic}, full of little noises and warm daylight."


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    signal = SIGNALS[params.signal]
    protector = PROTECTORS[params.protector]
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Lila", "Tessa", "Maya"} else "boy",
        label=params.name,
        phrase=f"a {params.trait} child",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "confusion": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type="mother" if "Aunt" not in params.adult and "Mr." not in params.adult and "Papa" not in params.adult else "father",
        label=params.adult,
        phrase=params.adult,
        memes={"worry": 0.0, "trust": 0.0},
    ))
    sig = world.add(Entity(
        id=signal.id,
        type="signal",
        label=signal.label,
        phrase=signal.label,
        meters={"misread": 0.0},
    ))
    team = world.add(Entity(
        id=protector.id,
        type="agency",
        label=protector.label,
        phrase=protector.label,
        memes={"kindness": 0.0, "confidence": 0.0},
    ))

    world.facts.update(child=child, adult=adult, signal=sig, protector=team, signal_def=signal, protector_def=protector)
    return world


def apply_misunderstanding(world: World) -> None:
    child = world.facts["child"]
    sig: Signal = world.facts["signal_def"]
    adult = world.facts["adult"]

    add_meme(child, "confusion", 1.0)
    add_meme(child, "worry", 1.0)
    add_meter(world.get(sig.id), "misread", 1.0)
    add_meme(adult, "trust", 0.5)
    world.trace_log.append("misunderstanding: child misreads the gibberish note")


def apply_clue(world: World) -> None:
    child = world.facts["child"]
    sig: Signal = world.facts["signal_def"]
    if meter(world.get(sig.id), "misread") >= THRESHOLD:
        add_meter(child, "distance", 1.0)
        add_meme(child, "confusion", 0.5)
        world.trace_log.append("clue noticed: the funny stamp and light knocks suggest kindness")


def apply_kindness(world: World) -> None:
    child = world.facts["child"]
    adult = world.facts["adult"]
    team = world.facts["protector"]
    protector: Protector = world.facts["protector_def"]

    add_meme(team, "kindness", 1.0)
    add_meme(team, "confidence", 1.0)
    add_meme(child, "trust", 1.0)
    add_meme(adult, "trust", 1.0)
    add_meme(child, "worry", -0.5)
    add_meme(child, "confusion", -0.5)
    add_meme(child, "relief", 1.0)
    world.trace_log.append(f"kindness: {protector.kindness_action}")
    world.trace_log.append(f"sound effect: {protector.sound_effect}")


def resolve_story(world: World) -> None:
    child = world.facts["child"]
    adult = world.facts["adult"]
    signal: Signal = world.facts["signal_def"]
    protector: Protector = world.facts["protector_def"]

    if meme(child, "trust") >= THRESHOLD and meme(child, "relief") >= THRESHOLD:
        add_meter(child, "distance", -1.0)
        world.trace_log.append("resolution: the child steps closer and understands the message")
        add_meme(adult, "trust", 0.5)


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro_paragraph(world: World) -> None:
    child: Entity = world.facts["child"]
    signal: Signal = world.facts["signal_def"]
    protector: Protector = world.facts["protector_def"]

    world.say(
        f"{child.label} was a {world.facts['child'].phrase} who liked quiet things, "
        f"but the words 'protector agency' sounded big and a little scary."
    )
    world.say(
        f"Then a note arrived with {signal.sound} written across it, and {child.label} could not tell if it meant {signal.intended_meaning} or {signal.muddled_meaning}."
    )


def tension_paragraph(world: World) -> None:
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]
    signal: Signal = world.facts["signal_def"]
    place: Place = world.place

    world.say(setting_detail(place))
    world.say(
        f"{child.label} pointed at the note and frowned. "
        f'"{signal.sound}?" {child.pronoun("subject").capitalize()} whispered, '
        f"and it felt more like a puzzle than a promise."
    )
    world.say(
        f"{adult.label} noticed the wobble in {child.pronoun('possessive')} voice and said, "
        f'"Let us look again before we decide anything."'
    )


def turn_paragraph(world: World) -> None:
    child: Entity = world.facts["child"]
    signal: Signal = world.facts["signal_def"]
    protector: Protector = world.facts["protector_def"]

    world.say(
        f"That was when {child.label} saw the small clue: {signal.clue}."
    )
    world.say(
        f"Right then, the protector agency arrived with {protector.sound_effect}, "
        f"and instead of rushing, they smiled and offered {protector.kindness_action}."
    )


def ending_paragraph(world: World) -> None:
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]
    protector: Protector = world.facts["protector_def"]

    world.say(
        f"{child.label} laughed in surprise, because the agency was not bossy at all; "
        f"they were careful helpers who made the day feel safe."
    )
    world.say(
        f"By the end, {child.label} walked beside {adult.label} with a steady heart, "
        f"while {protector.label} kept working nearby and the little sound effects "
        f"felt kind instead of confusing."
    )


def trace_state(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 3) for k, v in ent.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    if world.trace_log:
        lines.append("  events:")
        for item in world.trace_log:
            lines.append(f"    - {item}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    signal: Signal = world.facts["signal_def"]
    protector: Protector = world.facts["protector_def"]
    place: Place = world.place
    return [
        f"Write a heartwarming story about {child.label}, a protector agency, and a confusing message full of {signal.id.replace('_', ' ')}.",
        f"Tell a gentle story set in {place.label} where {child.label} misreads {signal.sound} but learns the meaning with kindness.",
        f"Write a child-friendly story that includes a misunderstanding, friendly sound effects, and {protector.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]
    signal: Signal = world.facts["signal_def"]
    protector: Protector = world.facts["protector_def"]

    return [
        QAItem(
            question=f"Why did {child.label} first feel unsure about the note?",
            answer=f"{child.label} felt unsure because the note used {signal.sound} and looked like gibberish, so it could be read in the wrong way.",
        ),
        QAItem(
            question=f"What did the protector agency do that helped clear up the misunderstanding?",
            answer=f"The protector agency arrived with {protector.sound_effect}, stayed calm, and offered {protector.kindness_action}, which helped the message feel friendly.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end of the story?",
            answer=f"{child.label} felt relieved and brave at the end, because the note turned out to be a kind offer of help instead of a scary warning.",
        ),
        QAItem(
            question=f"Who stayed close to {child.label} while everything made sense again?",
            answer=f"{adult.label} stayed close and helped {child.label} look again before deciding what the note meant.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    signal: Signal = world.facts["signal_def"]
    protector: Protector = world.facts["protector_def"]
    out = [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a message means one thing, but it really means something else.",
        ),
        QAItem(
            question="Why can sound effects help people understand each other?",
            answer="Sound effects can carry clues, like a gentle knock or a happy hum, that help people guess whether a message is kind or serious.",
        ),
        QAItem(
            question="What does kindness do in a story?",
            answer="Kindness helps people feel safe, listen carefully, and fix problems without hurting anyone's feelings.",
        ),
    ]
    if "gibberish" in signal.tags:
        out.append(
            QAItem(
                question="What is gibberish?",
                answer="Gibberish is speech or writing that seems scrambled or hard to understand, so it can be confusing at first.",
            )
        )
    if "kindness" in protector.tags:
        out.append(
            QAItem(
                question="What is a protector agency in this story world?",
                answer="A protector agency is a group of helpful people who come with practical help and calm kindness when someone needs support.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A misunderstanding happens when a signal is marked as misread.
misunderstanding(S) :- signal(S), misread(S).

% Kindness from a protector agency can resolve misunderstanding when both are present.
can_resolve(P, S) :- protector(P), signal(S), kind_action(P), sound_help(P, S).
resolved(S) :- misunderstanding(S), can_resolve(_, S).

% A story is reasonable only if the signal can be misread and the protector can help.
valid_story(Place, Signal, Protector) :- place(Place), signal(Signal), protector(Protector),
                                          misreadable(Signal), kind_action(Protector),
                                          sound_help(Protector, Signal).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
    for sid, sig in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        if "gibberish" in sig.tags:
            lines.append(asp.fact("misreadable", sid))
        for tag in sig.tags:
            lines.append(asp.fact("signal_tag", sid, tag))
    for pid, prot in PROTECTORS.items():
        lines.append(asp.fact("protector", pid))
        lines.append(asp.fact("kind_action", pid))
        for tag in prot.tags:
            lines.append(asp.fact("protector_tag", pid, tag))
        # simple hand-coded link: every protector can help with every signal in this tiny world
        for sid in SIGNALS:
            lines.append(asp.fact("sound_help", pid, sid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (place, sig, prot)
        for place in PLACES
        for sig in SIGNALS
        for prot in PROTECTORS
        if SIGNALS[sig].id and PROTECTORS[prot].id
    }
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches the simple Python story space ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro_paragraph(world)
    world.para()
    apply_misunderstanding(world)
    tension_paragraph(world)
    world.para()
    apply_clue(world)
    apply_kindness(world)
    resolve_story(world)
    turn_paragraph(world)
    world.para()
    ending_paragraph(world)
    return world


# ---------------------------------------------------------------------------
# Parameter resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for signal in SIGNALS:
            for prot in PROTECTORS:
                combos.append((place, signal, prot))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world about a protector agency, gibberish, sound effects, kindness, and misunderstanding."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--signal", choices=sorted(SIGNALS))
    ap.add_argument("--protector", choices=sorted(PROTECTORS))
    ap.add_argument("--name", choices=sorted(HERO_NAMES))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--adult", choices=sorted(ADULT_NAMES))
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
    place = args.place or rng.choice(list(PLACES))
    signal = args.signal or rng.choice(list(SIGNALS))
    protector = args.protector or rng.choice(list(PROTECTORS))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(place=place, signal=signal, protector=protector, name=name, trait=trait, adult=adult)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(trace_state(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="market", signal="gibberish_note", protector="snack_team", name="Mina", trait="curious", adult="Aunt June"),
        StoryParams(place="library", signal="knock_pattern", protector="book_team", name="Theo", trait="shy", adult="Ms. Vale"),
        StoryParams(place="courtyard", signal="humming_tune", protector="lamp_team", name="Lila", trait="cheerful", adult="Nina"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, signal, protector) combos:\n")
        for place, sig, prot in stories:
            print(f"  {place:10} {sig:16} {prot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.signal} / {p.protector}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
