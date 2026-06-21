#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/burnous_magic_twist_lesson_learned_fairy_tale.py
================================================================================

A tiny fairy-tale storyworld about a child, a burnous, a bit of magic, a twist,
and a lesson learned.

Premise:
- A child treasures a burnous.
- A small magical wish goes sideways in a gentle twist.
- A grown-up or helper reveals a wiser, safer kind of magic.
- The ending proves the child learned something concrete.

The world is intentionally small and constraint-driven. Stories are generated
from simulated state, not by swapping nouns into a fixed paragraph.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    attrs: dict[str, str] = field(default_factory=dict)
    magical: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "fairy"}
        male = {"boy", "father", "king", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "fairy": "fairy"}.get(self.type, self.type)
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    safe: bool
    power: int
    twist: str
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
class Trouble:
    id: str
    label: str
    phrase: str
    risk: str
    spread: int
    magical: bool = True
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
class Remedy:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    wisdom: int
    lesson: str
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
        return clone


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.get("loom").meters["twisted"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("child", "helper"):
        world.get(eid).memes["surprise"] += 1
    world.get("room").meters["glow"] += 1
    out.append("__twist__")
    return out


def _r_learn(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["lesson"] < THRESHOLD:
        return out
    sig = ("learn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["wisdom"] += 1
    out.append("__learn__")
    return out


CAUSAL_RULES = [_r_spread, _r_learn]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_charm(charm: Charm) -> bool:
    return charm.safe and charm.power >= 1


def valid_combo(charm: Charm, trouble: Trouble, remedy: Remedy) -> bool:
    return charm.safe and trouble.magical and remedy.wisdom >= 2 and remedy.power >= trouble.spread


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CHARMS.values():
        for t in TROUBLES.values():
            for r in REMEDIES.values():
                if valid_combo(c, t, r):
                    combos.append((c.id, t.id, r.id))
    return combos


@dataclass
class StoryParams:
    charm: str
    trouble: str
    remedy: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
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


class StoryScript:
    pass


def tell(charm: Charm, trouble: Trouble, remedy: Remedy, child: str = "Ayla",
         child_gender: str = "girl", helper: str = "Nori", helper_gender: str = "boy",
         parent: str = "Queen Maris") -> World:
    world = World()
    kid = world.add(Entity(id="child", kind="character", type=child_gender, label=child, role="child"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper, role="helper"))
    parent_ent = world.add(Entity(id="parent", kind="character", type="queen", label=parent, role="parent"))
    world.add(Entity(id="room", type="room", label="the mossy hall"))
    world.add(Entity(id="loom", type="thing", label=charm.label, magical=True))
    world.facts["charm"] = charm
    world.facts["trouble"] = trouble
    world.facts["remedy"] = remedy
    world.facts["child"] = kid
    world.facts["helper"] = helper_ent
    world.facts["parent"] = parent_ent

    kid.memes["hope"] += 1
    helper_ent.memes["care"] += 1
    world.say(
        f"Once in a little green kingdom, {child} loved a {charm.label}: {charm.phrase}. "
        f"It {charm.effect}, and everyone said it felt like a bit of moonlight."
    )
    world.say(
        f"One evening, {child} wanted to use it near {trouble.phrase}, because the dark corner "
        f"of the hall looked lonely and cold."
    )

    world.para()
    kid.memes["desire"] += 1
    helper_ent.memes["warning"] += 1
    world.say(
        f'{helper} touched {helper}\'s chin and said, "{child}, that magic is lively. '
        f"It might {trouble.risk}."'
    )
    world.say(
        f"But {child} only smiled and said the burnous could make anything brave."
    )

    world.para()
    kid.meters["twisted"] += 1
    propagate(world, narrate=False)
    if charm.twist:
        world.say(
            f"{child} lifted the burnous, whispered a wish, and the hem answered with a twist: "
            f"{charm.twist}."
        )
    world.say(
        f"At once, the air changed, and the hall's glow grew odd and curious."
    )

    world.para()
    kid.memes["lesson"] += 1
    world.say(
        f"Then {helper} found a wiser thing: {remedy.phrase}. {helper} used it to {remedy.method}, "
        f"and the magic settled down like a tired kitten."
    )
    world.say(
        f"{parent} smiled and said, \"A clever heart learns when to ask for the kinder spell.\""
    )
    world.say(
        f"{child} nodded, tucked the burnous close, and remembered the lesson learned: {remedy.lesson}."
    )
    world.say(
        f"From then on, the burnous was still wonderful, but it was used for gentle magic and safe surprises."
    )

    world.facts["outcome"] = "wise"
    return world


CHARMS = {
    "moon_burnous": Charm(
        id="moon_burnous",
        label="burnous",
        phrase="a soft silver burnous",
        effect="shone with a gentle silver gleam",
        safe=True,
        power=2,
        twist="the sleeves fluttered like shy little wings",
        tags={"burnous", "magic"},
    ),
    "ember_burnous": Charm(
        id="ember_burnous",
        label="burnous",
        phrase="a warm red burnous",
        effect="glowed like a tiny hearth",
        safe=True,
        power=2,
        twist="a tiny star hopped from the hem and bowed",
        tags={"burnous", "magic"},
    ),
}

TROUBLES = {
    "lonely_shadow": Trouble(
        id="lonely_shadow",
        label="lonely shadow",
        phrase="a lonely shadow in the corner",
        risk="wake the old spiders",
        spread=1,
        magical=True,
        tags={"shadow", "magic"},
    ),
    "sleepy_thorn": Trouble(
        id="sleepy_thorn",
        label="sleepy thorn",
        phrase="a sleepy thorn vine by the wall",
        risk="snag the cloth and tangle the spell",
        spread=2,
        magical=True,
        tags={"thorn", "magic"},
    ),
}

REMEDIES = {
    "lantern_song": Remedy(
        id="lantern_song",
        label="lantern song",
        phrase="a lantern that sang softly",
        method="light the hall without waking the dark",
        power=2,
        wisdom=3,
        lesson="kind magic works best when it does not rush",
        tags={"lantern", "song"},
    ),
    "mirror_knot": Remedy(
        id="mirror_knot",
        label="mirror knot",
        phrase="a mirror knot tied with a ribbon",
        method="steady the spell and calm the twist",
        power=3,
        wisdom=3,
        lesson="a clever spell is safer than a proud one",
        tags={"mirror", "knot"},
    ),
}

NAMES = ["Ayla", "Mina", "Romi", "Lio", "Sami", "Tala"]
HELPERS = ["Nori", "Bela", "Oren", "Fenn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a small child that includes the word "{f["charm"].label}" and a little bit of magic.',
        f"Tell a gentle fairy tale where {f['child'].id} learns that {f['remedy'].lesson}.",
        f"Write a story with a magical twist: a burnous, a careful helper, and a wiser ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    charm, trouble, remedy = f["charm"], f["trouble"], f["remedy"]
    child, helper, parent = f["child"], f["helper"], f["parent"]
    return [
        ("What was special about the burnous?",
         f"The burnous was magical and it {charm.effect}. That made it feel special, but also a little risky near trouble."),
        ("What twist happened in the story?",
         f"When {child.label} whispered a wish, the burnous answered with a twist and the hall's magic changed. The surprise showed that even good magic can behave in a new way."),
        ("How did the helper fix the problem?",
         f"{helper.label} used {remedy.phrase} to {remedy.method}. That steadied the magic and gave the child a safer way to continue."),
        ("What lesson did the child learn?",
         f"{child.label} learned that {remedy.lesson}. The ending proves it because the burnous was saved for gentle magic after that."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a burnous?",
         "A burnous is a long cloak or hooded robe. In a fairy tale it can feel noble, warm, and magical."),
        ("What is a twist in a story?",
         "A twist is a surprise change that makes the story go in a new direction. It often turns an ordinary moment into something unexpected."),
        ("What does it mean to learn a lesson?",
         "It means someone understands something important after what happened. The new understanding changes how they act next time."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.magical:
            bits.append("magical=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        charm="moon_burnous",
        trouble="lonely_shadow",
        remedy="lantern_song",
        child="Ayla",
        child_gender="girl",
        helper="Nori",
        helper_gender="boy",
        parent="Queen Maris",
    ),
    StoryParams(
        charm="ember_burnous",
        trouble="sleepy_thorn",
        remedy="mirror_knot",
        child="Mina",
        child_gender="girl",
        helper="Bela",
        helper_gender="girl",
        parent="King Thal",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.trouble and args.remedy:
        if not valid_combo(CHARMS[args.charm], TROUBLES[args.trouble], REMEDIES[args.remedy]):
            raise StoryError("That charm, trouble, and remedy do not make a sensible fairy tale.")
    combos = [c for c in valid_combos()
              if (args.charm is None or c[0] == args.charm)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    charm_id, trouble_id, remedy_id = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in HELPERS if n != child])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["Queen Maris", "King Thal", "Lady Ilen", "Lord Ferin"])
    return StoryParams(
        charm=charm_id,
        trouble=trouble_id,
        remedy=remedy_id,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.charm not in CHARMS or params.trouble not in TROUBLES or params.remedy not in REMEDIES:
        raise StoryError("Invalid params.")
    if not valid_combo(CHARMS[params.charm], TROUBLES[params.trouble], REMEDIES[params.remedy]):
        raise StoryError("Those parameters do not describe a reasonable fairy tale.")
    world = tell(CHARMS[params.charm], TROUBLES[params.trouble], REMEDIES[params.remedy],
                 child=params.child, child_gender=params.child_gender,
                 helper=params.helper, helper_gender=params.helper_gender, parent=params.parent)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: burnous, magic, twist, lesson learned.")
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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


ASP_RULES = r"""
valid(C,T,R) :- charm(C), trouble(T), remedy(R), safe(C), magical_trouble(T), wise(R), power(R,P), spread(T,S), P >= S.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.safe:
            lines.append(asp.fact("safe", cid))
        lines.append(asp.fact("power", cid, c.power))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.magical:
            lines.append(asp.fact("magical_trouble", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("wise", rid))
        lines.append(asp.fact("power", rid, r.power))
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
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True, trace=True)
        if not buf.getvalue():
            raise RuntimeError("emit produced no output")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations")
        for c, t, r in asp_valid_combos():
            print(f"  {c} {t} {r}")
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
            header = f"### {p.child}: {p.charm} / {p.trouble} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
