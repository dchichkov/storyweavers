#!/usr/bin/env python3
"""
Storyworld: intent_magic_bravery_fable
======================================

A small fable-like story domain about a child of the woods, a magical wish,
and the bravery needed to act on a good intent.

Premise:
- A tiny hero wants to help a neighbor.
- A magical object can do the helping, but only if the hero uses it wisely.
- Bravery is the turn: the hero must step forward, speak kindly, and keep the
  promise even when the task is scary.

The world model tracks:
- physical meters: distance, glow, weight, safety, storm, carried, wet
- emotional memes: intent, fear, bravery, trust, relief, pride

The story is generated from simulated state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    carries_magic: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    kind: str
    weather: str
    danger: str
    serenity: str


@dataclass
class Relic:
    label: str
    phrase: str
    magic: str
    helps: str
    glow: str
    risky: str


@dataclass
class StoryParams:
    setting: str
    relic: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, relic: Relic) -> None:
        self.setting = setting
        self.relic = relic
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w = World(self.setting, self.relic)
        w.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in self.entities.items()}
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "meadow": Setting(
        place="the meadow",
        kind="meadow",
        weather="breezy",
        danger="a thorny briar patch",
        serenity="soft grass and bees",
    ),
    "river": Setting(
        place="the riverbank",
        kind="riverbank",
        weather="misty",
        danger="a swift current",
        serenity="flat stones and reeds",
    ),
    "village": Setting(
        place="the village lane",
        kind="village",
        weather="cool",
        danger="a dark well",
        serenity="warm windows and bread smell",
    ),
}

RELICS = {
    "lantern": Relic(
        label="lantern",
        phrase="a small brass lantern",
        magic="light",
        helps="find the safe path",
        glow="glowed like a little star",
        risky="the dark",
    ),
    "cloak": Relic(
        label="cloak",
        phrase="a blue cloak with silver thread",
        magic="warmth",
        helps="cross the cold place",
        glow="shone softly at the hem",
        risky="the cold",
    ),
    "bell": Relic(
        label="bell",
        phrase="a tiny silver bell",
        magic="warning",
        helps="call for help",
        glow="tinkled with a bright note",
        risky="silence",
    ),
}

HEROES = ["Milo", "Lina", "Tara", "Pip", "Nora", "Eli"]
HELPERS = ["Aunt Reed", "Old Wren", "Moss", "Grandma Fern"]


def _set(world: World, eid: str, *, meters: Optional[dict[str, float]] = None, memes: Optional[dict[str, float]] = None) -> None:
    e = world.get(eid)
    if meters:
        e.meters.update(meters)
    if memes:
        e.memes.update(memes)


def _gain(world: World, eid: str, *, meters: Optional[dict[str, float]] = None, memes: Optional[dict[str, float]] = None) -> None:
    e = world.get(eid)
    if meters:
        for k, v in meters.items():
            e.meters[k] = e.meters.get(k, 0.0) + v
    if memes:
        for k, v in memes.items():
            e.memes[k] = e.memes.get(k, 0.0) + v


def predict_risk(world: World, hero: Entity) -> bool:
    sim = world.copy()
    _gain(sim, hero.id, meters={"distance": 1.0}, memes={"fear": 0.3, "intent": 1.0})
    if sim.setting.kind == "riverbank":
        _gain(sim, hero.id, meters={"wet": 1.0}, memes={"fear": 0.4})
    return hero.e("fear") + sim.get(hero.id).e("fear") >= 1.0


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a small wanderer who cared deeply about doing the right thing. "
        f"{helper.label} lived nearby and always had a patient smile."
    )
    world.say(
        f"One day, {hero.id} found {world.relic.phrase}, and it {world.relic.glow}."
    )


def desire(world: World, hero: Entity) -> None:
    _gain(world, hero.id, memes={"intent": 1.0, "joy": 0.4})
    world.say(
        f"{hero.id} wanted to use the {world.relic.label} to help someone at once, "
        f"because a kind intent had taken root in {hero.pronoun('possessive')} heart."
    )


def arrive(world: World, hero: Entity) -> None:
    _gain(world, hero.id, meters={"distance": 1.0})
    world.say(
        f"{hero.id} went to {world.setting.place}, where {world.setting.serenity} sat beside "
        f"{world.setting.danger}."
    )


def warn(world: World, hero: Entity) -> None:
    if predict_risk(world, hero):
        _gain(world, hero.id, memes={"fear": 1.0})
        world.say(
            f"But {world.setting.danger} made {hero.id} pause. "
            f"The little one knew that brave choices could still be trembling choices."
        )


def brave_step(world: World, hero: Entity) -> None:
    _gain(world, hero.id, memes={"bravery": 1.0}, meters={"safety": 0.3})
    world.say(
        f"{hero.id} took a breath, held the {world.relic.label} close, and stepped forward anyway."
    )


def use_magic(world: World, hero: Entity, helper: Entity) -> None:
    _gain(world, hero.id, meters={"glow": 1.0}, memes={"trust": 1.0})
    if world.setting.kind == "meadow" and world.relic.label == "lantern":
        world.say(
            f"{world.relic.phrase} {world.relic.glow}, and its light showed the briar patch from far away. "
            f"{hero.id} guided {helper.label} around the thorns before anyone got scratched."
        )
    elif world.setting.kind == "riverbank" and world.relic.label == "cloak":
        world.say(
            f"The cloak wrapped the cold from {hero.id}'s shoulders, and {hero.id} crossed the stones safely. "
            f"{helper.label} could follow without shivering."
        )
    else:
        world.say(
            f"The tiny bell rang once, clear and bright, and {helper.label} heard the warning in time. "
            f"Together they kept away from the well."
        )


def resolve(world: World, hero: Entity, helper: Entity) -> None:
    _gain(world, hero.id, memes={"relief": 1.0, "pride": 0.6}, meters={"safety": 1.0})
    world.say(
        f"At last, {hero.id} had done it: not by being unafraid, but by being brave enough to act kindly. "
        f"{helper.label} thanked {hero.id}, and the little hero smiled at the warm light of the day."
    )
    world.say(
        f"The {world.relic.label} stayed safe, the danger was avoided, and {hero.id}'s good intent came true."
    )


def tell(setting: Setting, relic: Relic, hero_name: str, helper_name: str) -> World:
    world = World(setting, relic)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="elder", label=helper_name))
    world.add(Entity(id="relic", kind="thing", type=relic.label, label=relic.label, phrase=relic.phrase, carries_magic=True))

    _set(world, hero.id, memes={"intent": 0.5, "fear": 0.2})
    _set(world, helper.id, memes={"trust": 0.5})

    introduce(world, hero, helper)
    world.para()
    desire(world, hero)
    arrive(world, hero)
    warn(world, hero)
    brave_step(world, hero)
    use_magic(world, hero, helper)
    world.para()
    resolve(world, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        relic=relic,
        setting=setting,
        brave=hero.memes.get("bravery", 0.0) >= THRESHOLD,
        feared=hero.memes.get("fear", 0.0) >= THRESHOLD,
        intent=hero.memes.get("intent", 0.0) >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for rid, relic in RELICS.items():
            if setting.kind == "meadow" and rid == "lantern":
                out.append((sid, rid))
            elif setting.kind == "riverbank" and rid == "cloak":
                out.append((sid, rid))
            elif setting.kind == "village" and rid == "bell":
                out.append((sid, rid))
    return out


@dataclass
class _WorldParams:
    setting: str
    relic: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


StoryParams = _WorldParams


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like world of intent, magic, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--helper-name", choices=HELPERS)
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
    combos = valid_combos()
    if args.setting or args.relic:
        combos = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.relic or c[1] == args.relic)]
    if not combos:
        raise StoryError("No valid setting/relic combination matches the given options.")
    setting, relic = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HEROES)
    helper_name = args.helper_name or rng.choice(HELPERS)
    if helper_name == hero_name:
        helper_name = rng.choice([h for h in HELPERS if h != helper_name])
    return StoryParams(setting=setting, relic=relic, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RELICS[params.relic], params.hero_name, params.helper_name)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short fable about a child who wants to use {world.relic.phrase} with good intent.",
        f"Tell a gentle story about bravery at {world.setting.place} where magic helps someone safely.",
        f"Write a child-friendly tale that shows a small hero choosing bravery over fear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    relic: Relic = world.facts["relic"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted to help at {setting.place}?",
            answer=f"{hero.id} wanted to help, and {helper.label} was the one nearby who needed care.",
        ),
        QAItem(
            question=f"What magical thing did {hero.id} find?",
            answer=f"{hero.id} found {relic.phrase}, which had the magic of {relic.magic}.",
        ),
        QAItem(
            question=f"What changed {hero.id} from scared to brave?",
            answer=f"{hero.id} felt fear at first, but then chose bravery and acted on a good intent.",
        ),
        QAItem(
            question=f"How did the magic help?",
            answer=f"The magic helped {relic.helps}, so the danger could be avoided safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    relic: Relic = world.facts["relic"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when you feel afraid.",
        ),
        QAItem(
            question="What is intent?",
            answer="Intent is the purpose or wish behind an action, like wanting to help someone.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses simple characters and teaches a lesson.",
        ),
        QAItem(
            question=f"What kind of place is {setting.place} in this story?",
            answer=f"It is a {setting.kind} place with a little danger and a little calm beside it.",
        ),
        QAItem(
            question=f"What does the {relic.label} do?",
            answer=f"The {relic.label} uses {relic.magic} magic to help keep things safe and clear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(sorted(e.meters.items()))} memes={dict(sorted(e.memes.items()))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "lantern", "Milo", "Old Wren"),
    StoryParams("river", "cloak", "Lina", "Aunt Reed"),
    StoryParams("village", "bell", "Nora", "Grandma Fern"),
]


ASP_RULES = r"""
valid_combo(meadow, lantern).
valid_combo(river, cloak).
valid_combo(village, bell).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    for sid, rid in valid_combos():
        lines.append(asp.fact("valid_combo", sid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combinations:")
        for sid, rid in triples:
            print(f"  {sid}: {rid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
