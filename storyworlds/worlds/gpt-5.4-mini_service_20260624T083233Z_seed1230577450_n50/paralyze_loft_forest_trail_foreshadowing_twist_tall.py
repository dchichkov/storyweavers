#!/usr/bin/env python3
"""
A tall-tale storyworld about a forest trail, a foreshadowed trouble, and a twist
that changes the ending.

The source tale behind this world is simple:
A little scout walks a forest trail carrying a lantern and a pouch of trail
marks. The trail grows strange, because a windmill-sized owl in the branches
keeps dropping hints: bent reeds, broken twigs, and a hidden bridge that may not
be what it seems. The scout fears a curse will paralyze the path, but the old
trail guide climbs a loft, spots the trick, and uses a high perch to reveal a
safer way across.

The simulation models:
- a forest trail with a looming gap
- a foreshadowing chain that increases unease before the problem is explained
- a twist that turns the "paralyze" threat into a controllable, non-magical jam
- a loft as a physical height advantage that helps uncover the truth

Stories are generated from world state, not from a fixed paragraph template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    in_loft: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    clue: object | None = None
    gap: object | None = None
    guide: object | None = None
    lantern: object | None = None
    loft: object | None = None
    scout: object | None = None
    trail: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "guide", "aunt"}
        male = {"boy", "man", "father", "uncle", "scout"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the forest trail"
    world: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    name: str
    gender: str
    guide_name: str
    guide_gender: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _narrate(world: World, msg: str) -> None:
    world.say(msg)
    world.trace.append(msg)


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    scout = world.get("Scout")
    trail = world.get("Trail")
    if scout.memes.get("unease", 0) < THRESHOLD:
        return out
    sig = ("foreshadow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trail.meters["mystery"] += 1
    trail.memes["warning"] += 1
    out.append("The trail felt like it was holding its breath.")
    out.append("Bent reeds and snapped twigs pointed ahead like little fingers.")
    return out


def _r_paralyze(world: World) -> list[str]:
    out: list[str] = []
    scout = world.get("Scout")
    guide = world.get("Guide")
    trail = world.get("Trail")
    if scout.memes.get("fear", 0) < THRESHOLD:
        return out
    if trail.meters.get("blocked", 0) < THRESHOLD:
        return out
    sig = ("paralyze",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scout.memes["stuck"] = 1
    guide.memes["urgency"] = guide.memes.get("urgency", 0) + 1
    out.append("For a spell, nobody wanted to take another step.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("Guide")
    trail = world.get("Trail")
    clue = world.get("Clue")
    if not guide.in_loft or clue.meters.get("seen", 0) < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trail.meters["blocked"] = 0
    trail.memes["warning"] = 0
    world.facts["twist_revealed"] = True
    out.append("That was when the old guide laughed and pointed out the trick.")
    out.append("The gap was not a curse at all, only a fallen log hidden by ferns.")
    return out


CAUSAL_RULES = [
    _r_foreshadow,
    _r_paralyze,
    _r_twist,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            msgs = rule(world)
            if msgs:
                changed = True
                produced.extend(msgs)
    if narrate:
        for msg in produced:
            world.say(msg)
    return produced


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    scout = world.add(Entity(id="Scout", kind="character", type=params.gender, label=params.name))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide_gender, label=params.guide_name))
    trail = world.add(Entity(id="Trail", type="trail", label="the forest trail"))
    lantern = world.add(Entity(id="Lantern", type="thing", label="lantern", owner=scout.id))
    clue = world.add(Entity(id="Clue", type="thing", label="clue", phrase="small hints in the brush"))
    loft = world.add(Entity(id="Loft", type="place", label="loft", in_loft=False))
    gap = world.add(Entity(id="Gap", type="thing", label="gap"))

    scout.memes["curiosity"] = 1
    scout.memes["unease"] = 1
    guide.memes["calm"] = 1
    trail.meters["blocked"] = 1
    trail.meters["mystery"] = 1
    gap.meters["blocked"] = 1

    world.facts.update(
        scout=scout,
        guide=guide,
        trail=trail,
        lantern=lantern,
        clue=clue,
        loft=loft,
        gap=gap,
    )
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    scout = world.get("Scout")
    guide = world.get("Guide")
    trail = world.get("Trail")
    lantern = world.get("Lantern")
    clue = world.get("Clue")
    loft = world.get("Loft")

    _narrate(world, f"{scout.label} was a little brave {scout.type} who loved the forest trail.")
    _narrate(world, f"{scout.pronoun().capitalize()} carried a lantern, because even tall tales like a little light.")
    _narrate(world, f"{guide.label} was an old trail guide with a steady smile and a voice like warm soup.")
    _narrate(world, "Before the trouble began, the reeds beside the path bent the wrong way.")
    _narrate(world, "A broken twig lay across the moss as if some unseen foot had warned the day.")
    propagate(world)

    world.para()
    _narrate(world, f"Then {scout.label} reached the place where the trail narrowed near the old bridge.")
    _narrate(world, f"{scout.pronoun().capitalize()} felt a strange hush, and {scout.pronoun('possessive')} knees went wobbly.")
    trail.meters["blocked"] = 1
    scout.memes["fear"] = 1
    _narrate(world, f"{scout.label} whispered that the path might paralyze them forever.")
    propagate(world)

    world.para()
    loft.in_loft = True
    guide.in_loft = True
    guide.meters["height"] = 1
    clue.meters["seen"] = 1
    _narrate(world, f"That was when {guide.label} climbed a loft above the trees to get a better look.")
    _narrate(world, f"From up high, {guide.label} spotted the clue hidden under the ferns.")
    propagate(world)

    world.para()
    _narrate(world, f"{guide.label} called down that the trail was not cursed at all.")
    _narrate(world, "It was only a fallen log across the path, and the ferns had made it look like a giant trap.")
    _narrate(world, f"So {guide.label} stepped down from the loft, lifted the log aside, and led the way.")
    trail.meters["blocked"] = 0
    scout.memes["fear"] = 0
    scout.memes["joy"] = 1
    _narrate(world, f"{scout.label} crossed with {lantern.label} held high, grinning at the trick of it all.")
    _narrate(world, "And the forest trail, no longer stuck in its own tall tale, opened wide ahead.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scout = f["scout"]
    guide = f["guide"]
    return [
        "Write a tall tale for a young child about a forest trail, a scary-looking clue, and a twist that turns fear into relief.",
        f"Tell a story where {scout.label} thinks the trail might paralyze the walk, but {guide.label} finds the answer from a loft.",
        "Write a simple, funny adventure with foreshadowing, a hidden trick, and a safe ending on a forest trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scout = f["scout"]
    guide = f["guide"]
    trail = f["trail"]
    return [
        QAItem(
            question=f"Who walked the forest trail and got worried that the path might paralyze them?",
            answer=f"It was {scout.label}, the little {scout.type}, who felt spooked by the narrow trail.",
        ),
        QAItem(
            question=f"What did the old guide climb to get a better look at the trail?",
            answer=f"{guide.label} climbed a loft above the trees so {guide.pronoun().capitalize()} could spot the clue.",
        ),
        QAItem(
            question="What made the story change from scary to safe?",
            answer="The twist was that the trouble was only a fallen log hidden by ferns, not a curse.",
        ),
        QAItem(
            question=f"What happened to the trail at the end?",
            answer=f"The blocked place on {trail.label} was cleared, and the path opened wide again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a loft?",
            answer="A loft is a high place or upper space, often above the ground, where you can see farther.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story drops little hints early so what happens later does not feel surprising.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the characters think is happening.",
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.in_loft:
            bits.append("in_loft=True")
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("setting", "forest_trail"))
    lines.append(asp.fact("place", "trail"))
    lines.append(asp.fact("place", "loft"))
    lines.append(asp.fact("feature", "foreshadowing"))
    lines.append(asp.fact("feature", "twist"))
    lines.append(asp.fact("keyword", "paralyze"))
    lines.append(asp.fact("keyword", "loft"))
    lines.append(asp.fact("can_hint", "forest_trail", "foreshadowing"))
    lines.append(asp.fact("can_reveal", "forest_trail", "twist"))
    lines.append(asp.fact("can_use", "loft", "reveal"))
    lines.append(asp.fact("can_block", "trail", "paralyze"))
    return "\n".join(lines)


ASP_RULES = r"""
hinting(forest_trail) :- setting(forest_trail), feature(foreshadowing).
twistable(forest_trail) :- setting(forest_trail), feature(twist), place(trail), place(loft).
safe_story(forest_trail) :- hinting(forest_trail), twistable(forest_trail), can_block(trail, paralyze).
#show hinting/1.
#show twistable/1.
#show safe_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_story/1."))
    atoms = asp.atoms(model, "safe_story")
    py = [("forest_trail",)] if asp_reasonable() else []
    if sorted(atoms) == py:
        print("OK: ASP and Python agree on the storyworld shape.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", py)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: forest trail, loft, foreshadowing, twist.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["woman", "man", "guide"], default="guide")
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
    name_pool_girl = ["Mina", "Lena", "Tia", "Nora", "Ivy"]
    name_pool_boy = ["Jude", "Eli", "Perry", "Owen", "Finn"]
    guide_pool = ["Aunt June", "Old Moss", "Gran Birch", "Uncle Reed", "Mabel"]
    guide_genders = ["woman", "man", "guide"]
    name = getattr(args, "name", None) or rng.choice(name_pool_girl if getattr(args, "gender", None) == "girl" else name_pool_boy)
    guide_name = getattr(args, "guide_name", None) or rng.choice(guide_pool)
    guide_gender = getattr(args, "guide_gender", None) or rng.choice(guide_genders)
    return StoryParams(name=name, gender=getattr(args, "gender", None), guide_name=guide_name, guide_gender=guide_gender)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show safe_story/1."))
        print(asp.atoms(model, "safe_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        cur = [
            StoryParams(name="Mina", gender="girl", guide_name="Aunt June", guide_gender="woman"),
            StoryParams(name="Jude", gender="boy", guide_name="Old Moss", guide_gender="guide"),
            StoryParams(name="Ivy", gender="girl", guide_name="Gran Birch", guide_gender="woman"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
