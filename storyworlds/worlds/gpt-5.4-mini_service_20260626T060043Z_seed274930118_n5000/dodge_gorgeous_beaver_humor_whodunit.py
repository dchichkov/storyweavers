#!/usr/bin/env python3
"""
storyworlds/worlds/dodge_gorgeous_beaver_humor_whodunit.py
===========================================================

A small whodunit storyworld with a humorous, child-friendly mystery:
someone lost a shiny thing, clues pile up, and the hero has to dodge
false leads before finding the real answer.

The seed words for this world are woven into the premise:
"dodge", "gorgeous", and "beaver".

Story shape:
- setup: a curious child detective notices a missing item at the pond lodge
- middle: clues point toward the beaver, which is funny but not quite right
- turn: the detective dodges a false conclusion and follows a better clue
- ending: the real culprit is revealed, and the world state proves what changed

The domain is intentionally small:
- one setting
- a few suspects
- one missing object
- one true cause
- one reveal

It also carries the shared storyworld contract:
- typed entities with physical meters and emotional memes
- reasonableness gate + inline ASP twin
- QA generation
- trace output
- verify mode

The humor comes from exaggerated clues, a dignified beaver, and the
detective's careful but funny deductions.
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
    carried_by: Optional[str] = None
    hidden_by: Optional[str] = None
    revealed: bool = False
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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the pond lodge"
    indoors: bool = True
    smell: str = "pine and wet mud"


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    clue: str
    alibi: str
    suspiciousness: float = 0.0
    guilty: bool = False


@dataclass
class Mystery:
    missing: str
    missing_phrase: str
    real_culprit: str
    false_lead: str
    reveal_method: str
    keyword: str = "beaver"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.suspects: dict[str, Suspect] = {}
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.suspects = _copy.deepcopy(self.suspects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = _copy.deepcopy(self.facts)
        return clone


def _clue_suspicion(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    for sid, suspect in world.suspects.items():
        if suspect.guilty:
            continue
        if world.fired.__contains__(("clue", sid)):
            continue
        if sid == "beaver":
            continue
        if suspect.suspiciousness >= THRESHOLD:
            world.fired.add(("clue", sid))
            detective.memes["interest"] = detective.memes.get("interest", 0) + 1
            out.append(f"{suspect.label} looked suspicious, but the clue was not finished yet.")
    return out


def _reveal(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    mystery: Mystery = world.facts["mystery"]
    culprit = world.get(mystery.real_culprit)
    item = world.get(mystery.missing)
    if culprit.revealed:
        return out
    if detective.memes.get("deduction", 0) < THRESHOLD:
        return out
    culprit.revealed = True
    culprit.memes["embarrassment"] = culprit.memes.get("embarrassment", 0) + 1
    out.append(f"The truth popped out at last.")
    out.append(
        f"The {culprit.label_word} had hidden the {item.label} by accident while gnawing on a loose ribbon."
    )
    return out


CAUSAL_RULES = [
    _clue_suspicion,
    _reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inspect_clue(world: World, detective: Entity, suspect: Suspect, clue: str) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    suspect.suspiciousness += 0.5
    world.say(f"{detective.id} checked {suspect.label} and found {clue}.")


def dodge_false_lead(world: World, detective: Entity, suspect: Suspect) -> None:
    detective.memes["caution"] = detective.memes.get("caution", 0) + 1
    world.say(
        f"{detective.id} dodged a quick conclusion about {suspect.label} and looked for a better clue."
    )


def solve_case(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["deduction"] = detective.memes.get("deduction", 0) + 1
    world.say(
        f"{detective.id} noticed the tiny marks, the bent ribbon, and the muddy trail."
    )
    propagate(world, narrate=True)


def setup_world(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, sidekick_name: str) -> World:
    world = World(setting)

    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=["curious", "careful", "funny"],
        meters={"step": 0.0},
        memes={"curiosity": 1.0, "caution": 0.0, "deduction": 0.0, "delight": 0.0},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type="mouse",
        label=sidekick_name,
        traits=["tiny", "helpful"],
        memes={"nervousness": 0.0, "delight": 0.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="trophy",
        label="golden spoon",
        phrase="a tiny golden spoon with a ribbon",
        owner=detective.id,
        carried_by=None,
        revealed=False,
        meters={"shine": 1.0},
        memes={"importance": 1.0},
    ))
    beaver = world.add(Entity(
        id="beaver",
        kind="character",
        type="beaver",
        label="the gorgeous beaver",
        traits=["gorgeous", "busy", "sticky-whiskered"],
        meters={"gnaw": 0.0},
        memes={"calm": 1.0, "embarrassment": 0.0},
    ))
    world.add(Entity(
        id="racoon",
        kind="character",
        type="raccoon",
        label="the raccoon janitor",
        traits=["sly", "tidy"],
        memes={"alibi": 1.0},
    ))
    world.suspects = {
        "beaver": Suspect(
            id="beaver",
            label="the gorgeous beaver",
            type="beaver",
            clue="wet twigs on the floor",
            alibi="he had been building a dam near the reeds",
            suspiciousness=0.7,
            guilty=True,
        ),
        "racoon": Suspect(
            id="racoon",
            label="the raccoon janitor",
            type="raccoon",
            clue="a mop standing by the door",
            alibi="she had been sweeping the porch the whole time",
            suspiciousness=0.3,
            guilty=False,
        ),
    }
    world.facts = {
        "mystery": mystery,
        "detective": detective,
        "sidekick": sidekick,
        "missing": missing,
        "beaver": beaver,
    }
    return world


def tell_story(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    detective = world.facts["detective"]
    sidekick = world.facts["sidekick"]
    missing = world.facts["missing"]
    beaver = world.facts["beaver"]

    world.say(
        f"At {world.setting.place}, the air smelled like {world.setting.smell}, and "
        f"{detective.label} the detective was trying to enjoy a quiet afternoon."
    )
    world.say(
        f"Then the {missing.label} went missing from the reading table, right when everyone was looking away."
    )
    world.say(
        f"{sidekick.label} squeaked, 'That is a very fancy mystery.' "
        f"{detective.label} nodded and peered at the crumbs, the mud, and the ribbon."
    )

    world.para()
    world.say(
        f"The first clue pointed at {beaver.label}. He was as {mystery.keyword} as a parade flag and left behind chew marks."
    )
    world.say(
        f"Still, {detective.label} knew a clue can be noisy without being true."
    )
    inspect_clue(world, detective, world.suspects["beaver"], world.suspects["beaver"].clue)
    dodge_false_lead(world, detective, world.suspects["beaver"])

    world.para()
    world.say(
        f"{detective.label} followed the ribbon instead of the gossip."
    )
    world.say(
        f"It led behind a stack of wet logs, where the breeze had tucked the {missing.label} under a leaf."
    )
    solve_case(world, detective, mystery)

    world.para()
    world.say(
        f"The {mystery.real_culprit} had not stolen anything on purpose; he had only nudged the ribbon while hauling sticks."
    )
    world.say(
        f"{beaver.label} blinked his shiny eyes, looked very gorgeous, and tried to pretend this was all part of the plan."
    )
    detective.memes["delight"] = detective.memes.get("delight", 0) + 1
    world.say(
        f"{detective.label} laughed, handed back the {missing.label}, and said the case was closed."
    )

    missing.revealed = True
    missing.carried_by = detective.id
    world.facts["solved"] = True


SETTINGS = {
    "pond_lodge": Setting(place="the pond lodge", indoors=True, smell="pine and wet mud"),
    "river_room": Setting(place="the river room", indoors=True, smell="warm tea and cedar"),
}

MYSTERIES = {
    "golden_spoon": Mystery(
        missing="missing",
        missing_phrase="a tiny golden spoon with a ribbon",
        real_culprit="beaver",
        false_lead="raccoon",
        reveal_method="follow the ribbon and the muddy trail",
        keyword="gorgeous",
    ),
}

HERO_NAMES = ["Maya", "Noah", "Lena", "Finn", "Zoe", "Eli"]
SIDEKICK_NAMES = ["Muffin", "Tippy", "Beans", "Pip"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    detective_type: str
    sidekick_name: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["detective"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a humorous whodunit for a young child set at {world.setting.place} about a missing {mystery.missing_phrase}.',
        f"Tell a short mystery where {hero.label} must dodge a false clue and solve the case with a beaver nearby.",
        f'Write a playful detective story that includes the word "beaver" and ends with the case being solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["detective"]
    sidekick = f["sidekick"]
    mystery: Mystery = f["mystery"]
    missing = f["missing"]
    beaver = f["beaver"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.label}, a curious detective who tried to solve a funny mystery.",
        ),
        QAItem(
            question=f"What went missing at {world.setting.place}?",
            answer=f"The missing item was {missing.label}, described as {mystery.missing_phrase}.",
        ),
        QAItem(
            question=f"Who looked like the first suspect?",
            answer=f"The first suspect was {beaver.label}, because the clues pointed toward him at first.",
        ),
        QAItem(
            question=f"How did {hero.label} avoid the wrong answer?",
            answer=(
                f"{hero.label} dodged the false lead, followed the ribbon instead of the gossip, "
                f"and found the real clue behind the wet logs."
            ),
        ),
        QAItem(
            question=f"Why was the beaver funny in the story?",
            answer=(
                f"The beaver was funny because he looked very serious and very gorgeous, "
                f"but he had only nudged the ribbon by accident."
            ),
        ),
        QAItem(
            question=f"What did {sidekick.label} do?",
            answer=f"{sidekick.label} squeaked about the mystery and stayed beside {hero.label} while the clues were checked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a beaver usually do?",
            answer=(
                "A beaver often builds dams, chews sticks, and works near water with strong teeth."
            ),
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer=(
                "Detectives look at clues to figure out what really happened instead of guessing too fast."
            ),
        ),
        QAItem(
            question="What is a false lead in a mystery?",
            answer=(
                "A false lead is a clue that seems important at first but does not actually solve the case."
            ),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.revealed:
            bits.append("revealed=True")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pond_lodge",
        mystery="golden_spoon",
        detective_name="Maya",
        detective_type="girl",
        sidekick_name="Pip",
    ),
    StoryParams(
        setting="river_room",
        mystery="golden_spoon",
        detective_name="Finn",
        detective_type="boy",
        sidekick_name="Beans",
    ),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("real_culprit", mid, m.real_culprit))
        lines.append(asp.fact("false_lead", mid, m.false_lead))
    lines.append(asp.fact("keyword", "beaver"))
    return "\n".join(lines)


ASP_RULES = r"""
% A case exists when there is a mystery and a real culprit.
case(M) :- mystery(M), real_culprit(M, C), culprit(C).

% A false lead is not the true culprit.
not_culprit(M, X) :- mystery(M), false_lead(M, X).

% A humorous whodunit should have at least one false lead and one culprit.
good_story(M) :- case(M), not_culprit(M, X), false_lead(M, X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show case/1. #show good_story/1."))
    return sorted(set(asp.atoms(model, "case")))


def asp_verify() -> int:
    expected = {("golden_spoon",)}
    got = set(asp_valid_cases())
    if got == expected:
        print(f"OK: clingo gate matches expected cases ({len(got)} case).")
        return 0
    print("MISMATCH between clingo and expected cases:")
    print("  got:", sorted(got))
    print("  expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny humorous whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=detective_name,
        detective_type=detective_type,
        sidekick_name=sidekick_name,
    )


def generate(params: StoryParams) -> StorySample:
    mystery = MYSTERIES[params.mystery]
    world = setup_world(
        SETTINGS[params.setting],
        mystery,
        params.detective_name,
        params.detective_type,
        params.sidekick_name,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show case/1. #show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show case/1. #show good_story/1."))
        print(f"{len(asp.atoms(model, 'case'))} case(s) found:")
        for atom in asp.atoms(model, "case"):
            print(" ", atom[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.detective_name}: whodunit at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
