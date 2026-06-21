#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/temple_nugget_detective_sharing_space_adventure.py
===================================================================================

A standalone storyworld for a tiny space-adventure tale:
a detective on a moon-temple mission must decide how to share a glowing nugget
with a nervous helper, and the ending proves what changed.

Core ingredients from the seed:
- temple
- nugget
- detective
- Sharing
- space adventure style

The world is modeled with typed entities, physical meters, emotional memes, a
small causal engine, and separate Q&A generation from world state.
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
BRAVERY_BASE = 4.0


@dataclass
class StoryParams:
    scene: str
    detective_name: str
    helper_name: str
    helper_type: str
    temple_kind: str
    nugget_kind: str
    share_kind: str
    seeker_kind: str
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "alien_girl"}
        male = {"boy", "father", "dad", "man", "brother", "alien_boy"}
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
class SceneConfig:
    id: str
    title: str
    temple: str
    dark_place: str
    travel: str
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
class NuggetConfig:
    id: str
    label: str
    glow: str
    value: int
    shareable: bool = True
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
class ShareConfig:
    id: str
    verb: str
    benefit: str
    calm_gain: int
    joy_gain: int
    text: str
    ending: str
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
        self.facts: dict[str, object] = {}

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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    nugget = world.get("nugget")
    if nugget.meters["glow"] < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["focus"] += 1
    helper.memes["worry"] += 1
    out.append("The glow made both of them watch the dark temple hall more carefully.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    nugget = world.get("nugget")
    share = world.facts["share"]
    if detective.memes["sharing"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["joy"] += share.joy_gain
    helper.memes["worry"] = max(0.0, helper.memes["worry"] - share.calm_gain)
    detective.memes["joy"] += 1
    nugget.meters["shared"] += 1
    out.append(share.text)
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_share(world: World) -> dict[str, float]:
    sim = world.copy()
    propagate(sim, narrate=False)
    helper = sim.get("helper")
    nugget = sim.get("nugget")
    return {"joy": helper.memes["joy"], "shared": nugget.meters["shared"]}


def build_story(world: World, scene: SceneConfig, nugget: NuggetConfig, share: ShareConfig) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    temple = world.get("temple")

    world.say(
        f"Far beyond the blue Earth, {detective.id} the detective landed at {scene.temple}. "
        f"The old stone temple floated on a rocky moon ridge, and {scene.dark_place} was deep inside."
    )
    world.say(
        f"Inside the temple, {world.facts['nugget_name']} glowed {nugget.glow}. "
        f"{helper.id} leaned close and whispered that the nugget looked too bright to keep alone."
    )

    world.para()
    helper.memes["worry"] += 1
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} did not rush. {detective.id} was a careful detective, and {detective.id} knew space adventures went better when friends shared."
    )
    world.say(
        f'{helper.id} said, "If you keep the nugget, I will only worry. If we share it, I can hold the map light."'
    )
    detective.memes["sharing"] += 1

    propagate(world, narrate=True)

    world.para()
    world.say(
        f'{detective.id} smiled and {share.verb} the nugget with {helper.id}. '
        f"{share.ending} {scene.ending_image}"
    )
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    helper.meters["held"] += 1
    nugget.meters["shared"] += 1
    temple.meters["explored"] += 1


SCENES = {
    "moon": SceneConfig(
        id="moon",
        title="a moon temple",
        temple="the moon temple",
        dark_place="the long shadow corridor",
        travel="across the silver dust",
        ending_image="The nugget lit their path as they walked out together under the stars.",
    ),
    "ruins": SceneConfig(
        id="ruins",
        title="a starlit ruin temple",
        temple="the starlit ruin temple",
        dark_place="the narrow echo chamber",
        travel="through the quiet dust",
        ending_image="Its glow made the carved walls shine like a tiny sunrise.",
    ),
    "comet": SceneConfig(
        id="comet",
        title="a comet temple",
        temple="the comet temple",
        dark_place="the shadow bridge",
        travel="past the shimmering rocks",
        ending_image="They left with the nugget between them, bright as a kindly star.",
    ),
}

NUGGETS = {
    "gold": NuggetConfig(id="gold", label="gold nugget", glow="softly like a lantern", value=5, tags={"gold", "treasure"}),
    "amber": NuggetConfig(id="amber", label="amber nugget", glow="warm and honey-bright", value=3, tags={"amber", "treasure"}),
    "star": NuggetConfig(id="star", label="star nugget", glow="like a tiny star", value=4, tags={"star", "treasure"}),
}

SHARES = {
    "split": ShareConfig(
        id="split",
        verb="shared",
        benefit="It gave both of them a way to see.",
        calm_gain=1,
        joy_gain=2,
        text="The detective held the nugget up high while the helper held the map light, and the temple path became easy to read.",
        ending="They could both see the symbols now.",
        tags={"sharing"},
    ),
    "pass": ShareConfig(
        id="pass",
        verb="passed",
        benefit="It helped the helper feel trusted.",
        calm_gain=2,
        joy_gain=1,
        text="The detective passed the nugget to the helper for a while, and the helper steadied the little map beam with a happy grin.",
        ending="Trust warmed the cold hall like a tiny heater.",
        tags={"sharing"},
    ),
    "together": ShareConfig(
        id="together",
        verb="shared",
        benefit="It turned the search into a team mission.",
        calm_gain=2,
        joy_gain=2,
        text="They decided to share the nugget by holding it together, and its light shone steady between their hands.",
        ending="The two friends moved as one bright team.",
        tags={"sharing"},
    ),
}

HELPER_TYPES = ["alien_boy", "alien_girl", "boy", "girl"]
NAMES = ["Nova", "Pip", "Milo", "Iris", "Zuri", "Kian", "Luna", "Bex"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SCENES:
        for n in NUGGETS:
            for sh in SHARES:
                out.append((s, n, sh))
    return out


def reasonableness_ok(scene: SceneConfig, nugget: NuggetConfig, share: ShareConfig) -> bool:
    return nugget.shareable and "sharing" in share.tags


def explain_rejection(scene: SceneConfig, nugget: NuggetConfig, share: ShareConfig) -> str:
    if not nugget.shareable:
        return f"(No story: {nugget.label} cannot be shared safely in this world.)"
    return f"(No story: this combination does not support the sharing theme.)"


def pick_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene_key = args.scene or rng.choice(list(SCENES))
    nugget_key = args.nugget or rng.choice(list(NUGGETS))
    share_key = args.share or rng.choice(list(SHARES))
    if not reasonableness_ok(SCENES[scene_key], NUGGETS[nugget_key], SHARES[share_key]):
        raise StoryError(explain_rejection(SCENES[scene_key], NUGGETS[nugget_key], SHARES[share_key]))
    detective_name = args.detective_name or pick_name(rng)
    helper_name = args.helper_name or pick_name(rng)
    if helper_name == detective_name:
        helper_name = pick_name(rng)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    seeker_kind = "space detective"
    return StoryParams(
        scene=scene_key,
        detective_name=detective_name,
        helper_name=helper_name,
        helper_type=helper_type,
        temple_kind="temple",
        nugget_kind=nugget_key,
        share_kind=share_key,
        seeker_kind=seeker_kind,
    )


def tell(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    nugget = NUGGETS[params.nugget_kind]
    share = SHARES[params.share_kind]
    world = World()
    detective = world.add(Entity(id=params.detective_name, kind="character", type="detective", role="lead"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    temple = world.add(Entity(id="temple", kind="thing", type="temple", label=scene.title, role="place"))
    nug = world.add(Entity(id="nugget", kind="thing", type="nugget", label=nugget.label, role="treasure", tags=set(nugget.tags)))
    world.facts.update(
        scene=scene,
        nugget=nugget,
        share=share,
        detective=detective,
        helper=helper,
        temple=temple,
        nugget_name=nugget.label,
    )
    build_story(world, scene, nugget, share)
    world.facts["outcome"] = "shared" if nug.meters["shared"] >= THRESHOLD else "not_shared"
    world.facts["helper_calm"] = helper.memes["worry"] < THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story that includes the words "temple", "nugget", and "detective", and shows sharing between {f["detective"].id} and {f["helper"].id}.',
        f"Tell a child-friendly story where a detective finds a glowing nugget in a temple and chooses to share it with a friend.",
        f"Write a short space adventure about a temple treasure being shared so the team can explore safely together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    share = f["share"]
    nugget = f["nugget"]
    scene = f["scene"]
    return [
        ("Who is the story about?",
         f"It is about {det.id}, a detective, and {helper.id}, who explored a temple together."),
        ("What did the detective find?",
         f"{det.id} found a {nugget.label} inside the temple, and it glowed in the dark hall."),
        ("What changed when they shared?",
         f"Once they shared the nugget, {helper.id} became calmer and both friends could see the path clearly. "
         f"Sharing turned the search into a team adventure."),
        ("How did the story end?",
         f"It ended with the nugget helping both of them travel safely out of {scene.temple}. "
         f"The ending image shows that sharing made the adventure brighter."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a temple?",
         "A temple is an old building where people may go to pray, explore, or look at carved stones in stories."),
        ("What is a nugget?",
         "A nugget is a small piece of something valuable, like gold or a glowing treasure in a story."),
        ("What does a detective do?",
         "A detective looks for clues and solves mysteries by noticing small details."),
        ("What does sharing mean?",
         "Sharing means letting someone else use, hold, or enjoy something too, so more than one person benefits."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.tags:
            parts.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
scene(S) :- scene_fact(S).
nugget(N) :- nugget_fact(N).
share(X) :- share_fact(X).
valid(S,N,X) :- scene(S), nugget(N), share(X).
shared :- nugget_shared.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene_fact", s))
    for n in NUGGETS:
        lines.append(asp.fact("nugget_fact", n))
        if NUGGETS[n].shareable:
            lines.append(asp.fact("nugget_shareable", n))
    for x in SHARES:
        lines.append(asp.fact("share_fact", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, nugget=None, share=None, detective_name=None, helper_name=None, helper_type=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify complete.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with temple, nugget, detective, and sharing.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--nugget", choices=NUGGETS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.nugget_kind not in NUGGETS or params.share_kind not in SHARES:
        raise StoryError("Invalid story parameters.")
    if not reasonableness_ok(SCENES[params.scene], NUGGETS[params.nugget_kind], SHARES[params.share_kind]):
        raise StoryError("This combination does not support a reasonable sharing story.")
    world = tell(params)
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
        for s, n, x in asp_valid_combos():
            print(f"  {s:8} {n:8} {x}")
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(scene=s, detective_name="Nova", helper_name="Pip", helper_type="alien_boy", temple_kind="temple", nugget_kind=n, share_kind=x, seeker_kind="space detective")
            for s, n, x in valid_combos()
        ]
        samples = [generate(p) for p in params_list[:5]]
    else:
        seen = set()
        while len(samples) < args.n:
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
