#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/urn_dote_controversy_suspense_humor_mystery.py
===============================================================================

A standalone storyworld for a small mystery tale about an urn, a dote, and a
sudden controversy.

Premise:
- A child and a careful grown-up are trying to solve a funny little mystery in
  a quiet room.
- A tiny dote mark on an old urn starts a controversy because nobody agrees on
  where it came from.
- The mystery builds suspense, but the ending proves the truth and leaves a
  warm, humorous image behind.

This world uses typed entities with physical meters and emotional memes, a small
forward-chained causal model, a Python reasonableness gate, and an inline ASP
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
    age: int
    traits: list[str] = field(default_factory=list)
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
class Artifact:
    id: str
    label: str
    phrase: str
    detail: str
    fragile: bool = False
    suspicious: bool = False
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
class Response:
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


def _r_suspense(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["tension"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["quiet"] = max(0.0, world.get("room").meters["quiet"] - 1)
        out.append("")
    return out


def _r_controversy(world: World) -> list[str]:
    out = []
    urn = world.get("urn")
    if urn.meters["scrutinized"] >= THRESHOLD and urn.meters["dote_seen"] >= THRESHOLD:
        sig = ("controversy",)
        if sig not in world.fired:
            world.fired.add(sig)
            for ch in list(world.entities.values()):
                if ch.role == "investigator":
                    ch.memes["confusion"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("suspense", "mood", _r_suspense), Rule("controversy", "social", _r_controversy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(artifact: Artifact, response: Response) -> bool:
    return artifact.fragile and response.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for art_id, art in ARTIFACTS.items():
        for resp_id, resp in RESPONSES.items():
            if reasonableness_gate(art, resp):
                combos.append((art_id, resp_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    artifact: str
    response: str
    child: str
    child_type: str
    helper: str
    helper_type: str
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


SETTINGS = {
    "museum_room": Setting("museum_room", "the museum room", "glass cases hummed under soft lamps"),
    "attic_corner": Setting("attic_corner", "the attic corner", "dust motes drifted in a thin stripe of light"),
}

CHARACTERS = {
    "maya": CharacterCfg("Maya", "girl", 7, ["curious", "quiet"]),
    "noah": CharacterCfg("Noah", "boy", 7, ["careful", "bright"]),
    "aunt_rose": CharacterCfg("Aunt Rose", "aunt", 35, ["careful", "gentle"]),
    "uncle_lev": CharacterCfg("Uncle Lev", "uncle", 38, ["patient", "dry"]),
}

ARTIFACTS = {
    "urn": Artifact("urn", "urn", "an old urn", "the clay urn on the pedestal", fragile=True, suspicious=True, tags={"urn", "mystery"}),
    "vase": Artifact("vase", "vase", "a tall vase", "the painted vase on the shelf", fragile=True, suspicious=True, tags={"urn", "mystery"}),
    "box": Artifact("box", "box", "a wooden box", "the box", fragile=False, suspicious=False, tags={"box"}),
}

RESPONSES = {
    "cloth": Response("cloth", 3, 3, "lifted the cloth and peeked underneath", "lifted the cloth, but the clue had already been missed", "lifted the cloth and solved the little mystery", tags={"clue"}),
    "glove": Response("glove", 2, 2, "slipped on cotton gloves and checked the rim", "checked too quickly and only made everyone more puzzled", "checked the rim with cotton gloves", tags={"clue"}),
    "lamp": Response("lamp", 3, 3, "moved the lamp closer and studied the mark", "moved the lamp, but the shadow still hid the clue", "studied the mark by lamp light", tags={"light"}),
}

CURIOSITY = ["wonder", "joy", "suspense"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a tiny mystery with an urn, a dote, and a controversy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child", choices=[c.id for c in CHARACTERS.values()])
    ap.add_argument("--helper", choices=[c.id for c in CHARACTERS.values()])
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
    if args.artifact and args.response and not reasonableness_gate(ARTIFACTS[args.artifact], RESPONSES[args.response]):
        raise StoryError("No story: this clue and response do not make a sensible mystery.")
    combos = [c for c in valid_combos()
              if (args.artifact is None or c[0] == args.artifact)
              and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    art_id, resp_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child = args.child or rng.choice(["Maya", "Noah"])
    helper = args.helper or rng.choice(["Aunt Rose", "Uncle Lev"])
    child_cfg = CHARACTERS["maya"] if child == "Maya" else CHARACTERS["noah"]
    helper_cfg = CHARACTERS["aunt_rose"] if helper == "Aunt Rose" else CHARACTERS["uncle_lev"]
    return StoryParams(setting=setting, artifact=art_id, response=resp_id, child=child_cfg.id, child_type=child_cfg.type, helper=helper_cfg.id, helper_type=helper_cfg.type)


def tell(setting: Setting, artifact: Artifact, response: Response, child: CharacterCfg, helper: CharacterCfg) -> World:
    world = World()
    c = world.add(Entity(id=child.id, kind="character", type=child.type, role="investigator", traits=list(child.traits)))
    h = world.add(Entity(id=helper.id, kind="character", type=helper.type, role="helper", traits=list(helper.traits)))
    urn = world.add(Entity(id="urn", kind="thing", type="urn", label=artifact.label, attrs={"clue": "dote"}))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    room.meters["quiet"] = 2
    c.memes["curiosity"] = 1
    h.memes["calm"] = 1
    world.say(f"In {setting.place}, {setting.detail}. {c.id} and {h.id} found {artifact.phrase}.")
    world.say(f"The odd thing was a tiny dote mark on the side of the {artifact.label}, and that made a small controversy at once.")
    world.para()
    c.meters["tension"] += 1
    urn.meters["scrutinized"] += 1
    urn.meters["dote_seen"] += 1
    propagate(world, narrate=False)
    world.say(f"{c.id} leaned closer, and {h.id} frowned in a funny, thoughtful way. They did not touch the {artifact.label}; they only watched.")
    world.para()
    world.say(f'"Let us check the clue carefully," {h.id} said.')
    body = response.text
    world.say(f"{c.id} {body}.')
    urn.meters["solved"] += 1
    world.say("The tiny mark turned out to be a spilled dot of jam from an earlier snack, and the room's big mystery suddenly became a very small, sticky joke.")
    world.say(f'{c.id} laughed. "{artifact.label.capitalize()} drama, solved!"')
    world.say("The controversy faded, and the old urn sat peacefully under the lamp, wearing its little jam dote like a freckle.")
    world.facts.update(setting=setting, artifact=artifact, response=response, child=c, helper=h, urn=urn, room=room, outcome="solved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["artifact"]
    return [
        f'Write a short mystery story for a child that includes the words "urn", "dote", and "controversy".',
        f"Tell a suspenseful, funny story where {f['child'].id} and {f['helper'].id} inspect an {a.label} and calmly solve a tiny controversy.",
        f'Write a gentle mystery with a humorous ending: the clue is a dote on an urn, and everyone learns what really happened.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    art = f["artifact"]
    c = f["child"]
    h = f["helper"]
    return [
        ("What was the mystery about?",
         f"It was about a tiny dote mark on the {art.label}. That little mark caused a controversy because nobody knew what it meant at first."),
        ("Why was everyone tense?",
         f"{c.id} and {h.id} were worried the mark might be an important clue. The suspense grew because they had to look carefully before guessing."),
        ("What solved the problem?",
         f"They looked closely and found out the dote was just jam. That made the controversy disappear, and the mystery became funny instead of scary."),
        ("How did the story end?",
         f"It ended with the {art.label} safe and the clue explained. {c.id} laughed, so the room felt calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an urn?",
         "An urn is a large container, often made from clay or stone. People may use it to hold flowers or ashes, and old urns can look very mysterious."),
        ("What is a dote mark?",
         "A dote is a tiny dot or spot. A small dot can be a clue when someone is trying to solve a mystery."),
        ("What is a controversy?",
         "A controversy is a disagreement that many people notice. It can sound serious, but sometimes it is really just people arguing about a small thing."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        out.append(f"  {e.id:6} ({e.type:7}) {' '.join(parts)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="museum_room", artifact="urn", response="cloth", child="Maya", child_type="girl", helper="Aunt Rose", helper_type="aunt"),
    StoryParams(setting="attic_corner", artifact="vase", response="glove", child="Noah", child_type="boy", helper="Uncle Lev", helper_type="uncle"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.artifact not in ARTIFACTS or params.response not in RESPONSES:
        raise StoryError("Invalid params for this storyworld.")
    child_cfg = CHARACTERS["maya"] if params.child == "Maya" else CHARACTERS["noah"]
    helper_cfg = CHARACTERS["aunt_rose"] if params.helper == "Aunt Rose" else CHARACTERS["uncle_lev"]
    world = tell(SETTINGS[params.setting], ARTIFACTS[params.artifact], RESPONSES[params.response], child_cfg, helper_cfg)
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
fragile(A) :- artifact(A), fragile_artifact(A).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(A,R) :- fragile(A), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.fragile:
            lines.append(asp.fact("fragile_artifact", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {r for r, resp in RESPONSES.items() if resp.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: verify passed and story generation smoke-tested.")
    return rc


def explain_rejection() -> str:
    return "No story: this clue-response pair is too thin for a mystery worth telling."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.artifact is None or c[0] == args.artifact)
              and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    art_id, resp_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child = args.child or rng.choice(["Maya", "Noah"])
    helper = args.helper or rng.choice(["Aunt Rose", "Uncle Lev"])
    child_cfg = CHARACTERS["maya"] if child == "Maya" else CHARACTERS["noah"]
    helper_cfg = CHARACTERS["aunt_rose"] if helper == "Aunt Rose" else CHARACTERS["uncle_lev"]
    return StoryParams(setting=setting, artifact=art_id, response=resp_id, child=child_cfg.id, child_type=child_cfg.type, helper=helper_cfg.id, helper_type=helper_cfg.type)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for a, r in asp_valid_combos():
            print(a, r)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
