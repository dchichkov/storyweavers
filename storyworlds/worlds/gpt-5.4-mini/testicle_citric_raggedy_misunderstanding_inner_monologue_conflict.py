#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/testicle_citric_raggedy_misunderstanding_inner_monologue_conflict.py
====================================================================================================

A small mythic story world built from the seed words:
- testicle
- citric
- raggedy

Narrative instruments:
- Misunderstanding
- Inner Monologue
- Conflict

Style:
- Mythic, child-facing, concrete, and state-driven.

This world tells a short legend about a temple keeper, a raggedy pilgrim, and a
mistaken omen involving a citric offering and a strange sacred object called the
testicle stone.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Realm:
    id: str
    name: str
    mood: str
    shrine: str
    waters: str
    omen: str

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
class SacredThing:
    id: str
    label: str
    phrase: str
    myth_text: str
    is_citric: bool = False
    is_raggedy: bool = False

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
class Response:
    id: str
    sense: int
    calm: int
    text: str
    fail: str
    qa_text: str

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    priest = world.entities.get("keeper")
    pilgrim = world.entities.get("pilgrim")
    if not priest or not pilgrim:
        return out
    if priest.memes["alarm"] >= THRESHOLD and pilgrim.memes["stung"] >= THRESHOLD:
        sig = ("conflict",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        priest.memes["conflict"] += 1
        pilgrim.memes["conflict"] += 1
        out.append("__conflict__")
    return out


RULES = [Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_misunderstanding(world: World, sacred: SacredThing) -> dict:
    sim = world.copy()
    _do_spark(sim, sim.get("pilgrim"), sacred, narrate=False)
    return {
        "conflict": sim.get("keeper").memes["conflict"] >= THRESHOLD or sim.get("pilgrim").memes["conflict"] >= THRESHOLD,
        "alarm": sim.get("keeper").memes["alarm"],
    }


def _do_spark(world: World, pilgrim: Entity, sacred: SacredThing, narrate: bool = True) -> None:
    if sacred.is_citric:
        pilgrim.meters["scent"] += 1
    pilgrim.memes["hope"] += 1
    if narrate:
        world.say(f"The air filled with the {sacred.label} scent, bright as dawn.")
    world.get("keeper").memes["alarm"] += 1
    pilgrim.memes["stung"] += 1
    propagate(world, narrate=narrate)


def tell(realm: Realm, sacred: SacredThing, response: Response,
         keeper_name: str = "Aster", pilgrim_name: str = "Mira") -> World:
    world = World()
    keeper = world.add(Entity(id="keeper", kind="character", type="priestess", label=keeper_name, role="keeper"))
    pilgrim = world.add(Entity(id="pilgrim", kind="character", type="girl", label=pilgrim_name, role="pilgrim",
                               traits=["raggedy"], attrs={"cloak": "raggedy cloak"}))
    relic = world.add(Entity(id="relic", kind="thing", type="thing", label=sacred.label))
    realm_ent = world.add(Entity(id="realm", kind="thing", type="place", label=realm.name))

    keeper.memes["duty"] = 1.0
    pilgrim.memes["wonder"] = 1.0

    world.say(
        f"In the old days, when the shrine of {realm.name} still listened to the wind, "
        f"the keeper watched over the {realm.omen} and the stone of {sacred.label}."
    )
    world.say(
        f"A raggedy pilgrim named {pilgrim_name} came from the hills in a {pilgrim.attrs['cloak']}, "
        f"carrying a basket of {sacred.phrase} offerings."
    )
    world.say(
        f"{pilgrim_name} thought the citric scent meant the gods were asking for the {sacred.label}, "
        f"but {keeper_name} believed the offering should stay on the altar."
    )

    world.para()
    world.say(
        f'"I must be wise," {pilgrim_name} thought. "If the omen is true, the shrine will open."'
    )
    world.say(
        f'"I must guard the rite," {keeper_name} thought. "If the child touches the stone, the peace may break."'
    )

    pred = predict_misunderstanding(world, sacred)
    world.facts["predicted_conflict"] = pred["conflict"]

    world.para()
    world.say(
        f"Then {pilgrim_name} reached for the {sacred.label}, and the keeper cried out."
    )
    world.say(
        f'"That is not what the omen means!" {keeper_name} said. "Leave the {sacred.label} where it rests."'
    )
    _do_spark(world, pilgrim, sacred, narrate=False)

    world.para()
    if response.sense >= SENSE_MIN:
        if response.calm >= 3:
            world.say(
                f"{keeper_name} lowered {keeper.pronoun('possessive')} voice and {response.text.replace('{target}', sacred.label)}."
            )
            world.say(
                f"The pilgrim listened, and the anger faded like smoke after rain."
            )
            keeper.memes["alarm"] = 0.0
            pilgrim.memes["stung"] = 0.0
            pilgrim.memes["peace"] += 1
            keeper.memes["peace"] += 1
            world.say(
                f"In the end, the citric basket stayed on the altar, the raggedy cloak stayed on {pilgrim_name}'s shoulders, "
                f"and the shrine shone calm beneath the moon."
            )
            outcome = "resolved"
        else:
            world.say(
                f"{keeper_name} tried to answer, but {response.fail.replace('{target}', sacred.label)}"
            )
            world.say(
                f"The misunderstanding grew into a sharp quarrel under the temple lamps."
            )
            outcome = "quarrel"
    else:
        raise StoryError("Response is too weak for this mythic conflict.")

    world.facts.update(
        keeper=keeper,
        pilgrim=pilgrim,
        relic=relic,
        realm=realm_ent,
        sacred=sacred,
        response=response,
        outcome=outcome,
        realm_cfg=realm,
    )
    return world


REALMS = {
    "temple": Realm("temple", "the moon temple", "listening hush", "moon altar", "silver pool", "citric omen"),
    "grove": Realm("grove", "the grove of reeds", "green hush", "stone arch", "still pool", "citric omen"),
    "isle": Realm("isle", "the island shrine", "salt hush", "shell altar", "blue pool", "citric omen"),
}

SACRED_THINGS = {
    "citric_orb": SacredThing("citric_orb", "citric orb", "bright citric fruits", "a golden fruit said to wake sleeping spirits", is_citric=True),
    "raggedy_cloak": SacredThing("raggedy_cloak", "raggedy cloak", "a raggedy cloak hemmed with bells", "a raggedy cloak that belonged to the first wanderer", is_raggedy=True),
    "testicle_stone": SacredThing("testicle_stone", "testicle stone", "the testicle stone of the hill", "a round sacred stone that the old tales named the testicle stone",),
}

RESPONSES = {
    "gentle_explain": Response("gentle_explain", 3, 3,
                               "explained that the omen pointed to a blessing, not a theft, and asked for patience",
                               "spoke too hurriedly and only made the child more certain",
                               "explained the omen and asked for patience"),
    "song": Response("song", 2, 2,
                     "began a low temple song that soothed the air",
                     "tried to sing, but the note broke in the middle",
                     "began a temple song"),
    "warning": Response("warning", 2, 1,
                        "spoke a warning, but not enough to settle the matter",
                        "warned, yet the words slipped away like water",
                        "spoke a warning"),
}

REALM_ORDER = list(REALMS)
THING_ORDER = list(SACRED_THINGS)


@dataclass
@dataclass
class StoryParams:
    realm: str
    sacred: str
    response: str
    keeper_name: str
    pilgrim_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for r in REALMS:
        for s in SACRED_THINGS:
            for resp in RESPONSES.values():
                if resp.sense >= SENSE_MIN:
                    out.append((r, s, resp.id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with misunderstanding, inner monologue, and conflict.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--sacred", choices=SACRED_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--keeper-name")
    ap.add_argument("--pilgrim-name")
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
              if (args.realm is None or c[0] == args.realm)
              and (args.sacred is None or c[1] == args.sacred)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, sacred, response = rng.choice(sorted(combos))
    return StoryParams(
        realm=realm,
        sacred=sacred,
        response=response,
        keeper_name=args.keeper_name or rng.choice(["Aster", "Lysa", "Ione", "Thale"]),
        pilgrim_name=args.pilgrim_name or rng.choice(["Mira", "Nemi", "Sora", "Lyra"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sacred = f["sacred"]
    return [
        f'Write a mythic story for a young child that includes the words "{sacred.label}", "citric", and "raggedy".',
        f"Tell a legend where a raggedy pilgrim misunderstands a sacred sign and a keeper calms the conflict.",
        f"Write a story with an inner monologue, a misunderstanding, and a temple conflict in an old mythic style.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = f["keeper"]
    pilgrim = f["pilgrim"]
    sacred = f["sacred"]
    realm = f["realm_cfg"]
    out = [
        QAItem(
            "Who came to the shrine?",
            f"A raggedy pilgrim named {pilgrim.label_word} came to the shrine in {realm.name}. {keeper.label_word} watched over the rite."
        ),
        QAItem(
            "Why was there a misunderstanding?",
            f"{pilgrim.label_word} thought the citric scent meant the gods wanted the {sacred.label}. The keeper understood it as a sign to guard the offering instead."
        ),
        QAItem(
            "What did the characters think to themselves?",
            f"{pilgrim.label_word} thought about being wise and hoped the omen was true. {keeper.label_word} thought about guarding the peace and feared the rite might break."
        ),
    ]
    if f["outcome"] == "resolved":
        out.append(QAItem(
            "How did the conflict end?",
            f"{keeper.label_word} answered gently, the misunderstanding softened, and the quarrel ended. The citric basket stayed on the altar, so the shrine became calm again."
        ))
    else:
        out.append(QAItem(
            "How did the conflict end?",
            f"The misunderstanding turned into a quarrel, because the answer was not calm enough. The shrine stayed tense instead of peaceful."
        ))
    return out


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does citric mean?", "Citric means having to do with citrus fruits, like lemons and oranges, which smell bright and tangy."),
        QAItem("What does raggedy mean?", "Raggedy means worn, old, and a little torn around the edges."),
        QAItem("What is a misunderstanding?", "A misunderstanding happens when people think a sign or words mean one thing, but they mean something else."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("temple", "citric_orb", "gentle_explain", "Aster", "Mira"),
    StoryParams("grove", "raggedy_cloak", "song", "Lysa", "Nemi"),
    StoryParams("isle", "testicle_stone", "warning", "Ione", "Lyra"),
]


ASP_RULES = r"""
valid(R, S, Q) :- realm(R), sacred(S), response(Q), sense(Q, N), sense_min(M), N >= M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in REALMS:
        lines.append(asp.fact("realm", r))
    for s in SACRED_THINGS:
        lines.append(asp.fact("sacred", s))
    for q, r in RESPONSES.items():
        lines.append(asp.fact("response", q))
        lines.append(asp.fact("sense", q, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() crashed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(REALMS[params.realm], SACRED_THINGS[params.sacred], RESPONSES[params.response],
                 params.keeper_name, params.pilgrim_name)
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
    if trace and sample.world:
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
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
