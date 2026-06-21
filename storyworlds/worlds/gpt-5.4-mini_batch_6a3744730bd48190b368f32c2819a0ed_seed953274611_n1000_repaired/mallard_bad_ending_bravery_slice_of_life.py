#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mallard_bad_ending_bravery_slice_of_life.py
=============================================================================

A small, child-facing storyworld about an ordinary day at a pond: a brave child
tries to help a mallard, but the risk is larger than their courage. The story
keeps a slice-of-life tone, with a clear beginning, a brief turn, and a bad
ending that still teaches something concrete.

Seed words: mallard
Features: Bad Ending, Bravery
Style: Slice of Life
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 4.0


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
    attrs: dict = field(default_factory=dict)

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
    detail: str
    allows: set[str] = field(default_factory=set)
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
class CharacterCfg:
    id: str
    type: str
    gender: str
    brave: float
    curious: float
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
class MallardCfg:
    id: str
    label: str
    behavior: str
    danger: str
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
class OutcomeCfg:
    id: str
    severity: int
    text: str
    aftermath: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_panic(world: World) -> list[str]:
    out: list[str] = []
    pond = world.get("pond")
    if pond.meters["ripple"] >= THRESHOLD and ("panic", "pond") not in world.fired:
        world.fired.add(("panic", "pond"))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("The water shivered, and the day felt suddenly too small.")
    return out


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    duck = world.get("mallard")
    child = world.get("child")
    if duck.meters["distress"] >= THRESHOLD and ("wet", "mallard") not in world.fired:
        world.fired.add(("wet", "mallard"))
        child.memes["sadness"] += 1
        out.append("The mallard looked skittish, as if even the grass felt sharp.")
    return out


CAUSAL_RULES = [Rule("panic", _r_panic), Rule("wet", _r_wet)]


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


def ask_for_bravery(world: World, child: Entity, mallard: Entity, setting: Setting) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"After school, {child.id} walked to {setting.place} with a small, steady step. "
        f"The {setting.detail} made the afternoon feel calm, and a {mallard.label} bobbed near the bank."
    )
    world.say(
        f'{child.id} took a breath and said, "Hello, mallard." '
        f"{child.pronoun().capitalize()} wanted to be brave enough to help."
    )


def warn_about_risk(world: World, child: Entity, mallard: Entity) -> None:
    child.memes["care"] += 1
    world.say(
        f"The bird was brave too, but not in the same way. It kept stepping away from the path, "
        f"and its feathers twitched whenever a bicycle rattled by."
    )
    world.say(
        f"{child.id} noticed that {mallard.label_word if mallard.label_word else mallard.label} was not a pet and not a toy. "
        f"Bravery, {child.id} thought, should still be gentle."
    )


def reach_out(world: World, child: Entity, mallard: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} crouched low and held out {child.pronoun("possessive")} hand. '
        f'"It\'s okay," {child.id} whispered, trying to look calm.'
    )


def bad_turn(world: World, child: Entity, mallard: Entity, outcome: OutcomeCfg) -> None:
    mallard.meters["distress"] += 1
    mallard.meters["ripple"] += 1
    propagate(world, narrate=True)
    world.say(
        f"The mallard startled hard, flapped across the water, and hit the reeds with a messy splash. "
        f"Then {outcome.text}"
    )
    world.say(
        f"{outcome.aftermath}"
    )


def ending_image(world: World, child: Entity, mallard: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"By sunset, {child.id} stood with {child.pronoun('possessive')} hands tucked in {child.pronoun('possessive')} pockets, "
        f"watching the mallard drift far away on the darkening pond."
    )
    world.say(
        f"The brave feeling was still there, but now it was quieter. {child.id} had learned that some help means keeping your distance."
    )


def tell(setting: Setting, child_cfg: CharacterCfg, mallard_cfg: MallardCfg, outcome: OutcomeCfg,
         child_name: str = "Mina", parent_name: str = "Mom") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_cfg.gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent"))
    pond = world.add(Entity(id="pond", kind="thing", type="place", label=setting.place))
    mallard = world.add(Entity(id=mallard_cfg.id, kind="thing", type="animal", label=mallard_cfg.label))
    world.facts.update(setting=setting, child=child, parent=parent, mallard=mallard, outcome=outcome)

    child.memes["bravery"] = child_cfg.brave
    child.memes["curiosity"] = child_cfg.curious

    ask_for_bravery(world, child, mallard, setting)
    world.para()
    warn_about_risk(world, child, mallard)
    reach_out(world, child, mallard)
    world.para()
    bad_turn(world, child, mallard, outcome)
    ending_image(world, child, mallard)
    return world


SETTINGS = {
    "pond": Setting(
        id="pond",
        place="the little pond behind the park",
        detail="duckweed on the water",
        allows={"watch"},
    ),
    "lake": Setting(
        id="lake",
        place="the lake path by the playground",
        detail="small waves near the shore",
        allows={"watch"},
    ),
}

CHILDREN = {
    "brave_kid": CharacterCfg(id="brave_kid", type="girl", gender="girl", brave=5.0, curious=4.0),
    "gentle_kid": CharacterCfg(id="gentle_kid", type="boy", gender="boy", brave=4.0, curious=5.0),
    "quiet_kid": CharacterCfg(id="quiet_kid", type="girl", gender="girl", brave=4.0, curious=3.0),
}

MALLARDS = {
    "mallard": MallardCfg(
        id="mallard",
        label="mallard",
        behavior="drifting close",
        danger="startled flight",
        tags={"mallard", "duck", "bird"},
    ),
    "duck": MallardCfg(
        id="mallard",
        label="duck",
        behavior="drifting close",
        danger="startled flight",
        tags={"mallard", "duck", "bird"},
    ),
}

OUTCOMES = {
    "bad_scare": OutcomeCfg(
        id="bad_scare",
        severity=2,
        text="the bird flew up in a panic, and its wing knocked over a paper cup on the path.",
        aftermath="The cup rolled into the water, and the pond-side bench was left wet and sad.",
        tags={"bad", "scare"},
    ),
    "bad_lost_snack": OutcomeCfg(
        id="bad_lost_snack",
        severity=3,
        text="the bird bolted, and the snack in {child}’s hand fell into the mud by the reeds.",
        aftermath="The snack was ruined, and the child had to walk home empty-handed.",
        tags={"bad", "snack"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    child: str
    mallard: str
    outcome: str
    child_name: str = "Mina"
    parent_name: str = "Mom"
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
        setting="pond",
        child="brave_kid",
        mallard="mallard",
        outcome="bad_scare",
        child_name="Mina",
        parent_name="Mom",
        seed=1,
    ),
    StoryParams(
        setting="lake",
        child="gentle_kid",
        mallard="duck",
        outcome="bad_lost_snack",
        child_name="Noah",
        parent_name="Dad",
        seed=2,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid in CHILDREN:
            for mid in MALLARDS:
                if "mallard" in MALLARDS[mid].tags and "pond" in setting.id:
                    for oid in OUTCOMES:
                        combos.append((sid, cid, oid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life mallard storyworld with a bad ending and a brave child."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--mallard", choices=MALLARDS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["Mom", "Dad"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.child is None or c[1] == args.child)
              and (args.outcome is None or c[2] == args.outcome)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, child, outcome = rng.choice(sorted(combos))
    mallard = args.mallard or "mallard"
    name = args.name or rng.choice(["Mina", "Luna", "Noah", "Eli", "Iris"])
    parent = args.parent or rng.choice(["Mom", "Dad"])
    return StoryParams(setting=setting, child=child, mallard=mallard, outcome=outcome, child_name=name, parent_name=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.child not in CHILDREN:
        raise StoryError("Invalid child.")
    if params.mallard not in MALLARDS:
        raise StoryError("Invalid mallard.")
    if params.outcome not in OUTCOMES:
        raise StoryError("Invalid outcome.")
    world = tell(SETTINGS[params.setting], CHILDREN[params.child], MALLARDS[params.mallard], OUTCOMES[params.outcome],
                 child_name=params.child_name, parent_name=params.parent_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a slice-of-life story that includes the word "mallard" and ends with a sad consequence.',
        f"Tell a calm everyday story where {f['child'].id} tries to help a mallard by getting too close, but the moment goes wrong.",
        f"Write a short child-facing story about bravery near {f['setting'].place} with a bad ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mallard = f["mallard"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and a mallard at {setting.place}. The story follows an ordinary afternoon that turns sad."),
        ("Why did the child get close to the mallard?",
         f"{child.id} wanted to be brave and help the mallard. The child thought a gentle hello would be enough, but the bird felt frightened instead."),
        ("What happened at the end?",
         f"The mallard panicked and flew away, leaving a bad ending. {child.id} was left standing alone by the pond, learning that bravery also needs care."),
    ]
    if f["outcome"].id == "bad_lost_snack":
        qa.append(
            ("What was lost in the worst moment?",
             f"A snack fell into the mud and was ruined. That made the ending feel even worse because the child could not get it back.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a mallard?",
         "A mallard is a kind of duck. It can swim on water and flap away very quickly if it gets scared."),
        ("What does bravery mean?",
         "Bravery means doing something difficult even when you feel nervous. It is best when you also stay gentle and careful."),
        ("Why should people keep some distance from wild birds?",
         "Wild birds can be scared by sudden movement or close hands. Keeping space helps the bird stay calm and keeps people safer too."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,O) :- setting(S), child(C), outcome(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for oid in OUTCOMES:
        lines.append(asp.fact("outcome", oid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: verification passed.")
    return rc


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(show="#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
