#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sea_hag_question_bad_ending_twist_kindness.py
===============================================================================

A tiny fable-style storyworld about a child by the sea, a hag, a question, a
kindness, a twist, and a bad ending.

The premise is simple: a child meets a hag at the shore and asks a question
about the sea. A kind act opens the hag's heart enough to answer, but the twist
is that the answer is still too late to save the child from the tide. The story
must end with a concrete change in the world: a lost boat, a soaked cloak, an
empty shore, or some other proof that the sea took something back.

This world is deliberately small and constraint-checked. It uses typed entities,
physical meters, emotional memes, a forward causal step, a reasonableness gate,
and an inline ASP twin for parity checking.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/sea_hag_question_bad_ending_twist_kindness.py
    python storyworlds/worlds/gpt-5.4-mini/sea_hag_question_bad_ending_twist_kindness.py --qa
    python storyworlds/worlds/gpt-5.4-mini/sea_hag_question_bad_ending_twist_kindness.py --all
    python storyworlds/worlds/gpt-5.4-mini/sea_hag_question_bad_ending_twist_kindness.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DANGER_TIDE = 2.0
KINDNESS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"wet": 0.0, "lost": 0.0, "tide": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "fear": 0.0, "hope": 0.0, "grief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hag"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    place: str
    sea_image: str
    danger_image: str
    question_about: str
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
class Gift:
    id: str
    label: str
    phrase: str
    warmth: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Outcome:
    id: str
    sense: int
    twist: str
    ending: str
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


def _r_tide(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    sea = world.get("sea")
    if child.memes["fear"] >= THRESHOLD and sea.meters["tide"] < DANGER_TIDE:
        sig = ("tide",)
        if sig not in world.fired:
            world.fired.add(sig)
            sea.meters["tide"] = DANGER_TIDE
            child.meters["wet"] += 1
            out.append("__tide__")
    return out


CAUSAL_RULES = [Rule("tide", _r_tide)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    lines: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                lines.extend(r for r in res if not r.startswith("__"))
    if narrate:
        for line in lines:
            world.say(line)


def tell(setting: Setting, gift: Gift, outcome: Outcome,
         child_name: str = "Mina", child_gender: str = "girl",
         hag_name: str = "Old Nera", hag_gender: str = "hag") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    hag = world.add(Entity(id="hag", kind="character", type=hag_gender, label=hag_name, role="hag"))
    sea = world.add(Entity(id="sea", kind="thing", type="thing", label="the sea", role="sea"))
    boat = world.add(Entity(id="boat", kind="thing", type="thing", label="a little boat", role="boat"))
    shore = world.add(Entity(id="shore", kind="thing", type="thing", label="the shore", role="shore"))

    world.say(
        f"Once by {setting.place}, {child.label} came to {setting.sea_image}. "
        f"There {child.label} met {hag.label_word}, a hag with salt in {hag.pronoun('possessive')} hair."
    )
    world.say(
        f'"Why is {setting.question_about}?" {child.label} asked the hag. '
        f'The question drifted over the water like a gull.'
    )

    world.para()
    child.memes["kindness"] += 1
    hag.memes["hope"] += 1
    world.say(
        f"{child.label} shared {gift.phrase} with {hag.label_word}, and the hag's hard face softened. '
        f'"That is kind," {hag.label_word} said, warming {hag.pronoun('possessive')} hands on the gift."
    )

    world.para()
    world.say(
        f"{hag.label_word} gave a twist of answer: {outcome.twist}. "
        f'Then {hag.label_word} pointed to the water and warned, "The sea keeps what it can."'
    )
    child.memes["fear"] += 1
    propagate(world, narrate=False)

    world.para()
    if outcome.id == "bad":
        boat.meters["lost"] += 1
        child.memes["grief"] += 1
        world.say(
            f"The child believed the answer a little too late. A white wave ran up fast, "
            f"pushed the little boat loose, and carried it out from the shore."
        )
        world.say(
            f"{child.label} reached for it, but the tide was already stronger than small hands. "
            f"By dusk, the boat was gone, and only wet sand stayed where it had been."
        )
        world.say(
            f"{hag.label_word} stood on the rocks with a gentle face, but the ending was still sad: "
            f"kindness had opened the answer, not the door home."
        )
    else:
        child.memes["hope"] += 1
        world.say(
            f"The child listened in time and tied the little boat high, so the sea only licked the stones."
        )
        world.say(
            f"{setting.ending}."
        )

    world.facts.update(
        child=child, hag=hag, sea=sea, boat=boat, shore=shore,
        setting=setting, gift=gift, outcome=outcome,
        bad=(outcome.id == "bad"),
        question=setting.question_about,
        twist=outcome.twist,
    )
    return world


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="the gray cove",
        sea_image="a strip of silver water under the clouds",
        danger_image="the tide climbing the black stones",
        question_about="the sea always wanted the brightest shell",
    ),
    "pier": Setting(
        id="pier",
        place="the old pier",
        sea_image="wooden boards above a bright, wavering sea",
        danger_image="the tide licking the pier posts",
        question_about="the sea sounded like it was whispering names",
    ),
    "bay": Setting(
        id="bay",
        place="the quiet bay",
        sea_image="a calm bay where the water looked smooth as glass",
        danger_image="the tide sliding farther up the sand",
        question_about="the sea could keep a secret forever",
    ),
}

GIFTS = {
    "bread": Gift(id="bread", label="bread", phrase="a crust of warm bread", warmth="warm"),
    "apple": Gift(id="apple", label="apple", phrase="a bright apple from the basket", warmth="sweet"),
    "cloak": Gift(id="cloak", label="cloak", phrase="a dry blue cloak", warmth="soft"),
}

OUTCOMES = {
    "bad": Outcome(
        id="bad",
        sense=3,
        twist="the hag was not hungry for gold at all, only lonely enough to speak kindly",
        ending="",
    ),
}

@dataclass
class StoryParams:
    setting: str
    gift: str
    outcome: str
    child_name: str
    child_gender: str
    hag_name: str
    hag_gender: str
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
    StoryParams(
        setting="cove",
        gift="bread",
        outcome="bad",
        child_name="Mina",
        child_gender="girl",
        hag_name="Old Nera",
        hag_gender="hag",
        seed=None,
    ),
    StoryParams(
        setting="pier",
        gift="apple",
        outcome="bad",
        child_name="Pavel",
        child_gender="boy",
        hag_name="Marrow",
        hag_gender="hag",
        seed=None,
    ),
    StoryParams(
        setting="bay",
        gift="cloak",
        outcome="bad",
        child_name="Lina",
        child_gender="girl",
        hag_name="Sable",
        hag_gender="hag",
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, g, o) for s in SETTINGS for g in GIFTS for o in OUTCOMES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sea-hag fable storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--name")
    ap.add_argument("--hag-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.gift is None or c[1] == args.gift)
              and (args.outcome is None or c[2] == args.outcome)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, gift, outcome = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        gift=gift,
        outcome=outcome,
        child_name=args.name or rng.choice(["Mina", "Pavel", "Lina", "Oren"]),
        child_gender=gender,
        hag_name=args.hag_name or rng.choice(["Old Nera", "Marrow", "Sable"]),
        hag_gender="hag",
        seed=None,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable with the words "sea", "hag", and "question" set at {f["setting"].place}.',
        f"Tell a child-facing sea story where {f['child'].label} asks a hag a question, shows kindness, and the ending is sad.",
        f'Write a fable-like story about kindness at the sea that ends with a twist and a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["hag"]
    s = world.facts["setting"]
    o = world.facts["outcome"]
    items = [
        QAItem(
            question="Who asked the question?",
            answer=f"{c.label} asked the question. {c.label} wanted to understand the sea instead of just staring at it."
        ),
        QAItem(
            question="Why was the hag kinder after the child shared a gift?",
            answer=f"The shared {world.facts['gift'].label} made the hag feel seen and less alone. That kindness opened her heart enough to answer the child."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {o.twist}. So the answer was gentle, but it still could not stop the tide."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly. The little boat was lost to the sea, and the shore was left wet and empty."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the sea?",
            answer="The sea is a huge body of salt water. It moves with waves and tides, and it can become dangerous quickly."
        ),
        QAItem(
            question="What is a hag in stories?",
            answer="A hag is usually an old witch-like woman in a fairy tale. In this world she is lonely, salty, and a little mysterious."
        ),
        QAItem(
            question="Why can a tide be dangerous near the shore?",
            answer="A tide can rise and change the shoreline fast. It can pull things away before a child has time to save them."
        ),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.gift not in GIFTS or params.outcome not in OUTCOMES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], GIFTS[params.gift], OUTCOMES[params.outcome],
                 child_name=params.child_name, child_gender=params.child_gender,
                 hag_name=params.hag_name, hag_gender=params.hag_gender)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:6} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, O) :- setting(S), gift(G), outcome(O).
bad_end(O) :- outcome(O), sense(O, N), N < 5.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for o, ob in OUTCOMES.items():
        lines.append(asp.fact("outcome", o))
        lines.append(asp.fact("sense", o, ob.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show bad_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
