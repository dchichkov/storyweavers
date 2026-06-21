#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pimento_rattler_comet_moral_value_foreshadowing_space.py
=======================================================================================

A small Storyweavers world for a child-facing Space Adventure tale with:
- the seed words pimento, rattler, comet
- moral value as the lesson axis
- foreshadowing as the narrative instrument

Premise:
A tiny crew prepares a comet garden at a moon base. A rash choice risks the
mission, a subtle clue warns what is coming, and a moral turn turns selfishness
into care.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORAL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    detail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risky: bool = False
    foreshadow: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MoralChoice:
    id: str
    temptation: str
    wise: str
    moral: str
    lesson: str
    risk: int
    repair: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    object: str
    choice: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_alert(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["danger"] >= THRESHOLD and ("alert", e.id) not in world.fired:
            world.fired.add(("alert", e.id))
            world.get("base").meters["busy"] += 1
            out.append("__alert__")
    return out


def _r_moral(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if hero and hero.meters["helped"] >= THRESHOLD and ("moral", hero.id) not in world.fired:
        world.fired.add(("moral", hero.id))
        hero.memes["moral_value"] += 1
        out.append("__moral__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_alert, _r_moral):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "moon_base": Setting(
        id="moon_base",
        place="a little moon base",
        sky="the black sky",
        detail="The windows showed a silver comet trail above the dust.",
    ),
    "star_harbor": Setting(
        id="star_harbor",
        place="Star Harbor",
        sky="the deep night sky",
        detail="A bright comet kept blinking over the dock like a warning light.",
    ),
    "glass_dome": Setting(
        id="glass_dome",
        place="a glass dome on Mars",
        sky="the red sky",
        detail="Outside, a comet tail curled like a ribbon over the sand.",
    ),
}

OBJECTS = {
    "pimento": ObjectCfg(
        id="pimento",
        label="pimento pepper",
        phrase="a bowl of bright pimento pepper slices",
        risky=True,
        foreshadow="one pepper slice slipped toward the hatch, a tiny red clue",
        tags={"food", "red"},
    ),
    "satchel": ObjectCfg(
        id="satchel",
        label="snack satchel",
        phrase="a snack satchel",
        risky=False,
        foreshadow="the satchel felt too full to close, like it might spill later",
        tags={"bag"},
    ),
    "glowseed": ObjectCfg(
        id="glowseed",
        label="glowseed pouch",
        phrase="a glowseed pouch",
        risky=False,
        foreshadow="the glowseed pouch shimmered softly, but stayed sealed",
        tags={"bag", "light"},
    ),
}

CHOICES = {
    "share": MoralChoice(
        id="share",
        temptation="keep the pimento all for himself",
        wise="share the pimento with the crew",
        moral="sharing makes the whole crew stronger",
        lesson="small kindness can save a big trip",
        risk=1,
        repair=1,
        tags={"moral", "share"},
    ),
    "hide": MoralChoice(
        id="hide",
        temptation="hide the pimento in his pocket",
        wise="tell the truth about the missing snack",
        moral="truth is safer than secret greed",
        lesson="a hidden snack can still cause trouble",
        risk=2,
        repair=1,
        tags={"moral", "truth"},
    ),
    "rush": MoralChoice(
        id="rush",
        temptation="rush the comet mission and ignore the warning",
        wise="slow down and check the warning light",
        moral="care keeps everyone safe",
        lesson="the comet clue was there for a reason",
        risk=2,
        repair=2,
        tags={"moral", "care"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nova", "Iris", "Zoe", "Mina"]
BOY_NAMES = ["Kai", "Rex", "Jett", "Owen", "Theo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if not obj.risky:
                continue
            for cid in CHOICES:
                out.append((sid, oid, cid))
    return out


def explain_rejection(obj: ObjectCfg) -> str:
    if not obj.risky:
        return f"(No story: {obj.label} is too calm for the danger-and-choice arc.)"
    return "(No story: invalid combination.)"


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.choice not in CHOICES:
        raise StoryError(f"Unknown choice: {params.choice}")

    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    choice = CHOICES[params.choice]

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend, role="friend"))
    base = world.add(Entity(id="base", kind="character", type="thing", label=setting.place, role="base"))
    comet = world.add(Entity(id="comet", kind="thing", type="thing", label="comet", tags={"comet"}))
    snack = world.add(Entity(id="snack", kind="thing", type="thing", label=obj.label, tags=obj.tags))

    hero.memes["curiosity"] += 1
    friend.memes["care"] += 1
    base.meters["busy"] += 0
    comet.meters["bright"] += 1

    world.say(
        f"At {setting.place}, {hero.label} and {friend.label} prepared a tiny space snack cart. "
        f"{setting.detail}"
    )
    world.say(
        f'The comet was already there in the sky, and {obj.foreshadow}. '
        f'{hero.label} stared at it for a long moment.'
    )

    world.para()
    world.say(
        f'{hero.label} wanted to {choice.temptation}, but {friend.label} pointed at the comet trail. '
        f'"That glow looks like a warning," {friend.label} said.'
    )
    hero.memes["want"] += 1
    friend.memes["foreshadow"] += 1

    if params.choice == "rush":
        world.para()
        world.say(
            f"{hero.label} almost rushed ahead anyway. The hatch light blinked once, then twice, "
            f"like it knew something was coming."
        )
        snack.meters["danger"] += choice.risk
        propagate(world, narrate=False)
        world.say(
            f"The warning was right: a loose pimento slice slid into the control tray and made the mission messy."
        )
        world.say(
            f'{friend.label} steadied the tray and said, "Slow is kind when the ship is crowded."'
        )
        hero.memes["moral_value"] += 1
        hero.meters["helped"] += 1
        world.para()
        world.say(
            f'Then {hero.label} fixed the tray, shared the snack, and the crew watched the comet pass by '
            f'without any more trouble.'
        )
    else:
        world.para()
        world.say(
            f'{hero.label} listened. Instead of keeping the pimento secret, {hero.label} chose {choice.wise}. '
            f'The crew laughed, and the snack cart stayed neat.'
        )
        hero.meters["helped"] += 1
        propagate(world, narrate=False)
        world.say(
            f"That choice made the whole base feel warmer, even under the cold moon sky."
        )
        world.para()
        world.say(
            f'When the comet brightened overhead, everyone shared the pimento and watched the sky together.'
        )

    world.facts.update(
        setting=setting,
        hero=hero,
        friend=friend,
        base=base,
        comet=comet,
        object_cfg=obj,
        choice_cfg=choice,
        outcome="moral",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Space Adventure story for a young child that includes the words "pimento", "rattler", and "comet".',
        f"Tell a gentle moon-base story where {f['hero'].label} learns that {f['choice_cfg'].moral}.",
        f'Write a story with foreshadowing: the comet should hint that a choice will matter later, and the ending should prove the lesson.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    choice = f["choice_cfg"]
    obj = f["object_cfg"]
    return [
        ("Who is the story about?",
         f"It is about {hero.label} and {friend.label} at a moon base, where a comet and a snack helped set up the adventure."),
        ("What clue appeared before the problem?",
         f"The comet trail and the loose pimento slice both hinted that something needed attention later. That foreshadowing made the warning feel earned instead of sudden."),
        ("What did {0} learn?".format(hero.label),
         f"{hero.label} learned that {choice.moral}. By the end, {choice.lesson} and the crew could enjoy the night together."),
        ("Why was the pimento important?",
         f"The pimento was the risky snack in the story, so it helped create the problem and the fix. Sharing it turned a selfish moment into a kinder one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a comet?",
         "A comet is an icy space object that can leave a bright tail when it flies near the Sun."),
        ("What does a pimento look like?",
         "A pimento is a small red pepper. It can be sweet or gently tangy, and it is often used in food."),
        ("What is a rattler?",
         "A rattler is something that rattles, like a toy or a little machine with parts that make a shaking sound."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.risky:
            lines.append(asp.fact("risky", oid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,C) :- setting(S), object(O), choice(C), risky(O).
foreshadow(O) :- object(O), risky(O).
moral(C) :- choice(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        ok = False
        print("MISMATCH: ASP and Python disagree on valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world with pimento, rattler, and comet.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--choice", choices=CHOICES)
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
    if args.object and args.object not in OBJECTS:
        raise StoryError(f"Unknown object: {args.object}")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, choice = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero])
    return StoryParams(setting=setting, hero=hero, hero_gender=hero_gender,
                       friend=friend, friend_gender=friend_gender,
                       object=obj, choice=choice)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.choice not in CHOICES:
        raise StoryError(f"Unknown choice: {params.choice}")
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, o, c in asp_valid_combos():
            print(f"  {s:12} {o:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(setting=s, hero="Luna", hero_gender="girl",
                                        friend="Kai", friend_gender="boy",
                                        object=o, choice=c))
                   for s, o, c in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
