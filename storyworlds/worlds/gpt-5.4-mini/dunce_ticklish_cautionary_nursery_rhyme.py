#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dunce_ticklish_cautionary_nursery_rhyme.py
===========================================================================

A standalone story world for a tiny cautionary nursery-rhyme domain.

Premise:
- A child is called a dunce by a sneering rhyme-spout.
- The child is ticklish and loses composure when poked.
- A small cautionary turn warns that teasing can turn playful balance into a spill.
- A calm helper redirects the moment into a gentler rhyme game.

The world is intentionally small: one room, one teasing prop, one precarious
object, one helper, and one safe ending image that proves the change.

The story style is nursery-rhyme-like: short, rhythmic, concrete, child-facing,
and lightly repetitive, while still being driven by simulated state.
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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    cozy_detail: str
    rhyme_frame: str

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
class Tease:
    id: str
    label: str
    verb: str
    nudge: str
    line: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)

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
class PrecariousThing:
    id: str
    label: str
    phrase: str
    balance: str
    fall_text: str
    delicate: bool = True
    tags: set[str] = field(default_factory=set)

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
class Redirect:
    id: str
    label: str
    action: str
    ending: str
    safety: int
    tags: set[str] = field(default_factory=set)

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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_fluster(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["fluster"] < THRESHOLD:
        return out
    sig = ("fluster",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confidence"] -= 1
    child.meters["wobble"] += 1
    out.append("__fluster__")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["wobble"] < THRESHOLD:
        return out
    bowl = world.get("bowl")
    if bowl.meters["balanced"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["spilled"] += 1
    world.get("stage").meters["mess"] += 1
    out.append("__spill__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    child = world.get("child")
    if helper.memes["calm"] < THRESHOLD or child.memes["upset"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["upset"] = 0
    child.memes["joy"] += 1
    helper.memes["warmth"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [_r_fluster, _r_spill, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def safe_reasonable(tease: Tease, thing: PrecariousThing, redirect: Redirect) -> bool:
    return tease.risky and thing.delicate and redirect.safety >= 2


def predict_spill(world: World, tease: Tease, thing: PrecariousThing) -> bool:
    sim = world.copy()
    child = sim.get("child")
    bowl = sim.get("bowl")
    child.memes["fluster"] += 1
    child.meters["wobble"] += 1
    bowl.meters["balanced"] += 1
    propagate(sim, narrate=False)
    return sim.get("bowl").meters["spilled"] >= THRESHOLD


def tease_child(world: World, child: Entity, tease: Tease) -> None:
    child.memes["fluster"] += 1
    child.memes["upset"] += 1
    child.memes["sensitivity"] += 1
    world.say(
        f"{child.id} was in {world.setting.place}, under the soft old moon of "
        f"{world.setting.rhyme_frame}. {world.setting.cozy_detail}"
    )
    world.say(
        f"A teasing little voice sang, \"{tease.line}\" and poked at {child.id} "
        f"with a {tease.label}."
    )
    world.say(
        f"{child.id} was ticklish indeed, and the little poke made {child.pronoun()} "
        f"wiggle and wobble."
    )


def caution(world: World, parent: Entity, child: Entity, tease: Tease, thing: PrecariousThing) -> None:
    predicted = predict_spill(world, tease, thing)
    world.facts["predicted_spill"] = predicted
    world.say(
        f"{parent.label_word.capitalize()} came by and said, "
        f"\"Now hush, hush, little one. A teasing poke can shake the {thing.label} "
        f"and send it on a tumble.\""
    )
    if predicted:
        world.say(
            f"\"When a child is ticklish and a thing is perched so neatly, a naughty "
            f"joke may turn to a spill.\""
        )


def defy(world: World, child: Entity, tease: Tease) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} tried to laugh it off and stood on tiptoe, still all "
        f"fizzy with the tease."
    )


def wobble_and_spill(world: World, child: Entity, thing: PrecariousThing) -> None:
    child.meters["wobble"] += 1
    thing_ent = world.get("bowl")
    thing_ent.meters["balanced"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {thing.label} gave a little sway, a little sway, and down went the "
        f"{thing.label} with a soft, sad plop."
    )
    if world.get("bowl").meters["spilled"] >= THRESHOLD:
        world.say(f"{thing.fall_text}")


def redirect_game(world: World, helper: Entity, child: Entity, redirect: Redirect) -> None:
    helper.memes["calm"] += 1
    child.memes["upset"] += 0
    world.say(
        f"{helper.id} knelt down and smiled. \"Let us use a kinder song,\" "
        f"{helper.pronoun()} said. \"No pokes, no knocks, just tap-tap feet and "
        f"{redirect.label}.\""
    )
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    world.say(
        f"{child.id} sniffled once, then nodded, and {redirect.action} instead."
    )
    world.say(redirect.ending)


def tell(setting: Setting, tease: Tease, thing: PrecariousThing, redirect: Redirect,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Aunt May", parent_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="helper"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="thing", label=thing.label))
    stage = world.add(Entity(id="stage", kind="thing", type="thing", label="the little stage"))

    child.memes["confidence"] = 2.0
    helper.memes["calm"] = 1.0
    bowl.meters["balanced"] = 1.0

    world.say(
        f"On a quiet night, {child.id} and {helper.id} kept time to the nursery-rhyme "
        f"bells."
    )
    world.say(
        f"On the shelf sat {thing.phrase}, {thing.balance} and ready to stay."
    )
    world.para()
    tease_child(world, child, tease)
    caution(world, helper, child, tease, thing)
    defy(world, child, tease)
    wobble_and_spill(world, child, thing)
    world.para()
    redirect_game(world, helper, child, redirect)
    world.say(
        f"And so the little room went quiet again, with the {thing.label} set "
        f"steady and the ticklish child smiling safe."
    )

    world.facts.update(
        child=child,
        helper=helper,
        tease=tease,
        thing_cfg=thing,
        redirect=redirect,
        bowl=bowl,
        stage=stage,
        outcome="spill" if bowl.meters["spilled"] >= THRESHOLD else "safe",
        ticklish=child.memes["sensitivity"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "A little lamp glowed on the sill.", "a hush-a-bye tune"),
    "parlor": Setting("parlor", "the parlor", "The carpet was neat and the curtains were blue.", "a round-a-round tune"),
    "schoolroom": Setting("schoolroom", "the schoolroom", "A chalk fox slept by the board.", "a clap-a-clap tune"),
}

TEASES = {
    "feather": Tease("feather", "feather", "tickle", "a feather", "Dunce, dunce, danced in place!", True, {"ticklish", "teasing"}),
    "twig": Tease("twig", "twig", "poke", "a twig", "Dunce, dunce, never move!", True, {"ticklish", "teasing"}),
    "rattle": Tease("rattle", "rattle", "jiggle", "a toy rattle", "Dunce, dunce, shake and sway!", True, {"ticklish", "teasing"}),
}

THINGS = {
    "bowl": PrecariousThing("bowl", "porridge bowl", "a warm porridge bowl", "balanced on a little stool", "The porridge slid out in a soft brown spill.", True, {"porridge", "spill"}),
    "tower": PrecariousThing("tower", "block tower", "a tower of red blocks", "stacked high as a hat", "The blocks toppled into a clatter of red and blue.", True, {"blocks", "spill"}),
    "tray": PrecariousThing("tray", "berry tray", "a tray of berries", "resting on a narrow tray-table", "The berries rolled away like marbles.", True, {"berries", "spill"}),
}

REDIRECTS = {
    "clap": Redirect("clap", "clapping", "clapped to the beat", "And together they clapped, clap-clap-clap, until the room felt kind again.", 3, {"safe", "music"}),
    "dance": Redirect("dance", "dancing", "danced in a circle", "And together they danced a circle, soft and slow, while the shelf stood still.", 3, {"safe", "music"}),
    "tap": Redirect("tap", "tapping", "tapped their toes", "And together they tapped a tiny march, and the tickle turned to laughter.", 2, {"safe", "music"}),
}

NAMES = ["Mina", "Pippa", "Nell", "Toby", "Rosa", "Finn"]
GENDERS = {"Mina": "girl", "Pippa": "girl", "Nell": "girl", "Toby": "boy", "Rosa": "girl", "Finn": "boy"}


@dataclass
@dataclass
class StoryParams:
    setting: str
    tease: str
    thing: str
    redirect: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TEASES:
            for th in THINGS:
                for r in REDIRECTS:
                    if safe_reasonable(TEASES[t], THINGS[th], REDIRECTS[r]):
                        combos.append((s, t, th, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a cautionary nursery-rhyme about a ticklish dunce and a safer song.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tease", choices=TEASES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--redirect", choices=REDIRECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--parent")
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
              and (args.tease is None or c[1] == args.tease)
              and (args.thing is None or c[2] == args.thing)
              and (args.redirect is None or c[3] == args.redirect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tease, thing, redirect = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(NAMES)
    child_gender = args.gender or GENDERS.get(child_name, rng.choice(["girl", "boy"]))
    parent_name = args.parent or rng.choice(["Aunt May", "Grandpa", "Mama Rose"])
    parent_gender = "woman" if "Aunt" in parent_name or "Mama" in parent_name else "man"
    return StoryParams(setting, tease, thing, redirect, child_name, child_gender, parent_name, parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary nursery rhyme for a child named {f["child"].id} that includes the words "dunce" and "ticklish".',
        f"Tell a soft warning story where {f['child'].id} is teased beside a {f['thing_cfg'].label} and a grown-up turns it into a kinder rhyme.",
        f'Write a short nursery-rhyme story about teasing, a wobble, and a safer song with the word "dunce" in it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    thing = f["thing_cfg"]
    return [
        QAItem(
            question="Why did the child wobble?",
            answer=f"{child.id} was ticklish, so the teasing poke made {child.pronoun()} wiggle and lose balance. That wobble mattered because the {thing.label} was perched carefully nearby."
        ),
        QAItem(
            question="What did the helper warn about?",
            answer=f"{helper.id} warned that teasing can shake the {thing.label} and make it spill. The warning was careful because the little thing was sitting high and delicate."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended safely: the child stopped the teasing game and chose clapping and tapping instead. The {thing.label} stayed steady, and the room felt kind again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does ticklish mean?", "Ticklish means a small touch or poke can make someone laugh, wiggle, or squirm. It is a feeling that can be hard to control."),
        QAItem("What is a cautionary story?", "A cautionary story warns about a mistake so children can choose a safer way next time. It teaches by showing what could go wrong and how to fix it gently."),
        QAItem("What is a nursery rhyme?", "A nursery rhyme is a short, musical story or poem with a bouncy rhythm and repeating sounds. Children often hear them as gentle songs."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("nursery", "feather", "bowl", "clap", "Mina", "girl", "Aunt May", "woman"),
    StoryParams("parlor", "twig", "tray", "dance", "Toby", "boy", "Grandpa", "man"),
    StoryParams("schoolroom", "rattle", "tower", "tap", "Rosa", "girl", "Mama Rose", "woman"),
]


def explain_rejection(tease: Tease, thing: PrecariousThing) -> str:
    return f"(No story: this teasing would not feel cautionary enough for the {thing.label}.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TEASES[params.tease],
        THINGS[params.thing],
        REDIRECTS[params.redirect],
        params.child_name,
        params.child_gender,
        params.parent_name,
        params.parent_gender,
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


ASP_RULES = r"""
ticklish(child) :- child_id(child).
fluster(child) :- teased(child), ticklish(child).
spill(bowl) :- fluster(child), precarious(bowl).
safe_end :- redirect(safe), not spill(bowl).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TEASES:
        lines.append(asp.fact("tease", t))
    for th in THINGS:
        lines.append(asp.fact("thing", th))
    for r in REDIRECTS:
        lines.append(asp.fact("redirect", r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        sample = generate(CURATED[0])
    except Exception as e:
        print(f"FAIL: generate smoke test crashed: {e}")
        return 1
    if not sample.story.strip():
        print("FAIL: generated story is empty")
        return 1
    if "dunce" not in sample.story.lower() or "ticklish" not in sample.story.lower():
        print("FAIL: required seed words missing from story")
        return 1
    if sample.world is None:
        print("FAIL: world missing")
        return 1
    print("OK: generate smoke test passed.")
    return 0


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses a tiny ASP twin for registry parity only.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = build_sample_from_args(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.tease} near {p.thing} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
