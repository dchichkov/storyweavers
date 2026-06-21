#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/extinguisher_tiger_film_moral_value_happy_ending.py
====================================================================================

A small standalone storyworld about a space-station film crew, a tiger prop, a
film reel, and a grown-up with an extinguisher. The world aims for a gentle
space-adventure tone with a clear moral value and a happy ending: when the reel
sparks, the children call for help, the fire is put out, and honesty turns a
scary mistake into a brighter lesson.

This script follows the shared storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- reasonableness gate plus inline ASP twin
- prompts, story QA, and world-knowledge QA
- generate / emit / main / parser / verify / JSON / trace / QA / ASP modes
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0


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
    flammable: bool = False
    makes_heat: bool = False
    has_extinguisher: bool = False

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


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    role: str
    makes_heat: bool = False
    flammable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fire_started") and ("spread",) not in world.fired:
        world.fired.add(("spread",))
        for e in world.chars():
            e.memes["fear"] += 1
        world.get("bay").meters["danger"] += 1
        out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(prop: Prop, setting: Setting) -> bool:
    return prop.flammable and "film" in setting.supports


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPS.items():
            if pid != "film" or hazard_at_risk(prop, setting):
                for rid, resp in RESPONSES.items():
                    if resp.sense >= SENSE_MIN:
                        combos.append((sid, pid, rid))
    return combos


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def _do_fire(world: World, narrate: bool = True) -> None:
    world.facts["fire_started"] = True
    world.get("film").meters["burning"] += 1
    world.get("bay").meters["danger"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, delay: int) -> dict:
    sim = world.copy()
    _do_fire(sim, narrate=False)
    return {"danger": sim.get("bay").meters["danger"], "delay": delay}


def setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On the bright space station {setting.place}, {hero.id} and {friend.id} were making a film. "
        f"{setting.detail}"
    )
    world.say(
        f'Their pretend space story had a brave tiger, a shiny camera, and a big promise to show everyone how teamwork could save the day.'
    )


def want_scene(world: World, hero: Entity, prop: Prop) -> None:
    world.say(
        f'{hero.id} pointed at the set. "We need the {prop.label} to make the scene look real," '
        f"{hero.pronoun()} said."
    )


def warn(world: World, friend: Entity, hero: Entity, prop: Prop) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} frowned. "{prop.label.capitalize()} can be dangerous near hot lights," '
        f"{friend.pronoun()} said. \"Let's ask a grown-up if anything starts to smoke.\""
    )


def ignite(world: World, prop: Prop) -> None:
    _do_fire(world)
    world.say(
        f"The hot lamp tapped the edge of the film reel. It curled once, then a small flame flickered up."
    )


def call_help(world: World, adult: Entity) -> None:
    world.say(f'"{adult.label_word.upper()}!" the children shouted.')
    world.say(f"{adult.label_word.capitalize()} came running with an extinguisher in both hands.")


def rescue(world: World, adult: Entity, response: Response) -> None:
    world.get("film").meters["burning"] = 0
    world.get("bay").meters["danger"] = 0
    adult.memes["calm"] += 1
    world.say(
        f"{adult.pronoun().capitalize()} {response.success}."
    )
    world.say(
        f"The flame hissed out at once, and only a gray puff of smoke drifted above the set."
    )


def lesson(world: World, adult: Entity, hero: Entity, friend: Entity, prop: Prop) -> None:
    for e in (hero, friend):
        e.memes["relief"] += 1
        e.memes["honesty"] += 1
        e.memes["moral"] += 1
    world.say(
        f"Then {adult.id} knelt down and was not angry. \"If something gets hot, tell me right away,\" "
        f"{adult.pronoun()} said. \"That is how we keep each other safe.\""
    )
    world.say(
        f"{hero.id} and {friend.id} promised to speak up fast, because a good crew tells the truth before a small spark becomes a big problem."
    )


def ending(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, the children finished the film with safer lights, and the tiger stayed bright on the screen instead of near the flame."
    )
    world.say(
        f"When the last scene was done, they waved from the bay and smiled at the stars outside the window."
    )


@dataclass
class StoryParams:
    setting: str
    prop: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    seed: Optional[int] = None
    delay: int = 0


SETTINGS = {
    "moon_bay": Setting("moon_bay", "Moon Bay", "The docking bay looked like a silver cave, with star charts on the wall and a screen glowing blue.", supports={"film"}),
    "orbital_stage": Setting("orbital_stage", "Orbital Stage", "The little stage had bright lamps, a curtain of stars, and cables tucked under the floor.", supports={"film"}),
    "cargo_hall": Setting("cargo_hall", "Cargo Hall", "The cargo hall was wide and echoey, with boxes stacked like towers and a camera cart by the door.", supports={"film"}),
}

PROPS = {
    "tiger": Prop("tiger", "tiger", "a tiger costume", "scene prop", tags={"tiger"}),
    "film": Prop("film", "film reel", "a reel of film", "scene prop", flammable=True, tags={"film"}),
    "extinguisher": Prop("extinguisher", "extinguisher", "an extinguisher", "safety tool", tags={"extinguisher"}),
}

RESPONSES = {
    "extinguisher": Response("extinguisher", 3, 4, "grabbed the extinguisher and sprayed until the fire was gone", "tried to spray, but the flames were already too big", "put the fire out with the extinguisher", tags={"extinguisher"}),
    "blanket": Response("blanket", 2, 2, "covered the smoking reel with a thick blanket and smothered the sparks", "covered it too slowly, and the fire kept growing", "smothered the sparks with a blanket", tags={"blanket"}),
    "call_help": Response("call_help", 3, 3, "called for help and used the extinguisher with a steady hand", "called for help, but the flames were already too strong", "called for help and put the fire out", tags={"extinguisher"}),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Zoe", "Lily"]
BOY_NAMES = ["Leo", "Max", "Noah", "Eli", "Finn", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a tiger, a film reel, and an extinguisher.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["captain", "engineer"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.prop and args.prop != "film":
        raise StoryError("This world needs the film reel to be the thing that can catch fire.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, response = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero])
    adult = args.adult or rng.choice(["captain", "engineer"])
    return StoryParams(setting=setting, prop=prop, response=response, hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender, adult=adult, delay=args.delay)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type="adult", label=f"the {params.adult}"))
    tiger = world.add(Entity(id="tiger", kind="thing", type="thing", label="tiger", attrs={"role": "hero prop"}))
    film = world.add(Entity(id="film", kind="thing", type="thing", label="film reel", flammable=True))
    extinguisher = world.add(Entity(id="extinguisher", kind="thing", type="thing", label="extinguisher", has_extinguisher=True))

    setup(world, hero, friend, setting)
    world.para()
    want_scene(world, hero, PROPS["tiger"])
    warn(world, friend, hero, PROPS["film"])
    world.say(f"The brave tiger prop stood near the camera, while the film reel waited beside a hot lamp.")

    world.para()
    world.say(f"{hero.id} decided to try one more shot, and the lamp made the room shine like a tiny rocket bay.")
    ignite(world, PROPS["film"])
    call_help(world, adult)
    response = RESPONSES[params.response]
    if is_contained(response, params.delay):
        rescue(world, adult, response)
        lesson(world, adult, hero, friend, PROPS["film"])
        world.para()
        ending(world, hero, friend, setting)
    else:
        world.say(f"The fire grew faster than the crew could handle, but everyone still got out safely.")
        world.say(f"Even so, they learned that telling the truth early is the bravest choice.")

    world.facts.update(hero=hero, friend=friend, adult=adult, tiger=tiger, film=film, extinguisher=extinguisher,
                       setting=setting, prop=PROPS["film"], response=response, outcome="happy", delay=params.delay)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a space-adventure story that includes the words extinguisher, tiger, and film, and ends happily.",
        "Tell a child-friendly story about a film reel near a hot light, a tiger prop on set, and a calm adult using an extinguisher.",
        "Write a moral story in space where the crew tells the truth quickly, gets help, and finishes safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    return [
        QAItem(
            question="What were the children making?",
            answer=f"They were making a film on the space station. They wanted the tiger prop to look exciting and space-brave."
        ),
        QAItem(
            question="Why did the grown-up need the extinguisher?",
            answer="The film reel got too close to a hot lamp and started to smoke. The grown-up used the extinguisher so the small fire would not grow."
        ),
        QAItem(
            question="What moral did the children learn?",
            answer="They learned to tell the truth fast and ask for help right away. That choice kept the crew safe and helped the story end happily."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an extinguisher do?",
            answer="An extinguisher is a safety tool that sprays out material to help stop a fire. Grown-ups use it on small fires to keep them from spreading."
        ),
        QAItem(
            question="What is a tiger?",
            answer="A tiger is a big striped cat. Tigers are strong animals, and in a story they can also be a costume or a pretend character."
        ),
        QAItem(
            question="What is film?",
            answer="Film is a thin strip used to record pictures or make a movie. It can be delicate, so it should be kept away from heat and flames."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(setting(S), prop(P)) :- supports(S, film), flammable(P).
sensible(response(R)) :- sense(R, K), sense_min(M), K >= M.
valid(setting(S), prop(P), response(R)) :- hazard(setting(S), prop(P)), sensible(response(R)).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for x in sorted(s.supports):
            lines.append(asp.fact("supports", sid, x))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.flammable:
            lines.append(asp.fact("flammable", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP gate does not match valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story:
            ok = False
            print("MISMATCH: smoke test produced empty story.")
    except Exception as exc:
        ok = False
        print(f"MISMATCH: smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and generate() smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.prop not in PROPS:
        raise StoryError("Unknown prop.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if params.prop != "film":
        raise StoryError("This world needs the film reel to be the flammable thing.")
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="moon_bay", prop="film", response="extinguisher", hero="Mia", hero_gender="girl", friend="Leo", friend_gender="boy", adult="captain", delay=0),
            StoryParams(setting="orbital_stage", prop="film", response="blanket", hero="Noah", hero_gender="boy", friend="Ava", friend_gender="girl", adult="engineer", delay=0),
            StoryParams(setting="cargo_hall", prop="film", response="call_help", hero="Luna", hero_gender="girl", friend="Finn", friend_gender="boy", adult="captain", delay=1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
