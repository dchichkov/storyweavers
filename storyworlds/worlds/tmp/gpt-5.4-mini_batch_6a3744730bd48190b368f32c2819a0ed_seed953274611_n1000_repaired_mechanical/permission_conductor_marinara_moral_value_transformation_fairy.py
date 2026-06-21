#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/permission_conductor_marinara_moral_value_transformation_fairy.py
==================================================================================================

A small fairy-tale storyworld about a child who wants permission to borrow a
conductor's silver baton so they can stir a pot of marinara, learns a moral
value lesson about honesty and respect, and is transformed from sneaking to
asking kindly.

The domain is intentionally tiny and classical: a child, a conductor, a kitchen
task, a moment of temptation, a consequence-driven turn, and a gentle ending
image proving what changed. The story keeps the required seed words:
"permission", "conductor", and "marinara".
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "conductor"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    conductor: str
    conductor_gender: str
    sauce: str
    vessel: str
    lesson: str
    transformation: str
    setting: str = "the old kitchen"
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


@dataclass
class Theme:
    id: str
    opening: str
    task: str
    dream: str
    ending_image: str
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
class Sauce:
    id: str
    label: str
    phrase: str
    smell: str
    spill: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    fragile: bool = True
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
class Lesson:
    id: str
    value: str
    sentence: str
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
class Transformation:
    id: str
    from_state: str
    to_state: str
    line: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    vessel = world.entities.get("vessel")
    sauce = world.entities.get("sauce")
    if not hero or not vessel or not sauce:
        return out
    if hero.meters["sneaking"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vessel.meters["smeared"] += 1
    sauce.meters["spilled"] += 1
    hero.memes["guilt"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def tell(theme: Theme, sauce: Sauce, vessel: Vessel, lesson: Lesson,
         trans: Transformation, hero_name: str, hero_gender: str,
         conductor_name: str, conductor_gender: str, setting: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender,
                            label=hero_name, role="child"))
    conductor = world.add(Entity(id="conductor", kind="character", type=conductor_gender,
                                 label=conductor_name, role="conductor"))
    bowl = world.add(Entity(id="vessel", type="thing", label=vessel.label, attrs={"fragile": vessel.fragile}))
    pot = world.add(Entity(id="sauce", type="thing", label=sauce.label))
    world.facts.update(theme=theme, sauce=sauce, vessel=vessel, lesson=lesson,
                       trans=trans, setting=setting, hero=hero, conductor=conductor)
    hero.memes["longing"] += 1
    conductor.memes["patience"] += 1

    world.say(f"Once in {setting}, {hero.label} longed to help the {conductor.label_word}.")
    world.say(f"{theme.opening} {hero.label} hoped to stir the {sauce.phrase} with a shiny spoon, but then {hero.label} saw the {vessel.phrase} and had a far bolder idea.")
    world.say(f'"May I have permission to borrow your baton?" {hero.label} asked, looking up at the {conductor.label_word}.')
    world.say(f'The {conductor.label_word} smiled and said the {lesson.sentence}')

    world.para()
    hero.meters["sneaking"] += 1
    hero.memes["defiance"] += 1
    world.say(f"But the wish to be clever tugged harder. {hero.label} tiptoed closer and lifted the baton anyway.")
    propagate(world, narrate=False)
    world.say(f"The baton touched the {sauce.label}, and the {sauce.spill} smell rose at once. A bright ribbon of {sauce.label} marked the {vessel.label}.")
    world.say(f'The {conductor.label_word} turned at once and said, "{theme.dream}"')
    world.say(f"{hero.label} felt the sting of shame, because taking without permission had made a sweet task go wrong.")

    world.para()
    hero.meters["sneaking"] = 0
    hero.memes["guilt"] += 1
    hero.memes["humility"] += 1
    hero.memes["wisdom"] += 1
    world.say(f"Then {hero.label} lowered the baton and whispered, 'I am sorry. I should have asked.'")
    world.say(f"The {conductor.label_word} wiped the spill, forgave {hero.pronoun('object')}, and showed {hero.pronoun('object')} how to help by stirring slowly with a wooden spoon instead.")
    world.say(f"That was the moral value of the day: {lesson.value}. {trans.line}")

    world.para()
    hero.memes["joy"] += 1
    world.say(f"By evening, the {sauce.label} bubbled safely again, and {hero.label} stirred it the proper way.")
    world.say(f"{theme.ending_image} {hero.label} worked beside the {conductor.label_word}, calm and changed, with honest hands and a kinder heart.")

    world.facts.update(outcome="transformed", sweet=True)
    return world


THEMES = {
    "fairy": Theme(
        id="fairy",
        opening="A tiny lantern blinked above the stove like a star in a jar.",
        task="help",
        dream="You may help when you ask first.",
        ending_image="The lantern glowed warm as a blessing,",
    )
}

SAUCES = {
    "marinara": Sauce(
        id="marinara",
        label="marinara",
        phrase="marinara sauce",
        smell="tomato",
        spill="tomato",
        tags={"marinara", "sauce"},
    )
}

VESSELS = {
    "baton": Vessel(
        id="baton",
        label="silver baton",
        phrase="silver baton",
        fragile=True,
        tags={"conductor", "baton"},
    )
}

LESSONS = {
    "permission": Lesson(
        id="permission",
        value="ask before you use what belongs to someone else",
        sentence="permission keeps kind helpers from becoming angry and keeps little mistakes from growing big",
        tags={"permission", "moral_value"},
    )
}

TRANSFORMS = {
    "honesty": Transformation(
        id="honesty",
        from_state="sneaking",
        to_state="honest helping",
        line="The sneaky wish turned into honest helping, and the child became gentler for it.",
        tags={"transformation", "moral_value"},
    )
}

GIRL_NAMES = ["Mina", "Ivy", "Lila", "Nora", "Ruby"]
BOY_NAMES = ["Finn", "Owen", "Eli", "Theo", "Rowan"]
CONDUCTOR_NAMES = ["Maestro Bram", "Maestro Ivo", "Maestro Orrin", "Maestro Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for sauce in SAUCES:
            for vessel in VESSELS:
                combos.append((theme, sauce, vessel))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about permission, a conductor, marinara, moral value, and transformation.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--sauce", choices=SAUCES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--conductor")
    ap.add_argument("--conductor-gender", choices=["girl", "boy", "conductor"])
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
    if args.sauce and args.sauce != "marinara":
        raise StoryError("This tiny world only knows marinara sauce.")
    if args.vessel and args.vessel != "baton":
        raise StoryError("The conductor's baton is the only tempting object in this tale.")
    if args.hero_gender and args.hero and args.hero_gender not in {"girl", "boy"}:
        raise StoryError("Hero gender must be girl or boy.")
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    conductor_gender = args.conductor_gender or "conductor"
    conductor = args.conductor or rng.choice(CONDUCTOR_NAMES)
    return StoryParams(
        hero=hero,
        hero_gender=hero_gender,
        conductor=conductor,
        conductor_gender=conductor_gender,
        sauce="marinara",
        vessel="baton",
        lesson="permission",
        transformation="honesty",
    )


def generate(params: StoryParams) -> StorySample:
    if params.sauce not in SAUCES:
        raise StoryError("Unknown sauce.")
    if params.vessel not in VESSELS:
        raise StoryError("Unknown vessel.")
    if params.lesson not in LESSONS:
        raise StoryError("Unknown lesson.")
    if params.transformation not in TRANSFORMS:
        raise StoryError("Unknown transformation.")
    theme = THEMES["fairy"]
    world = tell(theme, SAUCES[params.sauce], VESSELS[params.vessel], LESSONS[params.lesson], TRANSFORMS[params.transformation], params.hero, params.hero_gender, params.conductor, params.conductor_gender, theme.id)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    conductor = f["conductor"]
    return [
        f'Write a fairy tale for a young child that includes the words "permission", "conductor", and "marinara".',
        f"Tell a short moral story where {hero.label} asks the {conductor.label_word} for permission, learns a lesson, and changes by the end.",
        f"Write a fairy tale about temptation, honesty, and transformation centered on marinara sauce and a conductor's baton.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    conductor = f["conductor"]
    lesson = f["lesson"]
    trans = f["trans"]
    return [
        ("Who is the story about?", f"It is about {hero.label} and the {conductor.label_word}. {hero.label} is the child who changes, and the conductor guides the lesson."),
        ("What did the child want to do?", f"{hero.label} wanted to borrow the conductor's baton to stir the marinara sauce. The desire was playful, but it was not respectful."),
        ("What lesson did the conductor teach?", f"The conductor taught that {lesson.value}. That was the moral value at the center of the tale."),
        ("How did the child change?", f"{trans.line} By the end, {hero.label} had become honest, careful, and kind."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is permission?", "Permission means a person says yes before something is borrowed or done. It helps keep everyone respectful and safe."),
        ("What is a conductor?", "A conductor is the person who guides musicians and helps keep a performance together. In fairy tales, a conductor can also be a wise helper."),
        ("What is marinara?", "Marinara is a tomato sauce that is often warm, red, and tasty. It can smell sweet and savory when it cooks."),
        ("What is a moral value?", "A moral value is a good rule for how to treat others, like honesty or kindness. Stories often teach moral values through what happens to the characters."),
        ("What is transformation?", "Transformation means something changes from one state into another. In stories, a character can transform by learning and behaving differently."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(x[0] if x else '' for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Mina", hero_gender="girl", conductor="Maestro Bram", conductor_gender="conductor", sauce="marinara", vessel="baton", lesson="permission", transformation="honesty"),
    StoryParams(hero="Finn", hero_gender="boy", conductor="Maestro Ivo", conductor_gender="conductor", sauce="marinara", vessel="baton", lesson="permission", transformation="honesty"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this tiny fairy world only supports the marinara-and-baton temptation, with permission and transformation as the lesson.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for s in SAUCES:
        lines.append(asp.fact("sauce", s))
    for v in VESSELS:
        lines.append(asp.fact("vessel", v))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    for tr in TRANSFORMS:
        lines.append(asp.fact("transformation", tr))
    lines.append(asp.fact("required_word", "permission"))
    lines.append(asp.fact("required_word", "conductor"))
    lines.append(asp.fact("required_word", "marinara"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,S,V) :- theme(T), sauce(S), vessel(V), S = marinara, V = baton.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print("OK: ASP and Python valid_combos match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as ex:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


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
        print(f"{len(combos)} valid combos:")
        for t, s, v in combos:
            print(f"  {t} {s} {v}")
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
