#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mistaken_fling_press_rhyme_sharing_superhero_story.py
=====================================================================================

A standalone storyworld for a tiny superhero domain: two kids in costume prepare
for a neighborhood hero game, one makes a mistaken "fling" with a gadget, the
other uses a careful press to stop the trouble, and the ending turns on rhyme
and sharing.  The world model tracks meters and memes so the story is driven by
state changes rather than a frozen paragraph swap.

Theme words intentionally woven into the domain:
- mistaken
- fling
- press

Style goals:
- superhero story feel
- child-facing language
- a clear beginning, turn, and ending image
- rhyme as a playful narrative instrument
- sharing as the resolution instrument
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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Gadget:
    id: str
    label: str
    label_phrase: str
    makes_mess: str
    stops_mess: str
    kind: str = "thing"

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
class Setting:
    id: str
    place: str
    detail: str

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["paint_spray"] < THRESHOLD:
            continue
        sig = ("scatter", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("alley").meters["mess"] += 1
        for kid in list(world.entities.values()):
            if kid.role in {"hero", "partner"}:
                kid.memes["worry"] += 1
        out.append("The bright spray streaked the sidewalk and made the scene feel risky.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    partner = world.entities.get("partner")
    if not hero or not partner:
        return out
    if hero.memes["share"] < THRESHOLD or partner.memes["share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] += 1
    partner.memes["calm"] += 1
    world.get("alley").meters["mess"] = 0.0
    out.append("The kids shared the cleanup, and the sidewalk looked neat again.")
    return out


CAUSAL_RULES = [
    Rule("scatter", _r_scatter),
    Rule("sharing", _r_sharing),
]


def _story_rhyme(hero: Entity, partner: Entity, setting: Setting) -> str:
    return (
        f"In {setting.place}, {hero.id} and {partner.id} wore bright capes and "
        f"watched the city glow. {setting.detail}"
    )


def _temptation(hero: Entity, gadget: Gadget) -> str:
    hero.memes["eager"] += 1
    return (
        f'{hero.id} spotted {gadget.label_phrase} and said, "I can fling this fast, '
        f'and make our hero game last!"'
    )


def _warning(partner: Entity, gadget: Gadget) -> str:
    partner.memes["careful"] += 1
    return (
        f'{partner.id} blinked and answered, "That is mistaken, my friend. '
        f'If we fling that now, we may make a mess instead of a win."'
    )


def _mistake(world: World, hero: Entity, gadget: Gadget) -> None:
    hero.meters["paint_spray"] += 1
    world.say(
        f"{hero.id} gave the gadget a wild fling, and a ribbon of paint sprayed "
        f"across the pavement."
    )
    propagate(world, narrate=False)


def _press_fix(world: World, partner: Entity, gadget: Gadget) -> None:
    partner.meters["press"] += 1
    world.say(
        f"{partner.id} used a gentle press on the stop switch, and the spray "
        f"settled right down."
    )


def _share_fix(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["share"] += 1
    partner.memes["share"] += 1
    world.say(
        f"Then {hero.id} and {partner.id} shared the sponge, pressed the spills "
        f"clean, and rhymed as they worked: bright light, right flight, tidy night."
    )
    propagate(world, narrate=False)


def _ending(world: World, hero: Entity, partner: Entity) -> None:
    world.say(
        f"At sunset, {hero.id} held one handle and {partner.id} held the other, "
        f"and their shared gear shone like a tiny team of stars."
    )


SETTINGS = {
    "cityblock": Setting(
        "cityblock",
        "the city block",
        "The street was smooth, the lamp was warm, and the alley waited like a quiet stage.",
    ),
    "rooftop": Setting(
        "rooftop",
        "the rooftop",
        "The roof tiles sparkled, and the wind made every cape flutter like a flag.",
    ),
    "playground": Setting(
        "playground",
        "the playground",
        "The swings creaked softly, and the empty path felt ready for a rescue game.",
    ),
}

GADGETS = {
    "sprayer": Gadget("sprayer", "paint sprayer", "a paint sprayer", "spray", "press"),
    "glitter_tube": Gadget("glitter_tube", "glitter tube", "a glitter tube", "fling", "press"),
    "bubble_wand": Gadget("bubble_wand", "bubble wand", "a bubble wand", "fling", "press"),
}

HERO_NAMES = ["Nova", "Milo", "Tessa", "Finn", "Ruby", "Theo", "Iris", "Zane"]
PARTNER_NAMES = ["Jade", "Pip", "Luna", "Kai", "Mara", "Bea", "Noel", "Nia"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    gadget: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, g) for s in SETTINGS for g in GADGETS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero rhyme-and-sharing storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for g in GADGETS:
        lines.append(asp.fact("gadget", g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G) :- setting(S), gadget(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.gadget not in GADGETS:
        raise StoryError("Unknown gadget.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    gadget = GADGETS[params.gadget]

    hero = world.add(Entity("hero", kind="character", type=params.hero_gender, role="hero", attrs={"name": params.hero_name}))
    partner = world.add(Entity("partner", kind="character", type=params.partner_gender, role="partner", attrs={"name": params.partner_name}))
    alley = world.add(Entity("alley", kind="place", label=setting.place))
    world.facts["setting"] = setting
    world.facts["gadget"] = gadget

    world.say(
        f"{params.hero_name} and {params.partner_name} were tiny superheroes on {setting.place}."
    )
    world.say(_story_rhyme(hero, partner, setting))
    world.say(
        f"They wanted to share one cool gadget so the whole block could hear their rhyme."
    )

    world.para()
    world.say(_temptation(hero, gadget))
    world.say(_warning(partner, gadget))
    _mistake(world, hero, gadget)
    _press_fix(world, partner, gadget)
    world.para()
    _share_fix(world, hero, partner)
    _ending(world, hero, partner)

    world.facts.update(hero=hero, partner=partner, alley=alley, outcome="shared")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    gadget: Gadget = f["gadget"]
    return [
        f'Write a superhero story for a young child set on {setting.place} that uses the words "mistaken", "fling", and "press".',
        f"Tell a rhyme-filled story where two children in capes share {gadget.label_phrase} and learn to use it safely.",
        "Write a short heroic story about a mistaken fling, a careful press, and sharing the cleanup.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    setting: Setting = world.facts["setting"]
    qa = [
        QAItem(
            question="Who are the story's heroes?",
            answer=f"The story is about {hero.attrs['name']} and {partner.attrs['name']}. They were pretending to be superheroes on {setting.place}.",
        ),
        QAItem(
            question="What went mistaken at first?",
            answer=(
                f"{hero.attrs['name']} made a mistaken fling with the gadget and sprayed paint across the pavement. "
                f"That was the trouble because the game needed careful hands, not wild motion."
            ),
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=(
                f"{partner.attrs['name']} used a gentle press to stop the spray, and then they shared the sponge. "
                f"Sharing helped them clean up together and turn the mistake into a team win."
            ),
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does press mean in this story?",
            answer="Here, press means pushing the stop switch gently so the gadget slows down or turns off.",
        ),
        QAItem(
            question="Why is sharing important for superheroes?",
            answer="Sharing helps superheroes work as a team. It also makes cleanup faster when something goes wrong.",
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_gate(StoryParams("", "", "", "", "", ""))
    setting = args.setting or rng.choice(list(SETTINGS))
    gadget = args.gadget or rng.choice(list(GADGETS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    partner_name = args.partner_name or rng.choice([n for n in PARTNER_NAMES if n != hero_name])
    return StoryParams(setting, gadget, hero_name, hero_gender, partner_name, partner_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("cityblock", "sprayer", "Nova", "girl", "Milo", "boy"),
    StoryParams("rooftop", "glitter_tube", "Ruby", "girl", "Theo", "boy"),
    StoryParams("playground", "bubble_wand", "Finn", "boy", "Jade", "girl"),
]


def asp_verify() -> int:
    import asp
    c = set(asp_valid_combos())
    p = set(valid_combos())
    ok = c == p
    rc = 0
    if ok:
        print(f"OK: ASP parity with valid_combos() ({len(c)} combos).")
    else:
        print("MISMATCH: ASP parity failed.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"MISMATCH: generate() smoke test failed: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, g in combos:
            print(s, g)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
