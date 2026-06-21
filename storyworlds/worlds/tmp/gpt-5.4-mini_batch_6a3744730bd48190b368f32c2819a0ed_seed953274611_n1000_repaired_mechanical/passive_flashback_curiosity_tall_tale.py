#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/passive_flashback_curiosity_tall_tale.py
========================================================================

A standalone storyworld for a tiny Tall-Tale-style domain about a curious child,
a passive old creature, and a flashback that reveals how the child solves the
mystery without breaking the rules.

Seed promise
------------
- Word: passive
- Features: Flashback, Curiosity
- Style: Tall Tale

Premise
-------
A child in a wide-open meadow spots something strange: an old, passive donkey
won't budge from a shed door that seems to guard a hidden bell. The child keeps
asking questions, and a caretaker remembers a flashback to a stormy night long
ago. The remembered clue leads to a simple, sturdy fix, and the child ends the
day with a new story and a new trail.

This world uses:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- QA generated from world state, not rendered prose
- an inline ASP twin for parity checks
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandfather": "grandpa", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    sky: str
    detail: str
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
class Mystery:
    id: str
    label: str
    thing: str
    hidden: str
    clue: str
    risk: int
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
class Memory:
    id: str
    label: str
    flashback_line: str
    lesson: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setting: str
    mystery: str
    memory: str
    fix: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
    guide_role: str
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


def _r_curiosity(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["curiosity"] >= THRESHOLD and ("curious",) not in world.fired:
        world.fired.add(("curious",))
        child.memes["curiosity"] += 0.5
        out.append("__curious__")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    child = world.get("child")
    guide = world.get("guide")
    if child.memes["curiosity"] >= 2 and guide.memes["memory"] >= THRESHOLD and ("flashback",) not in world.fired:
        world.fired.add(("flashback",))
        guide.memes["memory"] += 1
        out.append("__flashback__")
    return out


def _r_discovery(world: World) -> list[str]:
    out = []
    mystery = world.get("mystery")
    if mystery.meters["revealed"] >= THRESHOLD and ("discovery",) not in world.fired:
        world.fired.add(("discovery",))
        world.get("child").memes["joy"] += 1
        out.append("__discovery__")
    return out


CAUSAL_RULES = [
    Rule("curiosity", "social", _r_curiosity),
    Rule("flashback", "memory", _r_flashback),
    Rule("discovery", "physical", _r_discovery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reason_ok(mystery: Mystery, fix: Fix) -> bool:
    return mystery.risk <= fix.power and fix.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            for fid, f in FIXES.items():
                if reason_ok(m, f):
                    combos.append((sid, mid, fid))
    return combos


def explore(world: World, setting: Setting, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"In {setting.place}, the wind went whisper-quiet and the day looked as wide "
        f"as a wagon road. {child.id} spotted {mystery.thing}, hanging there like it had "
        f"been waiting for a question."
    )
    world.say(
        f'"Why is {mystery.label} so still?" {child.id} asked, and asked again, because '
        f'curiosity was riding {child.pronoun("possessive")} heels.'
    )


def passivity(world: World, child: Entity, mystery: Mystery) -> None:
    mystery_obj = world.get("mystery")
    mystery_obj.meters["still"] += 1
    world.say(
        f"Even when {child.id} nudged and peered, {mystery.label} stayed passive, '
        f"as calm as an old fence post."
    )


def remember(world: World, guide: Entity, memory: Memory, mystery: Mystery) -> None:
    guide.memes["memory"] += 1
    world.say(
        f"{guide.id} scratched {guide.pronoun('possessive')} chin. Then a flashback "
        f"came knocking: {memory.flashback_line}"
    )
    world.say(
        f"{guide.id} remembered the lesson clear as moonlight: {memory.lesson}"
    )


def solve(world: World, guide: Entity, fix: Fix, mystery: Mystery) -> None:
    mystery_obj = world.get("mystery")
    mystery_obj.meters["revealed"] += 1
    world.say(
        f"{guide.id} tried {fix.text}, and the old mystery gave way at last. "
        f"The hidden thing was there all along."
    )


def fail_fix(world: World, guide: Entity, fix: Fix, mystery: Mystery) -> None:
    world.say(
        f"{guide.id} tried {fix.fail}, but the old puzzle held tight as a nail in hard wood."
    )


def finish(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"By sunset, {child.id} knew the answer: {mystery.hidden}. {child.id} walked home "
        f"with a grin big enough to shade the barn."
    )
    world.say(
        f"And because {mystery.label} had finally yielded, the meadow seemed larger, "
        f"friendlier, and ready for the next curiosity."
    )


def tell(setting: Setting, mystery: Mystery, memory: Memory, fix: Fix,
         child_name: str, child_gender: str, guide_name: str, guide_gender: str,
         guide_role: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                             role="curious_child"))
    guide = world.add(Entity(id="guide", kind="character", type=guide_gender, label=guide_name,
                             role=guide_role))
    mystery_ent = world.add(Entity(id="mystery", kind="thing", type="thing", label=mystery.label))
    child.id = child_name
    guide.id = guide_name
    world.entities = {child.id: child, guide.id: guide, "mystery": mystery_ent}
    child.memes["curiosity"] = 1
    guide.memes["memory"] = 1

    explore(world, setting, child, mystery)
    world.para()
    passivity(world, child, mystery)
    remember(world, guide, memory, mystery)
    world.para()
    if fix.sense >= 2 and mystery.risk <= fix.power:
        solve(world, guide, fix, mystery)
        finish(world, child, mystery)
    else:
        fail_fix(world, guide, fix, mystery)
    world.facts.update(child=child, guide=guide, mystery=mystery, memory=memory, fix=fix, setting=setting)
    return world


SETTINGS = {
    "meadow": Setting(id="meadow", place="the meadow", sky="blue", detail="the grass leaned like it was listening"),
    "barnyard": Setting(id="barnyard", place="the barnyard", sky="gold", detail="the boards creaked in the sun"),
    "riverbank": Setting(id="riverbank", place="the riverbank", sky="silver", detail="the water slid by like a long ribbon"),
}

MYSTERIES = {
    "bell": Mystery(id="bell", label="the old bell", thing="an old bell on a fence post", hidden="a silver bell buried in the seed bin", clue="it had a crack like a lightning smile", risk=1, tags={"passive"}),
    "donkey": Mystery(id="donkey", label="the passive donkey", thing="a passive donkey beside the shed", hidden="the donkey was guarding a trail to the creek", clue="it would not move until the right song was sung", risk=2, tags={"passive"}),
    "wagon": Mystery(id="wagon", label="the wagon wheel", thing="a wagon wheel sunk in the mud", hidden="a hidden path under the wheel", clue="the spokes pointed toward the hill", risk=2, tags={"passive"}),
}

MEMORIES = {
    "storm": Memory(id="storm", label="the storm", flashback_line="the night the rain came down like buckets and the fence line vanished", lesson="when the world hides a trail, old clues can point the way", tags={"flashback"}),
    "lantern": Memory(id="lantern", label="the lantern", flashback_line="the lantern glow on the porch showed a tiny track through the dark", lesson="a little light and a careful eye can find what was lost", tags={"flashback"}),
}

FIXES = {
    "song": Fix(id="song", sense=2, power=2, text="sing a low song and follow the donkey's ears", fail="hum a tune and hope for a miracle", qa_text="sing a low song and follow the donkey's ears"),
    "rope": Fix(id="rope", sense=3, power=3, text="loop a rope around the latch and pull the door open gently", fail="give the rope a wild yank", qa_text="loop a rope around the latch and pull the door open gently"),
    "crumbs": Fix(id="crumbs", sense=1, power=1, text="scatter crumbs and wait for the answer", fail="scatter crumbs and wait forever", qa_text="scatter crumbs and wait for the answer"),
}

GIRL_NAMES = ["Lena", "Mabel", "Ivy", "Rose", "Nell"]
BOY_NAMES = ["Jasper", "Tommy", "Eli", "Nate", "Hank"]


CURATED = [
    StoryParams(setting="meadow", mystery="donkey", memory="storm", fix="rope",
                child_name="Ivy", child_gender="girl", guide_name="Hank", guide_gender="boy",
                guide_role="uncle"),
    StoryParams(setting="riverbank", mystery="wagon", memory="lantern", fix="song",
                child_name="Jasper", child_gender="boy", guide_name="Rose", guide_gender="girl",
                guide_role="grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with curiosity and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", dest="guide_gender", choices=["girl", "boy"])
    ap.add_argument("--guide-role")
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    setting, mystery, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    guide = args.guide or rng.choice(GIRL_NAMES if guide_gender == "girl" else BOY_NAMES)
    guide_role = args.guide_role or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    memory = args.memory or rng.choice(sorted(MEMORIES))
    return StoryParams(setting=setting, mystery=mystery, memory=memory, fix=fix,
                       child_name=name, child_gender=gender, guide_name=guide,
                       guide_gender=guide_gender, guide_role=guide_role)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child who is full of curiosity and includes the word "passive".',
        f"Tell a story where {f['child'].label} keeps asking about {f['mystery'].label} and an older relative remembers a flashback.",
        "Write a story with a big, calm landscape, a curious question, and a flashback that reveals the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guide, mystery, memory, fix = f["child"], f["guide"], f["mystery"], f["memory"], f["fix"]
    return [
        QAItem(question="Who was curious in the story?",
               answer=f"{child.label} was curious. {child.label} kept asking questions until the mystery made room for an answer."),
        QAItem(question="What did the guide remember in the flashback?",
               answer=f"{guide.label} remembered {memory.flashback_line}. That flashback pointed to the right way to handle {mystery.label}."),
        QAItem(question="How was the mystery solved?",
               answer=f"They used {fix.qa_text}. That careful move matched the problem and let the hidden thing be found."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does passive mean?",
               answer="Passive means calm or still, not rushing around or fighting back. In stories, a passive thing often waits to be noticed."),
        QAItem(question="What is a flashback?",
               answer="A flashback is when a story remembers something from earlier. It helps explain a clue or a feeling from the past."),
        QAItem(question="What is curiosity?",
               answer="Curiosity is the wish to know more. A curious character keeps asking questions and looking for answers."),
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


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("mystery", MYSTERIES), ("memory", MEMORIES), ("fix", FIXES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], MEMORIES[params.memory], FIXES[params.fix],
                 params.child_name, params.child_gender, params.guide_name, params.guide_gender, params.guide_role)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,F) :- setting(S), mystery(M), fix(F), risk(M,R), power(F,P), R <= P, sense(F,Se), Se >= 2.
"""

def asp_facts() -> str:
    import asp
    out = []
    for sid in SETTINGS:
        out.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        out.append(asp.fact("mystery", mid))
        out.append(asp.fact("risk", mid, m.risk))
    for fid, f in FIXES.items():
        out.append(asp.fact("fix", fid))
        out.append(asp.fact("sense", fid, f.sense))
        out.append(asp.fact("power", fid, f.power))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python combo gates")
        rc = 1
    # smoke test generate + emit
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
