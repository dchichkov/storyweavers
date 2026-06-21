#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/joy_audiotape_psychic_happy_ending_dialogue_myth.py
====================================================================================

A standalone story world for a tiny mythic tale about a child, an audiotape,
and a psychic warning that leads to a happy ending.

Seed idea
---------
A child hears an old audiotape from a psychic in a myth-like village. The tape
warns that a shrine's joy has gone dim. Through dialogue, the child and a
kind elder follow the prophecy, repair the shrine, and end in a bright,
celebratory image.

This script follows the storyworld contract:
- stdlib only
- eager import of storyworlds/results.py containers
- typed entities with meters and memes
- state-driven prose
- QA grounded in simulated state
- Python reasonableness gate plus inline ASP twin
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "priestess"}
        male = {"boy", "father", "dad", "man", "priest"}
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
    dark: str
    sacred: str
    ending_image: str

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
class Artifact:
    id: str
    label: str
    phrase: str
    spirit: str
    can_hear: bool = False
    makes_joy: bool = False
    makes_light: bool = False
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
class Problem:
    id: str
    label: str
    threat: str
    loss: str
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
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

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


def _r_joy(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["joy"] >= THRESHOLD and ("joy", e.id) not in world.fired:
            world.fired.add(("joy", e.id))
            out.append(f"{e.id} felt a bright lift in the chest.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


CAUSAL_RULES = [Rule("joy", _r_joy)]


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def reason_gate() -> bool:
    return bool(sensible_remedies())


def psychic_hint(aud: Artifact, problem: Problem) -> bool:
    return aud.can_hear and "light" in problem.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not reason_gate():
        return combos
    for s in SETTINGS:
        for a in TAPES:
            for p in PROBLEMS:
                if psychic_hint(TAPES[a], PROBLEMS[p]):
                    combos.append((s, a, p))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    tape: str
    problem: str
    remedy: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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


def tell(setting: Setting, tape: Artifact, problem: Problem, remedy: Remedy,
         child_name: str = "Mira", child_gender: str = "girl",
         elder_name: str = "Sorin", elder_gender: str = "man") -> World:
    w = World()
    child = w.add(Entity(child_name, kind="character", type=child_gender,
                         role="child", traits=["curious"]))
    elder = w.add(Entity(elder_name, kind="character", type=elder_gender,
                         role="elder", traits=["wise"]))
    shrine = w.add(Entity("shrine", type="shrine", label=setting.sacred))
    tape_ent = w.add(Entity("tape", type="artifact", label=tape.label))
    tape_ent.meters["music"] = 1.0
    child.memes["wonder"] += 1
    child.memes["joy"] += 1

    w.say(
        f"In {setting.place}, where old stories still clung to the stones, "
        f"{child.id} found {tape.phrase} beside {setting.dark}. {setting.ending_image}"
    )
    w.say(
        f'{child.id} held it up. "{tape.label.capitalize()}?" {child.pronoun()} whispered. '
        f'"It looks like a sleeping voice."'
    )
    w.say(
        f'Then the tape clicked, and a soft prophecy spilled out: "{tape.spirit}"'
    )

    w.para()
    if not psychic_hint(tape, problem):
        raise StoryError("This tape does not carry a psychic hint for the chosen problem.")
    child.memes["fear"] += 1
    w.say(
        f'{child.id} frowned. "{problem.threat}," {child.pronoun()} said. '
        f'"That sounds like trouble for {setting.sacred}."'
    )
    w.say(
        f'"And if the shrine loses its joy," {elder.id} said gently, '
        f'"the whole lane will grow quiet."'
    )
    elder.memes["calm"] += 1

    w.para()
    child.memes["hope"] += 1
    w.say(
        f'"What should we do?" {child.id} asked.'
    )
    w.say(
        f'"We follow the message," {elder.id} answered. '
        f'"Bring the tape. We will listen, then mend what the prophecy warned about."'
    )
    w.say(
        f'They went together to {setting.sacred}, and {elder.id} showed {child.id} '
        f'how to {problem.loss}.'
    )

    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(remedy.id))

    w.para()
    child.memes["joy"] += 1
    w.say(
        f'"Could this really help?" {child.id} asked.'
    )
    w.say(
        f'"Yes," {elder.id} said. "{remedy.text}"'
    )
    shrine.meters["broken"] = 1.0
    if remedy.power >= 1:
        shrine.meters["broken"] = 0.0
        shrine.meters["joy"] += 1
        child.meters["joy"] += 1
        child.memes["relief"] += 1
        elder.memes["relief"] += 1
        child.memes["joy"] += 1
        w.say(
            f'{remedy.qa_text}. The shrine answered at once: the dimness lifted, '
            f'and a warm gold glow returned to the stones.'
        )
    else:
        raise StoryError("This remedy is too weak for the mythic problem.")

    w.para()
    propagate(w, narrate=False)
    child.memes["joy"] += 2
    elder.memes["joy"] += 1
    w.say(
        f'{elder.id} smiled and tucked the tape away. "{tape.label.capitalize()} '
        f'told the truth," {elder.id} said. "And now the place is bright again."'
    )
    w.say(
        f'{child.id} laughed, and the two of them stood beside {setting.ending_image}, '
        f"listening to the shrine hum like a contented drum."
    )
    w.say(
        f"That night the village kept its song, {problem.label} was gone, and joy "
        f"stayed awake under the stars."
    )

    w.facts.update(
        child=child, elder=elder, shrine=shrine, tape=tape, setting=setting,
        problem=problem, remedy=remedy, outcome="happy", repaired=True
    )
    return w


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    good = ", ".join(sorted(x.id for x in sensible_remedies()))
    return f"(Refusing remedy '{rid}': sense={r.sense} is too low. Try: {good}.)"


SETTINGS = {
    "village": Setting("village", "the hill village", "a dark stair by the gate",
                       "the little shrine", "lanterns lined the path"),
    "temple": Setting("temple", "the riverside temple", "a shadow under the eaves",
                      "the singing altar", "bells shivered in the wind"),
    "orchard": Setting("orchard", "the moonlit orchard", "a hush beneath the trees",
                       "the stone shrine", "fruit glowed like amber"),
}

TAPES = {
    "oracle": Artifact("oracle", "an audiotape", "an old audiotape",
                       "The voice said, 'Listen well, brave one. The shrine's joy has faded, but the path home is still open.'",
                       can_hear=True, tags={"audiotape", "psychic"}),
    "seer": Artifact("seer", "audiotape", "a ribbon-wrapped audiotape",
                     "The whisper on the tape said, 'Go to the shrine and speak kindly; the broken thing will answer joy.'",
                     can_hear=True, tags={"audiotape", "psychic"}),
    "chorus": Artifact("chorus", "an audiotape", "a dusty audiotape",
                       "The tape murmured, 'When voices join, the heavy heart grows light.'",
                       can_hear=True, tags={"audiotape", "psychic"}),
}

PROBLEMS = {
    "dim_shrine": Problem("dim_shrine", "dim shrine joy", "the shrine's joy has gone dim",
                          "mend the cracked lamp", tags={"joy", "light", "shrine"}),
    "lost_song": Problem("lost_song", "lost song", "the village song has fallen silent",
                         "retie the bells and sing again", tags={"joy", "sound"}),
    "sleepy_gate": Problem("sleepy_gate", "sleepy gate", "the gate-watch has grown sleepy",
                           "oil the hinge and wake the watchfire", tags={"light"}),
}

REMEDIES = {
    "lamp": Remedy("lamp", 3, 1, "light the lamp with careful hands and bring it back to the shrine",
                   "lit a lamp, but the shrine stayed dim", "the lamp shone across the stones",
                   tags={"light", "joy"}),
    "song": Remedy("song", 3, 1, "call the neighbors to sing with you until the stones remember",
                   "called for singing, but the silence still lingered", "the neighbors sang in a bright ring",
                   tags={"joy", "sound"}),
    "oil": Remedy("oil", 2, 1, "oil the hinge and lift the gate before the dawn bell",
                  "oiled the hinge, but it still stuck", "the hinge opened with a soft sigh",
                  tags={"light"}),
}

SENSE_MIN = 2

NAMES = ["Mira", "Nina", "Ivo", "Lio", "Ari", "Tala", "Sami", "Oren"]
ELDERS = ["Sorin", "Mara", "Dione", "Elias", "Rhea", "Kato"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a child that includes the words "joy", "audiotape", and "psychic".',
        f"Tell a dialogue-heavy myth about {f['child'].id} hearing a psychic message on an audiotape and asking {f['elder'].id} what to do.",
        f"Write a happy-ending story where an audiotape gives a warning, an elder and child talk it through, and the village's joy returns.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, e, s, t, p, r = f["child"], f["elder"], f["setting"], f["tape"], f["problem"], f["remedy"]
    return [
        ("Who found the audiotape?",
         f"{c.id} found it in {s.place}, and {c.pronoun()} was the one who asked what the message meant."),
        ("What did the psychic message warn about?",
         f"It warned that {p.threat}. That warning sent {c.id} and {e.id} straight to {s.sacred}."),
        ("How did they solve the problem?",
         f"They listened together, then used {r.id} to fix the trouble. The careful choice brought back the shrine's joy."),
        ("How did the story end?",
         f"It ended happily: the shrine glowed again, {c.id} felt joy, and the village kept its song under the stars."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an audiotape?",
         "An audiotape is a tape that can hold recorded sound, so a voice or song can play back later."),
        ("What does psychic mean in a story?",
         "Psychic means someone seems to know something hidden, often through a vision, dream, or mysterious feeling."),
        ("Why do people tell myths?",
         "Myths are old stories people tell to explain a place, a lesson, or something special they believe in."),
        ("What is joy?",
         "Joy is a very happy feeling that makes a person want to smile, laugh, or dance."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "oracle", "dim_shrine", "lamp", "Mira", "girl", "Sorin", "man"),
    StoryParams("temple", "seer", "lost_song", "song", "Ari", "boy", "Mara", "woman"),
    StoryParams("orchard", "chorus", "sleepy_gate", "oil", "Tala", "girl", "Elias", "man"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TAPES:
        lines.append(asp.fact("tape", t))
        lines.append(asp.fact("can_hear", t))
        lines.append(asp.fact("tags", t, "psychic"))
        lines.append(asp.fact("tags", t, "audiotape"))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
        for tag in PROBLEMS[p].tags:
            lines.append(asp.fact("p_tag", p, tag))
    for r in REMEDIES.values():
        lines.append(asp.fact("remedy", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
        lines.append(asp.fact("power", r.id, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,P) :- setting(S), tape(T), problem(P), can_hear(T), p_tag(P, joy).
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
outcome(happy) :- sensible(R), remedy(R), power(R,P), P >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_remedies()}:
        print("OK: sensible remedies match.")
    else:
        print("MISMATCH in sensible remedies")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic joy / audiotape / psychic story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tape", choices=TAPES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "priestess", "priest"])
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
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))
    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.tape is None or c[1] == args.tape)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tape, problem = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(NAMES)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(setting, tape, problem, remedy, child, child_gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TAPES[params.tape], PROBLEMS[params.problem],
                 REMEDIES[params.remedy], params.child, params.child_gender,
                 params.elder, params.elder_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.elder}: {p.tape} / {p.problem} ({p.setting})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
