#!/usr/bin/env python3
"""
A small superhero story world about a twist, a tense mistake, and a warm
reconciliation.

Seed words:
- bacon
- remove

Features:
- Twist
- Reconciliation

Style:
- Superhero Story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Location:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple[str, str]] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    villain_name: str
    hero_gender: str = "boy"
    sidekick_gender: str = "girl"
    villain_gender: str = "boy"
    seed: Optional[int] = None


PLACES = {
    "city_roof": Location(id="city_roof", label="the city roof", tags={"city", "roof"}),
    "museum": Location(id="museum", label="the bright museum hall", tags={"city", "hall"}),
    "harbor": Location(id="harbor", label="the windy harbor", tags={"city", "water"}),
}

NAMES = {
    "boy": ["Miles", "Finn", "Leo", "Noah", "Eli"],
    "girl": ["Nova", "Iris", "Maya", "Zara", "June"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--sidekick-gender", choices=["boy", "girl"])
    ap.add_argument("--villain-gender", choices=["boy", "girl"])
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
    place = args.place or rng.choice(list(PLACES))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    sidekick_gender = args.sidekick_gender or ("girl" if hero_gender == "boy" else "boy")
    villain_gender = args.villain_gender or rng.choice(["boy", "girl"])
    hero = args.hero or rng.choice(NAMES[hero_gender])
    sidekick_pool = [n for n in NAMES[sidekick_gender] if n != hero]
    sidekick = args.sidekick or rng.choice(sidekick_pool)
    villain_pool = [n for n in NAMES[villain_gender] if n not in {hero, sidekick}]
    villain = args.villain or rng.choice(villain_pool)
    return StoryParams(
        place=place,
        hero_name=hero,
        sidekick_name=sidekick,
        villain_name=villain,
        hero_gender=hero_gender,
        sidekick_gender=sidekick_gender,
        villain_gender=villain_gender,
    )


@dataclass(frozen=True)
class Arc:
    key: str
    twist: str
    conflict: str
    remedy: str
    ending: str
    opener: tuple[str, str]
    trouble: tuple[str, str]
    dialogue: tuple[str, str]
    resolution: tuple[str, str]


ARCS = (
    Arc(
        key="bacon_bandit",
        twist="The bacon strips were not stolen at all; they had been wrapped around a smoke alarm sensor and needed to be removed.",
        conflict="The alarm kept screaming, and the little kitchen crowd thought a sneaky bacon bandit was on the loose.",
        remedy="The hero used a magnet glove to remove the bacon, while the sidekick held the ladder steady.",
        ending="At last the alarm fell quiet, the bacon was on a plate, and the neighbors cheered for the two heroes.",
        opener=(
            "On a windy afternoon at {place}, {hero} and {sidekick} stood ready in bright capes.",
            "They had trained all week for simple rescues, and today the city smelled strangely of bacon.",
        ),
        trouble=(
            "Then the alarm cried out in a loud, wobbly wail: twist! The sound bounced off every wall.",
            "“That is no ordinary clue,” said {sidekick}, with wide eyes and a brave little gulp.",
        ),
        dialogue=(
            "“We need to remove the problem, not just chase it,” said {hero}.",
            "“Then let us lift, reach, and calm the room,” said {sidekick}, gripping the ladder rail.",
        ),
        resolution=(
            "Together they climbed, unhooked the smoky strip, and placed it on a tray.",
            "“Sorry, little bacon,” said {hero}, “you are not a villain after all.”",
        ),
    ),
    Arc(
        key="twisted_cloak",
        twist="A gold ribbon twisted around the hero's cape clasp, making the cape snag on a statue.",
        conflict="The hero could not fly free, and the whole parade paused in worry.",
        remedy="The sidekick helped remove the ribbon while the hero held still and trusted the plan.",
        ending="When the ribbon came off, the cape snapped open like a flag, and the parade rolled on.",
        opener=(
            "At {place}, the grand hero parade was beginning under a blue sky.",
            "Children waved paper stars while {hero} and {sidekick} flew in to guide the march.",
        ),
        trouble=(
            "But a twist snagged the cape on a marble lion. The hero tugged once and stopped.",
            "“Easy,” said {sidekick}. “A stuck cape is not a scary case.”",
        ),
        dialogue=(
            "“Can you remove the ribbon without tearing the cloth?” asked {hero}.",
            "“Yes,” said {sidekick}. “Hold the clasp still, and I will free it gently.”",
        ),
        resolution=(
            "They worked with careful fingers, and the ribbon slipped away like a sleepy snake.",
            "The cape flew open again, and the crowd clapped for calm teamwork.",
        ),
    ),
    Arc(
        key="harbor_hook",
        twist="A rescue hook had twisted around the wrong rope, tying up the harbor crane.",
        conflict="A boat waited below, and the dock workers could not lift the crate of fish to safety.",
        remedy="The hero steadied the rope, and the sidekick removed the hook in one clean motion.",
        ending="The crate rose free, the boat waved goodbye, and the harbor lights blinked like stars.",
        opener=(
            "At {place}, fog drifted past the cranes and the water shone silver.",
            "{hero} and {sidekick} arrived on the roof of a rescue truck, listening for trouble.",
        ),
        trouble=(
            "Then they heard a twist in the rope and saw the hook locked fast.",
            "“If the crane cannot turn, the boat cannot wait forever,” whispered {sidekick}.",
        ),
        dialogue=(
            "“We will remove the hook together,” said {hero}.",
            "“I will hold the line,” said {sidekick}, “and you take the twist away.”",
        ),
        resolution=(
            "The hook came loose, the rope straightened, and the crane moved with a smooth hum.",
            "The dock crew thanked the heroes while the fish crate swung safely to shore.",
        ),
    ),
)


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.place}:{params.hero_name}:{params.sidekick_name}:{params.villain_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_gender, role="sidekick"))
    villain = world.add(Entity(id=params.villain_name, kind="character", type=params.villain_gender, role="villain"))
    rng = random.Random(_stable_seed(params))
    arc = ARCS[rng.randrange(len(ARCS))]

    values = {"place": place.label, "hero": hero.id, "sidekick": sidekick.id, "villain": villain.id}
    world.say(arc.opener[0].format(**values))
    world.say(arc.opener[1].format(**values))
    world.para()

    hero.memes["alert"] += 1
    sidekick.memes["alert"] += 1
    villain.memes["shifty"] += 1
    world.say(arc.trouble[0].format(**values))
    world.say(arc.trouble[1].format(**values))
    world.para()

    hero.memes["determined"] += 1
    sidekick.memes["calm"] += 1
    hero.meters["helped"] += 1
    sidekick.meters["helped"] += 1
    world.say(arc.dialogue[0].format(**values))
    world.say(arc.dialogue[1].format(**values))
    world.para()

    hero.meters["heroic"] += 1
    sidekick.meters["heroic"] += 1
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(arc.resolution[0].format(**values))
    world.say(arc.resolution[1].format(**values))
    world.para()

    world.say(arc.twist)
    world.say("Then came reconciliation: the misunderstanding was cleared up, and everyone knew who had done what.")
    world.say(arc.ending)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        place=place,
        arc=arc,
        twist=arc.twist,
        conflict=arc.conflict,
        remedy=arc.remedy,
        ending=arc.ending,
        reconciliation=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly superhero story that includes the words "bacon" and "remove".',
        f"Tell a superhero story where {f['hero'].id} and {f['sidekick'].id} face a twist at {f['place'].label}.",
        f"Make the ending about reconciliation after {f['conflict'].lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {f['twist'].replace('The ', '').rstrip('.')}"
        ),
        QAItem(
            question="How did the heroes solve the problem?",
            answer=f"They worked together to {f['remedy'].lower()}. That changed the scene from stuck and noisy to calm and safe."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation, because {f['ending'].lower()}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people make peace again after a problem or mix-up. It helps everyone feel calm and ready to work together."
        ),
        QAItem(
            question="What does remove mean?",
            answer="To remove something means to take it away from where it is. Heroes often remove a problem so others can be safe."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = [f"{e.id} ({e.type})"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append("  " + " ".join(parts))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


ASP_RULES = r"""
hero(X) :- hero_name(X).
sidekick(X) :- sidekick_name(X).
twist(X) :- twist_fact(X).
reconciled :- conflict(X), remedy(Y), remove_action(Y), calm(Z).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("sidekick_name", "sidekick"),
        asp.fact("twist_fact", "twist"),
        asp.fact("conflict", "conflict"),
        asp.fact("remove_action", "remove"),
        asp.fact("calm", "calm"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_gender not in NAMES or params.sidekick_gender not in NAMES or params.villain_gender not in NAMES:
        raise StoryError("Invalid gender.")
    if len({params.hero_name, params.sidekick_name, params.villain_name}) < 3:
        raise StoryError("Hero, sidekick, and villain must be different characters.")
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="city_roof", hero_name="Miles", sidekick_name="Nova", villain_name="Rex", hero_gender="boy", sidekick_gender="girl", villain_gender="boy"),
    StoryParams(place="museum", hero_name="Iris", sidekick_name="Finn", villain_name="Duke", hero_gender="girl", sidekick_gender="boy", villain_gender="boy"),
    StoryParams(place="harbor", hero_name="Eli", sidekick_name="Maya", villain_name="Tess", hero_gender="boy", sidekick_gender="girl", villain_gender="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=args.hero or rng.choice(NAMES[args.hero_gender or rng.choice(["boy", "girl"])]),
        sidekick_name=args.sidekick or rng.choice(NAMES[args.sidekick_gender or rng.choice(["boy", "girl"])]),
        villain_name=args.villain or rng.choice(NAMES[args.villain_gender or rng.choice(["boy", "girl"])]),
        hero_gender=args.hero_gender or rng.choice(["boy", "girl"]),
        sidekick_gender=args.sidekick_gender or rng.choice(["boy", "girl"]),
        villain_gender=args.villain_gender or rng.choice(["boy", "girl"]),
        seed=args.seed,
    )


def build_asp_show() -> str:
    return "#show reconciled/0."


def asp_verify() -> int:
    import storyworlds.asp as asp
    try:
        _ = asp.one_model(asp_program(build_asp_show()))
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("Story generation produced empty text.")
            return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(build_asp_show()))
    return sorted(set(asp.atoms(model, "reconciled")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(build_asp_show()))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
