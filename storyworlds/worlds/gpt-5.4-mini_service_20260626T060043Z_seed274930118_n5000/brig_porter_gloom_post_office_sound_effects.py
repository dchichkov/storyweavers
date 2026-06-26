#!/usr/bin/env python3
"""
storyworlds/worlds/brig_porter_gloom_post_office_sound_effects.py
==================================================================

A small slice-of-life storyworld set in a post office, built from a seed about
brig, porter, and gloom, with sound effects and a gentle misunderstanding.

The world model is intentionally compact:
- A porter keeps the post office calm and orderly.
- Ordinary sounds from mail tools and sorters can be misread as trouble.
- A child or customer may feel gloomy until the porter explains what the sound
  really was.
- The ending lands on a concrete, peaceful change in the room.

This script follows the standard storyworld contract:
- self-contained stdlib script
- eager import of shared result containers
- lazy import of asp helper inside ASP helpers only
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    caretaker: Optional[str] = None
    handled_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "porter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the post office"
    indoors: bool = True
    afford_sound_effects: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    sound: str
    source: str
    motion: str
    cause: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    worry: str
    explanation: str
    fix: str
    trigger_sound: str
    label: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.sound: Optional[SoundEffect] = None
        self.misunderstanding: Optional[Misunderstanding] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


SETTING = Setting(place="the post office", indoors=True, afford_sound_effects={"stamp", "cart", "slot", "tray", "bell"})


SOUND_EFFECTS = {
    "stamp": SoundEffect(
        id="stamp",
        sound="thunk-thunk",
        source="the postage stamp machine",
        motion="pressed a stack of stamps",
        cause="the porter fed labels into the machine",
        effect="the room heard a steady, busy thump",
        keyword="thunk-thunk",
        tags={"sound", "machine"},
    ),
    "cart": SoundEffect(
        id="cart",
        sound="clatter-clatter",
        source="the mail cart",
        motion="rolled over the tile floor",
        cause="the porter pushed the cart to the sorting table",
        effect="the wheels made a bright clattering sound",
        keyword="clatter-clatter",
        tags={"sound", "cart"},
    ),
    "slot": SoundEffect(
        id="slot",
        sound="slip",
        source="the letter slot",
        motion="swallowed a letter",
        cause="someone dropped a postcard through the slot",
        effect="the flap made a soft little slip",
        keyword="slip",
        tags={"sound", "mail"},
    ),
    "tray": SoundEffect(
        id="tray",
        sound="tap-tap",
        source="the sorting tray",
        motion="bumped against the counter",
        cause="the porter set the tray down a little too quickly",
        effect="the counter answered with a quick tapping sound",
        keyword="tap-tap",
        tags={"sound", "tray"},
    ),
    "bell": SoundEffect(
        id="bell",
        sound="ding",
        source="the service bell",
        motion="rang once",
        cause="a customer asked for help at the counter",
        effect="the bell sounded bright and neat",
        keyword="ding",
        tags={"sound", "bell"},
    ),
}


MISUNDERSTANDINGS = {
    "gloom": Misunderstanding(
        id="gloom",
        worry="the child thought the noisy sound meant something was wrong",
        explanation="it was only the porter doing an ordinary post office job",
        fix="the porter explained the sound and showed the calm, tidy cause",
        trigger_sound="cart",
        label="gloom",
    ),
    "lost_mail": Misunderstanding(
        id="lost_mail",
        worry="the customer thought a letter had fallen away and gone missing",
        explanation="the letter had simply slipped into the correct sorting tray",
        fix="the porter pointed to the tray and the customer could see it safely there",
        trigger_sound="slot",
        label="lost-mail worry",
    ),
    "broken_machine": Misunderstanding(
        id="broken_machine",
        worry="the child thought the machine was broken because it sounded so loud",
        explanation="the machine was only stamping labels as usual",
        fix="the porter showed the fresh stamps and smiled at the ordinary rhythm",
        trigger_sound="stamp",
        label="machine worry",
    ),
}


@dataclass
class StoryParams:
    sound: str
    misunderstanding: str
    hero_name: str
    hero_role: str
    child_name: str
    child_role: str
    seed: Optional[int] = None


GROWNUP_NAMES = ["Mina", "Jo", "Tess", "Rae", "Nina", "Ari", "Iris", "June"]
CHILD_NAMES = ["Pip", "Luna", "Theo", "Milo", "Nora", "Ivy", "Owen", "Sage"]
ROLES = ["porter", "customer", "child"]


def _default_hero_name() -> str:
    return "Porter"


class WorldState:
    def __init__(self, world: World) -> None:
        self.world = world
        self.hero: Optional[Entity] = None
        self.child: Optional[Entity] = None
        self.helper: Optional[Entity] = None
        self.misunderstanding_active = False


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_role,
        label="the porter" if params.hero_role == "porter" else params.hero_role,
        traits=["steady", "kind"],
        memes={"calm": 1.0, "pride": 0.3},
    ))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_role,
        label="the child" if params.child_role == "child" else params.child_role,
        traits=["curious", "quiet"],
        memes={"gloom": 1.0, "worry": 0.0},
    ))
    world.add(Entity(
        id="brig",
        kind="thing",
        type="mail_brig",
        label="the brig",
        phrase="a narrow wire brig for sorting parcels",
        owner=hero.id,
        caretaker=hero.id,
        plural=False,
        meters={"full": 0.5},
    ))
    return world


def say_intro(world: World, hero: Entity, child: Entity) -> None:
    world.say(
        f"{hero.id} was a porter at the post office, and {child.id} had come in with a small gloomy face."
    )
    world.say(
        f"On the counter sat the brig, a narrow mail sorter with little pockets for letters and slips."
    )


def say_sound(world: World, hero: Entity, sound: SoundEffect) -> None:
    hero.memes["purpose"] = hero.memes.get("purpose", 0.0) + 1.0
    world.facts["sound"] = sound
    world.say(
        f"Then {sound.sound} came from {sound.source} as {hero.id} {sound.motion}."
    )
    world.say(
        f"{sound.cause.capitalize()}, so the room heard {sound.effect}."
    )


def say_misunderstanding(world: World, child: Entity, mis: Misunderstanding, sound: SoundEffect) -> None:
    if mis.trigger_sound != sound.id:
        return
    child.memes["gloom"] = child.memes.get("gloom", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.facts["misunderstanding"] = mis
    world.say(
        f"{child.id} looked up and worried that the sound meant trouble."
    )
    world.say(
        f"{mis.worry.capitalize()}, and the little face went even more gloomy."
    )


def say_fix(world: World, hero: Entity, child: Entity, mis: Misunderstanding, sound: SoundEffect) -> None:
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    child.memes["gloom"] = max(0.0, child.memes.get("gloom", 0.0) - 0.5)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    world.say(
        f"{hero.id} noticed the worry right away and gave a gentle smile."
    )
    world.say(
        f"{mis.fix.capitalize()} {mis.explanation}, and {hero.id} pointed at the {sound.source}."
    )
    world.say(
        f"The child listened, and the gloomy feeling began to loosen."
    )


def say_resolution(world: World, hero: Entity, child: Entity, sound: SoundEffect) -> None:
    child.memes["gloom"] = 0.0
    child.memes["worry"] = 0.0
    world.say(
        f"After that, the post office felt ordinary again: the brig sat ready, the counter stayed neat, and {sound.sound} was only one more sound in a peaceful workday."
    )
    world.say(
        f"{child.id} even smiled at the tidy little sounds, and {hero.id} went back to sorting mail with easy hands."
    )


def tell_story(world: World, params: StoryParams) -> World:
    hero = world.get(params.hero_name)
    child = world.get(params.child_name)
    sound = SOUND_EFFECTS[params.sound]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    world.sound = sound
    world.misunderstanding = mis

    say_intro(world, hero, child)
    world.para()
    say_sound(world, hero, sound)
    say_misunderstanding(world, child, mis, sound)
    world.para()
    say_fix(world, hero, child, mis, sound)
    say_resolution(world, hero, child, sound)

    world.facts.update(hero=hero, child=child, sound=sound, misunderstanding=mis, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    sound: SoundEffect = f["sound"]
    mis: Misunderstanding = f["misunderstanding"]
    return [
        f'Write a short slice-of-life story set in a post office that includes the sound "{sound.sound}".',
        f"Tell a gentle story where {params.hero_name} the porter makes a {sound.keyword} sound and {params.child_name} misreads it at the post office.",
        f"Write a calm child-facing story about a brig, a porter, and a gloomy misunderstanding that ends with the real reason for the sound.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    child: Entity = f["child"]
    sound: SoundEffect = f["sound"]
    mis: Misunderstanding = f["misunderstanding"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who was working at the post office in the story?",
            answer=f"{hero.id} was the porter working at the post office and calmly handling the mail.",
        ),
        QAItem(
            question=f"What sound made {child.id} worry?",
            answer=f"The sound was {sound.sound}, which came from {sound.source}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel gloomy at first?",
            answer=f"{child.id} felt gloomy because {mis.worry.lower()}.",
        ),
        QAItem(
            question=f"What did the porter do to clear up the misunderstanding?",
            answer=f"{hero.id} explained that {mis.explanation.lower()} and showed the child the ordinary work behind the sound.",
        ),
        QAItem(
            question=f"What was the brig used for?",
            answer="The brig was used for sorting mail and keeping letters and slips in tidy little places.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the post office calm again, the noisy sound understood, and {child.id} feeling cheerful instead of gloomy.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "sound": [
        (
            "What is a sound effect?",
            "A sound effect is a noise that helps you notice what is happening, like a ding, a clatter, or a thunk.",
        )
    ],
    "mail": [
        (
            "What does a post office do?",
            "A post office sends and sorts mail like letters, postcards, and packages.",
        )
    ],
    "cart": [
        (
            "What is a mail cart for?",
            "A mail cart helps carry stacks of letters and parcels from one place to another without dropping them.",
        )
    ],
    "tray": [
        (
            "What is a sorting tray for?",
            "A sorting tray holds mail in order so people can put each piece in the right spot.",
        )
    ],
    "bell": [
        (
            "Why does a service bell ring?",
            "A service bell rings to let someone know a customer needs help.",
        )
    ],
    "brig": [
        (
            "What is a brig in this story?",
            "In this story, the brig is a mail sorter with small spaces that keeps things neat while they are being handled.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.sound.tags if world.sound else [])
    tags.add("mail")
    tags.add("brig")
    out: list[QAItem] = []
    for tag in ["sound", "mail", "cart", "tray", "bell", "brig"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    if world.sound:
        lines.append(f"  sound: {world.sound.id}")
    if world.misunderstanding:
        lines.append(f"  misunderstanding: {world.misunderstanding.id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(sound="cart", misunderstanding="gloom", hero_name="Porter", hero_role="porter", child_name="Pip", child_role="child"),
    StoryParams(sound="stamp", misunderstanding="broken_machine", hero_name="Mina", hero_role="porter", child_name="Nora", child_role="child"),
    StoryParams(sound="slot", misunderstanding="lost_mail", hero_name="Jo", hero_role="porter", child_name="Theo", child_role="child"),
    StoryParams(sound="tray", misunderstanding="gloom", hero_name="Rae", hero_role="porter", child_name="Ivy", child_role="child"),
]


ASP_RULES = r"""
sound_event(S) :- sound(S).
misunderstanding(M) :- mis(M).
causes_sound(S, M) :- sound_event(S), mis_trigger(M, S).
valid_story(S, M) :- sound_event(S), misunderstanding(M), mis_trigger(M, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_word", sid, s.sound))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("mis", mid))
        lines.append(asp.fact("mis_trigger", mid, m.trigger_sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((s, m) for s in SOUND_EFFECTS for m, mis in MISUNDERSTANDINGS.items() if mis.trigger_sound == s)
    cl = asp_valid_stories()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life post office storyworld with sound effects and misunderstanding.")
    ap.add_argument("--sound", choices=SOUND_EFFECTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--child-name")
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
    if args.misunderstanding and args.sound:
        if MISUNDERSTANDINGS[args.misunderstanding].trigger_sound != args.sound:
            raise StoryError("That misunderstanding does not fit that sound effect.")
    pairs = [(s, m) for s in SOUND_EFFECTS for m, mis in MISUNDERSTANDINGS.items() if mis.trigger_sound == s]
    if args.sound:
        pairs = [(s, m) for (s, m) in pairs if s == args.sound]
    if args.misunderstanding:
        pairs = [(s, m) for (s, m) in pairs if m == args.misunderstanding]
    if not pairs:
        raise StoryError("No valid sound and misunderstanding pair matches the given options.")
    sound, mis = rng.choice(sorted(pairs))
    hero_name = args.name or _default_hero_name()
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    return StoryParams(sound=sound, misunderstanding=mis, hero_name=hero_name, hero_role="porter", child_name=child_name, child_role="child")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell_story(world, params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible sound/misunderstanding pairs:\n")
        for s, m in stories:
            print(f"  {s:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.sound} / {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
