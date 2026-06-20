#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/octopi_guacamole_curiosity_surprise_teamwork_rhyming_story.py
============================================================================================

A small standalone story world for a rhyming, child-facing tale about curious
octopi, a surprise, and teamwork around guacamole.

The seed idea:
- Octopi discover a bowl of guacamole.
- Curiosity makes them peek, Surprise makes the scene change, and Teamwork
  helps them solve a little messy problem.
- The ending should feel complete and upbeat, with a tiny rhyme-like cadence.

This script is self-contained and follows the Storyweavers storyworld contract.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"octopus", "octopi"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    place: str
    water: str
    mood: str

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
class Creature:
    id: str
    label: str
    plural: bool = False
    curious: str = ""
    surprise: str = ""
    teamwork: str = ""

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
class Item:
    id: str
    label: str
    tasty: str
    spillable: bool = True

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
class Action:
    id: str
    verb: str
    splash: str
    method: str
    reward: str
    mess: str
    risk: int

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def prop_use(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["curiosity"] >= THRESHOLD and e.meters["smeared"] < THRESHOLD:
            sig = ("use", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["smeared"] += 1
            out.append("__splash__")
    return out


def prop_help(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork") and not world.facts.get("helped"):
        world.facts["helped"] = True
        out.append("__help__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    made: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (prop_use, prop_help):
            res = rule(world)
            if res:
                changed = True
                made.extend([x for x in res if not x.startswith("__")])
    if narrate:
        for s in made:
            world.say(s)
    return made


def tell(setting: Setting, creature: Creature, item: Item, action: Action,
         name_a: str = "Mira", name_b: str = "Nico") -> World:
    world = World(setting)
    octo_a = world.add(Entity(id=name_a, kind="character", type="octopus", label=name_a, role="curious"))
    octo_b = world.add(Entity(id=name_b, kind="character", type="octopus", label=name_b, role="helper"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label=item.label))
    spoon = world.add(Entity(id="spoon", kind="thing", type="spoon", label="a little spoon"))
    world.facts.update(item=item, action=action, creature=creature, bowl=bowl, spoon=spoon)

    octo_a.memes["curiosity"] = 1.0
    octo_b.memes["surprise"] = 1.0
    octo_b.memes["teamwork"] = 1.0

    world.say(
        f"In the bright blue sea where the seaweed swayed, {octo_a.id} and {octo_b.id} "
        f"met a bowl of {item.label}. It smelled so green, so smooth, so sweet."
    )
    world.say(
        f'"What is it?" said {octo_a.id} with a grin. '
        f'"Let us peek, let us see, let us taste what it might be!"'
    )

    world.para()
    world.say(
        f"{octo_b.id} blinked in {setting.mood} surprise, then pointed with a tentacle tip. "
        f'"It is {item.tasty}, and it sits by the tide. Still, be kind, and be tidy."'
    )
    world.say(
        f'They {action.verb} with care near the shore, '
        f'and the little bowl wobbled more and more.'
    )

    world.para()
    world.facts["teamwork"] = True
    if action.risk:
        octo_a.memes["curiosity"] += 1
        octo_b.memes["teamwork"] += 1
        world.say(
            f"Then, oh my, the bowl tipped by a bit; green guacamole dripped in a sunny split. "
            f"{octo_a.id} gasped, but did not flee. {octo_b.id} said, 'Teamwork! One, two, three!'"
        )
        propagate(world, narrate=False)
        bowl.meters["spilled"] += 1
        world.say(
            f"They steadied the bowl, and with a quick soft scoop, "
            f"they gathered the guacamole back into the loop."
        )
    else:
        world.say(
            f"The bowl stayed still, and the tide went hush; no mess, no rush, no splashy slush. "
            f"They shared a smile and a careful nibble, a tidy treat in a tentacled dribble."
        )

    world.para()
    world.say(
        f"At sunset they waved their arms and sang, 'Curious hearts can learn and play; "
        f"with teamwork, too, we save the day!'"
    )
    world.say(
        f"And the sea grew calm, the moon hung high, while two octopi drifted by -- "
        f"happy, helpful, guacamole-close, and bright as the sky."
    )

    world.facts.update(
        outcome="spilled" if action.risk else "tidy",
        curiosity=True,
        surprise=True,
        teamwork=True,
        octopi=(octo_a, octo_b),
    )
    return world


SETTINGS = {
    "tidepool": Setting("a tidepool", "sea foam", "wonderful"),
    "reef": Setting("a reef", "sunlight", "sparkly"),
    "harbor": Setting("a harbor", "harbor water", "glittery"),
}

CREATURES = {
    "octopi": Creature("octopi", "octopi", plural=True, curious="curious", surprise="surprised", teamwork="helpful"),
}

ITEMS = {
    "guacamole": Item("guacamole", "guacamole", "guacamole"),
}

ACTIONS = {
    "peek": Action("peek", "peered", "a tiny splash", "peeked closer", "shared a taste", "smeared", 1),
    "balance": Action("balance", "balanced", "a wobble", "balanced the bowl", "shared a snack", "smeared", 1),
    "carry": Action("carry", "carried", "a tilt", "carried it together", "shared a meal", "smeared", 0),
}

NAMES_A = ["Mira", "Tula", "Poppy", "Luna", "Coco", "Nori"]
NAMES_B = ["Nico", "Bobo", "Sage", "Kiki", "Milo", "Rafi"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    creature: str
    item: str
    action: str
    name_a: str
    name_b: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CREATURES:
            for i in ITEMS:
                for a in ACTIONS:
                    combos.append((s, c, i, a))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: octopi, guacamole, curiosity, surprise, teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    creature = args.creature or "octopi"
    item = args.item or "guacamole"
    action = args.action or rng.choice(sorted(ACTIONS))
    return StoryParams(
        setting=setting,
        creature=creature,
        item=item,
        action=action,
        name_a=args.name_a or rng.choice(NAMES_A),
        name_b=args.name_b or rng.choice(NAMES_B),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a rhyming story about octopi and guacamole where curiosity leads to a surprise and teamwork fixes the mess.",
        f"Tell a child-friendly rhyme set at {world.setting.place} with {world.facts['item'].label}, keeping the words octopi and guacamole in the story.",
        "Make the ending cheerful, musical, and full of teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    item = world.facts["item"].label
    a, b = world.facts["octopi"]
    return [
        QAItem(
            question="What did the octopi find?",
            answer=f"They found a bowl of {item}. It was the surprise that made them stop and look closer."
        ),
        QAItem(
            question="How did curiosity change the story?",
            answer=f"Curiosity made {a.id} want to peek and taste. That choice led them toward the little mess they had to solve together."
        ),
        QAItem(
            question="How did teamwork help at the end?",
            answer=f"{a.id} and {b.id} held the bowl steady and scooped the guacamole back in together. Teamwork turned the spill into a tidy, happy ending."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are octopi?",
            answer="Octopi are sea animals with eight arms. They can explore, grab, and help each other in clever ways."
        ),
        QAItem(
            question="What is guacamole?",
            answer="Guacamole is a soft green dip made from avocados. It can be tasty, and it can get messy if a bowl tips over."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means working together to do something better than one friend could do alone. It helps when a job needs more than one pair of hands."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={dict(meters)} memes={dict(memes)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    act = ACTIONS[params.action]
    item = ITEMS[params.item]
    creature = CREATURES[params.creature]
    a = world.add(Entity(id=params.name_a, kind="character", type="octopus", label=params.name_a))
    b = world.add(Entity(id=params.name_b, kind="character", type="octopus", label=params.name_b))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label=item.label))
    world.facts.update(item=item, action=act, creature=creature, bowl=bowl, octopi=(a, b))

    a.memes["curiosity"] = 1.0
    b.memes["surprise"] = 1.0
    b.memes["teamwork"] = 1.0

    world.say(
        f"Under the blue, blue brine, two octopi glimmered fine. "
        f"{a.id} and {b.id} found guacamole in a bowl, a green surprise for a curious soul."
    )
    world.say(
        f"{a.id} leaned near with a twinkly grin, for curious eyes like to peek within. "
        f'"What is it?" they asked, with a wiggle and a spin.'
    )
    world.para()
    world.say(
        f"{b.id} laughed in surprise, with wide round eyes. "
        f'"It is guacamole, green and grand; let us be gentle, let us be hand-in-hand."'
    )
    world.say(
        f"They {act.verb} close, and the bowl gave a sway, as seaweed swished in a playful way."
    )
    world.para()
    if act.risk:
        world.say(
            f"Then splish and splash, the bowl tipped in a flash. "
            f"Green guacamole slid with a little mash."
        )
        world.say(
            f"But teamwork came quick: {a.id} and {b.id} worked as one. "
            f"They steadied the bowl until the spill was done."
        )
        bowl.meters["spilled"] += 1
    else:
        world.say(
            f"The bowl stayed snug, no spill, no smudge. "
            f"They tasted with care and gave a happy shrug."
        )
    world.para()
    world.say(
        f"So if curiosity calls and surprise comes true, teamwork can help make the best things new. "
        f"With octopi, a rhyme, and guacamole too, the sea sang soft: \"We can do it, we two!\""
    )
    world.facts["outcome"] = "spill" if act.risk else "tidy"
    return world


def valid_story(params: StoryParams) -> bool:
    return params.creature == "octopi" and params.item == "guacamole" and params.setting in SETTINGS


ASP_RULES = r"""
valid(S, C, I, A) :- setting(S), creature(C), item(I), action(A).
storyful(C, I) :- creature(C), item(I), C = octopi, I = guacamole.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, creature=None, item=None, action=None, name_a=None, name_b=None), random.Random(7)))
        _ = sample.story
    except Exception as e:  # noqa: BLE001
        print(f"MISMATCH: normal generation failed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("tidepool", "octopi", "guacamole", "peek", "Mira", "Nico"),
    StoryParams("reef", "octopi", "guacamole", "balance", "Tula", "Sage"),
    StoryParams("harbor", "octopi", "guacamole", "carry", "Poppy", "Bobo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
