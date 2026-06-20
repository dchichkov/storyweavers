#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/conscience_bad_ending_superhero_story.py
========================================================================

A standalone story world for a tiny superhero domain with conscience, temptation,
a warning beat, and a bad ending when the hero ignores that warning.

The world is deliberately small:
- one young hero
- one conscience-guided helper
- one tempting shortcut
- one city object that can be harmed
- one adult responder that may arrive too late

The simulated state drives the story:
- bravery, pride, worry, and conscience are meters/memes
- the city has danger and damage meters
- the helper can predict the danger before speaking
- the ending becomes bad when the shortcut is chosen and help arrives late

Run it:
    python storyworlds/worlds/gpt-5.4-mini/conscience_bad_ending_superhero_story.py
    python storyworlds/worlds/gpt-5.4-mini/conscience_bad_ending_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/conscience_bad_ending_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/conscience_bad_ending_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GOOD_CONSCIENCE = 6.0
BAD_CONSCIENCE = 2.5
HELP_POWER_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class SetPiece:
    id: str
    scene: str
    hero_goal: str
    dark_place: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Shortcut:
    id: str
    label: str
    phrase: str
    danger: str
    risk: int
    makes_damage: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    city = world.entities.get("city")
    if city is None:
        return out
    if city.meters["danger"] >= THRESHOLD and ("damage", "city") not in world.fired:
        world.fired.add(("damage", "city"))
        city.meters["damage"] += 1
        for e in world.characters():
            e.memes["fear"] += 1
        out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("damage", "physical", _r_damage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, shortcut: Shortcut) -> dict:
    sim = world.copy()
    _take_shortcut(sim, sim.get("hero"), sim.get("helper"), shortcut, narrate=False)
    return {
        "danger": sim.get("city").meters["danger"],
        "damage": sim.get("city").meters["damage"],
    }


def _take_shortcut(world: World, hero: Entity, helper: Entity, shortcut: Shortcut, narrate: bool = True) -> None:
    hero.meters["danger"] += shortcut.risk
    hero.memes["pride"] += 1
    city = world.get("city")
    city.meters["danger"] += shortcut.risk
    propagate(world, narrate=narrate)


def setup(world: World, setpiece: SetPiece, hero: Entity, helper: Entity, city: Entity) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a bright evening in {setpiece.scene}, {hero.id} raced across the rooftops with a cape that fluttered like a flag."
    )
    world.say(
        f"{helper.id} stayed close by and watched the streets below, because {setpiece.dark_place} could hide trouble fast."
    )


def show_goal(world: World, hero: Entity, setpiece: SetPiece) -> None:
    world.say(
        f'{hero.id} wanted to {setpiece.hero_goal}, and {hero.pronoun("possessive")} chest felt warm with courage.'
    )


def tempt(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'Then {hero.id} spotted {shortcut.phrase}. It looked quick and easy, even though it could {shortcut.danger}.'
    )
    world.say(f'"I know what I am doing," {hero.id} told {hero.pronoun("possessive")} conscience in a small whisper.')


def warn(world: World, helper: Entity, hero: Entity, shortcut: Shortcut, city: Entity) -> None:
    pred = predict(world, shortcut)
    helper.memes["worry"] += 1
    world.facts["predicted_damage"] = pred["damage"]
    world.say(
        f'{helper.id} touched {hero.id}\'s arm. "{hero.id}, your conscience says this is the wrong shortcut. '
        f'If you rush that way, the city can get hurt."'
    )


def refuse(world: World, hero: Entity) -> None:
    hero.memes["conscience"] += 1


def take_shortcut(world: World, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {hero.id} shook off the warning and took {shortcut.label} anyway.'
    )
    _take_shortcut(world, hero, helper, shortcut, narrate=True)


def rescue(world: World, response: Response, city: Entity, hero: Entity, helper: Entity) -> None:
    city.meters["danger"] = 0.0
    body = response.text
    world.say(
        f"At last a grown-up hero arrived and {body}."
    )
    world.say(
        f"But the rescue came after the trouble had already spread, and {hero.id} and {helper.id} could only stare at the smoke."
    )


def ending_bad(world: World, setpiece: SetPiece, hero: Entity, helper: Entity, city: Entity) -> None:
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"By dawn, {setpiece.ending_image}. {hero.id} stood on the silent roof and knew that bravery without conscience had hurt the whole block."
    )


def tell(setpiece: SetPiece, shortcut: Shortcut, response: Response) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="boy", role="hero", label="the hero"))
    helper = world.add(Entity(id="helper", kind="character", type="girl", role="helper", label="the helper"))
    city = world.add(Entity(id="city", kind="thing", type="city", label="the city"))
    world.facts["setpiece"] = setpiece
    world.facts["shortcut"] = shortcut
    world.facts["response"] = response

    hero.memes["conscience"] = GOOD_CONSCIENCE
    helper.memes["conscience"] = GOOD_CONSCIENCE
    setup(world, setpiece, hero, helper, city)
    world.para()
    show_goal(world, hero, setpiece)
    tempt(world, hero, shortcut)
    warn(world, helper, hero, shortcut, city)
    refuse(world, hero)
    world.para()
    take_shortcut(world, hero, helper, shortcut)
    world.para()
    rescue(world, response, city, hero, helper)
    ending_bad(world, setpiece, hero, helper, city)
    world.facts.update(hero=hero, helper=helper, city=city, outcome="bad")
    return world


SETTINGS = {
    "downtown": SetPiece("downtown", "downtown", "save the museum", "the alley behind the museum", "the museum windows were black and broken"),
    "harbor": SetPiece("harbor", "the harbor", "stop the runaway drone", "the dark crane yard", "the docks were quiet, with one bent sign in the wind"),
    "midtown": SetPiece("midtown", "midtown", "catch the falling train car", "the tunnel mouth", "the station roof was empty and cold"),
}

SHORTCUTS = {
    "shortcut": Shortcut("shortcut", "the shortcut route", "shortcut route", "miss a hidden cable and crash into it", 2, tags={"shortcut"}),
    "blast": Shortcut("blast", "the blast beam", "blast beam", "shatter the wrong window and start a panic", 3, tags={"blast"}),
    "dash": Shortcut("dash", "the fast dash", "fast dash", "knock over a stack of crates and block the street", 2, tags={"dash"}),
}

RESPONSES = {
    "tow": Response("tow", 3, 3, "used a rescue cable and pulled the broken vehicle away", "tried to help, but the damage was already too wide", "used a rescue cable and pulled the broken vehicle away", tags={"rescue"}),
    "shield": Response("shield", 3, 2, "spread out a heavy shield and kept the crowd back", "raised a shield, but it was too late to stop the damage", "spread out a heavy shield and kept the crowd back", tags={"shield"}),
    "beam": Response("beam", 1, 1, "flashed a bright beam and hoped for the best", "flashed a bright beam, but it could not undo the damage", "flashed a bright beam", tags={"beam"}),
}

NAMES = ["Aster", "Nova", "Jet", "Piper", "Sky", "Milo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    shortcut: str
    response: str
    name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in SHORTCUTS:
            for r in RESPONSES:
                combos.append((s, c, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero story world with conscience and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name", choices=NAMES)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.shortcut is None or c[1] == args.shortcut)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, shortcut, response = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting, shortcut, response, name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the word "conscience" and ends badly after a hero ignores it.',
        f"Tell a superhero story where {f['hero'].id} wants to save the day in {f['setpiece'].scene}, but takes {f['shortcut'].label} and learns too late that conscience matters.",
        f'Write a short, child-facing story with capes, rooftop action, and a bad ending that teaches what happens when someone ignores conscience.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    shortcut = f["shortcut"]
    city = f["city"]
    return [
        QAItem(
            question="What did the hero want to do?",
            answer=f"{hero.id} wanted to save the day and help people in the city. The goal sounded brave, but the bad choice made the rescue go wrong."
        ),
        QAItem(
            question="What did the helper warn about?",
            answer=f"{helper.id} warned that {hero.id}'s conscience was right and that {shortcut.label} could hurt the city. The warning mattered because the shortcut would cause danger before help arrived."
        ),
        QAItem(
            question="Why is the ending bad?",
            answer=f"The ending is bad because the hero ignored conscience, took {shortcut.label}, and the city ended up damaged. Even when a grown-up hero came, it was too late to stop the harm."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is conscience?", "Conscience is the quiet feeling that helps you tell right from wrong. It can warn you when something looks brave but is actually a bad choice."),
        QAItem("What does a superhero usually try to do?", "A superhero usually tries to help people, stop danger, and protect the city. Good superheroes use courage and good choices together."),
        QAItem("Why can a shortcut be dangerous?", "A shortcut can be dangerous if it skips an important safety step. Then the quick choice can create a bigger problem than the one it was meant to solve."),
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:7} ({e.type}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
danger_city :- chose_shortcut, shortcut_risk(R), R >= 2.
bad_end :- danger_city.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("shortcut_risk", sid, s.risk))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE FAIL: {exc}")
        return 1
    py = set(valid_combos())
    if set(asp_valid_combos()) != py:
        print("MISMATCH in ASP parity.")
        rc = 1
    else:
        print(f"OK: ASP parity for {len(py)} combos.")
    print("OK: generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SHORTCUTS[params.shortcut], RESPONSES[params.response])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("downtown", "shortcut", "tow", "Aster"),
    StoryParams("harbor", "blast", "shield", "Nova"),
    StoryParams("midtown", "dash", "beam", "Jet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
