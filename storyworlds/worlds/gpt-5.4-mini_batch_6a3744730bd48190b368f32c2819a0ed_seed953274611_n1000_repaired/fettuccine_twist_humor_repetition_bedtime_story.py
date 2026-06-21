#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fettuccine_twist_humor_repetition_bedtime_story.py
===================================================================================

A tiny bedtime story world about a small kitchen surprise: a child sets out to
make a cozy supper, a silly twist changes the plan, repetition calms the moment,
and humor helps everything end in a warm, soft way.

The story always includes fettuccine and keeps a gentle bedtime-story feel:
quiet rooms, simple feelings, one small problem, a funny turn, and a comforting
ending image that proves what changed.
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    mood: str
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
class Food:
    id: str
    label: str
    phrase: str
    texture: str
    playful: str
    can_twist: bool = True
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
class Twist:
    id: str
    label: str
    funny_turn: str
    effect: str
    repeat_line: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    soup = world.get("fettuccine")
    if soup.meters["warm"] < THRESHOLD:
        return out
    sig = ("warm", soup.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["cozy"] += 1
    out.append("__warm__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["giggle"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent = world.get("parent")
    parent.memes["fond"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("warm", "feeling", _r_warm), Rule("laugh", "social", _r_laugh)]


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


def kitchen_twist(world: World, child: Entity, parent: Entity, food: Food, twist: Twist) -> None:
    child.memes["expecting"] += 1
    world.say(
        f"At bedtime, {child.id} and {parent.label_word} were in the little kitchen, "
        f"where {food.phrase} waited in a quiet pot."
    )
    world.say(
        f"{child.id} wanted dinner to be simple and sleepy. "
        f"{child.id} wanted dinner to be simple and sleepy. "
        f"That was the plan."
    )
    world.para()
    world.say(
        f"But then the pot did a {twist.funny_turn}. "
        f'Not a big twist, just a tiny twist: {twist.effect}.'
    )
    world.say(
        f'{child.id} blinked once, then twice. "{twist.label}," {child.id} whispered, '
        f'"{twist.label}."'
    )
    child.memes["surprise"] += 1
    child.memes["giggle"] += 1
    world.get("fettuccine").meters["twisted"] += 1
    propagate(world, narrate=False)


def repeat_and_settle(world: World, child: Entity, parent: Entity, twist: Twist) -> None:
    world.say(
        f"{child.id} took a breath and said it again: {twist.repeat_line}. "
        f"Then {parent.label_word} said it again too, in a soft bedtime voice."
    )
    world.say(
        f'"{twist.repeat_line}," said {child.id}. "{twist.repeat_line}," said {parent.label_word}. '
        f'And because the words came back the same, the room felt less wiggly.'
    )
    parent.memes["calm"] += 1
    child.memes["calm"] += 1


def solve_supper(world: World, parent: Entity, food: Food, comfort: Comfort) -> None:
    soup = world.get("fettuccine")
    soup.meters["warm"] += 1
    soup.meters["served"] += 1
    world.say(
        f"{parent.label_word} turned the funny little twist into supper. "
        f"{parent.pronoun().capitalize()} lifted the fettuccine carefully, and the noodles "
        f"stayed curly like ribbons."
    )
    world.say(
        f"Then {parent.label_word} added a small smile of butter and a quiet sprinkle of cheese. "
        f"It smelled like sleepy sunshine."
    )
    world.say(
        f"{child.id} held {comfort.phrase} close and nodded at the bowl. "
        f"The bowl was warm, the noodles were safe, and the twist had turned into a joke."
    )
    propagate(world, narrate=False)


def bedtime_close(world: World, child: Entity, parent: Entity, food: Food) -> None:
    world.say(
        f"At last, {child.id} slurped one noodle, then another, then one more. "
        f"{parent.label_word} smiled when the spoon made a tiny clink."
    )
    world.say(
        f"{child.id} was sleepy, {child.id} was happy, and {child.id} was full. "
        f"The fettuccine was gone, but the warm feeling stayed."
    )
    world.say(
        f"Outside the window, the night was dark and gentle. Inside, the kitchen "
        f"was quiet as a blanket."
    )


def tell(setting: Setting, food: Food, twist: Twist, comfort: Comfort,
         child_name: str = "Milo", child_gender: str = "boy",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="fettuccine", kind="thing", type="food", label=food.label))
    world.facts["setting"] = setting
    world.facts["food"] = food
    world.facts["twist"] = twist
    world.facts["comfort"] = comfort
    kitchen_twist(world, child, parent, food, twist)
    world.para()
    repeat_and_settle(world, child, parent, twist)
    solve_supper(world, parent, food, comfort)
    world.para()
    bedtime_close(world, child, parent, food)
    world.facts.update(child=child, parent=parent, outcome="soft_twist")
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="a little kitchen", mood="quiet"),
    "cozy": Setting(id="cozy", place="a cozy kitchen", mood="warm"),
}

FOODS = {
    "fettuccine": Food(
        id="fettuccine",
        label="fettuccine",
        phrase="a bowl of fettuccine",
        texture="curly",
        playful="wiggly",
        can_twist=True,
        tags={"fettuccine", "food", "noodle"},
    )
}

TWISTS = {
    "fork": Twist(
        id="fork",
        label="fork twist",
        funny_turn="fork twist",
        effect="one noodle looped around the fork and wore the fork like a crown",
        repeat_line="the noodle got a crown",
        tags={"twist", "humor", "repetition"},
    ),
    "napkin": Twist(
        id="napkin",
        label="napkin twist",
        funny_turn="napkin twist",
        effect="one napkin slid off the table and landed like a tiny cape",
        repeat_line="the cape fell down",
        tags={"twist", "humor", "repetition"},
    ),
    "steam": Twist(
        id="steam",
        label="steam twist",
        funny_turn="steam twist",
        effect="a wisp of steam danced up and made the spoon look surprised",
        repeat_line="the steam went up",
        tags={"twist", "humor", "repetition"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        glow="warm and sleepy",
        tags={"bedtime", "comfort"},
    ),
    "pillow": Comfort(
        id="pillow",
        label="pillow",
        phrase="a round pillow",
        glow="soft and cozy",
        tags={"bedtime", "comfort"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    food: str
    twist: str
    comfort: str
    child_name: str = ""
    child_gender: str = "boy"
    parent_name: str = "Mom"
    parent_gender: str = "mother"
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


CURATED = [
    StoryParams(setting="kitchen", food="fettuccine", twist="fork", comfort="blanket"),
    StoryParams(setting="cozy", food="fettuccine", twist="napkin", comfort="pillow"),
    StoryParams(setting="kitchen", food="fettuccine", twist="steam", comfort="blanket"),
]

GIGGLE_NAMES = ["Milo", "Nina", "Theo", "Luna", "Ada", "Owen"]
PARENT_NAMES = ["Mom", "Dad"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for food in FOODS:
            for twist in TWISTS:
                combos.append((setting, food, twist))
    return combos


def explain_rejection(_: object) -> str:
    return "(No story: this world only tells a gentle fettuccine bedtime tale.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the word "{f["food"].label}" and a small funny twist.',
        f"Tell a cozy story where {f['child'].id} notices a silly change in the fettuccine, repeats a calming line, and ends sleepy.",
        'Write a child-friendly bedtime story with twist, humor, and repetition around a bowl of fettuccine.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    twist = f["twist"]
    qa = [
        QAItem(
            question="What food is in the story?",
            answer="The story is about fettuccine. It is the warm, curly supper that the child and parent are getting ready for bedtime.",
        ),
        QAItem(
            question="What funny thing happened to the dinner?",
            answer=f"A tiny {twist.label} changed the noodles in a silly way. The twist made everyone pause, and then it turned into a joke instead of a problem.",
        ),
        QAItem(
            question="Why did the repeated words help?",
            answer=f"{child.id} and {parent.label_word} said the same little line again and again. Repeating it made the kitchen feel calmer, so the surprise did not stay scary.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with warm noodles, a quiet kitchen, and a sleepy child. The twist became a cozy supper story instead of a worry.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fettuccine?",
            answer="Fettuccine is a kind of pasta with long, flat noodles. It is often served warm with sauce or butter.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a small change that surprises you. It can make a story funny or interesting when something happens in a new way.",
        ),
        QAItem(
            question="Why can repetition be comforting?",
            answer="Repetition can feel comforting because familiar words come back the same way. That steadiness can help a child feel safe and calm.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime story world about fettuccine, a twist, humor, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    if args.food and args.food not in FOODS:
        raise StoryError("Unknown food.")
    setting = args.setting or rng.choice(list(SETTINGS))
    food = args.food or "fettuccine"
    twist = args.twist or rng.choice(list(TWISTS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(GIGGLE_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(
        setting=setting,
        food=food,
        twist=twist,
        comfort=comfort,
        child_name=child_name,
        child_gender=child_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.food not in FOODS or params.twist not in TWISTS or params.comfort not in COMFORTS or params.setting not in SETTINGS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        setting=SETTINGS[params.setting],
        food=FOODS[params.food],
        twist=TWISTS[params.twist],
        comfort=COMFORTS[params.comfort],
        child_name=params.child_name or "Milo",
        child_gender=params.child_gender,
        parent_name=params.parent_name or "Mom",
        parent_gender=params.parent_gender,
    )
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


ASP_RULES = r"""
food(fettuccine).
twist(fork). twist(napkin). twist(steam).
comfort(blanket). comfort(pillow).
setting(kitchen). setting(cozy).
valid(S,F,T) :- setting(S), food(F), twist(T), F = fettuccine.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("food", "fettuccine")]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.twist} / {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
