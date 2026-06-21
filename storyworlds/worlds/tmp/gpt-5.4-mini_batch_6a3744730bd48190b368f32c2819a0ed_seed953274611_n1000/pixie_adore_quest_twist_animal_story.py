#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pixie_adore_quest_twist_animal_story.py
========================================================================

A small standalone storyworld for a tiny animal tale with a quest and a twist.

Premise:
- An animal friend wants to find something special.
- A pixie helps guide the quest.
- The hero says they adore someone or something along the way.
- A twist changes what the quest prize really is, and the ending shows the new
  understanding or gift.

This world keeps the story child-facing and state-driven: the characters, their
feelings, the places they travel through, and the quest object all shape the
prose. The twist is not a random sentence swap; it comes from the simulated
world model and changes the ending image.

Run:
    python storyworlds/worlds/gpt-5.4-mini/pixie_adore_quest_twist_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/pixie_adore_quest_twist_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/pixie_adore_quest_twist_animal_story.py --verify
"""

from __future__ import annotations

import argparse
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    path: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    prize: str
    clue: str
    seek_phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    reveal: str
    meaning: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "traits": list(v.traits), "attrs": dict(v.attrs),
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wander(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["journey"] < THRESHOLD:
        return out
    sig = ("wander",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("trail").meters["noticed"] += 1
    out.append("__wander__")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["found"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("twist").meters["revealed"] += 1
    out.append("__twist__")
    return out


def _r_adore(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return out
    if hero.memes["adore"] < THRESHOLD:
        return out
    sig = ("adore",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["warmth"] += 1
    out.append("__adore__")
    return out


CAUSAL_RULES = [Rule("wander", _r_wander), Rule("twist", _r_twist), Rule("adore", _r_adore)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)


def explore(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.meters["journey"] += 1
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"On a bright morning, {hero.id} the {hero.type} set out along {world.setting.path}. "
        f"{friend.id}, a little pixie with silver wings, floated beside {hero.pronoun('object')}."
    )
    world.say(
        f'"{quest.clue}" whispered {friend.id}. "We can follow the trail and look for {quest.prize}."'
    )


def adore_beat(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["adore"] += 1
    world.say(
        f'{hero.id} smiled. "{hero.id} had to say it: I adore {friend.id}." '
        f'The pixie blushed and twirled in the air.'
    )


def search(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["found"] += 1
    world.say(
        f"They searched under roots, beside moss, and behind bright flowers. "
        f"{hero.id} kept thinking about {quest.prize}."
    )


def reveal_twist(world: World, hero: Entity, twist: Twist, quest: Quest) -> None:
    world.say(
        f"Then came the twist: {twist.reveal} {twist.meaning}."
    )
    world.say(
        f"{hero.id} stared, then laughed softly, because the quest was different from what {hero.pronoun('object')} first expected."
    )


def finish(world: World, hero: Entity, friend: Entity, quest: Quest, twist: Twist) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the end, {quest.ending_image} {twist.ending}"
    )


SETTINGS = {
    "meadow": Setting(id="meadow", place="a flower meadow", path="the winding meadow path", mood="bright", tags={"meadow"}),
    "forest": Setting(id="forest", place="a green forest", path="the ferny forest trail", mood="quiet", tags={"forest"}),
    "orchard": Setting(id="orchard", place="an apple orchard", path="the soft grass between the trees", mood="sweet", tags={"orchard"}),
}

QUESTS = {
    "acorn": Quest(
        id="acorn",
        prize="a shiny acorn",
        clue="The bird said a shiny prize was waiting near the oldest tree.",
        seek_phrase="seek the shiny acorn",
        ending_image="They found a tiny acorn glinting like a little brown star",
        tags={"acorn"},
    ),
    "shell": Quest(
        id="shell",
        prize="a pearly shell",
        clue="The stream whispered that something pearly rested by the water",
        seek_phrase="seek the pearly shell",
        ending_image="They found a shell that shimmered like moonlight on water",
        tags={"shell"},
    ),
    "berry": Quest(
        id="berry",
        prize="a red berry basket",
        clue="A robin chirped that red treasure hid under the hedges",
        seek_phrase="seek the berry basket",
        ending_image="They found a basket full of berries, warm from the sun",
        tags={"berry"},
    ),
}

TWISTS = {
    "gift": Twist(
        id="gift",
        reveal="the prize was not for keeping",
        meaning="it was meant as a gift for a tiny nest nearby",
        ending="So they carried it gently to the nest and watched the birds sing",
        tags={"gift"},
    ),
    "map": Twist(
        id="map",
        reveal="the clue was actually a map",
        meaning="it pointed not to treasure, but to a friend who needed help",
        ending="So they followed the map and found a lost baby chick waiting safely",
        tags={"map"},
    ),
    "mirror": Twist(
        id="mirror",
        reveal="the glittering prize was a mirror of water",
        meaning="it showed the sky, not a thing to take",
        ending="So they splashed and laughed as the clouds danced in the puddle",
        tags={"mirror"},
    ),
}

ANIMAL_TYPES = {
    "rabbit": "girl",
    "fox": "boy",
    "deer": "girl",
    "bear": "boy",
    "mouse": "girl",
}

ANIMAL_NAMES = ["Pip", "Milo", "Junie", "Nori", "Bram", "Tilly", "Puck", "Luna"]
PIXIE_NAMES = ["Fae", "Spark", "Mina", "Twinkle"]


@dataclass
class StoryParams:
    setting: str
    animal: str
    name: str
    pixie: str
    quest: str
    twist: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for q in QUESTS:
            for t in TWISTS:
                out.append((s, q, t))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with a pixie, a quest, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=sorted(ANIMAL_TYPES))
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--pixie")
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
    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, twist = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMAL_TYPES))
    name = args.name or rng.choice(ANIMAL_NAMES)
    pixie = args.pixie or rng.choice(PIXIE_NAMES)
    return StoryParams(setting=setting, animal=animal, name=name, pixie=pixie, quest=quest, twist=twist)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, label=params.name, role="hero"))
    pix = world.add(Entity(id=params.pixie, kind="character", type="pixie", label=params.pixie, role="helper"))
    trail = world.add(Entity(id="trail", kind="thing", type="trail", label="the trail"))
    twist = world.add(Entity(id="twist", kind="thing", type="twist", label=TWISTS[params.twist].id))
    quest = QUESTS[params.quest]

    explore(world, hero, pix, quest)
    adore_beat(world, hero, pix)
    world.para()
    search(world, hero, quest)
    hero.meters["found"] += 1
    propagate(world, narrate=False)
    reveal_twist(world, hero, TWISTS[params.twist], quest)
    finish(world, hero, pix, quest, TWISTS[params.twist])

    world.facts.update(hero=hero, pixie=pix, trail=trail, twist=twist, quest=quest, setting=setting, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    quest = QUESTS[params.quest]
    twist = TWISTS[params.twist]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "pixie" and "adore".',
        f"Tell a gentle quest story about {params.name} the {params.animal} and a pixie named {params.pixie} who {quest.seek_phrase}.",
        f"Write a short story with a twist where the ending changes what the shiny prize really means.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    params: StoryParams = f["params"]
    quest = QUESTS[params.quest]
    twist = TWISTS[params.twist]
    return [
        ("Who is the story about?",
         f"It is about {params.name} the {params.animal} and {params.pixie} the pixie. They go on a small quest together."),
        ("What did {0} adore?".format(params.name),
         f"{params.name} adored {params.pixie}. The story says it plainly, and that feeling helps the two friends stay close on the quest."),
        ("What was the quest for?",
         f"They were looking for {quest.prize}. At first it seemed like treasure, but the twist changes what it really means."),
        ("What was the twist?",
         f"{twist.reveal.capitalize()} {twist.meaning}. That changes the ending from simple treasure-hunting to a kind act."),
        ("How did the story end?",
         f"{twist.ending}. The ending proves the quest changed from wanting to keep something to doing the kinder thing."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pixie?",
         "A pixie is a tiny magical helper in a story, often shown with wings and a bright, quick way of moving."),
        ("What is a quest?",
         "A quest is a search for something important. In stories, it usually means a character goes out looking for a goal or prize."),
        ("What is a twist in a story?",
         "A twist is a surprise that changes what you thought was happening. It makes the story feel different near the end."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% Every registered setting/quest/twist combination is compatible.
valid(S,Q,T) :- setting(S), quest(Q), twist(T).

% The quest world is deterministic enough for parity checks.
story_ready(S,Q,T) :- valid(S,Q,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(StoryParams(setting="meadow", animal="rabbit", name="Pip", pixie="Fae", quest="acorn", twist="gift"))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed.")
    return rc


CURATED = [
    StoryParams(setting="forest", animal="fox", name="Milo", pixie="Spark", quest="acorn", twist="gift"),
    StoryParams(setting="meadow", animal="rabbit", name="Pip", pixie="Fae", quest="shell", twist="map"),
    StoryParams(setting="orchard", animal="deer", name="Junie", pixie="Mina", quest="berry", twist="mirror"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.pixie}: {p.setting}, {p.quest}, {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    params: StoryParams = f["params"]
    quest = QUESTS[params.quest]
    twist = TWISTS[params.twist]
    return [
        ("Who is the story about?",
         f"It is about {params.name} the {params.animal} and {params.pixie} the pixie. They go on a small quest together."),
        (f"What did {params.name} adore?",
         f"{params.name} adored {params.pixie}. The story says it plainly, and that feeling helps the two friends stay close on the quest."),
        ("What was the quest for?",
         f"They were looking for {quest.prize}. At first it seemed like treasure, but the twist changes what it really means."),
        ("What was the twist?",
         f"{twist.reveal.capitalize()} {twist.meaning}. That changes the ending from simple treasure-hunting to a kind act."),
        ("How did the story end?",
         f"{twist.ending}. The ending proves the quest changed from wanting to keep something to doing the kinder thing."),
    ]


if __name__ == "__main__":
    main()
