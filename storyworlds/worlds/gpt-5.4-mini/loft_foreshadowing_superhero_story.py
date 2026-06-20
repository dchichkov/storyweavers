#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py
======================================================================

A standalone story world for a tiny superhero tale in a loft.

Premise
-------
A child and a young hero are in a loft when a small clue warns them that a
problem is coming. They notice the clue, prepare, then use a simple superhero
plan to save the day and finish with a bright new ending image.

This world keeps the story close to a superhero story style: capes, gadgets,
quick thinking, a little danger, and a hopeful rescue. The special narrative
instrument is foreshadowing: the world plants an early clue that becomes
important later.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py
    python storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py --trace
    python storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/loft_foreshadowing_superhero_story.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Rule:
    name: str
    apply: callable

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_alarm(world: World) -> list[str]:
    out = []
    beacon = world.entities.get("beacon")
    if not beacon or beacon.meters["glow"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["alert"] += 1
    world.get("kid").memes["alert"] += 1
    world.get("loft").meters["risk"] += 1
    out.append("__alarm__")
    return out


def _r_brave(world: World) -> list[str]:
    out = []
    if world.get("hero").memes["alert"] < THRESHOLD:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["resolve"] += 1
    out.append("__resolve__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("brave", _r_brave)]


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


@dataclass
class Scene:
    id: str
    loft: str
    hero_label: str
    clue: str
    danger: str
    rescue_gadget: str
    rescue_line: str
    ending_image: str
    clue_hint: str
    danger_place: str
    risk_meter: int = 1

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SCENES = {
    "storm": Scene(
        "storm",
        "a bright loft with tall windows and dusty beams",
        "Skybolt",
        "a tiny crack of lightning across a window",
        "a loose lantern near the paint cans",
        "storm shield",
        "threw a strong metal cover over the lantern",
        "the loft stayed bright and safe, with the storm kept outside",
        "That crack in the sky was a clue that thunder was coming",
        "the windowsill",
        2,
    ),
    "thief": Scene(
        "thief",
        "a quiet loft above the bakery",
        "Comet Kid",
        "a little boot print on the ladder",
        "an open hatch near the secret map",
        "grapple rope",
        "pulled the hatch shut and tied it tight with a rope",
        "the secret map stayed hidden, and the loft door stayed locked",
        "That boot print was a clue that someone sneaky had been close",
        "the ladder",
        1,
    ),
    "smoke": Scene(
        "smoke",
        "a cozy loft stacked with old toys",
        "Captain Star",
        "a wisp of smoke drifting from a box fan",
        "a dusty fan near a pile of paper stars",
        "wind mask",
        "turned off the fan and opened the loft windows wide",
        "the smoke floated out, and the paper stars stayed safe",
        "That wisp of smoke was a clue that something was getting hot",
        "the fan",
        2,
    ),
}


@dataclass
@dataclass
class StoryParams:
    scene: str
    hero_name: str
    kid_name: str
    kid_gender: str
    parent_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


HERO_NAMES = ["Skybolt", "Comet Kid", "Captain Star", "Blue Flash", "Rocket Ray"]
KID_NAMES = ["Mia", "Noah", "Ava", "Leo", "Zoe", "Finn", "Nora", "Eli"]
PARENTS = ["mom", "dad"]
GENDERS = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero loft story world with foreshadowing.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--kid", choices=KID_NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, hero) for sid in SCENES for hero in HERO_NAMES]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for hero in HERO_NAMES:
        lines.append(asp.fact("hero", hero))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, H) :- scene(S), hero(H).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    if rc == 0:
        print("OK: ASP parity passed.")
    return rc


def clue_is_useful(scene: Scene) -> bool:
    return bool(scene.clue and scene.danger)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.hero is None or c[1] == args.hero)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, hero = rng.choice(sorted(combos))
    kid = args.kid or rng.choice(KID_NAMES)
    gender = args.gender or rng.choice(GENDERS)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(scene=scene, hero_name=hero, kid_name=kid, kid_gender=gender, parent_name=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sc = f["scene"]
    return [
        f'Write a superhero story for a young child that takes place in {sc.loft} and includes the word "loft".',
        f"Tell a story where {f['hero'].id} notices a tiny clue before trouble starts and then saves the day.",
        "Write a foreshadowing story with a loft, a warning sign, and a brave rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    kid = f["kid"].id
    scene = f["scene"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero} and {kid}, who are in the loft when a small clue appears. The clue matters because it points to the trouble before it grows."
        ),
        QAItem(
            question="What was the clue?",
            answer=f"The clue was {scene.clue}. It foreshadowed the danger by warning that something nearby was about to become a problem."
        ),
        QAItem(
            question="How did the hero solve the problem?",
            answer=f"{hero} used the {scene.rescue_gadget} and {scene.rescue_line}. That quick superhero move stopped the trouble before it could spread."
        ),
    ]
    if f.get("saved"):
        qa.append(QAItem(
            question="How did the loft look at the end?",
            answer=f"It looked calm and bright again, and {scene.ending_image}. The ending shows that the danger was handled safely."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early so readers can guess that something important will happen later. It makes the ending feel prepared and clever."
        ),
        QAItem(
            question="What is a loft?",
            answer="A loft is a room high up under a roof. It often feels open, bright, and a little bit secret."
        ),
        QAItem(
            question="Why do superheroes use gadgets?",
            answer="Superheroes use gadgets to solve problems quickly and safely. A good gadget can help a hero protect people without making the danger worse."
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(scene: Scene, hero_name: str, kid_name: str, kid_gender: str, parent_name: str) -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type="hero", role="protector"))
    kid = w.add(Entity(id=kid_name, kind="character", type=kid_gender, role="child"))
    parent = w.add(Entity(id=parent_name, kind="character", type=parent_name))
    loft = w.add(Entity(id="loft", kind="place", type="place", label=scene.loft))
    clue = w.add(Entity(id="clue", kind="thing", type="signal", label=scene.clue))
    danger = w.add(Entity(id="danger", kind="thing", type="hazard", label=scene.danger))
    gadget = w.add(Entity(id="gadget", kind="thing", type="tool", label=scene.rescue_gadget))
    w.facts.update(scene=scene, hero=hero, kid=kid, parent=parent, loft=loft, clue=clue, danger=danger, gadget=gadget)

    hero.memes["brave"] = 1
    kid.memes["curious"] = 1

    w.say(f"In a tall loft, {hero.id} and {kid.id} were building a pretend rescue station.")
    w.say(f"{scene.clue_hint} in the room. {hero.id} noticed it first and paused.")

    w.para()
    w.say(f'"Look," {hero.id} said softly. "That is a clue."')
    w.say(f"{kid.id} followed {hero.pronoun('object')} gaze and saw {scene.clue}.")
    w.say(f"It was a small thing, but it warned them that {scene.danger} was near.")

    w.para()
    hero.memes["caution"] += 1
    kid.memes["worry"] += 1
    w.say(f"Then the trouble began at {scene.danger_place}.")
    w.say(f"{hero.id} sprang into action like a true superhero.")
    w.say(f"{hero.id} {scene.rescue_line}.")
    w.say(f"{kid.id} cheered, because the warning had helped them act in time.")

    w.para()
    if scene.id == "storm":
        w.say("A crack of thunder rolled far away, but the loft stayed safe and warm.")
    elif scene.id == "thief":
        w.say("No sneaky footsteps came back, and the hidden map stayed exactly where it should.")
    else:
        w.say("Fresh air moved through the room, and the last wisp of danger floated away.")

    w.say(f"At the end, {scene.ending_image}.")
    hero.memes["pride"] += 1
    kid.memes["relief"] += 1
    w.facts["saved"] = True
    return w


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], params.hero_name, params.kid_name, params.kid_gender, params.parent_name)
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
    StoryParams("storm", "Skybolt", "Mia", "girl", "mom"),
    StoryParams("thief", "Comet Kid", "Noah", "boy", "dad"),
    StoryParams("smoke", "Captain Star", "Ava", "girl", "mom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (scene, hero) combos:")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
