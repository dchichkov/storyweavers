#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/volcano_stilt_guy_rhyme_ghost_story.py
======================================================================

A small storyworld about a lonely night watcher, a spooky rhyme, and a ghostly
warning near a volcano path. The world is built from simulated state: a stilt-
walking guy hears a rhyme, spots a glow from the volcano, follows the signs,
and ends with a safer, brighter ending.

This world keeps the story child-facing, eerie-but-gentle, and rhythmic.
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
class Place:
    id: str
    label: str
    night: bool = True
    foggy: bool = False
    near_volcano: bool = False
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
class Prop:
    id: str
    label: str
    safe_light: bool = False
    helps_climb: bool = False
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
class PromptTheme:
    id: str
    opening: str
    eerie_detail: str
    rhyme_line1: str
    rhyme_line2: str
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
class StoryParams:
    theme: str = "moonpath"
    place: str = "black_path"
    prop: str = "lantern"
    helper: str = "ghost"
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_fear(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spook"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__fear__")
    return out


def _r_glow(world: World) -> list[str]:
    out = []
    if world.get("volcano").meters["glow"] < THRESHOLD:
        return out
    sig = ("glow", "volcano")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("path").meters["lit"] += 1
    out.append("__glow__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("glow", _r_glow)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def reasonablest_combo(theme: PromptTheme, place: Place, helper: Prop) -> bool:
    return place.near_volcano and helper.safe_light


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for pid, place in PLACES.items():
            for hid, helper in PROPS.items():
                if reasonablest_combo(THEMES[tid], place, helper):
                    combos.append((tid, pid, hid))
    return combos


def _do_spook(world: World, actor: Entity, helper: Entity, theme: PromptTheme) -> None:
    actor.meters["spook"] += 1
    helper.meters["spook"] += 1
    propagate(world, narrate=False)
    world.say(theme.rhyme_line1)


def _do_guide(world: World, helper: Entity, theme: PromptTheme) -> None:
    helper.memes["kindness"] += 1
    world.say(theme.rhyme_line2)


def _do_walk(world: World, guy: Entity) -> None:
    guy.meters["stride"] += 1
    if world.place.foggy:
        guy.meters["spook"] += 1


def tell(theme: PromptTheme, place: Place, prop: Prop) -> World:
    world = World(place)
    guy = world.add(Entity(id="Guy", kind="character", type="man", role="wanderer", label="guy"))
    ghost = world.add(Entity(id="Ghost", kind="character", type="thing", role="helper", label="ghost"))
    volcano = world.add(Entity(id="volcano", kind="thing", type="thing", label="volcano"))
    path = world.add(Entity(id="path", kind="thing", type="thing", label="path"))
    tool = world.add(Entity(id=prop.id, kind="thing", type="thing", label=prop.label))

    world.facts["theme"] = theme
    world.facts["place"] = place
    world.facts["prop"] = prop

    world.say(f"At {place.label}, a lone guy went walking late at night.")
    world.say(f"The air was hush and gray, and {theme.eerie_detail}.")
    world.say(f"He walked on stilts so he could cross the wet stones with care.")
    world.say(f"Then a ghost in the dark began to hum a little tune.")

    world.para()
    _do_walk(world, guy)
    _do_spook(world, ghost, guy, theme)
    world.say(f'"{theme.rhyme_line1}" the ghost sang, soft as snow.')
    world.say(f'"{theme.rhyme_line2}" it whispered, low.')

    world.para()
    volcano.meters["glow"] += 1
    world.say("Far off, the volcano gave a red, sleepy glow.")
    if place.near_volcano:
        world.say("The path looked tricky, but the safe light showed the way.")
    _do_guide(world, ghost, theme)
    world.say(f"The guy lifted the {prop.label} and held it steady.")

    world.para()
    path.meters["lit"] += 1
    guy.memes["relief"] += 1
    ghost.memes["pride"] += 1
    world.say(f"With the {prop.label}, the dark path brightened like a small star.")
    world.say(f"The guy stepped carefully, one stilt, then the other, without a slip.")
    world.say(theme.ending_image)

    world.facts.update(
        guy=guy,
        ghost=ghost,
        volcano=volcano,
        path=path,
        tool=tool,
        outcome="safe",
    )
    return world


THEMES = {
    "moonpath": PromptTheme(
        id="moonpath",
        opening="a moonlit path",
        eerie_detail="the fog curled around the stones like a sleepy ghost's scarf",
        rhyme_line1="From the black path, the ghostly rhyme came slow and low",
        rhyme_line2="Keep your feet on the stilted beat, and do not go",
        ending_image="At the end, the volcano glowed far away while the path stayed bright and safe.",
    ),
    "ashwhisper": PromptTheme(
        id="ashwhisper",
        opening="an ash-silver trail",
        eerie_detail="thin ash dusted the ground like sugar from a ghost's hand",
        rhyme_line1="If the dark path shakes, the stilted step still knows the flow",
        rhyme_line2="Hold the light and mind the height, and down you go slow",
        ending_image="At the end, the volcano slept red in the distance, and the lantern made a warm little pool of light.",
    ),
    "echohollow": PromptTheme(
        id="echohollow",
        opening="an echoing road",
        eerie_detail="every little sound bounced back as if the hill itself could whisper",
        rhyme_line1="Stilt by stilt, don't tip, don't tilt, keep moving through the glow",
        rhyme_line2="If a ghost gives cheer to calm your fear, let the safe lamp show",
        ending_image="At the end, the guy smiled under the quiet sky, and the stilt steps went home in order.",
    ),
}

PLACES = {
    "black_path": Place(id="black_path", label="the black path", night=True, foggy=True, near_volcano=True),
    "ash_bridge": Place(id="ash_bridge", label="the ash bridge", night=True, foggy=False, near_volcano=True),
    "ridge_walk": Place(id="ridge_walk", label="the ridge walk", night=True, foggy=True, near_volcano=True),
}

PROPS = {
    "lantern": Prop(id="lantern", label="lantern", safe_light=True, tags={"light"}),
    "glowstone": Prop(id="glowstone", label="glowstone", safe_light=True, tags={"light", "glow"}),
    "beacon": Prop(id="beacon", label="tiny beacon", safe_light=True, tags={"light"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story rhyme world with a volcano, stilts, and a guy.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
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
              if (args.theme is None or c[0] == args.theme)
              and (args.place is None or c[1] == args.place)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, place, prop = rng.choice(sorted(combos))
    return StoryParams(theme=theme, place=place, prop=prop)


def story_qa(world: World) -> list[QAItem]:
    theme: PromptTheme = world.facts["theme"]
    prop: Prop = world.facts["prop"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about a guy who walks on stilts at night, with a ghost nearby and a volcano in the distance.",
        ),
        QAItem(
            question="What did the ghost do?",
            answer=f"The ghost sang a spooky rhyme and guided the guy with a {prop.label}. That made the dark path feel safer.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the volcano glowing far away and the path staying bright and safe. The guy kept his balance and went on carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a volcano?",
            answer="A volcano is a mountain that can sometimes glow hot or erupt. Even when it is quiet, it can look scary at night.",
        ),
        QAItem(
            question="What are stilts?",
            answer="Stilts are tall poles you stand on to walk higher off the ground. You need careful steps and good balance to use them.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale that feels spooky or mysterious, but it can still end safely. The best ones are eerie without being too scary.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    theme: PromptTheme = world.facts["theme"]
    return [
        f'Write a gentle ghost story with rhyme that includes the words "volcano", "stilt", and "guy".',
        f"Tell a spooky-but-kind story where a guy on stilts hears a ghost rhyme near a volcano and reaches safety.",
        f'Write a child-friendly rhyming story in a ghost-story style about {theme.opening}.',
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.place not in PLACES or params.prop not in PROPS:
        raise StoryError("Invalid params for this storyworld.")
    theme = THEMES[params.theme]
    place = PLACES[params.place]
    prop = PROPS[params.prop]
    if not reasonablest_combo(theme, place, prop):
        raise StoryError("(The selected combination cannot support a safe ghost story.)")
    world = tell(theme, place, prop)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(T, P, R) :- theme(T), place(P), prop(R), near_volcano(P), safe_light(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for p, place in PLACES.items():
        lines.append(asp.fact("place", p))
        if place.near_volcano:
            lines.append(asp.fact("near_volcano", p))
    for r, prop in PROPS.items():
        lines.append(asp.fact("prop", r))
        if prop.safe_light:
            lines.append(asp.fact("safe_light", r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(valid_combos_asp()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    try:
        sample = generate(StoryParams(theme="moonpath", place="black_path", prop="lantern"))
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP matches Python ({len(valid_combos())} combos) and generate() works.")
    return 0


CURATED = [
    StoryParams(theme="moonpath", place="black_path", prop="lantern"),
    StoryParams(theme="ashwhisper", place="ash_bridge", prop="glowstone"),
    StoryParams(theme="echohollow", place="ridge_walk", prop="beacon"),
]


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos_asp()
        print(f"{len(combos)} compatible (theme, place, prop) combos:\n")
        for t, p, r in combos:
            print(f"  {t:10} {p:12} {r}")
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
