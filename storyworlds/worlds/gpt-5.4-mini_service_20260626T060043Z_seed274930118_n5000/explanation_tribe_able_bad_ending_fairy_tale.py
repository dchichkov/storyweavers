#!/usr/bin/env python3
"""
A tiny fairy-tale story world about a tribe, an explanation, and someone being able
to do a brave or careful act. Some stories end in a Bad Ending when the wrong choice
is made or help arrives too late.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Tribe:
    name: str
    place: str
    custom: str
    danger: str
    aid: str
    meter_need: str
    meter_harm: str


@dataclass
class Ability:
    id: str
    title: str
    verb: str
    requirement: str
    cost: str
    help_kind: str
    danger_kind: str


@dataclass
class StoryParams:
    tribe: str
    ability: str
    setting: str
    name: str
    role: str
    seed: Optional[int] = None


@dataclass
class World:
    tribe: Tribe
    ability: Ability
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.tribe, self.ability, self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

TRIBES = {
    "river": Tribe(
        name="the River Tribe",
        place="the riverbank",
        custom="They told stories by the water at dusk.",
        danger="the river rose too high",
        aid="a wooden bridge",
        meter_need="thirst",
        meter_harm="flood",
    ),
    "hill": Tribe(
        name="the Hill Tribe",
        place="the hills",
        custom="They sang to keep the wind friendly.",
        danger="the fog hid the path",
        aid="a lantern path",
        meter_need="cold",
        meter_harm="lostness",
    ),
    "forest": Tribe(
        name="the Forest Tribe",
        place="the pine wood",
        custom="They left sweet bread for the birds.",
        danger="the trees whispered a warning too late",
        aid="a marked trail",
        meter_need="fear",
        meter_harm="darkness",
    ),
}

ABILITIES = {
    "explain": Ability(
        id="explain",
        title="an explanation",
        verb="explain the danger",
        requirement="a clear story",
        cost="patience",
        help_kind="understanding",
        danger_kind="confusion",
    ),
    "able": Ability(
        id="able",
        title="being able",
        verb="be able to cross safely",
        requirement="steady feet",
        cost="courage",
        help_kind="skill",
        danger_kind="hesitation",
    ),
    "guide": Ability(
        id="guide",
        title="a guiding light",
        verb="guide the way",
        requirement="a bright lantern",
        cost="oil",
        help_kind="direction",
        danger_kind="lostness",
    ),
}

SETTINGS = {
    "riverbank": "the riverbank",
    "hills": "the hills",
    "pine wood": "the pine wood",
}

NAMES = ["Mina", "Taro", "Lina", "Boro", "Sela", "Niko", "Ari", "Mara"]
ROLES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
tribe_name(river,riverbank).
tribe_name(hill,hills).
tribe_name(forest,wood).

ability(explain).
ability(able).
ability(guide).

bad_ending(T,A) :- tribe(T), ability(A), danger_late(T,A).
good_ending(T,A) :- tribe(T), ability(A), safe_help(T,A).

#show bad_ending/2.
#show good_ending/2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for tid, tribe in TRIBES.items():
        lines.append(asp.fact("tribe", tid))
        lines.append(asp.fact("place", tid, tribe.place))
    for aid in ABILITIES:
        lines.append(asp.fact("ability", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcomes() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/2.\n#show good_ending/2."))
    bad = set(asp.atoms(model, "bad_ending"))
    good = set(asp.atoms(model, "good_ending"))
    return bad | good


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    tribe = TRIBES[params.tribe]
    ability = ABILITIES[params.ability]
    world = World(tribe=tribe, ability=ability, setting=params.setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        meters={"need": 0.0, "fear": 0.0, "hope": 0.0, "safety": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "pride": 0.0, "sadness": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type="elder",
        label="the elder",
        meters={"time": 0.0},
        memes={"wisdom": 1.0},
    ))
    object_name = "bridge" if params.ability == "able" else "lantern"
    tool = world.add(Entity(
        id="Tool",
        kind="thing",
        type=object_name,
        label=object_name,
        owner=elder.id,
        meters={"light": 0.0, "stability": 0.0},
        memes={"trust": 0.0},
    ))

    world.facts.update(hero=hero, elder=elder, tool=tool, tribe=tribe, ability=ability)
    return world


def simulate(world: World) -> None:
    h: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    tool: Entity = world.facts["tool"]
    tribe: Tribe = world.tribe
    ability: Ability = world.ability

    world.say(f"In {tribe.place}, {h.id} lived with {tribe.name}.")
    world.say(tribe.custom)
    world.say(f"{h.id} loved the tale of {ability.title}, because {ability.requirement} sounded like a promise.")

    world.para()
    world.say(f"One evening, {tribe.danger}.")
    h.meters["need"] += 1
    h.memes["worry"] += 1
    world.say(f"{h.id} wanted to {ability.verb}, but {h.pronoun('possessive')} heart trembled with {tribe.meter_need}.")

    if world.setting == tribe.place:
        h.meters["hope"] += 1
        world.say(f"The elder lifted {tool.label} and began an explanation.")
        world.say(
            f'"Listen," {elder.label} said, "if you use {tool.label}, you may still {ability.verb}, '
            f'but only if you are calm enough to be careful."'
        )
        if ability.id == "explain":
            h.memes["hope"] += 2
            h.meters["safety"] += 1
            world.say(f"{h.id} understood the explanation and nodded slowly.")
        elif ability.id == "able":
            h.memes["hope"] += 1
            h.meters["safety"] += 1
            world.say(f"{h.id} took a deep breath and found that {h.pronoun()} was able after all.")
        else:
            h.memes["hope"] += 1
            h.meters["safety"] += 1
            world.say(f"The lantern lit the path, and the way looked less lonely.")
    else:
        h.memes["worry"] += 2
        h.meters["fear"] += 2
        world.say(f"But no helper came in time, and the warning grew thin in the dark.")
        world.say(f"{h.id} tried anyway, too soon and too fast.")

    world.para()
    if h.meters["safety"] >= 1:
        world.say(f"At last, {h.id} could {ability.verb} without panic.")
        world.say(f"The tribe cheered, and {tribe.aid} made the ending feel bright.")
        h.memes["pride"] += 1
        h.memes["sadness"] += 0
        world.facts["ending"] = "good"
    else:
        h.meters["safety"] -= 1
        h.memes["sadness"] += 2
        world.say(f"{h.id} could not fix the trouble in time.")
        world.say(f"The night kept its cold hand, and the story ended in a bad ending.")
        world.facts["ending"] = "bad"

    world.facts["tool"] = tool
    world.facts["tribe"] = tribe
    world.facts["ability"] = ability


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def choose_name(role: str, rng: random.Random) -> str:
    if role == "girl":
        return rng.choice(["Mina", "Lina", "Sela", "Mara"])
    return rng.choice(["Taro", "Boro", "Niko", "Ari"])


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h: Entity = f["hero"]
    t: Tribe = f["tribe"]
    a: Ability = f["ability"]
    return [
        f"Write a fairy tale about {h.id} from {t.name} learning about {a.title}.",
        f"Tell a short story where a tribe needs {a.title} and someone is able to help, or fails in a bad ending.",
        f"Write a child-friendly fairy tale that includes an explanation, a tribe, and a brave choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Entity = f["hero"]
    t: Tribe = f["tribe"]
    a: Ability = f["ability"]
    ending = f["ending"]
    qa = [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {h.id}, who lives with {t.name} and tries to learn about {a.title}.",
        ),
        QAItem(
            question=f"What was the trouble in the story?",
            answer=f"The trouble was that {t.danger} and {h.id} had to decide whether {h.pronoun()} could {a.verb}.",
        ),
        QAItem(
            question=f"Did the story end well?",
            answer=("Yes. The tribe found a safe way forward and the ending felt bright."
                    if ending == "good" else
                    "No. The help came too late, so the story ended in a bad ending."),
        ),
    ]
    if ending == "good":
        qa.append(QAItem(
            question=f"How did the explanation help {h.id}?",
            answer=f"The explanation helped {h.id} understand the danger and stay calm enough to be careful.",
        ))
    else:
        qa.append(QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {h.id} tried to act before help arrived, and the danger won that night.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    a: Ability = world.facts["ability"]
    t: Tribe = world.facts["tribe"]
    out = [
        QAItem(
            question="What is a tribe?",
            answer="A tribe is a group of people who live together, share customs, and help one another.",
        ),
        QAItem(
            question="What is an explanation?",
            answer="An explanation is a clear way of telling why something happens or how to do it.",
        ),
        QAItem(
            question="What does it mean to be able to do something?",
            answer="Being able to do something means you have the skill, strength, or courage to do it.",
        ),
    ]
    if a.id == "guide":
        out.append(QAItem(
            question="What is a lantern for?",
            answer="A lantern gives light so people can see the path in the dark.",
        ))
    if t.name == "the River Tribe":
        out.append(QAItem(
            question="Why can a river be dangerous?",
            answer="A river can be dangerous when it rises fast, because water can sweep over paths and make them hard to cross.",
        ))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  ending={world.facts.get('ending')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TRIBES:
        for a in ABILITIES:
            combos.append((t, a, SETTINGS[TRIBES[t].place]))
    return [(t, a, s) for t in TRIBES for a in ABILITIES for s in SETTINGS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    tribe = args.tribe or rng.choice(list(TRIBES))
    ability = args.ability or rng.choice(list(ABILITIES))
    setting = args.setting or TRIBES[tribe].place
    if setting != TRIBES[tribe].place:
        raise StoryError("This fairy tale works best when the setting matches the tribe's home place.")
    gender = args.gender or rng.choice(ROLES)
    name = args.name or choose_name(gender, rng)
    return StoryParams(tribe=tribe, ability=ability, setting=setting, name=name, role=gender)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
# ASP helpers
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    program = asp_program("#show bad_ending/2.\n#show good_ending/2.")
    model = asp.one_model(program)
    asp_pairs = set(asp.atoms(model, "bad_ending")) | set(asp.atoms(model, "good_ending"))
    py_pairs = asp_outcomes()
    if asp_pairs == py_pairs:
        print(f"OK: ASP and Python agree on {len(py_pairs)} outcomes.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_pairs - py_pairs))
    print("Python only:", sorted(py_pairs - asp_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale story world with a tribe, an explanation, and a bad ending mode.")
    ap.add_argument("--tribe", choices=TRIBES.keys())
    ap.add_argument("--ability", choices=ABILITIES.keys())
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=ROLES)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_facts() -> str:
    import asp
    lines = []
    for tid, tribe in TRIBES.items():
        lines.append(asp.fact("tribe", tid))
    for aid in ABILITIES:
        lines.append(asp.fact("ability", aid))
    return "\n".join(lines)


CURATED = [
    StoryParams(tribe="river", ability="explain", setting="the riverbank", name="Mina", role="girl"),
    StoryParams(tribe="hill", ability="able", setting="the hills", name="Taro", role="boy"),
    StoryParams(tribe="forest", ability="guide", setting="the pine wood", name="Sela", role="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/2.\n#show good_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/2.\n#show good_ending/2."))
        pairs = sorted(set(asp.atoms(model, "bad_ending")) | set(asp.atoms(model, "good_ending")))
        for p in pairs:
            print(p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
