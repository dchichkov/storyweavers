#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit: a missing syringe, a revolutionary
with a loud grudge, and a tyrant who may not be as honest as he seems.

This world keeps a small simulated mystery engine:
- physical meters track where the syringe is, whether a room is searched, and
  whether clues are found;
- emotional memes track suspicion, alarm, relief, and pride;
- the story turns on a clue chain and a twist that changes who looked guilty.

The setting, suspect, and solution are all constrained so the story stays
coherent and child-facing.
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
# Core entities and world model
# ---------------------------------------------------------------------------
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
        female = {"girl", "woman", "mother", "queen", "detective"}
        male = {"boy", "man", "father", "king", "tyrant", "revolutionary"}
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
    clue_places: set[str] = field(default_factory=set)
    public_places: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    role: str
    motive: str
    alibi: str
    tells: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "infirmary": Setting(
        place="the old infirmary",
        clue_places={"supply closet", "bedside cart", "wash basin"},
        public_places={"waiting bench", "front desk", "hallway"},
    ),
    "workshop": Setting(
        place="the lantern workshop",
        clue_places={"tool shelf", "ink table", "storage nook"},
        public_places={"workbench", "doorway", "lamp rack"},
    ),
    "station": Setting(
        place="the little train station",
        clue_places={"ticket booth", "baggage shelf", "signal room"},
        public_places={"platform", "bench", "counter"},
    ),
}

SUSPECTS = {
    "revolutionary": Suspect(
        id="revolutionary",
        label="the revolutionary",
        type="revolutionary",
        role="a loud protester",
        motive="wanted to stop the tyrant from getting the treatment",
        alibi="had been stamping flyers by the door",
        tells=["ink on the cuff", "a torn flyer corner", "a stray stamp mark"],
    ),
    "tyrant": Suspect(
        id="tyrant",
        label="the tyrant",
        type="tyrant",
        role="the boss who feared looking weak",
        motive="wanted to hide the syringe and avoid the shot",
        alibi="said he never left his chair",
        tells=["dust on the sleeve", "a squeaky chair wheel", "a hidden key ring"],
    ),
    "apothecary": Suspect(
        id="apothecary",
        label="the apothecary",
        type="woman",
        role="the careful keeper of supplies",
        motive="wanted the room tidy and the tools counted",
        alibi="was checking bottles at the sink",
        tells=["clean hands", "a fresh inventory list", "a measured cap"],
    ),
}

# The syringe is the key object in every mystery.
CLIUE = Entity(
    id="syringe",
    kind="thing",
    type="syringe",
    label="syringe",
    phrase="a small glass syringe with a blue rubber bulb",
    location="supply closet",
    meters={"missing": 1.0, "hidden": 1.0},
    memes={"alarm": 1.0},
)

HERO = Entity(
    id="pip",
    kind="character",
    type="boy",
    label="Pip",
    phrase="a careful little detective",
    meters={"search": 0.0},
    memes={"curiosity": 1.0, "pride": 0.0, "relief": 0.0},
)

TYRANT = Entity(
    id="tyrant",
    kind="character",
    type="man",
    label="the tyrant",
    phrase="a grumpy man with a big chair",
    meters={"nervous": 0.0},
    memes={"alarm": 0.0, "shame": 0.0},
)

REVOLUTIONARY = Entity(
    id="revolutionary",
    kind="character",
    type="revolutionary",
    label="the revolutionary",
    phrase="a fiery speaker with a red scarf",
    meters={"fury": 0.0},
    memes={"anger": 0.0, "hope": 0.0},
)

APOTHECARY = Entity(
    id="apothecary",
    kind="character",
    type="woman",
    label="the apothecary",
    phrase="the supply keeper",
    meters={"calm": 0.0},
    memes={"calm": 1.0},
)


# ---------------------------------------------------------------------------
# Reasonableness / validity
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for suspect in SUSPECTS:
            if setting == "station" and suspect == "tyrant":
                combos.append((setting, suspect))
            if setting == "infirmary" and suspect in {"revolutionary", "tyrant", "apothecary"}:
                combos.append((setting, suspect))
            if setting == "workshop" and suspect in {"revolutionary", "apothecary"}:
                combos.append((setting, suspect))
    return combos


def explain_rejection(setting: str, suspect: str) -> str:
    return (
        f"(No story: the {suspect} mystery does not fit {SETTINGS[setting].place} "
        f"for this tiny whodunit.)"
    )


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _rule_found_clue(world: World) -> list[str]:
    out = []
    syringe = world.get("syringe")
    if syringe.location == "wash basin" and ("clue", "wash basin") not in world.fired:
        world.fired.add(("clue", "wash basin"))
        syringe.meters["found"] = 1.0
        world.get("pip").memes["curiosity"] += 1
        out.append("Pip spotted a wet shine in the wash basin.")
    if syringe.location == "tool shelf" and ("clue", "tool shelf") not in world.fired:
        world.fired.add(("clue", "tool shelf"))
        syringe.meters["found"] = 1.0
        out.append("Pip noticed a careful gap on the tool shelf.")
    if syringe.location == "supply closet" and ("clue", "supply closet") not in world.fired:
        world.fired.add(("clue", "supply closet"))
        syringe.meters["found"] = 1.0
        out.append("Pip found the missing syringe tucked behind the spare gauze.")
    return out


def _rule_suspicion(world: World) -> list[str]:
    out = []
    syringe = world.get("syringe")
    if syringe.meters.get("found", 0) >= 1 and world.facts.get("accused") and ("sus", "rise") not in world.fired:
        world.fired.add(("sus", "rise"))
        world.get(world.facts["accused"]).memes["suspicion"] = 1.0
        out.append(f"That made {world.facts['accused']} look guilty at first.")
    return out


RULES = [_rule_found_clue, _rule_suspicion]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    suspect = SUSPECTS[params.suspect]
    world = World(setting)
    world.add(Entity(**vars(HERO)))
    world.add(Entity(**vars(TYRANT)))
    world.add(Entity(**vars(REVOLUTIONARY)))
    world.add(Entity(**vars(APOTHECARY)))
    world.add(Entity(**vars(CLIUE)))

    syringe = world.get("syringe")
    if params.setting == "infirmary":
        syringe.location = "supply closet"
    elif params.setting == "workshop":
        syringe.location = "tool shelf"
    else:
        syringe.location = "baggage shelf"

    world.facts["accused"] = suspect.id
    world.facts["real_hide"] = "wash basin" if suspect.id == "revolutionary" else "supply closet"

    # Act 1: setup
    world.say(
        f"At {setting.place}, the small glass syringe went missing from its place."
    )
    world.say(
        f"Pip, a careful little detective, arrived to ask who had moved it."
    )
    world.para()

    # Act 2: investigation
    world.say(
        f"The first suspect was {suspect.label}, because {suspect.motive}."
    )
    world.say(
        f"{suspect.label.capitalize()} insisted {suspect.alibi}."
    )
    if suspect.id == "revolutionary":
        world.say(
            "He had been waving flyers and arguing in a brave, noisy way."
        )
    elif suspect.id == "tyrant":
        world.say(
            "He glared at everyone and tapped his chair like a drum."
        )
    else:
        world.say(
            "She counted bottles twice and kept the labels straight."
        )
    world.para()

    # Solve
    world.say("Pip looked for the clue that did not fit.")
    if suspect.id == "revolutionary":
        syringe.location = "wash basin"
        world.say("A thin ring of water led from the closet to the wash basin.")
    elif suspect.id == "tyrant":
        syringe.location = "supply closet"
        world.say("A hidden key ring under the chair matched the closet latch.")
    else:
        syringe.location = "supply closet"
        world.say("A tidy inventory sheet showed nothing had truly been stolen.")
    propagate(world, narrate=True)

    # Twist
    world.para()
    if suspect.id == "revolutionary":
        world.say(
            "Then came the twist: the revolutionary had not stolen the syringe at all."
        )
        world.say(
            "He had used it to rinse a poison spot from the basin so the tyrant would not see the stain first."
        )
        world.say(
            "The tyrant had hidden the syringe after that, because he did not want anyone to notice he needed the medicine."
        )
        world.get("tyrant").memes["shame"] += 1
        world.get("revolutionary").memes["hope"] += 1
        world.get("pip").memes["pride"] += 1
    elif suspect.id == "tyrant":
        world.say(
            "Then came the twist: the tyrant had hidden the syringe himself."
        )
        world.say(
            "He wanted to delay the shot and blame the revolutionary for the fuss."
        )
        world.get("tyrant").memes["shame"] += 1
        world.get("revolutionary").memes["hope"] += 1
        world.get("pip").memes["pride"] += 1
    else:
        world.say(
            "Then came the twist: the apothecary had simply moved the syringe to wash it."
        )
        world.say(
            "The real problem was the tyrant's loud accusing, not a theft at all."
        )
        world.get("tyrant").memes["shame"] += 1
        world.get("apothecary").memes["calm"] += 1
        world.get("pip").memes["pride"] += 1

    world.say(
        "Pip explained the clues one by one, and the room grew quiet."
    )
    world.say(
        f"In the end, {suspect.label} was not the true thief, and the syringe was back where it belonged."
    )

    world.facts.update(
        setting=setting,
        suspect=suspect,
        syringe=world.get("syringe"),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    suspect: Suspect = f["suspect"]
    setting: Setting = f["setting"]
    return [
        f'Write a short whodunit for a child set at {setting.place} about a missing syringe.',
        f"Tell a mystery story where {suspect.label} looks guilty, but the clue trail shows a twist.",
        "Write a gentle detective story with a clear clue, a surprise turn, and a tidy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    suspect: Suspect = f["suspect"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What went missing at the start of the story?",
            answer="A small glass syringe went missing, and that made everyone curious.",
        ),
        QAItem(
            question=f"Why did {suspect.label} seem suspicious at first?",
            answer=f"{suspect.label.capitalize()} seemed suspicious because {suspect.motive}.",
        ),
        QAItem(
            question="What clue helped Pip solve the mystery?",
            answer="A clue that did not fit helped Pip: a water trail, a hidden key ring, or a tidy inventory sheet, depending on the case.",
        ),
        QAItem(
            question="What was the twist at the end?",
            answer="The first person who looked guilty was not the true answer; the real hiding was done for a different reason, and the syringe returned to where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a syringe for?",
            answer="A syringe is a tool that can hold and deliver medicine or other liquid in a careful way.",
        ),
        QAItem(
            question="What is a revolutionary?",
            answer="A revolutionary is a person who wants big change and speaks or acts loudly about it.",
        ),
        QAItem(
            question="What is a tyrant?",
            answer="A tyrant is a bossy ruler or person who uses power in a mean, unfair way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} {e.type:12} meters={meters} memes={memes} loc={e.location}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(infirmary; workshop; station).
suspect(revolutionary; tyrant; apothecary).

valid(S, P) :- setting(S), suspect(P), allowed(S, P).
allowed(infirmary, revolutionary).
allowed(infirmary, tyrant).
allowed(infirmary, apothecary).
allowed(workshop, revolutionary).
allowed(workshop, apothecary).
allowed(station, tyrant).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in SUSPECTS:
        lines.append(asp.fact("suspect", pid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - ap))
    print("only in clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect = rng.choice(sorted(combos))
    return StoryParams(setting=setting, suspect=suspect)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.suspect and (args.setting, args.suspect) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.suspect))
    return valid_story_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
    ap = argparse.ArgumentParser(description="Whodunit storyworld: a missing syringe, a revolutionary, and a tyrant.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
    StoryParams(setting="infirmary", suspect="revolutionary"),
    StoryParams(setting="station", suspect="tyrant"),
    StoryParams(setting="workshop", suspect="apothecary"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, p in asp_valid_combos():
            print(s, p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
