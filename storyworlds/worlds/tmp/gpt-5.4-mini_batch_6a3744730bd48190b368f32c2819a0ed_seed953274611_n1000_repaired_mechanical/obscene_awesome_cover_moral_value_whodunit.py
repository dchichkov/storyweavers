#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/obscene_awesome_cover_moral_value_whodunit.py
=============================================================================

A tiny whodunit storyworld about a vanished cover, a rude scribble, and a moral
choice: tell the truth or hide the mistake. The domain is small on purpose so
the state drives the plot, the reveal, and the ending image.

The seed words are woven into the world:
- obscene: a rude doodle / scribble
- awesome: the admired cover
- cover: the thing being prepared, hidden, and revealed
- Moral Value: honesty matters more than hiding a mistake
- Style: whodunit
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class StoryParams:
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    culprit: str
    culprit_gender: str
    parent: str
    location: str
    cover_item: str
    display_item: str
    stain: str
    moral_value: str
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
class SceneCfg:
    id: str
    place: str
    clue_place: str
    display_label: str
    cover_label: str
    extra_label: str
    atmosphere: str
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
class CulpritCfg:
    id: str
    motive: str
    hidden_reason: str
    stain_word: str
    apology: str
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


SCENES = {
    "library": SceneCfg(
        id="library",
        place="the school library",
        clue_place="under the reading table",
        display_label="the cover",
        cover_label="a book cover",
        extra_label="a display stand",
        atmosphere="quiet shelves and whispering footsteps",
    ),
    "artroom": SceneCfg(
        id="artroom",
        place="the art room",
        clue_place="by the paint sink",
        display_label="the cover",
        cover_label="a poster cover",
        extra_label="a drying rack",
        atmosphere="bright paper, glue, and paint-smell",
    ),
    "hallway": SceneCfg(
        id="hallway",
        place="the hallway bulletin board",
        clue_place="behind the notice board",
        display_label="the cover",
        cover_label="a bulletin cover",
        extra_label="a cork board",
        atmosphere="echoes, lockers, and rows of shoes",
    ),
}

CULPRITS = {
    "nervous": CulpritCfg(
        id="nervous",
        motive="wanted to hide a spill",
        hidden_reason="was scared of getting in trouble",
        stain_word="smudges",
        apology="I was scared, so I hid it.",
    ),
    "jealous": CulpritCfg(
        id="jealous",
        motive="wanted attention for a rude joke",
        hidden_reason="wanted everyone to laugh at the wrong thing",
        stain_word="scribbles",
        apology="I was trying to be funny, but I was wrong.",
    ),
    "rushed": CulpritCfg(
        id="rushed",
        motive="ran too fast and knocked the cover loose",
        hidden_reason="did not want to admit the accident",
        stain_word="creases",
        apology="I knocked it loose and then I hid it.",
    ),
}

COVER_ITEMS = {
    "cover": {"label": "cover", "awesome": "awesome", "sort": "cover"},
    "poster": {"label": "poster cover", "awesome": "awesome", "sort": "cover"},
    "dustjacket": {"label": "dust jacket", "awesome": "awesome", "sort": "cover"},
}

DISPLAY_ITEMS = {
    "book": {"label": "storybook", "best": "storybook"},
    "poster": {"label": "class poster", "best": "poster"},
    "project": {"label": "project display", "best": "project"},
}

MORAL = {
    "honesty": "Honesty is better than hiding a mistake.",
    "truth": "Telling the truth helps a problem get smaller.",
    "sorry": "A real apology matters more than pretending nothing happened.",
}

NAMES_GIRL = ["Mia", "Lina", "Zoe", "Ava", "Nora", "Maya"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Finn", "Leo", "Max"]


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


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    for line in produced:
        world.say(line)
    return produced


def _r_guilt(world: World) -> list[str]:
    out = []
    culprit = world.get("culprit")
    if culprit.memes["guilt"] >= THRESHOLD and ("guilt",) not in world.fired:
        world.fired.add(("guilt",))
        culprit.memes["fear"] += 1
        out.append("The culprit kept glancing away, as if the walls might answer back.")
    return out


def _r_truth(world: World) -> list[str]:
    out = []
    culprit = world.get("culprit")
    detective = world.get("detective")
    if culprit.memes["truth"] >= THRESHOLD and ("truth",) not in world.fired:
        world.fired.add(("truth",))
        detective.memes["relief"] += 1
        out.append("The room felt lighter once the truth finally came out.")
    return out


RULES = [Rule("guilt", _r_guilt), Rule("truth", _r_truth)]


def predict_covering(world: World) -> bool:
    sim = world.copy()
    target = sim.get("cover")
    culprit = sim.get("culprit")
    target.meters["broken"] += 1
    culprit.memes["guilt"] += 1
    return target.meters["broken"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for culprit in CULPRITS:
            for cover in COVER_ITEMS:
                combos.append((scene, culprit, cover))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit about an awesome cover, a rude clue, and honesty.")
    ap.add_argument("--location", choices=SCENES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--cover-item", choices=COVER_ITEMS)
    ap.add_argument("--display-item", choices=DISPLAY_ITEMS)
    ap.add_argument("--stain", choices=["ink", "paint", "mud"])
    ap.add_argument("--moral-value", choices=MORAL)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["teacher", "librarian", "coach"])
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
    location = args.location or rng.choice(list(SCENES))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    cover_item = args.cover_item or rng.choice(list(COVER_ITEMS))
    display_item = args.display_item or rng.choice(list(DISPLAY_ITEMS))
    stain = args.stain or rng.choice(["ink", "paint", "mud"])
    moral_value = args.moral_value or rng.choice(list(MORAL))
    if args.detective:
        detective = args.detective
        detective_gender = "girl" if detective in NAMES_GIRL else "boy"
    else:
        detective_gender = rng.choice(["girl", "boy"])
        detective = rng.choice(NAMES_GIRL if detective_gender == "girl" else NAMES_BOY)
    friend_gender = "boy" if detective_gender == "girl" else "girl"
    friend = args.friend or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    culprit_gender = rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["teacher", "librarian", "coach"])
    return StoryParams(
        detective=detective,
        detective_gender=detective_gender,
        friend=friend,
        friend_gender=friend_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        parent=parent,
        location=location,
        cover_item=cover_item,
        display_item=display_item,
        stain=stain,
        moral_value=moral_value,
    )


def setup_world(params: StoryParams) -> tuple[World, SceneCfg, CulpritCfg]:
    if params.location not in SCENES or params.culprit not in CULPRITS or params.cover_item not in COVER_ITEMS:
        raise StoryError("Invalid story parameters.")
    scene = SCENES[params.location]
    culprit_cfg = CULPRITS[params.culprit]
    world = World()
    detective = world.add(Entity(id="detective", kind="character", type=params.detective_gender, label=params.detective, role="detective"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend, role="friend"))
    culprit = world.add(Entity(id="culprit", kind="character", type=params.culprit_gender, label=params.culprit, role="culprit", attrs={"motive": culprit_cfg.motive}))
    parent = world.add(Entity(id="parent", kind="character", type="woman", label=params.parent, role="adult"))
    cover = world.add(Entity(id="cover", kind="thing", type="thing", label=COVER_ITEMS[params.cover_item]["label"]))
    display = world.add(Entity(id="display", kind="thing", type="thing", label=DISPLAY_ITEMS[params.display_item]["label"]))
    display.meters["admired"] += 1
    world.facts.update(params=params, scene=scene, culprit_cfg=culprit_cfg)
    return world, scene, culprit_cfg


def tell(world: World, scene: SceneCfg, culprit_cfg: CulpritCfg, params: StoryParams) -> None:
    d = world.get("detective")
    f = world.get("friend")
    c = world.get("culprit")
    p = world.get("parent")
    cover = world.get("cover")
    display = world.get("display")

    d.memes["curious"] += 1
    f.memes["curious"] += 1

    world.say(f"{d.label} and {f.label} found {scene.place}, where {scene.atmosphere} made the room feel like a clue waiting to be read.")
    world.say(f"On the table sat an {COVER_ITEMS[params.cover_item]['awesome']} {cover.label_word} over {display.label_word}, and everyone said it looked awesome.")
    world.say(f"Then a strange thing happened: the {cover.label_word} was still there, but something obscene had been drawn on it with {params.stain}.")

    world.para()
    world.say(f'"Who touched it?" {d.label} asked, just like a little detective in a whodunit.')
    world.say(f"{f.label} knelt near {scene.clue_place} and spotted a tiny clue: {culprit_cfg.stain_word} on the floor and a trail toward the culprit.")
    culprit.memes["guilt"] += 1
    propagate(world)

    world.para()
    world.say(f"{d.label} watched {c.label} fidget. {c.label.capitalize()} had {culprit_cfg.motive}, and that made the whole cover mess feel bigger.")
    world.say(f"{p.label_word.capitalize()} came over and said, 'A cover can be fixed, but a lie leaves a worse stain.'")
    c.memes["truth"] += 1
    world.say(f"{c.label.capitalize()} took a breath and confessed: {culprit_cfg.apology}")

    target = world.get("cover")
    target.meters["broken"] += 1
    if target.meters["broken"] >= THRESHOLD:
        world.say(f"The silly cover was cleaned, mended, and set straight again, while the rude mark was wiped away.")
    world.para()
    world.say(f"In the end, the {display.label_word} looked awesome again, and {d.label} learned the moral value of telling the truth.")
    world.say(f"The real mystery was never the stain. It was whether the culprit would hide it or be brave enough to own it.")


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f'Write a whodunit for a young child that includes the words "obscene", "awesome", and "cover" in {scene.place}.',
        f"Tell a small mystery where {p.detective} notices an obscene mark on an awesome cover and finds out who did it.",
        f"Write a story with a moral value about honesty, using a cover, a clue, and a careful reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    culprit_cfg = world.facts["culprit_cfg"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer="The mystery was who ruined the awesome cover and left an obscene mark on it. The children had to follow small clues and find out the truth.",
        ),
        QAItem(
            question=f"Who did the cover problem?",
            answer=f"{p.culprit} did it, because {culprit_cfg.hidden_reason}. In the end, {p.culprit} told the truth instead of hiding the mistake.",
        ),
        QAItem(
            question="What moral value did the story teach?",
            answer="It taught that honesty matters more than hiding a mistake. The cover could be fixed, but the lie would have made things worse.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where someone asks who did it and then follows clues to find out.",
        ),
        QAItem(
            question="What does obscene mean in this story?",
            answer="Here, obscene means rude or inappropriate, like a scribble that should not have been drawn there.",
        ),
        QAItem(
            question="What does awesome mean?",
            answer="Awesome means something is really impressive or very good.",
        ),
        QAItem(
            question="What is a cover?",
            answer="A cover is something that protects, hides, or goes over something else, like a book cover or a poster cover.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
obscene_mark(C) :- culprit(C), guilt(C).
truth_out(C) :- culprit(C), truth(C).
mystery_solved :- obscene_mark(C), truth_out(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for cid in COVER_ITEMS:
        lines.append(asp.fact("cover_item", cid))
    lines.append(asp.fact("moral", "honesty"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show obscene_mark/1.\n#show truth_out/1.\n#show mystery_solved/0."))
    _ = model
    ok = True
    py = set(valid_combos())
    if not py:
        ok = False
    try:
        sample = generate(resolve_params(argparse.Namespace(location=None, culprit=None, cover_item=None, display_item=None, stain=None, moral_value=None, detective=None, friend=None, parent=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: smoke test generation crashed: {exc}")
        return 1
    if ok:
        print("OK: ASP twin loaded and smoke test generation succeeded.")
        return 0
    print("FAIL: validation failed.")
    return 1


def asp_valids() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show scene/1.\n#show culprit/1.\n#show cover_item/1."))
    return sorted(set(asp.atoms(model, "scene")))


def explain_rejection() -> str:
    return "No reasonable mystery combination matched the requested options."


def generate(params: StoryParams) -> StorySample:
    world, scene, culprit_cfg = setup_world(params)
    tell(world, scene, culprit_cfg, params)
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
    StoryParams(
        detective="Mia",
        detective_gender="girl",
        friend="Eli",
        friend_gender="boy",
        culprit="nervous",
        culprit_gender="boy",
        parent="librarian",
        location="library",
        cover_item="cover",
        display_item="book",
        stain="ink",
        moral_value="honesty",
    ),
    StoryParams(
        detective="Noah",
        detective_gender="boy",
        friend="Ava",
        friend_gender="girl",
        culprit="jealous",
        culprit_gender="girl",
        parent="teacher",
        location="artroom",
        cover_item="poster",
        display_item="poster",
        stain="paint",
        moral_value="truth",
    ),
    StoryParams(
        detective="Lina",
        detective_gender="girl",
        friend="Finn",
        friend_gender="boy",
        culprit="rushed",
        culprit_gender="boy",
        parent="coach",
        location="hallway",
        cover_item="dustjacket",
        display_item="project",
        stain="mud",
        moral_value="sorry",
    ),
]


def valid_story(params: StoryParams) -> bool:
    return params.location in SCENES and params.culprit in CULPRITS and params.cover_item in COVER_ITEMS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        detective=args.detective or rng.choice(NAMES_GIRL + NAMES_BOY),
        detective_gender="girl" if (args.detective in NAMES_GIRL if args.detective else rng.choice([True, False])) else "boy",
        friend=args.friend or rng.choice(NAMES_GIRL + NAMES_BOY),
        friend_gender=args.friend and ("girl" if args.friend in NAMES_GIRL else "boy") or rng.choice(["girl", "boy"]),
        culprit=args.culprit or rng.choice(list(CULPRITS)),
        culprit_gender=rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["teacher", "librarian", "coach"]),
        location=args.location or rng.choice(list(SCENES)),
        cover_item=args.cover_item or rng.choice(list(COVER_ITEMS)),
        display_item=args.display_item or rng.choice(list(DISPLAY_ITEMS)),
        stain=args.stain or rng.choice(["ink", "paint", "mud"]),
        moral_value=args.moral_value or rng.choice(list(MORAL)),
    )
    if not valid_story(params):
        raise StoryError(explain_rejection())
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show obscene_mark/1.\n#show truth_out/1.\n#show mystery_solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
