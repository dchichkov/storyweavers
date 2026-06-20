#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/defensive_tag_plasticene_flashback_bad_ending_misunderstanding.py
=================================================================================================

A standalone story world for a small superhero-style domain: two kids playing
heroes, a defensive tag game, a piece of plasticene, a flashback to an earlier
warning, a misunderstanding, and a bad ending where the game goes wrong.

The world is built as a tiny causal simulation. Characters carry physical
meters and emotional memes. State changes drive the prose, and the rendered
story is not a frozen template with swapped names.

This world intentionally leans into the seed words:
- defensive
- tag
- plasticene

And the requested narrative instruments:
- Flashback
- Misunderstanding
- Bad Ending

It supports the standard Storyweavers interface:
build_parser, resolve_params, generate, emit, main
plus --qa, --json, --trace, --asp, --verify, --show-asp, --all, -n, --seed.
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
class Prop:
    id: str
    label: str
    phrase: str
    is_defensive: bool = False
    can_tag: bool = False
    is_plasticene: bool = False
    fragile: bool = False
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
class Setting:
    id: str
    place: str
    superhero_frame: str
    flashback_line: str
    closing_image: str
    sounds_like: str = ""

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
@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    defender: str
    prop: str
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


def _r_tag(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tagged"] < THRESHOLD:
            continue
        sig = ("tag", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["alarm"] += 1
        out.append("__tag__")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    if not prop or prop.meters["broken"] < THRESHOLD:
        return out
    sig = ("break", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "sidekick"}:
            ent.memes["fear"] += 1
    out.append("__break__")
    return out


CAUSAL_RULES = [Rule("tag", "social", _r_tag), Rule("break", "physical", _r_break)]


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


def would_misunderstand(world: World, defender: Entity, hero: Entity) -> bool:
    return defender.memes["warning"] >= THRESHOLD and hero.memes["pride"] >= THRESHOLD


def makes_sense(prop: Prop) -> bool:
    return prop.is_defensive and prop.can_tag and prop.is_plasticene


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hero in HERO_NAMES:
            for sidekick in SIDEKICK_NAMES:
                if sidekick == hero:
                    continue
                for defender in DEFENDER_NAMES:
                    for pid, prop in PROPS.items():
                        if makes_sense(prop):
                            combos.append((sid, hero, sidekick, pid))
    return combos


def flashback_line(world: World, setting: Setting, defender: Entity, hero: Entity, prop: Prop) -> None:
    defender.memes["warning"] += 1
    world.say(
        f"{setting.flashback_line} {defender.id} had warned {hero.id} before: "
        f'"Keep the defensive tag away from the plasticene, because it will not '
        f'hold up."'
    )


def setup(world: World, setting: Setting, hero: Entity, sidekick: Entity, defender: Entity, prop: Prop) -> None:
    hero.memes["pride"] += 1
    sidekick.memes["curiosity"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {sidekick.id} raced through "
        f"{setting.place} like little superheroes. {setting.superhero_frame}"
    )
    world.say(
        f'{hero.id} held up the {prop.label}, a {prop.phrase}, and grinned. '
        f'"This will make the best defensive tag ever!"'
    )


def warn(world: World, setting: Setting, defender: Entity, hero: Entity, prop: Prop) -> None:
    flashback_line(world, setting, defender, hero, prop)
    world.say(
        f'{defender.id} frowned. "{hero.id}, that is not a game tool." '
        f'"It is defensive, yes, but it can still break if it hits the floor."'
    )


def misunderstand(world: World, hero: Entity, sidekick: Entity, defender: Entity, prop: Prop) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f'{hero.id} thought {defender.id} meant {sidekick.id} could not play at '
        f"all, not that the {prop.label} needed to stay safe."
    )
    world.say(
        f'"We are superheroes," {hero.id} said. "Superheroes can handle a tag!"'
    )
    world.say(
        f"{sidekick.id} shrugged, because {sidekick.id} did not want to lose the "
        f"game."
    )


def accident(world: World, hero: Entity, sidekick: Entity, prop: Prop) -> None:
    prop_ent = world.get("prop")
    prop_ent.meters["tagged"] += 1
    prop_ent.meters["broken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} swung the {prop.label} in a fast tag move, and it clipped the "
        f"floor with a sharp crack."
    )
    world.say(
        f"The plasticene squished wrong, the neat shape split open, and the bright "
        f"game suddenly felt messy."
    )


def bad_ending(world: World, setting: Setting, defender: Entity, hero: Entity, sidekick: Entity, prop: Prop) -> None:
    for ent in (hero, sidekick):
        ent.memes["sadness"] += 1
        ent.memes["fear"] += 1
    world.say(
        f"{defender.id} ran over too late, and everyone stared at the broken "
        f"{prop.label} in silence."
    )
    world.say(
        f"{setting.closing_image} Now the room held only a crumpled piece of "
        f"plasticene, a ruined defensive tag, and two heroes who had learned a "
        f"hard lesson."
    )


def tell(setting: Setting, prop: Prop, hero_name: str, sidekick_name: str, defender_name: str,
         hero_gender: str = "boy", sidekick_gender: str = "girl", defender_gender: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    defender = world.add(Entity(defender_name, kind="character", type=defender_gender, role="defender"))
    prop_ent = world.add(Entity("prop", kind="thing", type="tool", label=prop.label))
    prop_ent.attrs["prop_id"] = prop.id

    setup(world, setting, hero, sidekick, defender, prop)
    world.para()
    warn(world, setting, defender, hero, prop)
    misunderstand(world, hero, sidekick, defender, prop)
    world.para()
    accident(world, hero, sidekick, prop)
    bad_ending(world, setting, defender, hero, sidekick, prop)

    world.facts.update(
        setting=setting,
        hero=hero,
        sidekick=sidekick,
        defender=defender,
        prop=prop,
        outcome="bad",
        misunderstanding=hero.memes["misunderstanding"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "rooftop": Setting(
        "rooftop",
        "the rooftop playground",
        "The bright towers below looked like a city waiting for rescue.",
        "A week earlier, on the same roof,",
        "The moon rose over the rooftop playground.",
    ),
    "alley": Setting(
        "alley",
        "the narrow alley behind the comics shop",
        "The painted walls made the lane feel like a secret hero base.",
        "Yesterday, beside the comic poster,",
        "The streetlamp turned the alley gold.",
    ),
    "lab": Setting(
        "lab",
        "the school makerspace",
        "The tables and tape rolls looked like a place where gadgets could be born.",
        "At lunch, near the toolbox,",
        "The science room lights hummed over the makerspace.",
    ),
}

PROPS = {
    "shield_tag_plasticene": Prop(
        "shield_tag_plasticene",
        "shield tag",
        "a little shield tag made of plasticene",
        is_defensive=True,
        can_tag=True,
        is_plasticene=True,
        fragile=True,
        tags={"defensive", "tag", "plasticene"},
    ),
    "star_tag_plasticene": Prop(
        "star_tag_plasticene",
        "star tag",
        "a star-shaped tag of plasticene",
        is_defensive=True,
        can_tag=True,
        is_plasticene=True,
        fragile=True,
        tags={"defensive", "tag", "plasticene"},
    ),
}

HERO_NAMES = ["Nova", "Piper", "Milo", "Zane", "Iris", "Tess"]
SIDEKICK_NAMES = ["Jun", "Rae", "Bea", "Luca", "Nia", "Owen"]
DEFENDER_NAMES = ["Captain Bright", "Aunt Spark", "Ms. Comet", "Guardian Gale"]

CURATED = [
    StoryParams("rooftop", "Nova", "Jun", "Captain Bright", "shield_tag_plasticene"),
    StoryParams("alley", "Piper", "Rae", "Aunt Spark", "star_tag_plasticene"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "defensive", "tag", and "plasticene".',
        f"Tell a story where {f['hero'].id} thinks a defensive tag game is safe, but a warning from {f['defender'].id} is misunderstood.",
        f"Write a short superhero tale with a flashback warning and a bad ending, using plasticene as the important object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, defender, prop, setting = f["hero"], f["sidekick"], f["defender"], f["prop"], f["setting"]
    return [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {sidekick.id}, and {defender.id}, who were playing like superheroes in {setting.place}.",
        ),
        (
            f"What did {hero.id} want to use?",
            f"{hero.id} wanted to use the {prop.label}, a defensive tag made of plasticene.",
        ),
        (
            f"What was the misunderstanding?",
            f"{hero.id} thought {defender.id} was saying the game must stop, but the warning was really about keeping the plasticene safe. That mix-up made {hero.id} act too fast.",
        ),
        (
            "How did the story end?",
            "It ended badly. The defensive tag broke, the plasticene got ruined, and the heroes were left with a sad, messy game.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = set(world.facts["prop"].tags)
    for tag in ["defensive", "tag", "plasticene"]:
        if tag in tags:
            if tag == "defensive":
                out.append(("What does defensive mean?", "Defensive means made to protect or guard something from harm."))
            elif tag == "tag":
                out.append(("What is tag?", "Tag is a game where players try to touch someone and call them tagged."))
            elif tag == "plasticene":
                out.append(("What is plasticene?", "Plasticene is a soft material you can shape with your hands, but it can squish out of shape if you press it too hard."))
    return out


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
tagged(E) :- entity(E), meter(E, tagged, V), V >= 1.
broken(P) :- prop(P), meter(P, broken, V), V >= 1.
misunderstanding(H) :- entity(H), meme(H, misunderstanding, V), V >= 1.
bad_ending :- broken(prop), misunderstanding(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.is_defensive:
            lines.append(asp.fact("defensive", pid))
        if p.can_tag:
            lines.append(asp.fact("tag", pid))
        if p.is_plasticene:
            lines.append(asp.fact("plasticene", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_props() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show defensive/1."))
    return sorted(p for (p,) in asp.atoms(model, "defensive"))


def asp_bad_ending() -> bool:
    import asp
    model = asp.one_model(asp_program(
        "\n".join([
            "entity(hero).",
            "meter(prop, broken, 1).",
            "meme(hero, misunderstanding, 1).",
        ]),
        "#show bad_ending/0.",
    ))
    return bool(asp.atoms(model, "bad_ending"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_props()) != set(PROPS):
        rc = 1
        print("MISMATCH: ASP defensive props differ from Python registry.")
    else:
        print("OK: ASP registry matches Python props.")
    if not asp_bad_ending():
        rc = 1
        print("MISMATCH: ASP bad ending inference failed.")
    else:
        print("OK: ASP can infer the bad ending.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world: defensive tag, plasticene, flashback, misunderstanding, bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--defender", choices=DEFENDER_NAMES)
    ap.add_argument("--prop", choices=PROPS)
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
    if args.prop and args.prop not in PROPS:
        raise StoryError("(Unknown prop.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hero is None or c[1] == args.hero)
              and (args.sidekick is None or c[2] == args.sidekick)
              and (args.prop is None or c[3] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hero, sidekick, prop = rng.choice(sorted(combos))
    defender = args.defender or rng.choice(DEFENDER_NAMES)
    return StoryParams(setting, hero, sidekick, defender, prop)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    prop = PROPS[params.prop]
    world = tell(setting, prop, params.hero, params.sidekick, params.defender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def valid_story_text(sample: StorySample) -> bool:
    return bool(sample.story and "{" not in sample.story and "}" not in sample.story)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show defensive/1.\n#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show defensive/1."))
        props = sorted(p for (p,) in asp.atoms(model, "defensive"))
        print("defensive props:", ", ".join(props))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            if not valid_story_text(sample) or sample.story in seen:
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
            header = f"### {p.hero} and {p.sidekick}: {p.prop} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
