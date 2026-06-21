#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jazz_bifocal_sound_effects_mystery.py
======================================================================

A small storyworld for a child-facing mystery with jazz, bifocal glasses,
and sound-effect narration. The premise is simple: someone misplaces an object
during a jazz rehearsal, a keen observer notices clues through bifocals, and a
careful investigation leads to a gentle reveal.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-chaining simulation, a Python reasonableness gate, and an inline ASP
twin for parity checks.
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
CLUE_THRESHOLD = 1.0
WORD_JAZZ = "jazz"
WORD_BIFOCAL = "bifocal"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "detective"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    sound: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    location: str
    searchable: bool = True
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
class ClueTool:
    id: str
    label: str
    phrase: str
    helps: str
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
class MysteryBeat:
    id: str
    clue_need: int
    reveal_text: str
    fail_text: str
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


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["heard"] < THRESHOLD:
            continue
        sig = ("attention", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["curiosity"] += 1
        out.append("")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["clue"] < CLUE_THRESHOLD:
            continue
        sig = ("clue", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("detective").memes["confidence"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("attention", _r_attention), Rule("clue", _r_clue)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True


def suspicion_check(setting: Setting, beat: MysteryBeat, obj: ObjectCfg, tool: ClueTool) -> bool:
    return bool(setting.place and obj.searchable and tool.helps and beat.clue_need >= 1)


def likely_solution(beat: MysteryBeat) -> bool:
    return beat.clue_need >= 1


def predict_clue(world: World, obj_id: str) -> dict:
    sim = world.copy()
    sim.get(obj_id).meters["clue"] += 1
    propagate(sim)
    return {"clue": sim.get(obj_id).meters["clue"], "confidence": sim.get("detective").memes["confidence"]}


def setup_scene(world: World, setting: Setting, detective: Entity, musician: Entity) -> None:
    world.say(
        f"At {setting.place}, the air felt quiet even though {setting.sound} drifted from the stage."
        f" {setting.detail}"
    )
    world.say(
        f"{detective.id} wore {detective.pronoun('possessive')} {detective.attrs.get('glasses', 'glasses')}, "
        f"and {musician.id} tapped a drumstick to keep time."
    )


def missing_item(world: World, obj: ObjectCfg, musician: Entity) -> None:
    world.say(
        f"Then came a tiny shock: {obj.phrase} was gone. {musician.id} looked under chairs, behind amps, "
        f"and even beside the piano."
    )


def sound_effect(world: World, text: str) -> None:
    world.say(text)


def inspect_with_bifocals(world: World, detective: Entity, obj: ObjectCfg, tool: ClueTool) -> None:
    detective.meters["heard"] += 1
    detective.memes["care"] += 1
    world.say(
        f"{detective.id} tipped {detective.pronoun('possessive')} bifocal glasses down and peered carefully."
        f" {tool.phrase} helped {detective.pronoun()} notice small things near {obj.location}."
    )


def find_clue(world: World, obj: ObjectCfg) -> None:
    target = world.get(obj.id)
    target.meters["clue"] += 1
    world.say(f"Snip! {obj.label.capitalize()}! There it was: a little clue tucked near {obj.location}.")


def reveal(world: World, beat: MysteryBeat, musician: Entity, detective: Entity, obj: ObjectCfg) -> None:
    world.say(beat.reveal_text.format(obj=obj.label, musician=musician.id, detective=detective.id))
    musician.memes["relief"] += 1
    detective.memes["pride"] += 1


def end_image(world: World, setting: Setting) -> None:
    world.say(
        f"By the last note of the jazz tune, the room felt calm again, and the missing thing was back where it belonged."
    )


def tell(setting: Setting, detective_name: str, musician_name: str, obj: ObjectCfg,
         tool: ClueTool, beat: MysteryBeat) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", label="the detective",
                                 role="sleuth", attrs={"glasses": "bifocal glasses"}))
    musician = world.add(Entity(id=musician_name, kind="character", type="person", label="the musician",
                                role="music", attrs={"instrument": "drum"}))
    missing = world.add(Entity(id=obj.id, kind="thing", type="object", label=obj.label, attrs={"location": obj.location}))

    setup_scene(world, setting, detective, musician)
    world.para()
    missing_item(world, obj, musician)
    sound_effect(world, "Clink! Tap-tap! Shuffle-shuffle!")
    inspect_with_bifocals(world, detective, obj, tool)
    pred = predict_clue(world, obj.id)
    world.facts["predicted"] = pred

    if not suspicion_check(setting, beat, obj, tool):
        raise StoryError("This mystery setup is too thin to support a clue-driven story.")

    world.para()
    find_clue(world, obj)
    sound_effect(world, "Whoop! Click!")
    reveal(world, beat, musician, detective, obj)
    end_image(world, setting)

    world.facts.update(
        setting=setting,
        detective=detective,
        musician=musician,
        object=obj,
        tool=tool,
        beat=beat,
        solved=True,
    )
    return world


SETTINGS = {
    "club": Setting(
        id="club",
        place="the little jazz club",
        detail="A red curtain hung by the bandstand, and a saxophone case waited by the wall.",
        sound="soft jazz",
        tags={"jazz", "club"},
    ),
    "hall": Setting(
        id="hall",
        place="the old concert hall",
        detail="Dusty seats pointed toward the stage, and every footstep sounded very loud.",
        sound="a jazzy drum beat",
        tags={"jazz", "hall"},
    ),
}

OBJECTS = {
    "sheet": ObjectCfg(
        id="sheet",
        label="music sheet",
        phrase="the music sheet with the lead melody",
        location="the piano bench",
        searchable=True,
        tags={"music", "sheet"},
    ),
    "hat": ObjectCfg(
        id="hat",
        label="hat",
        phrase="the sparkly hat from the show",
        location="near the trumpet stand",
        searchable=True,
        tags={"hat"},
    ),
}

TOOLS = {
    "bifocals": ClueTool(
        id="bifocals",
        label="bifocal glasses",
        phrase="The bifocal glasses were made for looking near and far.",
        helps="careful seeing",
        tags={"bifocal"},
    ),
    "magnifier": ClueTool(
        id="magnifier",
        label="magnifying glass",
        phrase="The magnifying glass shone in the stage lights.",
        helps="careful seeing",
        tags={"clue"},
    ),
}

BEATS = {
    "lost_sheet": MysteryBeat(
        id="lost_sheet",
        clue_need=1,
        reveal_text="The missing {obj} had slipped under the bench when {musician} laughed at {detective}'s joke.",
        fail_text="The room stayed puzzling and no clue made sense.",
        tags={"mystery", "jazz"},
    ),
    "missing_hat": MysteryBeat(
        id="missing_hat",
        clue_need=1,
        reveal_text="The {obj} had been hanging on the back of a chair all along, and {musician} grinned at the clever mistake.",
        fail_text="The clue trail vanished into the crowd.",
        tags={"mystery"},
    ),
}


@dataclass
class StoryParams:
    setting: str = "club"
    object: str = "sheet"
    tool: str = "bifocals"
    beat: str = "lost_sheet"
    detective_name: str = "June"
    musician_name: str = "Milo"
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OBJECTS:
            for t in TOOLS:
                for b in BEATS:
                    if suspicion_check(SETTINGS[s], BEATS[b], OBJECTS[o], TOOLS[t]):
                        combos.append((s, o, t, b))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A jazz mystery with sound effects and bifocal clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--detective")
    ap.add_argument("--musician")
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
              and (args.object is None or c[1] == args.object)
              and (args.tool is None or c[2] == args.tool)
              and (args.beat is None or c[3] == args.beat)]
    if not combos:
        raise StoryError("No valid mystery setup matches the given options.")
    s, o, t, b = rng.choice(sorted(combos))
    return StoryParams(
        setting=s,
        object=o,
        tool=t,
        beat=b,
        detective_name=args.detective or rng.choice(["June", "Nina", "Rae", "Mina"]),
        musician_name=args.musician or rng.choice(["Milo", "Theo", "Luca", "Arlo"]),
        seed=None,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short mystery story for a young child that includes {WORD_JAZZ} and {WORD_BIFOCAL}.",
        f"Tell a story about a missing object at a {f['setting'].place} where a detective uses {WORD_BIFOCAL} to solve the puzzle.",
        f"Write a gentle mystery with sound effects, jazz music, and a clear clue that leads to a happy reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    musician = f["musician"]
    obj = f["object"]
    tool = f["tool"]
    qa = [
        ("Who solved the mystery?",
         f"{detective.id} solved it by looking carefully and noticing the clue with {tool.label}."),
        ("What was missing?",
         f"{obj.phrase} was missing at first, which is why everyone looked so hard."),
        ("Why did the detective use bifocal glasses?",
         "Because bifocal glasses help someone look near and far with care. That made it easier to spot the small clue hiding by the stage."),
    ]
    if f.get("solved"):
        qa.append((
            "How did the mystery end?",
            f"It ended happily when the missing {obj.label} was found and the room felt calm again. The jazz tune could finish because the puzzle was solved."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is jazz?",
         "Jazz is a kind of music with lively rhythms and improvising sounds. It can feel bouncy, smooth, or a little mysterious."),
        ("What are bifocal glasses?",
         "Bifocal glasses have two viewing areas so a person can see near things and far things more clearly. They are useful for careful looking."),
        ("What is a clue in a mystery?",
         "A clue is a small piece of information that helps solve a puzzle. Clues can be objects, sounds, or things someone notices."),
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
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for bid in BEATS:
        lines.append(asp.fact("beat", bid))
    lines.append(asp.fact("word", WORD_JAZZ))
    lines.append(asp.fact("word", WORD_BIFOCAL))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,T,B) :- setting(S), object(O), tool(T), beat(B), good(S,O,T,B).
good(S,O,T,B) :- setting(S), object(O), tool(T), beat(B).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(StoryParams())
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.object not in OBJECTS:
        raise StoryError("Invalid object.")
    if params.tool not in TOOLS:
        raise StoryError("Invalid tool.")
    if params.beat not in BEATS:
        raise StoryError("Invalid beat.")
    if not suspicion_check(SETTINGS[params.setting], BEATS[params.beat], OBJECTS[params.object], TOOLS[params.tool]):
        raise StoryError("That setup is too thin for a mystery story.")

    world = tell(
        SETTINGS[params.setting],
        params.detective_name,
        params.musician_name,
        OBJECTS[params.object],
        TOOLS[params.tool],
        BEATS[params.beat],
    )
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


CURATED = [
    StoryParams(setting="club", object="sheet", tool="bifocals", beat="lost_sheet", detective_name="June", musician_name="Milo"),
    StoryParams(setting="hall", object="hat", tool="magnifier", beat="missing_hat", detective_name="Rae", musician_name="Luca"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
