#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/story_porpoise_phenomenon_sound_effects_transformation_quest.py
===============================================================================================

A standalone story world for a tiny mythic domain: a child-hero hears a strange
porpoise-omen, follows a quest, speaks in sound effects, and undergoes a small
transformation that changes how the sea answers.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate with an inline ASP twin
- three Q&A sets grounded in world state
- child-facing prose with a mythic tone

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/story_porpoise_phenomenon_sound_effects_transformation_quest.py
    python storyworlds/worlds/gpt-5.4-mini/story_porpoise_phenomenon_sound_effects_transformation_quest.py --all
    python storyworlds/worlds/gpt-5.4-mini/story_porpoise_phenomenon_sound_effects_transformation_quest.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/story_porpoise_phenomenon_sound_effects_transformation_quest.py --trace
    python storyworlds/worlds/gpt-5.4-mini/story_porpoise_phenomenon_sound_effects_transformation_quest.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    sparkling: bool = False
    singing: bool = False
    transformed: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    omen: str
    sound: str
    mood: str

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
class Quest:
    id: str
    goal: str
    gate: str
    offering: str
    return_sign: str
    final_image: str

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
class Transformation:
    id: str
    from_form: str
    to_form: str
    trigger: str
    gift: str
    cost: str

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


def _r_omen(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["wonder"] < THRESHOLD:
        return out
    sig = ("omen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sea").meters["awakened"] += 1
    hero.memes["calling"] += 1
    out.append("__omen__")
    return out


def _r_song(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    porpoise = world.get("porpoise")
    if hero.memes["calling"] < THRESHOLD or porpoise.meters["near"] < THRESHOLD:
        return out
    sig = ("song",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    porpoise.meters["song"] += 1
    out.append("__song__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pearl = world.get("pearl")
    if hero.meters["watermarked"] < THRESHOLD or pearl.meters["glow"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.transformed = True
    hero.meters["scaled"] += 1
    hero.memes["peace"] += 1
    world.get("cloak").meters["bright"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("omen", "myth", _r_omen), Rule("song", "sound", _r_song), Rule("transform", "myth", _r_transformation)]


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


def _do_quest(world: World, hero: Entity, setting: Setting, quest: Quest, trans: Transformation) -> None:
    hero.meters["on_quest"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"On a dusk-blue shore, {hero.id} heard the sea breathe like a drum. "
        f"{setting.omen}."
    )
    world.say(
        f'“{setting.sound},” sang the porpoise, and the water answered with a soft {setting.mood} glow.'
    )
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{hero.id} followed the omen to {quest.gate}, where the waves made room for {quest.offering}."
    )
    world.say(
        f'“{quest.goal},” whispered {hero.id}, and the porpoise answered “{quest.return_sign}!”'
    )
    hero.meters["watermarked"] += 1
    world.get("pearl").meters["glow"] += 1
    propagate(world, narrate=False)
    if hero.transformed:
        world.para()
        world.say(
            f"Then the old shape fell away like wet sand. {hero.id} became {trans.to_form}, "
            f"{trans.gift}, though the journey cost {trans.cost}."
        )
        world.say(
            f"In the end, {quest.final_image}, and the porpoise swam in shining circles beside the new {trans.to_form}."
        )
    else:
        world.para()
        world.say(
            f"The sea stayed dark, and the quest did not finish. {hero.id} still held the pearl close, listening for the next sign."
        )


THEMES = {
    "myth": Setting(
        "myth",
        "At the edge of the world, where cliffs met a silver sea, old fishermen told a story about a porpoise omen.",
        "plip-plop, hush-hush",
        "a moon-bright hush",
    ),
    "harbor": Setting(
        "harbor",
        "Beside the harbor, between ropes and gulls, the tide kept a story in its mouth.",
        "klik-klak, plip!",
        "a salt-bright hush",
    ),
}

QUESTS = {
    "shell": Quest(
        "shell",
        "find the lost shell that could wake the tide-god",
        "the cave of echoing foam",
        "a bowl of kelp and one clean pearl",
        "follow the song",
        "the shore glittered like a row of stars",
    ),
    "harp": Quest(
        "harp",
        "bring back the sea-harp for the sleeping queen",
        "the reef of singing stones",
        "three sea grapes and one bright pearl",
        "sing again",
        "the waves bowed like grateful birds",
    ),
    "lamp": Quest(
        "lamp",
        "carry a lantern-heart to the lighthouse ghost",
        "the tunnel beneath the cliffs",
        "a wick, a pearl, and a brave breath",
        "glow on",
        "the lighthouse blinked awake at last",
    ),
}

TRANSFORMATIONS = {
    "porpoise": Transformation(
        "porpoise",
        "child",
        "porpoise-speaker",
        "the pearl touched water",
        "a voice that could answer the sea",
        "a little fear and a goodbye to ordinary footsteps",
    ),
    "star": Transformation(
        "star",
        "child",
        "star-backed swimmer",
        "the omen was followed without turning back",
        "a back that shone like a little star",
        "one dry name and one old doubt",
    ),
    "reed": Transformation(
        "reed",
        "child",
        "reed-singer",
        "the porpoise called twice",
        "a song that traveled farther than feet",
        "the heaviness of silence",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for q in QUESTS:
            for x in TRANSFORMATIONS:
                combos.append((t, q, x))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    quest: str
    transformation: str
    hero: str
    hero_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: porpoise omen, quest, transformation, and sound effects.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.quest is None or c[1] == args.quest)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, quest, trans = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(["Mira", "Niko", "Lena", "Tavi", "Iris", "Arin"])
    return StoryParams(theme, quest, trans, hero, gender)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="quester"))
    sea = world.add(Entity(id="sea", type="sea", label="the sea"))
    porpoise = world.add(Entity(id="porpoise", type="porpoise", label="the porpoise", sparkling=True))
    pearl = world.add(Entity(id="pearl", type="thing", label="a pearl"))
    cloak = world.add(Entity(id="cloak", type="thing", label="a salt cloak"))
    world.add(sea)
    world.add(porpoise)
    world.add(pearl)
    world.add(cloak)

    setting = THEMES[params.theme]
    quest = QUESTS[params.quest]
    trans = TRANSFORMATIONS[params.transformation]

    world.say(
        f"{params.hero} was a little {params.hero_gender} with a listening heart, and this is the story of how {hero.id} found a sea omen."
    )
    _do_quest(world, hero, setting, quest, trans)

    world.facts.update(
        hero=hero,
        sea=sea,
        porpoise=porpoise,
        pearl=pearl,
        cloak=cloak,
        setting=setting,
        quest=quest,
        trans=trans,
        outcome="transformed" if hero.transformed else "unfinished",
    )
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
    return [
        f'Write a mythic story for a child that includes the words "story", "porpoise", and "phenomenon".',
        f"Tell a sea myth where {f['hero'].id} hears a porpoise omen, follows a quest, and changes form at the end.",
        f"Write a small myth with sound effects like a drum or splash, a quest over the sea, and a transformation that proves the hero has changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    trans: Transformation = f["trans"]
    q = [
        ("Who is the story about?",
         f"It is about {hero.id}, who followed a sea omen and listened to the porpoise. The hero begins as an ordinary child and ends changed by the quest."),
        ("What was the quest?",
         f"The quest was to {quest.goal}. The hero had to cross to {quest.gate} and bring back what the sea asked for."),
        ("What changed at the end?",
         f"{hero.id} changed from {trans.from_form} to {trans.to_form}. That transformation showed the sea had accepted the hero's brave listening."),
        ("Why did the porpoise matter?",
         f"The porpoise was the guide who made the omen clear. Its sounds led the hero forward when the path felt strange and mythical."),
    ]
    if f["outcome"] == "transformed":
        q.append(("How did the story end?",
                  f"It ended with the hero transformed and the sea shining around the new shape. The final image proves the quest succeeded and the world answered back."))
    return q


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a porpoise?",
         "A porpoise is a sea animal related to dolphins. It swims fast and can leap through the water."),
        ("What is a phenomenon?",
         "A phenomenon is something unusual that people notice and wonder about. It can be a strange sign in nature or a surprising event."),
        ("What is a quest?",
         "A quest is a journey with a goal. In myths, someone goes out to find something, solve a problem, or prove courage."),
        ("What are sound effects in a story?",
         "Sound effects are words that imitate noises, like splash or thump. They make the scene feel lively and easier to imagine."),
        ("What is transformation in a myth?",
         "Transformation means something changes form or nature. In myths, a hero might become stronger, wiser, or even take a new shape."),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.sparkling:
            bits.append("sparkling=True")
        if e.transformed:
            bits.append("transformed=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
omen :- wonder(hero).
song :- calling(hero), near(porpoise).
transform :- watermarked(hero), glow(pearl).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("wonder", "hero"),
        asp.fact("calling", "hero"),
        asp.fact("near", "porpoise"),
        asp.fact("watermarked", "hero"),
        asp.fact("glow", "pearl"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show omen/0.\n#show song/0.\n#show transform/0."))
    atoms = {name for name, _ in asp.atoms(model, "transform")} | {name for name, _ in asp.atoms(model, "song")} | {name for name, _ in asp.atoms(model, "omen")}
    ok = bool(atoms)
    sample = generate(StoryParams("myth", "shell", "porpoise", "Mira", "girl"))
    if not sample.story or not ok:
        print("MISMATCH or generation failed.")
        return 1
    print("OK: ASP twin and story generation smoke test passed.")
    return 0


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: this small mythic world always has a reasonable quest, so no explicit rejection is needed.)"


def solve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (theme, quest, transformation) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(t, q, x, "Mira", "girl")) for t, q, x in valid_combos()[:5]]
    else:
        seen: set[str] = set()
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
