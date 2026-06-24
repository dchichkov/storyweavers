#!/usr/bin/env python3
"""
A small mystery storyworld set in an apartment courtyard.

Premise:
- A child has a fortieth mission: deliver a tiny note to a neighbor in the
  apartment courtyard.
- A misunderstanding makes the child think the note was lost.
- Dialogue reveals the truth and the mystery resolves with a clear ending image.

This world models:
- physical meters: distance, hiddenness, dampness, noise
- emotional memes: worry, curiosity, relief, trust

It supports the standard storyworld CLI and an inline ASP twin for parity
checks.
"""

from __future__ import annotations

import argparse
import copy
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
    keeper: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the apartment courtyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    name: str
    clue: str
    target: str
    route: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    hidden_hint: str
    location: str
    easy_to_misread: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    dialogue_offer: str
    dialogue_reveal: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "courtyard": Setting(place="the apartment courtyard", affords={"mission", "dialogue", "search"}),
}

MISSIONS = {
    "fortieth": Mission(
        id="fortieth",
        name="fortieth mission",
        clue="the blue planter by the mailbox",
        target="the neighbor on the third floor",
        route="through the courtyard path",
        reveal="the note was tucked safely under the bench the whole time",
        tags={"mission", "mystery", "fortieth"},
    ),
}

TOKENS = {
    "note": Token(
        id="note",
        label="note",
        phrase="a folded note with a small red star",
        hidden_hint="it was easy to miss under a shadow",
        location="under the bench",
        easy_to_misread="trash",
        tags={"paper", "clue", "mystery"},
    ),
    "key": Token(
        id="key",
        label="key",
        phrase="a tiny brass key",
        hidden_hint="it gleamed like a crumb of sunlight",
        location="beside the flower pot",
        easy_to_misread="a coin",
        tags={"metal", "clue", "mystery"},
    ),
}

HELPERS = {
    "janitor": Helper(
        id="janitor",
        label="Mrs. Vale",
        kind="neighbor",
        dialogue_offer="I saw something by the bench earlier.",
        dialogue_reveal="I moved the note so it would not blow away.",
        tags={"dialogue", "helper", "mystery"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "June", "Tessa", "Nora", "Lina"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah", "Milo", "Jasper"]
TRAITS = ["careful", "curious", "quiet", "brave", "patient", "alert"]


@dataclass
class StoryParams:
    place: str
    mission: str
    token: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def mission_at_risk(mission: Mission, token: Token) -> bool:
    return mission.id == "fortieth" and token.id == "note"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mission_id in MISSIONS:
            for token_id in TOKENS:
                for helper_id in HELPERS:
                    if mission_at_risk(MISSIONS[mission_id], TOKENS[token_id]):
                        combos.append((place, mission_id, token_id, helper_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld in an apartment courtyard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.token is None or c[2] == args.token)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission_id, token_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission_id, token=token_id, helper=helper_id,
                       name=name, gender=gender, trait=trait)


def _dialogue(world: World, speaker: Entity, text: str) -> None:
    world.say(f'"{text}" {speaker.id} said.')


def tell(setting: Setting, mission: Mission, token: Token, helper: Helper,
         hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"curiosity": 1.0}))
    neighbor = world.add(Entity(id=helper.id, kind="character", type="woman", label=helper.label))
    clue = world.add(Entity(id=token.id, type="thing", label=token.label, phrase=token.phrase,
                            location=token.location))
    world.facts.update(hero=hero, helper=neighbor, token=clue, mission=mission, trait=trait)

    hero.memes["worry"] = 1.0
    hero.memes["curiosity"] = 2.0
    clue.meters["hidden"] = 1.0

    world.say(f"{hero.id} was a {trait} {hero_type} who loved small mysteries.")
    world.say(f"On the {mission.name}, {hero.id} carried {token.phrase} for {mission.target}.")
    world.say(f"{hero.id} followed {mission.route} in {setting.place}, looking for {mission.clue}.")

    world.para()
    world.say(f"Then {hero.id} noticed an empty spot by {token.location} and frowned.")
    hero.memes["misunderstanding"] = 1.0
    hero.memes["worry"] += 1.0
    _dialogue(world, hero, f"I think the note is gone! Maybe someone took it.")
    _dialogue(world, neighbor, helper.dialogue_offer)
    world.say(f"{neighbor.id} pointed near {token.location}, where the shadows made a tiny shape look like {token.easy_to_misread}.")
    world.say(f"{hero.id} leaned closer and realized the shape was not trash at all; it was {token.hidden_hint}.")

    world.para()
    _dialogue(world, neighbor, helper.dialogue_reveal)
    _dialogue(world, hero, f"So the note was here all along?")
    world.say(f"{neighbor.id} nodded, and the little mystery opened like a flower.")
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 2.0
    hero.memes["trust"] = 1.0
    world.say(f"{hero.id} smiled, took the note, and walked back {mission.route} with a lighter step.")
    world.say(f"At the end, {mission.reveal}, and the courtyard felt quiet and safe again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mission, token = f["hero"], f["mission"], f["token"]
    return [
        f'Write a gentle mystery story for a small child set in {world.setting.place}.',
        f"Tell a story where {hero.id} is on the {mission.name} and a misunderstanding about {token.label} gets solved in dialogue.",
        f'Write a short apartment-courtyard mystery that ends with the clue "{token.phrase}" being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mission, token, helper = f["hero"], f["mission"], f["token"], f["helper"]
    return [
        QAItem(
            question=f"What mission was {hero.id} working on in the courtyard?",
            answer=f"{hero.id} was on the {mission.name}, trying to deliver the clue to {mission.target}.",
        ),
        QAItem(
            question=f"What did {hero.id} first misunderstand about {token.label}?",
            answer=f"{hero.id} thought {token.label} was gone, but it was really still there near {token.location}.",
        ),
        QAItem(
            question=f"Who helped clear up the misunderstanding?",
            answer=f"{helper.id} helped by speaking calmly and explaining what happened to the {token.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a courtyard?",
            answer="A courtyard is an open space in the middle of a building or between buildings, often shared by neighbors.",
        ),
        QAItem(
            question="What is a mystery in a story?",
            answer="A mystery is a story where someone notices something puzzling and tries to figure out what is really happening.",
        ),
        QAItem(
            question="Why can people misunderstand each other?",
            answer="People can misunderstand each other when they do not have all the facts and make the wrong guess too quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mission_valid(M) :- mission(M).
token_valid(T) :- token(T).
helper_valid(H) :- helper(H).
story_valid(P,M,T,H) :- place(P), mission_valid(M), token_valid(T), helper_valid(H).
"""


def asp_facts() -> str:
    import asp
    out = []
    for pid in SETTINGS:
        out.append(asp.fact("place", pid))
    for mid in MISSIONS:
        out.append(asp.fact("mission", mid))
    for tid in TOKENS:
        out.append(asp.fact("token", tid))
    for hid in HELPERS:
        out.append(asp.fact("helper", hid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/4."))
    return sorted(set(asp.atoms(model, "story_valid")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], TOKENS[params.token],
                 HELPERS[params.helper], params.name, params.gender, params.trait)
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


CURATED = [
    StoryParams(place="courtyard", mission="fortieth", token="note", helper="janitor",
                name="Mina", gender="girl", trait="curious"),
    StoryParams(place="courtyard", mission="fortieth", token="key", helper="janitor",
                name="Owen", gender="boy", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
