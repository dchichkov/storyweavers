#!/usr/bin/env python3
"""
A mythic storyworld about a young hero, a sacred reservoir, a dangerous soak,
and the lesson that bravery is strongest when joined with teamwork.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("soak", 0.0) < THRESHOLD:
            continue
        sig = ("soak", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
        actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + 1
        out.append(f"The waters rose around {actor.id}, and {actor.pronoun()} did not turn away.")
    return out


CAUSAL_RULES = [_r_soak]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def setting_text(setting: Setting) -> str:
    return {
        "hallowed": f"The {setting.place} was hallowed, and the old stones listened.",
        "wild": f"The {setting.place} was wild, and the wind moved like a prophecy.",
        "silent": f"The {setting.place} was silent, and the water waited without a ripple.",
    }.get(setting.mood, f"The {setting.place} held its breath beneath the sky.")


def pray_over_reservoir(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"In that domain, {hero.id} guarded the reservoir, where the people drew water "
        f"and feared its deep secret."
    )
    world.say(
        f"{elder.label} warned that the reservoir could soak the valley if the stone seal failed."
    )


def test_bravery(world: World, hero: Entity, trial: Trial) -> None:
    hero.meters[trial.mess] = hero.meters.get(trial.mess, 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.zone = set(trial.zone)
    world.say(
        f"Then {hero.id} stepped toward {trial.verb}, though {hero.pronoun('possessive')} knees trembled."
    )
    propagate(world)


def reveal_turn(world: World, hero: Entity, ally: Entity, trial: Trial, relic: Entity) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    ally.memes["teamwork"] = ally.memes.get("teamwork", 0.0) + 1
    world.say(
        f"{ally.label} came beside {hero.id}, and together they carried ropes and lamps to the reservoir mouth."
    )
    world.say(
        f"By teamwork, they could {trial.rush} without losing the relic to the flood."
    )


def resolution(world: World, hero: Entity, ally: Entity, trial: Trial, relic: Entity, aid: Aid) -> None:
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0.0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    world.say(
        f"They tied on {aid.label} and chose the safer path."
    )
    world.say(
        f"In the end, {hero.id} was still {trial.gerund}, but the {relic.label} stayed dry, and the people sang of the lesson learned: "
        f"bravery can be bright, yet teamwork makes it wise."
    )


def tell(setting: Setting, trial: Trial, relic_cfg: Relic, hero_name: str, hero_type: str, ally_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    ally = world.add(Entity(id="Ally", kind="character", type=ally_type, label="the elder"))
    relic = world.add(Entity(id="relic", type="relic", label=relic_cfg.label, phrase=relic_cfg.phrase))
    aid = Aid(
        id="bridge-ropes",
        label="bridge ropes",
        covers={"feet", "legs"},
        guards={"soak"},
        prep="cross the flooded stones together",
        tail="crossed the flooded stones together",
    )

    hero.say = hero.id  # harmless convenience for internal phrasing, never narrated directly
    world.say(f"{hero.id} was a brave child of the {setting.place}, and the old songs named {hero.id} a keeper.")
    world.say(setting_text(setting))
    pray_over_reservoir(world, hero, ally)
    world.para()
    world.say(f"{hero.id} loved {trial.gerund}, and the rumor of the reservoir made the heart race.")
    world.say(f"One day, {hero.id} wanted to {trial.verb}, but a storm began to {trial.rush}.")
    world.say(f"The waters threatened to {trial.soil}, and the sacred {relic.label} could be lost.")
    world.para()
    test_bravery(world, hero, trial)
    world.say(f"Still, {hero.id} held fast and did not flee from the {trial.keyword}.")
    reveal_turn(world, hero, ally, trial, relic)
    world.para()
    resolution(world, hero, ally, trial, relic, aid)

    world.facts.update(
        hero=hero,
        ally=ally,
        relic=relic,
        aid=aid,
        trial=trial,
        setting=setting,
    )
    return world


SETTINGS = {
    "temple": Setting(place="the temple reservoir", mood="hallowed", affords={"soak"}),
    "cliffs": Setting(place="the cliff reservoir", mood="wild", affords={"soak"}),
    "garden": Setting(place="the hidden reservoir garden", mood="silent", affords={"soak"}),
}

TRIALS = {
    "soak": Trial(
        id="soak",
        verb="approach the reservoir",
        gerund="watching the waters",
        rush="soak the lower path",
        mess="soak",
        soil="flood the valley",
        zone={"feet", "legs"},
        keyword="soak",
        tags={"soak", "reservoir", "domain"},
    ),
}

RELICS = {
    "lamp": Relic(id="lamp", label="river-lamp", phrase="a river-lamp of silver", region="hands", genders={"girl", "boy"}),
    "crown": Relic(id="crown", label="sun-crown", phrase="a sun-crown of gold", region="head", genders={"girl", "boy"}),
}

GIRL_NAMES = ["Asha", "Mira", "Nira", "Kali", "Sera"]
BOY_NAMES = ["Arun", "Taro", "Kiran", "Ravi", "Milo"]

TRAITS = ["brave", "gentle", "steady", "curious"]


@dataclass
class StoryParams:
    setting: str
    trial: str
    relic: str
    name: str
    gender: str
    ally_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic reservoir storyworld about soak, bravery, teamwork, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--ally-type", choices=["elder", "guide"])
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
    trial = args.trial or "soak"
    relic = args.relic or rng.choice(list(RELICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.relic and args.gender not in RELICS[args.relic].genders:
        raise StoryError("That relic does not suit that child in this mythic telling.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ally_type = args.ally_type or "elder"
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, trial=trial, relic=relic, name=name, gender=gender, ally_type=ally_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about the {f["setting"].place} and the word "soak".',
        f"Tell a story where {f['hero'].id} shows bravery near a reservoir and learns teamwork.",
        f"Write a gentle legend with a lesson learned after a storm threatens a sacred reservoir.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    relic = f["relic"]
    trial = f["trial"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a brave child who guarded the reservoir with {ally.label}.",
        ),
        QAItem(
            question=f"What danger did the reservoir bring?",
            answer=f"The reservoir could soak the lower path and flood the valley if the storm grew strong.",
        ),
        QAItem(
            question=f"What did the hero learn?",
            answer="The hero learned that bravery is good, but teamwork makes a hard task wise and safe.",
        ),
        QAItem(
            question=f"What stayed safe in the end?",
            answer=f"The {relic.label} stayed dry while the hero kept watching the waters.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reservoir?",
            answer="A reservoir is a place where water is held so people can use it later.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and work together toward the same goal.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does the right thing even though they feel afraid.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(temple;cliffs;garden).
trial(soak).
relic(lamp;crown).
valid(S,T,R) :- setting(S), trial(T), relic(R), T = soak.
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TRIALS:
        lines.append(asp.fact("trial", t))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(s, t, r) for s in SETTINGS for t in TRIALS for r in RELICS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TRIALS[params.trial],
        RELICS[params.relic],
        params.name,
        params.gender,
        params.ally_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="temple", trial="soak", relic="lamp", name="Asha", gender="girl", ally_type="elder", trait="brave"),
            StoryParams(setting="cliffs", trial="soak", relic="crown", name="Arun", gender="boy", ally_type="guide", trait="steady"),
            StoryParams(setting="garden", trial="soak", relic="lamp", name="Mira", gender="girl", ally_type="elder", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
