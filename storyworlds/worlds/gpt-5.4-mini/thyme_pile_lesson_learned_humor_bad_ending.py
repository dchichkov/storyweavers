#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thyme_pile_lesson_learned_humor_bad_ending.py
==============================================================================

A small mythic storyworld about a child, a sacred pile of thyme, a joke that
turns sharp, and a lesson learned too late. The stories are built from a tiny
state machine rather than from fixed prose: the characters, the pile, the omen,
and the ending all change with the simulated world state.

Seed words: thyme, pile
Features: Lesson Learned, Humor, Bad Ending
Style: Myth
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)



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
class Pile:
    id: str
    label: str
    sacred: bool = True
    fragrant: bool = True

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
class Trick:
    id: str
    joke: str
    effect: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    pile: str
    trick: str
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


SETTINGS = {
    "hill": Setting("hill", "the wind-bent hill", "the crows went silent"),
    "grove": Setting("grove", "the mossy grove", "the leaves held still"),
    "hearth": Setting("hearth", "the old hearth court", "the ash turned cold"),
}

PILES = {
    "thyme": Pile("thyme", "thyme pile"),
}

TRICKS = {
    "goat": Trick("goat", "the goat looked offended and sneezed", "a careless laugh"),
    "echo": Trick("echo", "their own laugh came back smaller and sadder", "mocking the holy quiet"),
    "crow": Trick("crow", "a crow croaked as if it knew the joke was unwise", "a foolish tease"),
}

GIRL_NAMES = ["Mira", "Asha", "Lyra", "Nina", "Iris"]
BOY_NAMES = ["Orin", "Bram", "Koa", "Tarin", "Leif"]
ELDER_NAMES = ["Grandmother Nera", "Grandfather Sol", "Aunt Rhea", "Uncle Dain"]


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    pile = world.get("pile")
    if child.memes["mockery"] < THRESHOLD or pile.meters["order"] < THRESHOLD:
        return out
    sig = ("scatter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pile.meters["order"] = 0.0
    pile.meters["ruined"] += 1
    child.memes["regret"] += 1
    world.get("elder").memes["grief"] += 1
    out.append("__scatter__")
    return out


def _r_omen(world: World) -> list[str]:
    out: list[str] = []
    pile = world.get("pile")
    if pile.meters["ruined"] < THRESHOLD:
        return out
    sig = ("omen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("setting").memes["sorrow"] += 1
    world.get("hero").memes["fear"] += 1
    out.append("__omen__")
    return out


RULES = [Rule("scatter", _r_scatter), Rule("omen", _r_omen)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_trick(world: World, hero: Entity, trick: Trick, narrate: bool = True) -> None:
    hero.memes["humor"] += 1
    hero.memes["mockery"] += 1
    world.get("pile").meters["order"] -= 1
    world.say(f"{hero.id} laughed at {trick.effect}, and the joke rang across {world.setting.place}.")
    world.say(f"{trick.joke.capitalize()}.")
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, {hero.id} and {elder.id} kept a sacred {world.get('pile').label} near the stone ring."
    )
    world.say(
        f"The {world.get('pile').label} smelled of summer and healing, and the people said it should be left in peace."
    )


def want_fun(world: World, hero: Entity, trick: Trick) -> None:
    world.say(
        f"But {hero.id} wanted a little fun and pointed at the herbs. \"Look,\" {hero.pronoun()} said, \"even the {trick.id} would smile at this {world.get('pile').label}.\""
    )


def warn(world: World, elder: Entity, hero: Entity) -> None:
    world.get("elder").memes["warning"] += 1
    world.say(
        f"{elder.id} frowned. \"Do not tease what feeds the sick,\" {elder.pronoun()} said. \"A holy pile is not a toy for bright mouths.\""
    )


def defy(world: World, hero: Entity, trick: Trick) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"\"Only one joke,\" {hero.id} said, and reached for the {world.get('pile').label}."
    )
    _do_trick(world, hero, trick)


def bad_end(world: World, hero: Entity, elder: Entity) -> None:
    pile = world.get("pile")
    world.say(
        f"The wind came at once. It lifted the last thyme from the stones and blew it into the ditch."
    )
    world.say(
        f"By dusk, the {pile.label} was gone, the crows had returned, and no one could find enough leaves to mend the winter coughs."
    )
    world.say(
        f"{elder.id} gathered the child close and said, \"Now you know: laughter that tramples a blessing is paid back with grief.\""
    )
    world.say(
        f"{hero.id} nodded through tears, but the hill kept its silence, and the village learned its lesson after the loss, not before it."
    )


def tell(setting: Setting, pile: Pile, trick: Trick, hero_name: str, hero_gender: str,
         elder_name: str, elder_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", kind="character", type=hero_gender, role="child"))
    elder = world.add(Entity("elder", kind="character", type=elder_gender, role="elder"))
    world.add(Entity("setting", kind="thing", type="setting", label=setting.place))
    world.add(Entity("pile", kind="thing", type="pile", label=pile.label))
    hero.id = hero_name
    elder.id = elder_name
    world.get("pile").meters["order"] = 1.0
    setup(world, hero, elder)
    world.para()
    want_fun(world, hero, trick)
    warn(world, elder, hero)
    defy(world, hero, trick)
    world.para()
    bad_end(world, hero, elder)
    hero.memes["lesson"] += 1
    elder.memes["lesson"] += 1
    world.facts.update(hero=hero, elder=elder, pile=pile, trick=trick, setting=setting)
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TRICKS]


KNOWLEDGE = {
    "thyme": [(
        "What is thyme?",
        "Thyme is a small, fragrant herb used in cooking and healing. In old tales, people treat it with care because it is part of a blessing and a remedy."
    )],
    "pile": [(
        "What is a pile?",
        "A pile is a heap of things stacked or gathered together. A pile can be tidy and useful, or it can be scattered by wind or careless hands."
    )],
    "lesson": [(
        "What does it mean to learn a lesson?",
        "It means you understand what went wrong and remember how to do better next time. A lesson helps the same mistake hurt less in the future."
    )],
    "humor": [(
        "What is humor?",
        "Humor is something funny that makes people laugh. In stories, humor can lighten a moment, but it can also be unkind if it turns into mockery."
    )],
    "myth": [(
        "What is a myth?",
        "A myth is an old story that uses wonder, gods, spirits, or sacred places to explain why people should live wisely. Myths often teach a lesson through strange or magical events."
    )],
    "wind": [(
        "Why can wind change a scene quickly?",
        "Wind can carry light things away in a moment. In a story, that makes the world feel alive and a little dangerous."
    )],
}


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    pile: str
    trick: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: thyme, a sacred pile, humor, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pile", choices=PILES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "grandmother", "grandfather"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.pile and (args.pile not in PILES):
        raise StoryError("(No story: that pile is not part of this myth.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    pile = args.pile or "thyme"
    trick = args.trick or rng.choice(sorted(TRICKS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["grandmother", "grandfather", "woman", "man"])
    hero = args.hero or _pick_name(rng, hero_gender)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting, hero, hero_gender, elder, elder_gender, pile, trick)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a mythic story for a child that includes the words thyme and pile, and ends in a bad lesson learned too late.",
        f"Tell an old-style tale where {f['hero'].id} laughs at a sacred thyme pile and the joke goes wrong.",
        f"Write a short myth with humor, a warning from an elder, and a bad ending about {f['pile'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, elder, pile, trick = f["hero"], f["elder"], f["pile"], f["trick"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id} and {elder.id}, who guarded a sacred {pile.label} in a mythic place."),
        ("What did the child do that caused trouble?", f"{hero.id} laughed and mocked the holy quiet around the {pile.label}. That act turned a small joke into a harmful choice."),
        ("What warning did the elder give?", f"{elder.id} warned that the herbs fed the sick and should not be teased. The warning mattered because the pile was sacred and easy to lose."),
        ("How did the story end?", f"It ended badly: the wind scattered the thyme, the village lost the pile, and the lesson came only after the damage was done."),
    ]
    qa.append(("What was funny in the story?", f"The story had a brief joke when {trick.joke}. The humor made the moment feel playful, but it also showed how quickly play became disrespect."))
    qa.append(("What lesson was learned?", f"The lesson was that a blessing should be treated with care, not laughter that tramples it. {hero.id} learned that too late, after the loss had already happened."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"thyme", "pile", "lesson", "humor", "myth"}
    out: list[tuple[str, str]] = []
    for tag in ["thyme", "pile", "lesson", "humor", "myth", "wind"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill", "Mira", "girl", "Grandmother Nera", "grandmother", "thyme", "goat"),
    StoryParams("grove", "Orin", "boy", "Grandfather Sol", "grandfather", "thyme", "echo"),
    StoryParams("hearth", "Asha", "girl", "Aunt Rhea", "woman", "thyme", "crow"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PILES:
        lines.append(asp.fact("pile", pid))
        lines.append(asp.fact("sacred", pid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    return "\n".join(lines)


ASP_RULES = r"""
violates(H) :- hero(H).
lesson_learned :- violates(_).
bad_ending :- lesson_learned.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("hero(mira).", "#show bad_ending/0."))
    atoms = asp.atoms(model, "bad_ending")
    ok = bool(atoms) and valid_combos() == sorted(set(asp.atoms(asp.one_model(asp_program("#show setting/1.") ), "setting"))) is not False
    print("OK: ASP twin is present and reachable." if ok else "MISMATCH: ASP twin failed.")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PILES[params.pile],
        TRICKS[params.trick],
        params.hero,
        params.hero_gender,
        params.elder,
        params.elder_gender,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show pile/1.\n#show trick/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Mythic setting/pile/trick facts are available via ASP, but this world keeps one central bad-lesson pattern.")
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
