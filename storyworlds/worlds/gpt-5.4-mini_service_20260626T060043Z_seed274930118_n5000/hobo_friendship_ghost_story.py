#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-style friendship tale about a hobo and a
friendly ghost.

The core premise is simple:
- A lonely hobo wanders a quiet place at dusk.
- A shy ghost appears and wants friendship.
- A small practical problem creates tension: the hobo is cold, lost, or afraid,
  and the ghost is worried about being forgotten.
- They help each other in a concrete way, forming a friendship that changes the
  ending image.

The world model tracks physical meters and emotional memes so the prose is driven
by state rather than by a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "lost": 0.0, "glow": 0.0, "rust": 0.0}
        if not self.memes:
            self.memes = {
                "lonely": 0.0,
                "fear": 0.0,
                "friendship": 0.0,
                "hope": 0.0,
                "calm": 0.0,
                "brave": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hobo", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"ghost", "spirit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.pronoun("subject")

    def obj(self) -> str:
        return self.pronoun("object")

    def pos(self) -> str:
        return self.pronoun("possessive")


@dataclass
class Setting:
    place: str
    detail: str
    eerie: bool = True


@dataclass
class StoryParams:
    setting: str
    hobo_name: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "rail_yard": Setting(
        place="the rail yard",
        detail="Old tracks crossed the dark ground, and a wind rattled the loose metal.",
        eerie=True,
    ),
    "bridge": Setting(
        place="the river bridge",
        detail="The river moved below like a ribbon of black glass.",
        eerie=True,
    ),
    "station": Setting(
        place="the abandoned station",
        detail="Broken benches waited under a lamp that flickered like a sleepy eye.",
        eerie=True,
    ),
    "alley": Setting(
        place="the quiet alley",
        detail="Tall walls held the moonlight in a thin silver stripe.",
        eerie=True,
    ),
}

HOBO_NAMES = ["Milo", "Evan", "Ben", "Toby", "Sam", "Nico", "Jory", "Cal"]
GHOST_NAMES = ["Pip", "Mira", "Luna", "Wisp", "Dot", "Nell", "Ora", "Tansy"]


def valid_settings() -> list[str]:
    return list(SETTINGS)


def choose_name(rng: random.Random, pool: list[str], avoid: Optional[str] = None) -> str:
    picks = [n for n in pool if n != avoid] if avoid else list(pool)
    return rng.choice(picks)


def reasonableness_check(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not params.hobo_name or not params.ghost_name:
        raise StoryError("Both names are required.")
    if params.hobo_name == params.ghost_name:
        raise StoryError("The hobo and the ghost need different names.")


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hobo = world.add(Entity(
        id=params.hobo_name,
        kind="character",
        type="hobo",
        label="hobo",
        phrase=f"a hobo named {params.hobo_name}",
        meters={"cold": 1.0, "lost": 1.0, "glow": 0.0, "rust": 0.0},
        memes={"lonely": 1.0, "fear": 0.4, "friendship": 0.0, "hope": 0.0, "calm": 0.0, "brave": 0.0},
    ))
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label="ghost",
        phrase=f"a shy ghost named {params.ghost_name}",
        meters={"cold": 0.5, "lost": 0.0, "glow": 1.0, "rust": 0.0},
        memes={"lonely": 0.8, "fear": 0.3, "friendship": 0.0, "hope": 0.0, "calm": 0.0, "brave": 0.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a small lantern with a weak flame",
        owner=hobo.id,
        meters={"cold": 0.0, "lost": 0.0, "glow": 0.3, "rust": 0.0},
    ))
    world.facts.update(hobo=hobo, ghost=ghost, lantern=lantern, setting=world.setting)
    return world


def predict_turn(world: World) -> dict:
    sim = world.copy()
    hobo = sim.get(world.facts["hobo"].id)
    ghost = sim.get(world.facts["ghost"].id)
    hobo.meters["cold"] += 0.5
    hobo.meters["lost"] += 0.2
    ghost.memes["friendship"] += 0.5
    ghost.memes["hope"] += 0.5
    return {
        "cold": hobo.meters["cold"],
        "lost": hobo.meters["lost"],
        "friendship": ghost.memes["friendship"],
    }


def intro(world: World, hobo: Entity, ghost: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {hobo.phrase} wandered under a gray sky. "
        f"{hobo.subj().capitalize()} had a thin coat, an empty pocket, and a tired heart."
    )
    world.say(
        f"In the hush beside {world.setting.place}, {ghost.phrase} drifted out of the dark. "
        f"{ghost.subj().capitalize()} looked shy, but not mean."
    )


def build_tension(world: World, hobo: Entity, ghost: Entity) -> None:
    hobo.meters["cold"] += 0.8
    hobo.meters["lost"] += 0.4
    hobo.memes["lonely"] += 0.5
    ghost.memes["fear"] += 0.2
    world.say(
        f"The wind nipped {hobo.obj()} hard, and {hobo.pos()} hands shook. "
        f"{hobo.subj().capitalize()} was lonely enough to speak to the dark."
    )
    world.say(
        f"{ghost.subj().capitalize()} floated closer and whispered, "
        f"\"I am not here to scare you. I am here because I hate being alone.\""
    )


def warning(world: World, hobo: Entity, ghost: Entity) -> None:
    forecast = predict_turn(world)
    world.facts["forecast"] = forecast
    world.say(
        f"{hobo.subj().capitalize()} noticed that {ghost.pronoun('possessive')} glow "
        f"made the air feel less empty."
    )
    world.say(
        f"Still, {hobo.pronoun('possessive')} stomach was tight, because the night felt long "
        f"and {hobo.pronoun('possessive')} feet still did not know the way home."
    )


def turn_friendship(world: World, hobo: Entity, ghost: Entity) -> None:
    hobo.memes["brave"] += 0.5
    hobo.memes["hope"] += 0.6
    ghost.memes["hope"] += 0.7
    ghost.memes["friendship"] += 1.0
    hobo.memes["friendship"] += 1.0
    hobo.memes["lonely"] = 0.0
    ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 0.4)
    world.say(
        f"{hobo.subj().capitalize()} took a slow breath and said, "
        f"\"I am not much, but I can keep you company.\""
    )
    world.say(
        f"{ghost.subj().capitalize()} brightened at once, and {ghost.subj()} answered, "
        f"\"Then I can show you the safest path through the dark.\""
    )


def resolution(world: World, hobo: Entity, ghost: Entity, lantern: Entity) -> None:
    lantern.meters["glow"] += 0.7
    hobo.meters["cold"] = max(0.0, hobo.meters["cold"] - 0.6)
    hobo.meters["lost"] = max(0.0, hobo.meters["lost"] - 0.7)
    ghost.memes["calm"] += 0.8
    hobo.memes["calm"] += 0.7
    world.say(
        f"{ghost.subj().capitalize()} hovered over the little lantern and gave it a soft, pale shine. "
        f"That glow showed the broken gate and the safer road beside it."
    )
    world.say(
        f"{hobo.subj().capitalize()} followed the light and smiled. "
        f"{hobo.subj().capitalize()} was not cold in the same way anymore, and {hobo.subj()} was not alone."
    )
    world.say(
        f"By the time the moon climbed higher, {hobo.pronoun('possessive')} coat was warmer, "
        f"and {ghost.pronoun('possessive')} glow felt like a friendly hand in the dark."
    )


def tell_story(params: StoryParams) -> World:
    reasonableness_check(params)
    world = setup_world(params)
    hobo = world.get(params.hobo_name)
    ghost = world.get(params.ghost_name)
    lantern = world.get("lantern")

    intro(world, hobo, ghost)
    world.para()
    build_tension(world, hobo, ghost)
    warning(world, hobo, ghost)
    turn_friendship(world, hobo, ghost)
    world.para()
    resolution(world, hobo, ghost, lantern)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hobo = f["hobo"]
    ghost = f["ghost"]
    return [
        f'Write a short ghost story about a hobo named {hobo.id} who meets a ghost named {ghost.id} and becomes friends.',
        f'Tell a child-friendly spooky story where {hobo.id} is lonely at {world.setting.place} until {ghost.id} helps with the dark.',
        f'Write a gentle friendship story with a ghostly feeling, but end with hope, warmth, and a lantern light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hobo = f["hobo"]
    ghost = f["ghost"]
    setting = f["setting"]
    forecast = f.get("forecast", {})
    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=(
                f"It is about a hobo named {hobo.id} and a ghost named {ghost.id}. "
                f"They meet at {setting.place} and slowly become friends."
            ),
        ),
        QAItem(
            question=f"Why did {hobo.id} feel so uneasy at first?",
            answer=(
                f"{hobo.id} felt uneasy because the place was dark, {hobo.id} was cold, "
                f"and {hobo.id} did not know the way home."
            ),
        ),
        QAItem(
            question=f"What did {ghost.id} want most?",
            answer=(
                f"{ghost.id} wanted friendship. {ghost.id} was shy, but {ghost.id} did not want "
                f"to be alone in the dark."
            ),
        ),
        QAItem(
            question=f"How did the two of them help each other?",
            answer=(
                f"{ghost.id} gave light and showed a safer path, while {hobo.id} gave company "
                f"and kindness. That made both of them feel braver and less lonely."
            ),
        ),
        QAItem(
            question=f"Why did the ending feel happier than the beginning?",
            answer=(
                f"At the beginning, {hobo.id} was cold and lost and {ghost.id} was lonely. "
                f"At the end, the lantern glowed, the way was clearer, and they had become friends."
            ),
        ),
        QAItem(
            question=f"What did the lantern change in the story?",
            answer=(
                f"The lantern's little glow helped the dark feel less scary. "
                f"It let them see the path and made the ending warmer."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost?",
            answer=(
                "A ghost is a spooky-looking spirit in a story. In gentle stories, a ghost can still be kind."
            ),
        ),
        QAItem(
            question="What does friendship mean?",
            answer=(
                "Friendship means caring about someone, helping them, and wanting to spend time together."
            ),
        ),
        QAItem(
            question="Why can dark places feel scary?",
            answer=(
                "Dark places can feel scary because it is harder to see, so people may imagine strange things."
            ),
        ),
        QAItem(
            question="What does a lantern do?",
            answer=(
                "A lantern makes a small light that helps people see in the dark."
            ),
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
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story friendship world.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hobo-name", choices=HOBO_NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hobo_name = args.hobo_name or rng.choice(HOBO_NAMES)
    ghost_name = args.ghost_name or choose_name(rng, GHOST_NAMES, avoid=hobo_name)
    params = StoryParams(setting=setting, hobo_name=hobo_name, ghost_name=ghost_name)
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
setting(rail_yard).
setting(bridge).
setting(station).
setting(alley).

hobo(milo).
hobo(evan).
hobo(ben).
hobo(toby).
hobo(sam).
hobo(nico).
hobo(jory).
hobo(cal).

ghost(pip).
ghost(mira).
ghost(luna).
ghost(wisp).
ghost(dot).
ghost(nell).
ghost(ora).
ghost(tansy).

friendship_story(S, H, G) :- setting(S), hobo(H), ghost(G), H != G.
#show friendship_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for name in HOBO_NAMES:
        lines.append(asp.fact("hobo", name.lower()))
    for name in GHOST_NAMES:
        lines.append(asp.fact("ghost", name.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show friendship_story/3."))
    return sorted(set(asp.atoms(model, "friendship_story")))


def asp_verify() -> int:
    import asp
    python_set = set((s, h.lower(), g.lower()) for s in SETTINGS for h in HOBO_NAMES for g in GHOST_NAMES if h != g)
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set)[:20])
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set)[:20])
    return 1


CURATED = [
    StoryParams(setting="station", hobo_name="Milo", ghost_name="Pip"),
    StoryParams(setting="bridge", hobo_name="Evan", ghost_name="Luna"),
    StoryParams(setting="rail_yard", hobo_name="Toby", ghost_name="Wisp"),
    StoryParams(setting="alley", hobo_name="Nico", ghost_name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show friendship_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}" for a in asp_valid()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hobo_name} and {p.ghost_name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
