#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a misunderstanding that is healed by teamwork.

Seed premise:
A little helper named Myy is told to scold a leek for sneaking into the royal soup.
But the leek is not naughty at all: it was trying to help the cook carry a lantern.
The misunderstanding makes a mess of feelings, until Myy and the others work together
and discover the truth.

This world models:
- a tiny castle-kitchen fairy tale
- a misunderstanding between characters
- teamwork as the resolving turn
- physical meters and emotional memes
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "maid", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "boyish", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the castle kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "castle_kitchen"
    hero_name: str = "Myy"
    helper_name: str = "Bram"
    messenger_name: str = "Queen Elspeth"


SETTINGS = {
    "castle_kitchen": Setting(place="the castle kitchen", affords={"lantern", "soup", "leek"}),
    "garden_gate": Setting(place="the garden gate", affords={"lantern", "leek"}),
}


@dataclass
class Scenario:
    id: str
    truth: str
    misunderstanding: str
    teamwork: str


SCENARIOS = {
    "leek_lantern": Scenario(
        id="leek_lantern",
        truth="The leek was carrying a lantern to help find the soup spoon.",
        misunderstanding="Myy thinks the leek is sneaking into the soup pot.",
        teamwork="Myy, the leek, and the helper lift the lantern together and check the pot.",
    )
}


@dataclass
class StoryModel:
    world: World
    myy: Entity
    leek: Entity
    helper: Entity
    messenger: Entity
    lantern: Entity
    soup: Entity
    scenario: Scenario


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_mem(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _tell_setup(model: StoryModel) -> None:
    w = model.world
    myy = model.myy
    leek = model.leek
    helper = model.helper
    messenger = model.messenger
    lantern = model.lantern
    soup = model.soup

    w.say(f"Once in {w.setting.place}, there lived a small helper named {myy.id}.")
    w.say(
        f"{myy.id} was {myy.traits[0]} and kind, and {myy.pronoun().capitalize()} loved the hush of fairy-tale evenings."
    )
    w.say(
        f"Near the fire, {helper.id} watched the soup, while {lantern.id} glowed like a tiny moon."
    )
    w.say(
        f"There was also a little {leek.type} named {leek.id}, fresh from the garden and bright as a green ribbon."
    )
    w.say(
        f"{messenger.id} had asked for the royal soup, and {soup.label} had to be ready before the bells rang."
    )
    _add_mem(myy, "care", 1)
    _add_mem(leek, "hope", 1)
    _add_mem(helper, "duty", 1)
    _add_mem(messenger, "expectation", 1)


def _predict_misunderstanding(model: StoryModel) -> bool:
    sim = model.world.copy()
    sim.get(model.leek.id).meters["near_pot"] = 1
    sim.get(model.myy.id).memes["suspicion"] = 1
    return True


def _tell_conflict(model: StoryModel) -> None:
    w = model.world
    myy = model.myy
    leek = model.leek
    helper = model.helper
    lantern = model.lantern

    w.para()
    w.say(
        f"One dusk, {myy.id} saw {leek.id} beside the pot and hurried to judge the scene."
    )
    _add_mem(myy, "suspicion", 1)
    _add_mem(myy, "alarm", 1)
    _add_mem(leek, "hurt", 1)
    _add_mem(helper, "worry", 1)

    if _predict_misunderstanding(model):
        w.say(
            f'"Stop at once!" {myy.id} cried. "{leek.id}, do not bother the soup!"'
        )
        _add_mem(myy, "scold", 1)
        _add_mem(leek, "misunderstood", 1)
        _add_mem(leek, "sadness", 1)
        _add_meter(leek, "distance", 1)

    w.say(
        f"But {helper.id} lifted {lantern.id} higher and whispered that the little {leek.type} had not come to spoil anything."
    )
    w.say(
        f"{helper.id} said {leek.id} had only been trying to help find the spoon in the dim kitchen."
    )
    _add_mem(helper, "truth", 1)
    _add_mem(myy, "confusion", 1)


def _tell_resolution(model: StoryModel) -> None:
    w = model.world
    myy = model.myy
    leek = model.leek
    helper = model.helper
    lantern = model.lantern
    soup = model.soup

    w.para()
    w.say(
        f"{myy.id} looked again and saw the truth in the lantern light."
    )
    _add_mem(myy, "understanding", 1)
    _add_mem(myy, "shame", 1)
    _add_mem(leek, "relief", 1)

    w.say(
        f"{myy.id} lowered {myy.pronoun('possessive')} voice and apologized to {leek.id}."
    )
    _add_mem(myy, "kindness", 1)
    _add_mem(leek, "trust", 1)

    w.say(
        f"Then the three of them worked together: {helper.id} stirred the soup, {myy.id} held {lantern.id}, and {leek.id} pointed out the lost spoon."
    )
    _add_mem(myy, "teamwork", 1)
    _add_mem(helper, "teamwork", 1)
    _add_mem(leek, "teamwork", 1)
    _add_meter(soup, "ready", 1)
    _add_meter(lantern, "glow", 1)

    w.say(
        f"In the end, the spoon was found, the soup was served, and {leek.id} was welcomed as a helper instead of a troublemaker."
    )
    _set_meter(leek, "welcome", 1)
    _set_meter(myy, "peace", 1)
    _set_meter(helper, "peace", 1)


def build_world(params: StoryParams) -> StoryModel:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    world = World(SETTINGS[params.place])

    myy = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="helper",
        label="little helper",
        traits=["careful", "bright"],
    ))
    leek = world.add(Entity(
        id="Leek",
        kind="character",
        type="leek",
        label="leek",
        traits=["small", "green"],
    ))
    helper = world.add(Entity(
        id="Bram",
        kind="character",
        type="cook",
        label="the cook",
        traits=["busy", "gentle"],
    ))
    messenger = world.add(Entity(
        id=params.messenger_name,
        kind="character",
        type="queen",
        label="the queen",
        traits=["royal", "patient"],
    ))
    lantern = world.add(Entity(id="Lantern", kind="thing", type="lantern", label="lantern"))
    soup = world.add(Entity(id="Soup", kind="thing", type="soup", label="soup"))

    scenario = SCENARIOS["leek_lantern"]
    model = StoryModel(world=world, myy=myy, leek=leek, helper=helper, messenger=messenger, lantern=lantern, soup=soup, scenario=scenario)
    world.facts.update(myy=myy, leek=leek, helper=helper, messenger=messenger, lantern=lantern, soup=soup, scenario=scenario)
    return model


def tell(params: StoryParams) -> StoryModel:
    model = build_world(params)
    _tell_setup(model)
    _tell_conflict(model)
    _tell_resolution(model)
    return model


def generation_prompts(model: StoryModel) -> list[str]:
    return [
        'Write a short fairy tale about a misunderstanding that is fixed by teamwork, and include the word "myy".',
        f"Tell a gentle castle-kitchen story where {model.myy.id} scolds a leek by mistake, then learns the truth and works together with everyone.",
        'Write a child-friendly story about a leek, a lantern, and a misunderstanding that ends in teamwork.',
    ]


def story_qa(model: StoryModel) -> list[QAItem]:
    w = model.world
    myy = model.myy
    leek = model.leek
    helper = model.helper
    messenger = model.messenger
    lantern = model.lantern

    return [
        QAItem(
            question=f"Who first thought {leek.id} was causing trouble?",
            answer=f"{myy.id} first thought {leek.id} was causing trouble because {myy.id} saw {leek.id} near the pot in the dim kitchen.",
        ),
        QAItem(
            question=f"Why did the misunderstanding happen in {w.setting.place}?",
            answer=f"It happened because the kitchen was dim, and {lantern.id} did not make the whole scene clear at first.",
        ),
        QAItem(
            question=f"Who helped reveal the truth about {leek.id}?",
            answer=f"{helper.id} helped reveal the truth by lifting {lantern.id} and explaining that {leek.id} was only trying to help.",
        ),
        QAItem(
            question=f"What did {myy.id} do after realizing the mistake?",
            answer=f"{myy.id} apologized to {leek.id} and then joined the others in teamwork.",
        ),
        QAItem(
            question=f"How did the story end for {leek.id}?",
            answer=f"{leek.id} was welcomed as a helper, and the spoon was found before the soup was served to {messenger.id}.",
        ),
    ]


KNOWLEDGE = {
    "leek": [
        QAItem(
            question="What is a leek?",
            answer="A leek is a long green vegetable that looks a little like a giant spring onion.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so people can see in the dark.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to do something well.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing before they know the full truth.",
        )
    ],
    "scold": [
        QAItem(
            question="What does it mean to scold someone?",
            answer="To scold someone means to speak sharply because you think they have done something wrong.",
        )
    ],
    "myy": [
        QAItem(
            question="Who or what is Myy in this story?",
            answer="Myy is the little helper character in the castle kitchen who learns to listen before judging.",
        )
    ],
}


def world_knowledge_qa(model: StoryModel) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["myy"])
    out.extend(KNOWLEDGE["misunderstanding"])
    out.extend(KNOWLEDGE["teamwork"])
    out.extend(KNOWLEDGE["scold"])
    out.extend(KNOWLEDGE["leek"])
    out.extend(KNOWLEDGE["lantern"])
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


def dump_trace(model: StoryModel) -> str:
    lines = ["--- world model state ---"]
    for e in model.world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A misunderstanding happens if Myy scolds the leek before the helper reveals the truth.
misunderstanding(Myy, Leek) :- scolds(Myy, Leek), not truth_revealed(Leek).

% Teamwork is present when the helper, Myy, and the leek all contribute.
teamwork(Myy, Leek, Helper) :- helps(Myy), helps(Leek), helps(Helper).

% The fairy tale is valid if it has both misunderstanding and teamwork.
valid_story(P) :- misunderstanding(myy, leek), teamwork(myy, leek, helper).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "myy"),
        asp.fact("character", "leek"),
        asp.fact("character", "helper"),
        asp.fact("scolds", "myy", "leek"),
        asp.fact("helps", "myy"),
        asp.fact("helps", "leek"),
        asp.fact("helps", "helper"),
        asp.fact("truth_revealed", "leek"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP validation succeeded.")
        return 0
    print("MISMATCH: ASP validation failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about Myy, a leek, misunderstanding, and teamwork.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    return StoryParams(
        seed=args.seed,
        place=place,
        hero_name="Myy",
        helper_name="Bram",
        messenger_name="Queen Elspeth",
    )


def generate(params: StoryParams) -> StorySample:
    model = tell(params)
    return StorySample(
        params=params,
        story=model.world.render(),
        prompts=generation_prompts(model),
        story_qa=story_qa(model),
        world_qa=world_knowledge_qa(model),
        world=model,
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
    StoryParams(place="castle_kitchen", hero_name="Myy", helper_name="Bram", messenger_name="Queen Elspeth"),
    StoryParams(place="garden_gate", hero_name="Myy", helper_name="Bram", messenger_name="Queen Elspeth"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
