#!/usr/bin/env python3
"""
storyworlds/worlds/incubator_lone_snip_dialogue_magic_twist_detective.py
========================================================================

A small detective-story world with a lone investigator, a magical snip,
and a twist revealed through dialogue.

Premise:
- A lone detective is called to a greenhouse nursery where an incubator hums.
- Something small keeps vanishing from the warm tray.
- The detective uses clues, dialogue, and a little magic to solve it.
- The twist: the "thief" is not a person, but a wayward ribbon-botched latch
  inside the incubator door, which was hiding a rescued chick.

The world is modeled as stateful entities with physical meters and emotional
memes. The prose is generated from the simulated investigation, not from a
frozen template.

Supported CLI:
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
# World entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    evening: bool = False
    silence: str = "quiet hum"


@dataclass
class Clue:
    id: str
    line: str
    reveal: str
    meter: str = "certainty"


@dataclass
class StoryParams:
    setting: str
    detective: str
    sidekick: str
    suspect: str
    clue: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", evening=False, silence="warm hum"),
    "greenhouse": Setting(place="the greenhouse", evening=True, silence="soft drip"),
    "station": Setting(place="the tiny station office", evening=True, silence="tick of a clock"),
}

DETECTIVES = {
    "mira": ("girl", "Mira", "a lone little detective with a bright notebook"),
    "otis": ("boy", "Otis", "a lone little detective with careful eyes"),
    "nina": ("girl", "Nina", "a lone little detective with a wool coat"),
}

SIDEKICKS = {
    "lamp": ("thing", "lamp", "a brass lamp", "little lamp"),
    "moth": ("thing", "moth", "a gray moth", "small moth"),
    "mouse": ("thing", "mouse", "a tidy mouse", "tiny mouse"),
}

SUSPECTS = {
    "caretaker": ("woman", "caretaker", "the tired caretaker"),
    "trader": ("man", "trader", "the ribbon trader"),
    "clock": ("thing", "clock", "the old clock"),
}

CLUES = {
    "snip": Clue(
        id="snip",
        line="There was a clean snip in the ribbon by the incubator latch.",
        reveal="The snip was too neat to be an accident.",
        meter="certainty",
    ),
    "glow": Clue(
        id="glow",
        line="A small golden glow flickered under the incubator lid.",
        reveal="Something magical was hiding under the lid.",
        meter="mystery",
    ),
    "feather": Clue(
        id="feather",
        line="A pale feather rested on the floor beside the warm tray.",
        reveal="A chick had been close by.",
        meter="hope",
    ),
}

TRAITS = ["lone", "patient", "sharp", "kind", "careful"]
NAMES = ["Mira", "Otis", "Nina"]


# ---------------------------------------------------------------------------
# Reasonableness / world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _clue_found(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes.get("observation", 0.0) < THRESHOLD:
        return out
    if world.facts.get("clue_seen"):
        return out
    world.facts["clue_seen"] = True
    clue = CLUES[world.facts["clue"]]
    out.append(clue.line)
    detective.memes["mystery"] = detective.memes.get("mystery", 0.0) + 1
    return out


def _magic_glow(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("magic_used"):
        return out
    if world.facts.get("glow_done"):
        return out
    world.facts["glow_done"] = True
    world.get("incubator").meters["glow"] = 1.0
    out.append("The incubator gave off a soft glow, as if it wanted to tell the truth.")
    return out


def _twist_reveal(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("twist_ready"):
        return out
    if world.facts.get("twist_done"):
        return out
    world.facts["twist_done"] = True
    chick = world.get("chick")
    chick.meters["safe"] = 1.0
    out.append("Inside the incubator, the missing chick was safe, tucked behind the loose latch.")
    return out


RULES = [
    ("clue", _clue_found),
    ("magic", _magic_glow),
    ("twist", _twist_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    detective_type, detective_name, detective_phrase = DETECTIVES[params.detective]
    side_type, side_label, side_phrase, side_name = SIDEKICKS[params.sidekick]
    suspect_type, suspect_label, suspect_phrase = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]

    detective = world.add(
        Entity(
            id="detective",
            kind="character",
            type=detective_type,
            label=detective_name,
            phrase=detective_phrase,
            location=setting.place,
            meters={"attention": 0.0, "certainty": 0.0, "magic": 0.0},
            memes={"lone": 1.0, "curiosity": 1.0},
        )
    )
    sidekick = world.add(
        Entity(
            id="sidekick",
            kind="character",
            type=side_type,
            label=side_name,
            phrase=side_phrase,
            location=setting.place,
            meters={"attention": 0.0},
            memes={"helpfulness": 1.0},
        )
    )
    suspect = world.add(
        Entity(
            id="suspect",
            kind="character" if suspect_type != "thing" else "thing",
            type=suspect_type,
            label=suspect_label,
            phrase=suspect_phrase,
            location=setting.place,
            meters={"nervous": 0.0},
            memes={"worry": 0.0},
        )
    )
    incubator = world.add(
        Entity(
            id="incubator",
            kind="thing",
            type="incubator",
            label="incubator",
            phrase="a humming incubator",
            location=setting.place,
            meters={"warmth": 1.0, "glow": 0.0},
            memes={"secret": 0.0},
        )
    )
    snip = world.add(
        Entity(
            id="sniptool",
            kind="thing",
            type="scissors",
            label="snip",
            phrase="a tiny silver snip",
            location=setting.place,
            magical=True,
            meters={"sharpness": 1.0},
            memes={"magic": 1.0},
        )
    )
    chick = world.add(
        Entity(
            id="chick",
            kind="thing",
            type="chick",
            label="chick",
            phrase="a small chick",
            location="inside incubator",
            meters={"safe": 0.0},
            memes={"fear": 0.0},
        )
    )

    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        suspect=suspect,
        incubator=incubator,
        snip=snip,
        chick=chick,
        clue=clue.id,
        magic_used=False,
        twist_ready=False,
    )

    # Act 1
    world.say(f"At {setting.place}, a {params.detective} detective named {detective_name} worked alone.")
    world.say(f"{detective_name} liked the quiet hum of the incubator, but this morning something felt off.")
    world.say(f'“I only need one good clue,” {detective_name} said to {side_name}.')
    world.say(f'{side_name} answered, “Then let’s look where the light and the dust meet.”')
    detective.meters["attention"] += 1
    sidekick.meters["attention"] += 1

    # Act 2
    world.para()
    world.say(f"{detective_name} knelt by the incubator and examined the latch.")
    world.say(clue.line)
    detective.meters["certainty"] += 1
    world.say(f'“That snip is too neat,” {detective_name} said. “Someone wanted the latch open without a struggle.”')
    suspect.meters["nervous"] += 1
    world.say(f'“I only carried ribbons,” {suspect_phrase} muttered. “I did not touch the warm tray.”')
    world.say(f'{side_name} pointed at a faint glow and whispered, “Maybe the incubator is hiding the rest of the answer.”')
    detective.memes["lone"] = 0.5
    world.facts["magic_used"] = True
    propagate(world, narrate=True)

    # Act 3
    world.para()
    world.say(f"{detective_name} held up the tiny snip and tried it on the loose ribbon.")
    world.say(f'“Open the latch gently,” {detective_name} said, “and tell me what you were protecting.”')
    world.facts["twist_ready"] = True
    propagate(world, narrate=True)
    world.say(f"The door clicked, and the hidden chick blinked up from the warm shadows.")
    world.say(f'“You were not stealing,” {detective_name} said softly. “You were sheltering a frightened chick.”')
    world.say(f'{suspect_phrase} let out a relieved breath. “I cut the ribbon so the door would not jam on it.”')
    world.say(f'{side_name} smiled. “A very suspicious snip that turned out to be kindness.”')
    detective.memes["curiosity"] = 0.0
    detective.memes["mystery"] = 0.0

    world.facts.update(setting=setting, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short detective story for a child that includes "incubator", "lone", and "snip".',
        f"Tell a mystery where {p.detective} is a lone detective, hears a dialogue clue, and finds a magical twist.",
        f"Write a gentle detective tale in which a snip near an incubator leads to a surprising answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    detective = world.get("detective").label
    sidekick = world.get("sidekick").label
    suspect = world.get("suspect").phrase
    return [
        QAItem(
            question=f"Who was the lone detective in the story?",
            answer=f"The lone detective was {detective}, who worked carefully through the quiet case.",
        ),
        QAItem(
            question=f"What clue did {detective} notice near the incubator?",
            answer="The detective noticed a clean snip in the ribbon by the incubator latch.",
        ),
        QAItem(
            question=f"What did {sidekick} help {detective} do with the mystery?",
            answer=f"{sidekick} helped {detective} look closely, listen to the dialogue, and follow the glow to the right answer.",
        ),
        QAItem(
            question=f"Why did {suspect} seem suspicious at first?",
            answer=f"{suspect} seemed suspicious because of the snip and the worried words about the tray and the latch.",
        ),
        QAItem(
            question="What was the twist at the end?",
            answer="The twist was that the incubator was not hiding a thief. It was hiding a safe little chick behind the loose latch.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "incubator": [
        QAItem(
            question="What is an incubator for?",
            answer="An incubator is a warm container or room that helps eggs or tiny babies stay safe and warm until they are ready.",
        )
    ],
    "snip": [
        QAItem(
            question="What can a snip mean?",
            answer="A snip can mean a tiny cut made by scissors or something that has been neatly cut.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is something surprising and impossible in real life, like a glow that reveals a secret.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the answer different from what you first expected.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = ["detective", "incubator", "snip", "magic", "twist"]
    out: list[QAItem] = []
    for k in keys:
        out.extend(WORLD_KNOWLEDGE.get(k, []))
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
setting(nursery).
setting(greenhouse).
setting(station).

detective(mira). detective(otis). detective(nina).
sidekick(lamp). sidekick(moth). sidekick(mouse).
suspect(caretaker). suspect(trader). suspect(clock).
clue(snip). clue(glow). clue(feather).

has_setting(S) :- setting(S).
has_detective(D) :- detective(D).
has_sidekick(K) :- sidekick(K).
has_suspect(X) :- suspect(X).
has_clue(C) :- clue(C).

valid_story(S,D,K,X,C) :- has_setting(S), has_detective(D), has_sidekick(K), has_suspect(X), has_clue(C).
#show valid_story/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for k in DETECTIVES:
        lines.append(asp.fact("detective", k))
    for k in SIDEKICKS:
        lines.append(asp.fact("sidekick", k))
    for k in SUSPECTS:
        lines.append(asp.fact("suspect", k))
    for k in CLUES:
        lines.append(asp.fact("clue", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = len(SETTINGS) * len(DETECTIVES) * len(SIDEKICKS) * len(SUSPECTS) * len(CLUES)
    got = len(asp_valid_stories())
    if expected != got:
        print(f"MISMATCH: expected {expected}, got {got}")
        return 1
    print(f"OK: ASP emits {got} valid story combinations.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a magical twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    detective = args.detective or rng.choice(list(DETECTIVES))
    sidekick = args.sidekick or rng.choice(list(SIDEKICKS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    clue = args.clue or rng.choice(list(CLUES))
    return StoryParams(setting=setting, detective=detective, sidekick=sidekick, suspect=suspect, clue=clue)


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
    lines.append(f"  facts: {world.facts}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid detective story combinations:")
        for tup in stories:
            print("  ", tup)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for d in DETECTIVES:
                for k in SIDEKICKS:
                    for x in SUSPECTS:
                        for c in CLUES:
                            params = StoryParams(setting=s, detective=d, sidekick=k, suspect=x, clue=c)
                            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
