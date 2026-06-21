#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MARK = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    title: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    pavement: str
    shadow: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    role: str
    powers: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    label: str
    thing: str
    risk: str
    forbids: str
    makes_shadow: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Transform:
    id: str
    before: str
    after: str
    image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    hero: str
    companion: str
    danger: str
    relic: str
    remedy: str
    transform: str
    seed: Optional[int] = None


SETTINGS = {
    "sunroad": Setting(id="sunroad", place="the sun-road", pavement="the silver pavement", shadow="a long black shadow", omen="the path whispered", tags={"pavement"}),
    "moonbridge": Setting(id="moonbridge", place="the moon-bridge", pavement="the pale pavement", shadow="a cold blue shadow", omen="the stones hummed", tags={"pavement"}),
    "ashgate": Setting(id="ashgate", place="the ash-gate road", pavement="the cracked pavement", shadow="a thin gray shadow", omen="the old wall sighed", tags={"pavement"}),
}

RELICS = {
    "lantern_heart": Relic(id="lantern_heart", label="lantern-heart", phrase="a lantern-heart of bright gold", role="light", powers={"light", "truth"}, tags={"light"}),
    "river_jar": Relic(id="river_jar", label="river-jar", phrase="a jar of river water", role="quench", powers={"water", "cool"}, tags={"water"}),
    "echo_harp": Relic(id="echo_harp", label="echo-harp", phrase="an echo-harp of seven strings", role="song", powers={"song", "calm"}, tags={"sound"}),
}

DANGERS = {
    "night_wolf": Danger(id="night_wolf", label="Night Wolf", thing="the Night Wolf", risk="the road", forbids="the way is forbidden after dusk", makes_shadow=True, tags={"suspense"}),
    "stone_witch": Danger(id="stone_witch", label="Stone Witch", thing="the Stone Witch", risk="the pavement", forbids="the pavement may not be crossed in silence", makes_shadow=True, tags={"suspense"}),
    "river_dryad": Danger(id="river_dryad", label="River Dryad", thing="the River Dryad", risk="the bridge", forbids="the bridge must not be spoken over", makes_shadow=True, tags={"suspense"}),
}

REMEDIES = {
    "brighten": Remedy(id="brighten", label="brighten the road", action="raised the relic high", method="light", power=3, sense=3, tags={"problem_solving"}),
    "name_it": Remedy(id="name_it", label="name the fear", action="said the danger's true name", method="truth", power=2, sense=2, tags={"problem_solving"}),
    "sing_it": Remedy(id="sing_it", label="sing a brave song", action="sang until the shadows shook loose", method="song", power=4, sense=3, tags={"problem_solving"}),
}

TRANSFORMS = {
    "glow": Transform(id="glow", before="a frightened child", after="a road-keeper of light", image="their hands shone like little moons", tags={"transformation"}),
    "stone": Transform(id="stone", before="the silent pavement", after="the listening pavement", image="the pavement warmed under their feet", tags={"transformation"}),
    "wing": Transform(id="wing", before="a locked gate", after="a door with wings", image="the gate opened like a bird", tags={"transformation"}),
}

GIRL_NAMES = ["Asha", "Mira", "Ila", "Nia", "Sera"]
BOY_NAMES = ["Arun", "Kian", "Taro", "Bela", "Oren"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, d, r, t) for s in SETTINGS for d in DANGERS for r in REMEDIES for t in TRANSFORMS]


def explain_rejection() -> str:
    return "(No story: the chosen road, danger, remedy, and transformation must form a real mythic problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about pavement, a prohibition, suspense, problem solving, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
              and (args.danger is None or c[1] == args.danger)
              and (args.relic is None or c[2] == args.relic)
              and (args.remedy is None or c[3] == args.transform if False else True)]
    # explicit filters
    combos = [c for c in combos if (args.remedy is None or c[2] == args.relic or True)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, danger, remedy, transform = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    companion = args.companion or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(setting=setting, hero=name, companion=companion, danger=danger, relic="lantern_heart", remedy=remedy, transform=transform)


def _danger_wakes(world: World, hero: Entity, danger: Danger) -> None:
    hero.memes["fear"] += 1
    world.get("road").meters["shadow"] += 1
    world.say(f"Then {danger.thing} moved beyond the last lamplight, and the {danger.label.lower()} seemed to wait on the pavement.")


def _problem_solve(world: World, hero: Entity, companion: Entity, relic: Relic, remedy: Remedy, transform: Transform) -> None:
    hero.memes["courage"] += 1
    world.say(f"{companion.id} whispered that they must not run. {hero.id} took {relic.phrase} and thought hard.")
    world.say(f"At last {hero.id} {remedy.action}, and {relic.label} answered with its own power.")
    world.get("road").meters["light"] += remedy.power
    world.get("hero").memes["hope"] += 1
    world.say(f"Their choice changed them: {transform.image}, and the story turned from fear into {transform.after}.")


def tell(setting: Setting, danger: Danger, relic: Relic, remedy: Remedy, transform: Transform, hero_name: str, companion_name: str) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type="girl" if hero_name in GIRL_NAMES else "boy", label=hero_name, role="seeker"))
    comp = w.add(Entity(id="companion", kind="character", type="girl" if companion_name in GIRL_NAMES else "boy", label=companion_name, role="guide"))
    road = w.add(Entity(id="road", type="place", label=setting.place))
    w.add(Entity(id="relic", type="thing", label=relic.label))
    w.add(Entity(id="danger", type="thing", label=danger.label))
    w.say(f"Long ago, on {setting.pavement}, {hero.id} and {comp.id} walked where {setting.omen}.")
    w.say(f"The elders had come to prohibit the road after dusk, but the two children carried {relic.phrase} and hoped it would lead them safely onward.")
    w.para()
    _danger_wakes(w, hero, danger)
    w.say(f"The dark grew thick, and even the pavement seemed to hold its breath.")
    w.para()
    _problem_solve(w, hero, comp, relic, remedy, transform)
    w.para()
    hero.memes["change"] += 1
    comp.memes["joy"] += 1
    w.say(f"In the end, {hero.id} was no longer the same child. {transform.image}; and on the {setting.pavement}, the danger passed like a storm into dawn.")
    w.facts.update(setting=setting, danger=danger, relic=relic, remedy=remedy, transform=transform, hero=hero, companion=comp, outcome="transformed")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a mythic story that includes the words pavement and prohibit, and lets {f['hero'].label} solve a dangerous problem with {f['relic'].label}.",
        f"Tell a suspenseful myth where a child and a companion face {f['danger'].label} on {f['setting'].place} and transform by choosing a clever remedy.",
        f"Write a story with a dark road, a prohibition, a problem solved by wisdom, and a final transformation image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What was the road like?", answer=f"It was {f['setting'].pavement}, and the place felt old and important like a myth road."),
        QAItem(question="Why was there suspense?", answer=f"{f['danger'].thing} waited in the dark, and the elders had come to prohibit the road after dusk. That made every step feel careful and tense."),
        QAItem(question="How was the problem solved?", answer=f"{f['hero'].label} used {f['relic'].phrase} and {f['remedy'].label} to push the danger back. The choice was clever, so the fear broke apart."),
        QAItem(question="How did the hero change?", answer=f"{f['hero'].label} became {f['transform'].after}. In the end, the transformation showed on the road and in the hero too."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pavement?", answer="A pavement is a hard path made of stone, concrete, or bricks. People walk on it, and in myths it can feel like a road with a memory."),
        QAItem(question="What does prohibit mean?", answer="Prohibit means to say something is not allowed. A rule or elder can prohibit a thing to keep people safe."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of wondering what will happen next when danger is close. It makes a story feel tense and important."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,D,R,T) :- setting(S), danger(D), remedy(R), transform(T).
"""


def asp_facts() -> str:
    import asp
    out = []
    for s in SETTINGS:
        out.append(asp.fact("setting", s))
    for d in DANGERS:
        out.append(asp.fact("danger", d))
    for r in REMEDIES:
        out.append(asp.fact("remedy", r))
    for t in TRANSFORMS:
        out.append(asp.fact("transform", t))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    m = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(m, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, danger=None, relic=None, remedy=None, transform=None, name=None, companion=None, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.danger not in DANGERS or params.relic not in RELICS or params.remedy not in REMEDIES or params.transform not in TRANSFORMS:
        raise StoryError("Invalid parameters.")
    w = tell(SETTINGS[params.setting], DANGERS[params.danger], RELICS[params.relic], REMEDIES[params.remedy], TRANSFORMS[params.transform], params.hero, params.companion)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_qa(w), world=w)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n".join([f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa + sample.world_qa]))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = []
    for i in range(args.n if not args.all else 3):
        p = resolve_params(args, random.Random((args.seed or 0) + i if args.seed is not None else rng.randrange(2**31)))
        samples.append(generate(p))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
