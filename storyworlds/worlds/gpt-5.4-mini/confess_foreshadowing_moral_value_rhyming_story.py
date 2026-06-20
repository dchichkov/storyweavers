#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/confess_foreshadowing_moral_value_rhyming_story.py
===================================================================================

A standalone storyworld for a small rhyming moral tale: a child breaks or loses
something, notices a foreshadowing clue, feels the tug to hide it, then confesses
and makes it right.

The domain is deliberately tiny and classical:
- typed entities with meters and memes
- a causal turn from secret-keeping to confession
- a moral value ending that proves what changed
- light rhyming prose with a recurring refrain

The seed words were: confess.
Features requested: Foreshadowing, Moral Value.
Style requested: Rhyming Story.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/confess_foreshadowing_moral_value_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/confess_foreshadowing_moral_value_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/confess_foreshadowing_moral_value_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/confess_foreshadowing_moral_value_rhyming_story.py --verify
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
MORAL_MIN = 1.0


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
class Scene:
    setting: str
    place: str
    thing: str
    rhyme_word: str
    warning_clue: str
    broken_phrase: str
    made_right: str
    moral: str
    refrain: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_weight(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.memes["worry"] < THRESHOLD:
            continue
        sig = ("weight", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["guilt"] += 1
        out.append("")
    return out


def _r_confess(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.memes["guilt"] < THRESHOLD or child.memes["honesty"] < THRESHOLD:
            continue
        sig = ("confess", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["brave_truth"] += 1
        out.append("")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("weight", "social", _r_weight),
    Rule("confess", "social", _r_confess),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        if scene.thing:
            combos.append((sid, "tell"))
            combos.append((sid, "hide"))
    return combos


def reasonableness(scene: Scene) -> bool:
    return bool(scene.warning_clue and scene.broken_phrase and scene.made_right)


def foreshadow(world: World, child: Entity, scene: Scene) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Before the trouble, a small clue gave a hush: {scene.warning_clue}. "
        f"It glimmered like a nudge, a tiny sign in the brush."
    )


def break_thing(world: World, child: Entity, scene: Scene) -> None:
    child.meters["damage"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} made a sudden slip and heard a little clatter. "
        f"{scene.broken_phrase}, and the room went still -- what mattered?"
    )


def hide_truth(world: World, child: Entity, parent: Entity, scene: Scene) -> None:
    child.memes["secret"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} thought, \"I'll keep it quiet, neat and slick.\" "
        f"But secrets pinch the heart, and soon the chest felt thick."
    )


def confess(world: World, child: Entity, parent: Entity, scene: Scene) -> None:
    child.memes["honesty"] += 1
    child.memes["relief"] += 1
    world.say(
        f"At last {child.id} walked to {parent.label_word} and said, \"I must confess. "
        f"I broke {scene.thing} by mistake; I did not act my best.\""
    )
    world.say(
        f"{parent.label_word.capitalize()} took a breath, then answered soft and kind, "
        f"\"A truth told now is worth more than a secret left behind.\""
    )


def repair(world: World, child: Entity, parent: Entity, scene: Scene) -> None:
    child.memes["moral"] += 1
    child.meters["repair"] += 1
    world.say(
        f"Together they {scene.made_right}, then wiped the floor with care. "
        f"The worry shrank; the house felt bright, with love still in the air."
    )
    world.say(
        f"And {scene.moral} was the lesson as the moon climbed up so high: "
        f"{scene.refrain}"
    )


def tell(scene: Scene, child_name: str = "Nora", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["young"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              role="parent", label="the parent"))
    child.memes["honesty"] = 1.0
    world.facts["scene"] = scene
    world.facts["child"] = child
    world.facts["parent"] = parent

    world.say(
        f"One evening in {scene.setting}, {child.id} was near {scene.place}, "
        f"and the air was sweet with a rhyming tune."
    )
    world.say(
        f"{child.id} loved the little game of step and skip and spin, "
        f"but the day had a whisper hidden underneath the grin."
    )
    world.para()
    foreshadow(world, child, scene)
    hide_truth(world, child, parent, scene)
    break_thing(world, child, scene)
    propagate(world, narrate=False)
    world.para()
    confess(world, child, parent, scene)
    repair(world, child, parent, scene)
    return world


SCENES = {
    "jar": Scene(
        setting="the kitchen after supper",
        place="the windowsill",
        thing="Grandma's honey jar",
        rhyme_word="sparkle",
        warning_clue="the jar wobbled by the edge like it might dance away",
        broken_phrase="The jar gave a pop and spilled a golden stream",
        made_right="swept up the shards and poured the honey into a new clean bowl",
        moral="the bold value",
        refrain="Honest hearts mend trouble smart; truth can lighten any part.",
    ),
    "kite": Scene(
        setting="the yard at dusk",
        place="the fence post",
        thing="little red kite",
        rhyme_word="flutter",
        warning_clue="the string tugged loose like a ribbon in a breeze",
        broken_phrase="The kite snagged, fluttered down, and the paper tore apart",
        made_right="glued the rip and tied the string once more with care",
        moral="the kind value",
        refrain="Tell the truth and face the tune; shared repair will fix the moon.",
    ),
    "lamp": Scene(
        setting="the hallway before bed",
        place="the table corner",
        thing="the glass lamp",
        rhyme_word="shimmer",
        warning_clue="the lamp leaned close as a sleepy cloud",
        broken_phrase="The lamp tipped, tapped the floor, and gave a tiny crack",
        made_right="carefully cleaned the glass and set the lamp back straight",
        moral="the wise value",
        refrain="Truth comes first, then loving hands; honesty helps mended plans.",
    ),
}


@dataclass
@dataclass
class StoryParams:
    scene: str
    child_name: str
    child_gender: str
    parent_type: str
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


GIRL_NAMES = ["Nora", "Maya", "Lila", "Iris", "Mina", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Ezra", "Theo", "Owen", "Miles", "Finn", "Leo", "Noah", "Ben"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    child: Entity = f["child"]
    return [
        f'Write a rhyming story for a child that includes the word "confess" and '
        f"teaches that telling the truth is brave.",
        f"Tell a gentle moral story where {child.id} notices {scene.warning_clue}, "
        f"makes a mistake, and later says confess to {child.pronoun('possessive')} {f['parent'].label_word}.",
        f"Write a foreshadowing story in rhyme about {scene.thing} where the clue "
        f"comes first and the lesson comes last.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    return [
        ("What did the small clue do in the story?",
         f"It foreshadowed the trouble by hinting that something might go wrong. "
         f"That made the later mistake feel expected instead of sudden."),
        ("Why did {0} feel worried before confessing?".format(child.id),
         f"{child.id} felt worried because the mistake was hidden and the secret grew heavy. "
         f"Once the truth was spoken, the worry changed into relief."),
        (f"What did {child.id} do at the end?",
         f"{child.id} confessed to {parent.label_word} and helped make things right. "
         f"That choice showed the moral value of honesty."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    return [
        ("What is foreshadowing in a story?",
         "Foreshadowing is a clue that hints something may happen later. "
         "It helps the reader notice the shape of the story before the turn."),
        ("What does confess mean?",
         "To confess means to admit the truth, especially after a mistake. "
         "It is often hard, but it can lead to help and forgiveness."),
        ("What is a moral value?",
         "A moral value is a lesson about how to act kindly and wisely. "
         "Stories often end by showing that value in the character's choice."),
        (f"Why was the {scene.thing} important?",
         f"It was the special object that changed during the story. "
         f"Because it broke, the child had to decide whether to hide the mistake or confess."),
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


CURATED = [
    StoryParams("jar", "Nora", "girl", "mother"),
    StoryParams("kite", "Ezra", "boy", "father"),
    StoryParams("lamp", "Maya", "girl", "mother"),
]


def valid_story(params: StoryParams) -> bool:
    return params.scene in SCENES and params.child_gender in {"girl", "boy"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.scene not in SCENES:
        raise StoryError("(No story: unknown scene.)")
    scene_id = args.scene or rng.choice(sorted(SCENES))
    scene = SCENES[scene_id]
    if not reasonableness(scene):
        raise StoryError("(No story: scene is missing required structure.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
    else:
        name = args.name or rng.choice(BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene_id, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], params.child_name, params.child_gender, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
scene(scene1).
confessable(S) :- scene(S).
moral_value(S) :- scene(S).
foreshadowing(S) :- scene(S).
valid(S) :- scene(S), confessable(S), moral_value(S), foreshadowing(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/1."))
    return sorted(s for (s,) in asp.atoms(model, "valid"))


def asp_verify() -> int:
    rc = 0
    py = {sid for sid in SCENES}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches scene registry ({len(py)} scenes).")
    else:
        rc = 1
        print("MISMATCH in ASP scene validity:")
        print("  python:", sorted(py))
        print("  clingo:", sorted(cl))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-tested normal generation.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming moral storyworld: confess, foreshadowing, and a lesson in truth."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid scenes: " + ", ".join(asp_valid_combos()))
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
            header = f"### {p.child_name}: scene={p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
