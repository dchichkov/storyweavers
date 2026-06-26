#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/keeper_transmission_outing_dialogue_fable.py
=================================================================================================

A small, standalone story world in a fable-like style.

Premise:
- A keeper prepares for an outing with a young companion.
- A transmission matters because it carries an important warning.
- The keeper must choose between rushing out and sending the message clearly.

The simulated world tracks physical meters and emotional memes so the prose
comes from state changes rather than a fixed paragraph shell.
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
# Data model
# ---------------------------------------------------------------------------
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"keeper", "mother", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Transmission:
    id: str
    label: str
    phrase: str
    channel: str
    speed: str
    clarity: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Outing:
    id: str
    destination: str
    reason: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    weather: str = ""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", kind="outdoor", affords={"outing", "transmission"}),
    "harbor": Setting(place="the harbor", kind="outdoor", affords={"outing", "transmission"}),
    "tower": Setting(place="the old tower room", kind="indoor", affords={"transmission"}),
}

TRANSMISSIONS = {
    "bell": Transmission(
        id="bell",
        label="bell signal",
        phrase="a bright bell signal",
        channel="bell",
        speed="quick",
        clarity="clear",
        keyword="signal",
        tags={"signal", "clear"},
    ),
    "note": Transmission(
        id="note",
        label="paper note",
        phrase="a small paper note",
        channel="note",
        speed="slow",
        clarity="clear",
        keyword="note",
        tags={"note", "clear"},
    ),
    "whisper": Transmission(
        id="whisper",
        label="whispered message",
        phrase="a soft whispered message",
        channel="whisper",
        speed="quick",
        clarity="quiet",
        keyword="whisper",
        tags={"whisper", "quiet"},
    ),
}

OUTINGS = {
    "picnic": Outing(
        id="picnic",
        destination="the meadow",
        reason="share lunch and flowers",
        risk="the path can turn muddy",
        keyword="outing",
        tags={"outing", "meadow"},
    ),
    "harborwalk": Outing(
        id="harborwalk",
        destination="the harbor",
        reason="see the boats and gulls",
        risk="the wind can hide a warning",
        keyword="outing",
        tags={"outing", "harbor"},
    ),
}

KEEPER_NAMES = ["Mina", "Bram", "Tessa", "Jon", "Lena", "Otto"]
COMPANION_NAMES = ["Pip", "Nell", "Toby", "June", "Wren", "Milo"]


@dataclass
class StoryParams:
    place: str
    outing: str
    transmission: str
    keeper_name: str
    companion_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def outing_needs_transmission(outing: Outing, transmission: Transmission, setting: Setting) -> bool:
    if outing.id == "picnic":
        return transmission.id in {"bell", "note"}
    if outing.id == "harborwalk":
        return transmission.id in {"bell", "whisper"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for outing_id, outing in OUTINGS.items():
            if outing.destination != setting.place:
                continue
            for tx_id, tx in TRANSMISSIONS.items():
                if outing_needs_transmission(outing, tx, setting):
                    combos.append((place, outing_id, tx_id))
    return combos


def explain_rejection(outing: Outing, transmission: Transmission) -> str:
    return (
        f"(No story: {outing.reason}, but {transmission.label} does not fit that outing. "
        f"Choose a message that can travel well in that place.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def tell(setting: Setting, outing: Outing, tx: Transmission, keeper_name: str, companion_name: str) -> World:
    world = World(setting=setting)
    world.weather = "soft rain" if setting.kind == "outdoor" and outing.id == "picnic" else "wind"

    keeper = world.add(Entity(id=keeper_name, kind="character", type="keeper", label="keeper"))
    child = world.add(Entity(id=companion_name, kind="character", type="child", label="young companion", plural=False))
    message = world.add(Entity(id="transmission", type=tx.id, label=tx.label, phrase=tx.phrase, owner=keeper.id))
    outing_ent = world.add(Entity(id="outing", type=outing.id, label="outing", phrase=outing.reason, owner=child.id))

    # Beginning
    world.say(
        f"There was once a keeper named {keeper.id} who watched the path by {setting.place}. "
        f"One morning, {keeper.id} told {child.id}, \"Today is an {outing.keyword}.\""
    )
    _set_meme(keeper, "care", 1)
    _set_meme(child, "joy", 1)
    world.say(
        f"{child.id} smiled and said, \"Will we go right away?\" "
        f"{keeper.id} answered, \"Only after the transmission is sent.\""
    )

    # Middle: tension
    world.para()
    _set_meme(keeper, "worry", 1)
    _set_meme(child, "impatience", 1)
    _set_meter(message, "clarity", 1)
    world.say(
        f"The keeper lifted {message.it()} and looked toward {setting.place}. "
        f"{tx.clarity.capitalize()} was needed, because {outing.risk}."
    )
    world.say(
        f"\"If we rush, the message may blur,\" {keeper.id} said. "
        f"\"But the outing begins soon,\" {child.id} said, tapping a small foot."
    )

    # Turn: the keeper chooses a careful method.
    if tx.id == "bell":
        _set_meter(message, "sound", 1)
        _set_meme(keeper, "resolve", 1)
        world.say(
            f"{keeper.id} rang the bell three times and waited for the sound to travel. "
            f"\"A clear ring is kinder than a hurried shout,\" {keeper.id} said."
        )
    elif tx.id == "note":
        _set_meter(message, "ink", 1)
        _set_meme(keeper, "patience", 1)
        world.say(
            f"{keeper.id} wrote the note slowly and tied it to a bright string. "
            f"\"A careful note reaches farther than a careless one,\" {keeper.id} said."
        )
    else:
        _set_meter(message, "whisper", 1)
        _set_meme(keeper, "patience", 1)
        world.say(
            f"{keeper.id} bent close and whispered the warning twice. "
            f"\"Soft words can still be sure words,\" {keeper.id} said."
        )

    world.para()
    _set_meme(child, "trust", 1)
    world.say(
        f"{child.id} nodded and said, \"Then I will wait.\" "
        f"{keeper.id} smiled, because the transmission had gone through clean and true."
    )
    world.say(
        f"At last, they went on the {outing.keyword} together, and {outing.reason} as planned."
    )

    # Resolution
    _set_meme(keeper, "peace", 1)
    _set_meme(child, "joy", 1)
    world.say(
        f"The keeper and the child walked side by side. "
        f"The wind still blew, but the warning had already arrived, and the outing stayed safe."
    )
    world.say(
        f"So the keeper learned that a message sent with care can guide a whole day."
    )

    world.facts.update(
        keeper=keeper,
        child=child,
        transmission=tx,
        outing=outing,
        setting=setting,
        message=message,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    keeper = f["keeper"]
    child = f["child"]
    tx = f["transmission"]
    outing = f["outing"]
    return [
        f'Write a short fable about a keeper, a transmission, and an outing, with dialogue and a gentle lesson.',
        f"Tell a child-friendly story where {keeper.id} must send {tx.phrase} before {child.id}'s {outing.keyword}.",
        f"Write a simple fable about how {tx.label} helped keep an outing safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = f["keeper"]
    child = f["child"]
    tx = f["transmission"]
    outing = f["outing"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a keeper named {keeper.id} and a young companion named {child.id}.",
        ),
        QAItem(
            question=f"What did {keeper.id} need to send before the outing?",
            answer=f"{keeper.id} needed to send {tx.phrase} before the outing could begin safely.",
        ),
        QAItem(
            question=f"Why did the keeper want the transmission to be clear?",
            answer=f"The keeper wanted it to be clear because {outing.risk}, so the warning had to reach the child without being muddled.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {keeper.id} and {child.id} going on the outing together after the warning arrived safely.",
        ),
    ]


KNOWLEDGE = {
    "signal": [
        QAItem(
            question="What is a signal?",
            answer="A signal is a sign or message that tells someone what to do or what is happening.",
        )
    ],
    "outing": [
        QAItem(
            question="What is an outing?",
            answer="An outing is a short trip or walk that people take for fun, learning, or a visit.",
        )
    ],
    "note": [
        QAItem(
            question="What is a note?",
            answer="A note is a small piece of writing used to tell or remind someone of something.",
        )
    ],
    "whisper": [
        QAItem(
            question="What is a whisper?",
            answer="A whisper is a very soft way of speaking so only someone nearby can hear.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["transmission"].tags) | set(world.facts["outing"].tags)
    out: list[QAItem] = []
    for tag in ["signal", "outing", "note", "whisper"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A transmission is suitable when it matches the outing's needs.
suitable(Place, O, T) :- setting(Place), outing(O), transmission(T),
                         affords(Place, O), supports(O, T).

valid_story(Place, O, T) :- suitable(Place, O, T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, o in OUTINGS.items():
        lines.append(asp.fact("outing", oid))
        for t in sorted(o.tags):
            lines.append(asp.fact("out_tag", oid, t))
    for tid, t in TRANSMISSIONS.items():
        lines.append(asp.fact("transmission", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tx_tag", tid, tag))
        if tid == "bell":
            lines.append(asp.fact("supports", "picnic", tid))
        if tid == "note":
            lines.append(asp.fact("supports", "picnic", tid))
        if tid == "whisper":
            lines.append(asp.fact("supports", "harborwalk", tid))
        if tid == "bell":
            lines.append(asp.fact("supports", "harborwalk", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like keeper / transmission / outing story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--outing", choices=OUTINGS)
    ap.add_argument("--transmission", choices=TRANSMISSIONS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.outing and args.transmission:
        o = OUTINGS[args.outing]
        t = TRANSMISSIONS[args.transmission]
        if not outing_needs_transmission(o, t, SETTINGS[args.place or next(iter(SETTINGS))]):
            raise StoryError(explain_rejection(o, t))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.outing is None or c[1] == args.outing)
        and (args.transmission is None or c[2] == args.transmission)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, outing, tx = rng.choice(sorted(combos))
    keeper_name = args.name or rng.choice(KEEPER_NAMES)
    companion_name = args.companion or rng.choice(COMPANION_NAMES)
    return StoryParams(place=place, outing=outing, transmission=tx, keeper_name=keeper_name, companion_name=companion_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OUTINGS[params.outing], TRANSMISSIONS[params.transmission],
                 params.keeper_name, params.companion_name)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="meadow", outing="picnic", transmission="bell", keeper_name="Mina", companion_name="Pip"),
    StoryParams(place="harbor", outing="harborwalk", transmission="whisper", keeper_name="Bram", companion_name="Nell"),
    StoryParams(place="meadow", outing="picnic", transmission="note", keeper_name="Tessa", companion_name="Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, outing, tx in combos:
            print(f"  {place:8} {outing:12} {tx}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
